# SOGEN_data

SOGEN_data 是由 **索臻生物科技（SOGEN）**整理的妇产科与乳腺疾病相关 **GEO 公共数据集标注库**。

本仓库按疾病、测序类型和研究场景，对 GEO Series（GSE）进行结构化整理，并补充研究设计、样本来源、测序类型、可支持的分析方向及人工核验依据，便于研究者快速筛选候选公共数据集、设计生物信息学课题或建立数据分析队列。

> **重要说明**：本仓库保存的是公共数据集的索引、元数据与人工标注结果，不包含 GEO 原始表达矩阵、测序原始文件或完整临床数据。实际分析前仍需前往 GEO、SRA、PubMed 等原始来源下载数据并复核研究设计。

## 当前收录疾病

仓库目前包含以下 8 个疾病或研究主题目录：

- 乳腺癌
- 三阴性乳腺癌
- 男性乳腺癌
- 卵巢癌
- 子宫内膜癌
- 宫颈癌
- 妊娠期糖尿病
- 女性不孕

每个疾病目录通常包含：

- 7 个按测序或组学类型划分的 JSON 文件；
- 5 个按研究场景划分的专题 JSON 文件；
- 1 个便于人工浏览的数据集清单 Excel 文件。

## 仓库结构

```text
SOGEN_data/
├── 乳腺癌/
├── 三阴性乳腺癌/
├── 男性乳腺癌/
├── 卵巢癌/
├── 子宫内膜癌/
├── 宫颈癌/
├── 妊娠期糖尿病/
├── 女性不孕/
└── README.md
```

各疾病目录采用统一的文件命名规则：

```text
<疾病名称>/
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

## 文件分类说明

### 按测序或组学类型分类

| 编号 | 文件类别 | 主要内容 |
|---|---|---|
| 01 | 转录组测序 | bulk RNA-seq、mRNA-seq 等转录组测序数据 |
| 02 | 转录组芯片 | 基因表达芯片及其他转录组微阵列数据 |
| 03 | 单细胞/单核 | scRNA-seq、snRNA-seq 及相关单细胞数据 |
| 04 | 表观基因组学 | DNA 甲基化、ATAC-seq、ChIP-seq 等数据 |
| 05 | 非编码 RNA | miRNA、lncRNA、circRNA、small RNA 等数据 |
| 06 | 其他/长尾 | 蛋白组、代谢组、免疫组库及其他不属于前述类别的数据 |
| 07 | 空间转录组 | Visium、GeoMx、Stereo-seq 等空间表达数据 |

### 按研究场景分类

| 专题 | 主要筛选方向 |
|---|---|
| 差异表达 | 具备病例与对照或其他明确分组，可能支持差异分析的数据集 |
| 治疗干预 | 包含药物、手术、放疗、干预前后或疗效分组的数据集 |
| 相关性 | 可能支持基因表达与临床变量、表型或连续变量相关分析的数据集 |
| 免疫浸润 | 适合免疫微环境、免疫细胞构成或免疫相关表达研究的数据集 |
| 液体活检 | 血液、血清、血浆、外泌体及其他体液样本相关数据集 |

> **不要将专题文件与 7 个测序类型文件直接相加。** 两者是同一批数据的不同组织维度，一个 GSE 可以同时出现在测序类型文件和一个或多个专题文件中，专题之间也可能存在重叠。

## JSON 数据结构

### 顶层字段

不同文件的顶层字段会根据“测序类型文件”或“专题文件”略有差异，常见字段包括：

| 字段 | 含义 |
|---|---|
| `brand` | 数据整理品牌，通常为 `SOGEN` |
| `group_name` | 对应的数据交流或更新群名称 |
| `disease` | 疾病名称 |
| `disease_slug` | 疾病英文标识 |
| `category` | 测序或组学类别 |
| `category_note` | 类别补充说明 |
| `topic` | 专题名称 |
| `topic_field` | 专题英文字段名 |
| `note` | 专题文件的用途及与其他文件的关系说明 |
| `generated_at` | 当前文件生成或更新日期 |
| `n_datasets` | 文件内收录的数据集数量 |
| `organism_breakdown` | 物种构成统计 |
| `research_question_breakdown` | 可支持研究问题的数量统计 |
| `sequencing_type_breakdown` | 专题文件内测序类型构成统计 |
| `datasets` | 数据集记录数组 |

JSON 中部分以下划线开头、名称带随机字符的字段用于保存来源、署名或版本说明，例如 `_0802ff4a`。编写解析程序时，建议只读取明确需要的标准字段，并允许忽略未知字段，避免依赖这些随机字段名。

### 单个数据集的常见字段

| 字段 | 含义 |
|---|---|
| `gse_id` | GEO Series 编号 |
| `title` | GEO 数据集英文标题 |
| `organism` | 物种 |
| `n_samples` | GEO 样本条目数量 |
| `platform` | GEO Platform 编号或平台标识 |
| `pdat` | GEO 发布或更新日期 |
| `pubmed_ids` | 关联 PubMed 文献编号 |
| `sequencing_type` | 标注后的测序或检测类型 |
| `sample_source` | 样本来源，如 tissue、blood、cell line 等 |
| `summary` | GEO 原始研究摘要 |
| `overall_design` | GEO 原始总体实验设计 |
| `study_design` | 中文概括的核心研究设计 |
| `relevance_reason` | 与目标疾病相关的判定依据 |
| `treatment` | 是否存在治疗或干预设计 |
| `treatment_type` | 干预类型 |
| `drug_names` | 涉及的药物名称 |
| `case_vs_control_differential` | 是否可能支持病例与对照差异分析 |
| `correlation` | 是否可能支持相关性分析 |
| `pre_post_treatment` | 是否包含干预前后设计 |
| `survival_analysis` | 是否具有可识别的生存分析条件 |
| `response` | 是否具有疗效或应答分组 |
| `verified` | 当前记录是否经过人工核验 |
| `ftplink` | GEO FTP 数据目录 |
| `evidence` | 各项判定的详细证据与解释 |

`evidence` 通常进一步包含：

- `relevant`
- `sequencing_type`
- `sample_source`
- `case_vs_control_differential`
- `correlation`
- `treatment`
- `survival_analysis`
- 其他与具体文件有关的判定依据

## 使用方式

### 1. 克隆仓库

```bash
git clone https://github.com/Hawyoo/SOGEN_data.git
cd SOGEN_data
```

本仓库为私有仓库时，需要使用具有访问权限的 GitHub 账号或访问令牌。

### 2. 使用 R 读取 JSON

```r
library(jsonlite)
library(dplyr)
library(tibble)

json_file <- "乳腺癌/SOGEN_乳腺癌_专题_液体活检.json"

# flatten = TRUE 会将 evidence 等嵌套对象尽可能展开为数据框列
obj <- fromJSON(json_file, flatten = TRUE)

datasets <- as_tibble(obj$datasets)

# 查看文件级信息
obj$disease
obj$topic
obj$generated_at
obj$n_datasets

# 查看部分核心字段
datasets %>%
  select(
    gse_id,
    title,
    organism,
    n_samples,
    sequencing_type,
    verified,
    case_vs_control_differential,
    correlation,
    survival_analysis
  ) %>%
  print(n = 20)
```

### 3. 根据条件筛选候选数据集

例如，筛选已经核验、来源于人类且可能支持病例与对照差异分析的数据集：

```r
candidate_datasets <- datasets %>%
  filter(
    organism == "Homo sapiens",
    verified %in% TRUE,
    case_vs_control_differential %in% TRUE
  ) %>%
  arrange(desc(n_samples))

candidate_datasets %>%
  select(gse_id, title, n_samples, sequencing_type, study_design)
```

筛选可能含治疗或疗效信息的数据集：

```r
treatment_datasets <- datasets %>%
  filter(
    treatment %in% TRUE |
      pre_post_treatment %in% TRUE |
      response %in% TRUE
  )
```

筛选可能支持生存分析的数据集：

```r
survival_datasets <- datasets %>%
  filter(
    verified %in% TRUE,
    survival_analysis %in% TRUE
  )
```

### 4. 读取 Excel 清单

每个疾病目录中的 `数据集清单.xlsx` 适合直接浏览、筛选和整理课题候选数据集。

```r
library(readxl)

excel_file <- "乳腺癌/SOGEN_乳腺癌_数据集清单.xlsx"
excel_data <- read_excel(excel_file)
```

## 推荐工作流程

1. 根据疾病目录确定研究范围；
2. 根据测序类型文件选择数据平台；
3. 根据专题文件快速筛选研究设计；
4. 阅读 `study_design`、`relevance_reason` 和 `evidence`；
5. 打开 GEO 原始页面及关联文献复核样本信息；
6. 下载表达矩阵、原始数据和样本注释；
7. 在正式分析前重新核对分组、患者数量、重复样本和临床变量。

## 使用注意事项

### 1. 标注结果用于筛选，不替代原始数据核查

仓库中的布尔字段和证据说明适合用于候选数据集初筛，但不能替代对 GEO Series、GSM 样本信息、补充材料和原始论文的完整阅读。

### 2. `n_samples` 不一定等于独立患者数

GEO 中一个患者可能对应多个组织、多个时间点、多个区域或多个技术重复。因此：

- 不能仅根据 `n_samples` 判断统计效能；
- 相关性分析应核对独立患者数量；
- 单细胞和空间转录组应区分样本数、切片数、区域数和细胞数；
- 配对设计应确认患者配对关系。

### 3. `false` 不等于绝对不可分析

某个分析标记为 `false`，通常表示按照当前核验标准未发现充分条件，或 GEO 公开元数据不足，并不代表结合论文补充材料、作者数据或重新整理临床信息后绝对无法进行该分析。

### 4. 专题数据存在重复

同一个 GSE 可同时属于差异表达、免疫浸润、治疗干预、相关性或液体活检等多个专题。合并文件时应使用 `gse_id` 去重。

```r
all_datasets <- bind_rows(dataset_list) %>%
  distinct(gse_id, .keep_all = TRUE)
```

### 5. 数据库会持续变化

GEO 记录、关联文献和样本注释可能更新。请结合文件中的 `generated_at` 判断标注版本，并在正式使用前再次访问原始数据库确认。

### 6. 原始数据遵循原数据库规定

本仓库对 GEO 公开信息进行结构化整理。原始数据、论文和补充材料的使用仍应遵守 NCBI GEO、SRA、PubMed、原作者及期刊的相关条款。

## 数据来源

- NCBI Gene Expression Omnibus（GEO）：https://www.ncbi.nlm.nih.gov/geo/
- NCBI Sequence Read Archive（SRA）：https://www.ncbi.nlm.nih.gov/sra
- PubMed：https://pubmed.ncbi.nlm.nih.gov/

## 署名、授权与联系

本数据集由 **索臻生物科技 SOGEN** 标注整理并共享。使用、转发或基于本仓库整理衍生清单时，请保留 SOGEN 来源与署名，不要删除或隐藏数据文件内已有的来源和授权说明。

本仓库当前未单独提供标准开源许可证文件；具体使用要求以各 JSON 文件内嵌的“使用授权”与“声明”为准。

- SOGEN 官网：https://www.sogentech.com/
- 科研合作与增量数据咨询：微信 `bioinformaticsboy`

## 引用建议

若本仓库对研究课题筛选或数据集整理有实质帮助，可在方法、补充材料或数据可用性部分说明：

> GEO candidate datasets were screened using the SOGEN_data curated annotation repository, followed by manual verification of the original GEO records and associated publications.

同时，请优先引用实际纳入分析的 GEO 数据集原始论文及其数据库编号。
