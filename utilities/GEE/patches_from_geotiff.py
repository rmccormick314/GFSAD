"""
Convert exported GeoTIFFs (embedding + CDL) into a .npz patch dataset
using a sliding window. Replaces the slow per-patch sampleRectangle approach.

A 50 km × 50 km AOI at 10 m/px is ~5000×5000 pixels.
With patch_size=64, stride=64: ~6,000 non-overlapping patches.
With patch_size=64, stride=32: ~24,000 overlapping patches.

Usage:
    python patches_from_geotiff.py \\
        --embed  ../../data/geotiff/ca_sjv_embeddings_2022.tif \\
        --cdl    ../../data/geotiff/ca_sjv_cdl_2022.tif \\
        --out    ../../data/patches_ca_large.npz
"""

import sys
import importlib.util
import subprocess

_REQUIRED = {"rasterio": "rasterio", "numpy": "numpy"}
def _ensure_deps():
    missing = [pip for mod, pip in _REQUIRED.items() if importlib.util.find_spec(mod) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
_ensure_deps()

import argparse
import numpy as np
import rasterio
from rasterio.enums import Resampling
from pathlib import Path
from export_patches import CDL_REMAP, NUM_CLASSES, CLASS_NAMES


def load_geotiffs(embed_path: str, cdl_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns:
        embeddings : (64, H, W)  float32  — 64 embedding bands
        cdl        : (H, W)      int32    — raw CDL crop codes
    """
    with rasterio.open(embed_path) as src:
        embeddings = src.read().astype(np.float32)   # (64, H, W)

    H, W = embeddings.shape[1], embeddings.shape[2]

    with rasterio.open(cdl_path) as src:
        # Resample CDL to match the embedding grid size exactly
        cdl = src.read(
            1,
            out_shape=(H, W),
            resampling=Resampling.nearest,
        ).astype(np.int32)

    print(f"Embedding : {embeddings.shape}  ({H*W:,} pixels)")
    print(f"CDL       : {cdl.shape}")
    return embeddings, cdl


def extract_patches(
    embeddings: np.ndarray,
    cdl:        np.ndarray,
    patch_size: int = 64,
    stride:     int = 64,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Slide a window over the image and collect (patch, label) pairs.
    Label is the CDL class at the patch center pixel.

    stride=patch_size  → no overlap, fastest, fewest patches
    stride=patch_size//2 → 50% overlap, 4× more patches, some redundancy
    """
    _, H, W  = embeddings.shape
    half     = patch_size // 2
    patches, labels = [], []

    row_starts = range(0, H - patch_size + 1, stride)
    col_starts = range(0, W - patch_size + 1, stride)
    total = len(row_starts) * len(col_starts)
    print(f"Grid: {len(row_starts)} rows × {len(col_starts)} cols = {total:,} patches")

    done = 0
    for r in row_starts:
        for c in col_starts:
            patch     = embeddings[:, r:r+patch_size, c:c+patch_size]
            label_raw = int(cdl[r + half, c + half])
            label     = CDL_REMAP.get(label_raw, 0)
            patches.append(patch)
            labels.append(label)
            done += 1
        if done % 500 == 0:
            print(f"  {done:>7,} / {total:,}", end="\r")

    print(f"  {done:>7,} / {total:,}  done")
    return (np.stack(patches).astype(np.float32),
            np.array(labels, dtype=np.int64))


def main(cfg: argparse.Namespace):
    embeddings, cdl = load_geotiffs(cfg.embed, cfg.cdl)
    patches, labels = extract_patches(embeddings, cdl, cfg.patch_size, cfg.stride)

    Path(cfg.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez(cfg.out, patches=patches, labels=labels,
             class_names=CLASS_NAMES, year=cfg.year)

    mb = patches.nbytes / 1e6
    print(f"\nSaved {len(patches):,} patches ({mb:.0f} MB) → {cfg.out}")

    print("\nClass distribution:")
    counts  = np.bincount(labels, minlength=NUM_CLASSES)
    max_cnt = counts.max()
    for cls, (name, count) in enumerate(zip(CLASS_NAMES, counts)):
        bar = "█" * int(count * 40 / max(max_cnt, 1))
        pct = count / len(labels) * 100
        print(f"  {cls} {name:<15} {count:>7,}  {pct:5.1f}%  {bar}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed",      required=True,
                        help="Path to embedding GeoTIFF (ca_sjv_embeddings_2022.tif)")
    parser.add_argument("--cdl",        required=True,
                        help="Path to CDL GeoTIFF (ca_sjv_cdl_2022.tif)")
    parser.add_argument("--out",        default="../../data/patches_ca_large.npz")
    parser.add_argument("--patch_size", type=int, default=64)
    parser.add_argument("--stride",     type=int, default=64,
                        help="Pixel stride between patches. "
                             "Use patch_size for no overlap, patch_size//2 for 50%% overlap.")
    parser.add_argument("--year",       type=int, default=2022)
    main(parser.parse_args())
