# 反混淆与解包（T1–T3）

使用场景：识别 ob-fuscator.io、字符串数组加密、CFG扁平化、eval-pack/JSFuck/JJencode/aaencode 等。

## T1 变量重命名 / 死代码

```bash
# Prettier美化
npx prettier --parser babel --print-width 120 obfuscated.js > pretty.js

# js-beautify
js-beautify -n obfuscated.js -o pretty.js
```

```javascript
// Babel AST重命名hex标识符
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;
const fs = require('fs');

const code = fs.readFileSync('pretty.js', 'utf8');
const ast = parser.parse(code, { sourceType: 'module', plugins: ['jsx'] });
let counter = 0;
const nameMap = {};

traverse(ast, {
  Identifier(path) {
    const n = path.node.name;
    if (/^_0x[0-9a-f]+$/i.test(n)) {
      if (!nameMap[n]) nameMap[n] = 'v' + (counter++);
      path.node.name = nameMap[n];
    }
  }
});
fs.writeFileSync('renamed.js', generate(ast).code);
```

## T2 ob-fuscator.io / 字符串数组加密 / CFG扁平化

**指纹特征：**
- 顶部大型字符串数组：`var _0x1a2b = ['encStr1', ...]`
- 轮换函数：`_0x1a2b.push(_0x1a2b.shift())`
- 解码器：`function _0x3c4d(index, key) { ... }`
- CFG扁平化：`while(true){switch(state){...}}`

**字符串数组解码（vm2沙箱）：**
```javascript
const { NodeVM } = require('vm2');
const vm = new NodeVM({ sandbox: {} });
const decoderSrc = require('fs').readFileSync('decoder_extracted.js', 'utf8');
const decode = vm.run(decoderSrc + '\nmodule.exports = _0x3c4d;');

const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;
const fs = require('fs');

const code = fs.readFileSync('obfuscated.js', 'utf8');
const ast = parser.parse(code);

traverse(ast, {
  CallExpression(path) {
    const { callee, arguments: args } = path.node;
    if (callee.name && /^_0x[0-9a-f]+$/i.test(callee.name) && args.length >= 1) {
      try {
        const idx = args[0].value;
        const key = args[1] ? args[1].value : undefined;
        const result = decode(idx, key);
        if (typeof result === 'string') path.replaceWith({ type: 'StringLiteral', value: result });
      } catch (e) {}
    }
  }
});
fs.writeFileSync('deobf_strings.js', generate(ast).code);
```

**CFG扁平化线性化（思路）：**
- 找到 `order = '3|1|0|2'.split('|')` 这类序列
- 按序列排列 `switch` 的 `case` 体
- 用线性 `BlockStatement` 替换 `while+switch`

## T3 eval-packing / JSFuck / JJencode / aaencode

**eval pack 解包（捕获而不执行）：**
```javascript
const _eval = window.eval;
window.eval = function(src) {
  console.log('[eval captured] length:', src.length);
  console.log(src.slice(0, 2000));
  return undefined; // 如可疑则阻止执行
};
```

**离线解包：**
```javascript
const packedSrc = require('fs').readFileSync('packed.js', 'utf8');
const unpacked = packedSrc.replace(/\beval\b/, 'console.log');
require('vm').runInNewContext(unpacked, { console });
```

**常用工具（优先顺序）：**
- webcrack
- synchrony (deobfuscator)
- restringer
- js-deobfuscator
- ast-deobfuscator

