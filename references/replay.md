# 协议重建与重放

使用场景：签名/加密参数还原、API重放、WebSocket/SSE协议解析。

## 参数结构还原
- 同操作重放两次 → diff请求体，分离静态/动态字段
- 时间戳/nonce → 追踪生成逻辑
- HMAC/签名 → 用捕获的 key + 算法重算验证
- Token 生命周期：登录 → 签发 → 过期 → 刷新

## web_replay.js 模板（Node.js）

```javascript
#!/usr/bin/env node
'use strict';
const https   = require('https');
const crypto  = require('crypto');
const { URL } = require('url');

const BASE_URL  = 'https://target.com';
const ENDPOINT  = '/api/v2/data';
const APP_KEY   = 'captured_app_key';
const SECRET    = 'captured_hmac_secret';
const TOKEN     = 'session_token_from_cookie_or_localstorage';

function buildSign(params, secret) {
  const ts = Date.now().toString();
  const nonce = Math.random().toString(36).slice(2, 10);
  const sorted = Object.entries({ ...params, timestamp: ts, nonce })
    .sort(([a],[b]) => a.localeCompare(b))
    .map(([k,v]) => `${k}=${v}`)
    .join('&');
  return {
    sign: crypto.createHmac('sha256', secret).update(sorted).digest('hex'),
    timestamp: ts,
    nonce,
  };
}

async function request(method, path, params = {}) {
  const { sign, timestamp, nonce } = buildSign(params, SECRET);
  const body = JSON.stringify({ ...params, sign, timestamp, nonce });
  return new Promise((res, rej) => {
    const url = new URL(path, BASE_URL);
    const req = https.request({
      hostname: url.hostname, port: 443, path: url.pathname + url.search,
      method, headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TOKEN}`,
        'X-App-Key': APP_KEY,
        'Content-Length': Buffer.byteLength(body),
      }
    }, r => { let d = ''; r.on('data', c => d += c); r.on('end', () => res({ status: r.statusCode, body: d })); });
    req.on('error', rej);
    req.write(body);
    req.end();
  });
}

(async () => {
  console.log('[*] 发送重放请求...');
  const result = await request('POST', ENDPOINT, { uid: '12345', action: 'query' });
  console.log('[*] Status:', result.status);
  console.log('[*] Response:', result.body);
})();
```

## WebSocket / SSE 帧解析
- JSON 字符串 → 直接解析
- 0x08/0x0A 开头 → 疑似 protobuf（可用 `protoc --decode_raw`）
- 0x82–0x8F 开头 → msgpack fixmap/fixarray
- XOR 混淆 → 从已知明文推导 key

## 交付物补充
- `crypto_params.json`：捕获的 key/iv/nonce/ts/明文/密文
- `token_flow.md`：token 生成、过期、刷新流程

