import json
import urllib.parse
import urllib.request
import pathlib
from datetime import datetime, timezone

def point_in_ring(x, y, ring):
    """
    Ray-casting algorithm to determine if a point is inside a polygon ring.
    """
    inside = False
    n = len(ring)
    if n < 3:
        return False
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if ((y1 > y) != (y2 > y)):
            xinters = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xinters:
                inside = not inside
    return inside

def point_in_polygon(x, y, poly):
    """
    Checks if a point is inside the exterior ring and NOT inside any holes.
    """
    if not poly or not point_in_ring(x, y, poly[0]):
        return False
    # Check interior rings (holes)
    for hole in poly[1:]:
        if point_in_ring(x, y, hole):
            return False
    return True

def point_in_multipolygon(x, y, multipoly):
    """Checks if a point is within any polygon of a MultiPolygon."""
    return any(point_in_polygon(x, y, poly) for poly in multipoly)

def main():
    # 1. Load Admin Boundary
    admin_path = pathlib.Path('admin0.json')
    if not admin_path.exists():
        raise FileNotFoundError("admin0.json not found in current directory.")
        
    data = json.loads(admin_path.read_text(encoding='utf-8'))
    polygons = []
    
    # Parse GeoJSON features into a list of polygons
    for feat in data.get('features', []):
        geom = feat.get('geometry', {})
        gtype = geom.get('type')
        coords = geom.get('coordinates', [])
        if gtype == 'Polygon':
            polygons.append(coords)
        elif gtype == 'MultiPolygon':
            polygons.extend(coords)

    if not polygons:
        raise SystemExit('No polygon geometry found in admin0.json')

    # 2. Calculate Bounding Box (BBox)
    all_pts = [pt for poly in polygons for ring in poly for pt in ring]
    min_lon = min(pt[0] for pt in all_pts)
    max_lon = max(pt[0] for pt in all_pts)
    min_lat = min(pt[1] for pt in all_pts)
    max_lat = max(pt[1] for pt in all_pts)

    # 3. Fetch Data from USGS API
    start_date = '2025-03-28'
    end_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    base_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
    
    limit = 20000
    offset = 1
    all_features = []

    print(f"Fetching events from {start_date} to {end_time}...")
    
    while True:
        params = {
            'format': 'geojson',
            'starttime': start_date,
            'endtime': end_time,
            'minlongitude': f'{min_lon:.6f}',
            'maxlongitude': f'{max_lon:.6f}',
            'minlatitude': f'{min_lat:.6f}',
            'maxlatitude': f'{max_lat:.6f}',
            'orderby': 'time-asc',
            'limit': str(limit),
            'offset': str(offset)
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        with urllib.request.urlopen(url, timeout=120) as resp:
            batch_data = json.load(resp)
        
        batch = batch_data.get('features', [])
        all_features.extend(batch)
        
        print(f'Fetched {len(batch)} events (Total so far: {len(all_features)})')
        
        if len(batch) < limit:
            break
        offset += limit

    # 4. Spatial Filtering (Refining BBox results to the exact Polygon shape)
    filtered = []
    for f in all_features:
        coords = (f.get('geometry') or {}).get('coordinates') or []
        if len(coords) >= 2:
            if point_in_multipolygon(coords[0], coords[1], polygons):
                filtered.append(f)

    # 5. Output Results
    out_data = {
        'type': 'FeatureCollection',
        'metadata': {
            'generated': int(datetime.now(timezone.utc).timestamp() * 1000),
            'title': 'USGS Earthquakes within admin0 polygon',
            'count': len(filtered),
            'bboxCount': len(all_features),
            'starttime': start_date,
            'endtime': end_time,
            'source': 'USGS FDSN Event API'
        },
        'features': filtered
    }

    date_str = datetime.now(timezone.utc).date().isoformat()
    out_name = f'usgs_earthquakes_admin0_{start_date}_to_{date_str}.geojson'
    
    pathlib.Path(out_name).write_text(json.dumps(out_data, separators=(',', ':')), encoding='utf-8')
    print(f'Done! Wrote {len(filtered)} filtered events to {out_name}')

if __name__ == "__main__":
    main()