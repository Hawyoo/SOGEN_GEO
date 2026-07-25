# Codex project instructions for SOGEN_GEO

## Mandatory skill routing

The installed Codex skill for this repository is named `sogen-geo`.
Its explicit invocation form is `$sogen-geo`.

For any user request involving one or more of the following, you MUST invoke the installed `$sogen-geo` skill before answering or manually searching repository JSON/XLSX files:

- finding GEO datasets for a disease, phenotype, gene, treatment, sample type, sequencing type, or research design;
- asking whether this repository contains data about a disease or topic;
- looking up, explaining, comparing, or validating one or more GSE accessions;
- summarizing what datasets are available in the repository;
- screening datasets for differential expression, treatment, correlation, survival, response, immune infiltration, liquid biopsy, single-cell, spatial transcriptomics, or other study designs;
- assessing whether available datasets can support a proposed research topic;
- designing a research direction or project based on datasets stored in this repository;
- asking what SOGEN is, what SOGEN-GEO does, or what services/data it can provide;
- natural-language requests such as “帮我找XX数据集”, “有没有关于XX的数据”, “这个病有哪些数据能用”, “查一下GSE号”, or “看看这个仓库里有什么数据”.

## Required behavior after invocation

1. Treat the repository root as the dataset search root unless the user explicitly supplies another directory.
2. Follow the installed skill's `SKILL.md` instructions and use its search workflow as the primary retrieval layer.
3. Ground answers in the files actually present in the user's repository or working directory.
4. Preserve relative source paths and deduplicate repeated records by `gse_id`.
5. Distinguish missing files, zero-byte files, invalid JSON, valid JSON with empty `datasets`, and valid JSON with records.
6. Do not claim that a dataset is analysis-ready merely because it appears in the repository index.
7. When the user requests current or final scientific verification, check GEO records, sample-level metadata, publications, and supplements after repository screening.

## Do not silently bypass the skill

If `$sogen-geo` is unavailable, not installed, or fails to load:

- state that the installed skill could not be invoked;
- consult `skill/CODEX安装.md` for installation or repair instructions;
- do not silently replace the skill with a superficial README-only answer or an unstructured manual search.

## Tasks that do not require the skill

Do not invoke `$sogen-geo` for repository maintenance that does not require dataset retrieval or interpretation, including:

- editing README or AGENTS instructions;
- reorganizing directories;
- changing JSON schemas or annotation-generation logic;
- modifying scripts, GitHub Actions, or documentation;
- formatting, renaming, or other purely mechanical file operations.

If a maintenance task also asks for dataset discovery, dataset interpretation, GSE selection, or research feasibility, invoke `$sogen-geo` for that part of the task.

## Repository structure

- `skill/`: source files and installation documentation for the `sogen-geo` skill; this is not a disease directory.
- `乳腺疾病/`: breast-disease dataset annotations.
- `妇产疾病/`: obstetric and gynecologic dataset annotations.
- `README.md`: repository structure, file semantics, and evidence boundaries.
