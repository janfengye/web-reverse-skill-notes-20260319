# Action Summary And Skill Notes

## 1. 这轮实际做了什么

### 1.1 服务端漂移验证

- 对照历史公开题解与当前 2026-03-19 线上资源，确认当前题面环境已明显不同。
- 直接抓取当前 `https://match.yuanrenxue.cn/match/10` 页面资源指纹，确认实际加载的是：
  - `/static/new_match/question/10/rs.js`
  - `/api2/10`
  - `/api/10/offset`
  - `/static/new_match/question/general.js`
- 直接请求历史题解常见旧入口，验证当前线上状态：
  - `/api/match/10 -> 404`
  - `/static/match/match10/main.js -> 404`
  - `/api2/10 -> 500`
  - `/api/10/offset -> 200`

### 1.2 `_yrx$Ds` 生成链追踪

- 追到 `_yrx$Ds` 的核心生成链：
  - `aiding_5702 -> _yrx4U7`
  - `_yrx4U7 -> _yrxBXG`
- 给 `_yrx4U7` 做了源码内联打点，不再只看 `window` 暴露值，而是记录：
  - `seed`
  - `four_array`
  - `old_time`
  - `_yrxTcE`
  - `new_wp`
  - `_yrxS_G_691`
  - `mix`
  - `key`
  - `enc`
  - `out`
- 结果是：`page4 -> page5` 期间，上述大部分输入都不变，真正滚动的业务输入只剩服务端下发的 `k` 对应动态全局。

### 1.3 排除“随机链”嫌疑

- 静态和动态同时验证 `_yrxqge()`。
- 结论：
  - `_yrxqge()` 不是随机源
  - 它只是固定返回 `1773892515 + window.DEGb` 的 4 组复制
- 这意味着 `_yrxBXG` 那段并不是“因为随机 IV 导致第 5 页不稳定”。

### 1.4 排除“用错上一页 k”嫌疑

- 在当前样本中，服务端下发的动态全局变量名为 `DEdB`。
- 依次拿到的历史值是：
  - `809`
  - `1275`
  - `1287`
  - `1181`
- 把这四个值分别手动注入页面，再重新生成 fresh `page5` URL 去打。
- 结果四种都还是：
  - `400 {"error":"token failed"}`

### 1.5 继续硬追闭包/不可见内存态

- 新增作用域快照接口，不只看 `window` 全局，还抓模块/闭包层可访问状态。
- 在真实点击流里比较 `page4` 与 `page5` 请求发出前的作用域快照。
- 继续把 `_yrxdZQ()` 这组闭包表纳入快照。
- 结果：
  - `page4` 前和 `page5` 前，`_yrxdZQ()` 摘要完全一致
  - 差分只剩 `_yrx$Ds` 和 `_yrx6dT`
  - `_yrx6dT` 的静态引用只落在容器遍历/统计逻辑中，未见其直接参与签名拼接

## 2. 这轮新增的主要文件

- [Reverse_Report_CN_match10.md](/Users/zjxiong/Downloads/web-reverse/Reverse_Report_CN_match10.md)
- [trace_click_flow_compact.py](/Users/zjxiong/Downloads/web-reverse/.codex_tmp/trace_click_flow_compact.py)
- [trace_click_flow_compact.out.json](/Users/zjxiong/Downloads/web-reverse/.codex_tmp/trace_click_flow_compact.out.json)
- [trace_ds_chain.py](/Users/zjxiong/Downloads/web-reverse/.codex_tmp/trace_ds_chain.py)
- [trace_ds_chain.out.json](/Users/zjxiong/Downloads/web-reverse/.codex_tmp/trace_ds_chain.out.json)
- [experiment_page5_dedb_variants.py](/Users/zjxiong/Downloads/web-reverse/.codex_tmp/experiment_page5_dedb_variants.py)
- [experiment_page5_dedb_variants.out.json](/Users/zjxiong/Downloads/web-reverse/.codex_tmp/experiment_page5_dedb_variants.out.json)
- [trace_scope_snap.py](/Users/zjxiong/Downloads/web-reverse/.codex_tmp/trace_scope_snap.py)
- [trace_scope_snap.out.json](/Users/zjxiong/Downloads/web-reverse/.codex_tmp/trace_scope_snap.out.json)

## 3. 这轮最终结论

- 继续硬追客户端状态后，没有找到能够解释 `page5` 单独失败的新前端状态。
- 当前最有力的结论是：
  - `page5` 高概率是当前线上环境的服务端判定漂移
  - 而不是还差一个普通前端参数、cookie、storage 键、随机数或闭包态

## 4. 哪些动作适合写成 skill

### 4.1 适合沉淀成 skill 的动作

1. 题面漂移/版本漂移验证模板
- 输入目标页面 URL。
- 自动完成：
  - 页面 HTML 指纹抓取
  - 脚本与接口资源枚举
  - 历史公开题解入口对照探测
  - 输出“当前线上资源图谱”和“旧入口可用性矩阵”
- 适合做成一个可复用的 `drift-check` 子流程。

2. 浏览器真实点击流与协议流一致性验证
- 自动跑三条链路：
  - 真实点击流
  - browser-native `fetch`
  - 协议层 replay
- 比较同一页、同一 signer 下的结果是否一致。
- 对这类 CTF/web-reverse 题很有复用价值。

3. 运行时导出 signer 并做轻量 trace
- 自动识别 `eval`/壳层脚本。
- 注入导出：
  - signer 入口
  - 关键 helper
  - 请求前状态摘要
- 这是通用的“真实 signer 导出 + 最小跟踪”能力。

4. 动态全局变量影响面实验
- 自动收集服务端响应里的 `k`
- 自动注入候选全局值
- 自动生成 fresh URL 并请求
- 输出“哪些动态值真实影响请求，哪些只是噪声”
- 很适合抽成单独实验型 skill。

5. 作用域/闭包快照差分
- 在混淆 runtime 内插入一个最小化快照接口
- 在关键请求前抓作用域摘要
- 自动做相邻页面差分
- 这个能力适合处理“页面状态都看完了，还怀疑闭包态”的题。

6. 证据型中文报告更新模板
- 把 FACTS / INFERENCES / UNKNOWNS / 证据表自动维护到报告中
- 适合这类连续多轮推进的逆向任务

### 4.2 不太适合直接做成通用 skill 的动作

1. 直接写死某题变量名
- 例如 `DEdB`、`_yrx$Ds`、`_yrxdZQ()`
- 这些都是题目特化细节，不适合直接写进通用 skill

2. 针对某一段混淆源码做硬编码替换
- 某次 patch 的字符串替换位置、源码片段、helper 名称都太题目特化
- 适合作为 skill 内的“策略”，不适合作为固定实现

3. 依赖单个站点当前资源路径的判断
- 比如 `/static/new_match/question/10/rs.js`
- 这种只能作为案例，不适合作为 skill 规则本体

## 5. 我建议的 skill 拆分

### 方案 A：在现有 `web-reverse` skill 下补三个子流程

- `drift_check`
- `signer_export_and_trace`
- `scope_snapshot_diff`

优点：
- 不会把 skill 拆得过碎
- 仍然适合这类 Web CTF / API signer 逆向任务

### 方案 B：拆成两个 skill

- 一个偏前置验证：
  - `web-reverse-drift-check`
- 一个偏深挖运行时：
  - `web-reverse-runtime-trace`

优点：
- 复用边界更清楚
- 后续也能单独用于非 CTF 的 Web signer 题

## 6. 我认为最值得先写进 skill 的部分

优先级从高到低：

1. 漂移验证流程
2. signer 导出与轻量 trace
3. 浏览器/协议一致性矩阵
4. 作用域快照差分
5. 动态全局变量注入实验

如果只做一个最小增量，我建议先把“漂移验证 + signer 导出”写进现有 [SKILL.md](/Users/zjxiong/Downloads/web-reverse/SKILL.md)。
