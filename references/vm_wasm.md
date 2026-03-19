# JS-VM / WASM 逆向（T4–T7）

使用场景：发现 VM 调度器/字节码数组，或检测到 WASM 参与核心逻辑。

## JS-VM 识别与反虚化

**指纹：**
- 大型 opcode/字节码数组（Uint8Array / base64 blob）
- 调度循环：`while(pc < bytecode.length){ op = bytecode[pc++]; switch(op){...} }`
- 虚拟寄存器或栈结构：`regs[]` / `stack.push/pop`
- opcode → handler 映射表

**建议步骤：**
1. 定位调度器函数与 opcode 分发点
2. 记录 opcode→handler 映射，输出 `vm_opcodes.txt`
3. 动态插桩：在 handler 入口记录 pc/opcode/栈状态
4. 结合 AST/运行时日志做语义提升

## WASM 识别与分析

**指纹：**
- `WebAssembly.instantiate` / `instantiateStreaming`
- 网络请求 `.wasm`
- emscripten/wabt 相关特征

**建议步骤：**
1. 导出 wasm 文件
2. `wasm-dis` 生成 WAT（保存 `wasm_analysis.wat`）
3. 使用 IDA/Ghidra WASM 插件定位关键函数
4. 运行时 hook WASM 导入/导出函数

## 混合防护（T6/T7）

- T6：先 JS-VM 反虚化，再进入 WASM 语义恢复
- T7：外层混淆 → 中层 VM → 内层 WASM，按层剥离，分层产物交付

