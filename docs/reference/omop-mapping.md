# OMOP Mapping

This document explains how OMOP concept IDs and clinical data in the database are mapped to what participants see on the case review page.

## Overview

Patient clinical data is stored in OMOP CDM format, where clinical entities are identified by integer concept IDs rather than text descriptions. When a participant opens a case, the API:

1. Reads the participant's `display_config` to determine which clinical sections to show
2. Queries OMOP tables for the relevant data
3. Resolves concept IDs to human-readable names via the `concept` table
4. Applies the path config to filter, structure, and style the data
5. Returns a hierarchical JSON tree for the frontend to render

## The Page Configuration

The `system_config` table entry with `id = 'page_config'` defines the mapping between the three UI sections and their corresponding OMOP concept IDs.

Example page config (abbreviated):

```json
{
  "BACKGROUND": {
    "Family History": [4167217],
    "Social History": {
      "Smoke": [4041306],
      "Alcohol": [4029833]
    },
    "Medical History": [1008364],
    "AI Predictions": [your_ai_concept_id]
  },
  "PATIENT COMPLAINT": {
    "Chief Complaint": [38000282, 38000283]
  },
  "PHYSICAL EXAMINATION": {
    "Abdominal": [4152368],
    "Body measure": [3013762, 40490382]
  }
}
```

> **Example:** The CRC screening study used `"CRC risk assessments": [45614722]`. See [CRC Terminology](../examples/crc-screening/terminology.md) for all CRC-specific concept mappings.

Each key under a section maps to a list of `observation_concept_id` or `measurement_concept_id` values used to query the clinical data tables.

## How Each Section Is Built

### BACKGROUND Section

**Patient Demographics** (always shown, always first):

The API retrieves:
- `person.year_of_birth` and `visit_occurrence.visit_start_date` → computes age at visit
- `person.gender_concept_id` → resolved to "MALE" or "FEMALE" via the `concept` table

**Family History, Medical History, Social History:**

These subsections are built by querying the `observation` table:

```sql
SELECT observation_concept_id, value_as_string, value_as_number, value_as_concept_id,
       unit_concept_id, qualifier_concept_id, unit_source_value
FROM observation
WHERE visit_occurrence_id = :case_id
  AND observation_concept_id IN (:concept_id_list)
```

- Multiple observations with the same concept ID are grouped and displayed as a list
- `value_as_string` → displayed directly as text
- `value_as_number` → converted to string
- `value_as_concept_id` → resolved to concept name via `concept` table
- `qualifier_concept_id` → prepended to the value (e.g., "Yes : Fatigue")
- `unit_concept_id` → appended to the value

**AI Predictions (AI Score):**

Special handling for the AI prediction concept ID (configured in your page config):

```sql
SELECT value_as_string, value_as_number
FROM observation
WHERE visit_occurrence_id = :case_id
  AND observation_concept_id = :your_ai_concept_id
ORDER BY observation_datetime DESC
LIMIT 1
```

The AI score format depends on your study configuration. The API reads `value_as_string` and displays it with a "Predicted" prefix.

Alternatively, the score can be provided directly in the display config CSV path:

```
RISK ASSESSMENT.{Score Label}: {numeric_value}
```

When a literal score is in the CSV, it takes precedence over the database value.

> **Example:** The CRC study stored scores as `"Colorectal Cancer Score: {value}"` using concept ID `45614722`. See [CRC Terminology](../examples/crc-screening/terminology.md).

### PATIENT COMPLAINT Section

Built from `observation` table using concept IDs mapped to the "Chief Complaint" category. The API groups observations by `observation_concept_id` and resolves each to a concept name, producing a list of chief complaint labels.

### PHYSICAL EXAMINATION Section

Built from the `measurement` table:

```sql
SELECT measurement_concept_id, value_as_number, value_as_concept_id,
       unit_concept_id, operator_concept_id, unit_source_value
FROM measurement
WHERE visit_occurrence_id = :case_id
  AND measurement_concept_id IN (:concept_id_list)
```

Value extraction follows the same priority as observations:
1. `value_as_number` (with unit appended if available)
2. `value_as_concept_id` → resolved concept name
3. `unit_source_value`

**BMI Special Handling:**

Measurement concept ID `40490382` (BMI) stores a numeric percentile. The API converts this to a categorical label:

| Numeric value | Display label |
|--------------|---------------|
| 18 | Underweight |
| 22 | Normal |
| 27 | Overweight |
| 30 | Obese |

BMI is only shown if explicitly included in the path config:
```
PHYSICAL EXAMINATION.Body measure.BMI (body mass index) range
```

## How the Display Config Filters the Data

After building the full data tree, the API applies the display config to prune it:

1. **BACKGROUND subsections:** Only subsections listed in the path config are shown. Each row in the path config specifying `BACKGROUND.{Category}.{Feature}: {Value}` keeps that feature visible for that category. Categories not in the path config have their values cleared (shown as empty).

2. **PHYSICAL EXAMINATION:** If any `PHYSICAL EXAMINATION` paths are in the config, only those specified findings are shown. If no physical exam paths are present, all findings are shown (except BMI).

3. **PATIENT COMPLAINT:** Always shown in full (not filtered by display config).

4. **AI Score:** Only shown if the corresponding `RISK ASSESSMENT.*` path is in the path config.

## Key Concept IDs

| Concept ID | Domain | Used As | Display |
|-----------|--------|---------|---------|
| 4167217 | Observation | Family history observation type | Groups family history entries |
| 1008364 | Observation | Medical history observation type | Groups medical history entries |
| 38000282 | Observation | Chief complaint type | Chief complaint label |
| 4152368 | Measurement | Abdominal exam | Physical examination |
| 3013762 | Measurement | Body weight | Physical examination |
| 40490382 | Measurement | BMI percentile | Converted to categorical range |
| 4041306 | Observation | Smoking history | Social history |
| 8507 | — | Male gender | Resolved from `person.gender_concept_id` |
| 8532 | — | Female gender | Resolved from `person.gender_concept_id` |

> **Note:** The concept IDs above are common clinical concepts. AI prediction concept IDs are study-specific and configured in the page config. See [CRC Terminology](../examples/crc-screening/terminology.md) for the concept IDs used in the CRC screening study.

## Loading OMOP Data

To load OMOP data into the database, the `script/sample_data/` directory contains sample CSV files and the `src/load_omop.sh` script.

For production data from a real EHR:

1. Export data from your source EHR system into OMOP CDM format
2. Verify concept IDs are standard OMOP vocabulary codes
3. Import using PostgreSQL `COPY` or `psql` commands
4. Load the OMOP vocabulary (concept table) from Athena: [athena.ohdsi.org](https://athena.ohdsi.org)
5. Update the `system_config.page_config` to include the relevant concept IDs for your clinical features

## Querying Clinical Data

To explore what concept IDs are available in your data:

```sql
-- Most common observation concept IDs
SELECT
    o.observation_concept_id,
    c.concept_name,
    COUNT(*) AS occurrence_count
FROM observation o
JOIN concept c ON c.concept_id = o.observation_concept_id
GROUP BY o.observation_concept_id, c.concept_name
ORDER BY occurrence_count DESC
LIMIT 50;

-- Check observations for a specific case
SELECT
    c.concept_name,
    o.value_as_string,
    o.value_as_number,
    o.observation_datetime
FROM observation o
JOIN concept c ON c.concept_id = o.observation_concept_id
WHERE o.visit_occurrence_id = :case_id
ORDER BY o.observation_datetime;
```

## Related Documentation

- [Data Dictionary](data-dictionary.md) — Full OMOP table column descriptions
- [Config CSV Format](config-csv-format.md) — How paths reference OMOP data
- [Database](../admin-guide/database.md) — Schema overview
- [OMOP CDM Documentation](https://ohdsi.github.io/CommonDataModel/) — Official OMOP CDM reference
