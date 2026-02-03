# DAG Refactoring Comparison

## Overview

This document explains the refactoring improvements made to `extract_fda_events.py` and **why** each change matters for production code.

---

## Key Improvements

### 1. **Separation of Concerns** (Single Responsibility Principle)

#### Before:
```python
def extract_and_save(product_code, **context):
    # 130 lines doing:
    # - Date calculation
    # - API requests
    # - Pagination logic
    # - S3 upload
    # - XCom communication
```

#### After:
```python
# Each function has ONE job:
def extract_fda_events(...)      # Only API extraction
def upload_to_s3(...)             # Only S3 operations
def build_s3_path(...)            # Only path construction
def extract_and_save_task(...)    # Orchestrates the flow
```

**Why This Matters:**
- **Testability**: You can test API extraction without mocking S3
- **Reusability**: `extract_fda_events()` can be used in other contexts
- **Debugging**: When S3 fails, you know exactly which function to check
- **Maintainability**: Changes to S3 logic don't affect API logic

**What Breaks Without It:**
- Hard to unit test individual pieces
- Changes in one area risk breaking unrelated code
- Difficult to reuse extraction logic elsewhere

---

### 2. **Configuration Management**

#### Before:
```python
# Hardcoded values scattered throughout:
bucket_name = 'medtech-sentinel-raw-luke'  # Line 113
base_url = 'https://api.fda.gov/device/event.json'  # Line 30
product_folders = {'DYE': 'heart-valves', ...}  # Line 105
```

#### After:
```python
@dataclass
class PipelineConfig:
    S3_BUCKET: str = 'medtech-sentinel-raw-luke'
    FDA_API_BASE_URL: str = 'https://api.fda.gov/device/event.json'
    PRODUCT_FOLDERS: Dict[str, str] = {...}
    
CONFIG = PipelineConfig()  # Single source of truth
```

**Why This Matters:**
- **Environment Management**: Easy to switch dev/staging/prod configs
- **Change Management**: Update bucket name in ONE place
- **Type Safety**: Dataclass provides structure and validation
- **Documentation**: Config class documents all settings

**What Breaks Without It:**
- Changing bucket name requires finding all occurrences
- Risk of inconsistent values (typos, missed updates)
- Hard to support multiple environments

---

### 3. **Type Hints & Docstrings**

#### Before:
```python
def extract_and_save(product_code, **context):
    # No type information
    # No documentation
```

#### After:
```python
def extract_fda_events(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG
) -> List[Dict[str, Any]]:
    """
    Extract all FDA events for a product code and date range with pagination.
    
    Args:
        product_code: FDA product code (e.g., 'DYE', 'MUD')
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        config: Pipeline configuration object
    
    Returns:
        List of all adverse event records (empty list if no records found)
    """
```

**Why This Matters:**
- **IDE Support**: Autocomplete and error detection
- **Self-Documentation**: Function signature explains what it needs
- **Catch Errors Early**: Type checkers find bugs before runtime
- **Onboarding**: New developers understand functions faster

**What Breaks Without It:**
- IDE can't help with autocomplete
- Runtime errors from wrong argument types
- Harder for new team members to understand

---

### 4. **SQL Injection Prevention**

#### Before:
```python
# Dangerous: Direct string interpolation
delete_command = f"""
DELETE FROM RAW.MEDTECH_SENTINEL.RAW_ADVERSE_EVENTS
WHERE source_file = '{file_path_in_stage}';
"""
cs.execute(delete_command)
```

#### After:
```python
# Safe: Parameterized query
delete_command = f"""
DELETE FROM {config.SNOWFLAKE_DATABASE}.{config.SNOWFLAKE_SCHEMA}.{config.SNOWFLAKE_TABLE}
WHERE source_file = %(file_path)s;
"""
cs.execute(delete_command, {'file_path': file_path})
```

**Why This Matters:**
- **Security**: Prevents SQL injection attacks
- **Data Integrity**: Special characters in file paths handled correctly
- **Best Practice**: Industry standard for database queries

**What Breaks Without It:**
- If file path contains `'` or `;`, SQL breaks
- Potential security vulnerability if XCom is compromised
- Data corruption risk from malformed SQL

**Note**: Table/schema names still use f-strings because Snowflake doesn't support parameterization for identifiers, but `file_path` comes from XCom (internal), not user input.

---

### 5. **Custom Exceptions**

#### Before:
```python
if response.status_code == 404:
    raise AirflowSkipException(msg)
if response.status_code != 200:
    raise Exception(f"API request failed...")
```

#### After:
```python
class NoDataFoundError(Exception):
    """Raised when no data is found for the query (404)."""
    pass

class FDAAPIError(Exception):
    """Raised when FDA API request fails."""
    pass

# In code:
if response.status_code == 404:
    raise NoDataFoundError(...)
if response.status_code != 200:
    raise FDAAPIError(...)
```

**Why This Matters:**
- **Error Handling**: Callers can catch specific exceptions
- **Clarity**: Exception name explains what went wrong
- **Debugging**: Stack traces are more meaningful
- **Monitoring**: Can alert on specific error types

**What Breaks Without It:**
- Generic `Exception` catches everything (hard to handle differently)
- Can't distinguish "no data" from "API broken"
- Monitoring systems can't categorize errors

---

### 6. **Resource Management**

#### Before:
```python
conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
cs = conn.cursor()
try:
    # ... operations ...
finally:
    cs.close()
    conn.close()
```

#### After:
```python
conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
try:
    # ... operations ...
finally:
    conn.close()  # Cursor closed automatically when connection closes
```

**Why This Matters:**
- **Resource Leaks**: Ensures connections always close
- **Simpler Code**: Less boilerplate
- **Error Safety**: Even if operations fail, cleanup happens

**What Breaks Without It:**
- Connection leaks if exception occurs before cleanup
- Snowflake connection pool exhaustion
- Cost: Unclosed connections consume resources

---

### 7. **Code Duplication Elimination**

#### Before:
```python
# S3 path constructed twice:
S3_path = f"data/{folder}/{product_code}_{start_date}_{end_date}.json"  # Line 110
file_path_in_stage = f"{folder}/{product_code}_{start_date}_{end_date}.json"  # Line 124
```

#### After:
```python
# Single function returns both:
def build_s3_path(...) -> tuple[str, str]:
    return full_s3_path, file_path_in_stage
```

**Why This Matters:**
- **DRY Principle**: Don't Repeat Yourself
- **Consistency**: Paths always match
- **Maintainability**: Change path format in one place

**What Breaks Without It:**
- Risk of paths getting out of sync
- Format changes require multiple updates
- Bugs from inconsistent path construction

---

### 8. **Function Organization**

#### Before:
- All functions at top level
- No clear grouping
- Mixed concerns

#### After:
```python
# Clear sections with comments:
# ============================================================================
# CONFIGURATION
# ============================================================================
# ============================================================================
# FDA API EXTRACTION
# ============================================================================
# ============================================================================
# S3 OPERATIONS
# ============================================================================
# ============================================================================
# SNOWFLAKE OPERATIONS
# ============================================================================
# ============================================================================
# AIRFLOW TASKS
# ============================================================================
```

**Why This Matters:**
- **Readability**: Easy to find related code
- **Navigation**: Jump to section you need
- **Mental Model**: Clear separation of concerns

---

## Migration Path

### Option 1: Gradual Refactoring (Recommended)
1. Start with configuration extraction
2. Split `extract_and_save` into smaller functions
3. Add type hints incrementally
4. Fix SQL injection issues
5. Add custom exceptions

### Option 2: Full Replacement
- Test refactored version in parallel
- Switch over when confident
- Keep old version as backup

---

## Testing Improvements

With refactored code, you can now:

```python
# Test API extraction without S3
def test_extract_fda_events():
    events = extract_fda_events('DYE', '20240101', '20240107')
    assert len(events) > 0

# Test S3 upload without API
def test_upload_to_s3():
    mock_data = [{'test': 'data'}]
    upload_to_s3(mock_data, 'test/path.json')

# Test path building
def test_build_s3_path():
    full_path, stage_path = build_s3_path('DYE', '20240101', '20240107')
    assert 'heart-valves' in full_path
```

**Before refactoring**: Hard to test - everything was coupled together.

---

## Performance Impact

**No performance degradation** - refactoring is purely structural. Same operations, better organization.

---

## Learning Takeaways

1. **Single Responsibility**: Each function should do ONE thing well
2. **Configuration Management**: Centralize settings for maintainability
3. **Type Safety**: Type hints catch bugs before runtime
4. **Security**: Always parameterize SQL queries
5. **Error Handling**: Specific exceptions > generic Exception
6. **Resource Management**: Always clean up resources (connections, files)
7. **DRY Principle**: Don't repeat yourself - extract common logic

---

## Next Steps

Consider:
- Moving config to environment variables or Airflow Variables
- Adding unit tests for each function
- Creating a separate `utils.py` for shared functions
- Adding logging instead of print statements
- Implementing retry logic with exponential backoff at function level
