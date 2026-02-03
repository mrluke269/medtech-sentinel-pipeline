# Learning Path: Understanding MedTech Sentinel Pipeline

## 🎯 Phase 1: Understand the "Why" (30 minutes)

### Step 1: Read the Business Context
**File:** `README.md`

**Focus on:**
- What problem does this solve? (Post-market surveillance for medical devices)
- Who uses it? (Quality engineers, regulatory teams)
- What's the business value? (Safety trend detection, manufacturer comparison)

**Key Questions to Answer:**
- Why automate this instead of manual analysis?
- Why weekly extraction? (FDA data updates, trend detection needs)
- Why these two device types? (Different risk classes - Class II vs Class III)

---

## 🏗️ Phase 2: Understand the Architecture (45 minutes)

### Step 2: Visualize the Data Flow
**Files:** 
- `images/architechture.png`
- `images/tech_stack.png`
- `README.md` (Architecture section)

**Conceptual Understanding:**
```
API → S3 → Snowflake → dbt → Power BI
```

**Why this architecture?**
- **S3 as staging**: Durable storage, audit trail, decouples extraction from loading
- **Snowflake as warehouse**: Handles JSON natively, scales compute separately from storage
- **dbt for transformations**: Version-controlled SQL, testing, documentation
- **Airflow for orchestration**: Handles retries, scheduling, dependencies

**Think of it like a factory assembly line:**
- **Extract** = Raw materials arrive (API calls)
- **Load** = Materials stored in warehouse (S3) then moved to factory floor (Snowflake)
- **Transform** = Assembly line processes materials (dbt models)
- **Visualize** = Finished products displayed (Power BI)

---

## 🔄 Phase 3: Follow the Data Flow (1-2 hours)

### Step 3: Start with Extraction (The Entry Point)
**File:** `airflow/dags/extract_fda_events.py`

**Read in this order:**
1. **Lines 194-200**: DAG definition - understand the schedule and structure
2. **Lines 211-230**: Task creation - see how tasks are chained together
3. **Lines 17-129**: `extract_and_save()` function - the extraction logic
4. **Lines 131-193**: `load_to_snowflake()` function - the loading logic

**Key Concepts to Understand:**
- **Why pagination?** (API limit is 1000 records, need multiple requests)
- **Why S3 first?** (Idempotency - can reload if Snowflake fails)
- **Why XCom?** (Pass file path between tasks)
- **Why idempotent delete?** (Can re-run without duplicates)

**Questions to Answer:**
- What happens if the API returns 404? (Skip this run - see line 46-52)
- How does the pipeline handle failures? (Retries with exponential backoff)
- Why two product codes? (Different device types, parallel processing)

### Step 4: Understand the Data Model
**Files:**
- `images/model_2.png` (visual overview)
- `airflow/dbt/models/marts/schema.yml` (data dictionary)

**Key Pattern: Star Schema**
```
Fact Table (fct_adverse_events)
    ↓
    ├── dim_dates (when did it happen?)
    ├── dim_devices (what device?)
    ├── dim_manufacturers (who made it?)
    └── dim_event_types (what type of event?)
```

**Why Star Schema?**
- **Fast queries**: Pre-joined dimensions, denormalized for analytics
- **Business-friendly**: Matches how analysts think (events by date, device, manufacturer)
- **Flexible**: Easy to add new dimensions without changing fact table

---

## 🧹 Phase 4: Understand Data Transformation Layers (2-3 hours)

### Step 5: Staging Layer (Data Cleaning)
**File:** `airflow/dbt/models/STAGE/stg_adverse_events.sql`

**Read with focus on:**
- **Lines 10-14**: How raw JSON is parsed (Snowflake's `::` casting syntax)
- **Lines 18-45**: Brand name standardization (WHY? Data quality - same device, different spellings)
- **Lines 54-70**: Manufacturer name standardization (WHY? Same company, different formats)
- **Lines 78-79**: Array flattening (WHY? Arrays are hard to query, strings are easier)

**Key Pattern: "Clean Once, Use Many Times"**
- All cleaning happens in staging
- Downstream models trust staging is clean
- Single source of truth for business rules

**Questions:**
- Why use `CASE WHEN` for standardization? (Business logic - "PERIMOUNT" = "Carpentier-Edwards Perimount")
- Why `coalesce()` everywhere? (Handle NULLs consistently)
- Why materialize as VIEW? (Always fresh, no storage cost, but slower queries)

### Step 6: Dimensional Models (Reference Data)
**Files:**
- `airflow/dbt/models/marts/dim_dates.sql`
- `airflow/dbt/models/marts/dim_devices.sql`
- `airflow/dbt/models/marts/dim_manufacturers.sql`
- `airflow/dbt/models/marts/dim_event_types.sql`

**Read one dimension at a time:**

**dim_dates.sql:**
- **Why a date dimension?** (Pre-calculated date attributes, consistent date handling)
- **Why YYYYMMDD as key?** (Numeric, sortable, human-readable)

**dim_devices.sql:**
- **Why MD5 hash for key?** (Deterministic - same device = same key, even if loaded multiple times)
- **Why GROUP BY?** (Deduplicate - one device might appear in many events)

**dim_manufacturers.sql:**
- **Why separate from devices?** (Normalization - one manufacturer makes many devices)
- **Why materialize as TABLE?** (Changes rarely, faster queries)

**Key Pattern: Surrogate Keys**
- Natural keys (manufacturer name) can change or have duplicates
- Surrogate keys (MD5 hash) are stable and unique
- Enables historical tracking (what if manufacturer name changes?)

### Step 7: Fact Table (Events)
**File:** `airflow/dbt/models/marts/fct_adverse_events.sql`

**Key Concepts:**
- **Lines 2-4**: Incremental materialization (WHY? Only process new data, faster runs)
- **Lines 26-33**: Joins to dimensions (creates the "star")
- **Lines 49-51**: Incremental logic (only load records newer than last run)

**Why Incremental?**
- Full refresh would reprocess 6,557+ events every week
- Incremental only processes new events (maybe 50-100 per week)
- 10-100x faster, lower compute costs

**Questions:**
- What's the grain? (One row per adverse event report)
- Why foreign keys to dimensions? (Enables filtering/grouping in Power BI)
- Why keep `patient_problems` and `product_problems` as strings? (Power BI can parse, but Snowflake can't easily query arrays)

### Step 8: Analytical Marts (Business Questions)
**Files:** 
- `airflow/dbt/models/marts/death_*.sql`
- `airflow/dbt/models/marts/injury_*.sql`

**Pattern: "Exploded → Categorized → Root Cause"**

**Example: `death_product_problems_exploded.sql`**
- Takes comma-separated string: `"stenosis, calcification"`
- Splits into rows: one row per problem
- WHY? Enables counting (how many events had "stenosis"?)

**Example: `death_product_problems_category.sql`**
- Groups problems into categories: "Hemodynamic/Functional", "Structural Failure"
- WHY? Business-friendly groupings for dashboard filters

**Key Pattern: "Pre-aggregate for Dashboards"**
- Dashboards query these marts, not the fact table
- Faster queries, simpler DAX formulas
- Trade-off: More storage, but worth it for user experience

---

## 🧪 Phase 5: Understand Quality & Testing (30 minutes)

### Step 9: Data Quality
**File:** `airflow/dbt/models/marts/schema.yml`

**Read to understand:**
- **not_null tests**: Critical fields must have values
- **unique tests**: Keys must be unique (data integrity)
- **relationships tests**: Foreign keys must exist in dimension (referential integrity)
- **accepted_values tests**: Enums must match expected values

**Why Test?**
- Catch data quality issues early
- Document expectations (self-documenting code)
- Prevent bad data from reaching dashboards

**See it in action:**
- Line 10-11: `date_key` must be unique and not null
- Line 154-156: `date_key` must exist in `dim_dates` (referential integrity)

---

## 🎨 Phase 6: Understand the End User Experience (30 minutes)

### Step 10: Dashboard Structure
**Files:**
- `dashboard/*.png` (screenshots)
- `README.md` (Dashboard section)

**Understand the user journey:**
1. **Overview**: High-level KPIs (total events, trends)
2. **Death Events**: Focused analysis on most severe events
3. **Injury Events**: Focused analysis on common events

**Each event type has 3 views:**
- **Analysis**: Distribution by brand/manufacturer
- **Products Analysis**: What failed on the device?
- **Patient Analysis**: What happened to the patient?

**Why this structure?**
- Separates product problems (engineering concern) from patient problems (clinical concern)
- Enables different teams to focus on their domain
- Interactive filters allow drill-down analysis

---

## 🔧 Phase 7: Understand Infrastructure (1 hour)

### Step 11: Containerization
**Files:**
- `airflow/Dockerfile`
- `airflow/docker-compose.yaml`

**Dockerfile:**
- **Why custom image?** (Need dbt installed in Airflow container)
- **Why specific versions?** (Reproducibility, avoid breaking changes)

**docker-compose.yaml:**
- **Why multiple services?** (Separation of concerns - webserver, scheduler, database)
- **Why volume mounts?** (Code changes reflect immediately, no rebuild)
- **Why health checks?** (Services wait for dependencies to be ready)

**Key Concept: "Infrastructure as Code"**
- Reproducible environment
- Easy to deploy to AWS EC2
- Version-controlled infrastructure

### Step 12: Configuration
**Files:**
- `airflow/dbt/dbt_project.yml`
- `airflow/dbt/models/STAGE/_src_medtech.yml`

**dbt_project.yml:**
- **Why materialization strategies?** (Views for staging = always fresh, Tables for marts = faster queries)
- **Why profile configuration?** (Separate dev/prod environments)

**_src_medtech.yml:**
- **Why source definitions?** (Abstracts database/schema names, enables lineage tracking)

---

## 🎓 Phase 8: Deep Dive - Pick Your Interest (2-4 hours)

### Option A: Understand API Integration
**Files:**
- `documents/fda-api-reference.md`
- `documents/functions/extract_function.md`
- `airflow/dags/extract_fda_events.py` (extract_and_save function)

**Focus on:**
- Pagination patterns
- Error handling strategies
- Rate limiting considerations

### Option B: Understand dbt Patterns
**Files:**
- All files in `airflow/dbt/models/`
- `airflow/dbt/models/marts/schema.yml`

**Focus on:**
- Staging → Dimensions → Facts → Marts pattern
- Incremental materialization logic
- Testing strategies

### Option C: Understand Airflow Orchestration
**File:**
- `airflow/dags/extract_fda_events.py`

**Focus on:**
- Task dependencies (why `extract >> load >> transform >> test`?)
- XCom usage (passing data between tasks)
- Retry logic and error handling
- Dynamic task generation (why loop over product codes?)

---

## ✅ Phase 9: Validate Understanding (1 hour)

### Exercises to Test Your Knowledge:

1. **Trace a single event through the pipeline:**
   - How does one adverse event go from API → S3 → Snowflake → dbt → Power BI?

2. **Explain the data model:**
   - Why is `fct_adverse_events` the center of the star?
   - What happens if a manufacturer name changes? (How does surrogate key help?)

3. **Understand incremental loading:**
   - What happens on the second weekly run?
   - Why doesn't it duplicate data?

4. **Explain error handling:**
   - What happens if the API is down?
   - What happens if Snowflake COPY fails?
   - What happens if dbt transformation fails?

5. **Understand the business logic:**
   - Why standardize brand names? (Give an example)
   - Why separate product problems from patient problems?

---

## 🚀 Next Steps

Once you understand the structure:

1. **Run it locally:**
   - Follow `documents/setup/Docker-setup.md`
   - See the pipeline execute in real-time

2. **Modify it:**
   - Add a new dimension (e.g., `dim_reporters`)
   - Add a new analytical mart (e.g., `malfunction_events_analysis`)
   - Add a new product code (e.g., pacemakers)

3. **Extend it:**
   - Add data quality alerts (email on test failures)
   - Add data freshness monitoring
   - Add automated report generation

---

## 📚 Key Data Engineering Concepts Used

- **ELT vs ETL**: Extract → Load → Transform (transform in warehouse, not in memory)
- **Star Schema**: Fact table + dimension tables (classic data warehouse pattern)
- **Incremental Loading**: Only process new/changed data (performance optimization)
- **Idempotency**: Can re-run safely without side effects (critical for reliability)
- **Separation of Concerns**: Staging (clean) → Dimensions (reference) → Facts (events) → Marts (analytics)
- **Infrastructure as Code**: Docker/Compose files version-controlled with code
- **Data Quality Testing**: Catch issues before they reach users

---

## 💡 Pro Tips

1. **Start with the README** - It's your map
2. **Follow the data flow** - One event, start to finish
3. **Read code with questions** - Don't just read, ask "why?"
4. **Compare patterns** - How are dimensions similar? How are they different?
5. **Use the documentation** - The `documents/` folder has detailed explanations
6. **Look at the tests** - `schema.yml` documents what "good data" looks like

---

## 🎯 Success Criteria

You understand this project when you can:
- ✅ Explain the data flow from API to dashboard
- ✅ Understand why each layer exists (staging, dimensions, facts, marts)
- ✅ Explain the star schema design
- ✅ Understand incremental loading logic
- ✅ Trace how one event moves through the pipeline
- ✅ Explain error handling and retry logic
- ✅ Understand the business value of each component
