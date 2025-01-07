# Global Food-and-Water Security-support Analysis Data (GFSAD)
The [GFSADO30 Project](https://www.usgs.gov/centers/western-geographic-science-center/science/global-food-and-water-security-support-analysis) is a NASA funded project (2023-2028) to provide highest-resolution global cropland data and their water use that contributes towards global food-and-water security in the twenty-first century. The GFSAD products are derived through multi-sensor remote sensing data (e.g., Landsat-series, Sentinel-series, MODIS, AVHRR), secondary data, and field-plot data and aims at documenting cropland dynamics from 2000 to 2030.

---

### Crop Intensity
This module focuses on analyzing crop growth cycles to determine the number of harvestable crop cycles within a year. Using temporal and spatial data from HLSL30 and CDL, this process identifies crop intensity patterns.

### Crop Type
This module maps different crop types within a region using neural network classification techniques applied to HLSL30 and CDL datasets.

### Preprocessing (WIP)
Preprocessing steps for generating training and validation data.

### Utilities (WIP)
This section provides additional tools and scripts.
- **ASD File Parser**: Parses data dumps from handleheld ASD Spectroradiometer.
- **AppEEARS (WIP)**: Uses the NASA AppEEARS interface to pull data from LPDAAC.

---

### Data Sources
- **HLSL30**: Harmonized Landsat and Sentinel-2 data at 30-meter resolution.
- **CDL**: Cropland Data Layer providing annual crop-specific land cover.

---

### Contributing
Contributions are welcome! Please create a pull request or open an issue if you have suggestions or improvements.

### License
This project is licensed under the [MIT License](LICENSE).
