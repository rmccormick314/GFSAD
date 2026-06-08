"""
Google Earth Engine - Satellite Embedding Collection
GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL

64-dimensional annual embeddings from Google's satellite imagery foundation model.
Each pixel holds a vector (emb_0 … emb_63) derived from composite Sentinel-2 / Landsat imagery.
Resolution: 10 m/px  |  Tile size: 256 x 256 px  |  Cadence: annual
"""

import importlib.util
import subprocess
import sys

# ---------------------------------------------------------------------------
# 0. Dependency check
# ---------------------------------------------------------------------------
_REQUIRED = {
    "ee":    "earthengine-api",
    "numpy": "numpy",
}

def _ensure_deps():
    missing = [pip_name for mod, pip_name in _REQUIRED.items()
               if importlib.util.find_spec(mod) is None]
    if missing:
        print(f"Installing missing packages: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("Done. Re-importing…")

_ensure_deps()

import ee
import numpy as np


# ---------------------------------------------------------------------------
# 1. Authentication & initialization
# ---------------------------------------------------------------------------
# First-time setup: run ee.Authenticate() once to store credentials locally.
# Afterward, only ee.Initialize() is needed each session.
#
# Replace 'your-cloud-project-id' with your GCP project that has the
# Earth Engine API enabled.

def init_ee(project: str = "ee-rmccormick314-gfsad", authenticate: bool = False):
    if authenticate:
        try:
            # Preferred: uses gcloud ADC, avoids the unverified-app block.
            # Requires: gcloud auth application-default login
            ee.Authenticate(auth_mode="gcloud")
        except Exception:
            # Fallback: opens a browser URL; paste the token back into the terminal.
            ee.Authenticate(auth_mode="notebook")
    ee.Initialize(project=project)
    print("Earth Engine initialized.")


# ---------------------------------------------------------------------------
# 2. Load the collection
# ---------------------------------------------------------------------------
COLLECTION_ID = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"

# The 64 embedding bands are named emb_0 through emb_63.
EMBEDDING_BANDS = [f"A{i:02d}" for i in range(64)]


def load_collection(year: int | None = None, aoi: ee.Geometry | None = None) -> ee.ImageCollection:
    col = ee.ImageCollection(COLLECTION_ID)

    if year is not None:
        start = f"{year}-01-01"
        end   = f"{year}-12-31"
        col   = col.filterDate(start, end)

    if aoi is not None:
        col = col.filterBounds(aoi)

    return col


# ---------------------------------------------------------------------------
# 3. Inspect the collection
# ---------------------------------------------------------------------------

def inspect_collection(col: ee.ImageCollection):
    size = col.size().getInfo()
    print(f"Image count : {size}")

    if size == 0:
        print("Collection is empty — check your date/AOI filters.")
        return

    first = col.first()
    props = first.propertyNames().getInfo()
    print(f"Properties  : {props}")

    band_names = first.bandNames().getInfo()
    print(f"Bands       : {band_names[:8]} … ({len(band_names)} total)")

    date = first.date().format("YYYY-MM-dd").getInfo()
    print(f"First image date: {date}")


# ---------------------------------------------------------------------------
# 4. Extract embeddings over a region  (for downstream ML / analysis)
# ---------------------------------------------------------------------------

def sample_embeddings(
    image: ee.Image,
    region: ee.Geometry,
    scale: int = 10,
    num_pixels: int = 500,
) -> np.ndarray:
    """
    Sample embedding vectors from a single image over a region.
    Returns an (N, 64) float32 numpy array, or None if sampling fails.
    """
    sample = image.select(EMBEDDING_BANDS).sample(
        region=region,
        scale=scale,
        numPixels=num_pixels,
        seed=42,
        geometries=False,
    )

    features = sample.getInfo().get("features", [])
    if not features:
        print("No pixels sampled — region may be outside image coverage.")
        return None

    vectors = [list(f["properties"].values()) for f in features]
    return np.array(vectors, dtype=np.float32)


def mean_embedding(image: ee.Image, region: ee.Geometry, scale: int = 10) -> np.ndarray:
    """
    Reduce an image to the mean embedding vector over a region.
    Returns a (64,) float32 numpy array.
    """
    means = image.select(EMBEDDING_BANDS).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
    ).getInfo()

    return np.array([means[b] for b in EMBEDDING_BANDS], dtype=np.float32)


# ---------------------------------------------------------------------------
# 5. Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Initialize ---
    # Set authenticate=True the very first time you run this.
    init_ee(project="ee-rmccormick314-gfsad", authenticate=True)

    # --- Define an area of interest (lon/lat bounding box) ---
    aoi = ee.Geometry.BBox(-100.5, 39.5, -99.5, 40.5)  # central Kansas example

    # --- Load annual embeddings for 2022 ---
    col = load_collection(year=2022, aoi=aoi)
    inspect_collection(col)

    # --- Work with the first (or only) image in the collection ---
    image = col.mosaic()  # merge overlapping tiles into one image

    # Sample N random pixels and get their 64-dim vectors
    embeddings = sample_embeddings(image, aoi, scale=10, num_pixels=200)
    if embeddings is not None:
        print(f"\nSampled embeddings shape : {embeddings.shape}")   # (N, 64)
        print(f"Mean of first vector     : {embeddings[0].mean():.4f}")

    # Or get a single mean embedding for the whole AOI
    mean_vec = mean_embedding(image, aoi)
    print(f"Mean embedding shape     : {mean_vec.shape}")            # (64,)
    print(f"Mean embedding (first 8) : {mean_vec[:8]}")
