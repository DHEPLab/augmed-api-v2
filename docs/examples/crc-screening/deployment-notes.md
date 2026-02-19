# CRC Screening Deployment Notes

This file documents deployment considerations specific to the AIM-AHEAD CRC Screening Study.

## Data Source

Patient cases were drawn from de-identified electronic health record (EHR) data, converted to OMOP CDM format. The conversion involved:

1. **EHR extraction** — De-identified patient records with family history, medical history, social history, chief complaints, physical examination findings, and lab results
2. **OMOP mapping** — Clinical concepts mapped to standard OMOP vocabulary codes via Athena
3. **AI score generation** — A machine learning model generated CRC risk scores for each patient, stored as OMOP observations (concept ID `45614722`)
4. **Quality review** — Clinical team reviewed mapped data for accuracy and completeness

## IRB Considerations

The CRC screening study operated under IRB approval for:

- Use of de-identified EHR data (HIPAA Safe Harbor)
- Clinician participants (not patients) as research subjects
- Informed consent for clinician participation
- Data export restricted to anonymized identifiers (`user_id` is SHA-256 hash of email)

When adapting AugMed for your study, consult your institution's IRB regarding:

- **Data classification** — De-identified vs. limited dataset vs. identifiable
- **Participant consent** — Whether clinician reviewers are considered human subjects
- **Data storage** — Where AugMed is hosted and how data is protected
- **Export controls** — Who can access exported research data

## Clinical Context

### Screening Guidelines

The CRC study was designed around USPSTF (U.S. Preventive Services Task Force) colorectal cancer screening guidelines, which recommend:

- Regular screening for adults aged 45-75
- Stool-based tests (FIT, FIT-DNA) as initial screening options
- Colonoscopy as both a screening and diagnostic procedure
- Consideration of family history and personal risk factors

### Questionnaire Design Rationale

The two primary outcome questions (risk assessment and screening recommendation) were designed to:

1. **Risk assessment (1-5 scale):** Capture the clinician's overall CRC risk judgment — ordinal scale enables both ordinal and continuous analysis
2. **Screening recommendation (categorical):** Map directly to clinical action items in screening guidelines — enables analysis of appropriateness against guideline-concordant care

### Feature Selection Rationale

The clinical features shown to participants (family history, medical history, social history, physical exam) were selected because they are:

- Available in standard OMOP-formatted EHR data
- Clinically relevant to CRC risk assessment per screening guidelines
- Controllable at the individual feature level (enabling factorial experimental designs)

## Production Infrastructure

The CRC study was deployed on AWS:

- **API + Frontend:** AWS ECS (Fargate) behind an Application Load Balancer
- **Database:** AWS RDS (PostgreSQL)
- **Domain:** `augmed1.dhep.org`
- **Infrastructure-as-code:** Terraform (see `augmed-infra` repository)

For simpler deployments, AugMed also supports Railway (one-click) and Docker Compose (self-hosted). See [Deployment](../../admin-guide/deployment.md) for all options.

## Recruitment

Clinician participants were recruited through professional networks and clinical partnerships. The recruitment survey (Qualtrics) collected:

- Professional role and specialty
- Years of clinical practice
- CRC screening experience
- Practice location (state)

This survey data was joined with AugMed export data using participant email as the key. See [Exporting Data](../../researcher-guide/exporting-data.md) for details on the recruitment survey integration.
