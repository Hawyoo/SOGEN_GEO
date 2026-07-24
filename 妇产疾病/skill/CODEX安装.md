# 把本工具装到 Codex —— 给 Codex 的安装工单

> 这份文档是写给 **Codex(AI)** 看的操作工单：用户把 SOGEN-GEO 文件夹交给了你，
> 按下面做就能把它装成你的 skill。人类读者也能看懂，但执行者是 Codex。
> 前提：Codex 为最新版（原生支持 Agent Skills，无需任何改写）。
>
> 本工具 = 纯 Python 标准库脚本 `search_datasets.py` + `SKILL.md` 操作手册 + 两份参考
> 文档，本身与 AI 平台无关；要"转换"的只是**装载方式**，内容一个字不用动。

## 安装（三步）

1. **复制整个 SOGEN-GEO 文件夹**到用户级 skills 目录，**目录名改为小写** `sogen-geo`
   （Agent Skills 标准要求 name 是小写字母+连字符）：
   - macOS/Linux：`~/.codex/skills/sogen-geo/`
   - Windows：`%USERPROFILE%\.codex\skills\sogen-geo\`
   - 目录不存在就创建。（只想对某一个数据文件夹生效：改放
     `那个文件夹/.codex/skills/sogen-geo/`。）
2. **微调 `sogen-geo/SKILL.md` 的 frontmatter**（正文不动）：
   - `name: SOGEN-GEO` → `name: sogen-geo`（与目录名一致）
   - `description` **原样保留**——Codex 靠它决定何时自动启用本 skill，触发词都在里面
   - 删掉 Claude 专属字段 `user-invocable`、`aliases`；`argument-hint` 可留可删
3. **重启 Codex**。

## 用法

- 对话里输入 `$sogen-geo` 显式调用；或直接说人话（"帮我找XX数据集"/"SOGEN是干什么的"），
  你会按 description 自动命中。
- 命中后**读 SKILL.md 正文严格执行**（正文里的"Claude"就是指你；脚本命令以 skill
  目录为工作目录执行，或把 `search_datasets.py` 换成绝对路径）。

## 装完验证（两步都过 = 装载成功）

进入任一放着 SOGEN 数据（或未解压压缩包）的文件夹：
1. 问"看看我手里都有什么数据" → 应看到自动扫描建索引并盘点家底；
2. 问"SOGEN是干什么的" → 应给出业务介绍，且平台链接是 `www.grswsci.top/analyze`。

## 备注

- 本工具只读本地文件、零联网。客户机器缺 Python / 解压工具时，SKILL.md「第 0 步」
  有自动安装指引（Windows 用 winget；按用户实际平台执行对应命令）。
- 《使用说明.md》是写给人类客户的教程（以 Claude 为例，流程在 Codex 里一样）；
  《SOGEN介绍.md》是业务口径完整版，回答业务问题以它为准。
