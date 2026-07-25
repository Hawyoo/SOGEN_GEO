# SOGEN_GEO

> 面向乳腺疾病、妇产疾病及神经精神脑病研究的 GEO 公共数据集结构化标注仓库。仓库原名为 `SOGEN_data`。

本仓库用于帮助研究者和 AI 快速定位候选 GSE、理解研究设计，并初步判断数据可能支持的分析方向。仓库主要保存结构化 JSON 标注和便于人工浏览的 XLSX 清单，不包含原始表达矩阵、原始测序文件或完整临床数据。

---

## AI_READER_PROTOCOL

```yaml
repository_name: SOGEN_GEO
repository_role: GEO_dataset_annotation_index
primary_consumer: AI_agent_and_researcher
primary_data_format: JSON
secondary_data_format: XLSX
raw_omics_data_included: false
clinical_data_complete: false
annotation_is_final_evidence: false

codex_project_instructions: AGENTS.md
codex_installed_skill: sogen-geo
codex_explicit_invocation: $sogen-geo
skill_source_directory: skill/

top_level_disease_categories:
  - 乳腺疾病
  - 妇产疾病
  - 神经精神脑病

reading_order:
  - read_AGENTS_md
  - invoke_sogen_geo_skill_for_dataset_tasks
  - scan_repository_root
  - select_top_level_category
  - select_disease_directory
  - inspect_target_file_state
  - read_numbered_JSON_for_omics_type
  - read_topic_JSON_for_research_design
  - join_records_by_gse_id
  - preserve_source_paths
  - deduplicate_by_gse_id
  - verify_with_GEO_publication_and_sample_metadata
```

强制规则：

- 根目录当前包含 `乳腺疾病/`、`妇产疾病/` 和 `神经精神脑病/` 三个疾病数据类别。
- 根目录 `skill/` 保存 `sogen-geo` skill 的源文件和安装说明，不是疾病目录，不得纳入疾病数量统计或数据集筛选。
- 在 Codex 中执行数据集检索、GSE 查询、数据盘点、课题可行性判断或基于仓库数据设计课题时，应先遵循根目录 `AGENTS.md` 并调用已安装的 `$sogen-geo`。
- 编号 JSON 用于按组学或检测类型筛选；专题 JSON 用于按研究问题筛选。
- 同时需要组学类型和研究设计时，应读取两类文件并按 `gse_id` 关联。
- 同一 GSE 可能同时存在于多个文件中，合并时必须去重并保留原始来源路径。
- 仓库标注仅用于候选初筛，不得直接解释为数据已经下载、质量已经验证或分析可以直接运行。
- 新增目录中可能存在零字节文件或合法但 `datasets == []` 的 JSON，必须先检查文件状态，再判断是否包含候选记录。

## Codex 与 sogen-geo skill

### 自动调用机制

README 是仓库说明文档，不是 Codex 的强制路由文件。为了让 Codex 在进入本仓库后优先使用已安装的 skill，仓库根目录提供：

```text
AGENTS.md
```

`AGENTS.md` 要求 Codex 在处理以下任务时，优先调用已安装的 `$sogen-geo`：

- “帮我找 XX 疾病的数据集”；
- “这个仓库有没有关于 XX 的数据”；
- “查一下某个 GSE”；
- “看看仓库里都有什么数据”；
- 按疾病、基因、物种、样本类型、测序类型或研究设计筛选数据；
- 判断现有数据能否支持某个研究方向；
- 基于仓库中的真实数据设计课题；
- 询问 SOGEN 或 SOGEN-GEO 能做什么。

### 安装要求

Codex 中安装后的 skill 名称必须为小写：

```text
sogen-geo
```

推荐安装位置：

```text
macOS/Linux: ~/.codex/skills/sogen-geo/
Windows:     %USERPROFILE%\.codex\skills\sogen-geo\
```

安装和 frontmatter 调整方法见：

```text
skill/CODEX安装.md
```

安装后可通过自然语言自动匹配，也可显式调用：

```text
$sogen-geo
```

### 调用边界

以下纯仓库维护任务不需要调用 skill：

- 修改 README 或 AGENTS；
- 调整目录结构；
- 修改 JSON schema、标注逻辑或生成脚本；
- 修改 GitHub Actions；
- 文件重命名、格式整理等机械操作。

当维护任务同时包含数据集检索、GSE 选择或研究可行性判断时，对检索和解释部分仍应调用 `$sogen-geo`。

## 当前目录结构

```text
SOGEN_GEO/
├── AGENTS.md                       # Codex 项目级指令和 skill 路由规则
├── README.md
├── skill/                          # sogen-geo skill 源文件与安装说明
│   ├── SKILL.md
│   ├── search_datasets.py
│   ├── requirements.txt
│   ├── CODEX安装.md
│   ├── 使用说明.md
│   └── SOGEN介绍.md
├── 乳腺疾病/
│   ├── 三阴性乳腺癌/
│   ├── 乳腺癌/
│   ├── 导管原位癌/
│   ├── 炎性乳腺癌/
│   └── 男性乳腺癌/
├── 妇产疾病/
│   ├── 反复种植失败/
│   ├── 宫颈上皮内瘤变/
│   └── 其他妇产疾病目录/
└── 神经精神脑病/
    └── 多个神经系统、精神心理及脑疾病目录/
```

> 上述目录树重点展示顶层结构和本次新增目录。完整疾病目录应以仓库当前实际路径为准，并优先通过 `$sogen-geo` 或 `skill/search_datasets.py` 检索，不建议依赖 README 中的静态枚举完成全库盘点。

## 本次新增内容

最新数据提交已确认新增以下目录：

### 乳腺疾病

- `乳腺疾病/炎性乳腺癌/`

该目录包含转录组测序、转录组芯片、单细胞/单核、表观基因组学、非编码 RNA、其他长尾，以及免疫浸润、差异表达、治疗干预、液体活检、相关性等专题标注文件和 XLSX 清单。

### 妇产疾病

- `妇产疾病/反复种植失败/`
- `妇产疾病/宫颈上皮内瘤变/`

`反复种植失败/` 已包含编号 `01`–`07` 中的多类组学文件及多个专题文件；`宫颈上皮内瘤变/` 已包含转录组、表观基因组学、非编码 RNA、其他长尾及相关专题文件。部分文件可能为空，使用前必须检查文件状态。

### 神经精神脑病

仓库新增 `神经精神脑病/` 顶层目录，当前已确认包含的疾病目录包括但不限于：

- `ICU谵妄/`
- `MOG抗体相关疾病/`
- `不宁腿综合征/`
- `中枢神经系统孤立性纤维瘤/`
- `中枢神经细胞瘤/`
- `产后抑郁/`
- `亨廷顿病/`
- `偏头痛/`
- `创伤后应激障碍/`
- `创伤性脑损伤/`
- `卒中/`
- `原发性中枢神经系统血管炎/`
- `原发性震颤/`
- `双相障碍/`
- `可卡因使用障碍/`
- `吉兰-巴雷综合征/`
- `周围神经病/`
- `囊虫病、脑囊虫病/`
- `多发性硬化/`
- `失眠/`
- `孤独症谱系障碍/`
- `帕金森病/`
- `强迫症/`
- `慢性炎性脱髓鞘性多发性神经病/`
- `抑郁症/`
- `智力障碍/`
- `正常压力脑积水/`
- `焦虑障碍/`
- `物质使用障碍/`
- `特发性颅内高压/`

该清单是最新提交中已确认的目录示例，不作为神经精神脑病目录的永久完整枚举。新增批次中有相当一部分文件为零字节占位文件，因此目录存在并不等于已有可用候选 GSE。

## 疾病分类概览

### 乳腺疾病

当前明确包括：

- `乳腺疾病/三阴性乳腺癌/`
- `乳腺疾病/乳腺癌/`
- `乳腺疾病/导管原位癌/`
- `乳腺疾病/炎性乳腺癌/`
- `乳腺疾病/男性乳腺癌/`

### 妇产疾病

原有妇产疾病目录继续保留，本次新增：

- `妇产疾病/反复种植失败/`
- `妇产疾病/宫颈上皮内瘤变/`

完整妇产疾病清单请以仓库实际目录或 skill 检索结果为准。

### 神经精神脑病

该类别为本次新增的大型疾病分类。由于疾病目录数量较多、文件状态差异明显且后续可能持续追加，README 不维护固定数量；AI 和研究者应扫描 `神经精神脑病/` 当前实际目录，并逐文件检查状态。

## 疾病目录内文件规则

每个疾病目录通常按以下模式组织。不同疾病的数据基础不同，因此不保证每个目录均包含全部文件，也不保证每个文件均包含候选记录。

```text
<顶层类别>/<疾病名称>/
├── SOGEN_<疾病名称>_01_转录组测序.json
├── SOGEN_<疾病名称>_02_转录组芯片.json
├── SOGEN_<疾病名称>_03_单细胞单核.json
├── SOGEN_<疾病名称>_04_表观基因组学.json
├── SOGEN_<疾病名称>_05_非编码RNA.json
├── SOGEN_<疾病名称>_06_其他长尾.json
├── SOGEN_<疾病名称>_07_空间转录组.json
├── SOGEN_<疾病名称>_专题_免疫浸润.json
├── SOGEN_<疾病名称>_专题_差异表达.json
├── SOGEN_<疾病名称>_专题_治疗干预.json
├── SOGEN_<疾病名称>_专题_液体活检.json
├── SOGEN_<疾病名称>_专题_相关性.json
└── SOGEN_<疾病名称>_数据集清单.xlsx
```

## 文件语义

### 编号文件

| 编号 | 主要内容 |
|---|---|
| `01_转录组测序` | bulk RNA-seq、mRNA-seq 及其他转录组测序 |
| `02_转录组芯片` | 基因表达芯片、转录组芯片 |
| `03_单细胞单核` | scRNA-seq、snRNA-seq |
| `04_表观基因组学` | DNA 甲基化、ATAC-seq、ChIP-seq 等 |
| `05_非编码RNA` | miRNA、lncRNA、circRNA、small RNA 等 |
| `06_其他长尾` | 蛋白组、代谢组、免疫组库及其他少见类型 |
| `07_空间转录组` | Visium、GeoMx、Stereo-seq 等空间表达数据 |

### 专题文件

| 文件 | 主要研究问题 |
|---|---|
| `专题_差异表达` | 病例与对照、分组间表达差异 |
| `专题_治疗干预` | 药物、治疗、干预或疗效反应 |
| `专题_相关性` | 表达与临床变量或连续变量的相关性 |
| `专题_免疫浸润` | 免疫微环境、免疫细胞浸润及相关研究 |
| `专题_液体活检` | 血液、血清、血浆、羊水、外泌体等体液样本 |

编号文件回答“属于什么组学或检测类型”，专题文件回答“可能支持什么研究问题”；两类文件不是互斥集合。

## 文件状态与证据边界

- `missing`：路径或文件不存在。
- `zero_byte`：文件存在但内容为空。
- `invalid_json`：文件内容无法解析为完整 JSON。
- `valid_json_empty_datasets`：JSON 合法且 `datasets == []`，仅表示当前标注规则下该文件暂无候选记录。
- `valid_json_with_records`：JSON 合法且包含一个或多个候选数据集对象。
- XLSX 文件主要用于人工浏览；AI 解析时优先读取 JSON 中的标准字段和 `datasets` 数组。
- 缺失、零字节、无效 JSON 和空 `datasets` 是不同状态，均不能证明 GEO 中绝对不存在相关研究。
- `n_datasets` 仅表示当前文件中的记录数，不代表唯一 GSE 数、样本数或患者数。
- 最终研究设计必须回到 GEO 原始记录、样本级元数据、关联论文和补充材料进行核验。
- 用户要求最新数据时，应同时检查仓库最新提交、文件生成时间和 GEO 当前记录。

---

## 联系方式

**索臻生物科技 SOGEN**

- 微信：`bioinformaticsboy`
