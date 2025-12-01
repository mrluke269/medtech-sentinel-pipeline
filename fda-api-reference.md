# FDA Device Adverse Event API Reference

## Overview

The FDA provides a public API to access medical device adverse event data from the MAUDE (Manufacturer and User Facility Device Experience) database.

**Documentation:** https://open.fda.gov/apis/device/event/

## API Structure

```
https://api.fda.gov/device/event.json?search=...&limit=...
```

| Component | Description |
|-----------|-------------|
| `api.fda.gov` | FDA's API server |
| `/device/event.json` | Endpoint for device adverse events in JSON format |
| `?` | Separates endpoint from query parameters |
| `&` | Separates multiple parameters |

## Query Parameters

| Parameter | Description | Notes |
|-----------|-------------|-------|
| `search` | Filter criteria for the data | Supports field filters and date ranges |
| `limit` | Number of results to return | **Maximum: 1000** |
| `skip` | Number of results to skip (for pagination) | Default: 0. Max total: 26,000 |

## Search Syntax

### Filter by Product Code
```
search=device.device_report_product_code:"DYE"
```

### Filter by Date Range
Uses bracket syntax for ranges:
```
search=date_received:[20241101+TO+20241107]
```

### Combine Multiple Filters
Use `+AND+` between conditions:
```
search=device.device_report_product_code:"DYE"+AND+date_received:[20241101+TO+20241107]
```

## Example Queries

### Heart Valves (DYE) - One Week of Data
```
https://api.fda.gov/device/event.json?search=device.device_report_product_code:"DYE"+AND+date_received:[20241101+TO+20241107]&limit=2
```

### Pulse Oximeters (MUD) - One Week of Data
```
https://api.fda.gov/device/event.json?search=device.device_report_product_code:"MUD"+AND+date_received:[20241101+TO+20241107]&limit=2
```

## Key Facts

| Item | Detail |
|------|--------|
| Data Source | MAUDE Database |
| Time Period | 2009 to present |
| Update Frequency | Weekly |
| Max Results per Request | 1000 |

## Product Codes for This Project

| Device Type | Product Code | Total Events (approx) |
|-------------|--------------|----------------------|
| Heart Valves | DYE | 35,889 |
| Pulse Oximeters | MUD | 673 |

## Pagination

### Limits

| Limit Type | Value | Description |
|------------|-------|-------------|
| Per-request | 1,000 | Maximum results returned in a single API call |
| Total via pagination | 26,000 | Maximum results accessible via skip/limit combination |

**Note:** The 26,000 cap won't affect our weekly processing since weekly event counts are far below this threshold.

### The `skip` Parameter

Use `skip` to offset results for pagination:

```
&skip=0      → returns results 1-1000
&skip=1000   → returns results 1001-2000
&skip=2000   → returns results 2001-3000
```

### Pagination Example

For a week with 1,200 events:

| Request | Parameters | Results Returned | Running Total |
|---------|-----------|------------------|---------------|
| 1 | `limit=1000&skip=0` | 1000 | 1000 |
| 2 | `limit=1000&skip=1000` | 200 | 1200 |

### How to Know When to Stop

The API response includes metadata:
```json
{
  "meta": {
    "results": {
      "skip": 0,
      "limit": 1000,
      "total": 1200
    }
  },
  "results": [...]
}
```

**Two stopping conditions (either works):**

1. **Compare to total:** Stop when `skip + limit > total`
2. **Compare results received:** Stop when `results_received < limit` (asked for 1000 but got fewer)

---

## Notes

- Date format: `YYYYMMDD`
- The `+` in URLs represents a space (URL encoding)
- Brackets `[ ]` denote ranges for dates, numbers, or strings