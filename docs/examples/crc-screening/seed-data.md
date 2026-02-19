# CRC Demo Seed Data

This file documents the demo seed data created by `script/seed/seed_demo.py` for the CRC screening example.

## Overview

The seed script creates a minimal but complete dataset for exploring the CRC screening use case. It is idempotent (checks for existing data before inserting) and runs automatically when `SEED_DEMO_DATA=true` is set in the environment.

## What Gets Created

### OMOP Concepts

The seed inserts the minimum OMOP vocabulary entries needed to render cases:

| Category | Concepts |
|----------|----------|
| Gender | MALE (8507), FEMALE (8532) |
| Race | Black/African American (8516), White (8527), Asian (8515) |
| Observations | Tobacco (4041306), Alcohol (4238768), Family History (4167217), Medical History (1008364), Chief Complaint (38000282), Abdominal Pain (35826012), **CRC Score (45614722)** |
| Measurements | Hemoglobin (4181041), Weight (4301868), Blood Pressure (4326744), Abdominal (4152368), BMI (40490382) |

### Patients (3 records)

| person_id | Gender | Birth Year | Source ID |
|-----------|--------|------------|-----------|
| 1001 | Female | 1983 | DEMO-001 |
| 1002 | Male | 1975 | DEMO-002 |
| 1003 | Female | 1990 | DEMO-003 |

### Clinical Data Per Patient

Each patient gets identical observation types with varying values:

- **Smoking status:** "non-smoker" (concept 4041306)
- **Alcohol intake:** recorded as units (concept 4238768)
- **Family history:** "Cancer: No" (concept 4167217)
- **Medical history:** "Hypertension: Yes" (concept 1008364)
- **Chief complaint:** Nocturia, "3x per night" (concept 79936)
- **Abdominal pain:** Patient-reported, "Duration: 2 months" (concept 35826012)
- **CRC risk score:** `"Colorectal Cancer Score: {7 + person_id - 1001}"` (concept 45614722)
  - Patient 1001: score 7 (Medium risk)
  - Patient 1002: score 8 (Medium risk)
  - Patient 1003: score 9 (Medium risk)

### Page Configuration

The seed creates a `page_config` in `system_config`:

```json
{
  "BACKGROUND": {
    "Family History": [4167217],
    "Social History": {
      "Smoke": [4041306],
      "Drink": [4238768]
    },
    "Medical History": [1008364],
    "CRC risk assessments": [45614722]
  },
  "PATIENT COMPLAINT": {
    "Chief Complaint": [38000282],
    "Patient Reported": [44814721]
  },
  "PHYSICAL EXAMINATION": {
    "Hemoglobin": [4181041],
    "Body measure": [4301868, 4326744, 4152368]
  }
}
```

### Answer Configuration (CRC Questionnaire)

```json
[
  {
    "type": "single_choice",
    "title": "Based on the information provided, what is your assessment of colorectal cancer risk for this patient?",
    "required": true,
    "options": ["Low risk", "Medium risk", "High risk", "Insufficient information"]
  },
  {
    "type": "single_choice",
    "title": "Would you recommend this patient for colorectal cancer screening?",
    "required": true,
    "options": ["Yes, immediately", "Yes, within routine schedule", "No", "Need more information"]
  },
  {
    "type": "free_text",
    "title": "Please provide any additional comments or reasoning for your assessment.",
    "required": false
  }
]
```

### Display Configs

All 3 cases are assigned to the demo researcher (`researcher@demo.augmed.org`) with full feature visibility including the CRC risk score:

```json
[
  {"path": "BACKGROUND.Family History.Cancer: No", "style": {"highlight": true}},
  {"path": "BACKGROUND.Medical History.Hypertension: Yes", "style": {"highlight": true}},
  {"path": "BACKGROUND.Social History.Smoke.non-smoker", "style": {}},
  {"path": "BACKGROUND.Social History.Drink", "style": {}},
  {"path": "RISK ASSESSMENT.CRC risk assessments", "style": {}}
]
```

### Demo Users

| Email | Role | Password |
|-------|------|----------|
| `admin@demo.augmed.org` | Admin | `augmed-demo` |
| `researcher@demo.augmed.org` | Researcher/Participant | `augmed-demo` |

## Adapting for Your Study

To create a seed script for a different clinical domain, you would modify:

1. **Observation concepts** — Replace CRC-specific concept IDs with your domain's OMOP concepts
2. **AI score observations** — Replace concept `45614722` and the `"Colorectal Cancer Score: {value}"` format with your AI model's output
3. **Page configuration** — Update `"CRC risk assessments"` key and concept ID list
4. **Answer configuration** — Replace CRC screening questions with your study's questionnaire
5. **Display configs** — Update the `"RISK ASSESSMENT.CRC risk assessments"` path to match your page config

See [Adapting AugMed for Your Study](../../guides/adapting-for-your-study.md) for the full workflow.
