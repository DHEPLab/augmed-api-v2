# CRC Screening Experiment Configuration

This file shows the complete experiment configuration used in the AIM-AHEAD CRC Screening Study, including the questionnaire, arm definitions, and display config examples.

## Answer Configuration (Questionnaire)

The CRC study used a four-question questionnaire:

```json
{
  "config": [
    {
      "type": "SingleChoice",
      "title": "How would you assess this patient's risk for colorectal cancer?",
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
}
```

## Arm Definitions

### Two-Arm Design (AI vs. No AI)

- **Arm A (AI shown):** Participants see clinical history + AI CRC risk score
- **Arm B (No AI):** Participants see clinical history only

### Four-Arm Design (Feature Variation)

- **Arm A:** Full history + AI score
- **Arm B:** Full history, no AI score
- **Arm C:** Limited history + AI score
- **Arm D:** Limited history, no AI score

## Display Config CSV Examples

### Arm A: AI Score Shown

```csv
User,Case No.,Path,Collapse,Highlight,Top
alice@example.com,12,BACKGROUND.Family History.Colorectal Cancer: No,FALSE,TRUE,
alice@example.com,12,BACKGROUND.Family History.Cancer: No,FALSE,TRUE,
alice@example.com,12,BACKGROUND.Medical History.Fatigue: Yes,FALSE,TRUE,
alice@example.com,12,BACKGROUND.Medical History.Rectal Bleeding: No,FALSE,TRUE,
alice@example.com,12,BACKGROUND.Medical History.Blood Stained Stool: No,FALSE,TRUE,
alice@example.com,12,RISK ASSESSMENT.CRC risk assessments,FALSE,TRUE,
```

### Arm B: No AI Score

```csv
alice@example.com,13,BACKGROUND.Family History.Colorectal Cancer: No,FALSE,TRUE,
alice@example.com,13,BACKGROUND.Family History.Cancer: No,FALSE,TRUE,
alice@example.com,13,BACKGROUND.Medical History.Fatigue: No,FALSE,TRUE,
alice@example.com,13,BACKGROUND.Medical History.Rectal Bleeding: Yes,FALSE,TRUE,
alice@example.com,13,BACKGROUND.Medical History.Blood Stained Stool: No,FALSE,TRUE,
```

Note: Arm B is identical except the `RISK ASSESSMENT.CRC risk assessments` row is omitted.

## Python Script for Generating Config CSV

```python
import csv

participants = ["alice@example.com", "bob@example.com"]
cases_arm_a = [1, 3, 5, 7]   # AI shown
cases_arm_b = [2, 4, 6, 8]   # No AI

features = [
    ("Family History", "Colorectal Cancer", None),
    ("Family History", "Cancer", None),
    ("Medical History", "Fatigue", None),
    ("Medical History", "Rectal Bleeding", None),
]

rows = []
for user in participants:
    for case_id in cases_arm_a:
        for category, feature, value in features:
            path = f"BACKGROUND.{category}.{feature}: Yes"  # derive from DB
            rows.append([user, case_id, path, "FALSE", "TRUE", ""])
        rows.append([user, case_id, "RISK ASSESSMENT.CRC risk assessments", "FALSE", "TRUE", ""])

    for case_id in cases_arm_b:
        for category, feature, value in features:
            path = f"BACKGROUND.{category}.{feature}: No"  # derive from DB
            rows.append([user, case_id, path, "FALSE", "TRUE", ""])

with open("experiment_config.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["User", "Case No.", "Path", "Collapse", "Highlight", "Top"])
    writer.writerows(rows)
```

## Outcome Variables in Export Data

| Column | Type | Description |
|--------|------|-------------|
| `risk_assessment` | integer (1-5) | CRC risk rating: 1=Very Low, 2=Low, 3=Moderate, 4=High, 5=Very High |
| `confidence_level` | integer (1-3) | Confidence: 1=Not Confident, 2=Somewhat, 3=Very Confident |
| `screening_recommendation` | string | "Colonoscopy", "FIT", "No screening", "Reassessment in N years" |
| `ai_score (shown)` | Yes/No | Whether the AI CRC risk score was visible |
| `ai_score (value)` | integer | Numeric CRC risk score |
| `experience_screening` | string | Whether participant has CRC screening experience |
| `years_screening` | string | Years of CRC screening experience |

## Sample Answer JSON

```json
{
  "How would you assess this patient's risk for colorectal cancer?": "Moderate Risk",
  "How confident are you in your screening recommendation?": "2 - Somewhat Confident",
  "What colorectal cancer screening options would you recommend for this patient?": "Colonoscopy",
  "What additional information would be useful for making your recommendation?": "Would like to know more about the patient's recent lab results."
}
```

## R Analysis Snippet (CRC-Specific)

```r
# Screening recommendation analysis
df %>%
  mutate(rec_colonoscopy = (screening_recommendation == "Colonoscopy")) %>%
  group_by(ai_shown) %>%
  summarize(
    pct_colonoscopy = mean(rec_colonoscopy, na.rm = TRUE),
    n = n()
  )

# Factor levels for CRC screening recommendations
df$screening_rec <- factor(df$screening_recommendation,
  levels = c("No screening", "Reassessment in 1 years",
             "Reassessment in 3 years", "FIT", "Colonoscopy"))
```
