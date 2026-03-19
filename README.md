# web-reverse-skill-notes

`web-reverse` 前端逆向技能包与 2026-03-19 当天产出的分析文档整理版仓库。

这个仓库主要包含两部分：

- `SKILL.md` 与 `references/`：可直接复用的 Web 前端逆向技能说明、分级方法、交付模板和常用实验参考。
- `Reverse_Report_CN*.md`、`Action_Summary_Skill_Notes_CN.md`、复现脚本：当天整理出的题目分析报告、行动总结以及最小可复现实验代码。

## 目录结构

```text
.
├── SKILL.md
├── references/
│   ├── ctf.md
│   ├── deobf.md
│   ├── hooks.md
│   ├── replay.md
│   └── vm_wasm.md
├── Reverse_Report_CN.md
├── Reverse_Report_CN_guide2.md
├── Reverse_Report_CN_match10.md
├── Action_Summary_Skill_Notes_CN.md
├── web_replay.js
├── web_replay_guide2.js
└── solver.py
```

## 内容说明

### 1. Skill

- `SKILL.md`
  - 定义了 Web 前端逆向场景的触发条件、边界、T0-T7 分级、标准流程和交付要求。
- `references/`
  - 提供 hook、反混淆、协议重放、VM/WASM、CTF 分析等可按需加载的参考材料。

### 2. 当天文档

- `Action_Summary_Skill_Notes_CN.md`
  - 记录当天围绕 `match/10` 做过的关键动作、阶段性结论，以及哪些步骤适合继续沉淀成 skill。
- `Reverse_Report_CN.md`
  - `match/1` 的中文逆向报告与复现说明。
- `Reverse_Report_CN_guide2.md`
  - `guide2` 的中文逆向报告与最小复现说明。
- `Reverse_Report_CN_match10.md`
  - `match/10` 的阶段性分析报告，重点覆盖 runtime signer 导出、状态对比和线上资源漂移判断。

### 3. 复现脚本

- `web_replay.js`
  - 复现 `match/1` 的 `m` 参数并抓取 5 页数据。
- `web_replay_guide2.js`
  - 抽取 `guide2` 中 `POST /api/user` 的固定 `sign`。
- `solver.py`
  - `match/10` 的实验型脚本，用 Playwright 驱动真实运行时导出 signer，并验证多页请求行为。

## 使用方式

### Node.js 脚本

```bash
node web_replay.js
node web_replay_guide2.js
```

如果目标题目需要登录态，按需通过环境变量传入：

```bash
COOKIE='sessionid=your_sessionid_here' node web_replay.js
```

### Playwright 脚本

`solver.py` 依赖本机可用的 Chrome 与 Python Playwright。

```bash
YRX_SESSIONID='your_sessionid_here' python3 solver.py
```

## 敏感信息处理

- 仓库内不包含原始登录态。
- 需要登录态的脚本均改为从环境变量读取。
- 文档中的会话值已脱敏，保留的是分析结论和复现路径，而不是可直接复用的私人凭据。
