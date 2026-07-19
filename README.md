# SOGEN_data

SOGEN_data 是面向妇产科、乳腺及女性生殖相关疾病研究的 GEO 公共数据集结构化标注仓库。仓库用于帮助 AI 快速定位候选 GSE、理解研究设计、判断可能支持的分析方向；仓库不包含原始表达矩阵、原始测序文件或完整临床数据。

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
repository_snapshot_date: 2026-07-19
directory_snapshot_is_authoritative: false
source_of_truth_for_final_analysis:
  - original_GEO_record
  - sample_level_metadata
  - associated_publication
  - supplementary_materials
```

## 1. NON_NEGOTIABLE_READING_RULES

AI 读取本仓库时必须遵循：

1. 先动态扫描仓库根目录；README 中的目录清单只是快照，不是永久白名单。
2. 根据用户指定的疾病、组学类型和研究问题选择文件，不得无差别读取后直接混合全部记录。
3. 读取文件前先判断文件是否存在、是否有内容、是否为有效 JSON。
4. 目标组学类型对应编号为 `01`–`07` 的分类 JSON。
5. 目标研究问题对应文件名中包含 `专题` 的 JSON。
6. 同时需要组学类型和研究设计时，读取两类文件并按 `gse_id` 关联。
7. 跨文件、跨专题和跨目录汇总时，默认以 `gse_id` 为主键去重。
8. 优先读取 `datasets` 数组中的标准字段和 `evidence` 对象。
9. 默认忽略名称不稳定的随机下划线字段，不得把它们写入固定 schema 或用作筛选条件。
10. 输出候选数据集时，必须区分“仓库标注提示可能可用”和“已经复核为可直接分析”。
11. 不得把仓库标注直接表述为数据已经下载、质量已经验证、分析能够直接运行或研究结论已经复现。
12. 用户要求“最新数据”时，应同时检查仓库最新提交、文件的 `generated_at` 和 GEO 当前记录。

## 2. CURRENT_DIRECTORY_SNAPSHOT

以下目录存在于 2026-07-19 的仓库快照中：

```yaml
disease_directories:
  breast_and_gynecologic_oncology:
    - 乳腺癌
    - 三阴性乳腺癌
    - 男性乳腺癌
    - 导管原位癌
    - 卵巢癌
    - 子宫内膜癌
    - 宫颈癌
    - 外阴癌

  benign_gynecologic_and_reproductive_disorders:
    - 女性不孕
    - 多囊卵巢综合征
    - 子宫内膜异位症
    - 外阴硬化性苔藓
    - 子宫内膜增生
    - 子宫肌瘤
    - 盆腔炎

  pregnancy_and_perinatal_disorders:
    - 妊娠期糖尿病
    - 双胎输血综合征
    - 子痫前期
    - 围产期心肌病
    - 妊娠期肝内胆汁淤积症
    - 异位妊娠
    - 胎儿生长受限

  infection_related_topics:
    - 细菌性阴道病
    - 寨卡病毒病
    - 风疹
```

目录分类仅用于导航，不代表疾病之间的数据可以合并，也不代表每个目录的数据完整程度相同。实际读取必须以当前仓库根目录和文件内容为准。

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

该模式是预期命名规范，不保证每个目录始终包含全部文件，也不保证每个文件均有候选记录。

## 4. FILE_STATE_MODEL

AI 必须先给每个目标文件分配状态：

```yaml
file_states:
  missing:
    meaning: 目标路径不存在
    action: 记录缺失并继续检查同目录其他文件

  zero_byte:
    meaning: 文件存在但无内容
    action: 不执行 JSON 解析；不得等同于 datasets 为空

  invalid_json:
    meaning: 文件有内容但无法解析为完整 JSON
    action: 标记解析失败；不得从中生成候选数据集

  valid_json_without_datasets:
    meaning: JSON 有效但不存在标准 datasets 数组
    action: 仅使用可识别的文件级信息；不得虚构 datasets

  valid_json_empty_datasets:
    meaning: JSON 有效且 datasets == []
    action: 解释为当前文件未收录符合该分类规则的记录

  valid_json_with_records:
    meaning: JSON 有效且 datasets 包含一个或多个对象
    action: 执行字段解析、筛选、去重和证据评估

  xlsx_present:
    meaning: 存在人工浏览清单
    action: 可用于交叉检查；字段级判断仍优先使用 JSON
```

强制区分：

```yaml
zero_byte_is_empty_dataset: false
missing_file_is_empty_dataset: false
invalid_json_is_empty_dataset: false
valid_empty_dataset_proves_no_GEO_study_exists: false
```

即使某个分类文件为空、缺失或没有记录，也只能说明当前仓库快照未在该文件中提供候选记录，不能据此断言 GEO 中不存在相关研究。

## 5. FILE_TYPE_SEMANTICS

### 5.1 编号分类文件

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

编号文件主要回答：该 GSE 属于什么检测、测序或组学类型。

### 5.2 专题文件

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

专题文件主要回答：该 GSE 可能支持什么研究问题。

### 5.3 XLSX 文件

```yaml
xlsx_role: human_readable_dataset_inventory
preferred_for_AI_field_parsing: false
preferred_AI_source: JSON
```

## 6. CROSS_FILE_RELATIONSHIP

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
- 同一个 GSE 也可能因 SuperSeries、SubSeries 或多组学设计出现在不同组学分类中。
- 合并结果时以 `gse_id` 为主键去重，同时保留全部 `source_files`、`categories` 和 `topics`。
- `n_datasets` 仅表示当前 JSON 的 `datasets` 数组记录数。
- `n_verified_total` 不得解释为唯一 GSE 数、可分析数据集数、样本数或患者数。
- 同一 GSE 在不同文件中字段不一致时，不得静默覆盖。

## 7. JSON_TOP_LEVEL_SCHEMA

字段可能缺失，也可能新增；解析器必须允许 schema 扩展。

```yaml
brand:
  type: string

group_name:
  type: string

disease:
  type: string

disease_slug:
  type: string

category:
  type: string
  applies_to: numbered_files

category_note:
  type: string
  applies_to: numbered_files

 topic:
  type: string
  applies_to: topic_files

 topic_field:
  type: string
  applies_to: topic_files

note:
  type: string
  optional: true

generated_at:
  type: date_string

n_datasets:
  type: integer
  meaning: 当前 JSON 的 datasets 数组记录数

n_verified_total:
  type: integer
  optional: true
  meaning: 文件级核验规模统计，不等同于 n_datasets

organism_breakdown:
  type: object_string_to_integer
  optional: true

sequencing_type_breakdown:
  type: object_string_to_integer
  optional: true

research_question_breakdown:
  type: object_string_to_integer
  optional: true

datasets:
  type: array_of_dataset_objects
  required_for_standard_record_parsing: true
```

### 7.1 不稳定下划线字段

JSON 中可能出现：

```text
_<随机字符>
```

默认策略：

```yaml
use_for_dataset_selection: false
use_as_stable_schema_key: false
ignore_when_unknown: true
preserve_when_copying_original_record: true
```

这些字段可能包含来源、版本、署名、授权、宣传或其他附加信息。不得依赖具体随机字段名建立解析逻辑。

## 8. DATASET_OBJECT_SCHEMA

`datasets` 数组中的对象通常代表 GSE 级记录。

```yaml
gse_id:
  type: string
  role: primary_identifier

title:
  type: string

organism:
  type: string
  note: 可能包含多个物种或 synthetic construct

n_samples:
  type: integer
  meaning: GEO 样本条目数，不等于独立患者数或独立供体数

platform:
  type: string_or_integer_or_array

pdat:
  type: date_string

pubmed_ids:
  type: array
  empty_allowed: true

sequencing_type:
  type: string

sample_source:
  type: string_or_array

summary:
  type: string
  source: GEO

overall_design:
  type: string
  source: GEO

study_design:
  type: string
  meaning: 标注后的核心研究设计概括

relevance_reason:
  type: string
  meaning: 与目标疾病相关的标注依据

treatment:
  type: boolean

treatment_type:
  type: string

drug_names:
  type: string_or_array

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
  meaning: 标注记录经过人工核验，不代表分析结果已复现

ftplink:
  type: string
  meaning: GEO FTP 路径；可访问性仍需重新检查

evidence:
  type: object
  role: field_level_annotation_rationale
```

字段不存在、为空字符串或为 `null` 时，必须输出 `unknown_or_not_provided`，不得自行补全。

## 9. BOOLEAN_AND_EVIDENCE_SEMANTICS

```yaml
boolean_true:
  meaning: 当前标注证据提示可能满足该研究设计
  interpretation: candidate_positive

boolean_false:
  meaning: 当前公开信息或核验标准下未发现充分支持
  interpretation: insufficient_current_evidence
  absolute_impossibility: false

verified_true:
  meaning: 标注条目经过人工检查
  does_not_mean:
    - raw_data_downloaded
    - sample_metadata_complete
    - quality_control_passed
    - analysis_reproduced
    - publication_conclusion_validated
```

证据优先级：

```yaml
annotation_priority:
  - evidence 中针对具体字段的解释
  - study_design
  - relevance_reason
  - overall_design
  - summary
  - 文件级统计字段
```

若布尔字段与 `evidence` 冲突，必须记录冲突并回到 GEO 或关联论文复核，不得只采用更方便的值。

## 10. SAMPLE_COUNT_RULES

`n_samples` 表示 GEO 样本条目数。AI 不得直接将其改写为“患者数”。

必须区分：

```yaml
possible_sampling_units:
  - independent_patient
  - independent_donor
  - tissue_sample
  - paired_tumor_normal_sample
  - longitudinal_timepoint
  - technical_replicate
  - biological_replicate
  - cell_line
  - organoid
  - animal
  - single_cell_library
  - spatial_slide
  - ROI
  - sequencing_run
```

特别规则：

- 单细胞数据不得用细胞总数替代独立供体数。
- 空间转录组不得用 spot、ROI 或切片数替代患者数。
- 同一患者的配对组织、多个时间点或多个区域不得默认视为独立样本。
- 多物种、动物、细胞系、类器官和人体组织不得无条件合并。

## 11. ANALYSIS_CANDIDATE_RULES

### 11.1 差异表达

```yaml
candidate_conditions:
  - case_vs_control_differential == true
  - verified == true preferred
  - 检测平台能够生成可比较的表达定量数据
  - 存在明确且可恢复的比较组
  - 独立生物学重复满足用户要求
```

`case_vs_control_differential == true` 不代表对照一定是健康人；对照可能是癌旁、良性疾病、治疗前、低风险或其他参照组。

### 11.2 相关性

```yaml
candidate_conditions:
  - correlation == true
  - verified == true preferred
  - 存在表达定量数据
  - 存在目标临床变量或连续表型
  - 独立疾病样本数满足用户要求
```

专题相关性文件不保证包含用户指定的 BMI、年龄、分期、疗效等变量，必须检查样本级 metadata。

### 11.3 治疗与疗效

```yaml
any_treatment_context:
  condition: treatment == true

paired_or_longitudinal_intervention:
  condition: pre_post_treatment == true

treatment_response_comparison:
  condition: response == true

fields_to_read:
  - treatment_type
  - drug_names
  - evidence.treatment
```

仅有 `pretreatment` 样本不代表存在治疗前后比较。

### 11.4 生存分析

```yaml
candidate_conditions:
  - survival_analysis == true
  - evidence.survival_analysis 明确支持样本级生存时间和状态可获得
  - 独立患者 ID 可建立
```

论文使用外部 TCGA 进行生存验证，不代表当前 GEO 数据集本身可进行生存分析。

### 11.5 单细胞或单核数据

```yaml
required_checks:
  - independent_donor_count
  - disease_state_per_donor
  - sample_tissue
  - scRNA_seq_or_snRNA_seq
  - sequencing_batch
  - matrix_availability
  - sample_level_metadata
  - donor_cell_mapping
```

### 11.6 空间转录组

```yaml
required_checks:
  - patient_count
  - slide_count
  - ROI_or_region_count
  - platform
  - disease_or_region_groups
  - regions_nested_within_patient
```

### 11.7 液体活检

```yaml
required_checks:
  - body_fluid_type
  - serum_plasma_whole_blood_cells_or_other
  - measured_molecule_type
  - case_and_control_definition
  - tissue_pairing
  - diagnostic_recurrence_metastasis_or_response_target
```

`sample_source` 包含 `blood` 不代表记录一定适合无创标志物研究。

## 12. DEDUPLICATION_AND_CONFLICT_RULES

```yaml
primary_key: gse_id
fallback_key_when_gse_id_missing:
  - title
  - platform
  - pdat
```

正常情况下必须以 `gse_id` 去重。不得仅按标题去重，因为标题可能变化，也可能存在 SuperSeries/SubSeries。

同一 GSE 多文件合并后应保留：

```yaml
merged_record:
  gse_id: unique_identifier
  source_files: all_matching_paths
  source_file_states: state_for_each_path
  categories: all_numbered_categories
  topics: all_topic_categories
  latest_generated_at: maximum_available_date
  dataset_fields: most_complete_non_conflicting_values
  evidence_by_source: all_evidence_objects
  conflicts: explicit_field_conflicts
```

冲突处理顺序：

```yaml
conflict_resolution:
  - 不静默覆盖
  - 比较来源文件语境
  - 比较 generated_at
  - 比较 verified
  - 比较 evidence 的具体程度
  - 检查 SuperSeries 与 SubSeries 关系
  - 返回 GEO 和论文复核
```

文件更新日期只能作为辅助信号，不自动代表较新记录一定更准确。

## 13. SUPER_SERIES_AND_SUBSERIES_RULES

遇到 GEO SuperSeries 或 SubSeries 时必须检查：

```yaml
required_checks:
  - 当前 GSE 是否只是索引容器
  - 实际表达矩阵位于哪个 SubSeries
  - 不同 SubSeries 是否对应不同组学平台
  - 样本是否在多个 SubSeries 中重复
  - 研究问题应在 SuperSeries 还是 SubSeries 层面定义
```

不得因 SuperSeries 的 `n_samples` 较大就默认所有样本属于同一可合并表达矩阵。

## 14. CANDIDATE_STATUS_MODEL

```yaml
candidate_status:
  annotated_candidate:
    meaning: 仓库标注提示可能符合条件

  metadata_checked:
    meaning: 已进一步检查 GEO 样本级 metadata

  publication_checked:
    meaning: 已检查关联论文和必要的补充材料

  files_confirmed:
    meaning: 已确认所需矩阵或原始文件可获得

  analysis_ready:
    meaning: 已确认矩阵、分组、独立样本量和必要变量能够支持目标分析
```

除非完成相应核查，不得把 `annotated_candidate` 表述为 `analysis_ready`。

## 15. AI_OUTPUT_CONTRACT

使用本仓库筛选数据集时，每个候选记录应尽量输出：

```yaml
required_output_fields:
  - gse_id
  - title
  - disease
  - sequencing_type
  - organism
  - n_samples_as_GEO_entries
  - independent_subject_count_if_verified
  - sample_source
  - study_design
  - relevant_boolean_flags
  - evidence_summary
  - source_files
  - source_file_states
  - generated_at
  - candidate_status
  - limitations
  - original_data_recheck_status
```

推荐措辞：

```yaml
preferred_language:
  - 仓库标注显示该数据集可能支持……
  - 当前公开元数据中可识别到……
  - 仍需核对独立患者数、分组和样本级变量……
  - 该 GSE 可作为候选，但尚不能仅凭标注确认可直接分析……
```

## 16. PROHIBITED_INFERENCES

AI 不得仅凭本仓库直接推断：

- 某 GSE 一定能够下载全部原始数据；
- 某 GSE 一定包含用户指定的临床变量；
- `n_samples` 等于患者数；
- `case_vs_control_differential == true` 代表存在健康对照；
- `survival_analysis == true` 代表生存字段完整且无缺失；
- `verified == true` 代表分析已经复现；
- 专题文件之间互斥；
- 编号文件与专题文件的数量可以直接累加；
- 空文件、缺失文件和 `datasets == []` 具有相同含义；
- 动物、细胞系、类器官和人体组织可以无条件合并；
- 不同表达平台的数据可以直接合并；
- 同一患者的多个样本可以作为独立个体；
- 论文摘要中的分析一定能够由 GEO 公开数据独立重现。

---

## 联系方式

- 机构：**索臻生物科技 SOGEN**
- 官网：https://www.sogentech.com/
- 科研合作与增量数据咨询：微信 `bioinformaticsboy`
