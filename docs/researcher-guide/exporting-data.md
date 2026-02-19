# Exporting Data

This guide explains how to export AugMed research data for analysis, describes the output CSV format, and documents the column definitions.

## Export Methods

### Method 1: Export Script (Current Primary Method)

The `export_answers_to_csv.py` script is the primary data export tool. It queries the database directly and produces a structured CSV file with one row per participant-case combination.

**Location:** `script/answer_export/export_answers_to_csv.py`

**Setup:**

```bash
# Install dependencies
pip install pandas sqlalchemy psycopg2-binary

# Set database credentials (or use environment variables)
export POSTGRES_HOST=your-db-host
export POSTGRES_USER=augmed
export POSTGRES_PASSWORD=your-password
export POSTGRES_DB=augmed
```

**Basic export:**

```bash
cd script/answer_export
python export_answers_to_csv.py
```

Produces a file named `answers_data_YYYYMMDD_HHMMSS.csv` in the current directory.

**With validation:**

```bash
python export_answers_to_csv.py --validate
```

Runs consistency checks on medical/family history values for patients who appear in multiple records. Logs warnings if inconsistencies are found.

**Options:**

| Flag | Description |
|------|-------------|
| *(none)* | Standard export |
| `--validate` | Include data consistency validation |
| `--analyze` | Extended analysis mode (not yet fully implemented) |
| `--test-mode` | Run with sample data, no database required |
| `--log-level DEBUG` | Verbose logging for troubleshooting |

### Method 2: Recruitment Survey Integration

The export script automatically joins with a recruitment survey CSV if it is present in the same directory. The survey file must be named:

```
recruitment_survey_data - Augmed_recruit_alldoc_new.csv
```

This file is a Qualtrics export. The script maps Qualtrics column codes to descriptive names:

| Qualtrics Column | Output Column |
|-----------------|---------------|
| Q3 | email |
| Q22 | professional_role |
| Q22_7_TEXT | professional_role_other |
| Q4 | practice_years |
| Q5 | practice_state |
| Q6 | experience_screening |
| Q7 | years_screening |

If the recruitment survey file is not present, those columns will be empty in the output.

## Output CSV Format

The export CSV has one row per participant-case submission. Rows are sorted by `person_id`.

### Column Groups

#### Identifier Columns

| Column | Type | Description |
|--------|------|-------------|
| `person_id` | integer | OMOP patient identifier |
| `user_id` | integer | Stable anonymized participant identifier (SHA-256 hash of email) |
| `order_id` | integer | Sequential case number for this participant (1 = first case reviewed) |

!!! note
    `user_email` is intentionally not included in the export to protect participant privacy. `user_id` is a stable, consistent identifier that can be used for longitudinal analysis without exposing email addresses.

#### Analytics Timing Columns

| Column | Type | Description |
|--------|------|-------------|
| `case_open_time` | datetime (UTC) | Timestamp when participant opened the case |
| `answer_open_time` | datetime (UTC) | Timestamp when participant opened the answer form |
| `answer_submit_time` | datetime (UTC) | Timestamp when participant submitted answers |
| `to_answer_open_secs` | float | Seconds from case open to answer form open (case review time) |
| `to_submit_secs` | float | Seconds from answer form open to submission (answer time) |
| `total_duration_secs` | float | Total seconds from case open to submission |

!!! note
    Timing data comes from the `analytics` table. If a participant's timing was not recorded (older data or recording failures), these columns will be empty.

#### Demographic Columns

| Column | Type | Description |
|--------|------|-------------|
| `age` | integer | Patient age at time of visit (visit year minus birth year) |
| `gender` | string | Patient gender (from OMOP concept name, e.g., "MALE", "FEMALE") |

#### Clinical Feature Columns (Shown Flags)

One column per clinical feature in your study's configuration, indicating whether the feature was visible to the participant. Column names follow the pattern `{Category}.{Feature} (shown)`:

| Column Pattern | Values | Description |
|--------|--------|-------------|
| `Family History.{Feature} (shown)` | True/False | Was this family history feature shown? |
| `Medical History.{Feature} (shown)` | True/False | Was this medical history feature shown? |
| `Social History.{Feature} (shown)` | True/False | Was this social history feature shown? |

The specific feature columns depend on your study's page configuration.

#### AI Score Column (Shown Flag)

| Column | Values | Description |
|--------|--------|-------------|
| `ai_score (shown)` | Yes/No | Whether the AI prediction was shown to the participant |

#### Feature Value Columns

Parallel to each `(shown)` column, there is a corresponding `(value)` column with the patient's actual clinical value:

| Column Pattern | Values | Description |
|--------|--------|-------------|
| `{Category}.{Feature} (value)` | Yes/No | Patient's actual clinical value for this feature |
| `ai_score (value)` | integer or empty | Numeric AI prediction score |

!!! note
    Value columns contain the patient's ground truth value regardless of whether the feature was shown to the participant. A participant may not have seen a feature (shown = False) but the patient's actual value is still recorded. This allows researchers to analyze how unseen information relates to outcomes.

#### Outcome Columns (Participant Responses)

Outcome columns are derived from your answer config (questionnaire). The export script normalizes raw questionnaire responses into structured columns. The specific columns depend on your study design.

| Column Pattern | Type | Description |
|--------|------|-------------|
| *(study-specific)* | varies | Normalized response values from your questionnaire |
| `additional_info` | string | Free-text response (if included in your questionnaire) |

!!! example
    The CRC study exported `risk_assessment` (1-5 scale), `confidence_level` (1-3), and `screening_recommendation` (categorical). See [CRC Experiment Config](../examples/crc-screening/experiment-config.md).

#### Recruitment Survey Columns (Optional)

If a recruitment survey CSV is present, these columns are joined automatically:

| Column | Description |
|--------|-------------|
| `professional_role` | Participant's clinical role |
| `professional_role_other` | Free-text if "Other" was selected |
| `practice_years` | Years in clinical practice |
| `practice_state` | State where participant practices |
| *(study-specific)* | Additional survey fields |

## Example CSV Row

```
person_id,user_id,order_id,case_open_time,answer_open_time,answer_submit_time,to_answer_open_secs,to_submit_secs,total_duration_secs,age,gender,{Feature}.{Name} (shown),...,ai_score (shown),ai_score (value),...
1001,8472938475827364,3,2024-10-15T14:23:01.000Z,2024-10-15T14:25:47.000Z,2024-10-15T14:28:33.000Z,166.0,166.0,332.0,58,MALE,True,...,Yes,12,...
```

## Method 3: Export API (Recommended)

The Export API provides programmatic access to all research data without requiring direct database access. It supports both JSON and CSV response formats.

**Authentication:** Either an API key (`X-API-Key` header) or a JWT token (`Authorization: Bearer` header).

### Available Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/export/answers` | Answer data with demographics, AI scores, and timing |
| `GET /api/v1/export/analytics` | Timing analytics |
| `GET /api/v1/export/participants` | Anonymized participant metadata with completion stats |
| `GET /api/v1/export/display-configs` | Current case assignments |

### Query Parameters

All endpoints support:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 1000 | Max rows to return (up to 10,000) |
| `offset` | integer | 0 | Skip this many rows (for pagination) |
| `since` | ISO 8601 | — | Only return records created after this timestamp (answers and analytics only) |

### Response Format

Set the `Accept` header to control output format:

- `Accept: application/json` (default) — JSON response
- `Accept: text/csv` — CSV download

### Examples

**Export answers as CSV:**

```bash
curl "https://augmed.dhep.org/api/v1/export/answers?since=2025-01-01" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Accept: text/csv" \
  -o answers.csv
```

**Export answers as JSON with pagination:**

```bash
curl "https://augmed.dhep.org/api/v1/export/answers?limit=500&offset=0" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Export using JWT (from admin panel session):**

```bash
curl "https://augmed.dhep.org/api/v1/export/participants" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Paginate through all records:**

```bash
# First page
curl "https://augmed.dhep.org/api/v1/export/answers?limit=1000&offset=0" ...
# Second page
curl "https://augmed.dhep.org/api/v1/export/answers?limit=1000&offset=1000" ...
# Continue until has_more is false
```

## Related Documentation

- [Analyzing Results](analyzing-results.md) — R and Python examples for working with the export
- [Data Dictionary](../reference/data-dictionary.md) — Full database schema
- [Monitoring Progress](monitoring-progress.md) — Check completion before exporting
