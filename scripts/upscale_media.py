#!/usr/bin/env python3
"""Porta in 4K le foto e i video del sito (i video anche a 60 fps).

Il sito resta un progetto statico senza build step: questo script serve solo a
rigenerare gli asset multimediali quando si sostituisce una foto o un video.
Non è eseguito dal sito né dal workflow di sincronizzazione Telegram.

Cosa fa
-------
* **Foto** — super-risoluzione AI con Real-ESRGAN (modelli ncnn, eseguibili su
  CPU) fino a 4K (3840x2160), poi genera le varianti responsive WebP/JPEG
  (3840 / 2560 / 1920 / 1280) usate dagli attributi `srcset` nelle pagine.
* **Video** — porta il video a 3840x2160 a 60 fps: leggera riduzione del rumore,
  interpolazione dei fotogrammi con stima del movimento (motion compensated) e
  ingrandimento Lanczos con sharpening finale, codifica H.264 ottimizzata.

Requisiti (solo per chi rigenera gli asset)
-------------------------------------------
```bash
pip install pillow ncnn sr-vulkan-model-realesrgan imageio-ffmpeg
```
* `ncnn` + `sr-vulkan-model-realesrgan`: modello Real-ESRGAN x4plus. Se mancano,
  le foto vengono comunque portate a 4K con Lanczos (nessun dettaglo in più).
* `imageio-ffmpeg`: fornisce un binario ffmpeg statico. In alternativa basta
  avere `ffmpeg` nel PATH oppure esportare `FFMPEG=/percorso/ffmpeg`.

Uso
---
```bash
python3 scripts/upscale_media.py            # foto + video + varianti
python3 scripts/upscale_media.py --only images
python3 scripts/upscale_media.py --only video
python3 scripts/upscale_media.py --only variants
python3 scripts/upscale_media.py --dry-run  # mostra cosa farebbe
```
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Serve Pillow: pip install pillow")

ROOT = Path(__file__).resolve().parents[1]

# ---- impostazioni -----------------------------------------------------------
TARGET_W, TARGET_H = 3840, 2160        # 4K
TARGET_FPS = 60                        # frame rate di uscita dei video
VARIANT_WIDTHS = (3840, 2560, 1920, 1280)
JPEG_MASTER_QUALITY = 92               # qualità del master 4K
JPEG_VARIANT_QUALITY = 88
WEBP_QUALITY = 84
VIDEO_CRF = 30                         # 4K60 "compresso al massimo"
TILE = 240                             # riquadri per l'upscaling AI (memoria)
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")
VIDEO_SUFFIXES = (".mp4", ".webm", ".mov")


# ---- helper -----------------------------------------------------------------
def log(msg: str) -> None:
    print(msg, flush=True)


def find_ffmpeg() -> str | None:
    """Binario ffmpeg: variabile FFMPEG, imageio-ffmpeg o PATH."""
    env = os.environ.get("FFMPEG")
    if env and Path(env).exists():
        return env
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def fit_target(size: tuple[int, int]) -> tuple[int, int]:
    """Ridimensiona per stare dentro il 4K mantenendo le proporzioni."""
    w, h = size
    scale = min(TARGET_W / w, TARGET_H / h, 1.0)
    return (max(1, round(w * scale)), max(1, round(h * scale)))


# ---- super-risoluzione AI ---------------------------------------------------
class Upscaler:
    """Real-ESRGAN x4plus via ncnn (con tiling per limitare la memoria)."""

    def __init__(self, model: str = "x4plus"):
        self.model = model
        self.scale = 4
        self.net = None
        try:
            import numpy as np
            import ncnn
            import sr_vulkan_model_realesrgan

            models_dir = Path(sr_vulkan_model_realesrgan.__file__).parent / "models"
        except Exception:
            log("  ! ncnn o i modelli Real-ESRGAN non disponibili: uso Lanczos")
            return
        self.ncnn, self.np = ncnn, np
        param = models_dir / f"REALESRGAN_{model.upper()}_UP4X.param"
        weights = models_dir / f"REALESRGAN_{model.upper()}_UP4X.bin"
        if not param.exists() or not weights.exists():
            log("  ! modelli Real-ESRGAN non trovati: uso Lanczos")
            return
        net = ncnn.Net()
        net.opt.use_vulkan_compute = False
        net.opt.num_threads = os.cpu_count() or 1
        net.load_param(str(param))
        net.load_model(str(weights))
        self.net = net
        log(f"  modello: Real-ESRGAN {model} (x4, ncnn CPU)")

    def available(self) -> bool:
        return self.net is not None

    def _infer(self, rgb):
        """Esegue il modello su un array RGB uint8 (H, W, 3) -> uint8 x4."""
        np = self.np
        h, w = rgb.shape[:2]
        mat = self.ncnn.Mat.from_pixels(
            rgb.tobytes(), self.ncnn.Mat.PixelType.PIXEL_RGB, w, h
        )
        mat.substract_mean_normalize([0.0, 0.0, 0.0], [1 / 255.0] * 3)
        ex = self.net.create_extractor()
        ex.input("data", mat)
        _, out = ex.extract("output")
        arr = np.array(out)  # (c, h, w) float32 in 0..1
        if arr.ndim == 3 and arr.shape[0] == 3 and arr.shape[2] != 3:
            arr = arr.transpose(1, 2, 0)
        return np.clip(arr * 255.0, 0, 255).astype("uint8")

    def process(self, img: "Image.Image") -> "Image.Image":
        if not self.available():
            return img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
        np = self.np
        rgb = np.array(img.convert("RGB"))
        h, w = rgb.shape[:2]
        if h <= TILE and w <= TILE:
            out = self._infer(np.ascontiguousarray(rgb))
            return Image.fromarray(out)
        prepad = 10
        padded = np.pad(rgb, ((prepad, prepad), (prepad, prepad), (0, 0)), "reflect")
        canvas = np.zeros((h * self.scale, w * self.scale, 3), dtype="uint8")
        ny, nx = (h + TILE - 1) // TILE, (w + TILE - 1) // TILE
        done = 0
        for iy in range(ny):
            for ix in range(nx):
                y0, x0 = iy * TILE, ix * TILE
                y1, x1 = min(y0 + TILE, h), min(x0 + TILE, w)
                chunk = padded[y0:y1 + 2 * prepad, x0:x1 + 2 * prepad]
                res = self._infer(np.ascontiguousarray(chunk))
                p = prepad * self.scale
                res = res[p:p + (y1 - y0) * self.scale, p:p + (x1 - x0) * self.scale]
                canvas[y0 * self.scale:y1 * self.scale, x0 * self.scale:x1 * self.scale] = res
                done += 1
                log(f"    tile {done}/{ny * nx}")
        return Image.fromarray(canvas)


# ---- foto -------------------------------------------------------------------
def master_images() -> list[Path]:
    """Immagini "master" del sito (esclude le varianti già generate)."""
    out = []
    for folder in ("assets/images", "assets/videos"):
        base = ROOT / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            if any(f"-{w}" in path.stem for w in VARIANT_WIDTHS):
                continue  # variante generata, non un master
            out.append(path)
    return out


def upscale_images(dry_run: bool = False) -> None:
    images = master_images()
    if not images:
        log("Nessuna immagine da upscalare.")
        return
    todo = []
    for path in images:
        with Image.open(path) as im:
            w, h = im.size
        if w >= TARGET_W or h >= TARGET_H:
            log(f"- {path.relative_to(ROOT)}: già {w}x{h}, salto")
            continue
        todo.append((path, w, h))
    if not todo:
        log("Tutte le immagini sono già in 4K.")
        return
    up = Upscaler()
    for path, w, h in todo:
        log(f"- {path.relative_to(ROOT)}: {w}x{h} -> 4K")
        if dry_run:
            continue
        with Image.open(path) as im:
            img = im.convert("RGB")
        res = up.process(img)
        target = fit_target(res.size)
        if res.size != target:
            res = res.resize(target, Image.LANCZOS)
        tmp = path.with_suffix(".upscaled.jpg")
        res.save(tmp, quality=JPEG_MASTER_QUALITY, optimize=True, progressive=True)
        if path.suffix.lower() in (".png", ".webp"):
            path.unlink()
            path = path.with_suffix(".jpg")
        tmp.replace(path)
        log(f"  salvato {path.name} {res.size[0]}x{res.size[1]} "
            f"({path.stat().st_size / 1e6:.2f} MB)")


def build_variants(dry_run: bool = False) -> None:
    """Genera le copie ridotte (WebP + JPEG) usate dal srcset."""
    for path in master_images():
        with Image.open(path) as im:
            img = im.convert("RGB")
        stem, ext = path.stem, path.suffix.lower()
        for width in VARIANT_WIDTHS:
            if width >= img.width:
                # la variante più grande è il master: la serviamo in WebP
                if ext == ".jpg" or ext == ".jpeg":
                    webp = path.with_name(f"{stem}-{width}.webp")
                    if not dry_run:
                        img.save(webp, quality=WEBP_QUALITY, method=6)
                    log(f"  + {webp.name}")
                continue
            height = round(img.height * width / img.width)
            small = img.resize((width, height), Image.LANCZOS)
            webp = path.with_name(f"{stem}-{width}.webp")
            jpg = path.with_name(f"{stem}-{width}.jpg")
            if not dry_run:
                small.save(webp, quality=WEBP_QUALITY, method=6)
            log(f"  + {webp.name}")
            if width == 1920 and not dry_run:
                small.save(jpg, quality=JPEG_VARIANT_QUALITY, optimize=True,
                           progressive=True)
                log(f"  + {jpg.name}")


# ---- video ------------------------------------------------------------------
def find_videos() -> list[Path]:
    base = ROOT / "assets" / "videos"
    if not base.exists():
        return []
    return [p for p in sorted(base.iterdir()) if p.suffix.lower() in VIDEO_SUFFIXES]


def video_info(ffmpeg: str, path: Path) -> tuple[int, int, float, bool]:
    """Restituisce (larghezza, altezza, fps, ha_audio)."""
    proc = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)],
                          capture_output=True, text=True)
    text = proc.stderr
    w = h = 0
    fps = 0.0
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Stream #") and "Video:" in line:
            for chunk in line.split(","):
                chunk = chunk.strip()
                if "x" in chunk and chunk.split("x")[0].isdigit():
                    dims = chunk.split(" ")[0]
                    w, h = (int(v) for v in dims.split("x"))
                if "fps" in chunk:
                    fps = float(chunk.split(" ")[0])
    return w, h, fps, "Audio:" in text


def upscale_videos(dry_run: bool = False) -> None:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        log("! ffmpeg non trovato: installalo (pip install imageio-ffmpeg) "
            "o esporta FFMPEG=/percorso/ffmpeg")
        return
    for path in find_videos():
        w, h, fps, audio = video_info(ffmpeg, path)
        if not w:
            log(f"- {path.name}: impossibile leggere le informazioni, salto")
            continue
        if w >= TARGET_W and fps >= TARGET_FPS - 0.5:
            log(f"- {path.name}: già {w}x{h} @ {fps:.2f} fps, salto")
            continue
        log(f"- {path.name}: {w}x{h} @ {fps:.2f} fps -> {TARGET_W}x{TARGET_H} "
            f"@ {TARGET_FPS} fps (CRF {VIDEO_CRF})")
        if dry_run:
            continue
        filt = (
            "hqdn3d=1.5:1.0:6:6,"
            f"minterpolate=fps={TARGET_FPS}:mi_mode=mci:mc_mode=aobmc:"
            "me_mode=bidir:vsbmc=1:search_param=32,"
            f"scale={TARGET_W}:{TARGET_H}:flags=lanczos,"
            "cas=0.45,format=yuv420p"
        )
        tmp = Path(tempfile.mkstemp(suffix=".mp4", dir=str(path.parent))[1])
        cmd = [ffmpeg, "-y", "-v", "error", "-stats", "-i", str(path),
               "-map", "0:v:0", "-map", "0:a?", "-vf", filt,
               "-c:v", "libx264", "-preset", "slower", "-crf", str(VIDEO_CRF),
               "-profile:v", "high", "-level:v", "5.2", "-g", str(TARGET_FPS * 2),
               "-c:a", "copy", "-movflags", "+faststart", str(tmp)]
        run(cmd)
        shutil.copystat(path, tmp)
        tmp.replace(path)
        nw, nh, nfp, _ = video_info(ffmpeg, path)
        log(f"  fatto: {nw}x{nh} @ {nfp:.2f} fps "
            f"({path.stat().st_size / 1e6:.2f} MB)")


# ---- main -------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=("images", "video", "variants"),
                    help="esegui una sola fase")
    ap.add_argument("--dry-run", action="store_true",
                    help="mostra cosa verrebbe fatto senza modificare i file")
    args = ap.parse_args()

    only = args.only
    log(f"Progetto: {ROOT}")
    if only in (None, "images"):
        log("== Foto ==")
        upscale_images(args.dry_run)
    if only in (None, "video"):
        log("== Video ==")
        upscale_videos(args.dry_run)
    if only in (None, "variants"):
        log("== Varianti responsive ==")
        build_variants(args.dry_run)
    log("Fatto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
