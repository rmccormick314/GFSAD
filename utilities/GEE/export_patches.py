"""
Export 64x64 satellite embedding patches paired with USDA CDL crop labels.
Saves a .npz file usable by the PyTorch CropPatchDataset.

Usage:
    python export_patches.py
"""

import sys
import importlib.util
import subprocess

_REQUIRED = {"ee": "earthengine-api", "numpy": "numpy"}

def _ensure_deps():
    missing = [pip for mod, pip in _REQUIRED.items() if importlib.util.find_spec(mod) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

_ensure_deps()

import ee
import numpy as np
from pathlib import Path
from satellite_embeddings import init_ee, load_collection, EMBEDDING_BANDS

# ---------------------------------------------------------------------------
# Label source: USDA Cropland Data Layer (US only, annual, 30 m)
# ---------------------------------------------------------------------------
CDL_COLLECTION = "USDA/NASS/CDL"

# Map CDL integer codes -> compact class index (0 = other/non-crop)
# Tuned for California Central Valley (San Joaquin / Tulare Basin)
CDL_REMAP = {
    # Grains
    1:   1,   # Corn
    3:   1,   # Rice
    21:  1,   # Winter wheat
    22:  1,   # Durum wheat
    23:  1,   # Spring wheat
    # Cotton
    2:   2,   # Cotton
    # Field crops
    5:   3,   # Soybeans
    54:  3,   # Tomatoes
    # Tree nuts (almonds, pistachios, walnuts dominate San Joaquin)
    204: 4,   # Pistachios
    217: 4,   # Almonds
    218: 4,   # Walnuts
    # Grapes / vineyards
    69:  5,   # Grapes
    # Citrus
    212: 6,   # Citrus
    # Forage
    36:  7,   # Alfalfa
    37:  7,   # Other hay
    176: 7,   # Grassland / pasture
}
NUM_CLASSES = 8
CLASS_NAMES = ["other", "grains", "cotton", "field_crops",
               "tree_nuts", "grapes", "citrus", "forage"]

PATCH_SIZE = 64   # pixels
SCALE      = 10   # metres per pixel (native embedding resolution)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cdl_image(year: int) -> ee.Image:
    return (ee.ImageCollection(CDL_COLLECTION)
              .filterDate(f"{year}-01-01", f"{year}-12-31")
              .first()
              .select("cropland"))


def get_label(point: ee.Geometry.Point, year: int) -> int:
    val = (_cdl_image(year)
           .sample(region=point, scale=30, numPixels=1)
           .first()
           .get("cropland")
           .getInfo())
    return CDL_REMAP.get(int(val), 0)


def get_patch(point: ee.Geometry.Point, year: int) -> "np.ndarray | None":
    """
    Returns float32 array of shape (64, PATCH_SIZE, PATCH_SIZE) or None on failure.
    The 64 leading dimension is the embedding channel axis.
    """
    half   = (PATCH_SIZE * SCALE) / 2
    region = point.buffer(half).bounds()
    image  = (load_collection(year=year)
              .filterBounds(region)
              .mosaic()
              .select(EMBEDDING_BANDS))
    try:
        rect  = image.sampleRectangle(region=region, defaultValue=0).getInfo()
        props = rect["properties"]
        arrays = [np.array(props[b], dtype=np.float32) for b in EMBEDDING_BANDS]
        patch  = np.stack(arrays, axis=0)          # (64, H, W)
    except Exception as exc:
        print(f"    sampleRectangle failed: {exc}")
        return None

    # Crop / zero-pad to exactly PATCH_SIZE × PATCH_SIZE
    _, h, w = patch.shape
    out = np.zeros((len(EMBEDDING_BANDS), PATCH_SIZE, PATCH_SIZE), dtype=np.float32)
    out[:, :min(h, PATCH_SIZE), :min(w, PATCH_SIZE)] = patch[:, :PATCH_SIZE, :PATCH_SIZE]
    return out


# ---------------------------------------------------------------------------
# Main export
# ---------------------------------------------------------------------------

def build_dataset(
    points: list[tuple[float, float]],
    year:   int,
    out_path: str,
):
    """
    Sample patches and labels for each (lon, lat) point and save to out_path.npz.

    The saved arrays:
        patches : (N, 64, PATCH_SIZE, PATCH_SIZE)  float32
        labels  : (N,)                              int64
    """
    patches, labels = [], []

    for i, (lon, lat) in enumerate(points):
        print(f"[{i+1:>4}/{len(points)}] lon={lon:.4f} lat={lat:.4f}", end="  ")
        pt = ee.Geometry.Point([lon, lat])

        label = get_label(pt, year)
        patch = get_patch(pt, year)

        if patch is not None:
            patches.append(patch)
            labels.append(label)
            print(f"class {label} ({CLASS_NAMES[label]})")
        else:
            print("skipped")

    patches_arr = np.stack(patches)                   # (N, 64, 64, 64)
    labels_arr  = np.array(labels, dtype=np.int64)    # (N,)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    np.savez(out_path, patches=patches_arr, labels=labels_arr,
             class_names=CLASS_NAMES, year=year)

    print(f"\nSaved {len(patches_arr)} patches -> {out_path}")
    counts = np.bincount(labels_arr, minlength=NUM_CLASSES)
    for cls, (name, count) in enumerate(zip(CLASS_NAMES, counts)):
        print(f"  {cls}: {name:<15} {count}")


if __name__ == "__main__":
    init_ee(project="ee-rmccormick314-gfsad", authenticate=False)

    # Tulare / Kings County, CA — dense mixed farming in the San Joaquin Valley:
    # almonds, pistachios, grapes, cotton, tomatoes, citrus, alfalfa, wheat
    rng  = np.random.default_rng(42)
    lons = rng.uniform(-119.8, -119.3, 150)
    lats = rng.uniform(  36.1,   36.6, 150)

    build_dataset(
        points   = list(zip(lons, lats)),
        year     = 2022,
        out_path = "../../data/patches_ca_2022.npz",
    )
