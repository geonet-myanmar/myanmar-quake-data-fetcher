# GeoNet - Myanmar Earthquake Data Fetcher

A Python application that fetches earthquake data from the USGS (United States Geological Survey) API and filters it to show only earthquakes occurring within Myanmar's administrative boundaries.

## Overview

This project retrieves earthquake data from the USGS FDSN Event Web Service and performs spatial filtering to identify earthquakes that occurred within Myanmar's geographical boundaries. The application uses a two-step approach:
1. **Bounding box query**: Fetches all earthquakes within a rectangular area encompassing Myanmar
2. **Precise polygon filtering**: Filters results to include only earthquakes within Myanmar's exact borders

## Features

- **Automated Data Fetching**: Retrieves earthquake data from USGS API with pagination support
- **Spatial Filtering**: Uses ray-casting algorithm to accurately determine if earthquakes occurred within Myanmar
- **GeoJSON Support**: Reads boundary data and outputs results in GeoJSON format
- **Batch Processing**: Handles large datasets by fetching data in batches (up to 20,000 events per request)
- **Polygon & MultiPolygon Support**: Handles complex geometries including holes in polygons
- **Automatic File Naming**: Generates output files with timestamp-based names

## Project Structure

```
GeoNet/
├── usgs_quakes_mm.py    # Main Python script
├── admin0.json          # Myanmar administrative boundary (GeoJSON)
└── README.md           # Project documentation
```

## Requirements

### System Requirements
- Python 3.7 or higher
- Internet connection (for API access)

### Python Dependencies
The application uses only Python standard library modules:
- `json` - JSON parsing and generation
- `urllib.parse` - URL encoding
- `urllib.request` - HTTP requests
- `pathlib` - File path handling
- `datetime` - Date and time operations

No external packages are required!

## Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/geonet-myanmar/myanmar-quake-data-fetcher.git
   cd myanmar-quake-data-fetcher
   ```

2. **Verify admin0.json exists**
   Ensure the `admin0.json` file (Myanmar boundary data) is present in the project directory.

3. **No additional installation needed**
   The script uses only Python standard library.

## Usage

### Basic Usage

Run the script from the command line:

```bash
python usgs_quakes_mm.py
```

### Expected Output

The script will:
1. Load Myanmar's administrative boundaries from `admin0.json`
2. Calculate the bounding box coordinates
3. Fetch earthquake data from USGS API
4. Filter earthquakes to Myanmar's exact boundaries
5. Save results to a GeoJSON file

**Console output example:**
```
Fetching events from 2025-03-28 to 2026-02-09T12:30:45...
Fetched 20000 events (Total so far: 20000)
Fetched 15234 events (Total so far: 35234)
Fetched 8456 events (Total so far: 43690)
Done! Wrote 1234 filtered events to usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson
```

### Output Files

The script generates a GeoJSON file with the naming pattern:
```
usgs_earthquakes_admin0_<start-date>_to_<end-date>.geojson
```

Example: `usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson`

## Configuration

### Modifying Date Range

To change the earthquake data date range, edit line 70 in `usgs_quakes_mm.py`:

```python
start_date = '2025-03-28'  # Change to your desired start date (YYYY-MM-DD)
```

The end date is automatically set to the current time.

### Adjusting Batch Size

To modify the number of events fetched per request (default: 20,000), edit line 74:

```python
limit = 20000  # Maximum events per API request
```

Note: USGS API has a maximum limit per request.

### Changing Admin Boundary

To use a different geographical boundary:
1. Replace `admin0.json` with your GeoJSON file
2. Update line 42 if using a different filename:
   ```python
   admin_path = pathlib.Path('your_boundary_file.json')
   ```

## How It Works

### 1. Boundary Loading
- Reads `admin0.json` containing Myanmar's MultiPolygon geometry
- Extracts all polygon coordinates from GeoJSON features
- Supports both Polygon and MultiPolygon geometry types

### 2. Bounding Box Calculation
- Calculates the minimum and maximum longitude/latitude from all boundary points
- Creates a rectangular bounding box that encompasses Myanmar
- Uses this bbox for initial API query (faster than point-in-polygon for millions of points)

### 3. USGS API Data Fetching
Queries the USGS FDSN Event Web Service with parameters:
- **format**: geojson
- **starttime**: Configurable start date
- **endtime**: Current UTC time
- **minlongitude/maxlongitude**: Bounding box west/east limits
- **minlatitude/maxlatitude**: Bounding box south/north limits
- **orderby**: time-asc (chronological order)
- **limit**: 20,000 events per request
- **offset**: Pagination offset

### 4. Spatial Filtering Algorithm

#### Ray-Casting Algorithm (`point_in_ring`)
Determines if a point is inside a polygon ring by:
- Casting a ray from the point to infinity
- Counting how many times the ray crosses polygon edges
- If odd number of crossings → point is inside
- If even number of crossings → point is outside

#### Polygon with Holes (`point_in_polygon`)
Checks if a point is:
- Inside the exterior ring (outer boundary)
- NOT inside any interior rings (holes)

#### MultiPolygon Support (`point_in_multipolygon`)
Myanmar's boundary is a MultiPolygon (mainland + islands), so the function checks if the earthquake point is within ANY of the constituent polygons.

### 5. Output Generation
Creates a GeoJSON FeatureCollection containing:
- **metadata**:
  - generated: Unix timestamp
  - title: Descriptive title
  - count: Number of filtered events
  - bboxCount: Total events in bounding box
  - starttime/endtime: Query date range
  - source: Data source attribution
- **features**: Array of filtered earthquake events

## Output Data Structure

The output GeoJSON file contains:

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generated": 1707480645000,
    "title": "USGS Earthquakes within admin0 polygon",
    "count": 1234,
    "bboxCount": 5678,
    "starttime": "2025-03-28",
    "endtime": "2026-02-09T12:30:45",
    "source": "USGS FDSN Event API"
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "mag": 4.5,
        "place": "12 km E of Myeik, Myanmar",
        "time": 1680000000000,
        ...
      },
      "geometry": {
        "type": "Point",
        "coordinates": [98.6, 12.4, 10.0]
      },
      "id": "us6000..."
    },
    ...
  ]
}
```

### Feature Properties (from USGS)
Each earthquake feature includes (among others):
- **mag**: Magnitude
- **place**: Location description
- **time**: Occurrence time (Unix timestamp)
- **updated**: Last update time
- **tz**: Timezone offset
- **url**: USGS event page URL
- **detail**: Detailed information URL
- **felt**: Number of "felt" reports
- **cdi**: Community Decimal Intensity
- **mmi**: Modified Mercalli Intensity
- **alert**: Alert level (green, yellow, orange, red)
- **status**: Review status
- **tsunami**: Tsunami warning flag
- **sig**: Significance value
- **net**: Network code
- **code**: Event code
- **ids**: Associated IDs
- **sources**: Contributing networks
- **types**: Available product types
- **nst**: Number of stations
- **dmin**: Minimum distance to stations
- **rms**: Root mean square travel time residual
- **gap**: Azimuthal gap
- **magType**: Magnitude type
- **type**: Event type (earthquake, quarry blast, etc.)
- **title**: Event title

### Geometry
- **type**: "Point"
- **coordinates**: [longitude, latitude, depth_in_km]

## API Reference

### USGS FDSN Event Web Service

**Endpoint**: `https://earthquake.usgs.gov/fdsnws/event/1/query`

**Documentation**: https://earthquake.usgs.gov/fdsnws/event/1/

**Rate Limits**:
- The USGS API is free and open
- Be respectful with request frequency
- Large queries may take time to process

**Data Updates**:
- Recent earthquakes are updated frequently
- Historical data is generally stable

## admin0.json File

The `admin0.json` file contains:
- **Type**: GeoJSON FeatureCollection
- **Source**: Myanmar Information Management Unit (MIMU)
- **Geometry Type**: MultiPolygon
- **Coverage**: Myanmar (Burma) administrative boundary at admin level 0
- **Coordinate System**: WGS84 (EPSG:4326)
- **Features**: 1 feature representing Myanmar's complete boundary
- **File Size**: ~2.7 MB (high-resolution boundary data)

## Troubleshooting

### File Not Found Error
```
FileNotFoundError: admin0.json not found in current directory.
```
**Solution**: Ensure `admin0.json` is in the same directory as the script.

### No Polygon Geometry Found
```
SystemExit: No polygon geometry found in admin0.json
```
**Solution**: Verify `admin0.json` contains valid GeoJSON with Polygon or MultiPolygon geometry.

### API Timeout
```
urllib.error.URLError: <urlopen error timed out>
```
**Solution**:
- Check your internet connection
- The timeout is set to 120 seconds (line 96)
- Increase timeout if needed: `urllib.request.urlopen(url, timeout=300)`

### Empty Results
If the output shows 0 filtered events:
- Check the date range (start_date)
- Verify there were earthquakes in Myanmar during that period
- Check bboxCount in metadata - if this is 0, the API query returned no results

## Advanced Usage

### Filtering by Magnitude

To filter earthquakes by magnitude, add this parameter to the API query (line 81-92):

```python
params = {
    'format': 'geojson',
    'starttime': start_date,
    'endtime': end_time,
    'minmagnitude': '4.0',  # Add this line
    # ... other parameters
}
```

### Including Event Details

To get more detailed information for each earthquake, you can fetch additional data using the `detail` URL from each feature's properties.

### Exporting to Other Formats

The GeoJSON output can be:
- Imported into QGIS, ArcGIS, or other GIS software
- Converted to CSV using tools like `ogr2ogr`
- Visualized on web maps using Leaflet, Mapbox, etc.
- Analyzed using GeoPandas in Python

Example with GeoPandas:
```python
import geopandas as gpd
gdf = gpd.read_file('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson')
print(gdf.head())
```

## Performance Considerations

- **Bounding box query**: Fast, filters at API level
- **Polygon filtering**: O(n×m) where n = events, m = polygon vertices
- **Large datasets**: 50,000+ events may take a few minutes to process
- **Memory usage**: Minimal, processes features one at a time

## Data Sources and Attribution

- **Earthquake Data**: USGS (United States Geological Survey)
  - URL: https://earthquake.usgs.gov/
  - License: Public domain

- **Boundary Data**: Myanmar Information Management Unit (MIMU)
  - Data ID: mmr_polbnda_adm0_250k_mimu_1
  - Format: GeoJSON

## License

This script is provided as-is for educational and research purposes.

**Data Licenses:**
- USGS earthquake data is in the public domain
- Check the admin0.json data license with MIMU

## Contributing

Contributions are welcome! Areas for improvement:
- Add command-line arguments for date range and output path
- Support for different countries/regions
- Add magnitude filtering options
- Include data visualization
- Export to multiple formats (CSV, KML, Shapefile)

## Future Enhancements

Potential features to add:
- [ ] Command-line interface (CLI) with argparse
- [ ] Magnitude filtering
- [ ] Depth filtering
- [ ] Email notifications for new significant earthquakes
- [ ] Automated scheduling (daily/weekly runs)
- [ ] Data visualization (matplotlib/folium maps)
- [ ] Database storage (SQLite/PostgreSQL)
- [ ] Web interface
- [ ] Real-time monitoring mode

## Contact and Support

For questions or issues:
- Check USGS API documentation: https://earthquake.usgs.gov/fdsnws/event/1/
- Review GeoJSON specification: https://geojson.org/
- File issues in the project repository

## Version History

- **v1.0** - Initial release
  - Basic earthquake data fetching
  - Spatial filtering for Myanmar
  - GeoJSON output

---

**Last Updated**: February 2026
