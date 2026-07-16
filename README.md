# SOGEN_data

SOGEN_data 是一个面向妇产科、乳腺及女性生殖相关疾病研究的 GEO 公共数据集结构化标注仓库。仓库用于帮助 AI 快速定位候选 GSE、理解研究设计、判断可支持的分析方向，并识别进一步复核原始数据时需要关注的限制。仓库不包含原始表达矩阵、原始测序文件或完整临床数据。

---

# AI_READER_PROTOCOL

```yaml
repository_role: GEO_dataset_annotation_index
primary_consumer: AI_agent
primary_data_format: JSON
secondary_data_format: XLSX
raw_omics_data_included: false
clinical_data_complete: false
annotation_is_final_evidence: false
source_of_truth_for_analysis:
  - original_GEO_record
  - sample_level_metadata
  - associated_publication
  - supplementary_materials
repository_index_updated_at: 2026-07-15
```

## 1. REQUIRED_READING_BEHAVIOR

AI 读取本仓库时必须遵循以下顺序：

1. 动态扫描仓库根目录，不得只依赖 README 中的目录清单。
2. 根据用户研究疾病选择对应疾病目录。
3. 根据目标组学类型读取编号为 `01`–`07` 的分类 JSON。
4. 根据目标研究问题读取名称中包含 `专题` 的 JSON。
5. 同时需要组学类型和研究设计时，读取两类文件并按 `gse_id` 关联。
6. 对跨文件结果按 `gse_id` 去重，不得把同一 GSE 重复计数。
7. 优先读取 `datasets` 数组中的标准字段和 `evidence` 对象。
8. 默认忽略名称不稳定的随机下划线字段，不得将其作为筛选条件或固定 schema。
9. 输出候选数据集时，必须区分“仓库标注提示可行”和“经 GEO、论文及样本级信息复核后确认可行”。
10. 不得把仓库标注直接表述为数据已下载、质量已验证、分析可以直接运行或结论已经复现。
11. 当 JSON 的 `datasets` 为空时，只能解释为当前文件没有收录符合该分类规则的记录，不得解释为 GEO 中绝对不存在相关研究。
12. 用户要求“最新数据”时，应同时检查仓库最新提交、文件的 `generated_at` 和 GEO 当前记录。

## 2. REPOSITORY_SCOPE

当前仓库目录包括：

```yaml
disease_directories:
  breast_and_gynecologic_oncology:
    - 乳腺癌
    - 三阴性乳腺癌
    - 男性乳腺癌
    - 卵巢癌
    - 子宫内膜癌
    - 宫颈癌
  reproductive_and_obstetric_diseases:
    - 妊娠期糖尿病
    - 女性不孕
    - 双胎输血综合征
    - 子宫内膜异位症
    - 子痫前期
    - 细菌性阴道病
```

本次目录索引新增：

```yaml
newly_indexed_directories:
  - 双胎输血综合征
  - 子宫内膜异位症
  - 子痫前期
  - 细菌性阴道病
```

上述列表仅用于描述当前仓库快照。疾病目录和文件可能继续增加，实际读取时必须以仓库根目录为准。

## 3. EXPECTED_DIRECTORY_PATTERN

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

并非每个疾病目录都保证包含全部文件，也不保证每个文件的 `datasets` 均非空。遇到缺失或空文件时，应继续读取实际存在的其他分类文件，不得虚构记录。

## 4. FILE_TYPE_SEMANTICS

### 4.1 编号分类文件

```yaml
01_转录组测序:
  intended_scope:
    - bulk_RNA_seq
    - mRNA_seq
    - other_bulk_transcriptome_sequencing

02_转录组芯片:
  intended_scope:
    - gene_expression_microarray
    - transcriptome_array

03_单细胞单核:
  intended_scope:
    - scRNA_seq
    - snRNA_seq
    - related_single_cell_or_single_nucleus_expression_data

04_表观基因组学:
  intended_scope:
    - DNA_methylation
    - ATAC_seq
    - ChIP_seq
    - other_epigenomic_data

05_非编码RNA:
  intended_scope:
    - miRNA
    - lncRNA
    - circRNA
    - small_RNA
    - other_non_coding_RNA_data

06_其他长尾:
  intended_scope:
    - proteomics
    - metabolomics
    - immune_repertoire
    - targeted_assays
    - uncommon_or_unclassified_omics

07_空间转录组:
  intended_scope:
    - spatial_transcriptomics
    - Visium
    - GeoMx
    - Stereo_seq
    - other_spatial_expression_platforms
```

编号分类文件主要回答：**该 GSE 属于什么检测、测序或组学类型。**

### 4.2 专题文件

```yaml
专题_差异表达:
  target_question: 是否存在病例组、对照组或其他明确比较组，可用于组间表达比较

专题_治疗干预:
  target_question: 是否存在药物、放疗、手术或其他干预，以及干预前后或疗效应答设计

专题_相关性:
  target_question: 是否可能支持表达量与临床变量、分期、表型或连续变量的相关分析

专题_免疫浸润:
  target_question: 是否适合研究免疫微环境、免疫细胞构成或免疫相关表达

专题_液体活检:
  target_question: 是否包含血液、血清、血浆、羊水、外泌体或其他体液来源样本
```

专题文件主要回答：**该 GSE 可能支持什么研究问题。**

### 4.3 XLSX 文件

```yaml
xlsx_role: human_readable_dataset_inventory
preferred_for_AI_parsing: false
preferred_AI_source: JSON
```

XLSX 适合人工浏览和快速筛选；AI 进行字段级判断时应优先读取 JSON，并在需要时使用 XLSX 交叉检查。

## 5. CROSS_FILE_RELATIONSHIP

```yaml
numbered_files_mutually_exclusive: usually_but_not_guaranteed
numbered_files_vs_topic_files_mutually_exclusive: false
topic_files_mutually_exclusive: false
same_gse_may_appear_in_multiple_files: true
canonical_cross_file_key: gse_id
```

必须遵守：

- 不得把 7 个编号文件与专题文件中的 `n_datasets` 直接相加作为疾病数据集总数。
- 同一个 GSE 可以同时出现在一个编号文件和多个专题文件中。
- 合并候选结果时以 `gse_id` 为主键去重。
- `n_datasets` 仅表示当前 JSON 的 `datasets` 数组记录数。
- `n_verified_total` 不得默认解释为当前文件的唯一 GSE 数、可分析数据集数或患者数。
- 同一 GSE 在不同文件中字段不一致时，应保留来源文件和冲突信息，不得静默覆盖。

## 6. JSON_TOP_LEVEL_SCHEMA

常见顶层字段如下。字段可能缺失，也可能出现额外字段，解析器必须允许 schema 扩展。

```yaml
brand:
  type: string
  meaning: 数据标识

group_name:
  type: string
  meaning: 数据更新或交流群名称

disease:
  type: string
  meaning: 目标疾病中文名称

disease_slug:
  type: string
  meaning: 目标疾病英文或程序化标识

category:
  type: string
  applies_to: numbered_files
  meaning: 测序或组学类别

category_note:
  type: string
  applies_to: numbered_files
  meaning: 类别补充说明

topic:
  type: string
  applies_to: topic_files
  meaning: 研究专题名称

topic_field:
  type: string
  applies_to: topic_files
  meaning: 专题对应的程序化字段名称

note:
  type: string
  optional: true
  meaning: 文件定位、统计口径或专题重叠说明

generated_at:
  type: date_string
  meaning: 当前标注文件生成或更新日期

n_datasets:
  type: integer
  meaning: 当前 JSON 的 datasets 数组记录数

n_verified_total:
  type: integer
  optional: true
  meaning: 某些专题文件提供的核验规模统计，不得默认等同于 n_datasets

organism_breakdown:
  type: object_string_to_integer
  meaning: 当前文件内物种构成

sequencing_type_breakdown:
  type: object_string_to_integer
  optional: true
  meaning: 当前文件内测序类型构成

research_question_breakdown:
  type: object_string_to_integer
  optional: true
  meaning: 当前文件内研究设计布尔标记汇总

datasets:
  type: array_of_dataset_objects
  meaning: 数据集标注主体
```

### 6.1 非稳定字段

JSON 中可能存在名称类似以下形式的字段：

```text
_<随机字符>
```

这些字段可能承载版本、来源、署名、说明或其他附加信息。AI 默认行为：

```yaml
use_for_dataset_selection: false
use_as_stable_schema_key: false
ignore_when_unknown: true
preserve_when_copying_original_record: true
```

不得编写依赖特定随机下划线字段名称的固定解析逻辑。

## 7. DATASET_OBJECT_SCHEMA

`datasets` 数组中的每个对象通常代表一个 GSE 级记录。

```yaml
gse_id:
  type: string
  expected_pattern: '^GSE[0-9]+$'
  role: canonical_dataset_identifier

title:
  type: string
  source: GEO

organism:
  type: string
  note: 可能包含多个物种或 synthetic construct

n_samples:
  type: integer
  meaning: GEO 样本条目数，不保证等于独立患者或独立供体数

platform:
  type: string_or_integer_or_array

pdat:
  type: date_string
  meaning: GEO 发布或更新日期

pubmed_ids:
  type: array
  empty_allowed: true

sequencing_type:
  type: string
  meaning: 标注后的实际检测或测序类型

sample_source:
  type: array_of_strings
  typical_values:
    - tissue
    - primary_cell
    - blood
    - serum
    - plasma
    - body_fluid
    - cell_line
    - organoid
    - other

summary:
  type: string
  source: GEO

overall_design:
  type: string
  source: GEO

study_design:
  type: string
  meaning: 中文核心设计概括

relevance_reason:
  type: string
  meaning: 数据与目标疾病相关的简要判定理由

treatment:
  type: boolean

treatment_type:
  type: string
  note: 可能存在自由文本或未完全标准化值，不能未经核验直接作为受控词表

drug_names:
  type: string_or_array
  note: 空值不代表关联论文中绝对不存在药物

case_vs_control_differential:
  type: boolean

correlation:
  type: boolean

pre_post_treatment:
  type: boolean

survival_analysis:
  type: boolean

response:
  type: boolean

verified:
  type: boolean
  note: 表示记录经过当前标注流程核验，不代表原始数据和结论已复现

ftplink:
  type: string
  meaning: GEO FTP 目录，可能为 ftp 协议地址

evidence:
  type: object
  meaning: 各判定字段的具体证据、限制和解释
```

字段类型属于宽松约定。AI 必须容忍 `null`、空字符串、缺失字段、单值与数组混用、自由文本和历史格式差异。

## 8. EVIDENCE_PRIORITY

`evidence` 是解释布尔标记和研究设计判定的关键对象。常见子字段包括：

```yaml
evidence.relevant: 疾病主体和样本与目标疾病的对应依据
evidence.sequencing_type: 测序或检测类型的判定依据
evidence.sample_source: 样本来源、分选、培养或直接取材的依据
evidence.case_vs_control_differential: 差异分析可行或不可行的理由
evidence.correlation: 相关性分析可行或不可行的理由
evidence.treatment: 治疗或干预轴的判断依据
evidence.survival_analysis: 生存字段是否存在及能否执行生存分析的依据
evidence.study_design: 可选的设计补充
evidence.relevance_reason: 可选的相关性补充
```

候选筛选时的证据优先级：

```yaml
priority_1: evidence 中的具体说明
priority_2: study_design 和 overall_design
priority_3: summary
priority_4: 数据集级布尔字段
priority_5: 顶层汇总字段
priority_6: 文件名和专题名称
```

布尔字段适合快速检索，`evidence` 适合解释和排除误判。不得只看布尔值而忽略证据文本。

## 9. BOOLEAN_FIELD_INTERPRETATION

### 9.1 `true`

`true` 表示按照当前标注规则发现了支持该分析方向的公开证据。它不保证：

- 原始矩阵可以直接下载；
- 分组数量满足用户的统计要求；
- 所有 GSM 都有完整注释；
- 独立患者数等于 `n_samples`；
- 批次效应可以处理；
- 数据适合作为训练集、验证集或因果证据；
- 用户指定的目标变量一定存在于样本级 metadata 中。

### 9.2 `false`

`false` 表示按照当前公开信息和当前规则未识别到充分条件。可能原因包括：

```yaml
possible_false_reasons:
  - 目标字段不存在或未公开
  - 样本级 metadata 不完整
  - 测序平台不适合该分析
  - 独立患者或供体数不足
  - 对照组不符合当前定义
  - 只有治疗前样本而没有干预比较轴
  - 生存信息只出现在论文汇总结果中
  - 论文提到某分析，但 GEO 数据本身不提供执行条件
```

因此，`false` 应表述为“当前公开标注未确认可行”，不得解释为理论上绝对不可分析。

### 9.3 空 `datasets`

```yaml
empty_datasets_means:
  - 当前文件未收录满足当前分类或专题规则的记录
empty_datasets_does_not_mean:
  - GEO 中绝对不存在相关数据
  - 目标疾病没有任何组学研究
  - 其他分类文件中也一定为空
```

## 10. SAMPLE_COUNT_RULES

`n_samples` 是 GEO 样本条目数量。不得自动解释为：

- 独立患者数；
- 独立供体数；
- 生物学重复数；
- 可用于统计模型的有效样本数；
- 单细胞数据中的细胞数；
- 空间转录组中的 spot 或 ROI 数；
- 配对病例数。

可能造成样本条目数与独立个体数不一致的情况：

```yaml
sample_multiplicity:
  - 同一患者多个组织或病灶
  - 肿瘤与配对正常组织
  - 多个时间点
  - 治疗前后样本
  - 多个空间区域或切片
  - 多个细胞亚群
  - 技术重复
  - 多平台或 SuperSeries/SubSeries 结构
```

涉及最小样本量、相关性、生存分析、机器学习或外部验证时，必须进一步核对独立患者或供体数。

## 11. DATASET_SELECTION_LOGIC

### 11.1 差异表达

```yaml
required_or_preferred:
  - case_vs_control_differential == true
  - verified == true
  - sequencing_type 为表达定量平台
  - evidence 明确说明比较组
  - 独立样本数和重复数可核查
```

不得因为标题含某疾病名称就默认存在健康对照。良性疾病、癌旁组织、健康人、细胞系、动物模型和不同疾病对照不得视为等价对照。

### 11.2 相关性分析

```yaml
required_or_preferred:
  - correlation == true
  - verified == true
  - 存在表达定量数据
  - 存在目标临床变量或连续表型
  - 独立疾病样本数达到用户要求
```

专题文件中的相关性标记不保证用户指定的 BMI、年龄、分期、孕周、疗效等变量存在，必须进一步检查样本级 metadata。

### 11.3 治疗与疗效

```yaml
any_treatment_context:
  condition: treatment == true

paired_or_longitudinal_intervention:
  condition: pre_post_treatment == true

treatment_response_comparison:
  condition: response == true

identified_intervention_fields:
  - treatment_type
  - drug_names
  - evidence.treatment
```

仅有 `pretreatment` 样本时，不得自动认定存在治疗前后比较。`treatment_type` 出现自然语言说明时，应结合 `evidence.treatment` 重新归一化。

### 11.4 生存分析

```yaml
required:
  - survival_analysis == true
  - evidence.survival_analysis 明确指出样本级生存时间和状态可获得
  - 独立患者 ID 可以建立
```

论文使用外部 TCGA 或其他队列做生存验证，不代表当前 GEO 数据集本身可以做生存分析。

### 11.5 单细胞或单核数据

```yaml
check:
  - 独立供体数
  - 每位供体的疾病状态
  - 样本组织或细胞来源
  - 是否为 scRNA-seq 或 snRNA-seq
  - 是否存在多个测序批次
  - 是否提供原始或处理后矩阵
  - 是否提供 sample-level metadata
  - 是否能区分供体而非仅区分细胞
```

不得使用细胞总数替代独立供体数。

### 11.6 空间转录组

```yaml
check:
  - 患者或供体数
  - 切片数
  - ROI 或空间区域数量
  - 平台类型
  - 是否包含明确比较区域
  - 多个区域是否来自同一患者
```

不得将多个 ROI、切片或 spot 当作独立患者进行无层级处理的统计比较。

### 11.7 液体活检和体液样本

```yaml
check:
  - blood_or_body_fluid_type
  - serum_plasma_whole_blood_amniotic_fluid_or_other
  - 被测分子类型
  - 病例和对照定义
  - 是否与组织样本配对
  - 是否存在诊断、分期、复发、转移或疗效目标
```

`sample_source` 为 `blood` 或 `body_fluid` 不代表该记录一定适合无创标志物研究，必须结合检测对象、样本采集方式和研究设计判断。

## 12. DEDUPLICATION_AND_CONFLICT_RULES

### 12.1 去重主键

```yaml
primary_key: gse_id
fallback_key_when_gse_id_missing:
  - title
  - platform
  - pdat
```

正常情况下以 `gse_id` 去重。不要仅以标题去重，因为标题可能变化，也可能存在 SuperSeries/SubSeries。

### 12.2 同一 GSE 多记录合并

```yaml
merged_record:
  gse_id: 唯一编号
  source_files: 所有命中文件路径
  categories: 所有编号分类
  topics: 所有专题分类
  latest_generated_at: 最大日期
  dataset_fields: 选择信息更完整的记录
  evidence_by_source: 按来源文件保留全部 evidence
  conflicts: 显式记录不一致字段
```

### 12.3 字段冲突处理

```yaml
conflict_resolution_order:
  - 不静默覆盖冲突
  - 比较 generated_at
  - 比较 verified
  - 比较 evidence 的具体程度
  - 检查是否由专题筛选语境不同导致
  - 回到 GEO、样本级 metadata 和论文复核
```

较新的文件不必然代表单条记录一定更准确，更新日期只能作为辅助信号。

## 13. SUPER_SERIES_AND_SUBSERIES

遇到 GEO SuperSeries 或 SubSeries 时必须检查：

```yaml
check:
  - 当前 GSE 是否只是索引容器
  - 实际表达矩阵位于哪个 SubSeries
  - 不同 SubSeries 是否对应不同组学平台
  - 样本是否在多个 SubSeries 中重复
  - 研究问题应在 SuperSeries 还是 SubSeries 层面定义
```

不得因为 SuperSeries 的 `n_samples` 较大就默认所有样本属于同一可合并表达矩阵。

## 14. TEMPORAL_AND_VERSION_RULES

```yaml
annotation_version_field: generated_at
external_records_can_change: true
latest_file_is_not_automatic_ground_truth: true
recheck_original_source_before_final_inclusion: required
```

输出时应说明读取的来源文件及其 `generated_at`。用户要求最新数据时，应检查仓库最新提交和 GEO 当前记录，而不是只依赖历史标注。

## 15. AI_OUTPUT_CONTRACT

使用本仓库回答数据集筛选问题时，建议输出：

```yaml
required_output_fields:
  - gse_id
  - title
  - disease
  - sequencing_type
  - organism
  - n_samples_as_GEO_entries
  - estimated_or_verified_independent_subject_count_if_available
  - sample_source
  - study_design
  - relevant_boolean_flags
  - evidence_summary
  - source_file
  - generated_at
  - limitations
  - original_data_recheck_status
```

候选状态必须区分：

```yaml
candidate_status:
  annotated_candidate: 仓库标注提示可能符合
  metadata_checked: 已进一步检查 GEO 样本级 metadata
  publication_checked: 已检查关联论文或补充材料
  analysis_ready: 已确认矩阵、分组、样本量和必要变量可获得
```

除非已经完成相应核查，不得把 `annotated_candidate` 表述为 `analysis_ready`。

## 16. PROHIBITED_INFERENCES

AI 不得仅凭本仓库直接推断：

- 某 GSE 一定可以成功下载全部原始数据；
- 某 GSE 一定含有用户指定的临床变量；
- `n_samples` 等于患者或供体数；
- `case_vs_control_differential == true` 代表存在健康对照；
- `survival_analysis == true` 代表生存字段无缺失；
- `verified == true` 代表数据和结论已经复现；
- 空 `datasets` 代表 GEO 中不存在相关数据；
- 专题文件之间互斥；
- 编号文件和专题文件的数量可以直接相加；
- 动物、细胞系、类器官、原代细胞和人体组织可以无条件合并；
- 不同平台的表达值可以直接合并；
- 同一患者的多个样本可以作为独立个体；
- 论文摘要中的分析一定能由 GEO 公开数据独立重现。

## 17. MINIMUM_RESPONSE_LANGUAGE

使用本仓库回答用户时，优先采用：

```yaml
preferred:
  - 仓库标注显示该数据集可能支持……
  - 当前公开元数据中可识别到……
  - 该 GSE 可作为候选，但仍需核对矩阵、独立样本数、分组和样本级变量……
  - 当前文件的 datasets 为空，表示该分类下暂未收录记录，不代表 GEO 中绝对不存在相关研究……

avoid_without_full_verification:
  - 该数据集一定可以用于……
  - 该数据集包含完整的……
  - 样本量为 n_samples 名患者……
  - 已证明……
```

---

## 联系方式

- 机构：**索臻生物科技 SOGEN**
- 官网：https://www.sogentech.com/
- 科研合作与增量数据咨询：微信 `bioinformaticsboy`
