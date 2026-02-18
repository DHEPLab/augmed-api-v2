# Creating Experiments

This guide walks through the complete process of setting up an experiment: defining your arms, building display config CSV files, and uploading them to the platform.

## Overview

Creating an experiment in AugMed requires four things:

1. **Cases in the database** — OMOP-formatted clinical records (loaded by the data team)
2. **An answer config** — the questionnaire all participants will complete (uploaded once)
3. **A participant roster** — user accounts for each clinician participant
4. **A display config CSV** — the mapping of participants to cases and feature visibility

The display config CSV is the primary tool researchers use to implement their experimental design. Each row specifies one clinical feature to show to one participant for one case. The collection of rows for a given participant-case pair defines that participant's complete information set for that case.

## Step 1: Define Your Experimental Arms

Before creating any files, decide on your experimental design. Common designs for CRC screening studies:

**Two-arm design (AI vs. no AI):**
- Arm A: participants see clinical history + AI risk score
- Arm B: participants see clinical history only

**Four-arm design (feature variation):**
- Arm A: full history + AI score
- Arm B: full history, no AI score
- Arm C: limited history + AI score
- Arm D: limited history, no AI score

Write down exactly which BACKGROUND features each arm shows. The available background feature categories are:

- `Family History` — with features: Cancer, Colorectal Cancer, Diabetes, Hypertension
- `Medical History` — with features: Abdominal Pain/Distension, Anxiety and/or Depression, Asthma, Blood Stained Stool, Chronic Diarrhea, Constipation, Diabetes, Fatigue, Headache, Hyperlipidemia, Hypertension, Hypothyroidism, Irritable Bowel Syndrome, Migraines, Osteoarthritis, Rectal Bleeding, Shortness of Breath, Tenderness Abdomen

**Note:** Patient Demographics (age and gender) are always shown and cannot be suppressed.

## Step 2: Determine Case Assignments

Decide which cases each participant reviews. Common approaches:

- **Between-subjects**: each participant reviews a different set of cases, with cases evenly distributed across arms
- **Within-subjects**: each participant reviews cases from multiple arms (some cases with AI, some without)
- **Repeated cases**: multiple participants review the same cases (required for inter-rater reliability analysis)

Keep track of case IDs (visit_occurrence_ids) in the database. Ask your data team for the full list of available case IDs.

## Step 3: Build the Display Config CSV

The CSV has six columns:

```
User,Case No.,Path,Collapse,Highlight,Top
```

| Column | Required | Description |
|--------|----------|-------------|
| `User` | Yes | Participant's email address (must match their account) |
| `Case No.` | Yes | The case ID (visit_occurrence_id, integer) |
| `Path` | Yes | The clinical feature path to show (see path syntax below) |
| `Collapse` | Optional | `TRUE` to collapse this section by default, `FALSE` or blank |
| `Highlight` | Optional | `TRUE` to visually highlight this item, `FALSE` or blank |
| `Top` | Optional | Pin this item to the key findings panel; lower number = higher priority |

### Path Syntax

Paths identify clinical features using dot-separated segments:

**Background feature (specific value)**:
```
BACKGROUND.{Category}.{Feature}: {Value}
```
Example: `BACKGROUND.Medical History.Fatigue: Yes`

The `: Yes` or `: No` at the end specifies the patient's actual value for that feature. This value is stored and later exported — it is not filtered by the path; it is the ground truth value you are surfacing to the participant.

**AI score section**:
```
RISK ASSESSMENT.CRC risk assessments
```
Including this path shows the AI-generated CRC risk score for the patient.

**Physical examination items**:
```
PHYSICAL EXAMINATION.{Section}.{Finding}
```
Example: `PHYSICAL EXAMINATION.Abdominal.Tenderness`

### Building Rows for One Participant-Case Pair

For each participant-case combination, add one row per feature you want to show. All rows for the same participant-case pair must have the same `User` and `Case No.` values.

Example — showing selected features for participant `alice@example.com`, case 12, in the "AI shown" arm:

```csv
User,Case No.,Path,Collapse,Highlight,Top
alice@example.com,12,BACKGROUND.Family History.Colorectal Cancer: No,FALSE,TRUE,
alice@example.com,12,BACKGROUND.Family History.Cancer: No,FALSE,TRUE,
alice@example.com,12,BACKGROUND.Medical History.Fatigue: Yes,FALSE,TRUE,
alice@example.com,12,BACKGROUND.Medical History.Rectal Bleeding: No,FALSE,TRUE,
alice@example.com,12,BACKGROUND.Medical History.Blood Stained Stool: No,FALSE,TRUE,
alice@example.com,12,RISK ASSESSMENT.CRC risk assessments,FALSE,TRUE,
```

The same participant with case 13 in the "no AI" arm:

```csv
alice@example.com,13,BACKGROUND.Family History.Colorectal Cancer: No,FALSE,TRUE,
alice@example.com,13,BACKGROUND.Family History.Cancer: No,FALSE,TRUE,
alice@example.com,13,BACKGROUND.Medical History.Fatigue: No,FALSE,TRUE,
alice@example.com,13,BACKGROUND.Medical History.Rectal Bleeding: Yes,FALSE,TRUE,
alice@example.com,13,BACKGROUND.Medical History.Blood Stained Stool: No,FALSE,TRUE,
```

Note that the "no AI" case simply omits the `RISK ASSESSMENT.CRC risk assessments` row.

### Generating the CSV Programmatically

For large experiments (many participants, many cases), generating the CSV by hand is impractical. The `script/assign_cases/` directory contains shell scripts used in past rounds:

```bash
script/assign_cases/generate_config.sh
script/assign_cases/generate_round3_test_config.sh
```

Review these scripts as starting points. They demonstrate how to generate assignment rows programmatically.

For Python-based generation:

```python
import csv
import itertools

participants = ["alice@example.com", "bob@example.com"]
cases_arm_a = [1, 3, 5, 7]   # AI shown
cases_arm_b = [2, 4, 6, 8]   # No AI

features = [
    ("Family History", "Colorectal Cancer", None),   # value from DB
    ("Family History", "Cancer", None),
    ("Medical History", "Fatigue", None),
    ("Medical History", "Rectal Bleeding", None),
]

rows = []
for user in participants:
    for case_id in cases_arm_a:
        for category, feature, value in features:
            # value should come from your case database extract
            path = f"BACKGROUND.{category}.{feature}: Yes"  # placeholder
            rows.append([user, case_id, path, "FALSE", "TRUE", ""])
        # Add AI score row
        rows.append([user, case_id, "RISK ASSESSMENT.CRC risk assessments", "FALSE", "TRUE", ""])

    for case_id in cases_arm_b:
        for category, feature, value in features:
            path = f"BACKGROUND.{category}.{feature}: No"  # placeholder
            rows.append([user, case_id, path, "FALSE", "TRUE", ""])
        # No AI score row for arm B

with open("experiment_config.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["User", "Case No.", "Path", "Collapse", "Highlight", "Top"])
    writer.writerows(rows)
```

> **Important:** The value in the path (e.g., `Fatigue: Yes`) must match the patient's actual clinical data. The display config does not transform the data — it selects which features the participant sees, and the value shown to the participant is drawn from the OMOP database. The `: Yes/No` in the path is metadata that gets stored in the answer record's `display_configuration` field, which enables the export script to reconstruct which features were shown and what their values were.

## Step 4: Upload the Display Config

Once your CSV is ready, upload it via the admin API:

```bash
curl -X POST https://your-augmed-server/admin/config/upload \
  -F "file=@experiment_config.csv"
```

> **Warning:** Uploading a new config **completely replaces all existing display configs**. All previous assignments are deleted. Run uploads carefully, and only after confirming participants have completed their assigned cases or their data has been exported.

Expected response:

```json
{
  "data": [
    {"user_case_key": "alice@example.com-1", "status": "added"},
    {"user_case_key": "alice@example.com-2", "status": "added"},
    ...
  ],
  "status": "success"
}
```

If any assignment fails (e.g., due to a database error), that entry will show `"status": "failed"`.

## Step 5: Verify the Upload

After uploading, confirm that participants see the correct cases. You can check by retrieving a user's case list:

1. Log in as the participant (or use a test account with their email)
2. Call `GET /api/cases` with a valid JWT — it returns the participant's current (next incomplete) case

Alternatively, query the database directly:

```sql
SELECT user_email, case_id, jsonb_array_length(path_config::jsonb) AS num_features
FROM display_config
WHERE user_email = 'alice@example.com'
ORDER BY case_id;
```

## Related Documentation

- [Config CSV Format](../reference/config-csv-format.md) — Full CSV specification with all path syntax options
- [Managing Participants](managing-participants.md) — How to create and activate user accounts
- [Monitoring Progress](monitoring-progress.md) — Track who has completed which cases
