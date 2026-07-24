#!/usr/bin/env python3
"""SOGEN-GEO 检索工具——扫描当前目录里的 SOGEN 交付 JSON，回答"我手里有什么数据"。

使用场景：客户在自己电脑上，进入他保存检索文件的工作目录(可能是群里陆续下载攒下来的，
可能扁平堆放、可能自己建了文件夹分类、可能混着多个专科群的交付)，直接用自然语言问。
工具不做任何先验假设：**每次调用都先主动扫描当前目录**，发现所有 SOGEN 桶文件
(`SOGEN_{疾病}_0X_{测序类型}.json`，01-07 共 7 类)，就地建索引后查询。目录里有什么才
能查到什么——客户没收到的病，索引里结构性不存在，不是"被过滤掉"。

扫描规则：
- 只认文件名匹配 `SOGEN_*_0[1-7]_*.json` 的桶文件，任意深度任意嵌套都算；
  专题精选 JSON(与 7 桶内容重叠)、汇总 Excel(与 7 桶内容相同)、txt 等杂物天然被排除。
- 压缩包(.7z/.zip/.rar)自动处理：客户很可能把群里下载的包原样丢进目录、从没解压——
  按内容识别 SOGEN 交付包(成员含桶 JSON 或嵌套压缩包)就地解压后再索引；合集包里的
  嵌套压缩包逐层解开；客户已手动解压过的不重复解压(按内容识别,不会重复计数)；
  无关压缩包不碰。`.zip` 走 Python 标准库(零依赖)；`.7z`/`.rar` 需要系统 7-Zip
  (或装了 py7zr),缺工具时明确给中文安装指引,不静默漏数据。
- 疾病名/slug/专科群名全部从文件**内容**里取(桶文件顶层带 group_name/disease/disease_slug)，
  不依赖目录怎么组织——多个群的文件混放也能正确区分来源。
- 交付状态：客户自己目录里的文件一律是「已发送」(他手里有)。仅当扫描根本身带
  "之前所有发送结果原始目录"存档结构时才区分：存档区内=已发送、尚未归档=待发；
  普通客户目录不会长成那个结构，全部一律已发送。

索引缓存：SQLite，放用户目录 `~/.cache/sogen-geo/index-<扫描根路径hash>.db`
- 按扫描根分库：换目录=独立索引，互不污染；同目录重复调用靠文件 mtime 增量同步，
  日常调用只有 walk+stat 的几秒开销，真正重新解析的只有 mtime 变过的文件。
- WSL 用户注意：不要把缓存指到 /mnt/*(9P 挂载)上——实测 LIKE 全表扫描 50+ 秒，
  原生文件系统 1 秒级。默认路径已是原生位置，别用 --db 指过去。
- 索引是派生数据，可删可重建(删掉后下次调用自动重扫全量)。

扫描根解析优先级：`--root 参数` > 环境变量 `SOGEN_GEO_ROOT` > 当前工作目录。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import unicodedata
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

__version__ = "1.2.1"

CACHE_DIR = Path.home() / ".cache" / "sogen-geo"
ROOT_ENV_VAR = "SOGEN_GEO_ROOT"

ARCHIVE_DIR_NAME = "之前所有发送结果原始目录"  # 已发送存档子目录名(其下文件=已发送)
MASTER_DIR_NAME = "群分享交付"                # 交付管理目录名(仅作结构识别的第一道信号)
STATUS_SENT = "已发送"      # 客户手里有这个文件(自己目录里的一切；存档区内的文件)
STATUS_PENDING = "待发"     # 仅交付管理目录里尚未归档的文件；普通客户目录不会出现

# SOGEN_{疾病}_01_转录组测序.json —— 只认 01-07 桶文件；专题/Excel/7z/txt 天然被排除
BUCKET_FILE_RE = re.compile(r"^SOGEN_.+_0[1-7]_.+\.json$")

# 自动解压支持的压缩包后缀(.zip 走标准库;.7z/.rar 走 7-Zip 或 py7zr)
ARCHIVE_EXTS = (".7z", ".zip", ".rar")

RQ_FIELDS = ["case_vs_control_differential", "treatment", "correlation",
             "pre_post_treatment", "survival_analysis", "response"]
RQ_LABELS = {
    "case_vs_control_differential": "病例对照", "treatment": "治疗干预",
    "correlation": "相关性分析", "pre_post_treatment": "治疗前后对比",
    "survival_analysis": "生存分析", "response": "药物响应",
}

# 物种别名组(--organism 用；自由关键词走 search_text，同一套别名在 SEARCH_TEXT_SQL 里)。
# 医生说"小鼠/病人样本"不说拉丁学名——输入落在任一组里就整组展开成 OR。
ORG_ALIAS_GROUPS = [
    ("sapiens", "human", "人", "人类"),
    ("musculus", "mouse", "小鼠"),
    ("rattus", "rat", "大鼠"),
    ("danio", "zebrafish", "斑马鱼"),
    ("macaca", "monkey", "猕猴", "猴"),
    ("scrofa", "pig", "猪"),
    ("canis", "dog", "犬"),
    ("oryctolagus", "rabbit", "兔", "家兔"),
]


def _organism_terms(query):
    q = query.lower()
    terms = {q}
    for group in ORG_ALIAS_GROUPS:
        if q in group:
            terms.update(group)
    return sorted(terms)

# 展平进 SQLite 的列(evidence/search_text 单独处理，不在这个清单里)
COLUMNS = [
    "gse_id", "disease", "disease_slug", "specialty", "group_name", "delivery_status",
    "bucket", "file_name", "rel_path",
    "organism", "n_samples", "platform", "pdat", "pubmed_ids", "sequencing_type",
    "sample_source", "title", "summary", "overall_design", "study_design", "relevance_reason",
    "treatment", "treatment_type", "drug_names",
    "case_vs_control_differential", "correlation", "pre_post_treatment",
    "survival_analysis", "response", "ftplink",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    gse_id TEXT, disease TEXT, disease_slug TEXT, specialty TEXT, group_name TEXT,
    delivery_status TEXT, bucket TEXT, file_name TEXT, rel_path TEXT,
    organism TEXT, n_samples INTEGER, platform TEXT, pdat TEXT, pubmed_ids TEXT,
    sequencing_type TEXT, sample_source TEXT, title TEXT, summary TEXT, overall_design TEXT,
    study_design TEXT, relevance_reason TEXT,
    treatment INTEGER, treatment_type TEXT, drug_names TEXT,
    case_vs_control_differential INTEGER, correlation INTEGER, pre_post_treatment INTEGER,
    survival_analysis INTEGER, response INTEGER, ftplink TEXT, evidence TEXT, search_text TEXT
);
CREATE TABLE IF NOT EXISTS meta (rel_path TEXT PRIMARY KEY, mtime REAL, n_records INTEGER);
CREATE TABLE IF NOT EXISTS archives (rel_path TEXT PRIMARY KEY, mtime REAL, size INTEGER, verdict TEXT);
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
CREATE INDEX IF NOT EXISTS idx_specialty ON datasets(specialty);
CREATE INDEX IF NOT EXISTS idx_disease ON datasets(disease);
CREATE INDEX IF NOT EXISTS idx_gse_id ON datasets(gse_id);
"""

SEARCH_TEXT_SQL = """
    UPDATE datasets SET search_text = LOWER(
        COALESCE(disease,'') || ' ' || COALESCE(disease_slug,'') || ' ' || COALESCE(gse_id,'') || ' ' ||
        COALESCE(title,'') || ' ' || COALESCE(summary,'') || ' ' || COALESCE(overall_design,'') || ' ' ||
        COALESCE(study_design,'') || ' ' || COALESCE(relevance_reason,'') || ' ' ||
        COALESCE(treatment_type,'') || ' ' || COALESCE(drug_names,'') || ' ' ||
        COALESCE(specialty,'') || ' ' || COALESCE(group_name,'') || ' ' || COALESCE(bucket,'') || ' ' ||
        COALESCE(sequencing_type,'') || ' ' || COALESCE(sample_source,'') || ' ' ||
        -- 物种别名：医生大概率说"小鼠/病人样本"而不是 "Mus musculus/Homo sapiens"。
        -- 用串联 WHEN 而非 CASE：混物种记录("Homo sapiens; Mus musculus")每个都补上别名。
        (CASE WHEN LOWER(COALESCE(organism,'')) LIKE '%sapiens%' THEN 'human 人 人类 ' ELSE '' END) ||
        (CASE WHEN LOWER(COALESCE(organism,'')) LIKE '%musculus%' THEN 'mouse 小鼠 ' ELSE '' END) ||
        (CASE WHEN LOWER(COALESCE(organism,'')) LIKE '%rattus%' THEN 'rat 大鼠 ' ELSE '' END) ||
        (CASE WHEN LOWER(COALESCE(organism,'')) LIKE '%danio%' THEN 'zebrafish 斑马鱼 ' ELSE '' END) ||
        (CASE WHEN LOWER(COALESCE(organism,'')) LIKE '%macaca%' THEN 'monkey 猕猴 猴 ' ELSE '' END) ||
        (CASE WHEN LOWER(COALESCE(organism,'')) LIKE '%scrofa%' THEN 'pig 猪 ' ELSE '' END) ||
        (CASE WHEN LOWER(COALESCE(organism,'')) LIKE '%canis%' THEN 'dog 犬 ' ELSE '' END) ||
        (CASE WHEN LOWER(COALESCE(organism,'')) LIKE '%oryctolagus%' THEN 'rabbit 兔 家兔 ' ELSE '' END)
    ) WHERE rel_path = ?
"""


def resolve_root(cli_root=None):
    """扫描根：--root 参数 > SOGEN_GEO_ROOT 环境变量 > 当前工作目录。"""
    raw = cli_root or os.environ.get(ROOT_ENV_VAR) or os.getcwd()
    return Path(raw).expanduser().resolve()


def db_path_for(root, cli_db=None):
    """每个扫描根一个独立索引库(根路径取 hash 进文件名)，换目录互不污染。"""
    if cli_db:
        return Path(cli_db).expanduser()
    h = hashlib.sha1(str(root).encode("utf-8")).hexdigest()[:10]
    return CACHE_DIR / f"index-{h}.db"


def _joinable(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if x not in (None, ""))
    return str(v)


def _bool_int(v):
    return 1 if v is True else 0


def _connect(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")  # 读不阻塞写、写不阻塞读——目录可能有并发会话在改
    conn.executescript(SCHEMA)
    return conn


def _specialty_from_group(group_name):
    """从群名派生专科标签：'SOGEN心血管数据集交流6群' → '心血管6群'。
    派生不出来就返回 ''，调用方回退到路径提示。"""
    if not group_name:
        return ""
    s = re.sub(r"^SOGEN", "", group_name.strip())
    return s.replace("数据集交流", "").strip()


def _classify(rel_path, is_master_root):
    """桶文件相对路径 → (status, bucket, 路径提示 specialty)；不是 01-07 桶文件返回 None。
    任意深度任意嵌套都接受——客户怎么存文件是他的自由。状态判定：
      路径经过存档目录                              → 已发送
      扫描根是交付管理目录(见 _collect_files)且不在存档区 → 待发
      其余一切(客户自己的目录)                      → 已发送(在手里就是有)
    """
    if not BUCKET_FILE_RE.match(rel_path.name):
        return None
    parts = rel_path.parts
    bucket = "_".join(rel_path.stem.split("_")[-2:])  # 如 "01_转录组测序"
    if ARCHIVE_DIR_NAME in parts[:-1]:
        status = STATUS_SENT
    elif is_master_root:
        status = STATUS_PENDING
    else:
        status = STATUS_SENT
    # 路径提示 specialty：有上层目录就取第一层(交付管理目录下=专科目录名；
    # 客户自己目录下=他自己建的文件夹名)。内容里的 group_name 优先于它(见 _row_values)。
    hint = parts[0] if len(parts) >= 2 else ""
    return status, bucket, hint


def _row_values(info, rel_path, status, bucket, specialty_hint, raw):
    values = {
        "gse_id": raw.get("gse_id", ""),
        "disease": info.get("disease") or "",
        "disease_slug": info.get("disease_slug") or "",
        # specialty 权威来源是文件内容里的群名(客户目录怎么组织不影响)；
        # 文件没带群名时回退到第一层目录名。
        "specialty": _specialty_from_group(info.get("group_name")) or specialty_hint,
        "group_name": info.get("group_name") or "",
        "delivery_status": status, "bucket": bucket,
        "file_name": rel_path.name, "rel_path": str(rel_path),
        "organism": raw.get("organism"), "n_samples": raw.get("n_samples"),
        "platform": _joinable(raw.get("platform")), "pdat": raw.get("pdat"),
        "pubmed_ids": _joinable(raw.get("pubmed_ids")),
        "sequencing_type": _joinable(raw.get("sequencing_type")),
        "sample_source": _joinable(raw.get("sample_source")),
        "title": raw.get("title"), "summary": raw.get("summary"),
        "overall_design": raw.get("overall_design"), "study_design": raw.get("study_design"),
        "relevance_reason": raw.get("relevance_reason"),
        "treatment": _bool_int(raw.get("treatment")), "treatment_type": raw.get("treatment_type"),
        "drug_names": _joinable(raw.get("drug_names")),
        "case_vs_control_differential": _bool_int(raw.get("case_vs_control_differential")),
        "correlation": _bool_int(raw.get("correlation")),
        "pre_post_treatment": _bool_int(raw.get("pre_post_treatment")),
        "survival_analysis": _bool_int(raw.get("survival_analysis")),
        "response": _bool_int(raw.get("response")), "ftplink": raw.get("ftplink"),
    }
    return [values[c] for c in COLUMNS]


def _parse_one(abs_path):
    """读一个桶文件，返回 (文件级信息 dict, 记录 list)。解析失败抛异常，由调用方记账。
    注意坏文件的两类常见形态都必须抛 ValueError 族：截断文件(微信下载中断)切在多字节
    字符中间时 read_text 抛 UnicodeDecodeError；JSON 合法但顶层不是对象(如数组)主动
    判出来——否则会在 data.get 处漏出 AttributeError。"""
    data = json.loads(abs_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"顶层不是 JSON 对象(实际 {type(data).__name__})")
    info = {k: data.get(k) for k in ("group_name", "disease", "disease_slug")}
    rows = [r for r in (data.get("datasets") or []) if isinstance(r, dict)]
    return info, rows


def _index_one_file(conn, abs_path, rel_path, status, bucket, specialty_hint, mtime, parsed=None):
    """(重新)索引单个桶文件：先删该文件的旧行再插入新的。解析失败也在 meta 里记一笔
    (用当前 mtime)，否则同一个坏文件会在每次调用时被反复尝试解析。"""
    conn.execute("DELETE FROM datasets WHERE rel_path = ?", (str(rel_path),))
    try:
        info, rows = parsed if parsed is not None else _parse_one(abs_path)
    except (OSError, ValueError) as e:  # ValueError 族=JSONDecodeError/UnicodeDecodeError/顶层非dict
        print(f"⚠ 跳过无法解析的交付文件 {rel_path}: {e}", file=sys.stderr)
        conn.execute("INSERT OR REPLACE INTO meta VALUES (?,?,?)", (str(rel_path), mtime, 0))
        return 0
    insert_sql = f"INSERT INTO datasets ({','.join(COLUMNS)}) VALUES ({','.join('?' * len(COLUMNS))})"
    n = 0
    for raw in rows:
        cur = conn.execute(insert_sql, _row_values(info, rel_path, status, bucket, specialty_hint, raw))
        evidence = raw.get("evidence")
        if evidence:
            conn.execute("UPDATE datasets SET evidence = ? WHERE rowid = ?",
                         (json.dumps(evidence, ensure_ascii=False), cur.lastrowid))
        n += 1
    conn.execute(SEARCH_TEXT_SQL, (str(rel_path),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES (?,?,?)", (str(rel_path), mtime, n))
    return n


def _collect_files(scan_root):
    """walk 扫描根(任意深度)，返回 {rel_path: (abs_path, status, bucket, specialty_hint)}。
    只收 01-07 桶 JSON；专题/Excel/7z/txt/其他杂物在文件名正则阶段就排除。"""
    pairs = []
    for root, _, files in os.walk(scan_root):
        for f in files:
            if not BUCKET_FILE_RE.match(f):
                continue
            abs_path = Path(root) / f
            pairs.append((abs_path, abs_path.relative_to(scan_root)))
    # 交付管理目录要双重识别：目录名对 + 目录下确实存在存档区结构(至少一个桶文件
    # 位于存档子目录内)。只看名字会冤枉恰好把文件夹起成同名的客户——他手里全是
    # 已发送。识别不上就按普通客户目录处理(一律已发送)，宁可不区分也不错判。
    is_master = (scan_root.name == MASTER_DIR_NAME
                 and any(ARCHIVE_DIR_NAME in rel.parts[:-1] for _, rel in pairs))
    found = {}
    for abs_path, rel in pairs:
        cls = _classify(rel, is_master)
        if cls:
            found[rel] = (abs_path, *cls)
    return found


# ---------- 压缩包自动解压 ----------
# 客户很可能把群里下载的 .7z/.zip 原样丢进目录、从没解压过。每次调用自动发现压缩包、
# 按内容认出 SOGEN 交付包(成员里有桶 JSON 或嵌套压缩包)、就地解压,再纳入索引。
# 解压发生在桶文件收集之前;已处理过的包按 mtime+size 记账(archives 表),不重复解压。


def _find_archive_tool():
    """.7z/.rar 的解压工具:优先系统 7-Zip(快),其次 py7zr(可选依赖,装了就能用),
    都没有返回 None——调用方给中文安装指引,不静默漏数据。.zip 不需要它(标准库)。"""
    for name in ("7z", "7za", "7zr"):
        p = shutil.which(name)
        if p:
            return ("7z", p)
    for p in (r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe"):
        if os.path.isfile(p):
            return ("7z", p)
    try:
        import py7zr  # noqa: F401 —— 可选依赖:装了就能免系统 7-Zip
        return ("py7zr", None)
    except ImportError:
        return None


def _decode_console(raw):
    """7z 控制台输出:新版是 UTF-8,老 Windows 中文版系统可能是 GBK。"""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gbk", errors="replace")


def _list_ext_members(tool, abs_path):
    """列 .7z/.rar 成员路径(7z 二进制 -slt 或 py7zr);读不了(损坏/不完整)返回 None。"""
    kind, binpath = tool
    if kind == "py7zr":
        try:
            import py7zr
            with py7zr.SevenZipFile(abs_path, "r") as z:
                return z.getnames()
        except Exception:  # py7zr 对坏包抛的异常类型很多,统一按"读不了"处理
            return None
    try:
        proc = subprocess.run([binpath, "l", "-slt", str(abs_path)],
                              capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return [ln[7:] for ln in _decode_console(proc.stdout).splitlines() if ln.startswith("Path = ")]


def _zip_members(zf):
    """zipfile 成员 + 修正后的文件名。Windows 老打包软件不写 UTF-8 标记时,
    中文名会被 zipfile 按 CP437 解码成乱码——回退 GBK 抢救。"""
    out = []
    for zi in zf.infolist():
        name = zi.filename
        if not zi.flag_bits & 0x800:  # 无 UTF-8 标记
            try:
                name = name.encode("cp437").decode("gbk")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        out.append((zi, name))
    return out


def _classify_members(names):
    """成员路径(统一成正斜杠)→ (桶 JSON 成员, 嵌套压缩包成员)。
    两者都为空 = 不相干的压缩包(客户目录里的其他 zip),不碰。"""
    buckets, nested = [], []
    for n in names:
        n = n.replace("\\", "/").rstrip("/")
        base = n.rsplit("/", 1)[-1]
        if BUCKET_FILE_RE.match(base):
            buckets.append(n)
        elif base.lower().endswith(ARCHIVE_EXTS):
            nested.append(n)
    return buckets, nested


def _unsafe_member(name):
    """路径穿越守卫:绝对路径/盘符/.. 段都算异常——防恶意构造的包解压时写出目录外。"""
    p = name.replace("\\", "/")
    return p.startswith("/") or (len(p) > 1 and p[1] == ":") or ".." in p.split("/")


def _dest_for(abs_archive, names):
    """解压目的地:成员全部位于与压缩包同名的顶层目录下 → 就地解(和压缩包并列,
    不多套一层);否则解进 {压缩包stem}/ 子目录,保持客户目录整洁。
    注意有的格式会把"顶层目录"本身也列为成员(py7zr 的 getnames、7z -slt 都会),
    这类目录条目必须先剔除——否则它被当成"根上散文件",目的地会多套一层。"""
    files = set()
    for n in names:
        p = "/".join(x for x in n.replace("\\", "/").split("/") if x not in ("", "."))
        if p:
            files.add(p)
    files = {p for p in files if not any(o != p and o.startswith(p + "/") for o in files)}
    tops = set()
    for p in files:
        parts = p.split("/")
        if len(parts) < 2:
            return abs_archive.parent / abs_archive.stem  # 根上有散文件 → 进同名子目录
        tops.add(parts[0])
    return abs_archive.parent if tops == {abs_archive.stem} else abs_archive.parent / abs_archive.stem


def _safe_member_dest(dest_dir, name):
    target = (Path(dest_dir) / name.replace("\\", "/")).resolve()
    base = Path(dest_dir).resolve()
    return target if target == base or str(target).startswith(str(base) + os.sep) else None


def _extract_zip(abs_path, dest_dir, members):
    try:
        with zipfile.ZipFile(abs_path) as zf:
            for zi, name in members:
                if zi.is_dir():
                    continue
                target = _safe_member_dest(dest_dir, name)
                if target is None:
                    continue  # 外层已拦过异常路径,双保险
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(zi) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
    except (OSError, zipfile.BadZipFile) as e:
        return str(e)
    return None


def _extract_ext(tool, abs_path, dest_dir):
    kind, binpath = tool
    if kind == "py7zr":
        try:
            import py7zr
            with py7zr.SevenZipFile(abs_path, "r") as z:
                z.extractall(path=dest_dir)
            return None
        except Exception as e:
            return str(e)
    try:
        proc = subprocess.run([binpath, "x", "-y", f"-o{dest_dir}", str(abs_path)],
                              capture_output=True, timeout=3600)
    except (OSError, subprocess.TimeoutExpired) as e:
        return str(e)
    if proc.returncode != 0:
        lines = _decode_console(proc.stderr or proc.stdout).strip().splitlines()
        return lines[-1] if lines else f"7z 退出码 {proc.returncode}"
    return None


def _handle_one_archive(abs_path, rel, tool, bucket_names_on_disk, no_tool):
    """识别并解压单个压缩包。返回 (verdict, 桶文件basename集, 错误消息):
    verdict ∈ extracted / already-present / not-delivery;出错时 verdict=None 且不记账
    (下次调用重试并再次提醒)——微信下载中断的半截包是常态,不能记成"已处理"。"""
    suffix = abs_path.suffix.lower()
    try:
        if suffix == ".zip":
            with zipfile.ZipFile(abs_path) as zf:
                members = _zip_members(zf)
                names = [n for _, n in members]
        elif suffix == ".rar" and (not tool or tool[0] != "7z"):
            no_tool.append(str(rel))  # py7zr 不解 rar,必须要 7-Zip
            return None, set(), None
        else:
            if not tool:
                no_tool.append(str(rel))
                return None, set(), None
            names = _list_ext_members(tool, abs_path)
            if names is None:
                return None, set(), f"无法读取压缩包 {rel}(多半是下载中断/文件损坏,重新下载一份丢进来即可)"
            members = None
    except (OSError, zipfile.BadZipFile) as e:
        return None, set(), f"无法读取压缩包 {rel}: {e}(多半是下载中断,重新下载一份丢进来即可)"

    buckets, nested = _classify_members(names)
    if not buckets and not nested:
        return "not-delivery", set(), None
    bucket_bases = {b.rsplit("/", 1)[-1] for b in buckets}
    if bucket_bases and bucket_bases <= bucket_names_on_disk:
        # 客户已经手动解压过(或同内容的另一个包已解过)——不重复解压,也就不会重复计数
        return "already-present", bucket_bases, None
    if any(_unsafe_member(n) for n in names):
        return None, set(), f"压缩包 {rel} 含异常路径,出于安全已跳过——建议重新下载"
    dest = _dest_for(abs_archive=abs_path, names=names)
    print(f"  正在解压 {rel}…", file=sys.stderr)
    err = _extract_zip(abs_path, dest, members) if suffix == ".zip" else _extract_ext(tool, abs_path, dest)
    if err:
        return None, set(), f"解压 {rel} 失败:{err}"
    return "extracted", bucket_bases, None


def _extract_pending_archives(scan_root, conn):
    """发现扫描根里的压缩包(任意深度),识别 SOGEN 交付包并自动解压。
    合集包里有嵌套压缩包(交付侧把整批疾病 .7z 再打成一个合集),逐层解开——
    每轮解压后重新扫描,直到没有新包;10 层是病态嵌套的兜底。返回成功解压的包数。"""
    known = {r[0]: (r[1], r[2]) for r in conn.execute("SELECT rel_path, mtime, size FROM archives")}
    tool = _find_archive_tool()
    no_tool, total_extracted = [], 0
    for _round in range(10):
        pending = []
        for root, _, files in os.walk(scan_root):
            for f in files:
                if not f.lower().endswith(ARCHIVE_EXTS):
                    continue
                ap = Path(root) / f
                try:
                    st = os.stat(ap)
                except OSError:
                    continue
                rel = str(ap.relative_to(scan_root))
                if known.get(rel) != (st.st_mtime, st.st_size):
                    pending.append((ap, rel, st))
        if not pending:
            break
        bucket_names_on_disk = set()
        for root, _, files in os.walk(scan_root):
            bucket_names_on_disk.update(f for f in files if BUCKET_FILE_RE.match(f))
        extracted_this_round = 0
        for ap, rel, st in pending:
            verdict, bucket_bases, err = _handle_one_archive(ap, rel, tool, bucket_names_on_disk, no_tool)
            if err:
                print(f"⚠ {err}", file=sys.stderr)
                continue
            if verdict is None:
                continue  # 缺工具:不记账,统一在最后给安装指引
            conn.execute("INSERT OR REPLACE INTO archives VALUES (?,?,?,?)",
                         (rel, st.st_mtime, st.st_size, verdict))
            known[rel] = (st.st_mtime, st.st_size)  # 同一次调用内不重复处理——
            # 否则合集包每轮都被当"新包"重解,10 轮上限都打不满收敛
            if verdict == "extracted":
                extracted_this_round += 1
                total_extracted += 1
                bucket_names_on_disk |= bucket_bases  # 同轮内另一个包含相同内容 → 判 already-present
                print(f"✓ 已解压 {rel}", file=sys.stderr)
            elif verdict == "already-present":
                print(f"· {rel} 的内容目录里已经有了,不重复解压", file=sys.stderr)
            else:
                print(f"· 跳过 {rel}(里面没有 SOGEN 数据集文件)", file=sys.stderr)
        conn.commit()
        if not extracted_this_round:
            break
    if no_tool:
        uniq = sorted(set(no_tool))
        print(f"\n发现 {len(uniq)} 个 SOGEN 压缩包需要解压({ '、'.join(uniq[:5]) }"
              f"{'等' if len(uniq) > 5 else ''}),但这台电脑上没有解压工具。\n"
              "装一个 7-Zip 就能自动解压(约一分钟,装一次以后都不用管):\n"
              "  Windows: winget install -e --id 7zip.7zip --accept-package-agreements --accept-source-agreements\n"
              "  macOS:   brew install sevenzip\n"
              "  Linux:   sudo apt-get install -y p7zip-full\n"
              "装完重新问一次即可;也可以手动解压这些包丢进目录,效果完全一样。",
              file=sys.stderr)
    return total_extracted


def sync_index(scan_root, db_path, force=False):
    """增量同步：按每个桶文件自己的 mtime 只重新解析变化过的(或已被删除/挪走的)，
    不是"有任何变化就整库重建"。force=True(仅 rebuild 子命令用)清空各表强制全量。
    返回 (重新索引的文件数, 移除的文件数, 解压的压缩包数)——平时应该都是 0 或个位数。"""
    conn = _connect(db_path)
    conn.execute("INSERT OR REPLACE INTO kv VALUES ('root', ?)", (str(scan_root),))
    if force:
        conn.executescript("DELETE FROM datasets; DELETE FROM meta; DELETE FROM archives;")
        known = {}
    else:
        known = dict(conn.execute("SELECT rel_path, mtime FROM meta"))

    # 先处理压缩包(客户可能从没解压过),解压出来的桶文件再走正常收集索引
    n_extracted = _extract_pending_archives(scan_root, conn)

    found = _collect_files(scan_root)
    # 挂载盘(9P/网络盘)上 stat 是逐个 RPC，16 线程把上万文件的 stat 压到秒级
    with ThreadPoolExecutor(max_workers=16) as ex:
        mtimes = list(ex.map(lambda p: os.stat(p).st_mtime, [v[0] for v in found.values()]))
    cur = {str(rel): m for rel, m in zip(found.keys(), mtimes)}

    changed = [rel for rel in found if known.get(str(rel)) != cur[str(rel)]]
    removed = [s for s in known if s not in cur]

    # 并发解析变化文件(挂载盘读也是 RPC)，DB 写入仍串行
    parsed = {}
    if changed:
        def _job(rel):
            abs_path = found[rel][0]
            try:
                return rel, _parse_one(abs_path)
            except (OSError, ValueError) as e:  # 坏文件必须记账进 meta，否则每次调用都崩
                return rel, e
        with ThreadPoolExecutor(max_workers=16) as ex:
            for rel, result in ex.map(_job, changed):
                parsed[rel] = result

    # 大批量重建时打印进度(stderr,不污染数据输出)——首次全量可能上千文件分钟级,
    # 客户盯着黑屏会以为卡死;日常增量(个位数文件)保持安静。
    first_build = not known
    show_progress = len(changed) >= 50
    if show_progress:
        print(f"{'首次建立索引' if first_build else '同步交付文件'}:共 {len(changed)} 个文件,稍等…",
              file=sys.stderr)
    for i, rel in enumerate(changed, 1):
        abs_path, status, bucket, specialty_hint = found[rel]
        result = parsed.get(rel)
        if isinstance(result, Exception):
            conn.execute("DELETE FROM datasets WHERE rel_path = ?", (str(rel),))
            print(f"⚠ 跳过无法解析的交付文件 {rel}: {result}", file=sys.stderr)
            conn.execute("INSERT OR REPLACE INTO meta VALUES (?,?,?)", (str(rel), cur[str(rel)], 0))
            continue
        _index_one_file(conn, abs_path, rel, status, bucket, specialty_hint, cur[str(rel)], parsed=result)
        if show_progress and i % 100 == 0:
            print(f"  索引进行中… {i}/{len(changed)}", file=sys.stderr)
        if i % 500 == 0:
            conn.commit()  # 分批提交：限制 WAL 体积，被 kill 也保住已索引部分

    for rel in removed:
        conn.execute("DELETE FROM datasets WHERE rel_path = ?", (rel,))
        conn.execute("DELETE FROM meta WHERE rel_path = ?", (rel,))

    conn.commit()
    conn.close()
    return len(changed), len(removed), n_extracted


def ensure_index(scan_root, db_path):
    t0 = time.monotonic()
    try:
        n_changed, n_removed, n_extracted = sync_index(scan_root, db_path)
    except sqlite3.OperationalError as e:
        # 另一个并发会话正好也在写索引——不硬失败，就用当前已有的索引查(可能略过期，
        # 好过直接报错卡住对话)。但若连 schema 都还没建出来(首次运行就撞锁)，现有索引
        # 是空壳，查下去只会 traceback——这时友好退出，让用户等并发会话建完再试。
        print(f"WARNING: 索引同步暂时失败({e})，本次用现有索引查询", file=sys.stderr)
        try:
            probe = sqlite3.connect(db_path)
            probe.execute("SELECT 1 FROM datasets LIMIT 1")
            probe.close()
        except sqlite3.OperationalError:
            print("另一个会话正在首次构建索引，索引还没成形——请等它建完(或几秒后重试)。",
                  file=sys.stderr)
            sys.exit(1)
        return
    if n_changed or n_removed or n_extracted:
        # 把索引总量一并报出——"引擎在转"的感知,数字也给客户一个锚点
        conn = sqlite3.connect(db_path)
        n_rows, n_files = conn.execute(
            "SELECT COALESCE(SUM(n_records),0), COUNT(*) FROM meta").fetchone()
        conn.close()
        print(f"✓ 索引已同步 · {n_rows:,} 条记录 / {n_files} 个交付文件"
              f"(更新 {n_changed} · 移除 {n_removed}"
              + (f" · 解压 {n_extracted} 个压缩包" if n_extracted else "")
              + f" · {time.monotonic() - t0:.1f}s)",
              file=sys.stderr)


def search(db_path, keyword=None, disease=None, group=None, organism=None, seqtype=None,
           flag=None, min_samples=None, status=None, limit=20):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    clauses, params = [], []
    if keyword:
        for tok in keyword.lower().split():
            clauses.append("search_text LIKE ?")
            params.append(f"%{tok}%")
    if disease:
        clauses.append("(LOWER(disease) LIKE ? OR LOWER(disease_slug) LIKE ?)")
        d = disease.lower()
        params.extend([f"%{d}%", f"%{d}%"])
    if group:
        clauses.append("(LOWER(specialty) LIKE ? OR LOWER(group_name) LIKE ?)")
        g = group.lower()
        params.extend([f"%{g}%", f"%{g}%"])
    if organism:
        terms = _organism_terms(organism)
        clauses.append("(" + " OR ".join("LOWER(organism) LIKE ?" for _ in terms) + ")")
        params.extend(f"%{t}%" for t in terms)
    if seqtype:
        # 同时匹配记录里的英文测序类型(mRNA-seq/scRNA)和桶文件的中文标签(01_转录组测序)
        clauses.append("(LOWER(sequencing_type) LIKE ? OR LOWER(bucket) LIKE ?)")
        s = seqtype.lower()
        params.extend([f"%{s}%", f"%{s}%"])
    if flag:
        clauses.append(f"{flag} = 1")
    if min_samples is not None:
        clauses.append("n_samples >= ?")
        params.append(min_samples)
    if status:
        clauses.append("delivery_status = ?")
        params.append(status)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    total = conn.execute(f"SELECT COUNT(*) FROM datasets {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM datasets {where} ORDER BY n_samples DESC LIMIT ?", params + [limit]
    ).fetchall()
    conn.close()
    return rows, total


def detail(db_path, gse_ids):
    """按 GSE 号取全部出现位置——同一数据集可能出现在多个群的交付里(客户参加了多个群)，
    每次出现都带自己的交付文件和来源群。"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" for _ in gse_ids)
    rows = conn.execute(
        f"SELECT * FROM datasets WHERE gse_id IN ({placeholders}) ORDER BY specialty, disease",
        gse_ids,
    ).fetchall()
    conn.close()
    return rows


def list_diseases(db_path, keyword):
    """在已索引的交付记录里按疾病名/slug/专科群模糊匹配，按 专科群×疾病×状态 汇总条数。"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    kw = f"%{keyword.lower()}%"
    rows = conn.execute(
        """SELECT specialty, MAX(group_name) group_name, disease, disease_slug,
                  delivery_status, COUNT(*) c
           FROM datasets
           WHERE LOWER(disease) LIKE ? OR LOWER(disease_slug) LIKE ? OR LOWER(specialty) LIKE ?
           GROUP BY specialty, disease, delivery_status
           ORDER BY specialty, disease""",
        (kw, kw, kw),
    ).fetchall()
    conn.close()
    return rows


def stats(db_path, group=None, disease=None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    base, base_params = [], []
    if group:
        base.append("(LOWER(specialty) LIKE ? OR LOWER(group_name) LIKE ?)")
        g = group.lower()
        base_params.extend([f"%{g}%", f"%{g}%"])
    if disease:
        base.append("(LOWER(disease) LIKE ? OR LOWER(disease_slug) LIKE ?)")
        d = disease.lower()
        base_params.extend([f"%{d}%", f"%{d}%"])

    def where_sql(extra=None):
        clauses = list(base) + ([extra] if extra else [])
        return ("WHERE " + " AND ".join(clauses)) if clauses else ""

    total = conn.execute(f"SELECT COUNT(*) FROM datasets {where_sql()}", base_params).fetchone()[0]
    n_diseases = conn.execute(
        f"SELECT COUNT(DISTINCT disease) FROM datasets {where_sql()}", base_params).fetchone()[0]
    n_specialties = conn.execute(
        f"SELECT COUNT(DISTINCT specialty) FROM datasets {where_sql()}", base_params).fetchone()[0]
    by_status = conn.execute(
        f"SELECT delivery_status, COUNT(*) c FROM datasets {where_sql()} "
        f"GROUP BY delivery_status ORDER BY c DESC", base_params,
    ).fetchall()
    by_group = conn.execute(
        f"SELECT specialty, COUNT(*) c, COUNT(DISTINCT disease) d FROM datasets {where_sql()} "
        f"GROUP BY specialty ORDER BY c DESC LIMIT 15", base_params,
    ).fetchall()
    by_bucket = conn.execute(
        f"SELECT bucket, COUNT(*) c FROM datasets {where_sql()} "
        f"GROUP BY bucket ORDER BY bucket", base_params,
    ).fetchall()
    by_organism = conn.execute(
        f"SELECT organism, COUNT(*) c FROM datasets {where_sql()} "
        f"GROUP BY organism ORDER BY c DESC LIMIT 10", base_params,
    ).fetchall()
    flag_counts = {
        f: conn.execute(f"SELECT COUNT(*) FROM datasets {where_sql(f + ' = 1')}", base_params).fetchone()[0]
        for f in RQ_FIELDS
    }
    conn.close()
    return total, n_diseases, n_specialties, by_status, by_group, by_bucket, by_organism, flag_counts


# ---------- 输出排版 ----------
# 客户(零技术背景的医生)会在终端里直接看到这些输出——按产品标准写,不按脚本标准写。
# 只用 Unicode 框线/对齐,不用 ANSI 颜色:Claude Code 管道里 stdout 不是 tty,
# 转义序列有显示成乱码的风险;纯 Unicode 在任何终端都稳。

RULE = "─" * 48
HEAVY = "━" * 48


def _dw(s):
    """显示宽度:东亚全角字符算 2 列,其余算 1——中文表格对齐全靠它。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _pad(s, w):
    return s + " " * max(0, w - _dw(s))


def _clip(s, w):
    """按显示宽度截断,超宽补 …(只用于对齐列宽,别用在要完整引用的长文本上)。"""
    s = s or ""
    if _dw(s) <= w:
        return s
    out, acc = [], 0
    for c in s:
        cw = 2 if unicodedata.east_asian_width(c) in "WF" else 1
        if acc + cw > w - 1:
            break
        out.append(c)
        acc += cw
    return "".join(out) + "…"


def _truncate(s, n=120):
    s = s or ""
    return s if len(s) <= n else s[:n] + f"…(共{len(s)}字符，完整内容用 detail 查)"


def _mini_table(title, rows, name_fn, val_fn, name_cap=26):
    """stats 用的两栏小表:名称列按显示宽度对齐,值列跟在后面。"""
    print(f"\n■ {title}")
    w = min(max((_dw(_clip(name_fn(r), name_cap)) for r in rows), default=0), name_cap)
    for r in rows:
        print(f"  {_pad(_clip(name_fn(r), name_cap), w)}  {val_fn(r)}")


def _print_hints(hints):
    """每次查询输出末尾的「下一步」提示块——让客户永远知道接下来可以问什么。
    内容由本次结果动态生成；Claude 负责挑 2-3 条变成客户可以直接照抄的问句
    (回答方式见 SKILL.md)。最后一行是服务出口：需要更多数据、分析或实验时找群主。"""
    hints = [h for h in hints if h][:4]
    if not hints:
        return
    print("\n" + RULE)
    print("💡 下一步可以这样继续：")
    for h in hints:
        print(f"  · {h}")
    print("  · 没找到想要的，或想做进一步的分析/实验验证：加 SOGEN 群主微信 bioinformaticsboy"
          "——生信+湿实验一站式支持")


def _onboarding_if_empty(db_path, scan_root):
    """空索引友好引导(小白最常见的开局)：一个桶文件都没识别到 / 文件都在但全解析失败 /
    只有压缩包没解压，分别给可执行的指引，然后退出——别让四个子命令各自吐一句干瘪的
    '没有匹配'。"""
    conn = sqlite3.connect(db_path)
    n_files, n_rows = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(n_records),0) FROM meta").fetchone()
    conn.close()
    if n_rows:
        return
    print(f"{HEAVY}\n  SOGEN-GEO v{__version__} · 专科群数据集检索\n{HEAVY}\n")
    n_archives = sum(1 for root, _, files in os.walk(scan_root) for f in files
                     if f.lower().endswith(ARCHIVE_EXTS))
    if n_archives:
        print(f"目录里有 {n_archives} 个压缩包，但还没解压出可用的数据集文件。\n"
              "往上看刚才的提示：缺解压工具就装一个 7-Zip(装完重新问一次,会自动解压)；\n"
              "提示包损坏就回群里重新下载一份丢进来。也可以自己手动解压,效果一样。")
    elif n_files:
        print(f"识别到 {n_files} 个交付文件，但都没能解析(多半是下载中断/文件不完整)。\n"
              f"把对应的 SOGEN_*.json 重新下载一遍、覆盖后再问即可"
              f"(不在群里？加群主微信 bioinformaticsboy 要一份)。")
    else:
        print("这个目录里还没识别到 SOGEN 交付文件(SOGEN_疾病_01~07_测序类型.json)。\n"
              "用法：把群里下载的这些 JSON 文件丢进当前目录(自己建子文件夹分类也行;压缩包\n"
              "不用自己解压,会自动解开)，然后再来问。\n"
              "注意：只下载了汇总 Excel 不算——索引以 7 个分类 JSON 为准(内容与 Excel 一致，不重复计)。\n"
              "文件都是群里陆续发的；想多要病种/数据，找群主问——在群里直接群里问，"
              "不在群里加微信 bioinformaticsboy。")
    sys.exit(0)


def _where_line(row):
    """定位行：用 rel_path(含客户自己建的子目录)而不只是文件名——建了文件夹分类的
    客户靠这个直接找到文件。rel_path 相对他自己的扫描根，天然无内部路径。"""
    src = row['group_name'] or row['specialty'] or '(未标注来源群)'
    # 客户目录里一切必然"已发送",不啰嗦;"待发"只在交付管理目录出现,才值得标出
    tail = f" · {row['delivery_status']}" if row['delivery_status'] == STATUS_PENDING else ""
    return f"    📄 {row['rel_path']} · {src}{tail}"


def _geo_url(gse_id):
    """GEO 数据集主页——对外唯一该给出的链接格式。FTP 原始数据下载链接不输出
    (用户 2026-07-19 拍板:只给数据集主页;要下原始数据从 GEO 页面进,或找群主)。"""
    return f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={gse_id}"


def _json_rows(rows):
    """--format json 的出口:剥掉 ftplink(FTP 不对外)、挂上现成的 geo_url,
    让读 JSON 的 AI 拿到的就是该给的链接,没有可转述错的字段。"""
    out = []
    for r in rows:
        d = dict(r)
        d.pop("ftplink", None)
        d["geo_url"] = _geo_url(d["gse_id"])
        out.append(d)
    return out


def format_record_text(row, idx=None):
    prefix = f"[{idx}] " if idx is not None else ""
    flags_hit = [RQ_LABELS[f] for f in RQ_FIELDS if row[f]]
    n = f"{row['n_samples']:,}" if row['n_samples'] is not None else "?"
    lines = [f"{prefix}{row['gse_id']} · {row['disease']} · {_clip(row['organism'], 40)} · "
             f"{n} 例 · {row['sequencing_type']}"]
    if row["title"]:
        lines.append(f"    标题: {row['title']}")
    if row["study_design"]:
        lines.append(f"    研究设计: {_truncate(row['study_design'])}")
    if flags_hit:
        lines.append(f"    标记: {' · '.join(flags_hit)}")
    if row["treatment"] and (row["treatment_type"] or row["drug_names"]):
        t = " · ".join(x for x in [row["treatment_type"], row["drug_names"]] if x)
        lines.append(f"    治疗: {t}")
    lines.append(_where_line(row))
    lines.append(f"    GEO: {_geo_url(row['gse_id'])}")
    return "\n".join(lines)


DETAIL_FIELDS = [  # (列名, 中文标签)——标签列按显示宽度对齐,长文本(summary 等)不在此列
    ("title", "标题"), ("organism", "物种"), ("n_samples", "样本量"), ("platform", "平台"),
    ("pdat", "发布日期"), ("pubmed_ids", "PubMed"), ("sequencing_type", "测序类型"),
    ("sample_source", "样本来源"), ("study_design", "研究设计"), ("relevance_reason", "相关性研判"),
    ("treatment_type", "治疗类型"), ("drug_names", "药物"),
    # ftplink 刻意不在此列:FTP 原始数据链接不对外输出,只给 GEO 主页(_geo_url)
]


def format_record_detail(row):
    head = f"━━ {row['gse_id']} · {row['disease']} "
    lines = [head + "━" * max(4, 50 - _dw(head))]
    lines.append(f"{_pad('交付文件:', 12)}{row['rel_path']}")
    lines.append(f"{_pad('来源群:', 12)}{row['group_name'] or row['specialty'] or '(未标注)'}")
    if row['delivery_status'] == STATUS_PENDING:  # 客户目录不会出现,只在交付管理目录值得提醒
        lines.append(f"{_pad('状态:', 12)}待发(还没发到群里，别当成已有)")
    lines.append(f"{_pad('GEO 主页:', 12)}{_geo_url(row['gse_id'])}")
    for key, label in DETAIL_FIELDS:
        v = row[key]
        if v in (None, "", 0):
            continue
        if key == "n_samples":
            v = f"{v:,}"
        lines.append(f"{_pad(label + ':', 12)}{v}")
    flags_hit = [RQ_LABELS[f] for f in RQ_FIELDS if row[f]]
    if flags_hit:
        lines.append(f"{_pad('研究标记:', 12)}{' · '.join(flags_hit)}")
    if row["summary"]:
        lines.append(f"{_pad('摘要:', 12)}{row['summary']}")
    if row["overall_design"]:
        lines.append(f"{_pad('整体设计:', 12)}{row['overall_design']}")
    if row["evidence"]:
        try:
            ev = json.loads(row["evidence"])
            lines.append("判定依据: " + json.dumps(ev, ensure_ascii=False, indent=2))
        except (TypeError, ValueError):
            pass
    return "\n".join(lines)


def print_about():
    """客户问"SOGEN 是干什么的/能帮我做什么"时的标准口径(about 子命令)——完整版见
    skill 目录《SOGEN介绍.md》。事实全部对齐交付侧 sogen-group-drop/sogen_brand.py
    (SOGEN_ABOUT 单一事实源):顶刊只写"给…提供过…支持"(不写"合作过"),不暴露标注方法配方。"""
    print(HEAVY)
    print(f"  SOGEN-GEO v{__version__} · 专科群数据集检索")
    print(HEAVY)
    print("""
■ SOGEN(索臻生物科技)是干什么的
  生信分析 + AI 智能分析 + 各类基础湿实验,一站式科研服务——从数据到洞见、从实验到成果。
  您所在的群:SOGEN 按专科运营的数据集交流群(心血管/呼吸胸病/消化/肝胆胰/内分泌代谢/
  神经·精神·脑病/妇产乳腺/血液病学/风湿免疫/泌尿肾脏/运动骨病/皮肤/眼·耳鼻喉·口腔颌面/
  感染·重症·慢创·烧伤等),GEO 标注语料陆续共享、每天发新病种;新进群的老师会拿到
  「之前所有发送结果合集」,不亏。

■ 您手里的文件是什么
  群里收到的 SOGEN_*.json、汇总 Excel(或还没解压的 .7z/.zip)就是"检索语料":把每个病
  GEO 上真正相关的数据集从噪音里捞干净、逐字段标好(样本量/测序类型/研究设计研判/
  6 个研究标记/判定依据)——每个疾病 = 7 个按测序类型分类的 JSON + 1 个汇总 Excel。
  这个检索工具(SOGEN-GEO)在您自己电脑上查它们:找数据集、看详情、聊课题——
  只读本地文件,不联网、不上传;压缩包丢进来不用自己解压,会自动解开。

■ 除了数据,SOGEN 还能帮什么
  · 生信分析 —— 转录组(TransDEA 差异表达/DrugSens 药物敏感/Prognosis 预后/Diagnosis
    诊断标志物/机器学习建模)、单细胞(注释/亚群/细胞通讯/拟时序等 20+ 款)
  · 不会写代码 —— SparkleDB 光热生信云平台,379 个一键工具、不写代码产发表级图
    (www.grswsci.top/analyze)
  · 湿实验验证 —— WB/qPCR/流式/细胞功能/类器官/病理多色/动物模型,千平实验室
  · 测序 —— 自有测序平台 14 大类 85+ 款(单细胞/空间/免疫组库/转录组/宏基因组/蛋白/代谢/表观)
  · 课题合作 —— 团队给 Nature Biotechnology、Nature Cancer、Cancer Discovery、
    Nature Communications 等一区顶刊都提供过生信分析与实验技术支持

■ 联系方式
  群主微信 bioinformaticsboy(本来就在群里的,直接群里找群主也行)
  官网 sogentech.com · 标准化产品站 order.sogentech.com/products
  详细业务介绍见随包的《SOGEN介绍.md》。
""")


def _main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=None,
                    help=f"扫描根目录(默认：当前工作目录；也可用环境变量 {ROOT_ENV_VAR} 指定)。"
                         f"换目录=独立索引，互不污染")
    ap.add_argument("--db", default=None,
                    help="索引库路径(默认：~/.cache/sogen-geo/index-<扫描根hash>.db，一般不用动)")
    sub = ap.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("search", help="关键词/条件检索手里的交付数据集")
    sp.add_argument("keyword", nargs="?", default=None,
                    help="自由关键词(中英文都行：命中疾病名/GEO原文字段/研判字段/专科群/测序桶)")
    sp.add_argument("--disease", help="疾病中文名或 slug 子串(如 胆脂瘤 / cholesteatoma)")
    sp.add_argument("--group", help="专科群子串(参加了多个群时按来源群过滤，如 心血管 / 消化)")
    sp.add_argument("--organism", help="物种子串，如 human / mouse")
    sp.add_argument("--seqtype", help="测序类型子串，中英文都行(如 RNA-seq / scRNA / 单细胞)")
    sp.add_argument("--flag", choices=RQ_FIELDS, help="研究问题标记(预后/疗效/标志物等，见 RQ_LABELS)")
    sp.add_argument("--min-samples", type=int, help="最小样本量")
    sp.add_argument("--status", choices=[STATUS_SENT, STATUS_PENDING],
                    help="按交付状态过滤(自己目录里的文件通常全是已发送，一般用不到)")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--format", choices=["text", "json"], default="text")

    dp = sub.add_parser("detail", help="按 GSE 号取完整记录(含 evidence 判定依据 + 交付文件位置)")
    dp.add_argument("gse_ids", nargs="+")
    dp.add_argument("--format", choices=["text", "json"], default="text")

    dd = sub.add_parser("diseases", help="模糊查找手里的疾病(按 专科群×疾病×状态 汇总)")
    dd.add_argument("keyword")

    st = sub.add_parser("stats", help="聚合统计：看看手里都有什么(状态/专科群/测序桶/物种/研究标记分布)")
    st.add_argument("--group", help="限定到某个专科群")
    st.add_argument("--disease", help="限定到某个疾病")

    sub.add_parser("rebuild", help="强制全量重建索引(平时不需要，其余子命令会自动增量扫描同步；"
                                    "只有怀疑索引损坏、改过 schema、或解压结果被人为删除后才用)")

    sub.add_parser("about", help="SOGEN 是干什么的、除了数据还能帮你做什么(业务介绍，不查数据)")

    args = ap.parse_args()

    if args.command == "about":
        print_about()
        return

    scan_root = resolve_root(args.root)
    db_path = db_path_for(scan_root, args.db)

    if not scan_root.is_dir():
        print(f"扫描根目录不存在：{scan_root}", file=sys.stderr)
        sys.exit(2)

    if args.command == "rebuild":
        n_changed, n_removed, n_extracted = sync_index(scan_root, db_path, force=True)
        print(f"✓ 索引全量重建完成 · {n_changed} 个交付文件已索引、{n_removed} 个移除"
              + (f"、{n_extracted} 个压缩包已解压" if n_extracted else ""))
        print(f"  索引位置: {db_path}")
        return

    ensure_index(scan_root, db_path)
    _onboarding_if_empty(db_path, scan_root)

    if args.command == "search":
        t0 = time.monotonic()
        rows, total = search(db_path, keyword=args.keyword, disease=args.disease, group=args.group,
                             organism=args.organism, seqtype=args.seqtype, flag=args.flag,
                             min_samples=args.min_samples, status=args.status, limit=args.limit)
        elapsed = time.monotonic() - t0
        if args.format == "json":
            print(json.dumps(_json_rows(rows), ensure_ascii=False, indent=2))
            return
        if not rows:
            print("按当前条件没有匹配的数据集。")
            hints = []
            if any([args.flag, args.min_samples, args.seqtype, args.organism, args.group, args.status]):
                hints.append("条件可能卡太严——去掉部分筛选"
                             "(--flag/--min-samples/--seqtype/--organism/--group/--status)重试")
            if args.disease:
                hints.append(f"病名再确认下：diseases \"{args.disease}\" 模糊查相近病种")
            elif args.keyword:
                hints.append("关键词换个更短/更口语的词再试；或按病种找：diseases \"<病名>\"")
            hints.append("放宽后还是没有 = 这个病咱们群里还没发过。可以找群主问："
                         "SOGEN 一直在整理新病种，也许已经有了，或者后续会发到群里")
            _print_hints(hints)
            return
        print(f"共 {total:,} 条匹配 · 显示前 {len(rows)} 条(按样本量从大到小)· 本次检索 {elapsed:.2f}s")
        print(RULE)
        for i, r in enumerate(rows, 1):
            print(format_record_text(r, i))
            print()
        hints = [f"看某条的完整信息(判定依据/治疗方案/样本来源)：detail {rows[0]['gse_id']}"]
        if not args.flag:
            flag_hits = sorted(((f, sum(1 for r in rows if r[f])) for f in RQ_FIELDS),
                               key=lambda x: -x[1])
            top_labels = [RQ_LABELS[f] for f, c in flag_hits[:2] if c]
            if top_labels:
                hints.append(f"按研究目的筛：--flag {flag_hits[0][0]}"
                             f"(本批带「{'」「'.join(top_labels)}」标记的多)")
        if total > len(rows):
            hints.append(f"还有 {total - len(rows)} 条没显示——--limit 50 看更多，或加 --seqtype/--min-samples 缩小")
        _print_hints(hints)

    elif args.command == "detail":
        rows = detail(db_path, args.gse_ids)
        if not rows:
            print("没有找到匹配的 GSE 号(不在当前目录的交付文件里——可能还没收到，可以问群主)")
            return
        if args.format == "json":
            print(json.dumps(_json_rows(rows), ensure_ascii=False, indent=2))
            return
        for r in rows:
            print(format_record_detail(r))
            print()
        found = {r["gse_id"] for r in rows}
        missing = [g for g in args.gse_ids if g not in found]
        if missing:
            print(f"(这些 GSE 不在当前目录交付里：{', '.join(missing)}——可能还没发到群里，找群主问问)")
        hints = [f"这个病还有哪些数据：search --disease \"{rows[0]['disease']}\""]
        flags = [f for f in RQ_FIELDS if rows[0][f]]
        if flags:
            hints.append(f"同研究类型的更多：search --disease \"{rows[0]['disease']}\" --flag {flags[0]}")
        _print_hints(hints)

    elif args.command == "diseases":
        rows = list_diseases(db_path, args.keyword)
        if not rows:
            print(f"当前目录的交付内容里没有找到匹配 '{args.keyword}' 的疾病/专科群。")
            _print_hints([
                "换个更短/更口语的词再试(如 \"乳腺\"、\"肺\"、\"糖尿\")",
                "stats 直接看手里全部病种的分布",
                "确实没有 = 这个病咱们群里还没发过——找群主问问：SOGEN 一直在整理新病种，"
                "也许已经有了，或者后续会发",
            ])
            return
        print(f"找到 {len(rows)} 组匹配(专科群 × 疾病)：")
        names = [(r["disease"] or "") + (f" ({r['disease_slug']})" if r["disease_slug"] else "")
                 for r in rows]
        w = min(max((_dw(n) for n in names), default=0), 40)
        cur_specialty = None
        for r, name in zip(rows, names):
            if r["specialty"] != cur_specialty:
                cur_specialty = r["specialty"]
                print(f"\n  【{r['group_name'] or cur_specialty or '(未标注来源群)'}】")
            # 客户目录里必然"已发送",不标;"待发"只在交付管理目录出现才值得提醒
            status_txt = f"{r['delivery_status']} · " if r['delivery_status'] == STATUS_PENDING else ""
            print(f"    {_pad(_clip(name, 40), w)}  {status_txt}{r['c']:,} 条记录")
        top = max(rows, key=lambda r: r["c"])
        _print_hints([
            f"看「{top['disease']}」的底数：stats --disease \"{top['disease']}\"",
            f"直接找它的数据集：search --disease \"{top['disease']}\"",
        ])

    elif args.command == "stats":
        total, n_diseases, n_specialties, by_status, by_group, by_bucket, by_organism, flag_counts = \
            stats(db_path, group=args.group, disease=args.disease)
        scope_parts = []
        if args.group:
            scope_parts.append(f"专科群 {args.group}")
        if args.disease:
            scope_parts.append(f"疾病 {args.disease}")
        scope = " · ".join(scope_parts) if scope_parts else "当前目录全部交付内容"
        print(HEAVY)
        print(f"  SOGEN-GEO v{__version__} · 专科群数据集检索")
        print(HEAVY)
        print(f"\n  范围: {scope}")
        print(f"  总量: {total:,} 条记录 · {n_diseases} 个病种 · {n_specialties} 个专科群")
        if not total:
            print("\n(当前目录下还没索引到交付文件——确认 SOGEN_*_01_*.json 这类文件是不是放在这个目录里)")
            return
        has_pending = any(r['delivery_status'] == STATUS_PENDING for r in by_status)
        if has_pending:
            # 客户目录里一切必然"已发送"(在手里就是有),这一节只在交付管理目录
            # 检出"待发"文件时才出现——只展示携带信息的状态。
            _mini_table("发送状态(已发送=手里已有；待发=还没发到群里)", by_status,
                        lambda r: r['delivery_status'], lambda r: f"{r['c']:,}")
        _mini_table(f"专科群分布(前 {len(by_group)})", by_group,
                    lambda r: r['specialty'] or '(未标注来源群)',
                    lambda r: f"{r['c']:,} 条 · {r['d']} 个病种")
        _mini_table("测序桶分布(交付文件名的 01-07 分类)", by_bucket,
                    lambda r: r['bucket'], lambda r: f"{r['c']:,}")
        _mini_table("物种分布(前 10)", by_organism,
                    lambda r: r['organism'] or '(未标注)', lambda r: f"{r['c']:,}", name_cap=30)
        _mini_table("研究标记命中数", RQ_FIELDS,
                    lambda f: RQ_LABELS[f], lambda f: f"{flag_counts[f]:,}")
        hints = []
        if not args.disease and not args.group:
            conn = sqlite3.connect(db_path)
            top_diseases = [r[0] for r in conn.execute(
                "SELECT disease FROM datasets GROUP BY disease ORDER BY COUNT(*) DESC LIMIT 3")]
            conn.close()
            if top_diseases:
                hints.append(f"钻进某个病种看细节：stats --disease \"{top_diseases[0]}\""
                             f"(或 search --disease \"{top_diseases[0]}\" 直接找数据集)")
            hints.append("不确定病名怎么写：diseases \"<关键词>\" 模糊定位")
        else:
            scope_arg = " ".join(x for x in (f"--group \"{args.group}\"" if args.group else "",
                                             f"--disease \"{args.disease}\"" if args.disease else "")
                                 if x)
            if args.disease and total < 50:
                hints.append(f"这个病目前有 {total} 条——想做课题的话，可以找群主问问"
                             f"有没有更多数据或相近病种")
            for f in ("treatment", "survival_analysis", "case_vs_control_differential"):
                if flag_counts[f]:
                    hints.append(f"筛出带「{RQ_LABELS[f]}」的 {flag_counts[f]} 条："
                                 f"search {scope_arg} --flag {f}".replace("  ", " "))
                    break
            hints.append(f"直接列出数据集：search {scope_arg}".strip())
        _print_hints(hints)


def main():
    """全局兜底:绝不把 Python traceback 露给客户(零技术背景的医生)——一律翻成人话 +
    可执行的下一步。traceback 一出现,医生对工具的信任就崩了。"""
    try:
        _main()
    except SystemExit:
        raise  # argparse/主动退出的正常通道
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        sys.exit(130)
    except (OSError, sqlite3.Error, ValueError) as e:
        # 环境类常见问题(缓存目录不可写/索引损坏/读到半截文件)
        print(f"\n检索工具出了点问题:{e}\n"
              "先原样再试一次;还出现就重建索引:\n"
              "  python3 search_datasets.py rebuild\n"
              "依然不行 → 截图发给群主(微信 bioinformaticsboy),说明刚才输入了什么。",
              file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # 意料之外的 bug 同样兜底
        print(f"\n检索工具出了点意外({type(e).__name__}):{e}\n"
              "先原样再试一次;还出现就重建索引:\n"
              "  python3 search_datasets.py rebuild\n"
              "依然不行 → 截图发给群主(微信 bioinformaticsboy),说明刚才输入了什么。",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
