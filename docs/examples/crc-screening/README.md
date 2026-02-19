# Example: Colorectal Cancer Screening Study

This directory contains a complete worked example of how AugMed was configured for the **AIM-AHEAD Colorectal Cancer (CRC) Screening Study** at UNC-Chapel Hill's DHEP Lab.

Use these files as a reference when adapting AugMed for your own clinical domain. Each file maps to a section of the main documentation and shows how the generic concepts were instantiated for CRC screening research.

## Files

| File | Description |
|------|-------------|
| [terminology.md](terminology.md) | CRC-specific OMOP concepts, medical terms, and screening pathway |
| [experiment-config.md](experiment-config.md) | Sample experiment JSON with CRC questions, answer configs, and arm definitions |
| [seed-data.md](seed-data.md) | Walkthrough of the CRC demo seed data (`script/seed/seed_demo.py`) |
| [deployment-notes.md](deployment-notes.md) | CRC-specific deployment considerations, data sources, and clinical context |

## Study Overview

The AIM-AHEAD CRC Screening Study investigated how AI-generated risk scores influence clinician decision-making in colorectal cancer screening. Participants (clinicians) reviewed de-identified patient cases and made two key judgments:

1. **Risk assessment** — rating the patient's CRC risk on a 1-5 scale (Very Low to Very High)
2. **Screening recommendation** — choosing from Colonoscopy, FIT (Fecal Immunochemical Test), reassessment, or no screening

The experiment used a controlled information disclosure design: some participants saw an AI-generated CRC risk score alongside the patient's clinical history, while others saw only the clinical history. By comparing outcomes across arms, researchers measured the causal effect of AI assistance on clinical judgment accuracy, confidence, and screening decisions.

## How to Use This Example

1. Read [Adapting AugMed for Your Study](../../guides/adapting-for-your-study.md) for the general workflow
2. Review the files in this directory to see how each step was implemented for CRC screening
3. Use the CRC configuration as a template, replacing clinical concepts with those from your domain

## Related Documentation

- [Platform Overview](../../getting-started/overview.md)
- [Creating Experiments](../../researcher-guide/creating-experiments.md)
- [OMOP Mapping](../../reference/omop-mapping.md)
