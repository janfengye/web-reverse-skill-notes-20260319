# Reverse Report CN

## 1. 任务摘要

- `target`: `https://match.yuanrenxue.cn/match/1`
- `objective`: 还原 `/api/question/1` 的 `m` 参数生成逻辑，请求全部 5 页并计算总和
- `requirements`: standard；中文报告；提供可复现脚本
- `boundaries`: 仅在题目页面和题目接口范围内分析，不高频提交答案，不扩展到其他题目或站点

## 2. 核心发现

1. 题目关键接口是 `GET /api/question/1`，实际需要模拟的是查询参数 `m`。
2. 页面并不会真正请求 `/api/match/1`，而是先把 `$.ajax` 临时劫持，拦截对 `/api/match/1` 的伪请求，从 `arguments[0].data.m` 里取出生成后的 `m` 并写入 `window.match1`。
3. `window.request()` 的核心公式是：
   `adjusted_ms = Date.parse(new Date()) + 100000000`
   `hash = md5_variant(adjusted_ms.toString())`
   `m = hash + "丨" + Math.floor(adjusted_ms / 1000)`
4. 这里的 `md5_variant` 不是直接调用浏览器原生接口，而是由页面把 `window.a` 解码成一段 Base64，再还原出一份 MD5 旧实现源码，最后执行 `window.f = hex_md5(mwqqppz)`。
5. 最后一页必须把 `User-Agent` 改成 `yuanrenxue`，否则第 5 页不会返回目标数据。

## 3. 证据表

| 结论 | 证据 | 说明 |
| --- | --- | --- |
| 题目要求逆向 `m` 参数 | 页面文案第 404-415 行 | 明确要求模拟 `m`，并提醒最后一页更换 `User-Agent`、携带 `sessionid` |
| 页面拦截 `/api/match/1` | HTML 第 507-515 行 | 覆盖 `$.ajax`，若 `url === "/api/match/1"` 就把 `data.m` 赋给 `window.match1` |
| 页面发真实题目请求 | HTML 第 584-595 行 | `req()` 调用 `window.request()` 后向 `/api/question/1` 发 GET |
| 当前真实请求样例 | DevTools `reqid=23` | 请求参数形如 `m=<32位hash>丨<秒级时间戳>` |
| `window.request()` 公式 | 浏览器中 `window.request.toString()` | 明文可见 `Date.parse(new Date()) + 100000000`、`oo0O0(...)+window.f`、拼接 `丨` |
| 解码后的 MD5 赋值 | 浏览器解码 `window.b` 末尾 | 末尾为 `window.f = hex_md5(mwqqppz)` |
| 总和复现成功 | 本地脚本 `node web_replay.js` | 5 页全部返回 `200`，总和为 `30210542` |

## 4. 调用链

1. 浏览器加载 `GET /match/1`
2. 页面注入 `uyt.js`、`uzt.js` 作为反调试噪声
3. 页面临时劫持 `$.ajax`
4. 页面调用 `window.request()`
5. `window.request()` 计算 `adjusted_ms = Date.parse(new Date()) + 100000000`
6. `oo0O0(adjusted_ms.toString())` 解码 `window.a`，执行 MD5 脚本，将结果写进 `window.f`
7. 页面构造 `m = window.f + "丨" + adjusted_ms/1000`
8. 对 `/api/match/1` 的伪请求被拦截，`window.match1` 被赋值
9. 页面再请求真实接口 `/api/question/1?page=...&m=...`

## 5. 风险与影响

- 页面用了两层低强度干扰：定时 `debugger` 和控制台乱码输出。它们会影响手工调试效率，但不改变核心算法。
- 真正的参数逻辑不复杂，重点是识别“伪请求 + 拦截赋值”这一层中转，而不是被大段乱码 HTML 模板拖住。

## 6. FACTS / INFERENCES / UNKNOWNS

### FACTS

- `m` 由 32 位十六进制哈希、一个中文竖线 `丨` 和秒级时间戳组成。
- `adjusted_ms` 使用的是 `Date.parse(new Date())`，不是 `Date.now()`。
- `window.a` 每个字符都按 `charCodeAt(i) - i - 5` 解码后组成 Base64。
- 第 5 页必须使用 `User-Agent: yuanrenxue`。
- 当前无 `sessionid` 条件下，5 页数据总和为 `30210542`。

### INFERENCES

- 题目作者故意把 `$.ajax` 劫持成一个“本地生成器”，让初学者先学会区分伪请求与真实网络请求。
- 页面提到 `sessionid`，说明登录态下每个用户的数据可能不同；当前这组结果对应的是当前未携带 `sessionid` 的请求环境。

### UNKNOWNS

- 未验证登录态下带 `sessionid` 的数值是否会变化到什么范围。
- 未实际向 `/a/1` 提交答案，避免触发不必要的提交频率限制。

## 7. 下一步行动

1. 直接运行 `node web_replay.js` 获取全部 5 页数据和总和。
2. 若你有自己的登录态，执行前设置 `COOKIE='sessionid=...' node web_replay.js`。
3. 将脚本输出的 `total` 填入页面提交框。

## 8. 交付物清单

- `web_replay.js`: 复现 `m` 参数、抓取全部 5 页并计算总和
- `Reverse_Report_CN.md`: 当前题目的中文逆向报告

## 9. 复现步骤

```bash
node web_replay.js
```

若需要携带登录态：

```bash
COOKIE='sessionid=your_sessionid_here' node web_replay.js
```

当前环境下的预期总和：

```text
total: 30210542
```
