# GeoNet Usage Guide

This guide provides detailed instructions on how to use the Myanmar Earthquake Data Fetcher.

## Quick Start

### Step 1: Verify Files
Ensure you have both required files in the project directory:
```
GeoNet/
├── usgs_quakes_mm.py
└── admin0.json
```

### Step 2: Run the Script
```bash
python usgs_quakes_mm.py
```

### Step 3: Wait for Completion
The script will display progress as it fetches data:
```
Fetching events from 2025-03-28 to 2026-02-09T12:30:45...
Fetched 20000 events (Total so far: 20000)
Fetched 8456 events (Total so far: 28456)
Done! Wrote 1234 filtered events to usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson
```

### Step 4: View Results
The output GeoJSON file can be opened with:
- GIS software (QGIS, ArcGIS)
- Web mapping libraries (Leaflet, Mapbox)
- Text editors (for JSON inspection)
- Python (GeoPandas, Pandas)

## Customization Options

### Change Date Range

**Modify the start date:**
Edit line 70 in `usgs_quakes_mm.py`:
```python
start_date = '2024-01-01'  # Fetch earthquakes from Jan 1, 2024
```

**Modify the end date:**
Edit line 71 in `usgs_quakes_mm.py`:
```python
# Instead of datetime.now(), use a specific date:
end_time = '2024-12-31T23:59:59'
```

### Filter by Magnitude

Add a minimum magnitude filter by modifying the params dictionary (line 81-92):

```python
params = {
    'format': 'geojson',
    'starttime': start_date,
    'endtime': end_time,
    'minmagnitude': '3.0',      # Only earthquakes >= 3.0 magnitude
    'minlongitude': f'{min_lon:.6f}',
    'maxlongitude': f'{max_lon:.6f}',
    'minlatitude': f'{min_lat:.6f}',
    'maxlatitude': f'{max_lat:.6f}',
    'orderby': 'time-asc',
    'limit': str(limit),
    'offset': str(offset)
}
```

Available magnitude filters:
- `minmagnitude`: Minimum magnitude (e.g., '2.5', '4.0', '5.5')
- `maxmagnitude`: Maximum magnitude (e.g., '6.0')

### Filter by Depth

Add depth filters:

```python
params = {
    # ... other parameters
    'mindepth': '10',     # Minimum depth in km
    'maxdepth': '100',    # Maximum depth in km
}
```

### Change Output Filename

Modify lines 131-132 to customize the output filename:

```python
date_str = datetime.now(timezone.utc).date().isoformat()
out_name = f'myanmar_earthquakes_{start_date}_{date_str}.geojson'
```

### Use Different Boundary File

To analyze earthquakes for a different region:

1. Obtain a GeoJSON file with the region's boundary
2. Replace `admin0.json` or update the filename in line 42:
   ```python
   admin_path = pathlib.Path('thailand_boundary.json')
   ```

## Understanding the Output

### Metadata Section
```json
"metadata": {
    "generated": 1707480645000,      // Unix timestamp (milliseconds)
    "title": "USGS Earthquakes within admin0 polygon",
    "count": 1234,                    // Earthquakes within Myanmar
    "bboxCount": 5678,                // Total earthquakes in bounding box
    "starttime": "2025-03-28",
    "endtime": "2026-02-09T12:30:45",
    "source": "USGS FDSN Event API"
}
```

**Key Metrics:**
- `count < bboxCount`: Shows how many earthquakes were filtered out (outside Myanmar's exact borders)
- High difference suggests many border-region earthquakes
- If `count == bboxCount`, most earthquakes were within Myanmar

### Feature Properties

Each earthquake feature contains:

#### Location Information
- `place`: Human-readable location (e.g., "12 km E of Myeik, Myanmar")
- `coordinates`: [longitude, latitude, depth_in_km]

#### Magnitude & Intensity
- `mag`: Magnitude value (e.g., 4.5)
- `magType`: Magnitude type (mb, ml, mw, etc.)
- `sig`: Significance score (0-1000+)
- `cdi`: Community Decimal Intensity (felt intensity)
- `mmi`: Modified Mercalli Intensity

#### Time Information
- `time`: Earthquake occurrence time (Unix timestamp in milliseconds)
- `updated`: Last update time (Unix timestamp in milliseconds)

#### Status & Alerts
- `status`: Review status ("automatic", "reviewed", "deleted")
- `alert`: Alert level (null, "green", "yellow", "orange", "red")
- `tsunami`: Tsunami warning flag (0 or 1)

#### Source Information
- `net`: Contributing network (e.g., "us", "ci", "nc")
- `code`: Event code
- `sources`: All contributing networks
- `types`: Available product types (origin, phase-data, etc.)

## Working with the Output Data

### View in QGIS

1. Open QGIS
2. Layer → Add Layer → Add Vector Layer
3. Select the generated .geojson file
4. The earthquakes will appear as points on the map

### Convert to CSV

Using `ogr2ogr` (part of GDAL):
```bash
ogr2ogr -f CSV earthquakes.csv usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson -lco GEOMETRY=AS_XY
```

### Analyze with Python

```python
import json
import pandas as pd

# Load the GeoJSON file
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Extract features into a list
events = []
for feature in data['features']:
    props = feature['properties']
    coords = feature['geometry']['coordinates']

    events.append({
        'magnitude': props.get('mag'),
        'place': props.get('place'),
        'time': pd.to_datetime(props.get('time'), unit='ms'),
        'longitude': coords[0],
        'latitude': coords[1],
        'depth_km': coords[2],
        'alert': props.get('alert'),
        'tsunami': props.get('tsunami')
    })

# Create DataFrame
df = pd.DataFrame(events)

# Analysis examples
print(f"Total earthquakes: {len(df)}")
print(f"Average magnitude: {df['magnitude'].mean():.2f}")
print(f"Strongest earthquake: {df['magnitude'].max()}")
print(f"\nMagnitude distribution:")
print(df['magnitude'].describe())

# Filter significant earthquakes
significant = df[df['magnitude'] >= 5.0]
print(f"\nEarthquakes >= 5.0: {len(significant)}")
```

### Create a Simple Map with Folium

```python
import folium
import json

# Load data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Create map centered on Myanmar
m = folium.Map(location=[21.9, 96.0], zoom_start=6)

# Add earthquake markers
for feature in data['features']:
    coords = feature['geometry']['coordinates']
    props = feature['properties']

    # Color code by magnitude
    mag = props.get('mag', 0)
    if mag < 3:
        color = 'green'
    elif mag < 5:
        color = 'orange'
    else:
        color = 'red'

    # Create popup text
    popup_text = f"""
    <b>Magnitude:</b> {mag}<br>
    <b>Location:</b> {props.get('place')}<br>
    <b>Depth:</b> {coords[2]:.1f} km<br>
    <b>Time:</b> {props.get('time')}
    """

    folium.CircleMarker(
        location=[coords[1], coords[0]],
        radius=mag * 2,
        popup=folium.Popup(popup_text, max_width=300),
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.6
    ).add_to(m)

# Save map
m.save('myanmar_earthquakes_map.html')
print("Map saved to myanmar_earthquakes_map.html")
```

## Common Use Cases

### 1. Monthly Earthquake Summary

Set date range to one month:
```python
start_date = '2025-01-01'
end_time = '2025-01-31T23:59:59'
```

### 2. Significant Earthquakes Only

Add magnitude filter:
```python
'minmagnitude': '5.0'
```

### 3. Recent Earthquakes (Last 7 Days)

```python
from datetime import datetime, timedelta, timezone

start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
```

### 4. Historical Data Analysis

For long time periods, the script may take several minutes:
```python
start_date = '2020-01-01'
# End date defaults to now
```

### 5. Deep Earthquakes Only

```python
params = {
    # ... other parameters
    'mindepth': '70',  # Only earthquakes deeper than 70 km
}
```

## Performance Tips

### Reduce API Calls
- Use specific date ranges instead of fetching all historical data
- Add magnitude filters to reduce result size
- Consider caching results locally

### Speed Up Processing
The spatial filtering is the slowest part. For better performance:
- Use a simpler boundary file (fewer vertices)
- Pre-filter by magnitude before spatial filtering
- Process results in parallel (requires code modification)

### Handle Large Datasets
For very large result sets (100,000+ events):
- Process in smaller date chunks
- Save intermediate results
- Consider using a database instead of in-memory lists

## Troubleshooting

### No Results Returned

Check these factors:
1. **Date range**: Are there earthquakes in Myanmar during this period?
2. **Magnitude**: Did you add a magnitude filter that's too restrictive?
3. **API status**: Is the USGS API operational? (Check: https://earthquake.usgs.gov/)

### Script Hangs or Times Out

Possible causes:
1. **Large dataset**: Fetching years of data may take time
2. **Network issues**: Check internet connection
3. **API overload**: USGS API may be slow during peak times

Solutions:
- Increase timeout (line 96): `timeout=300`
- Reduce date range
- Add magnitude filter

### Memory Issues

If processing millions of events:
- Add magnitude filter to reduce data volume
- Process in smaller date chunks
- Use streaming approach (modify code to write features incrementally)

## Advanced Modifications

### Add Progress Bar

Install `tqdm` and modify the spatial filtering loop:

```python
from tqdm import tqdm

# Replace line 110-114 with:
filtered = []
for f in tqdm(all_features, desc="Filtering earthquakes"):
    coords = (f.get('geometry') or {}).get('coordinates') or []
    if len(coords) >= 2:
        if point_in_multipolygon(coords[0], coords[1], polygons):
            filtered.append(f)
```

### Save to SQLite Database

```python
import sqlite3

# After fetching data, save to database:
conn = sqlite3.connect('earthquakes.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS earthquakes (
        id TEXT PRIMARY KEY,
        magnitude REAL,
        place TEXT,
        time INTEGER,
        longitude REAL,
        latitude REAL,
        depth REAL
    )
''')

for f in filtered:
    props = f['properties']
    coords = f['geometry']['coordinates']
    cursor.execute('''
        INSERT OR REPLACE INTO earthquakes VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        f['id'],
        props.get('mag'),
        props.get('place'),
        props.get('time'),
        coords[0],
        coords[1],
        coords[2]
    ))

conn.commit()
conn.close()
```

### Email Notifications

Add email notifications for significant earthquakes:

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(filtered):
    significant = [f for f in filtered if f['properties'].get('mag', 0) >= 5.5]

    if significant:
        msg = MIMEText(f"Found {len(significant)} significant earthquakes (M >= 5.5)")
        msg['Subject'] = 'Myanmar Earthquake Alert'
        msg['From'] = 'alerts@example.com'
        msg['To'] = 'your-email@example.com'

        # Configure SMTP settings
        # ... (add your SMTP configuration)
```

## Resources

### USGS API Documentation
- Main page: https://earthquake.usgs.gov/fdsnws/event/1/
- Query builder: https://earthquake.usgs.gov/earthquakes/search/
- Data formats: https://earthquake.usgs.gov/data/formats/

### GeoJSON Resources
- Specification: https://geojson.org/
- Validator: https://geojsonlint.com/
- Tools: https://github.com/tmcw/awesome-geojson

### Myanmar Geographic Data
- MIMU (Myanmar Information Management Unit): http://themimu.info/
- OpenStreetMap Myanmar: https://www.openstreetmap.org/relation/50371

### Python Geospatial Libraries
- GeoPandas: https://geopandas.org/
- Shapely: https://shapely.readthedocs.io/
- Folium: https://python-visualization.github.io/folium/

---

**Need Help?**
- Review the main README.md for project overview
- Check the API documentation for query parameters
- Test with small date ranges first
