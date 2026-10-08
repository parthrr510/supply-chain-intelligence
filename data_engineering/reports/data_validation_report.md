# End-to-End Data Validation Report

## Overview
This report validates the end-to-end curated data pipeline from raw files through Data Quality (DQ) checks, quarantine/cleaning, and loading into DuckDB. 

## Final Observed DQ Findings & Quarantines
During execution, the following data anomalies were identified by the DQ framework. Affected rows were quarantined where necessary to preserve curated data integrity:

| Check Name | Dataset | Rows Affected | Action |
| ---------- | ------- | ------------- | ------ |
| Exact Duplicates | shipments | 16 | Dropped |
| Conflicting Duplicates | shipments | 40 | Quarantined |
| Invalid Origin Port | shipments | 42 | Quarantined |
| Invalid Destination Port | shipments | 55 | Quarantined |
| Negative Weight | shipments | 36 | Quarantined |
| Missing Status | shipments | 54 | Reported |
| Missing Event Type | port_events | 140 | Quarantined |

## Cleaning actions performed
- Whitespace and case formatting were normalized on all string columns.
- Standardized known status aliases (e.g., "COMPLETED" mapped to "DELIVERED").
- Exact duplicate rows were safely dropped without entering the database.

## Curated Row Counts
After applying the deterministic ingestion process, the curated state in DuckDB represents the clean schema:

| Table | Row Count |
| ----- | --------- |
| ports | 25 |
| shipments | 4,852 |
| port_events | 24,656 |

## Schema Validation
- **Keys**: Verified Primary Keys `port_code`, `shipment_id`, and `event_id`. `shipment_id` is excluded from the `port_events` schema directly, resolving a mismatch between data provided and intended relationships.
- **Derived Fields**: Successfully generated `actual_delay_hours`, `on_time_flag` (boolean mapped safely off >24hr requirement logic), `route_key`, `transit_days_planned`, and `transit_days_actual`.
- **Determinism**: Verified idempotent execution. Rerunning `pipeline.ingest` cleanly rebuilds without duplicate aggregation. 

## Data Limitations
- 140 events lacked an event type and required quarantining.
- Shipments lacking valid port matching in the reference dataset (97 shipments combined for origin/destination) limit absolute analytic size. 
- Early arrivals produce negative delay hours (e.g. -24), which is valid business context rather than a DQ error.
