# Config CSV Format

This document specifies the complete format for the display config CSV file used to assign cases to participants and control feature visibility.

## File Requirements

- **Format:** UTF-8 encoded CSV with comma delimiters
- **Extension:** Must be `.csv`
- **Headers:** Required in the first row, exactly as specified below
- **Upload endpoint:** `POST /admin/config/upload`
- **Effect of upload:** Replaces all existing display configs

> **Warning:** Uploading a new file deletes all current display configs before inserting the new ones. Ensure participants have completed their current assignments (or data has been exported) before uploading.

## Column Specification

```csv
User,Case No.,Path,Collapse,Highlight,Top
```

| Column | Required | Type | Description |
|--------|----------|------|-------------|
| `User` | Yes | string | Participant's email address |
| `Case No.` | Yes | integer | Case ID (`visit_occurrence_id`) |
| `Path` | Yes | string | Clinical feature path (see syntax below) |
| `Collapse` | No | TRUE/FALSE | Collapse this section by default |
| `Highlight` | No | TRUE/FALSE | Visually highlight this item |
| `Top` | No | float | Pin to key findings panel; lower = higher priority |

## One Row = One Feature for One Participant for One Case

Each row specifies a single clinical feature to show for one participant-case combination. To show multiple features, include multiple rows with the same `User` and `Case No.` values.

The system groups all rows with the same `(User, Case No.)` pair into a single `display_config` record. The `Path`, `Collapse`, `Highlight`, and `Top` values from each row become entries in the `path_config` JSON array.

## Path Syntax

The `Path` column uses a dot-separated hierarchical syntax matching the three clinical sections displayed in the UI.

### BACKGROUND Section

Background paths show clinical history features.

**Pattern:**
```
BACKGROUND.{Category}.{Feature}: {Value}
```

The `{Value}` at the end (after `: `) specifies the patient's actual clinical value — "Yes" if the condition is present, "No" if absent. This value is stored and exported, and appears in the display for the participant.

**Available Categories and Features:**

The specific categories and features depend on your study's page configuration (`page_config` in `system_config`). The general pattern is:

```
BACKGROUND.Patient Demographics        (always shown — cannot be controlled by path config)
BACKGROUND.{Category}.{Feature}: Yes/No
```

For example:
```
BACKGROUND.Family History.Condition A: Yes/No
BACKGROUND.Medical History.Symptom X: Yes/No
BACKGROUND.Social History.Risk Factor: Yes/No
```

> **Note:** The `{Value}` (Yes/No) must match the patient's actual clinical data in the OMOP database. If the value in the path does not match what is in the database, the feature may still be shown but the stored display configuration will reflect the path value, not the database value. Always derive values from your OMOP data extract.

> **Example:** The CRC screening study used 4 family history features, 18 medical history features, and 2 social history features. See [CRC Terminology](../examples/crc-screening/terminology.md) for the complete feature list.

### RISK ASSESSMENT Section

Shows the AI-generated prediction for the patient.

```
RISK ASSESSMENT.{Your AI Section Name}
```

No `: Yes/No` suffix. This is a toggle — including this path shows the AI score section; omitting it hides it. The section name must match a key in your `page_config`.

**Alternative format for providing the score directly in the CSV** (bypasses database lookup):

```
RISK ASSESSMENT.{Score Label}: {numeric_value}
```

Example: `RISK ASSESSMENT.Risk Score: 12`

When this form is used, the API displays the CSV-provided score rather than fetching it from the OMOP observation table.

> **Example:** The CRC study used `RISK ASSESSMENT.CRC risk assessments` and `RISK ASSESSMENT.Colorectal Cancer Score: {value}`. See [CRC Experiment Config](../examples/crc-screening/experiment-config.md).

### PHYSICAL EXAMINATION Section

Shows physical examination findings.

**Pattern:**
```
PHYSICAL EXAMINATION.{Section}.{Finding}
```

Examples:
```
PHYSICAL EXAMINATION.Abdominal.Tenderness
PHYSICAL EXAMINATION.Body measure.BMI (body mass index) range
```

If no `PHYSICAL EXAMINATION` paths are included in the config, all physical examination data is shown (except BMI). If any `PHYSICAL EXAMINATION` paths are included, only the specified findings are shown.

## Style Columns

### Collapse

`TRUE` — The section is initially collapsed in the UI; the participant must click to expand it.
`FALSE` or blank — The section is expanded by default.

### Highlight

`TRUE` — The item is visually highlighted (emphasis styling in the UI).
`FALSE` or blank — No highlight.

### Top

A numeric value (float) that pins this item to the "Key Findings" panel at the top of the case review page. Items with lower `Top` values are shown first (e.g., `Top: 1` appears before `Top: 3`).

Leave blank to not pin the item.

> **Note:** The `Top` column cannot be set on top-level paths (paths with fewer than two dot-separated segments). Attempting to do so will cause a validation error.

## Complete Example

A two-arm experiment:

**Arm A: AI prediction shown, selected features**

```csv
User,Case No.,Path,Collapse,Highlight,Top
alice@example.com,1,BACKGROUND.Family History.Condition A: No,FALSE,TRUE,
alice@example.com,1,BACKGROUND.Family History.Condition B: No,FALSE,TRUE,
alice@example.com,1,BACKGROUND.Medical History.Symptom X: Yes,FALSE,TRUE,1
alice@example.com,1,BACKGROUND.Medical History.Symptom Y: No,FALSE,TRUE,
alice@example.com,1,BACKGROUND.Medical History.Symptom Z: Yes,FALSE,TRUE,
alice@example.com,1,RISK ASSESSMENT.AI Predictions,FALSE,TRUE,
alice@example.com,2,BACKGROUND.Family History.Condition A: Yes,FALSE,TRUE,
alice@example.com,2,BACKGROUND.Medical History.Symptom X: Yes,FALSE,TRUE,1
alice@example.com,2,BACKGROUND.Medical History.Symptom Y: No,FALSE,TRUE,
alice@example.com,2,RISK ASSESSMENT.AI Predictions,FALSE,TRUE,
```

**Arm B: No AI prediction**

```csv
bob@example.com,1,BACKGROUND.Family History.Condition A: No,FALSE,TRUE,
bob@example.com,1,BACKGROUND.Family History.Condition B: No,FALSE,TRUE,
bob@example.com,1,BACKGROUND.Medical History.Symptom X: Yes,FALSE,TRUE,1
bob@example.com,1,BACKGROUND.Medical History.Symptom Y: No,FALSE,TRUE,
bob@example.com,1,BACKGROUND.Medical History.Symptom Z: Yes,FALSE,TRUE,
bob@example.com,2,BACKGROUND.Family History.Condition A: Yes,FALSE,TRUE,
bob@example.com,2,BACKGROUND.Medical History.Symptom X: Yes,FALSE,TRUE,1
bob@example.com,2,BACKGROUND.Medical History.Symptom Y: No,FALSE,TRUE,
```

> Arm B is identical to Arm A except the `RISK ASSESSMENT.AI Predictions` rows are omitted.

> **Example:** For CRC-specific display config examples with colorectal cancer features, see [CRC Experiment Config](../examples/crc-screening/experiment-config.md).

## Validation Errors

The upload endpoint returns errors in these situations:

| Error | Cause | Fix |
|-------|-------|-----|
| 400 — No file | No `file` field in the multipart request | Include `file` in the form data |
| 400 — Invalid extension | File does not end in `.csv` | Rename the file with `.csv` extension |
| 400 — Invalid user email | `User` column is empty in a row | Fill in the email for all rows |
| 400 — Invalid case ID | `Case No.` is empty or non-integer | Ensure all case IDs are integers |
| 400 — Config file incorrect | `Top` value is not numeric, or path has fewer than 2 segments but has a Top value | Fix the `Top` column values |

## Related Documentation

- [Creating Experiments](../researcher-guide/creating-experiments.md) — How to design and generate the CSV
- [Admin Configuration](../admin-guide/configuration.md) — How to upload and manage configs
- [OMOP Mapping](omop-mapping.md) — How paths map to clinical data in the database
