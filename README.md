# SOGEN_data

SOGEN_data 是面向妇产科、乳腺及女性生殖相关疾病研究的 GEO 公共数据集结构化标注仓库。仓库用于帮助 AI 定位候选 GSE、理解研究设计并判断可能支持的分析方向；仓库不包含原始表达矩阵、原始测序文件或完整临床数据。

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
final_source_of_truth:
  - original_GEO_record
  - sample_level_metadata
  - associated_publication
  - supplementary_materials
```

## 1. REQUIRED_BEHAVIOR

```yaml
reading_order:
  - dynamically_scan_repository_root
  - select_disease_directory
  - inspect_target_file_state
  - read_numbered_JSON_for_omics_type
  - read_topic_JSON_for_research_design
  - join_records_by_gse_id
  - preserve_source_paths
  - deduplicate_by_gse_id
  - evaluate_evidence_and_limitations
  - assign_candidate_status
```

强制规则：

- README 的目录清单只是快照，不是永久白名单。
- 文件名为 `01`–`07` 的 JSON 用于组学类型筛选；包含 `专题` 的 JSON 用于研究问题筛选。
- 同时需要组学类型和研究设计时，必须读取两类文件并按 `gse_id` 关联。
- 优先读取 `datasets` 数组中的标准字段和 `evidence` 对象。
- 随机下划线字段不得作为固定 schema、筛选条件或数据主键。
- 仓库标注只能用于候选初筛，不得直接表述为数据已下载、质量已验证、分析可直接运行或结论已复现。
- 用户要求“最新数据”时，应检查仓库最新提交、文件 `generated_at` 和 GEO 当前记录。

## 2. CURRENT_DIRECTORY_SNAPSHOT

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

该分类仅用于导航。实际目录可能继续增加，必须以仓库根目录现状为准。

## 3. EXPECTED_FILE_PATTERN

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

该模式是预期命名规范，不保证每个目录始终包含全部文件或全部文件均有候选记录。

## 4. FILE_STATE_MODEL

```yaml
file_states:
  missing:
    definition: path_not_found
    usable: false

  zero_byte:
    definition: file_exists_but_has_no_content
    usable: false

  invalid_json:
    definition: content_cannot_be_parsed_as_complete_JSON
    usable: false

  valid_json_without_datasets:
    definition: valid_JSON_without_standard_datasets_array
    usable_for_dataset_records: false

  valid_json_empty_datasets:
    definition: valid_JSON_and_datasets_is_empty_array
    usable: true
    interpretation: no_records_in_this_file_under_current_annotation_rules

  valid_json_with_records:
    definition: valid_JSON_with_one_or_more_dataset_objects
    usable: true

  xlsx_present:
    definition: human_readable_inventory_exists
    preferred_for_AI_field_parsing: false
```

```yaml
zero_byte_equals_empty_datasets: false
missing_file_equals_empty_datasets: false
invalid_json_equals_empty_datasets: false
empty_datasets_proves_no_relevant_GEO_study_exists: false
```

缺失、零字节、解析失败和 `datasets == []` 必须分别报告。任何一种状态都不能证明 GEO 中绝对不存在相关研究。

## 5. FILE_TYPE_SEMANTICS

```yaml
numbered_files:
  01_转录组测序:
    - bulk_RNA_seq
    - mRNA_seq
    - other_bulk_transcriptome_sequencing
  02_转录组芯片:
    - gene_expression_microarray
    - transcriptome_array
  03_单细胞单核:
    - scRNA_seq
    - snRNA_seq
  04_表观基因组学:
    - DNA_methylation
    - ATAC_seq
    - ChIP_seq
    - other_epigenomic_data
  05_非编码RNA:
    - miRNA
    - lncRNA
    - circRNA
    - small_RNA
  06_其他长尾:
    - proteomics
    - metabolomics
    - immune_repertoire
    - targeted_assays
    - uncommon_or_unclassified_omics
  07_空间转录组:
    - spatial_transcriptomics
    - Visium
    - GeoMx
    - Stereo_seq
    - other_spatial_expression_platforms

topic_files:
  专题_差异表达: group_expression_comparison
  专题_治疗干预: treatment_intervention_or_response
  专题_相关性: expression_clinical_or_continuous_variable_correlation
  专题_免疫浸润: immune_microenvironment_or_infiltration
  专题_液体活检: blood_serum_plasma_amniotic_fluid_exosome_or_other_body_fluid
```

编号文件回答“属于什么检测或组学类型”；专题文件回答“可能支持什么研究问题”。两类文件不是互斥集合。

## 6. CROSS_FILE_RULES

```yaml
numbered_files_mutually_exclusive: usually_but_not_guaranteed
numbered_files_vs_topic_files_mutually_exclusive: false
topic_files_mutually_exclusive: false
same_gse_may_appear_in_multiple_files: true
canonical_cross_file_key: gse_id
```

- 不得把编号文件与专题文件的 `n_datasets` 相加作为疾病数据集总数。
- 同一 GSE 可同时出现在一个编号文件和多个专题文件中。
- 同一 GSE 可能因 SuperSeries、SubSeries 或多组学设计出现在多个组学分类中。
- 合并时必须保留 `source_files`、`source_file_states`、`categories`、`topics` 和各来源的 `evidence`。
- `n_datasets` 仅表示当前 JSON 的记录数。
- `n_verified_total` 不得解释为唯一 GSE 数、可分析数据集数、样本数或患者数。
- 字段冲突不得静默覆盖。

## 7. JSON_TOP_LEVEL_SCHEMA

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
  meaning: length_of_datasets_in_current_JSON

n_verified_total:
  type: integer
  optional: true
  not_equivalent_to: n_datasets

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
```

解析器必须允许字段缺失和 schema 扩展。

### 7.1 RANDOM_UNDERSCORE_FIELDS

```yaml
field_pattern: _<random_characters>
possible_content:
  - source_information
  - version_information
  - attribution
  - authorization
  - promotional_information
  - other_metadata
use_for_dataset_selection: false
use_as_stable_schema_key: false
ignore_when_unknown: true
preserve_when_copying_original_record: true
```

## 8. DATASET_OBJECT_SCHEMA

```yaml
gse_id:
  type: string
  role: primary_identifier

title:
  type: string

organism:
  type: string
  note: may_include_multiple_species_or_synthetic_construct

n_samples:
  type: integer
  meaning: GEO_sample_entry_count
  not_equivalent_to:
    - independent_patient_count
    - independent_donor_count

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
  role: curated_design_summary

relevance_reason:
  type: string
  role: curated_disease_relevance_rationale

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
  meaning: annotation_manually_checked
  not_equivalent_to: analysis_reproduced

ftplink:
  type: string
  accessibility_requires_recheck: true

evidence:
  type: object
  role: field_level_annotation_rationale
```

缺失、空字符串或 `null` 字段必须表示为 `unknown_or_not_provided`，不得自行补全。

## 9. BOOLEAN_AND_EVIDENCE_SEMANTICS

```yaml
boolean_true:
  interpretation: candidate_positive_under_current_annotation

boolean_false:
  interpretation: insufficient_current_evidence
  absolute_impossibility: false

verified_true:
  means: annotation_record_was_manually_checked
  does_not_mean:
    - raw_data_downloaded
    - sample_metadata_complete
    - quality_control_passed
    - analysis_reproduced
    - publication_conclusion_validated
```

```yaml
evidence_priority:
  - evidence_field_specific_rationale
  - study_design
  - relevance_reason
  - overall_design
  - summary
  - file_level_statistics
```

布尔字段与 `evidence` 冲突时，必须显式记录冲突并回到 GEO 或论文复核。

## 10. SAMPLE_UNIT_RULES

```yaml
possible_units:
  - independent_patient
  - independent_donor
  - tissue_sample
  - paired_sample
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

- `n_samples` 只能称为 GEO 样本条目数，除非已核对独立患者或供体。
- 单细胞数据不得用细胞总数替代独立供体数。
- 空间转录组不得用 spot、ROI 或切片数替代患者数。
- 同一患者的配对组织、多个时间点或多个区域不得默认作为独立个体。
- 动物、细胞系、类器官和人体组织不得无条件合并。

## 11. ANALYSIS_CANDIDATE_RULES

```yaml
differential_expression:
  required_checks:
    - case_vs_control_differential
    - expression_quantification_platform
    - recoverable_comparison_groups
    - independent_biological_replicates
  warning: true_does_not_guarantee_healthy_control

correlation:
  required_checks:
    - correlation
    - target_variable_exists_in_sample_metadata
    - independent_subject_count
  warning: topic_file_does_not_guarantee_specific_variable_exists

treatment:
  flags:
    treatment: any_treatment_context
    pre_post_treatment: paired_or_longitudinal_intervention
    response: treatment_response_comparison
  warning: pretreatment_only_is_not_pre_post_design

survival:
  required_checks:
    - survival_analysis
    - survival_time_available
    - survival_status_available
    - independent_patient_ID_available
  warning: external_TCGA_validation_does_not_make_GEO_survival_ready

single_cell_or_nucleus:
  required_checks:
    - independent_donor_count
    - disease_state_per_donor
    - tissue_source
    - scRNA_or_snRNA
    - batch_information
    - matrix_availability
    - donor_cell_mapping

spatial_transcriptomics:
  required_checks:
    - patient_count
    - slide_count
    - ROI_or_region_count
    - platform
    - comparison_groups
    - regions_nested_within_patient

liquid_biopsy:
  required_checks:
    - body_fluid_type
    - measured_molecule_type
    - case_control_definition
    - tissue_pairing
    - diagnostic_recurrence_metastasis_or_response_target
```

## 12. DEDUPLICATION_AND_CONFLICTS

```yaml
primary_key: gse_id
fallback_key_if_missing:
  - title
  - platform
  - pdat

merged_record:
  gse_id: unique_identifier
  source_files: all_matching_paths
  source_file_states: state_for_each_path
  categories: all_numbered_categories
  topics: all_topic_categories
  latest_generated_at: maximum_available_date
  evidence_by_source: all_evidence_objects
  conflicts: explicit_field_conflicts
```

```yaml
conflict_resolution_order:
  - do_not_silently_overwrite
  - compare_file_context
  - compare_generated_at
  - compare_verified
  - compare_evidence_specificity
  - inspect_SuperSeries_SubSeries_relationship
  - recheck_GEO_and_publication
```

较新的文件不自动等于更准确的记录。

## 13. SUPER_SERIES_AND_SUBSERIES

```yaml
required_checks:
  - is_current_GSE_only_an_index_container
  - which_SubSeries_contains_the_actual_matrix
  - whether_SubSeries_use_different_omics_platforms
  - whether_samples_repeat_across_SubSeries
  - whether_analysis_should_use_SuperSeries_or_SubSeries
```

不得因 SuperSeries 的 `n_samples` 较大就认为全部样本属于同一可合并表达矩阵。

## 14. CANDIDATE_STATUS

```yaml
candidate_status:
  annotated_candidate: repository_annotation_suggests_possible_fit
  metadata_checked: GEO_sample_level_metadata_checked
  publication_checked: publication_and_required_supplements_checked
  files_confirmed: required_matrix_or_raw_files_confirmed_available
  analysis_ready: matrix_groups_independent_sample_size_and_required_variables_confirmed
```

除非完成对应核查，不得把 `annotated_candidate` 表述为 `analysis_ready`。

## 15. AI_OUTPUT_CONTRACT

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

- 仓库标注显示该数据集可能支持……
- 当前公开元数据中可识别到……
- 仍需核对独立患者数、分组和样本级变量……
- 该 GSE 可作为候选，但尚不能仅凭标注确认可直接分析……

## 16. PROHIBITED_INFERENCES

仅凭本仓库不得推断：

- 某 GSE 一定能够下载全部原始数据；
- 某 GSE 一定包含用户指定的临床变量；
- `n_samples` 等于患者数；
- `case_vs_control_differential == true` 代表健康对照；
- `survival_analysis == true` 代表生存字段完整；
- `verified == true` 代表分析已经复现；
- 专题文件之间互斥；
- 编号文件与专题文件的数量可以直接相加；
- 缺失文件、零字节文件、无效 JSON 和 `datasets == []` 含义相同；
- 动物、细胞系、类器官和人体组织可以无条件合并；
- 不同表达平台可以直接合并；
- 同一患者的多个样本可以作为独立个体；
- 论文摘要中的分析一定能够由 GEO 公开数据独立重现。

---

## 联系方式

- 机构：**索臻生物科技 SOGEN**
- 官网：https://www.sogentech.com/
- 科研合作与增量数据咨询：微信 `bioinformaticsboy`
