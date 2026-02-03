# Syntax and Logic Explained: Step-by-Step

## Overview

This guide explains the **syntax** (how to write it) and **logic** (how it works) in the refactored code. We'll go piece by piece, starting simple and building up.

---

## Part 1: Function Definition Syntax

### Basic Function (You Know This)

```python
def my_function(name):
    return f"Hello {name}"

result = my_function("Luke")
# result = "Hello Luke"
```

### Function with Type Hints (New Syntax)

```python
def my_function(name: str) -> str:
    return f"Hello {name}"
```

**Breaking it down:**
- `name: str` means "parameter `name` must be a string"
- `-> str` means "this function returns a string"
- The `:` and `->` are just syntax markers - they don't change how it works

**Why use them?**
- Helps IDEs autocomplete
- Documents what the function expects/returns
- Catches errors before running

**You can ignore them** - they're optional in Python. This works too:
```python
def my_function(name):
    return f"Hello {name}"
```

---

## Part 2: Multiple Return Values (Tuples)

### The Concept

A function can return **multiple values** using a tuple:

```python
def get_name_and_age():
    return "Luke", 30  # This is a tuple

# How to use it:
name, age = get_name_and_age()
# name = "Luke"
# age = 30
```

**What's happening:**
- `return "Luke", 30` creates a tuple `("Luke", 30)`
- `name, age = ...` **unpacks** the tuple into two variables
- This is called **tuple unpacking**

### In Our Code: `build_s3_path()`

```python
def build_s3_path(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG
) -> Tuple[str, str]:  # Returns a tuple of 2 strings
    folder = config.PRODUCT_FOLDERS.get(product_code)
    filename = f"{product_code}_{start_date}_{end_date}.json"
    full_s3_path = f"data/{folder}/{filename}"
    file_path_in_stage = f"{folder}/{filename}"
    
    return full_s3_path, file_path_in_stage  # Returns 2 values
```

**How it's used:**

```python
# Call the function
s3_path, file_path_in_stage = build_s3_path(
    product_code, start_date_str, end_date_str
)

# Now you have:
# s3_path = "data/heart-valves/DYE_20240101_20240107.json"
# file_path_in_stage = "heart-valves/DYE_20240101_20240107.json"
```

**Step by step:**
1. Function returns: `("data/heart-valves/DYE_20240101_20240107.json", "heart-valves/DYE_20240101_20240107.json")`
2. The `=` unpacks it into two variables
3. First value goes to `s3_path`, second to `file_path_in_stage`

**If you don't unpack:**
```python
result = build_s3_path(...)
# result = ("data/heart-valves/...", "heart-valves/...")
# You'd have to access: result[0] and result[1]
```

---

## Part 3: Default Parameters

### The Concept

You can give parameters **default values**:

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}"

greet("Luke")              # Uses default: "Hello, Luke"
greet("Luke", "Hi")        # Overrides: "Hi, Luke"
```

### In Our Code

```python
def extract_fda_events(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG  # Default value
) -> List[Dict[str, Any]]:
    # ... function code ...
```

**What this means:**
- `config` has a default value of `CONFIG` (a global variable)
- You can call it two ways:

```python
# Option 1: Use default config
events = extract_fda_events('DYE', '20240101', '20240107')

# Option 2: Provide your own config
my_config = PipelineConfig(S3_BUCKET='my-bucket')
events = extract_fda_events('DYE', '20240101', '20240107', config=my_config)
```

**Why use defaults?**
- Most of the time you use the same config
- Saves typing
- Can override when needed (testing, different environments)

---

## Part 4: How Functions Call Each Other

### The Flow in `extract_and_save_task()`

Let's trace through what happens when Airflow calls this function:

```python
def extract_and_save_task(product_code: str, **context: Any) -> bool:
    # Step 1: Get dates from Airflow context
    start_date = context['data_interval_start'].date()
    end_date = context['data_interval_end'].date() - timedelta(days=1)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    # Step 2: Call extract_fda_events()
    events = extract_fda_events(product_code, start_date_str, end_date_str)
    #     ↑
    #     This calls another function and stores the result
    
    # Step 3: Check if we got data
    if not events:
        return False
    
    # Step 4: Call build_s3_path() and unpack the result
    s3_path, file_path_in_stage = build_s3_path(
        product_code, start_date_str, end_date_str
    )
    #     ↑
    #     This calls another function and unpacks 2 values
    
    # Step 5: Call upload_to_s3()
    upload_to_s3(events, s3_path)
    #     ↑
    #     This calls another function (doesn't return anything)
    
    # Step 6: Save path for next task
    context['ti'].xcom_push(key='file_path', value=file_path_in_stage)
    
    return True
```

### Visual Flow

```
Airflow calls extract_and_save_task()
    │
    ├─> Gets dates from context
    │
    ├─> Calls extract_fda_events()
    │   │
    │   ├─> Calls build_fda_search_query()
    │   │   └─> Returns: "device.device_report_product_code:'DYE'..."
    │   │
    │   ├─> Calls fetch_fda_api_page() (multiple times in loop)
    │   │   └─> Returns: {"meta": {...}, "results": [...]}
    │   │
    │   └─> Returns: [event1, event2, event3, ...]
    │
    ├─> Calls build_s3_path()
    │   └─> Returns: ("data/heart-valves/...", "heart-valves/...")
    │
    ├─> Calls upload_to_s3()
    │   └─> Uploads to S3 (no return value)
    │
    └─> Returns: True
```

---

## Part 5: Inside `extract_fda_events()` - How It Calls Other Functions

Let's see how `extract_fda_events()` uses other functions:

```python
def extract_fda_events(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG
) -> List[Dict[str, Any]]:
    
    # Line 174: Call build_fda_search_query()
    search_query = build_fda_search_query(product_code, start_date, end_date)
    #     ↑
    #     Calls function, stores result in search_query
    #     search_query = "device.device_report_product_code:'DYE' AND date_received:[20240101 TO 20240107]"
    
    # Line 175: Initialize empty list
    results_combined: List[Dict[str, Any]] = []
    #     ↑
    #     Type hint says "this will be a list of dictionaries"
    #     Same as: results_combined = []
    
    skip = 0
    
    # Line 180: Call fetch_fda_api_page()
    data = fetch_fda_api_page(config.FDA_API_BASE_URL, search_query, skip, config.API_LIMIT)
    #     ↑
    #     Calls function with 4 arguments:
    #     1. config.FDA_API_BASE_URL = "https://api.fda.gov/device/event.json"
    #     2. search_query = "device.device_report_product_code:'DYE'..."
    #     3. skip = 0
    #     4. config.API_LIMIT = 1000
    #     Returns: {"meta": {...}, "results": [...]}
    
    # Line 183-185: Extract data from the response
    meta = data.get('meta', {})
    #     ↑
    #     Gets 'meta' key from dictionary, or {} if not found
    #     Same as: meta = data['meta'] if 'meta' in data else {}
    
    meta_results = meta.get('results', {})
    total_records = meta_results.get('total', 0)
    
    # Line 200-212: Loop that calls fetch_fda_api_page() multiple times
    while skip < total_records:
        data = fetch_fda_api_page(config.FDA_API_BASE_URL, search_query, skip, config.API_LIMIT)
        #     ↑
        #     Calls the same function again, but with different skip value
        #     First time: skip=0 (get records 1-1000)
        #     Second time: skip=1000 (get records 1001-2000)
        #     etc.
        
        batch = data.get('results', [])
        results_combined.extend(batch)
        #     ↑
        #     Adds batch to the list
        #     Same as: results_combined = results_combined + batch
        
        skip += len(batch)
        time.sleep(config.API_RATE_LIMIT_DELAY)
    
    # Line 214: Return the combined results
    return results_combined
    #     ↑
    #     Returns the list of all events
```

---

## Part 6: Understanding `**context` and `**kwargs`

### What is `**context`?

The `**` means "unpack all keyword arguments into a dictionary":

```python
def my_function(**kwargs):
    print(kwargs)
    # kwargs is a dictionary

my_function(name="Luke", age=30)
# Prints: {'name': 'Luke', 'age': 30}
```

### In Our Code

```python
def extract_and_save_task(product_code: str, **context: Any) -> bool:
    # Airflow passes context as keyword arguments
    # context becomes a dictionary with keys like:
    # - 'data_interval_start'
    # - 'data_interval_end'
    # - 'ti' (task instance)
    
    start_date = context['data_interval_start'].date()
    #     ↑
    #     Access dictionary value using key
```

**Why use `**context`?**
- Airflow passes many things in context
- We only need a few of them
- `**context` lets us access any of them

**Alternative (if you knew exactly what you needed):**
```python
def extract_and_save_task(
    product_code: str,
    data_interval_start,
    data_interval_end,
    ti
) -> bool:
    # But this is less flexible
```

---

## Part 7: Type Hints Explained

### Basic Types

```python
def example(
    name: str,              # String
    age: int,               # Integer
    is_active: bool,        # Boolean
    scores: list,           # List (any type)
    config: dict            # Dictionary (any type)
):
    pass
```

### Generic Types (More Specific)

```python
from typing import List, Dict, Any, Tuple

def example(
    events: List[Dict[str, Any]],  # List of dictionaries
    #     ↑
    #     "A list where each item is a dictionary
    #      with string keys and any type of values"
    
    paths: Tuple[str, str]         # Tuple of 2 strings
    #     ↑
    #     "A tuple containing exactly 2 strings"
):
    pass
```

### Breaking Down `List[Dict[str, Any]]`

```python
events: List[Dict[str, Any]]
```

**Reading it from outside in:**
1. `List[...]` = "a list"
2. `Dict[str, Any]` = "each item is a dictionary"
3. `str` = "dictionary keys are strings"
4. `Any` = "dictionary values can be anything"

**Example:**
```python
events = [
    {"device": "valve", "date": "2024-01-01"},  # Dict[str, Any]
    {"device": "oximeter", "date": "2024-01-02"} # Dict[str, Any]
]
# This matches List[Dict[str, Any]]
```

---

## Part 8: Complete Execution Flow (Step by Step)

Let's trace through what happens when Airflow runs the task:

### Step 1: Airflow Calls the Task

```python
# Airflow internally does:
extract_and_save_task(
    product_code='DYE',
    **{
        'data_interval_start': datetime(2024, 1, 1),
        'data_interval_end': datetime(2024, 1, 8),
        'ti': <TaskInstance object>,
        # ... other context ...
    }
)
```

### Step 2: Extract Dates

```python
# Inside extract_and_save_task():
start_date = context['data_interval_start'].date()
# start_date = date(2024, 1, 1)

end_date = context['data_interval_end'].date() - timedelta(days=1)
# end_date = date(2024, 1, 7)

start_date_str = start_date.strftime('%Y%m%d')
# start_date_str = "20240101"

end_date_str = end_date.strftime('%Y%m%d')
# end_date_str = "20240107"
```

### Step 3: Call `extract_fda_events()`

```python
events = extract_fda_events('DYE', '20240101', '20240107')
```

**Inside `extract_fda_events()`:**

```python
# Line 174: Build search query
search_query = build_fda_search_query('DYE', '20240101', '20240107')
# search_query = "device.device_report_product_code:'DYE' AND date_received:[20240101 TO 20240107]"

# Line 180: Fetch first page
data = fetch_fda_api_page(
    'https://api.fda.gov/device/event.json',
    search_query,
    0,      # skip
    1000    # limit
)
# data = {
#     "meta": {"results": {"total": 1500}},
#     "results": [event1, event2, ..., event1000]
# }

# Line 192-193: Add first batch
batch = data.get('results', [])  # Gets 1000 events
results_combined.extend(batch)   # Adds them to list
# results_combined now has 1000 events

# Line 200-212: Loop for remaining records
while skip < total_records:  # 1000 < 1500, so continue
    data = fetch_fda_api_page(..., skip=1000, ...)
    batch = data.get('results', [])  # Gets remaining 500 events
    results_combined.extend(batch)   # Now has 1500 events
    skip += len(batch)               # skip = 1500
    # Loop condition: 1500 < 1500 is False, so exit

# Line 214: Return all events
return results_combined  # Returns list of 1500 events
```

**Back in `extract_and_save_task()`:**

```python
# events now contains 1500 event dictionaries
events = [event1, event2, ..., event1500]
```

### Step 4: Build S3 Path

```python
s3_path, file_path_in_stage = build_s3_path('DYE', '20240101', '20240107')
```

**Inside `build_s3_path()`:**

```python
folder = config.PRODUCT_FOLDERS.get('DYE')
# folder = "heart-valves"

filename = f"DYE_20240101_20240107.json"
# filename = "DYE_20240101_20240107.json"

full_s3_path = f"data/{folder}/{filename}"
# full_s3_path = "data/heart-valves/DYE_20240101_20240107.json"

file_path_in_stage = f"{folder}/{filename}"
# file_path_in_stage = "heart-valves/DYE_20240101_20240107.json"

return full_s3_path, file_path_in_stage
# Returns: ("data/heart-valves/DYE_20240101_20240107.json", "heart-valves/DYE_20240101_20240107.json")
```

**Back in `extract_and_save_task()`:**

```python
# Tuple unpacking happens here:
s3_path = "data/heart-valves/DYE_20240101_20240107.json"
file_path_in_stage = "heart-valves/DYE_20240101_20240107.json"
```

### Step 5: Upload to S3

```python
upload_to_s3(events, s3_path)
```

**Inside `upload_to_s3()`:**

```python
s3_client = boto3.client('s3')
s3_client.put_object(
    Body=json.dumps(events),  # Convert list to JSON string
    Bucket='medtech-sentinel-raw-luke',
    Key='data/heart-valves/DYE_20240101_20240107.json'
)
# File is now in S3
# Function returns None (no return statement)
```

### Step 6: Save Path for Next Task

```python
context['ti'].xcom_push(key='file_path', value=file_path_in_stage)
# Saves "heart-valves/DYE_20240101_20240107.json" to XCom
# Next task can retrieve it
```

### Step 7: Return Success

```python
return True
# Airflow knows task succeeded
```

---

## Part 9: Common Patterns You'll See

### Pattern 1: Call Function, Store Result

```python
result = some_function(arg1, arg2)
# Call function, store what it returns
```

### Pattern 2: Unpack Multiple Returns

```python
value1, value2 = function_that_returns_two_things()
# Function returns tuple, unpack into 2 variables
```

### Pattern 3: Call Function, Use Result Immediately

```python
if not some_function():
    return False
# Call function, check result, don't store it
```

### Pattern 4: Chain Function Calls

```python
data = fetch_api_page(build_search_query(product_code, start, end))
# Inner function runs first, result passed to outer function
```

---

## Part 10: Practice Reading Code

Let's read this function call by call:

```python
def extract_and_save_task(product_code: str, **context: Any) -> bool:
    start_date = context['data_interval_start'].date()
    end_date = context['data_interval_end'].date() - timedelta(days=1)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    try:
        events = extract_fda_events(product_code, start_date_str, end_date_str)
        
        if not events:
            return False
        
        s3_path, file_path_in_stage = build_s3_path(
            product_code, start_date_str, end_date_str
        )
        
        upload_to_s3(events, s3_path)
        
        context['ti'].xcom_push(key='file_path', value=file_path_in_stage)
        
        return True
```

**Reading it:**
1. Get dates from context, convert to strings
2. **Call** `extract_fda_events()` → **store** result in `events`
3. If no events, return False
4. **Call** `build_s3_path()` → **unpack** 2 values into `s3_path` and `file_path_in_stage`
5. **Call** `upload_to_s3()` (doesn't return anything)
6. Save path to XCom
7. Return True

---

## Summary: Key Syntax Patterns

| Pattern | Example | What It Does |
|---------|---------|--------------|
| Type hints | `name: str` | Says parameter is a string |
| Return type | `-> bool` | Says function returns boolean |
| Default param | `config=CONFIG` | Uses CONFIG if not provided |
| Multiple returns | `return a, b` | Returns tuple (a, b) |
| Tuple unpacking | `x, y = func()` | Unpacks tuple into 2 variables |
| **kwargs | `**context` | All keyword args as dictionary |
| Generic types | `List[Dict[str, Any]]` | List of dictionaries |

---

## Next Steps

1. **Try reading** the functions one at a time
2. **Trace the flow** - follow function calls
3. **Ignore type hints** if they're confusing (they're optional)
4. **Focus on** what each function returns and how it's used

The logic is: **functions call other functions, pass data between them, and return results**.
