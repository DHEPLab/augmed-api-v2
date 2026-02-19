# Adapting AugMed for Your Study

This guide walks through the process of adapting AugMed for a new clinical domain. AugMed is designed as a general-purpose clinical case review platform — the clinical content is entirely configurable through OMOP data, page configuration, questionnaires, and display configs.

For a complete worked example, see the [CRC Screening Example](../examples/crc-screening/README.md).

## Overview

Adapting AugMed for a new study involves five steps:

1. **Define your clinical scenario** and identify OMOP concept mappings
2. **Create case data** in OMOP format
3. **Configure the questionnaire** (answer config)
4. **Design experimental arms** and build display configs
5. **Deploy and validate**

## Step 1: Define Your Clinical Scenario

Start by answering these questions:

- **What clinical decision** are participants making? (e.g., risk assessment, diagnosis, treatment recommendation)
- **What patient data** do participants need to review? (e.g., lab results, imaging reports, medication history, vital signs)
- **What is the AI model output?** If your study includes an AI component, what does the model predict and how is it formatted?
- **What are the experimental conditions?** How will you vary the information shown to participants?

### Map Your Clinical Concepts to OMOP

AugMed stores all clinical data in [OMOP CDM format](https://ohdsi.github.io/CommonDataModel/). You need to identify OMOP concept IDs for:

- **Observation concepts** — clinical findings, symptoms, history items, AI model outputs
- **Measurement concepts** — lab values, vital signs, physical exam findings
- **Drug concepts** — medications (if relevant)

Use [Athena](https://athena.ohdsi.org) to search the OMOP vocabulary and find standard concept IDs for your clinical domain.

**Example:** In the CRC screening study, concept ID `45614722` was used for the AI risk score, `4167217` for family history observations, and `1008364` for medical history. See [CRC Terminology](../examples/crc-screening/terminology.md) for the full mapping.

## Step 2: Create Case Data

Load your de-identified clinical data into the OMOP tables:

| Table | What to load |
|-------|-------------|
| `person` | Patient demographics (gender, birth year) |
| `visit_occurrence` | Clinical encounters (one per case) |
| `observation` | Clinical findings, history items, AI scores |
| `measurement` | Lab values, vital signs, physical exam |
| `drug_exposure` | Medications (optional) |
| `concept` | OMOP vocabulary entries for all concept IDs used |

Data can be loaded via PostgreSQL `COPY` commands from CSV files. See `script/sample_data/` for CSV templates.

### Configure the Page Structure

Update the `page_config` in the `system_config` table to map your clinical sections to OMOP concept IDs:

```json
{
  "BACKGROUND": {
    "Your Category 1": [concept_id_list],
    "Your Category 2": [concept_id_list],
    "Your AI Model Output": [your_ai_concept_id]
  },
  "PATIENT COMPLAINT": {
    "Chief Complaint": [complaint_concept_ids]
  },
  "PHYSICAL EXAMINATION": {
    "Exam Section": [measurement_concept_ids]
  }
}
```

The keys become section and category names displayed in the UI. The values are lists of OMOP concept IDs to query from the clinical data tables.

See [OMOP Mapping](../reference/omop-mapping.md) for details on how the page config drives data retrieval.

## Step 3: Configure the Questionnaire

Create an answer config with the questions participants will answer for each case:

```bash
curl -X POST https://your-augmed-server/admin/config/answer \
  -H "Content-Type: application/json" \
  -d '{
    "config": [
      {
        "type": "SingleChoice",
        "title": "Your primary outcome question",
        "options": ["Option A", "Option B", "Option C"],
        "required": true
      },
      {
        "type": "Paragraph",
        "title": "Any additional comments?",
        "required": false
      }
    ]
  }'
```

**Question types:** `Text` (single line), `Paragraph` (multi-line), `SingleChoice` (radio buttons), `MultipleChoice` (checkboxes).

See [Configuration](../admin-guide/configuration.md) for the full answer config specification.

**Example:** The CRC study used questions about risk assessment (1-5 scale), screening recommendation (categorical), and confidence. See [CRC Experiment Config](../examples/crc-screening/experiment-config.md).

## Step 4: Design Experimental Arms

Define your arms by deciding which clinical features each group of participants will see.

### Build the Display Config CSV

The CSV has six columns: `User, Case No., Path, Collapse, Highlight, Top`

Each row specifies one clinical feature visible to one participant for one case. The collection of rows for a participant-case pair defines their complete information set.

**Path syntax:**
```
BACKGROUND.{Category}.{Feature}: {Value}     # Clinical history items
RISK ASSESSMENT.{Your AI Section}             # AI model output toggle
PHYSICAL EXAMINATION.{Section}.{Finding}      # Physical exam items
```

**Arm differences** are implemented by including or excluding rows. For example, to create an "AI shown" vs. "no AI" design, include the `RISK ASSESSMENT.*` row for one arm and omit it for the other.

See [Creating Experiments](../researcher-guide/creating-experiments.md) and [Config CSV Format](../reference/config-csv-format.md) for the full specification.

## Step 5: Deploy and Validate

### Deploy

Choose a deployment option:

| Option | Best For |
|--------|----------|
| [One-Click Deploy (Railway)](../getting-started/one-click-deploy.md) | Quick setup, small studies |
| [Self-Hosted (Docker Compose)](../getting-started/self-hosted-deploy.md) | Local testing, institutional servers |
| [AWS Infrastructure](../admin-guide/deployment.md) | Production studies with compliance requirements |

### Validate

Before launching your study:

1. **Log in as a test participant** and review several cases to verify:
   - Clinical data displays correctly
   - The questionnaire matches your design
   - AI model output (if applicable) appears when expected and is hidden when expected
2. **Export test data** to confirm all columns are populated correctly
3. **Check arm assignments** by querying the database or reviewing display configs
4. **Run the attention check** — complete 10+ cases to verify the built-in attention check appears

### Seed Data for Testing

For a fresh deployment, create a seed script (similar to `script/seed/seed_demo.py`) with synthetic data from your clinical domain. This enables rapid testing without loading real patient data. See [CRC Seed Data](../examples/crc-screening/seed-data.md) for an example.

## Checklist

- [ ] OMOP concept IDs identified for all clinical features
- [ ] Patient data loaded in OMOP format
- [ ] Page config updated with your concept ID mappings
- [ ] Answer config created with your questionnaire
- [ ] Display config CSV built with arm assignments
- [ ] Test participant can log in and review cases
- [ ] AI model output displays correctly (if applicable)
- [ ] Export data contains all expected columns
- [ ] IRB approval obtained for your study protocol

## Related Documentation

- [CRC Screening Example](../examples/crc-screening/README.md) — Complete worked example
- [Platform Overview](../getting-started/overview.md) — Architecture and key concepts
- [Terminology](../getting-started/terminology.md) — Glossary of platform terms
- [OMOP CDM Documentation](https://ohdsi.github.io/CommonDataModel/) — Official OMOP reference
