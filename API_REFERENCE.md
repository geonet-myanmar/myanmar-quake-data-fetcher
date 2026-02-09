# API Reference

This document provides detailed information about the functions and USGS API used in the GeoNet project.

## Python Functions

### `point_in_ring(x, y, ring)`

Determines if a point is inside a polygon ring using the ray-casting algorithm.

**Parameters:**
- `x` (float): Longitude coordinate of the point
- `y` (float): Latitude coordinate of the point
- `ring` (list): List of coordinate pairs [[lon1, lat1], [lon2, lat2], ...]

**Returns:**
- `bool`: True if point is inside the ring, False otherwise

**Algorithm:**
The ray-casting algorithm works by:
1. Casting an imaginary ray from the point to infinity (horizontal ray to the right)
2. Counting how many times the ray crosses the polygon boundary
3. If the number of crossings is odd, the point is inside
4. If the number of crossings is even, the point is outside

**Example:**
```python
ring = [[0, 0], [10, 0], [10, 10], [0, 10]]  # Square
print(point_in_ring(5, 5, ring))    # True - inside
print(point_in_ring(15, 5, ring))   # False - outside
```

**Edge Cases:**
- Returns False if ring has fewer than 3 points
- Handles points exactly on edges (implementation detail may vary)

---

### `point_in_polygon(x, y, poly)`

Checks if a point is inside a polygon, accounting for holes (interior rings).

**Parameters:**
- `x` (float): Longitude coordinate of the point
- `y` (float): Latitude coordinate of the point
- `poly` (list): Polygon structure where:
  - `poly[0]` is the exterior ring (outer boundary)
  - `poly[1:]` are interior rings (holes)

**Returns:**
- `bool`: True if point is inside the polygon and NOT in any holes

**Logic:**
1. Check if point is in exterior ring (outer boundary)
2. If yes, check if point is in any interior ring (hole)
3. Return True only if in exterior and NOT in any interior ring

**Example:**
```python
# Polygon with a hole
exterior = [[0, 0], [10, 0], [10, 10], [0, 10]]
hole = [[3, 3], [7, 3], [7, 7], [3, 7]]
poly = [exterior, hole]

print(point_in_polygon(5, 5, poly))   # False - inside hole
print(point_in_polygon(2, 2, poly))   # True - inside polygon, outside hole
print(point_in_polygon(15, 5, poly))  # False - outside polygon
```

---

### `point_in_multipolygon(x, y, multipoly)`

Checks if a point is within any polygon of a MultiPolygon geometry.

**Parameters:**
- `x` (float): Longitude coordinate of the point
- `y` (float): Latitude coordinate of the point
- `multipoly` (list): List of polygons, each in the format used by `point_in_polygon`

**Returns:**
- `bool`: True if point is inside ANY of the constituent polygons

**Use Case:**
Myanmar's boundary is a MultiPolygon (mainland + islands). This function checks if an earthquake occurred anywhere in Myanmar.

**Example:**
```python
# Two separate polygons
polygon1 = [[[0, 0], [5, 0], [5, 5], [0, 5]]]
polygon2 = [[[10, 10], [15, 10], [15, 15], [10, 15]]]
multipoly = [polygon1, polygon2]

print(point_in_multipolygon(3, 3, multipoly))    # True - in polygon1
print(point_in_multipolygon(12, 12, multipoly))  # True - in polygon2
print(point_in_multipolygon(7, 7, multipoly))    # False - in neither
```

---

### `main()`

Main execution function that orchestrates the entire data fetching and filtering process.

**Process Flow:**
1. Load admin boundary from `admin0.json`
2. Parse GeoJSON and extract polygon coordinates
3. Calculate bounding box from boundary coordinates
4. Fetch earthquake data from USGS API (with pagination)
5. Filter earthquakes to exact polygon boundaries
6. Generate output GeoJSON file

**Error Handling:**
- Raises `FileNotFoundError` if admin0.json is missing
- Raises `SystemExit` if no polygon geometry found
- API errors may raise `urllib.error.URLError`

**Output:**
- Creates a GeoJSON file with filtered earthquake data
- Prints progress to console

---

## USGS FDSN Event Web Service API

### Base URL
```
https://earthquake.usgs.gov/fdsnws/event/1/query
```

### Supported Output Formats
- `geojson` (default in this project)
- `xml`
- `csv`
- `kml`
- `quakeml`
- `text`

### Query Parameters

#### Time Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `starttime` | ISO8601 | Start time for search | `2025-01-01` or `2025-01-01T00:00:00` |
| `endtime` | ISO8601 | End time for search | `2025-12-31T23:59:59` |

#### Location Parameters (Rectangular)

| Parameter | Type | Description | Range | Example |
|-----------|------|-------------|-------|---------|
| `minlatitude` | Decimal | Southern boundary | -90 to 90 | `15.0` |
| `maxlatitude` | Decimal | Northern boundary | -90 to 90 | `28.5` |
| `minlongitude` | Decimal | Western boundary | -180 to 180 | `92.2` |
| `maxlongitude` | Decimal | Eastern boundary | -180 to 180 | `101.2` |

#### Location Parameters (Circular)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `latitude` | Decimal | Center latitude | `21.9` |
| `longitude` | Decimal | Center longitude | `96.0` |
| `maxradius` | Decimal | Max radius in degrees | `5.0` |
| `minradius` | Decimal | Min radius in degrees | `0.0` |

**Note:** Cannot use both rectangular and circular simultaneously.

#### Magnitude Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `minmagnitude` | Decimal | Minimum magnitude | `3.0` |
| `maxmagnitude` | Decimal | Maximum magnitude | `7.0` |
| `magnitudetype` | String | Magnitude type | `ml`, `ms`, `mb`, `mw` |

#### Depth Parameters

| Parameter | Type | Description | Unit | Example |
|-----------|------|-------------|------|---------|
| `mindepth` | Decimal | Minimum depth | km | `10` |
| `maxdepth` | Decimal | Maximum depth | km | `100` |

#### Event Type Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `eventtype` | String | Type of event | `earthquake`, `quarry` |

Common event types:
- `earthquake` - Natural earthquake
- `quarry` - Quarry blast
- `explosion` - Explosion
- `mining explosion` - Mining explosion
- `nuclear explosion` - Nuclear explosion
- `rockburst` - Rock burst

#### Alert Parameters

| Parameter | Type | Description | Values |
|-----------|------|-------------|--------|
| `alertlevel` | String | PAGER alert level | `green`, `yellow`, `orange`, `red` |

#### Review Status

| Parameter | Type | Description | Values |
|-----------|------|-------------|--------|
| `reviewstatus` | String | Review status | `automatic`, `reviewed`, `all` |

#### Output Parameters

| Parameter | Type | Description | Default | Max | Example |
|-----------|------|-------------|---------|-----|---------|
| `format` | String | Output format | `quakeml` | - | `geojson` |
| `limit` | Integer | Max number of results | 20000 | 20000 | `1000` |
| `offset` | Integer | Result offset (pagination) | 1 | - | `1001` |
| `orderby` | String | Sort order | `time` | - | `time-asc`, `magnitude-desc` |

**orderby values:**
- `time` - Most recent first (default)
- `time-asc` - Oldest first
- `magnitude` - Largest magnitude first
- `magnitude-asc` - Smallest magnitude first

### Response Format (GeoJSON)

#### Structure
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generated": 1707480645000,
    "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?...",
    "title": "USGS Earthquakes",
    "status": 200,
    "api": "1.14.1",
    "count": 1234
  },
  "features": [
    {
      "type": "Feature",
      "properties": { ... },
      "geometry": { ... },
      "id": "us6000..."
    }
  ],
  "bbox": [min_lon, min_lat, min_depth, max_lon, max_lat, max_depth]
}
```

#### Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `generated` | Integer | Unix timestamp (milliseconds) when response was generated |
| `url` | String | Request URL |
| `title` | String | Result set title |
| `status` | Integer | HTTP status code |
| `api` | String | API version |
| `count` | Integer | Number of events in response |

#### Feature Properties

Comprehensive list of earthquake properties:

##### Basic Information
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `mag` | Decimal | Magnitude | `4.5` |
| `place` | String | Location description | `"12 km E of Yangon, Myanmar"` |
| `time` | Integer | Occurrence time (Unix ms) | `1680000000000` |
| `updated` | Integer | Last update time (Unix ms) | `1680001000000` |
| `tz` | Integer | Timezone offset (minutes) | `390` |
| `url` | String | Event details page | `"https://earthquake.usgs.gov/earthquakes/eventpage/us6000..."` |
| `detail` | String | GeoJSON detail feed | `"https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=us6000..."` |
| `felt` | Integer | Number of felt reports | `123` |
| `cdi` | Decimal | Community Decimal Intensity | `4.5` |
| `mmi` | Decimal | Modified Mercalli Intensity | `5.2` |
| `alert` | String | PAGER alert level | `"green"`, `"yellow"`, `"orange"`, `"red"` |
| `status` | String | Review status | `"automatic"`, `"reviewed"`, `"deleted"` |
| `tsunami` | Integer | Tsunami warning flag | `0` or `1` |

##### Significance & Impact
| Property | Type | Description | Range |
|----------|------|-------------|-------|
| `sig` | Integer | Significance score | 0-1000+ (typically 0-1000) |

**Significance Calculation:**
```
sig = mag * 100 * (mag / 6.5)
```
Modified by:
- Number of felt reports
- Estimated economic impact (PAGER)
- Tsunami potential

##### Source Information
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `net` | String | Network code | `"us"` (USGS), `"ci"` (CalTech) |
| `code` | String | Event code | `"6000abc123"` |
| `ids` | String | All associated IDs | `",us6000abc,ci123456,"` |
| `sources` | String | Contributing networks | `",us,ci,nc,"` |
| `types` | String | Available product types | `",origin,phase-data,shakemap,"` |

##### Location Quality
| Property | Type | Description | Unit |
|----------|------|-------------|------|
| `nst` | Integer | Number of reporting stations | count |
| `dmin` | Decimal | Minimum distance to stations | degrees |
| `rms` | Decimal | Root mean square travel time residual | seconds |
| `gap` | Decimal | Azimuthal gap | degrees |

**Quality Interpretation:**
- `nst` > 10: Good station coverage
- `dmin` < 2°: Nearby stations available
- `rms` < 1.0: Good fit to data
- `gap` < 180°: Good azimuthal coverage

##### Magnitude Details
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `magType` | String | Magnitude type | `"mb"`, `"ml"`, `"ms"`, `"mw"` |
| `type` | String | Event type | `"earthquake"`, `"quarry blast"` |

**Magnitude Types:**
- `mb` - Body wave magnitude
- `ml` - Local (Richter) magnitude
- `ms` - Surface wave magnitude
- `mw` - Moment magnitude (most accurate for large events)
- `md` - Duration magnitude
- `mh` - Helicorder magnitude

##### Additional
| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `title` | String | Event title | `"M 4.5 - 12 km E of Yangon, Myanmar"` |
| `horizontalError` | Decimal | Horizontal location error | `7.5` km |
| `depthError` | Decimal | Depth error | `3.2` km |
| `magError` | Decimal | Magnitude error | `0.1` |
| `magNst` | Integer | Stations used for magnitude | `45` |

#### Feature Geometry

```json
{
  "type": "Point",
  "coordinates": [longitude, latitude, depth_km]
}
```

| Index | Type | Description | Range |
|-------|------|-------------|-------|
| `[0]` | Decimal | Longitude | -180 to 180 |
| `[1]` | Decimal | Latitude | -90 to 90 |
| `[2]` | Decimal | Depth (km) | Usually 0-700 |

**Depth Information:**
- Positive values = below sea level
- 0-70 km: Shallow earthquakes (most common)
- 70-300 km: Intermediate
- 300-700 km: Deep earthquakes

### Rate Limits and Usage

#### Limits
- **Max results per request**: 20,000 events
- **Timeout**: Requests may timeout after 60-120 seconds
- **No authentication required**: API is free and open

#### Best Practices
1. Use specific date ranges instead of querying all history
2. Add magnitude filters when appropriate
3. Use pagination (offset) for large datasets
4. Implement exponential backoff for retries
5. Cache results locally when possible
6. Be respectful with request frequency

#### Example: Pagination

```python
limit = 20000
offset = 1
all_results = []

while True:
    url = f"{base_url}?format=geojson&limit={limit}&offset={offset}&..."
    response = fetch_data(url)
    batch = response['features']
    all_results.extend(batch)

    if len(batch) < limit:
        break  # No more data
    offset += limit
```

### Error Responses

#### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Success |
| 204 | No Content | Query successful but no results |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporarily unavailable |

#### Error Response Format

```json
{
  "type": "error",
  "metadata": {
    "error": "Bad Request",
    "status": 400
  }
}
```

### Example Queries

#### Basic Query
```
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2025-01-01&endtime=2025-12-31
```

#### With Magnitude Filter
```
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2025-01-01&minmagnitude=5.0
```

#### Rectangular Region
```
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minlatitude=15&maxlatitude=28&minlongitude=92&maxlongitude=101
```

#### Circular Region (100km around Yangon)
```
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude=16.8&longitude=96.2&maxradiuskm=100
```

#### Only Reviewed Events
```
https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&reviewstatus=reviewed&minmagnitude=4.0
```

## References

- **USGS API Documentation**: https://earthquake.usgs.gov/fdsnws/event/1/
- **GeoJSON Specification**: https://tools.ietf.org/html/rfc7946
- **FDSN Web Service Specification**: https://www.fdsn.org/webservices/
- **USGS Earthquake Catalogs**: https://earthquake.usgs.gov/data/comcat/

---

**Last Updated**: February 2026
