"""One-off script to re-export the CDL tile that failed."""
import ee, time
from satellite_embeddings import init_ee
from export_patches import CDL_COLLECTION

init_ee(project="ee-rmccormick314-gfsad", authenticate=False)

aoi  = ee.Geometry.BBox(-119.65, 36.30, -119.55, 36.40)
year = 2022

cdl_raw = (ee.ImageCollection(CDL_COLLECTION)
             .filterDate(f"{year}-01-01", f"{year}-12-31")
             .first()
             .select("cropland"))

# multiply(1) returns a new computed image with no source properties,
# which avoids the malformed class_names string that blocks export.
cdl = cdl_raw.multiply(1).rename("cropland").toInt16()

task = ee.batch.Export.image.toDrive(
    image=cdl,
    description="ca_kings_cdl_2022",
    folder="GFSAD_exports",
    fileNamePrefix="ca_kings_cdl_2022",
    region=aoi,
    scale=30,
    maxPixels=1e13,
    fileFormat="GeoTIFF",
)
task.start()
print(f"Started CDL export  task={task.id}")

terminal = {"COMPLETED", "FAILED", "CANCELLED"}
while True:
    s = task.status()
    print(s["state"], end="\r")
    if s["state"] in terminal:
        print()
        tag = "[OK]" if s["state"] == "COMPLETED" else "[FAIL]"
        print(f"{tag} {s['description']}: {s['state']}")
        if s["state"] == "FAILED":
            print("Error:", s.get("error_message", "unknown"))
        break
    time.sleep(20)
