# Deep Dive: Separation of Concerns

## The Problem: One Function Doing Everything

In the original code, `extract_and_save` was a **130-line function** that did **4 different jobs**:

1. **Date calculation** (lines 20-24)
2. **FDA API extraction with pagination** (lines 29-98)
3. **S3 upload** (lines 100-120)
4. **XCom communication** (lines 122-125)

This violates the **Single Responsibility Principle**: each function should have **one reason to change**.

---

## The Solution: Break It Into Focused Functions

### Before: One Monolithic Function

```18:129:airflow/dags/extract_fda_events.py
def extract_and_save(product_code, **context):
    
    start_date = context['data_interval_start'].date()
    end_date = context['data_interval_end'].date() - timedelta(days=1)
    
    start_date = start_date.strftime('%Y%m%d')
    end_date = end_date.strftime('%Y%m%d')


    print(f"Querying events from {start_date} to {end_date} for product_code={product_code}")

    # Build the API request URL and parameters
    base_url = 'https://api.fda.gov/device/event.json'
    skip = 0
    limit = 1000
    results_combined = []
    params = {
        'search': f'device.device_report_product_code:"{product_code}" AND date_received:[{start_date} TO {end_date}]',
        'limit': limit,
        'skip': skip
    }

    # Initial request
    print(f"Request URL: {base_url}")
    print(f"Params: {params}")

    response = requests.get(base_url, params=params)

    if response.status_code == 404:
        msg = (
        f"No data found for product_code={product_code} "
        f"between {start_date} and {end_date}. Skipping this run."
        )
        print(msg)
        raise AirflowSkipException(msg)

    if response.status_code != 200:
        try:
            error_info = response.json()
            print("Error JSON from openFDA:", json.dumps(error_info, indent=2))
        except Exception:
            print("Error response (not JSON):", response.text)
        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()

    # Get meta info
    meta = data.get('meta', {})
    meta_results = meta.get('results', {})
    total_records = meta_results.get('total', 0)
    if total_records == 0:
        print(f"No records found for {product_code} between {start_date} and {end_date}. Skipping upload and load.")
        return False

    # Current batch of results
    batch = data.get('results', [])
    results_combined.extend(batch)
    print(f"Total records to extract: {total_records}")
    print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")

    # Update skip for pagination
    skip += len(batch)

    # ---- Pagination loop ----
    while skip < total_records: # Continue until all records are fetched
        params['skip'] = skip
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")

        data = response.json()
        batch = data.get('results', [])
        if not batch:
            print("No more results returned by API, stopping...")
            break
        results_combined.extend(batch) # Append new batch to combined results
        print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")

        skip += len(batch)
        time.sleep(0.1)  # be polite to the API

    # Upload to S3
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    # Define S3 path
    product_folders = {
        'DYE': 'heart-valves',
        'MUD': 'pulse-oximeters'
    }
    folder = product_folders[product_code]
    S3_path = f"data/{folder}/{product_code}_{start_date}_{end_date}.json"

    # Define S3 bucket name
    bucket_name = 'medtech-sentinel-raw-luke'

    # Upload JSON data to S3
    s3_client.put_object(
    Body=json.dumps(results_combined),
    Bucket=bucket_name,
    Key=S3_path
)
    
    # Save S3 path to XCom
    ti = context['ti']
    file_path_in_stage = f"{folder}/{product_code}_{start_date}_{end_date}.json"
    ti.xcom_push(key='file_path', value= file_path_in_stage)
    print(f"Uploaded {len(results_combined)} "
          f"records to s3://{bucket_name}/{S3_path} on {start_date} "
          f"to {end_date} for {product_code}.")
    return True
```

**Problems with this approach:**
- ❌ Can't test API extraction without S3
- ❌ Can't reuse extraction logic elsewhere
- ❌ Hard to debug (which part failed?)
- ❌ Changes to S3 logic affect API logic
- ❌ 130 lines is hard to understand at once

---

### After: Separated Into Focused Functions

The refactored version breaks this into **4 separate functions**, each with ONE job:

#### 1. **`extract_fda_events()`** - Only Does API Extraction

```149:214:airflow/dags/extract_fda_events_refactored.py
def extract_fda_events(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG
) -> List[Dict[str, Any]]:
    """
    Extract all FDA events for a product code and date range with pagination.
    
    This function handles pagination automatically, fetching all records
    across multiple API requests if needed.
    
    Args:
        product_code: FDA product code (e.g., 'DYE', 'MUD')
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        config: Pipeline configuration object
    
    Returns:
        List of all adverse event records (empty list if no records found)
    
    Raises:
        FDAAPIError: If API requests fail
        NoDataFoundError: If no data exists for the query
    """
    search_query = build_fda_search_query(product_code, start_date, end_date)
    results_combined: List[Dict[str, Any]] = []
    skip = 0
    
    # Initial request to get total count
    print(f"Fetching FDA events for {product_code} from {start_date} to {end_date}")
    data = fetch_fda_api_page(config.FDA_API_BASE_URL, search_query, skip, config.API_LIMIT)
    
    # Extract metadata
    meta = data.get('meta', {})
    meta_results = meta.get('results', {})
    total_records = meta_results.get('total', 0)
    
    if total_records == 0:
        print(f"No records found for {product_code} between {start_date} and {end_date}")
        return []
    
    # Process first batch
    batch = data.get('results', [])
    results_combined.extend(batch)
    print(f"Total records to extract: {total_records}")
    print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")
    
    skip += len(batch)
    
    # Pagination loop - continue until all records fetched
    while skip < total_records:
        data = fetch_fda_api_page(config.FDA_API_BASE_URL, search_query, skip, config.API_LIMIT)
        batch = data.get('results', [])
        
        if not batch:
            print("No more results returned by API, stopping pagination")
            break
        
        results_combined.extend(batch)
        print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")
        
        skip += len(batch)
        time.sleep(config.API_RATE_LIMIT_DELAY)  # Rate limiting
    
    return results_combined
```

**What changed:**
- ✅ **No S3 code** - pure API extraction
- ✅ **No Airflow context** - just takes dates as strings
- ✅ **Returns data** - doesn't upload anything
- ✅ **Reusable** - can be called from anywhere

#### 2. **`upload_to_s3()`** - Only Does S3 Upload

```python
def upload_to_s3(
    data: List[Dict[str, Any]],
    s3_path: str,
    config: PipelineConfig = CONFIG
) -> None:
    """
    Upload JSON data to S3 bucket.
    
    Args:
        data: List of records to upload as JSON
        s3_path: S3 key (path) where data will be stored
        config: Pipeline configuration
    
    Raises:
        Exception: If S3 upload fails
    """
    s3_client = boto3.client('s3')
    
    try:
        s3_client.put_object(
            Body=json.dumps(data),
            Bucket=config.S3_BUCKET,
            Key=s3_path
        )
        print(f"Uploaded {len(data)} records to s3://{config.S3_BUCKET}/{s3_path}")
    except Exception as e:
        raise Exception(f"Failed to upload to S3: {e}") from e
```

**What changed:**
- ✅ **No API code** - just takes data and uploads it
- ✅ **No pagination logic** - doesn't know where data came from
- ✅ **Simple interface** - data in, upload done

#### 3. **`build_s3_path()`** - Only Builds Paths

```221:250:airflow/dags/extract_fda_events_refactored.py
def build_s3_path(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG
) -> Tuple[str, str]:
    """
    Build S3 path for storing extracted data.
    
    Args:
        product_code: FDA product code
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        config: Pipeline configuration
    
    Returns:
        Tuple of (full_s3_path, file_path_in_stage)
        - full_s3_path: Complete S3 path including prefix (for upload)
        - file_path_in_stage: Path relative to stage root (for Snowflake)
    """
    folder = config.PRODUCT_FOLDERS.get(product_code)
    if not folder:
        raise ValueError(f"Unknown product code: {product_code}")
    
    filename = f"{product_code}_{start_date}_{end_date}.json"
    full_s3_path = f"{config.S3_DATA_PREFIX}/{folder}/{filename}"
    file_path_in_stage = f"{folder}/{filename}"
    
    return full_s3_path, file_path_in_stage
```

**What changed:**
- ✅ **Single purpose** - just builds paths
- ✅ **No duplication** - path built once, returned as tuple
- ✅ **Testable** - easy to test path logic

#### 4. **`extract_and_save_task()`** - Orchestrates the Flow

```python
def extract_and_save_task(product_code: str, **context: Any) -> bool:
    """
    Airflow task: Extract FDA events and upload to S3.
    
    This orchestrates the extraction and upload process.
    """
    # Extract date range from Airflow context
    start_date = context['data_interval_start'].date()
    end_date = context['data_interval_end'].date() - timedelta(days=1)
    
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    try:
        # Step 1: Extract events from FDA API
        events = extract_fda_events(product_code, start_date_str, end_date_str)
        
        if not events:
            return False
        
        # Step 2: Build S3 path
        s3_path, file_path_in_stage = build_s3_path(
            product_code, start_date_str, end_date_str
        )
        
        # Step 3: Upload to S3
        upload_to_s3(events, s3_path)
        
        # Step 4: Pass file path to next task via XCom
        context['ti'].xcom_push(key='file_path', value=file_path_in_stage)
        
        return True
        
    except NoDataFoundError as e:
        # Handle 404 gracefully
        raise AirflowSkipException(...) from e
```

**What changed:**
- ✅ **Orchestrator** - calls other functions in sequence
- ✅ **Airflow-specific** - handles context and XCom
- ✅ **Clear flow** - easy to see the steps

---

## Why This Matters: Real-World Benefits

### 1. **Testability** - You Can Test Each Piece Separately

**Before (hard to test):**
```python
# To test API extraction, you need:
# - Mock Airflow context
# - Mock S3 client
# - Mock XCom
# - Can't test extraction without S3 working

def test_extract_and_save():
    # This is HARD - everything is coupled
    pass
```

**After (easy to test):**
```python
# Test API extraction independently
def test_extract_fda_events():
    events = extract_fda_events('DYE', '20240101', '20240107')
    assert len(events) > 0
    assert events[0]['device']['device_report_product_code'] == 'DYE'

# Test S3 upload independently
def test_upload_to_s3():
    mock_data = [{'test': 'data'}]
    upload_to_s3(mock_data, 'test/path.json')
    # Verify S3 was called correctly

# Test path building independently
def test_build_s3_path():
    full_path, stage_path = build_s3_path('DYE', '20240101', '20240107')
    assert 'heart-valves' in full_path
    assert stage_path == 'heart-valves/DYE_20240101_20240107.json'
```

**Why this matters:**
- Find bugs faster (test each piece separately)
- Write tests without complex mocking
- Test edge cases in isolation

---

### 2. **Reusability** - Use Functions in Other Contexts

**Before:**
```python
# Want to extract data for a one-off script?
# You're stuck - extract_and_save requires Airflow context
# You'd have to copy/paste the API code
```

**After:**
```python
# Use extract_fda_events() anywhere!
# In a Jupyter notebook:
events = extract_fda_events('DYE', '20240101', '20240107')
df = pd.DataFrame(events)

# In a different DAG:
events = extract_fda_events('MUD', '20240101', '20240107')
# Do something different with the data

# In a CLI script:
if __name__ == '__main__':
    events = extract_fda_events(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Found {len(events)} events")
```

**Why this matters:**
- Don't duplicate code
- Build new features faster
- Consistent behavior across contexts

---

### 3. **Debugging** - Know Exactly What Failed

**Before:**
```python
# Error: "Failed to upload to S3"
# Where did it fail?
# - API extraction? (lines 29-98)
# - S3 upload? (lines 100-120)
# - Path building? (lines 104-110)
# You have to read through 130 lines to find it
```

**After:**
```python
# Error: "Failed to upload to S3" in upload_to_s3()
# Stack trace points to exact function
# You know immediately: S3 upload failed, not API
# Fix the S3 code, don't touch API code
```

**Why this matters:**
- Faster debugging (know which function failed)
- Smaller code surface to check
- Clear error boundaries

---

### 4. **Maintainability** - Change One Thing Without Breaking Others

**Before:**
```python
# Scenario: S3 bucket name changes
# You have to:
# 1. Find line 113 (bucket_name = ...)
# 2. Make sure you don't break API code (lines 29-98)
# 3. Make sure you don't break path building (lines 104-110)
# Risk: Accidentally change something unrelated
```

**After:**
```python
# Scenario: S3 bucket name changes
# You only touch:
# 1. CONFIG.S3_BUCKET (one place)
# 2. upload_to_s3() function (if needed)
# API code is untouched - can't break it
```

**Why this matters:**
- Safer changes (isolated impact)
- Less risk of breaking unrelated code
- Easier code reviews (smaller changes)

---

## The Pattern: Single Responsibility Principle

**Rule of thumb:** A function should have **one reason to change**.

| Function | Reason to Change |
|----------|-----------------|
| `extract_fda_events()` | FDA API changes |
| `upload_to_s3()` | S3 upload logic changes |
| `build_s3_path()` | Path format changes |
| `extract_and_save_task()` | Airflow orchestration changes |

**If a function has multiple reasons to change, split it.**

---

## How to Apply This Pattern

### Step 1: Identify What Your Function Does

Ask: "What does this function do?"
- If you use "and" in the answer → probably doing too much

**Example:**
- ❌ "Extracts data **and** uploads to S3 **and** sends XCom"
- ✅ "Extracts data from FDA API"

### Step 2: Extract Each Concern

**Before:**
```python
def do_everything():
    # Step 1: Get data
    data = fetch_data()
    
    # Step 2: Process data
    processed = process(data)
    
    # Step 3: Save data
    save(processed)
```

**After:**
```python
def fetch_data():
    # Just fetching
    pass

def process_data(data):
    # Just processing
    pass

def save_data(data):
    # Just saving
    pass

def do_everything():
    # Orchestrates
    data = fetch_data()
    processed = process_data(data)
    save_data(processed)
```

### Step 3: Test Each Function Separately

Write tests for each function:
- `test_fetch_data()`
- `test_process_data()`
- `test_save_data()`

If you can't test them separately, they're still too coupled.

---

## Summary

**Separation of Concerns** means:
- ✅ Each function does ONE thing
- ✅ Functions are independent (can test separately)
- ✅ Functions are reusable (can use elsewhere)
- ✅ Changes are isolated (fix one thing, don't break others)

**The original `extract_and_save` did 4 jobs. The refactored version splits it into 4 functions, each doing 1 job.**

This is a **fundamental software engineering principle** that makes code:
- Easier to understand
- Easier to test
- Easier to maintain
- Easier to reuse
