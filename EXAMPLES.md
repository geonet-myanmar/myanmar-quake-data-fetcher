# Code Examples

This document provides practical code examples for working with the GeoNet earthquake data fetcher and analyzing the results.

## Table of Contents
1. [Basic Usage Examples](#basic-usage-examples)
2. [Data Analysis Examples](#data-analysis-examples)
3. [Visualization Examples](#visualization-examples)
4. [Integration Examples](#integration-examples)
5. [Advanced Modifications](#advanced-modifications)

---

## Basic Usage Examples

### Example 1: Fetch Last 30 Days of Earthquakes

Modify `usgs_quakes_mm.py`:

```python
from datetime import datetime, timedelta, timezone

def main():
    # ... (keep existing code until line 70)

    # Fetch last 30 days
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=30)

    start_date = start_time.strftime('%Y-%m-%d')
    end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%S')

    # ... (continue with rest of the code)
```

### Example 2: Fetch Only Significant Earthquakes (M >= 5.0)

Add magnitude filter to API parameters:

```python
params = {
    'format': 'geojson',
    'starttime': start_date,
    'endtime': end_time,
    'minmagnitude': '5.0',  # Add this line
    'minlongitude': f'{min_lon:.6f}',
    'maxlongitude': f'{max_lon:.6f}',
    'minlatitude': f'{min_lat:.6f}',
    'maxlatitude': f'{max_lat:.6f}',
    'orderby': 'time-asc',
    'limit': str(limit),
    'offset': str(offset)
}
```

### Example 3: Command-Line Interface

Create `usgs_quakes_cli.py`:

```python
import argparse
import json
import urllib.parse
import urllib.request
import pathlib
from datetime import datetime, timezone

# ... (include all the point_in_ring, point_in_polygon functions)

def main():
    parser = argparse.ArgumentParser(
        description='Fetch USGS earthquake data for Myanmar'
    )
    parser.add_argument(
        '--start-date',
        required=True,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        default=None,
        help='End date (YYYY-MM-DD), defaults to now'
    )
    parser.add_argument(
        '--min-magnitude',
        type=float,
        default=None,
        help='Minimum magnitude filter'
    )
    parser.add_argument(
        '--boundary-file',
        default='admin0.json',
        help='GeoJSON boundary file'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output filename'
    )

    args = parser.parse_args()

    # Load boundary
    admin_path = pathlib.Path(args.boundary_file)
    if not admin_path.exists():
        raise FileNotFoundError(f"{args.boundary_file} not found")

    data = json.loads(admin_path.read_text(encoding='utf-8'))
    polygons = []

    for feat in data.get('features', []):
        geom = feat.get('geometry', {})
        gtype = geom.get('type')
        coords = geom.get('coordinates', [])
        if gtype == 'Polygon':
            polygons.append(coords)
        elif gtype == 'MultiPolygon':
            polygons.extend(coords)

    if not polygons:
        raise SystemExit('No polygon geometry found')

    # Calculate bounding box
    all_pts = [pt for poly in polygons for ring in poly for pt in ring]
    min_lon = min(pt[0] for pt in all_pts)
    max_lon = max(pt[0] for pt in all_pts)
    min_lat = min(pt[1] for pt in all_pts)
    max_lat = max(pt[1] for pt in all_pts)

    # Prepare API parameters
    end_time = args.end_date if args.end_date else \
               datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

    base_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
    limit = 20000
    offset = 1
    all_features = []

    print(f"Fetching events from {args.start_date} to {end_time}...")

    while True:
        params = {
            'format': 'geojson',
            'starttime': args.start_date,
            'endtime': end_time,
            'minlongitude': f'{min_lon:.6f}',
            'maxlongitude': f'{max_lon:.6f}',
            'minlatitude': f'{min_lat:.6f}',
            'maxlatitude': f'{max_lat:.6f}',
            'orderby': 'time-asc',
            'limit': str(limit),
            'offset': str(offset)
        }

        if args.min_magnitude:
            params['minmagnitude'] = str(args.min_magnitude)

        url = f"{base_url}?{urllib.parse.urlencode(params)}"

        with urllib.request.urlopen(url, timeout=120) as resp:
            batch_data = json.load(resp)

        batch = batch_data.get('features', [])
        all_features.extend(batch)

        print(f'Fetched {len(batch)} events (Total: {len(all_features)})')

        if len(batch) < limit:
            break
        offset += limit

    # Spatial filtering
    filtered = []
    for f in all_features:
        coords = (f.get('geometry') or {}).get('coordinates') or []
        if len(coords) >= 2:
            if point_in_multipolygon(coords[0], coords[1], polygons):
                filtered.append(f)

    # Output
    out_data = {
        'type': 'FeatureCollection',
        'metadata': {
            'generated': int(datetime.now(timezone.utc).timestamp() * 1000),
            'title': 'USGS Earthquakes within boundary',
            'count': len(filtered),
            'bboxCount': len(all_features),
            'starttime': args.start_date,
            'endtime': end_time,
            'source': 'USGS FDSN Event API'
        },
        'features': filtered
    }

    if args.output:
        out_name = args.output
    else:
        date_str = datetime.now(timezone.utc).date().isoformat()
        out_name = f'usgs_earthquakes_{args.start_date}_to_{date_str}.geojson'

    pathlib.Path(out_name).write_text(
        json.dumps(out_data, separators=(',', ':')),
        encoding='utf-8'
    )
    print(f'Done! Wrote {len(filtered)} filtered events to {out_name}')

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Basic usage
python usgs_quakes_cli.py --start-date 2025-01-01

# With magnitude filter
python usgs_quakes_cli.py --start-date 2025-01-01 --min-magnitude 4.5

# With custom date range
python usgs_quakes_cli.py --start-date 2025-01-01 --end-date 2025-06-30

# With custom output filename
python usgs_quakes_cli.py --start-date 2025-01-01 --output my_earthquakes.geojson
```

---

## Data Analysis Examples

### Example 4: Basic Statistics with Pandas

```python
import json
import pandas as pd
from datetime import datetime

# Load GeoJSON
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Extract features into list
events = []
for feature in data['features']:
    props = feature['properties']
    coords = feature['geometry']['coordinates']

    events.append({
        'id': feature['id'],
        'magnitude': props.get('mag'),
        'place': props.get('place'),
        'time': pd.to_datetime(props.get('time'), unit='ms'),
        'longitude': coords[0],
        'latitude': coords[1],
        'depth_km': coords[2],
        'mag_type': props.get('magType'),
        'alert': props.get('alert'),
        'tsunami': props.get('tsunami'),
        'felt': props.get('felt'),
        'sig': props.get('sig'),
        'status': props.get('status')
    })

# Create DataFrame
df = pd.DataFrame(events)

# Basic statistics
print("="*50)
print("EARTHQUAKE DATA SUMMARY")
print("="*50)
print(f"\nTotal earthquakes: {len(df)}")
print(f"Date range: {df['time'].min()} to {df['time'].max()}")
print(f"\nMagnitude Statistics:")
print(df['magnitude'].describe())

# Magnitude distribution
print(f"\nMagnitude Distribution:")
print(df['magnitude'].value_counts(bins=5, sort=False))

# By month
df['month'] = df['time'].dt.to_period('M')
monthly = df.groupby('month').size()
print(f"\nMonthly Distribution:")
print(monthly)

# Strongest earthquakes
print(f"\nTop 10 Strongest Earthquakes:")
top_10 = df.nlargest(10, 'magnitude')[['time', 'magnitude', 'place', 'depth_km']]
print(top_10.to_string(index=False))

# Shallowest earthquakes
print(f"\nTop 10 Shallowest Earthquakes:")
shallow = df.nsmallest(10, 'depth_km')[['time', 'magnitude', 'place', 'depth_km']]
print(shallow.to_string(index=False))

# Alert levels
if df['alert'].notna().any():
    print(f"\nAlert Level Distribution:")
    print(df['alert'].value_counts())

# Felt reports
if df['felt'].notna().any():
    felt_events = df[df['felt'] > 0]
    print(f"\nFelt Reports:")
    print(f"Events with felt reports: {len(felt_events)}")
    print(f"Total felt reports: {df['felt'].sum()}")
```

### Example 5: Time Series Analysis

```python
import json
import pandas as pd
import matplotlib.pyplot as plt

# Load data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Extract to DataFrame
events = []
for feature in data['features']:
    props = feature['properties']
    coords = feature['geometry']['coordinates']
    events.append({
        'time': pd.to_datetime(props.get('time'), unit='ms'),
        'magnitude': props.get('mag'),
        'depth_km': coords[2]
    })

df = pd.DataFrame(events)
df = df.set_index('time').sort_index()

# Resample by day
daily = df.resample('D').agg({
    'magnitude': ['count', 'mean', 'max'],
    'depth_km': 'mean'
})

# Plot
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Daily count
axes[0].plot(daily.index, daily[('magnitude', 'count')], linewidth=0.8)
axes[0].set_title('Daily Earthquake Count')
axes[0].set_ylabel('Count')
axes[0].grid(True, alpha=0.3)

# Daily mean magnitude
axes[1].plot(daily.index, daily[('magnitude', 'mean')], color='orange', linewidth=0.8)
axes[1].set_title('Daily Mean Magnitude')
axes[1].set_ylabel('Magnitude')
axes[1].grid(True, alpha=0.3)

# Daily max magnitude
axes[2].plot(daily.index, daily[('magnitude', 'max')], color='red', linewidth=0.8)
axes[2].set_title('Daily Maximum Magnitude')
axes[2].set_ylabel('Magnitude')
axes[2].set_xlabel('Date')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('earthquake_time_series.png', dpi=300)
print("Saved earthquake_time_series.png")
```

### Example 6: Depth vs Magnitude Analysis

```python
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

events = []
for feature in data['features']:
    props = feature['properties']
    coords = feature['geometry']['coordinates']
    events.append({
        'magnitude': props.get('mag'),
        'depth_km': coords[2]
    })

df = pd.DataFrame(events)

# Create scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(df['magnitude'], df['depth_km'], alpha=0.5, s=10)
plt.xlabel('Magnitude')
plt.ylabel('Depth (km)')
plt.title('Earthquake Magnitude vs Depth')
plt.grid(True, alpha=0.3)

# Add regression line
z = np.polyfit(df['magnitude'].dropna(), df['depth_km'].dropna(), 1)
p = np.poly1d(z)
plt.plot(df['magnitude'].sort_values(), p(df['magnitude'].sort_values()),
         "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
plt.legend()

plt.tight_layout()
plt.savefig('magnitude_vs_depth.png', dpi=300)
print("Saved magnitude_vs_depth.png")

# Correlation
correlation = df['magnitude'].corr(df['depth_km'])
print(f"\nCorrelation between magnitude and depth: {correlation:.3f}")
```

---

## Visualization Examples

### Example 7: Interactive Map with Folium

```python
import json
import folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd

# Load data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Create base map centered on Myanmar
m = folium.Map(
    location=[21.9, 96.0],
    zoom_start=6,
    tiles='OpenStreetMap'
)

# Add marker cluster
marker_cluster = MarkerCluster().add_to(m)

# Add earthquakes
for feature in data['features']:
    coords = feature['geometry']['coordinates']
    props = feature['properties']

    mag = props.get('mag', 0)
    place = props.get('place', 'Unknown')
    time = pd.to_datetime(props.get('time'), unit='ms')
    depth = coords[2]

    # Color by magnitude
    if mag < 3:
        color = 'green'
    elif mag < 5:
        color = 'orange'
    else:
        color = 'red'

    # Create popup
    popup_html = f"""
    <div style="font-family: Arial; width: 200px;">
        <h4 style="margin: 0;">M {mag}</h4>
        <p style="margin: 5px 0;"><b>Location:</b> {place}</p>
        <p style="margin: 5px 0;"><b>Time:</b> {time}</p>
        <p style="margin: 5px 0;"><b>Depth:</b> {depth:.1f} km</p>
        <p style="margin: 5px 0;"><b>Status:</b> {props.get('status', 'N/A')}</p>
    </div>
    """

    folium.CircleMarker(
        location=[coords[1], coords[0]],
        radius=mag * 2,
        popup=folium.Popup(popup_html, max_width=300),
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.6
    ).add_to(marker_cluster)

# Add layer control
folium.LayerControl().add_to(m)

# Save map
m.save('myanmar_earthquakes_map.html')
print("Saved myanmar_earthquakes_map.html")
```

### Example 8: Heatmap Visualization

```python
import json
import folium
from folium.plugins import HeatMap

# Load data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Create map
m = folium.Map(location=[21.9, 96.0], zoom_start=6)

# Prepare heatmap data
heat_data = []
for feature in data['features']:
    coords = feature['geometry']['coordinates']
    mag = feature['properties'].get('mag', 1)
    # [lat, lon, weight]
    heat_data.append([coords[1], coords[0], mag])

# Add heatmap
HeatMap(
    heat_data,
    min_opacity=0.3,
    max_val=max(d[2] for d in heat_data),
    radius=15,
    blur=20,
    gradient={0.4: 'blue', 0.6: 'lime', 0.7: 'yellow', 1: 'red'}
).add_to(m)

m.save('earthquake_heatmap.html')
print("Saved earthquake_heatmap.html")
```

### Example 9: Static Map with Matplotlib

```python
import json
import matplotlib.pyplot as plt
import numpy as np

# Load data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Extract coordinates and magnitudes
lons = []
lats = []
mags = []
for feature in data['features']:
    coords = feature['geometry']['coordinates']
    lons.append(coords[0])
    lats.append(coords[1])
    mags.append(feature['properties'].get('mag', 0))

# Create plot
fig, ax = plt.subplots(figsize=(10, 8))

# Scatter plot with size proportional to magnitude
scatter = ax.scatter(
    lons, lats,
    s=[m**3 for m in mags],  # Size proportional to mag^3
    c=mags,  # Color by magnitude
    cmap='YlOrRd',
    alpha=0.6,
    edgecolors='black',
    linewidth=0.5
)

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Magnitude', rotation=270, labelpad=20)

# Labels and title
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Myanmar Earthquakes Distribution')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('earthquake_distribution.png', dpi=300)
print("Saved earthquake_distribution.png")
```

---

## Integration Examples

### Example 10: Save to SQLite Database

```python
import json
import sqlite3
from datetime import datetime

# Load data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Connect to database
conn = sqlite3.connect('earthquakes.db')
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS earthquakes (
    id TEXT PRIMARY KEY,
    magnitude REAL,
    place TEXT,
    time INTEGER,
    longitude REAL,
    latitude REAL,
    depth REAL,
    mag_type TEXT,
    status TEXT,
    alert TEXT,
    tsunami INTEGER,
    felt INTEGER,
    sig INTEGER,
    url TEXT
)
''')

# Insert data
for feature in data['features']:
    props = feature['properties']
    coords = feature['geometry']['coordinates']

    cursor.execute('''
        INSERT OR REPLACE INTO earthquakes VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    ''', (
        feature['id'],
        props.get('mag'),
        props.get('place'),
        props.get('time'),
        coords[0],
        coords[1],
        coords[2],
        props.get('magType'),
        props.get('status'),
        props.get('alert'),
        props.get('tsunami'),
        props.get('felt'),
        props.get('sig'),
        props.get('url')
    ))

conn.commit()
print(f"Inserted {len(data['features'])} earthquakes into database")

# Query example
cursor.execute('SELECT COUNT(*) FROM earthquakes WHERE magnitude >= 5.0')
count = cursor.fetchone()[0]
print(f"Earthquakes with magnitude >= 5.0: {count}")

conn.close()
```

### Example 11: Export to CSV

```python
import json
import csv
import pandas as pd

# Load data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

# Extract to list of dicts
events = []
for feature in data['features']:
    props = feature['properties']
    coords = feature['geometry']['coordinates']

    events.append({
        'id': feature['id'],
        'magnitude': props.get('mag'),
        'place': props.get('place'),
        'time': pd.to_datetime(props.get('time'), unit='ms'),
        'longitude': coords[0],
        'latitude': coords[1],
        'depth_km': coords[2],
        'mag_type': props.get('magType'),
        'status': props.get('status'),
        'alert': props.get('alert'),
        'url': props.get('url')
    })

# Create DataFrame and save
df = pd.DataFrame(events)
df.to_csv('earthquakes.csv', index=False)
print(f"Exported {len(df)} earthquakes to earthquakes.csv")
```

### Example 12: Send Email Alerts for Significant Earthquakes

```python
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd

def send_earthquake_alert(earthquakes, recipient_email):
    """Send email alert for significant earthquakes."""

    if not earthquakes:
        print("No significant earthquakes to report")
        return

    # Create email content
    subject = f"Myanmar Earthquake Alert: {len(earthquakes)} Significant Events"

    html_content = f"""
    <html>
    <body>
        <h2>Significant Earthquake Alert - Myanmar</h2>
        <p>The following significant earthquakes (M >= 5.5) were detected:</p>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Time</th>
                <th>Magnitude</th>
                <th>Location</th>
                <th>Depth</th>
                <th>Link</th>
            </tr>
    """

    for eq in earthquakes:
        html_content += f"""
            <tr>
                <td>{eq['time']}</td>
                <td style="font-weight: bold; color: red;">{eq['magnitude']}</td>
                <td>{eq['place']}</td>
                <td>{eq['depth']:.1f} km</td>
                <td><a href="{eq['url']}">Details</a></td>
            </tr>
        """

    html_content += """
        </table>
        <p><em>Data source: USGS Earthquake Hazards Program</em></p>
    </body>
    </html>
    """

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'earthquake-alerts@example.com'
    msg['To'] = recipient_email

    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)

    # Send email (configure your SMTP settings)
    try:
        # Example with Gmail (requires app password)
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login('your_email@gmail.com', 'your_app_password')
        # server.send_message(msg)
        # server.quit()

        print(f"Alert email would be sent to {recipient_email}")
        print(f"Subject: {subject}")
        print("(SMTP not configured - email not actually sent)")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Load and filter data
with open('usgs_earthquakes_admin0_2025-03-28_to_2026-02-09.geojson', 'r') as f:
    data = json.load(f)

significant = []
for feature in data['features']:
    props = feature['properties']
    mag = props.get('mag', 0)

    if mag >= 5.5:
        coords = feature['geometry']['coordinates']
        significant.append({
            'time': pd.to_datetime(props.get('time'), unit='ms'),
            'magnitude': mag,
            'place': props.get('place'),
            'depth': coords[2],
            'url': props.get('url')
        })

# Send alert
send_earthquake_alert(significant, 'your-email@example.com')
```

---

## Advanced Modifications

### Example 13: Real-time Monitoring Script

```python
import json
import urllib.request
import urllib.parse
import pathlib
import time
from datetime import datetime, timedelta, timezone

def fetch_recent_earthquakes(boundary_file='admin0.json', minutes=60):
    """Fetch earthquakes from the last N minutes."""

    # Load boundary
    data = json.loads(pathlib.Path(boundary_file).read_text(encoding='utf-8'))
    polygons = []

    for feat in data.get('features', []):
        geom = feat.get('geometry', {})
        gtype = geom.get('type')
        coords = geom.get('coordinates', [])
        if gtype == 'Polygon':
            polygons.append(coords)
        elif gtype == 'MultiPolygon':
            polygons.extend(coords)

    # Calculate bbox
    all_pts = [pt for poly in polygons for ring in poly for pt in ring]
    min_lon = min(pt[0] for pt in all_pts)
    max_lon = max(pt[0] for pt in all_pts)
    min_lat = min(pt[1] for pt in all_pts)
    max_lat = max(pt[1] for pt in all_pts)

    # Time range
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=minutes)

    # Fetch from API
    base_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
    params = {
        'format': 'geojson',
        'starttime': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
        'endtime': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
        'minlongitude': f'{min_lon:.6f}',
        'maxlongitude': f'{max_lon:.6f}',
        'minlatitude': f'{min_lat:.6f}',
        'maxlatitude': f'{max_lat:.6f}'
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(url, timeout=60) as resp:
        result = json.load(resp)

    # Spatial filter (use point_in_multipolygon from main script)
    filtered = []
    for f in result.get('features', []):
        coords = (f.get('geometry') or {}).get('coordinates') or []
        if len(coords) >= 2:
            # Simplified check (implement proper point_in_multipolygon)
            if min_lon <= coords[0] <= max_lon and min_lat <= coords[1] <= max_lat:
                filtered.append(f)

    return filtered

def monitor(check_interval_minutes=60, sleep_interval_minutes=5):
    """Continuously monitor for new earthquakes."""

    print(f"Starting earthquake monitor...")
    print(f"Checking for earthquakes every {sleep_interval_minutes} minutes")
    print(f"Looking back {check_interval_minutes} minutes each time")

    last_ids = set()

    while True:
        try:
            print(f"\n[{datetime.now()}] Checking for earthquakes...")

            earthquakes = fetch_recent_earthquakes(minutes=check_interval_minutes)
            new_earthquakes = [eq for eq in earthquakes if eq['id'] not in last_ids]

            if new_earthquakes:
                print(f"Found {len(new_earthquakes)} new earthquake(s)!")
                for eq in new_earthquakes:
                    props = eq['properties']
                    mag = props.get('mag')
                    place = props.get('place')
                    print(f"  - M{mag} {place}")
                    last_ids.add(eq['id'])
            else:
                print("No new earthquakes")

            time.sleep(sleep_interval_minutes * 60)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(sleep_interval_minutes * 60)

if __name__ == "__main__":
    monitor(check_interval_minutes=60, sleep_interval_minutes=5)
```

---

**For more examples, see:**
- README.md for project overview
- USAGE_GUIDE.md for detailed usage instructions
- API_REFERENCE.md for API documentation
