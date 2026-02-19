# CRC Screening Terminology

This file documents the clinical terminology, OMOP concept mappings, and screening pathway used in the AIM-AHEAD CRC Screening Study.

## Clinical Context

Colorectal cancer (CRC) is the third most common cancer in the United States. Screening guidelines (USPSTF) recommend regular screening for adults aged 45-75 using stool-based tests or direct visualization procedures. The AugMed CRC study presented clinicians with de-identified patient cases and asked them to assess CRC risk and recommend appropriate screening.

## CRC-Specific OMOP Concepts

| Concept ID | Concept Name | Domain | Used For |
|-----------|-------------|--------|---------|
| 45614722 | Colorectal Cancer Score | Observation | AI-generated CRC risk score |
| 4167217 | Family history of clinical finding | Observation | Family history category |
| 1008364 | History of clinical finding in subject | Observation | Medical history category |
| 38000282 | Chief Complaint | Type Concept | Chief complaint observations |
| 4152368 | Abdominal | Measurement | Abdominal examination findings |
| 40490382 | BMI (body mass index) centile | Measurement | BMI, displayed as categorical range |

## AI Risk Score

The CRC risk score was a machine-learning-generated numeric score stored in the OMOP `observation` table:

- **Concept ID:** `45614722`
- **Storage format:** `value_as_string = "Colorectal Cancer Score: {value}"`
- **Display format:** `"Predicted Colorectal Cancer Score: {value}"`
- **Risk categories:**
  - Low: score < 6
  - Medium: score 6-11
  - High: score > 11

The path to show/hide the AI score in display configs:
```
RISK ASSESSMENT.CRC risk assessments
```

To provide the score directly in the CSV (bypassing database lookup):
```
RISK ASSESSMENT.Colorectal Cancer Score: 12
```

## Clinical Feature Categories

### Family History Features

| Feature | Path Format |
|---------|------------|
| Cancer | `BACKGROUND.Family History.Cancer: Yes/No` |
| Colorectal Cancer | `BACKGROUND.Family History.Colorectal Cancer: Yes/No` |
| Diabetes | `BACKGROUND.Family History.Diabetes: Yes/No` |
| Hypertension | `BACKGROUND.Family History.Hypertension: Yes/No` |

### Medical History Features

| Feature | Path Format |
|---------|------------|
| Abdominal Pain/Distension | `BACKGROUND.Medical History.Abdominal Pain/Distension: Yes/No` |
| Anxiety and/or Depression | `BACKGROUND.Medical History.Anxiety and/or Depression: Yes/No` |
| Asthma | `BACKGROUND.Medical History.Asthma: Yes/No` |
| Blood Stained Stool | `BACKGROUND.Medical History.Blood Stained Stool: Yes/No` |
| Chronic Diarrhea | `BACKGROUND.Medical History.Chronic Diarrhea: Yes/No` |
| Constipation | `BACKGROUND.Medical History.Constipation: Yes/No` |
| Diabetes | `BACKGROUND.Medical History.Diabetes: Yes/No` |
| Fatigue | `BACKGROUND.Medical History.Fatigue: Yes/No` |
| Headache | `BACKGROUND.Medical History.Headache: Yes/No` |
| Hyperlipidemia | `BACKGROUND.Medical History.Hyperlipidemia: Yes/No` |
| Hypertension | `BACKGROUND.Medical History.Hypertension: Yes/No` |
| Hypothyroidism | `BACKGROUND.Medical History.Hypothyroidism: Yes/No` |
| Irritable Bowel Syndrome | `BACKGROUND.Medical History.Irritable Bowel Syndrome: Yes/No` |
| Migraines | `BACKGROUND.Medical History.Migraines: Yes/No` |
| Osteoarthritis | `BACKGROUND.Medical History.Osteoarthritis: Yes/No` |
| Rectal Bleeding | `BACKGROUND.Medical History.Rectal Bleeding: Yes/No` |
| Shortness of Breath | `BACKGROUND.Medical History.Shortness of Breath: Yes/No` |
| Tenderness Abdomen | `BACKGROUND.Medical History.Tenderness Abdomen: Yes/No` |

### Social History Features

| Feature | Path Format |
|---------|------------|
| Smoking | `BACKGROUND.Social History.Smoke: Yes/No` |
| Alcohol | `BACKGROUND.Social History.Alcohol: Yes/No` |

## Screening Pathway

The CRC screening questionnaire collected two primary outcomes:

### Risk Assessment (Primary Outcome)
- 1 = Very Low Risk
- 2 = Low Risk
- 3 = Moderate Risk
- 4 = High Risk
- 5 = Very High Risk

### Screening Recommendation (Secondary Outcome)
- Colonoscopy
- Fecal Immunochemical Test (FIT)
- No screening, recommendation for reassessment in 1 year
- No screening, recommendation for reassessment in 3 years
- No screening, recommendation for reassessment in 5 years

## Page Configuration

The CRC study used this `page_config` in the `system_config` table:

```json
{
  "BACKGROUND": {
    "Family History": [4167217],
    "Social History": {
      "Smoke": [4041306],
      "Alcohol": [4029833]
    },
    "Medical History": [1008364],
    "CRC risk assessments": [45614722]
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
