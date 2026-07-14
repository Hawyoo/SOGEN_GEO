# SOGEN_data

SOGEN_data 是一个面向妇产科与乳腺疾病研究的 GEO 公共数据集结构化标注仓库。仓库内容用于帮助 AI 快速识别候选 GSE、理解研究设计并判断数据可能支持的分析方向；仓库不包含原始表达矩阵、原始测序文件或完整临床数据。

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
source_of_truth_for_analysis: original_GEO_record_and_associated_publication
```

## 1. REQUIRED_READING_BEHAVIOR

AI 读取本仓库时必须遵循以下顺序：

1. 动态扫描仓库根目录，不要仅依赖 README 中列出的目录名称。
2. 根据用户研究疾病选择对应疾病目录。
3. 根据目标测序类型读取编号为 `01`–`07` 的分类 JSON。
4. 根据目标研究问题读取名称包含 `专题` 的专题 JSON。
5. 同时需要测序类型和研究设计时，读取两类文件并按 `gse_id` 关联。
6. 对跨文件结果按 `gse_id` 去重。
7. 优先读取 `datasets` 数组内的标准字段和 `evidence` 对象。
8. 忽略名称不稳定的随机下划线字段，除非用户明确要求读取其中内容。
9. 输出候选数据集前，区分“标注提示可行”与“经原始数据复核后确认可行”。
10. 不得把仓库标注直接表述为已完成的数据质量验证或最终分析结论。

## 2. REPOSITORY_SCOPE

当前仓库主要覆盖以下疾病或研究主题：

```yaml
disease_directories:
  - 乳腺癌
  - 三阴性乳腺癌
  - 男性乳腺癌
  - 卵巢癌
  - 子宫内膜癌
  - 宫颈癌
  - 妊娠期糖尿病
  - 女性不孕
```

该列表仅描述当前结构。AI 应始终以实际仓库目录为准，因为疾病目录和数据文件可能继续增加。

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

并非所有目录或文件都保证永远完整。遇到缺失文件时，AI 应基于实际存在的文件继续工作，不应虚构缺失内容。

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

编号文件主要回答：**该 GSE 属于什么检测或组学类型。**

### 4.2 专题文件

```yaml
专题_差异表达:
  target_question: 是否存在可用于组间表达比较的病例组、对照组或明确比较组

专题_治疗干预:
  target_question: 是否存在药物、放疗、手术、其他干预、干预前后或疗效应答设计

专题_相关性:
  target_question: 是否可能支持表达量与临床变量、表型或连续变量的相关分析

专题_免疫浸润:
  target_question: 是否适合研究免疫微环境、免疫细胞构成或免疫相关表达

专题_液体活检:
  target_question: 是否包含血液、血清、血浆、外泌体或其他体液来源样本
```

专题文件主要回答：**该 GSE 可能支持什么研究问题。**

## 5. CROSS_FILE_RELATIONSHIP

```yaml
numbered_files_mutually_exclusive: usually_but_not_guaranteed
numbered_files_vs_topic_files_mutually_exclusive: false
topic_files_mutually_exclusive: false
same_gse_may_appear_in_multiple_files: true
canonical_cross_file_key: gse_id
```

必须遵守：

- 不得把 7 个编号文件与专题文件的 `n_datasets` 直接相加作为疾病数据集总数。
- 同一个 GSE 可以同时出现在一个编号文件和多个专题文件中。
- 合并候选结果时以 `gse_id` 为主键去重。
- 若不同文件中同一 `gse_id` 的字段不完全一致，应保留来源文件信息，并优先比较 `generated_at`、`verified` 和 `evidence`，必要时回到 GEO 原始记录复核。
- `n_datasets` 是当前文件内记录数，不是疾病目录内唯一 GSE 总数。

## 6. JSON_TOP_LEVEL_SCHEMA

常见顶层字段如下。字段可能缺失，也可能出现额外字段；解析器必须允许 schema 扩展。

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
  meaning: 某些专题文件提供的核验规模统计；不得默认等同于 n_datasets

organism_breakdown:
  type: object_string_to_integer
  meaning: 当前文件内物种构成

sequencing_type_breakdown:
  type: object_string_to_integer
  optional: true
  meaning: 专题文件内测序类型构成

research_question_breakdown:
  type: object_string_to_integer
  optional: true
  meaning: 当前文件内各研究设计布尔标记的汇总

datasets:
  type: array_of_dataset_objects
  meaning: 数据集标注主体
```

### 6.1 非稳定字段

JSON 中可能存在名称类似以下形式的字段：

```text
_<随机字符>
```

这些字段通常承载版本、来源、署名、说明或其他附加信息。AI 默认行为：

```yaml
use_for_dataset_selection: false
use_as_stable_schema_key: false
ignore_when_unknown: true
preserve_when_copying_original_record: true
```

不得编写依赖某个随机下划线字段名称的固定逻辑。

## 7. DATASET_OBJECT_SCHEMA

`datasets` 数组内每个对象代表一个 GSE 级记录。常见字段如下：

```yaml
gse_id:
  type: string
  expected_pattern: '^GSE[0-9]+$'
  role: canonical_dataset_identifier

title:
  type: string
  source: GEO
  meaning: 数据集英文标题

organism:
  type: string
  meaning: 数据涉及的物种；可能包含多个物种或 synthetic construct

n_samples:
  type: integer
  meaning: GEO 中的样本条目数量，不保证等于独立患者数

platform:
  type: string_or_integer_or_array
  meaning: GEO Platform 编号或平台标识

pdat:
  type: date_string
  meaning: GEO 发布或更新日期

pubmed_ids:
  type: array
  meaning: 关联 PubMed ID；允许为空

sequencing_type:
  type: string
  meaning: 标注后的实际检测或测序类型

sample_source:
  type: array_of_strings
  typical_values:
    - tissue
    - blood
    - serum
    - plasma
    - cell_line
    - organoid
    - other
  meaning: 样本来源归一化标签

summary:
  type: string
  source: GEO
  meaning: GEO 研究摘要

overall_design:
  type: string
  source: GEO
  meaning: GEO 总体实验设计

study_design:
  type: string
  meaning: 中文核心设计概括

relevance_reason:
  type: string
  meaning: 数据与目标疾病相关的简要判定理由

treatment:
  type: boolean
  meaning: 是否识别到治疗或干预比较轴

treatment_type:
  type: string
  meaning: 干预类型；空字符串表示未识别或不适用

drug_names:
  type: string_or_array
  meaning: 识别到的药物名称；空值不等于论文中绝对不存在药物

case_vs_control_differential:
  type: boolean
  meaning: 按当前规则是否识别到可用于病例与对照或明确组间差异分析的条件

correlation:
  type: boolean
  meaning: 按当前规则是否识别到可用于相关性分析的表达数据与足够独立疾病样本

pre_post_treatment:
  type: boolean
  meaning: 是否识别到同类样本的干预前后设计

survival_analysis:
  type: boolean
  meaning: 是否识别到公开样本级生存时间和生存状态等必要条件

response:
  type: boolean
  meaning: 是否识别到疗效、应答或敏感/耐药分组

verified:
  type: boolean
  meaning: 当前记录是否经过标注核验；不代表原始数据已下载或分析可直接执行

ftplink:
  type: string
  meaning: GEO FTP 目录；可能为 ftp 协议地址

evidence:
  type: object
  meaning: 各判定字段的详细证据、限制和解释
```

字段类型是宽松约定。AI 必须容忍 `null`、空字符串、缺失字段、单值与数组混用等实际情况。

## 8. EVIDENCE_OBJECT_PRIORITY

`evidence` 是解释布尔标记和研究设计判定的关键字段。常见子字段：

```yaml
evidence.relevant: 疾病主体和样本与目标疾病的对应依据
evidence.sequencing_type: 测序或检测类型的判定依据
evidence.sample_source: 样本来源和是否分选、培养或直接取材的依据
evidence.case_vs_control_differential: 差异分析可行或不可行的具体理由
evidence.correlation: 相关性分析可行或不可行的具体理由
evidence.treatment: 治疗或干预轴的判断依据
evidence.survival_analysis: 生存字段是否存在及能否执行生存分析的判断依据
evidence.study_design: 可选的设计补充
evidence.relevance_reason: 可选的相关性补充
```

AI 进行候选筛选时的证据优先级：

```yaml
priority_1: evidence 中的具体说明
priority_2: study_design 和 overall_design
priority_3: summary
priority_4: 顶层或数据集级布尔字段
priority_5: 文件名和专题名称
```

布尔字段适合快速检索，`evidence` 适合解释和排除误判。不得只看布尔字段而忽略其证据文本。

## 9. BOOLEAN_FIELD_INTERPRETATION

### 9.1 `true`

`true` 表示按照当前标注规则发现了支持该分析方向的公开证据。它不保证：

- 原始矩阵可直接下载；
- 分组数量满足用户的统计要求；
- 所有 GSM 都有完整注释；
- 独立患者数等于 `n_samples`；
- 批次效应可以处理；
- 数据适合作为训练集、验证集或因果证据；
- 用户目标变量一定存在于公开元数据中。

### 9.2 `false`

`false` 表示按照当前公开信息和当前规则未识别到充分条件。它可能由以下原因导致：

```yaml
possible_false_reasons:
  - 目标字段不存在
  - 公开元数据不完整
  - 测序平台不适合该分析
  - 独立患者数不足
  - 对照不符合定义
  - 只有治疗前样本而没有干预比较轴
  - 生存信息仅出现在论文结果中而非公开样本级数据
  - 研究摘要提到分析，但 GEO 数据本身不提供执行条件
```

因此 `false` 不应被解释为理论上绝对不可分析。AI 应表述为“当前公开标注未确认可行”。

### 9.3 `verified`

```yaml
verified_true_means:
  - 记录经过当前标注流程核验
verified_true_does_not_mean:
  - 原始数据完整性已验证
  - 所有样本标签零错误
  - 论文结论已复现
  - 数据适合用户的具体模型
```

## 10. SAMPLE_COUNT_RULES

`n_samples` 是 GEO 样本条目数量。AI 不得自动将其解释为：

- 独立患者数；
- 生物学重复数；
- 可用于统计模型的有效样本数；
- 单细胞数据中的细胞数；
- 空间转录组中的 spot 数；
- 配对病例数。

可能造成 `n_samples` 与患者数不一致的情况：

```yaml
sample_multiplicity:
  - 同一患者多个组织
  - 肿瘤与配对正常组织
  - 多个时间点
  - 治疗前后样本
  - 多个空间区域或切片
  - 多个细胞亚群
  - 技术重复
  - 多平台或 SuperSeries/SubSeries 结构
```

当用户提出最小样本量、相关性、生存分析、机器学习或独立验证要求时，AI 必须从 `evidence`、`overall_design`、原始 GEO 和论文中核对独立患者数。

## 11. DATASET_SELECTION_LOGIC

### 11.1 差异表达

候选条件通常包括：

```yaml
required_or_preferred:
  - case_vs_control_differential == true
  - verified == true
  - sequencing_type 为表达定量平台
  - evidence 明确说明比较组
  - 独立样本和重复数可核查
```

不得因为标题包含“cancer”就默认存在正常对照。不得把良性疾病、癌旁组织、健康人、细胞系和动物模型视为等价对照。

### 11.2 相关性分析

候选条件通常包括：

```yaml
required_or_preferred:
  - correlation == true
  - verified == true
  - 存在表达定量数据
  - 存在目标临床变量或连续表型
  - 独立疾病样本数达到用户要求
```

专题文件中的相关性标记不保证用户指定变量存在。用户询问 BMI、年龄、分期、疗效等具体变量时，必须进一步检索样本级 metadata。

### 11.3 治疗与疗效

根据研究问题组合使用：

```yaml
any_treatment_context:
  condition: treatment == true

paired_or_longitudinal_intervention:
  condition: pre_post_treatment == true

treatment_response_comparison:
  condition: response == true

identified_drugs:
  fields:
    - treatment_type
    - drug_names
    - evidence.treatment
```

仅有 `pretreatment` 样本时，不得自动认定存在治疗前后比较。

### 11.4 生存分析

候选条件：

```yaml
required:
  - survival_analysis == true
  - evidence.survival_analysis 明确指出样本级生存时间和状态可获得
  - 独立患者 ID 可建立
```

论文使用外部 TCGA 做生存验证，不代表当前 GEO 数据集本身可以做生存分析。

### 11.5 单细胞或单核数据

重点核对：

```yaml
check:
  - 独立供体数
  - 每位供体的疾病状态
  - 样本组织来源
  - 是否为 scRNA-seq 或 snRNA-seq
  - 是否存在多个测序批次
  - 是否提供原始或处理后矩阵
  - 是否有可用的 sample-level metadata
  - 是否能区分患者而非仅区分细胞
```

不得用细胞总数替代独立患者数。

### 11.6 空间转录组

重点核对：

```yaml
check:
  - 患者数
  - 切片数
  - ROI 或空间区域数量
  - 平台类型
  - 是否包含正常、癌前、肿瘤或不同风险区域
  - 空间区域是否来自同一患者
```

不得将多个 ROI 当作独立患者进行无层级处理的统计比较。

### 11.7 液体活检

重点核对：

```yaml
check:
  - blood_or_body_fluid_type
  - serum_plasma_whole_blood_or_cells
  - 被测分子类型
  - 病例和对照定义
  - 是否与组织样本配对
  - 是否存在诊断、复发、转移或疗效目标
```

`sample_source` 中出现 `blood` 不等于所有记录都适合无创标志物研究，应结合检测对象和研究设计判断。

## 12. DEDUPLICATION_AND_CONFLICT_RULES

### 12.1 去重主键

```yaml
primary_key: gse_id
fallback_key_when_gse_id_missing:
  - title
  - platform
  - pdat
```

正常情况下应以 `gse_id` 去重。不要以标题去重，因为标题可能变化或存在 SuperSeries/SubSeries。

### 12.2 同一 GSE 多记录合并

推荐保留：

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
  - 回到 GEO 和论文复核
```

文件较新不必然代表单条记录一定更准确；更新日期只能作为辅助信号。

## 13. SUPER_SERIES_AND_SUBSERIES

AI 遇到 GEO SuperSeries 或 SubSeries 时必须检查：

```yaml
check:
  - 当前 GSE 是否只是索引容器
  - 实际表达矩阵位于哪个 SubSeries
  - 不同 SubSeries 是否对应不同组学平台
  - 样本是否在多个 SubSeries 中重复
  - 研究问题应在 SuperSeries 还是 SubSeries 层面定义
```

不得因 SuperSeries 的 `n_samples` 很大就默认所有样本属于同一可合并表达矩阵。

## 14. TEMPORAL_AND_VERSION_RULES

```yaml
annotation_version_field: generated_at
external_records_can_change: true
latest_file_is_not_automatic_ground_truth: true
recheck_original_source_before_final_inclusion: required
```

AI 输出时应说明读取的是哪个文件及其 `generated_at`。当用户要求“最新数据”时，需要检查仓库最新提交和 GEO 当前记录，而不是只依赖历史标注。

## 15. AI_OUTPUT_CONTRACT

当 AI 使用本仓库回答数据集筛选问题时，推荐输出每个候选 GSE 的以下信息：

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

AI 必须区分以下状态：

```yaml
candidate_status:
  annotated_candidate: 仓库标注提示可能符合
  metadata_checked: 已进一步检查 GEO 样本级 metadata
  publication_checked: 已检查关联论文和补充材料
  analysis_ready: 已确认矩阵、分组、样本量和必要变量可获得
```

除非已经完成相应核查，不得把 `annotated_candidate` 表述为 `analysis_ready`。

## 16. PROHIBITED_INFERENCES

AI 不得仅凭本仓库直接推断：

- 某 GSE 一定能成功下载全部原始数据；
- 某 GSE 一定有用户指定的临床变量；
- `n_samples` 等于患者数；
- `case_vs_control_differential == true` 代表健康对照；
- `survival_analysis == true` 代表生存字段无缺失；
- `verified == true` 代表结论已复现；
- 专题文件之间互斥；
- 编号文件与专题文件的数量可直接累加；
- 动物、细胞系、类器官和人体组织可以无条件合并；
- 不同平台的表达值可以直接合并；
- 同一患者的多个样本可作为独立个体；
- 论文摘要中的分析一定能由 GEO 公开数据独立重现。

## 17. MINIMUM_RESPONSE_LANGUAGE

使用本仓库给用户回答时，优先采用以下措辞：

```yaml
preferred:
  - 仓库标注显示该数据集可能支持……
  - 当前公开元数据中可识别到……
  - 仍需核对独立患者数、分组和样本级变量……
  - 该 GSE 可作为候选，但尚不能仅凭标注确认可直接分析……

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
