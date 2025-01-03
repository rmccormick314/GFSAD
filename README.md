# GFSAD
Crop type and crop intensity mapping using HLSL30 and CDL data for the GFSAD30 project.

---

## Crop Intensity
This module focuses on analyzing crop growth cycles to determine the number of harvestable crop cycles within a year. Using temporal and spatial data from HLSL30 and CDL, this process identifies crop intensity patterns and assists in agricultural resource management.

## Crop Type
This module maps different crop types within a region using classification techniques applied to HLSL30 and CDL datasets. It enables detailed agricultural analysis and supports crop monitoring efforts.

## Preprocessing
The preprocessing step includes: 
- Cleaning and aligning HLSL30 and CDL datasets.
- Resampling and reprojection to ensure consistency across datasets.
- Normalizing data to prepare it for analysis.

## Utilities
This section provides additional tools and scripts to support:
- Data visualization.
- Statistical analysis.
- Model evaluation and validation.

---

### Setup Instructions
1. Clone this repository:
   ```bash
   git clone https://github.com/rmccormick314/gfsad.git
   cd gfsad
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage
Run the main script with the required parameters:
```bash
python main.py --input /path/to/data --output /path/to/output
```

### Data Sources
- **HLSL30**: Harmonized Landsat and Sentinel-2 data at 30-meter resolution.
- **CDL**: Cropland Data Layer providing annual crop-specific land cover.

### Contributing
Contributions are welcome! Please create a pull request or open an issue if you have suggestions or improvements.

### License
This project is licensed under the [MIT License](LICENSE).
