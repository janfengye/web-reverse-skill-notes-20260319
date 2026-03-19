# Reverse Report CN - guide2

## 1. 任务摘要

- `target`: `https://match.yuanrenxue.cn/match/guide2`
- `objective`: 还原 `POST /api/user` 请求中的 `sign` 参数来源
- `requirements`: standard；中文报告；可复现脚本
- `boundaries`: 仅做页面与请求分析，不提交答案，不高频访问接口

## 2. 核心发现

1. 本题仍是 `T0`，没有混淆、没有签名算法、没有 WebCrypto、没有 WASM。
2. 题目要求在 Network 里查看 `POST /api/user` 的 `sign`，但这个 `sign` 并不是动态计算，而是页面内联脚本中写死的常量。
3. 浏览器实际发出的请求体与源码中的常量一致，`sign=yrx_network_welcome_v2_d33039f3fcbb267de77fb5df3a997960`。
4. `GET /api/user` 是普通登录态检查，真正用于题目的只有那个额外的 `POST /api/user`。

## 3. 证据表

| 结论 | 证据 | 说明 |
| --- | --- | --- |
| 题目指向 `POST /api/user` | 页面文案第 406-409 行 | 题目明确要求在 Network 里找 `POST api/user` 的 `sign` |
| 页面内联直接发起 POST | HTML 第 605-610 行 | 页面底部执行 `$.ajax({ url: '/api/user', method: 'POST', data: {sign: "..."} })` |
| `sign` 为固定常量 | HTML 第 608 行 | 明文值是 `yrx_network_welcome_v2_d33039f3fcbb267de77fb5df3a997960` |
| 动态抓包与源码一致 | DevTools `reqid=43` | 请求体为 `sign=yrx_network_welcome_v2_d33039f3fcbb267de77fb5df3a997960` |
| 响应与题目无关 | DevTools `reqid=43` 响应 | 返回 `{\"isLogin\": false}`，说明核心仅在请求参数本身 |

## 4. 调用链

1. 浏览器加载 `GET /match/guide2`
2. 页面渲染教程文案，引导用户去抓 `POST /api/user`
3. 页面底部内联脚本直接执行一个 `$.ajax` POST 请求
4. 请求体包含明文 `sign`
5. 服务器返回普通 JSON，题目只要求提取请求里的 `sign` 并提交

## 5. 风险与影响

- 这是新手引导题，训练重点是 Network 面板定位请求与参数。
- 在真实业务环境里，把所谓签名值硬编码在前端并主动发出请求，等于公开暴露，没有任何安全性。

## 6. FACTS / INFERENCES / UNKNOWNS

### FACTS

- 页面会发起两个 `/api/user` 请求，一个 `GET`，一个 `POST`。
- 目标 `sign` 出现在 `POST /api/user` 的表单体中。
- `sign` 值为 `yrx_network_welcome_v2_d33039f3fcbb267de77fb5df3a997960`。

### INFERENCES

- 题目作者刻意放一个同路径的 `GET /api/user` 干扰项，用来训练初学者区分请求方法。
- 本题没有“逆算法”过程，核心是从源码或抓包里取现成参数。

### UNKNOWNS

- 未登录状态下未验证 `/a/guide2` 提交成功后的完整响应结构。
- 未继续测试该 `sign` 是否按账号变化，因为当前页面源码与抓包均显示为固定常量。

## 7. 下一步行动

1. 直接把 `yrx_network_welcome_v2_d33039f3fcbb267de77fb5df3a997960` 填进提交框。
2. 或运行 `node web_replay_guide2.js` 自动提取 `sign`。
3. 做后续关卡时，优先区分“题面引导的接口”与“真正携带目标参数的请求”。

## 8. 交付物清单

- `web_replay_guide2.js`: 自动抓取页面并提取 `POST /api/user` 的 `sign`
- `Reverse_Report_CN_guide2.md`: guide2 中文逆向报告

## 9. 复现步骤

```bash
node web_replay_guide2.js
```

预期输出：

```text
[*] Fetching https://match.yuanrenxue.cn/match/guide2
[*] POST /api/user sign: yrx_network_welcome_v2_d33039f3fcbb267de77fb5df3a997960
```
