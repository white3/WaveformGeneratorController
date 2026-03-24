# Keysight 33500B / 33500 Series 查询能力调研

## 结论摘要

基于 Keysight 33500 Series 官方用户手册和 PyVISA 官方文档，目前可以较明确地得出以下结论：

1. **33500B 可以通过 SCPI 查询当前“配置状态”**，例如当前函数类型、频率、幅值、输出开关、错误队列、固件版本等。
2. **33500B 支持下载和选择任意波形（ARB）**，例如通过 `SOURce1:DATA:ARBitrary ...` 上传波形，并通过 `SOURce1:FUNCtion:ARBitrary ...` 选择当前 ARB。
3. **从已检索到的官方资料看，没有发现 33500B 内置“实时回读当前输出波形采样点”的明确接口**；也就是说，它更像“信号发生器状态可查”，而不是“示波器式波形采集设备”。
4. 因此，如果后续网页上要展示“实时波形曲线”，**大概率需要区分两类信息**：
   - **设备配置/状态变化曲线**：可直接通过轮询 SCPI 查询实现；
   - **真实输出模拟波形曲线**：通常需要外部采集设备（示波器、DAQ、采样 ADC）或至少借助同步/触发信号做间接可视化。

## 官方资料摘录要点

### 1) 设备本身支持 SCPI，并可远程配置输出函数

官方用户手册说明 33500 Series 支持 SCPI；函数类型可通过 `FUNCtion` 配置，频率可通过 `FREQuency` 配置，输出可通过 `OUTPut[1|2]` 控制。

### 2) SCPI 的“命令/查询”规则

Keysight 官方 SCPI 规则说明：一个既可设置又可查询的命令，其**查询形式就是在设置命令后追加 `?`**。

因此，虽然 33500 Series 用户手册很多位置只列出了 set form，例如：

- `FUNCtion {SINusoid|SQUare|RAMP|PULSe|NOISe|DC|PRBS|ARB}`
- `[SOURce[1|2]:]FREQuency {<frequency>|MINimum|MAXimum}`
- `VOLTage {<amplitude>|MINimum|MAXimum}`
- `OUTPut[1|2] {OFF|ON}`

按 SCPI 规则，通常可尝试其 query form：

- `FUNCtion?`
- `FREQuency?`
- `VOLTage?`
- `OUTPut1?`

### 3) 可查询的明确查询类命令

在官方手册中，可以直接看到一些明确的 query 命令：

- `SYSTem:ERRor?`：读取并清除一条错误队列
- `*IDN?`：返回厂商、型号、序列号和固件版本
- `SYSTem:VERSion?`：返回 SCPI 版本
- `*TST?`：返回自检结果

### 4) ARB 波形相关能力

官方示例明确展示了：

- `SOURce1:DATA:ARBitrary TestArb,...` 可下载任意波形数据；
- `SOURce1:FUNCtion:ARBitrary TestArb` 可切换当前 ARB；
- `MMEM:LOAD:DATA "INT:\BUILTIN\SINC.ARB"` 可从内置存储加载 `.ARB` 数据。

这说明**设备支持“上传/装载/切换波形”**，但当前检索到的资料中**未明确发现“把当前输出的采样波形实时 query 回 PC”** 的接口。

### 5) 存储状态与“波形数据”不是一回事

手册还说明：

- 仪器状态可通过 `MMEMory:STORe:STATe` / `MMEMory:LOAD:STATe` 或 `*SAV` / `*RCL` 存取；
- 前面板保存状态时，**不会保存 volatile arbitrary waveform**。

这进一步说明：

- 仪器“状态配置”是可管理/可查询/可持久化的一层；
- 任意波形数据本身属于另一层对象，且并不等同于实时输出采样回读能力。

## 对 Web 实时曲线的含义

后续如果要在网页上做“实时状态变化图”，建议先分两个阶段：

### 阶段 1：做“设备状态变化图”

可直接轮询这些值：

- 当前函数类型 `FUNC?`
- 频率 `FREQ?`
- 幅值 `VOLT?`
- 偏置 `VOLT:OFFSET?`
- 相位 `PHAS?`
- 输出状态 `OUTP1?`
- 触发/突发/扫频相关状态（需实机验证具体 query 名称）

这个阶段无需额外硬件。

### 阶段 2：做“真实波形曲线图”

如果你要看到真正的瞬时波形曲线（类似示波器 trace），建议：

1. 接入示波器或采样模块；
2. 由 Web 后端同时轮询 33500B 配置状态 + 外部采样数据；
3. 前端把“配置变化”和“真实采样曲线”分层展示。

## 脚本说明

本目录配套了几类脚本：

- `scripts/test_33500b_basic_queries.py`
  - 验证基础连接与显式/推断 query。
- `scripts/test_33500b_state_poll.py`
  - 持续轮询设备状态并保存 CSV，用于评估 Web 状态曲线刷新策略。
- `scripts/test_33500b_arb_upload.py`
  - 上传一个简单 ARB 波形并验证切换行为。
- `scripts/test_33500b_query_matrix.py`
  - 对多组候选 query 命令做探测，输出 JSON 结果，便于你把实机兼容性结果回传给我。
- `scripts/test_33500b_waveform_readback_candidates.py`
  - 对“是否存在波形数据读回接口”做偏探索式探测，尝试一些常见但未在当前官方手册中明确找到的 readback 命令。

## 待你实机回传的内容

请你连接真机后，把以下内容发我：

1. `test_33500b_basic_queries.py` 的终端输出；
2. `test_33500b_query_matrix.py` 生成的 JSON；
3. `test_33500b_state_poll.py` 生成的 CSV（任选一小段即可）；
4. `test_33500b_arb_upload.py` 是否成功、错误队列返回什么；
5. 你的设备资源名（例如 `USB0::...::INSTR` 或 `TCPIP0::...::INSTR`）和固件版本。

拿到这些结果后，我可以进一步判断：

- 哪些 query 可稳定用于 Web；
- 刷新频率能到多少；
- 是否需要引入后台缓存/节流；
- 实时曲线应该做“配置变化图”还是必须接示波器采样。
