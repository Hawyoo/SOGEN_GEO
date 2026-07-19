# SOGEN 索臻 · 业务介绍（完整版）

> 这份文档完整回答：**SOGEN 是干什么的、您手里的文件是什么、除了数据还能帮您做什么。**
> 在对话里直接问「SOGEN 是干什么的」「你们能帮我做什么」也会得到同样的回答
> （终端简版：`python3 search_datasets.py about`）。

---

## 一句话

**索臻生物科技 SOGEN：生信分析 + AI 智能分析 + 各类基础湿实验，一站式科研服务——
从数据到洞见、从实验到成果。**

## 您所在的群是什么

SOGEN 按专科运营一批**数据集交流群**——心血管、呼吸胸病、消化病学、肝胆胰、内分泌代谢、
神经·精神·脑病、妇产乳腺、血液病学、风湿免疫、泌尿肾脏病学、运动骨病、皮肤病学、
眼科·耳鼻喉·口腔颌面、感染·重症·慢创·烧伤等。

群的定位一句话：

> AI Agent 是大势所趋，拥抱未来，汇聚所有想在 AI 时代科研上更进一步的朋友，
> 合作交流，资源共享，认知共享。

群的节奏：

- 语料**陆续共享**，每天发新病种，直到把这个专科的病种穷举完；
- **新进群的老师不亏**：会拿到「之前所有发送结果合集」，之前发过的全都有；
- 入群 20 元不是为了赚钱，是挡广告号、筛真正做研究的人。

## 您手里的文件是什么（「检索语料」）

群里陆续收到的 `SOGEN_*.json`、汇总 Excel（或还没解压的 `.7z/.zip` 压缩包）就是语料本身。

它**不是**"帮您跑好的分析结果"，而是把某个病在 GEO 公共数据库上**全部真正相关的数据集
从噪音里捞干净、逐字段标注**出来的"这个病的数据版图"——原始数据您自己下、自己分析，
我们干的是它前面那道最脏、最费功夫的活：

- **每个疾病 = 7 个按测序类型互斥分类的 JSON**（01 转录组测序 … 07 空间转录组）
  **+ 1 个汇总 Excel**（汇总 + 7 个明细 sheet，可筛选）；部分疾病还有按研究问题维度
  精选的"专题 JSON"（与 7 桶有重叠，不重复计数）。
- **每条数据集都带着判断"对我的课题有没有用"的全部字段**：GSE 号、标题、摘要、
  实验设计、物种、样本量、平台、测序类型、样本来源、研究设计研判、相关性说明、
  治疗方案、6 个研究标记（病例对照 / 生存分析 / 治疗干预 / 治疗前后 / 相关性 / 药物响应）、
  **判定依据**、原始数据 FTP 链接。

**为什么金贵**：GEO 自己搜全是噪音（搜 X 病其实 X 只是背景板、号称单细胞实为分选后 bulk、
号称空转实为几个位置的 bulk），人力筛不全——标注质检是真代价，需要反复核对、互相印证，
这样标出来的语料全世界独一份。全景在手，您才够得着大课题：先看清这个病被研究到哪一步、
哪块还空白，再从真正的临床问题出发设计别人没做过的课题，一步步攒出自己独有的图谱。
以前这是大课题组的专属，现在这道工序我们替您做了。

## 用这份数据怎么设计课题（数据 → 产品的桥）

本数据集是 SOGEN 索臻免费共享的 GEO 标注语料（物种/测序类型/研究设计/能否病例对照等字段
已标好）。把它喂给 AI 助手、结合 SOGEN 的产品即可辅助设计、分析课题——例：

1. 这些 case/control 数据集做差异表达 + GSEA/KEGG 富集（**TransDEA**）；
2. 候选基因查药物敏感性与靶点（**DrugSens**，CMap/GDSC/PRISM/CTRP 五库）；
3. 建预后/诊断模型（**Prognosis / Diagnosis / ProgML / DiagML**，100+ 算法组合）；
4. 单细胞数据集做亚群/细胞通讯/拟时序（**scRNA 系列**）；
5. 免疫浸润 TME/突变 CNV/空间/蛋白组……一篇多组学论文要的分析，几乎都能在
   **SparkleDB**（光热生物 www.grswsci.top，379 个一键工具、不写代码产发表级图）里跑完。

数据不够、或要湿实验验证（WB/qPCR/流式/IHC/动物模型）？找 SOGEN——微信 bioinformaticsboy。

## 生信分析产品线

### 转录组

TransDEA 差异表达（DESeq2/limma/edgeR + ORA/GSEA + PPI，标准/专业版；专业版含通路活性/
转录因子/免疫浸润/TIDE/IPS/ESTIMATE）、DrugSens 药物靶点与敏感性（CMap/DGIdb/DrugBank/
GDSC/PRISM 五库）、Prognosis 预后风险（14 筛选 + 16 建模）、Diagnosis 诊断标志物
（20+ 特征选择 + 32 分类器）、SingleGene 单基因多队列系统挖掘、ProgML/DiagML 预后/诊断
机器学习框架（101/134 种算法组合穷举）、Subtype 分子亚型鉴定。

### 单细胞

scRNA 标准分析（QC/降维/聚类/注释/差异/富集）、scSubset 亚群深度、scCompare 分组差异、
细胞类型特异表达、单基因/虚拟敲除、转录因子活性、基因集评分、基因模块、细胞通讯 CCI
（CellChat/NicheNet）、代谢通量、分泌组学、空间/Bulk 反卷积、Pseudotime 拟时序
（Monocle3/scVelo/CellRank）、药物预测、克隆演化、恶性细胞鉴定、Bulk↔单细胞映射、
SAHMI 宿主-微生物互作 等 20+ 款。

### AI 科研智能体

Conflux 大模型智能文献检索、Plotter AI 自动统计分析与出图、Vizora AI 科研模式图生成与修复。

### SparkleDB 光热生信云平台

数据上传 → 质控 → 分析 → 可视化一站式，300+ 分析模块，不写代码一键出图；支持
Human/Mouse/Rat；交付交互式 HTML 报告 + 发表级 PDF/PNG 图表 + 完整 CSV 数据表 + 方法学详解。

### SparkleDB 癌症平台（www.grswsci.top）

癌症/肿瘤多组学在线分析平台，**379 个一键工具、不写代码产发表级图**，跨
『单-双-多基因 × 单癌-泛癌 × bulk-单细胞-空间』，分 32 个模块（每项后为工具数）：

1. 差异表达 27（肿瘤vs正常箱线/热图·配对·TCGA-GTEx联合·Logistic诊断·ROC·Bootstrap校准曲线·器官bodymap）
2. 生存分析 15（KM·单/多变量Cox·限制性立方样条·双基因联合评分·基因+免疫细胞联合·剪接PSI/RNA编辑/突变/eQTL生存·独立预后Cox）
3. 相关性 8（全基因组GSEA·双基因散点·多基因网络·跨组学circos/热图）
4. 通路 8（GSEA/GSVA·KEGG/Hallmark·代谢GSVA·PARADIGM·ssGSEA·肿瘤vs正常通路）
5. 临床卡方 4
6. 免疫微环境 TME 28（浸润相关·高低表达差异·免疫检查点四分位·Sig68/TIP/TILmap/EASIER/Sig18五套评分）
7. 突变 CNV 26（oncoplot·位点lollipop·突变vs野生差异/GSEA/对TME影响·cBioPortal频率·CNV扩增缺失·基因组打分·双基因互作）
8. 药物敏感性 34（GDSC1/2·CTRP·PRISM四库相关+top30·CMap XSum预测·全基因组药物筛选·GEO验证·CTD化学↔基因）
9. 免疫治疗 10（单/多基因/基因集×差异/ROC/生存·TIDE泛癌）
10. 单细胞 20（细胞类型/基因表达UMAP·AUCell/UCell/VAM/singscore/AddModuleScore五打分·伪散装相关·泛癌landscape·marker·两细胞类型DEG·TISCH注释）
11. 细胞通讯 CellChat 12（main/fine×五打分）
12. 空间转录组 16（表达可视化·恶性vs非恶性·肿瘤边界三区·细胞反卷积·切片图·五打分·STAD/BLCA全批）
13. HPA 蛋白图 5（IHC/IF下载·泛癌染色·强度统计）
14. PPI 3（BioGRID源/靶·ComPPI亚细胞网络）
15. GEO 外部验证 13（差异·生存KM/Cox meta·双基因·免疫浸润·GSEA·代谢）
16. GEO 临床变量差异 21（age/gender/stage/T/N/M/grade）
17. 蛋白质组 18（CPTAC 单/双/多基因×单/多蛋白组×差异/相关/生存）
18. PTM 磷酸化 7（CPTAC）
19. 转录后调控 9（miRNA→基因全基因组·剪接PSI·RNA编辑）
20. 转录调控 7（全TF相关·CistromeDB·ChEA3·ATAC整合）
21. 机器学习 7（LASSO·随机森林·XGBoost·Boruta·SVM-RFE·随机生存森林·10算法组合）
22. ssGSEA 评分 12（评分·分期趋势·诊断ROC·生存·单细胞打分）
23. 孟德尔随机化/共定位 5（eQTL 5e-08/1e-05·coloc·gassocplot）
24. 干性 Stemness 4
25. 基因敲除/依赖 DepMap 4（CRISPR必需性·双基因敲除·基因集敲除GSEA）
26. ATAC 染色质 2（peak注释·MEME motif）
27. WGCNA 模块-性状
28. 常规工具箱 23（GO/KEGG富集·HPA组织/单细胞/免疫细胞/亚细胞表达·PrimerBank·人鼠基因互转·GeneReview·基因↔通路·GPL注释·coloc/MR）
29. 多组学单因素 Cox 森林
30. 基因集评分 5
31. 预后 multigene signature
32. 永久会员泛癌预算 23（差异limma/wilcox·生存·分期/分级·病理T/N/M·性别/吸烟/饮酒·MSI·新辅助/放疗/靶向）

**数据底座**：TCGA 65 癌种（58,581 基因级 RDS）、GEO 538 外部验证数据集（差异469/生存318/
药敏412/临床381/TME386）、TISCH2 189 单细胞、CPTAC 23 蛋白组（11 癌种）、空间 230 切片
（18 癌种）、药敏 1914 化合物（GDSC1/2+CTRP+PRISM）、DepMap 17653 基因 CRISPR 依赖、
TIDE 免疫治疗、HPA 病理、cBioPortal 突变。

## 湿实验（千平实验室，全项目覆盖）

- **分子**：Western Blot（整膜/裁膜）、考马斯亮蓝/蛋白银染、Pull-down、IP/Co-IP/IP-MS
  （IP+Western+质谱）、凝胶电泳 PCR、荧光定量 qPCR、mRNA/lncRNA/miRNA/circRNA 引物设计合成、
  支原体污染检测、双荧光素酶报告基因、ELISA、ChIP
- **流式**：凋亡/周期/膜电位、巨噬细胞分化、T细胞/NK/效应细胞/耗竭型 CD8T、CAF 相关等——
  细胞样品与肿瘤样品流式检测
- **细胞功能**：CCK-8/IC50、克隆形成、Invasion/Transwell、EDU/TUNEL、划痕、血管形成、
  稳转细胞株构建（转染筛选/敲低/过表达）、siRNA 瞬时转染、球体形成、类器官培养（至 P3）、
  PBMC/T细胞原代提取、ROS/GSH/线粒体膜电位
- **病理**：HE 染色、免疫组化、免疫荧光单/双/三/四/五标、TUNEL、组织芯片多色检测、
  细胞爬片免疫荧光共定位、石蜡切片明场/荧光扫描（含数据整理分析+售后）
- **动物模型**

## 自有测序平台（14 大类 85+ 款产品）

索臻自有测序平台，测序·分析·湿实验一站式闭环，覆盖单细胞·空间·免疫组库·常规转录组·
宏基因组·蛋白/修饰/代谢/表观全组学（2026 官网版）：

- **单细胞与免疫组库**：自有 SeekOne®/10X Chromium 平台单细胞转录组——3'/5'/全序列/
  FFPE 探针法，单细胞 ATAC+RNA、DNA 甲基化+RNA 多组学，单细胞胞内菌测序（真迈/illumina/
  华大 T7，100–1000G）；单细胞免疫组库 TCR/BCR、TCR+BCR、5' 转录组+TCR/BCR 联合（10–120G）
- **空间组学**：全平台空间转录组——SeekSpace® 单细胞空间、华大 Stereo-seq 时空组
  （FFPE/FF，0.5–1cm²）、10X Visium FFPE/HD、Xenium 5k 单细胞原位检测；CoSMx SMI 超多色
  分子成像（1000/6000/18000 Plex RNA、64 Plex Protein）、GeoMx DSP 数字空间转录组
  （WTA 12–192 AOI）、CODEX/PCF 多重荧光蛋白空间组（IO60 肿瘤免疫 / 神经 42 标 /
  小鼠 25 标 / 自由组合 Panel）
- **转录组与宏基因组**：普通转录组 mRNA-seq（illumina/华大 T7，6G）、原核生物转录组、
  small RNA、lncRNA 测序；宏基因组测序、16S/ITS 二代扩增子测序（含标准分析）
- **蛋白与代谢组**：定量蛋白质组 Astral 平台——Rapid/Deep DIA、去高丰度血浆蛋白组
  Magic P3、Olink Target 96/Reveal；15+ 种蛋白质修饰组学（磷酸化/泛素化/乙酰化/糖基化/
  乳酸化/巴豆酰化/SUMO 化/丙酰化等）；代谢组学（非靶向代谢 / 脂质组 / 靶向氨基酸·脂肪酸·
  胆汁酸，LC-MS）
- **表观组学**：ChIP-Seq（转录因子 / 组蛋白修饰）、ATAC-Seq、WGBS 全基因组甲基化、
  MeRIP/MeDIP 甲基化测序（illumina）

## 课题合作实力

团队参与发表多篇高分论著：Nature Biotechnology、Nature Cancer、Cancer Discovery、
Nature Communications、Science Advances、STTT、JCI、PNAS、Cell Discovery、
Molecular Cancer、Cell Reports、eClinicalMedicine、eBioMedicine、iMeta、eLife、
Cancer Letters、Briefings in Bioinformatics、Phytomedicine、Oncogene、Research、
BMC Medicine 等一区期刊，有实力和条件给一区/顶刊子刊课题提供生信分析与实验技术支持；
核心成员均有顶刊/子刊发表经验，组学+实验、AI4S 方向第一梯队。

## 常见问题

- **我要的病还没发到群里** → SOGEN 一直在整理新病种，找群主问，也许已经有了，
  或者后续就会发到群里。
- **数据拿到了不会分析** → 两条路：① 语料 + Claude Code 就能自己设计课题、找数据；
  ② 交给 SOGEN 做（生信/湿实验一站式），找群主聊。
- **资料是别人转发给我的，我不在群里** → 一样可以用；想持续拿增量更新、进对应学科群，
  加微信 bioinformaticsboy（我们建了很多学科群、专题群，入群 20 元仅用于过滤广告号）。
- **想要更多专题/更深标注** → 找群主聊，学科群、专题群都在持续建。

## 联系方式

| 渠道 | 地址 |
|---|---|
| 科研合作 / 群主微信 | **bioinformaticsboy** |
| 官网 | www.sogentech.com |
| 标准化产品站 | order.sogentech.com/products |
| SparkleDB 光热平台 | www.grswsci.top/analyze |
| 公众号 | 医学僧的科研日记 · 光热生物 · 科研风向标 · 组学料理 |

---

**加群获取增量**：本材料是免费流传版；想要持续的增量更新、更多疾病与专题，请加微信
bioinformaticsboy 进对应私域群——我们建了很多学科群、专题群，入群 20 元仅用于过滤广告号。

**使用授权**：本数据集免费共享、欢迎转发使用。不得删改、涂抹或隐藏本 SOGEN 署名与宣传信息
（索臻生物科技·www.sogentech.com）。我们已同意免费分享，请保留出处。如有擅自删除署名、
篡改来源或用于商业牟利等侵权行为，本公司保留依法追究法律责任的权利。

**声明**：本数据集由索臻生物科技 SOGEN 标注整理、免费共享；欢迎转发。无论测序、自有数据
分析、公共数据库挖掘还是湿实验，均可深度合作。
