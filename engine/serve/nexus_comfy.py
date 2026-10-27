"""NEXUS local: image generation through a running ComfyUI (config's "images" section with backend "comfyui").

Why this exists: the upstream path compiles stable-diffusion.cpp into engine-image/sd-cli and loads .gguf weights.
This machine already runs ComfyUI with Qwen-Image-2.1-Turbo in ComfyUI's own formats (safetensors), so the image
endpoint forwards the job to ComfyUI's API instead of duplicating 13 GB of gguf weights and a C++ build.

The config's "images" section looks like this (paths are ComfyUI's model names, not local files):

  {"backend": "comfyui", "comfy_url": "http://127.0.0.1:8188",
   "unet": "qwen_image_2.1_turbo_bf16.safetensors", "clip": "qwen3vl_8b_bf16.safetensors",
   "vae": "qwen_image_2.1_vae_bf16.safetensors", "clip_type": "qwen_image",
   "sampler": "euler_ancestral", "sigmas": "1.0,0.978453,...", "cfg": 1.0,
   "steps": 8, "need_mib": 20000, "timeout_s": 600, "max_n": 4, "max_side": 2048,
   "comfy_launch": "D:/ComfyUI-aki/run_nvidia_gpu.bat", "comfy_boot_s": 180}

`comfy_launch` is optional: when ComfyUI is not answering, the server starts it and waits up to `comfy_boot_s` for
/prompt to answer.  ComfyUI keeps running afterwards (its models stay on the GPU until it is closed or /free is
called), so the GPU policy here is always "keep" - this module never unloads the chat engine.

ComfyUI's own workflow format is not sent: the API's `prompt` graph is built here from the config, so changing the
model or the sampler is a config edit, not a workflow export.
"""
from __future__ import annotations

import json
import random
import secrets
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from serve.images import ImageGen, ImageJobFailed

# Qwen-Image-2.1-Turbo's own schedule (8 steps, CFG 1): the same sigmas the upstream config carries.
TURBO_SIGMAS = "1.0,0.978453,0.95418,0.926626,0.89508,0.845148,0.704534,0.414568,0.0"


def _node(class_type: str, **inputs) -> dict:
    return {"class_type": class_type, "inputs": inputs}


class ComfyImageGen(ImageGen):
    """ImageGen's interface (run/store/response/status/file), a ComfyUI job per request."""

    def __init__(self, cfg: dict, log=None):
        self.cfg = dict(cfg)
        self.policy = "keep"                      # never make the chat engine give up its VRAM for this one
        self.reload = "lazy"
        self.model = self.cfg.get("model_name") or "qwen-image-2.1-turbo"
        self.log = log
        out = self.cfg.get("out_dir")
        if out:
            self.dir = Path(out)
            self.dir.mkdir(parents=True, exist_ok=True)
        else:
            import tempfile
            self.dir = Path(tempfile.mkdtemp(prefix="strata-images-"))
        self.keep_files = int(self.cfg.get("keep_files") or 64)
        self.lock = threading.Lock()
        self.totals = {"images": 0, "jobs": 0, "seconds": 0.0, "failed": 0}
        self.last = None
        self.progress = None
        self.url = (self.cfg.get("comfy_url") or "http://127.0.0.1:8188").rstrip("/")
        self._launched = False

    # ------------------------------------------------------------------ the ComfyUI API
    def _call(self, path: str, body: dict | None = None, timeout: float = 60) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.url + path, data=data,
                                     headers={"Content-Type": "application/json"} if data else {})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # never through a proxy
        with opener.open(req, timeout=timeout) as f:
            raw = f.read()
        return json.loads(raw.decode("utf-8")) if raw else {}

    def _alive(self) -> bool:
        try:
            self._call("/system_stats", timeout=3)
            return True
        except (urllib.error.URLError, OSError, ValueError):
            return False

    def _ensure_running(self) -> None:
        if self._alive():
            return
        launch = self.cfg.get("comfy_launch")
        if not launch or self._launched:
            raise ImageJobFailed(f"ComfyUI is not answering at {self.url}; start it (or set \"comfy_launch\" in the "
                                 "config's images section)")
        self._say(f"starting ComfyUI ({launch}); this takes a while")
        subprocess.Popen(["cmd", "/c", str(launch)], creationflags=0x00000008,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._launched = True
        deadline = time.monotonic() + float(self.cfg.get("comfy_boot_s") or 180)
        while time.monotonic() < deadline:
            if self._alive():
                self._say("ComfyUI answered")
                return
            time.sleep(2)
        raise ImageJobFailed(f"ComfyUI did not answer within {self.cfg.get('comfy_boot_s') or 180:g} s of starting")

    # ------------------------------------------------------------------ the workflow
    def _graph(self, job: dict) -> dict:
        cfg = self.cfg
        unet = cfg.get("unet") or "qwen_image_2.1_turbo_bf16.safetensors"
        clip = cfg.get("clip") or "qwen3vl_8b_bf16.safetensors"
        vae = cfg.get("vae") or "qwen_image_2.1_vae_bf16.safetensors"
        steps = int(job["steps"])
        sigmas = cfg.get("sigmas") if steps == int(cfg.get("steps") or 8) else None
        sigmas = sigmas or TURBO_SIGMAS
        return {
            "1": _node("UNETLoader", unet_name=unet, weight_dtype=cfg.get("weight_dtype") or "default"),
            "2": _node("CLIPLoader", clip_name=clip, type=cfg.get("clip_type") or "qwen_image",
                       device=cfg.get("clip_device") or "default"),
            "3": _node("VAELoader", vae_name=vae),
            "4": _node("TextEncodeQwenImage21", clip=["2", 0], prompt=job["prompt"],
                       negative_prompt=cfg.get("negative_prompt") or "", resolution=int(cfg.get("encode_res") or 1024)),
            "5": _node("EmptyLatentImage", width=job["width"], height=job["height"], batch_size=job["n"]),
            "6": _node("RandomNoise", noise_seed=job["seed"]),
            "7": _node("KSamplerSelect", sampler_name=cfg.get("sampler") or "euler_ancestral"),
            "8": _node("ManualSigmas", sigmas=str(sigmas).replace(" ", "")),
            "9": _node("CFGGuider", model=["1", 0], positive=["4", 0], negative=["4", 1],
                       cfg=float(cfg.get("cfg") or 1.0)),
            "10": _node("SamplerCustomAdvanced", noise=["6", 0], guider=["9", 0], sampler=["7", 0],
                        sigmas=["8", 0], latent_image=["5", 0]),
            "11": _node("VAEDecode", samples=["10", 0], vae=["3", 0]),
            "12": _node("SaveImage", images=["11", 0],
                        filename_prefix=cfg.get("filename_prefix") or "strata"),
        }

    # ------------------------------------------------------------------ ImageGen's interface
    def missing(self) -> list[str]:
        return []                                  # the weights live on ComfyUI's side: nothing local to check

    def run(self, job: dict, cancel: threading.Event | None = None) -> tuple[list[bytes], dict]:
        """One ComfyUI job -> (the PNG files' bytes in order, figures)."""
        self._ensure_running()
        t0 = time.monotonic()
        timeout = float(self.cfg.get("timeout_s") or 600)
        self.progress = (0, job["steps"])
        with self.lock:
            try:
                queued = self._call("/prompt", {"prompt": self._graph(job),
                                                "client_id": secrets.token_hex(8)}, timeout=60)
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:600]
                self.totals["failed"] += 1
                raise ImageJobFailed(f"ComfyUI refused the workflow ({e.code}): {detail}") from e
            except (urllib.error.URLError, OSError) as e:
                self.totals["failed"] += 1
                raise ImageJobFailed(f"ComfyUI is not reachable at {self.url}: {e}") from e
            bad = queued.get("node_errors") or {}
            if bad:
                self.totals["failed"] += 1
                raise ImageJobFailed("ComfyUI rejected these nodes: " +
                                     json.dumps(bad, ensure_ascii=False)[:800])
            pid = queued.get("prompt_id")
            if not pid:
                self.totals["failed"] += 1
                raise ImageJobFailed(f"ComfyUI returned no prompt_id: {json.dumps(queued)[:300]}")

            why = None
            entry = {}
            while True:
                if cancel is not None and cancel.is_set():
                    why = "cancelled (the client left)"
                elif time.monotonic() - t0 > timeout:
                    why = f"it ran past timeout_s ({timeout:g} s)"
                if why:
                    try:
                        self._call("/interrupt", {}, timeout=10)      # stop whatever ComfyUI is doing now
                    except (urllib.error.URLError, OSError):
                        pass
                    break
                try:
                    hist = self._call(f"/history/{pid}", timeout=30)
                except (urllib.error.URLError, OSError):
                    hist = {}
                entry = hist.get(pid) or {}
                st = (entry.get("status") or {})
                if entry and (st.get("completed") or st.get("status_str") in ("success", "error")):
                    break
                if self.progress:
                    self.progress = (min(self.progress[0] + 1, job["steps"]), job["steps"])
                time.sleep(0.8)
        self.progress = None
        secs = time.monotonic() - t0

        if why:
            self.totals["failed"] += 1
            raise ImageJobFailed(why)
        st = entry.get("status") or {}
        if st.get("status_str") == "error":
            msgs = [m for m in (st.get("messages") or []) if m and m[0] == "execution_error"]
            detail = json.dumps(msgs[-1][1] if msgs else st, ensure_ascii=False)[:800]
            self.totals["failed"] += 1
            raise ImageJobFailed(f"ComfyUI failed to run the workflow: {detail}")

        files: list[dict] = []
        for out in (entry.get("outputs") or {}).values():
            files.extend(out.get("images") or [])
        files = [f for f in files if f.get("type") in (None, "output", "temp")][:job["n"]]
        if not files:
            self.totals["failed"] += 1
            raise ImageJobFailed("ComfyUI finished but wrote no image (is SaveImage still in the graph?)")

        images = [self._fetch(f) for f in files]
        figures = {"seconds": round(secs, 2), "steps": job["steps"], "n": job["n"],
                   "size": f"{job['width']}x{job['height']}", "seed": job["seed"],
                   "backend": "comfyui", "quant": self.cfg.get("quant") or "safetensors",
                   "comfy_url": self.url}
        self.totals["jobs"] += 1
        self.totals["images"] += len(images)
        self.totals["seconds"] += secs
        self.last = figures
        return images, figures

    def _fetch(self, item: dict) -> bytes:
        q = urllib.parse.urlencode({"filename": item.get("filename") or "",
                                    "subfolder": item.get("subfolder") or "",
                                    "type": item.get("type") or "output"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(self.url + "/view?" + q, timeout=120) as f:
                return f.read()
        except (urllib.error.URLError, OSError) as e:
            raise ImageJobFailed(f"ComfyUI wrote {item.get('filename')!r} but it cannot be fetched: {e}") from e

    def status(self) -> dict:
        out = super().status()
        out["comfy_url"] = self.url
        out["reachable"] = self._alive()
        return out
