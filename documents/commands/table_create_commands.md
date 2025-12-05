
```
create database raw;
use database raw;
create schema medtech_sentinel;
use schema medtech_sentinel;

CREATE TABLE raw_adverse_events (
    raw_data VARIANT,
    loaded_at TIMESTAMP,
    source_file VARCHAR
);
```
