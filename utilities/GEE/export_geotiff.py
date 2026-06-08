"""
Batch-export satellite embeddings + CDL labels for an AOI to Google Drive as GeoTIFFs.
This replaces the slow per-patch sampleRectangle approach and enables 1,000–50,000 patches.

Workflow:
    1. Run this script  →  two GEE export tasks start (takes 10–30 min server-side)
    2. Download both .tif files from your Drive folder (GFSAD_exports/)
    3. Run patches_from_geotiff.py to extract patches locally

Usage:
    python export_geotiff.py
"""

import sys
import importlib.util
import subprocess
import time

_REQUIRED = {"ee": "earthengine-api"}
def _ensure_deps():
    missing = [pip for mod, pip in _REQUIRED.items() if importlib.util.find_spec(mod) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
_ensure_deps()

import ee
from satellite_embeddings import init_ee, load_collection, EMBEDDING_BANDS
from export_patches import CDL_COLLECTION

DRIVE_FOLDER  = "GFSAD_exports"
SCALE_EMBED   = 10   # embedding native resolution
SCALE_CDL     = 30   # CDL native resolution — rasterio resamples to match on load


def start_exports(
    aoi:    ee.Geometry,
    year:   int,
    prefix: str = "export",
) -> list[ee.batch.Task]:
    embed_image = (load_collection(year=year)
                   .filterBounds(aoi)
                   .mosaic()
                   .select(EMBEDDING_BANDS))

    # multiply(1) strips the malformed class_names string property that blocks CDL exports
    cdl_image = (ee.ImageCollection(CDL_COLLECTION)
                 .filterDate(f"{year}-01-01", f"{year}-12-31")
                 .first()
                 .select("cropland")
                 .multiply(1)
                 .rename("cropland")
                 .toInt16())

    tasks = []

    for image, name, scale in [(embed_image, "embeddings", SCALE_EMBED),
                               (cdl_image,   "cdl",        SCALE_CDL)]:
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=f"{prefix}_{name}_{year}",
            folder=DRIVE_FOLDER,
            fileNamePrefix=f"{prefix}_{name}_{year}",
            region=aoi,
            scale=scale,
            maxPixels=1e13,
            fileFormat="GeoTIFF",
        )
        task.start()
        print(f"Started : {prefix}_{name}_{year}  (task {task.id})")
        tasks.append(task)

    return tasks


def poll_tasks(tasks: list[ee.batch.Task], interval_s: int = 30):
    print(f"\nPolling every {interval_s}s — Ctrl+C to stop polling (tasks keep running).")
    terminal = {"COMPLETED", "FAILED", "CANCELLED"}

    while True:
        statuses = [t.status() for t in tasks]
        states   = [s["state"] for s in statuses]
        summary = " | ".join(s["description"] + ": " + s["state"] for s in statuses)
        print(f"  {summary}", end="\r")

        if all(s in terminal for s in states):
            print()
            break
        time.sleep(interval_s)

    for s in [t.status() for t in tasks]:
        icon = "OK" if s["state"] == "COMPLETED" else "FAIL"
        print(f"  [{icon}] {s['description']}: {s['state']}")
        if s["state"] == "FAILED":
            print(f"    Error: {s.get('error_message', 'unknown')}")


if __name__ == "__main__":
    init_ee(project="ee-rmccormick314-gfsad", authenticate=False)

    # Kings County, CA — ~9 km × 11 km dense farmland (almonds, cotton, forage)
    # Keeps embedding GeoTIFF ~250 MB — good for a test run
    aoi = ee.Geometry.BBox(-119.65, 36.30, -119.55, 36.40)

    tasks = start_exports(aoi=aoi, year=2022, prefix="ca_kings")
    poll_tasks(tasks)

    print(f"\nNext steps:")
    print(f"  1. Open Google Drive → {DRIVE_FOLDER}/")
    print(f"  2. Download ca_sjv_embeddings_2022.tif and ca_sjv_cdl_2022.tif")
    print(f"  3. Place both files in data/geotiff/")
    print(f"  4. Run: python patches_from_geotiff.py")
