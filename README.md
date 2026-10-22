# Strata NEXUS — 本地大模型工作台（前端深度定制版）

**简体中文** · [English](README.en.md)

![version](https://img.shields.io/badge/version-v0.64-71f6d2) ![engine](https://img.shields.io/badge/engine-0.1.47-9b8cff) ![license](https://img.shields.io/badge/license-MIT-8291aa)

**当前版本 v0.64**（2026-10-22）· 更新增量见 [更新日志](CHANGELOG.md)

基于 [Niko1221/Strata](https://github.com/Niko1221/Strata) 上游引擎的**前端深度定制版**。引擎能力不动，界面整个重做：把本地推理变成一个可看的、可调的、像样的工作台。

## 界面一览

**控制总览** — 生成速度 / 显存 / 模型状态 / API 请求量一屏尽收，资源概览实时刷新

![控制总览](shots/nexus-overview.png)

**智能对话** — 流式输出、Markdown 渲染、思考过程折叠、右侧参数面板，整页锁定视口不跳动

![智能对话](shots/nexus-chat.png)

**实时监控** — GPU/显存/CPU/内存实时水位 + 服务健康自检（health/status/metrics/slots）

![实时监控](shots/nexus-monitor.png)

**偏好与高级设置** — 主题 / 字体 / 颜色 / 动效全部可视化调，改完立即生效并本地保存

![偏好与高级设置](shots/nexus-settings.png)

**四套主题（v0.64 全量 token 化：每套独立 22 个颜色变量，强调色/辅助色/文字/面板/代码块全随主题切换）**

| 极光 Aurora | 冰川 Glacier | 熔 Ember | 钛灰 Mono |
|---|---|---|---|
| ![极光](shots/theme-aurora.png) | ![冰川](shots/theme-ice.png) | ![熔](shots/theme-ember.png) | ![钛灰](shots/theme-mono.png) |

## 相比官方前端的变化

### 界面架构
- **全新 NEXUS 视觉体系**：暗色玻璃拟态 + 氛围光效，取代官方默认界面
- **4 套主题全量 token 化**（极光 Aurora / 冰川 Glacier / 熔 Ember / 钛灰 Mono）：每套独立 22 个颜色变量，强调色 / 辅助色 / 文字 / 面板 / 代码块全部随主题切换，切主题自动套用该主题的预设色板；+ 紧凑/舒适密度切换 + 界面光效/闪烁动效/减少波动独立开关
- **强调色自定义**：主题色、辅助色、主/次文字颜色全局管理，图例/按钮/图表风格自动跟随

### 排版与可读性
- **三分区字号系统**：界面字号 / 代码字号 / 提示字号独立滑条（全局 calc 化，逐档可见），互不牵动
- **对话文字独立控制**：字号 + 颜色单独调节；对话渲染 Markdown / 纯文本可选，**默认 Markdown**（标题/表格/代码块/引用块全支持）
- **代码语法高亮 3 套配色**（跟随主题 / Classic / GitHub），自写 tokenizer，零外部依赖
- 提示字号自适应：检测到浏览器最小字号钳制时自动抬高下限，保证每档可辨

### 对话体验
- **智能滚动**：生成中可自由上滚浏览，滚回底部自动恢复跟随 + 回到底部悬浮钮
- **流式实时显示**：生成速度 / 耗时逐 token 更新，完成后精确覆盖
- **思考过程默认折叠**（显示字数摘要，点开查看）
- **消息操作**：复制 / 编辑（后续消息一并移除）/ 重新生成 / 删除
- **长提示读入进度条**：>8K token 提示显示读入进度，按 chunk 步进 + 走秒

### 数据与会话
- **会话持久化**：一键保存/恢复对话（引擎状态与前端消息配对存档），跨重启不丢
- **导出 Markdown**：对话一键导出
- **API 请求监视器**：最近 100 条请求的提示与回答可在界面查看

### 细节打磨
- 消息两侧对齐（AI 贴左铺满、用户气泡贴右）、输入框聚焦光晕、统一细滚动条
- 关键数值等宽数字（刷新不抖动）、代码块内部滚动、移动端/窄窗响应式适配
- 服务端配置通过 /config 端口热保存，前端偏好 localStorage 本地持久化

## 部署步骤（Windows + NVIDIA GPU）

1. **克隆本仓库**
   ```
   git clone https://github.com/SuperWJ062/Strata-NEXUS.git
   cd Strata-NEXUS
   ```
2. **首次初始化**：双击 `engine\START-HERE.bat`，按提示选择模型与参数（模型三件套会自动下载，详见下节；**也可自行下载，两者不冲突**）
3. **日常启动**：双击 `START.bat`（新版可在 设置→系统与更新 一键检查更新） —— 加载模型并自动打开 `http://127.0.0.1:8080/`

## 模型下载（地址与过程详解）

当前配置使用 **Qwen3.8-Flash-Next IQ2_XS** 量化版。

**模型仓库（Hugging Face）**：
> **https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF**
> （大陆镜像 ModelScope：https://www.modelscope.cn/models/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF ）

需要下载的东西共三样（主模型 + MTP 草稿层 + 视觉编码器）。**两种方式随便用、可混搭、互不冲突**：
- **方式 A（自动）**：`START-HERE.bat` 初始化时脚本自动下载
- **方式 B（手动）**：自行用浏览器/下载器（IDM、aria2 等）从上面仓库下载，放到指定目录即可

**为什么不冲突**：脚本对每个文件先检查"目标位置是否已有同名义件"，有则做 SHA-256 校验——通过就直接跳过下载（模拟部署实测输出 `[ok] ... already downloaded`）；校验不过或没有才重新下载。所以先手动下载再跑脚本、或脚本下了一半你手动补，都安全。

### ① 主模型 GGUF（约 68 GB，2 个分片）

| 项目 | 内容 |
|---|---|
| 来源仓库 | https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF |
| 文件 | `Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf`<br>`Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf` |
| 落位 | `Strata-data/models/IQ2_XS/` |
| 大陆镜像 | https://www.modelscope.cn/models/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF （同仓库同文件路径） |

### ② MTP 投机解码草稿层（约 5 GB）

- 来源是 Qwen 官方原始 BF16 checkpoint（**Qwen/Qwen3.8-Flash-Next**，整包 360 GB——**不用担心**，脚本只从中抽取 MTP 模块的张量，实际传输约 5 GB）
- 抽取与校验由 `tools/mtp_fetch.py` 完成：逐张量对照 pinned revision 的哈希，防下载损坏
- 自动落位 `Strata-data/mtp/rt`

### ③ 视觉编码器（读图功能，约 1 GB）

- `mmproj-Qwen3.8-Flash-Next-BF16.gguf`，与主模型同一仓库（上方 ① 的地址）
- 不需要读图可在初始化时选 `images: off` 跳过
- 自动落位 `Strata-data/models/`

### 下载过程（脚本自动做的事）

1. `START-HERE.bat` 首次运行 → 问 4 个问题（模型家族 / 量化档位 / 上下文长度 / 是否读图），然后按上面 ①→③ 顺序下载（**支持断点续传**，中断后重跑接着下）
2. 下载完成后自动做 SHA-256 逐分片校验
3. 自动把主模型准备成引擎专用的 pack（`Strata-data/packs/iq2_xs`，含 tokenizer），并抽取 MTP 层
4. 全部就绪后生成启动脚本；之后日常只需 `START.bat`

**手动下载**（如需用下载器加速）：把 ① 的两个分片放到 `Strata-data/models/IQ2_XS/`、③ 放到 `Strata-data/models/`，再运行一次 `START-HERE.bat` —— 脚本检测到文件已存在会跳过下载，直接进入校验与打包。

**大陆网络**：huggingface.co 不可达时，用 `--source modelscope` 参数（或环境变量 `STRATA_SOURCE=modelscope`）切换到 ModelScope 镜像，仓库与文件路径完全一致。

> 硬件参考：24 GB 显存 + 128 GB 内存实测流畅（约 30+ tok/s）。其他配置参考上游 README。

## 与上游的关系

- 定制集中在 `engine/serve/web/index.html`（前端）与 `strata-iq2_xs.json`（启动配置）
- 引擎更新走官方路线：双击 `SYNC-UPSTREAM.bat` 拉取上游新版，前端定制已隔离、不冲突

## 目录结构

```
├─ START.bat            日常启动（加载模型 + 开浏览器）
├─ SYNC-UPSTREAM.bat    从上游拉取引擎更新
├─ shots/               界面截图
├─ engine/              Strata 引擎（官方源码 + 定制前端）
│  └─ START-HERE.bat    首次初始化入口
└─ Strata-data/         模型与会话数据（首次运行时下载/生成，不入库）
```

## 作者与开源协议

**作者**：[猫叔哥-](https://space.bilibili.com/108196159)（GitHub: [SuperWJ062](https://github.com/SuperWJ062)）—— NEXUS 前端界面、服务端配置与部署文档的全部定制。

**开源协议**

| 组件 | 协议 | 说明 |
|---|---|---|
| 本仓库（NEXUS 定制层） | [MIT](LICENSE) | 前端定制、打包与文档，可自由使用/修改/分发 |
| 引擎 Strata（上游 [Niko1221/Strata](https://github.com/Niko1221/Strata)） | MIT | Copyright (c) 2026 Niko1221 and the Strata contributors |
| llama.cpp / ggml | MIT | 引擎所用推理组件 |

**模型协议**（模型文件不在本仓库内，使用时请遵守各自协议）：
- 基座模型 [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) — Qwen 团队
- IQ2_XS 量化版 [ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF) — 量化版协议以其仓库页面为准
- MTP 草稿层抽自 Qwen 官方原始 checkpoint

## 致谢

- [Niko1221/Strata](https://github.com/Niko1221/Strata) — 优秀的本地大模型引擎，本项目的基座
- [Qwen 团队](https://huggingface.co/Qwen) — Qwen3.8-Flash-Next 原始模型
- [ISTA-DASLab](https://huggingface.co/ISTA-DASLab) — GSQ-RCO 量化
- [llama.cpp / ggml](https://github.com/ggml-org/llama.cpp) — 底层推理

## 更新到新版本

项目发布新版后，在部署目录里两步：

```
git pull
engine\UPDATE.bat
```

- `git pull`：更新前端（`engine/serve/web/index.html`）、脚本与文档 —— 界面随仓库即时升级
- `engine\UPDATE.bat`：增量更新 Python 依赖与预编译引擎；**模型、MTP、会话数据一概不动，不需要重新下载**
- 你的本机配置（`engine/strata-iq2_xs.json`、`run-iq2_xs.bat`）由首次部署的 setup 自动生成，**不在 git 管理范围内，更新永远不会碰到它，也不会产生任何冲突**——也可以直接在前端 设置→系统与更新 一键完成
- 想参考作者的参数搭配？看 `engine/strata-iq2_xs.json.release`（模板存档，不会被运行读取）
