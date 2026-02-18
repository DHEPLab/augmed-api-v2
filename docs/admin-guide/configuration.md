# Configuration

AugMed has three main configuration objects: the system config (page structure), the answer config (questionnaire), and the display config (per-participant feature visibility). This guide covers how to set up and update each.

## System Config (Page Structure)

The `system_config` table stores the page configuration that defines which OMOP concept IDs map to which clinical sections on the case review page.

### Structure

The `page_config` entry contains a JSON object with three top-level sections:

```json
{
  "BACKGROUND": {
    "Family History": [concept_id_list],
    "Social History": {
      "Smoke": [concept_id_list],
      "Alcohol": [concept_id_list]
    },
    "Medical History": [concept_id_list],
    "CRC risk assessments": [45614722]
  },
  "PATIENT COMPLAINT": {
    "Chief Complaint": [concept_id_list]
  },
  "PHYSICAL EXAMINATION": {
    "Abdominal": [concept_id_list],
    "Body measure": [concept_id_list]
  }
}
```

- Keys under `BACKGROUND` become the category names shown in the "Background" section
- Values are either a list of concept IDs (leaf node) or a nested object (sub-categories)
- Concept ID `45614722` is the AI CRC risk score

### Updating Page Config

Update the system config directly in the database:

```sql
UPDATE system_config
SET json_config = '{
  "BACKGROUND": {
    "Family History": [4167217],
    "Medical History": [1008364],
    "CRC risk assessments": [45614722]
  },
  "PATIENT COMPLAINT": {
    "Chief Complaint": [38000282]
  },
  "PHYSICAL EXAMINATION": {
    "Abdominal": [4152368]
  }
}'::json
WHERE id = 'page_config';
```

> **Note:** After changing the page config, you may need to regenerate your display config CSVs if the section names have changed, since path strings must match the page config structure.

## Answer Config (Questionnaire)

The answer config defines the questionnaire that all participants complete for each case. You can maintain multiple versions; the API always uses the most recently created one.

### Question Types

| Type | Description |
|------|-------------|
| `Text` | Single-line free text response |
| `Paragraph` | Multi-line free text response |
| `SingleChoice` | Radio buttons — participant selects exactly one option |
| `MultipleChoice` | Checkboxes — participant can select multiple options |

### Creating an Answer Config

```bash
curl -X POST https://your-augmed-server/admin/config/answer \
  -H "Content-Type: application/json" \
  -d '{
    "config": [
      {
        "type": "SingleChoice",
        "title": "How would you assess this patient'\''s risk for colorectal cancer?",
        "options": ["Very Low Risk", "Low Risk", "Moderate Risk", "High Risk", "Very High Risk"],
        "required": true
      },
      {
        "type": "SingleChoice",
        "title": "How confident are you in your screening recommendation?",
        "options": [
          "1 - Not Confident",
          "2 - Somewhat Confident",
          "3 - Very Confident"
        ],
        "required": true
      },
      {
        "type": "SingleChoice",
        "title": "What colorectal cancer screening options would you recommend for this patient?",
        "options": [
          "No screening, recommendation for reassessment in 1 years",
          "No screening, recommendation for reassessment in 3 years",
          "No screening, recommendation for reassessment in 5 years",
          "Fecal Immunochemical Test (FIT)",
          "Colonoscopy"
        ],
        "required": true
      },
      {
        "type": "Paragraph",
        "title": "What additional information would be useful for making your recommendation?",
        "required": false
      }
    ]
  }'
```

Expected response:

```json
{
  "data": {"id": "550e8400-e29b-41d4-a716-446655440000"},
  "status": "success"
}
```

### Retrieving the Current Answer Config

```bash
curl https://your-augmed-server/api/config/answer
```

This returns the most recently created config. For authenticated users, an attention check question is dynamically appended every 10 cases.

### The Attention Check

Every 10 cases per participant, the API automatically adds an attention check question at the end of the questionnaire. The correct answer is "All of the above." This is a built-in quality control mechanism and does not need to be configured.

The attention check question:

```
"Attention Check – please read carefully and select 'All of the above' below"

Options:
- "I wasn't really reading"
- "I'm just clicking through"
- "I prefer not to answer"
- "All of the above"  ← correct answer
```

### Versioning Questionnaires

Each call to `POST /admin/config/answer` creates a new version. The API returns the latest version. Old versions remain in the database and are referenced by `answer.answer_config_id` for historical records.

To check which version was used for a given answer:

```sql
SELECT
    a.id,
    a.user_email,
    a.answer_config_id,
    ac.created_timestamp AS config_created
FROM answer a
JOIN answer_config ac ON ac.id = a.answer_config_id
ORDER BY a.created_timestamp DESC;
```

## Display Config (Feature Visibility)

The display config is uploaded as a CSV file and stored in the `display_config` table. See [Config CSV Format](../reference/config-csv-format.md) for the full specification.

### Uploading a Display Config

```bash
curl -X POST https://your-augmed-server/admin/config/upload \
  -F "file=@my_experiment_config.csv"
```

> **Warning:** Each upload **replaces all existing display configs**. The service calls `clean_configurations()` before saving new ones.

### Viewing Current Assignments

Query the database to review what is currently loaded:

```sql
SELECT
    user_email,
    case_id,
    jsonb_array_length(path_config::jsonb) AS num_paths
FROM display_config
ORDER BY user_email, case_id;
```

### Removing All Assignments

Use the script:

```bash
cd script/assign_cases
python remove_all_case_assignments.py
```

Or directly:

```sql
DELETE FROM display_config;
```

## Environment Configuration

For API-level settings (JWT, database), see [Deployment](deployment.md#environment-variables).

## Related Documentation

- [Config CSV Format](../reference/config-csv-format.md) — Full display config CSV specification
- [Creating Experiments](../researcher-guide/creating-experiments.md) — How to build the display config for your study
- [API Reference](../reference/api-reference.md) — Admin endpoints for uploading configs
