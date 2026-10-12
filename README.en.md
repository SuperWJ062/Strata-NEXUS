# Strata NEXUS — Local LLM Workstation (Frontend Custom Edition)

[简体中文](README.md) · **English**

![version](https://img.shields.io/badge/version-v0.60-71f6d2) ![engine](https://img.shields.io/badge/engine-0.1.42-9b8cff) ![license](https://img.shields.io/badge/license-MIT-8291aa)

**Current release v0.60** (2026-10-12) · see the [中文更新日志](CHANGELOG.md) for release notes

A **deeply customized frontend** for the [Niko1221/Strata](https://github.com/Niko1221/Strata) engine. The engine stays stock — the entire interface is rebuilt: local inference that looks, feels and tunes like a proper workstation.

## Screenshots

**Overview** — generation speed / VRAM / model status / API traffic on one screen

![Overview](shots/nexus-overview.png)

**Chat** — streaming, Markdown rendering, folded reasoning, parameter panel; the whole page is viewport-locked with no layout jumps

![Chat](shots/nexus-chat.png)

**Monitoring** — live GPU/VRAM/CPU/RAM levels plus service health checks (health/status/metrics/slots)

![Monitoring](shots/nexus-monitor.png)

**Preferences** — themes / fonts / colors / motion, all adjustable in-app, applied instantly and persisted locally

![Preferences](shots/nexus-settings.png)

## What changed vs. the stock frontend

### Interface architecture
- **All-new NEXUS visual system**: dark glassmorphism + ambient glow, replacing the stock interface
- **4 themes** (Aurora / Glacier / Ember / Mono), compact/comfortable density, independent toggles for ambient glow, flicker motion and reduced motion
- **Custom accent colors**: theme color, secondary color, primary/muted text colors managed globally

### Typography & readability
- **Three-zone font sizing**: interface / code / hint sizes as separate sliders (globally calc-derived, every step visible), independent of each other
- **Per-chat text control**: separate chat font size + color; Markdown / plain rendering selectable, **Markdown by default** (headings, tables, code blocks, quotes)
- **3 syntax highlighting themes** (Aurora / Classic / GitHub), hand-written tokenizer, zero dependencies
- Hint-size auto-adaptation: when the browser clamps minimum font size, the slider floor is raised automatically so every step stays visible

### Chat experience
- **Smart scrolling**: browse freely while generating, auto-resume on scroll-back + jump-to-bottom button
- **Live streaming stats**: tokens/s and elapsed time update per token, replaced by exact values on finish
- **Reasoning folded by default** (summary with token count, expandable)
- **Message actions**: copy / edit (removes following messages) / regenerate / delete
- **Long-prompt progress bar**: shows ingestion progress for >8K-token prompts, stepping per chunk with a running timer

### Data & sessions
- **Session persistence**: one-click save/restore (engine state paired with frontend messages), survives restarts
- **Markdown export** of conversations
- **API request monitor**: last 100 requests viewable in-app

### Polish
- Message alignment (AI flush-left full-width, user bubbles right), input focus glow, unified thin scrollbars
- Tabular numerals for live metrics (no jitter), inner-scrolling code blocks, responsive narrow-window layout
- Server config hot-saved via /config; frontend preferences persisted in localStorage

## Deployment (Windows + NVIDIA GPU)

1. **Clone**
   ```
   git clone https://github.com/SuperWJ062/Strata-NEXUS.git
   cd Strata-NEXUS
   ```
2. **First run**: double-click `engine\START-HERE.bat` and follow the prompts (the model files download automatically — see below; **you may also download them yourself, the two ways never conflict**)
3. **Daily start**: double-click `START.bat` — loads the model and opens `http://127.0.0.1:8080/`

## Model downloads (sources and process)

Current setup uses **Qwen3.8-Flash-Next IQ2_XS**.

**Model repository (Hugging Face)**:
> **https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF**
> (China mirror: https://www.modelscope.cn/models/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF )

Three things to download (main model + MTP draft layer + vision encoder). **Two ways, mix and match, never conflict**:
- **Option A (automatic)**: downloaded by `START-HERE.bat` during first run
- **Option B (manual)**: download from the repository above with any downloader, place the files as noted below

**Why they never conflict**: for every file the script first checks whether the target already exists; if it does, it verifies SHA-256 and **skips the download** (verified output: `[ok] ... already downloaded`). Files are only downloaded when missing or corrupt.

| Item | Size | Files | Destination |
|---|---|---|---|
| Main model | ~68 GB (2 shards) | `Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-0000{1,2}-of-00002.gguf` | `Strata-data/models/IQ2_XS/` |
| MTP draft layer | ~5 GB | extracted from the original Qwen BF16 checkpoint by `tools/mtp_fetch.py` (tensor-hash verified) | `Strata-data/mtp/rt` (automatic) |
| Vision encoder | ~1 GB | `mmproj-Qwen3.8-Flash-Next-BF16.gguf` | `Strata-data/models/` |

**The automatic process**: first run asks 4 questions (family / quant / context / images), then downloads in order with resume support, verifies every shard by SHA-256, prepares the engine pack (`Strata-data/packs/iq2_xs`, including the tokenizer) and the MTP layer, then writes the start scripts.

**Mainland China**: if huggingface.co is unreachable, use `--source modelscope` (or `STRATA_SOURCE=modelscope`) to switch to the ModelScope mirror — same repositories, same file paths.

## Updating to a new release

Two steps in the deploy folder:

```
git pull
engine\UPDATE.bat
```

- `git pull` updates the frontend (`engine/serve/web/index.html`), scripts and docs — the interface upgrades with the repository
- `engine\UPDATE.bat` incrementally updates Python dependencies and the prebuilt engine; **models, MTP and session data are never touched or re-downloaded**
- Your machine-local config (`engine/strata-iq2_xs.json`, `run-iq2_xs.bat`) is generated by setup on first deployment and is **not managed by git — updates can never conflict with it**
- Want the author's parameter set? See `engine/strata-iq2_xs.json.release` (a reference template, never read at runtime)

## Relationship to upstream

- Custom code lives in `engine/serve/web/index.html` (frontend) and `strata-iq2_xs.json.release` (reference config)
- Engine updates follow the official route: run `SYNC-UPSTREAM.bat` to pull upstream releases — the frontend customization is isolated and never conflicts

## Repository layout

```
├─ START.bat            daily start (load model + open browser)
├─ SYNC-UPSTREAM.bat    pull engine updates from upstream
├─ shots/               UI screenshots
├─ engine/              Strata engine (official sources + custom frontend)
│  └─ START-HERE.bat    first-run entry point
└─ Strata-data/         models and sessions (downloaded/generated on first run, not in git)
```

## Author & License

**Author**: [猫叔哥-](https://space.bilibili.com/108196159) (GitHub: [SuperWJ062](https://github.com/SuperWJ062)) — all NEXUS frontend, server configuration and deployment documentation customization.

**License**

| Component | License | Notes |
|---|---|---|
| This repository (NEXUS custom layer) | [MIT](LICENSE) | frontend customization, packaging, docs |
| Strata engine (upstream [Niko1221/Strata](https://github.com/Niko1221/Strata)) | MIT | Copyright (c) 2026 Niko1221 and the Strata contributors |
| llama.cpp / ggml | MIT | inference components |

**Model licenses** (model files are not part of this repository; comply with their own terms):
- Base model [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) — Qwen team
- IQ2_XS quantization [ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF) — see the repository page for its license
- MTP draft layer extracted from the official Qwen checkpoint

## Acknowledgements

- [Niko1221/Strata](https://github.com/Niko1221/Strata) — the excellent local LLM engine this project builds on
- [Qwen team](https://huggingface.co/Qwen) — the original Qwen3.8-Flash-Next model
- [ISTA-DASLab](https://huggingface.co/ISTA-DASLab) — the GSQ-RCO quantization
- [llama.cpp / ggml](https://github.com/ggml-org/llama.cpp) — underlying inference
