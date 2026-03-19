# Reverse Report CN - match/10

## 1. 任务摘要

- `target`: `https://match.yuanrenxue.cn/match/10`
- `objective`: 逆向第 10 题的 `m` 参数与请求规律，拿到全部 5 页数据
- `requirements`: 中文报告；给出可复现实验；不扩域
- `boundaries`: 仅分析 `match/10` 页面、`/api/question/10`、`/api2/10`、`/api/10/offset`

## 2. 核心发现

1. 实际接口是 `GET /api/question/10?page=N&m=...`，`token` 只是前端壳层噪声。
2. 已从真实浏览器运行时导出真正签名入口 `_yrxyA$`，并在协议层稳定复现 `page1..page4` 的 fresh `m` 生成与请求。
3. `User-Agent: yuanrenxue` 下，按真实 runtime 生成 `m`、并把每页响应里的 `k` 回填到 `window[name]=value` 后，`page1..page4` 仍可成功，但 `page5` 依旧 `{"error":"token failed"}`。
4. 当前给定 `sessionid=<redacted>` 下，已经捕获到一组完整的第 1 到 4 页真实数据，和为 `24550297`。
5. 第 5 页不是简单的 storage 缺失：`page2` 到 `page5` 之间，local/session storage 不再变化，只剩 `m=pua`、响应回填的 `k`、以及运行时内存变量（例如 `_yrx$Ds`）在变。
6. 当前线上环境里，真实点击流在 headless 和 headed 两种浏览器下都一致复现 `page5 -> 400 token failed`，并且第 5 页前没有任何额外后台接口参与状态准备。
7. `_yrx$Ds` 的生成链 `_yrx4U7` 在 `page4/page5` 期间几乎完全是常量：`seed`、`four_array`、`old_time`、`new_wp`、`_yrxS_G_691`、`mix`、`key` 都不变，真正滚动的动态输入只剩服务端下发的 `k` 对应全局变量（本轮样本里是 `DEdB`）。
8. 2026-03-19 当前线上资源指纹与历史公开题解不一致：当前页面加载的是 `/static/new_match/question/10/rs.js`、`/api2/10`、`/api/10/offset`，而历史文章提到的 `/api/match/10`、`/static/match/match10/main.js` 在当前线上分别返回 `404/404`。

## 3. 当前稳定数据

- `page1 = [656783, 599056, 194971, 810285, 368934, 997808, 692310, 925392, 243456, 776212]`
- `page2 = [490570, 527376, 609401, 756643, 339282, 788114, 744717, 962348, 237314, 265531]`
- `page3 = [818824, 123390, 957765, 963730, 986115, 494283, 596607, 933066, 369109, 819445]`
- `page4 = [157457, 156297, 927262, 512722, 283961, 103562, 634011, 730503, 324210, 489630]`
- `sum(page1..page4) = 24550297`

## 4. 证据表

| 结论 | 证据 | 说明 |
| --- | --- | --- |
| 真接口是 `/api/question/10` | 浏览器网络流与页面跳转 | 页面最终请求的都是 `page=N&m=...` |
| 第 1 到 4 页已捕获成功样本 | Playwright 导出 runtime 后协议直连 | `page1..page4` 可以在 fresh `m` 下稳定返回真实数字 |
| 第 5 页在协议序列里失败 | `solver.py` / `.codex_tmp/proto_sequence.py` | 同样的 runtime signer + `k` 回填，到 `page5` 仍是 `400 token failed` |
| 第 5 页不是“URL 已消费” | fresh page5 URL 在生成后立即协议层重放 | 即使浏览器未真正发出，该 URL 仍失败 |
| 第 5 页不是简单 cookie 分支 | `m=pua`、`155`、`05..f5` 全部失败 | fresh page5 URL 的 cookie 变体无一成功 |
| page5 不是少了 storage 键 | `.codex_tmp/inspect_page5_diff.py` | `page2..page5` 期间 local/session storage 完全不变 |
| WebRTC 相关键已部分落地 | `.codex_tmp/print_q_indices.py` + `.codex_tmp/inspect_page5_diff.py` | `$_JQnh`、`$_fb`、`$_fh0` 等会写入，但 `$_vvCI` 当前环境未见稳定值 |
| 手工补 storage 键也无效 | `.codex_tmp/experiment_page5_storage.out.json` | `$_vvCI`、`$_fr`、`$_fpn1` 单补或全补，`page5` 仍是 `token failed` |
| 页面壳层 `request/token` 不参与 | 浏览器内检查 `window.request` / `window.token` | 两者在当前线上页面里都是 `undefined` |
| 第 5 页前不存在额外后台请求 | `.codex_tmp/trace_click_flow_compact.out.json` + headed 点击流日志 | 真正点击 `1 -> 5` 的过程中，除 `rank-config`、`user`、`topic_info` 和 5 次 `question/10` 外没有别的接口 |
| page4 的 `k` 会改写 page5 的 `m`，但仍然过不了 | browser-native fetch 对 `before/after k-backfill` 两种 page5 URL 直接请求 | 两种 fresh `m` 都是 `400 token failed` |
| 真实点击流与协议流一致 | `.codex_tmp/trace_click_flow_compact.py` / headed Playwright 点击流 | headless、headed、browser-native fetch 三条链路都在第 5 页同样失败 |
| `_yrx4U7` 主体几乎是常量链 | `.codex_tmp/trace_ds_chain.out.json` | `seed`、`four`、`old`、`tc`、`wp`、`sg691`、`mix`、`key` 在 `page4/page5` 完全一致 |
| `_yrx4U7` 的有效动态输入只剩 `k` 全局 | `.codex_tmp/trace_ds_chain.out.json` | `page4 -> page5` 的 `_yrx4U7.dyn` 差分里，实质变化只剩 `DEdB`（即响应里的 `k` 变量）和由它导出的 `_yrx$Ds` |
| `_yrx4U7` 不是随机链 | `eval_runtime10.js` + `.codex_tmp/trace_ds_chain.out.json` | `_yrxqge()` 实现是固定 `1773892515 + window.DEGb` 的 4 组复制，不是随机 IV |
| page5 对所有历史 `DEdB` 变体都失败 | `.codex_tmp/experiment_page5_dedb_variants.out.json` | 手动把 `DEdB` 设为 `809/1275/1287/1181` 重新生成 fresh page5 URL，全部返回 `400 token failed` |
| 当前线上资源路径已变 | 2026-03-19 直接抓取 `match/10` HTML | 当前脚本列表是 `/static/new_match/question/10/rs.js`、`/api2/10`、`/api/10/offset` 等新版路径 |
| 历史题解中的旧入口已失效 | 2026-03-19 直接请求 | `/api/match/10 -> 404`，`/static/match/match10/main.js -> 404`，`/api2/10 -> 500`，说明题面环境不是历史文章中的原始状态 |
| 闭包态也未见 page5 专属漂移 | `.codex_tmp/trace_scope_snap.out.json` | 真实点击流里 `page4 -> page5` 请求发出前，模块/闭包快照差分只剩 `_yrx$Ds` 和 `_yrx6dT` |

## 5. FACTS / INFERENCES / UNKNOWNS

### FACTS

- 当前页面真实加载了 `question/10/rs.js`、`/api2/10`、`/api/10/offset`。
- 2026-03-19 当前页面 HTML 的 SHA-256 指纹是：
  - `14ad29bd3ac3b6eede9138a237dc24894040afb74ac5de3d5d35251c927cd925`
- 当前页面实际脚本资源包括：
  - `/static/new_match/question/10/rs.js`
  - `/api2/10`
  - `/api/10/offset`
  - `/static/new_match/question/general.js`
- 2026-03-19 直接请求旧资源的结果：
  - `/api/match/10 -> 404`
  - `/static/match/match10/main.js -> 404`
  - `/api2/10 -> 500`
  - `/api/10/offset -> 200`, body 为 `window.'abcd' = 0`
- `UA=yuanrenxue` 时，浏览器会先用 `m=155` 拿到第 1 页，之后切到 `m=pua`。
- 已成功在浏览器运行时导出 `_yrxyA$` / `_yrxBXT` / `_yrxQ9C`，说明当前逆向不是猜签名，而是直接走真实 signer。
- 当前线上页面里，`window.request` 与 `window.token` 都是 `undefined`，主页面壳层只留下一个空噪声调用点。
- 第 1 到 4 页响应里会动态下发 `k`，例如 `fcGb|1209`、`fcGb|1156`、`fcGb|130` 这样的值。
- 在本轮 `trace_ds_chain.py` 样本里，服务端下发的动态全局变量名是 `DEdB`，依次拿到：
  - `page1 -> DEdB|809`
  - `page2 -> DEdB|1275`
  - `page3 -> DEdB|1287`
  - `page4 -> DEdB|1181`
- `_yrxQ9C` 关键索引可还原为真实键名，例如：
  - `11 -> $_fr`
  - `15 -> $_fpn1`
  - `42 -> $_JQnh`
  - `60 -> $_fh0`
  - `61 -> $_vvCI`
  - `77 -> $_cDro`
  - `196 -> $_vJTp`
  - `356 -> $_fb`
- 第 5 页 fresh URL 在真实页面、协议重放、cookie 变体下都失败。
- `page4` 返回的 `k` 确实会改变下一次 `page5` 生成出来的 `m`，但 `before/after k-backfill` 两条 fresh URL 都仍然失败。
- `page2..page5` 之间 storage 不再变化；只剩内存态 `_yrx$Ds`、`k` 回填值和 `m` cookie 在滚动。
- headless 环境下，`$_fr`、`$_fpn1`、`$_vvCI` 为缺失态；但把这些键人工补齐后，第 5 页仍然失败。
- `_yrx4U7` 的 `armin`、`seed`、`four_array`、`old_time`、`_yrxTcE`、`new_wp`、`_yrxS_G_691`、`mix`、`key` 在 `page1..page5` 样本里都保持不变。
- `_yrx4U7` 真正变化的是 `_yrxBXG(...)` 产出的 `enc` 和最终 `_yrx$Ds`；而这一变化与当前 `k` 全局值同步。
- `_yrxqge()` 源码是：
  - `function _yrxVhD(){ return 1773892515 + window.DEGb }`
  - `function _yrxqge(){ return [_yrxVhD(), _yrxVhD(), _yrxVhD(), _yrxVhD()] }`
  所以 `_yrxBXG` 并不依赖真正随机源。
- `page4 -> page5` 的 `_yrx4U7.dyn` 差分只剩：
  - `DEdB: 1287 -> 1181`（上一页响应回填）
  - `_yrx$Ds` 随之更新
  - 若干运行计数器，例如 `__ds_seq`、`_yrx6dT`
- 即便把 `page1..page4` 历史上拿到过的全部 `DEdB` 值重新注入页面，再生成 fresh `page5` URL：
  - `809 -> 400 token failed`
  - `1275 -> 400 token failed`
  - `1287 -> 400 token failed`
  - `1181 -> 400 token failed`
- 继续硬追闭包/不可见内存态后，`trace_scope_snap.py` 暴露的模块级与闭包级快照显示：
  - `page4` 请求前和 `page5` 请求前，`_yrxdZQ()` 返回摘要完全一致
  - 差分只剩 `_yrx$Ds` 和 `_yrx6dT`
  - `_yrx6dT` 的静态引用只出现在一段容器遍历统计逻辑里，未见其直接参与签名拼接
- 真实点击 `1 -> 5` 的过程，无论 headless 还是 headed，都只会触发：
  - `/api/rank-config.js`
  - `/api/user?...`
  - `/api/topic_info?...`
  - `5` 次 `/api/question/10?page=N&m=...`
- `page4` 和 `page5` 请求前的紧邻 VM trace 只有：
  - `_yrxBXT(767, 3)`
  - `_yrxBXT(779, "/api/question/10?page=N", hash16, null)`
  - `_yrxyA$(...)`
  - `XHR send`
  没有额外 opcode 分支或额外网络请求参与第 5 页准备。

### INFERENCES

- 当前站点的第 5 页校验至少还绑定了一个未完全暴露的运行时内存状态，不是简单的 `UA + m + cookie + storage`。
- 现在看，客户端签名链里真正滚动的“业务输入”已经几乎只剩服务端下发的 `k` 变量；而这条输入已经被真实点击流正确回填，但第 5 页仍失败。
- 这使得“客户端还少一个显式状态”的解释进一步变弱，更像 VM 闭包/不可见内存态，或者当前线上服务端对最后一页做了额外判定。
- 再结合当前线上资源路径、接口可用性与历史公开题解的不一致，`服务端/题面漂移` 已经是高概率解释，而不再只是备选假设。
- 在继续硬追闭包态之后，仍未发现能解释 `page5` 单独失败的额外客户端状态；这进一步把结论推向“当前线上最后一页服务端判定已漂移”。

### UNKNOWNS

- 第 5 页在 2026-03-19 当前线上环境下是否存在服务端侧异常或题目漂移。
- `_yrx$Ds`、`fcGb` 之外是否还有未显式暴露但参与签名的 VM 内存状态。
- `$_vvCI` 这类 host candidate 缺失在当前环境下是否会影响最后一页，但当前证据不足以证明它是唯一原因。
- 第 5 页真实数字数组。

## 6. 结果声明

截至 2026-03-19，当前可以高置信复现的最终结果是：

- 第 1 到 4 页的真实数据已经通过成功样本拿到
- 第 5 页在真实浏览器自然流程下仍然 `token failed`
- 因此当前不能诚实声称“已拿到全部 5 页”

这不是简单的抓包或重放问题；当前证据更接近“第 5 页还依赖额外 VM 状态，且该状态在现有浏览器执行路径中没有被满足”。

## 7. 复现步骤

```bash
python3 /Users/zjxiong/Downloads/web-reverse/solver.py
```

预期看到：

- `all_yuanrenxue.steps[1..4]` 为真实数据响应
- `all_yuanrenxue.steps[5]` 为 `{"error":"token failed"}`
- `default_then_switch_p5.steps[5]` 同样失败
- `fresh_page5_replay` 中 `m=pua`、`155`、`05..f5` 全部失败
