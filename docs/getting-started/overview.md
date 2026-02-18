# Platform Overview

## Architecture

AugMed has three main components that work together:

```
React Frontend  →  Flask API  →  PostgreSQL Database
(augmed-app)       (augmed-api-v2)  (OMOP CDM + app tables)
```

**React Frontend** (`augmed-app`): The web interface that participants use. It displays clinical case information, manages the review workflow, and submits answers. The frontend communicates with the API over HTTPS using JWT tokens for authentication.

**Flask API** (`augmed-api-v2`): The backend server, written in Python. It handles authentication, retrieves and formats case data, stores participant responses, and records timing analytics. All data access goes through this API — the frontend never touches the database directly.

**PostgreSQL Database**: Stores two categories of data:
1. **OMOP CDM tables** — the de-identified clinical data (patients, visits, observations, measurements, drug exposures, concept definitions)
2. **Application tables** — users, experiment configurations, participant responses, and analytics

In production, the database runs on AWS RDS (managed PostgreSQL), the API runs on AWS ECS Fargate (containerized), and the frontend is served separately. See [Deployment](../admin-guide/deployment.md) for infrastructure details.

## How Experiments Work

A typical AugMed experiment follows this flow:

### 1. Load Clinical Cases

The researcher (or a data engineer) loads de-identified patient cases into the database in OMOP format. Each case corresponds to a clinical visit (`visit_occurrence`) linked to a patient (`person`) who has associated observations, measurements, drug exposures, and other clinical data.

### 2. Configure the Questionnaire

An administrator uploads an **answer config** — a JSON document defining the questionnaire that participants will complete for each case. This specifies each question's type (free text, single choice, multiple choice), wording, and options.

### 3. Design Experimental Arms

The researcher defines which clinical features each participant will see for each case. This is the core of the experimental design. A participant assigned to the "AI score shown" arm sees the AI CRC risk score; one assigned to the "no AI score" arm does not. Feature visibility is controlled at a per-feature, per-case, per-user level.

### 4. Upload the Display Config

The researcher prepares a CSV file mapping each participant email to each case they should review, specifying exactly which clinical features they should see. This CSV is uploaded via the admin API and stored as **display configs** in the database.

### 5. Participants Review Cases

Participants log in, see a list of their assigned cases (one at a time, in order), review the clinical information, and submit the questionnaire. The platform records their answers along with precise timing data.

### 6. Export and Analyze

After data collection, the researcher runs an export script to produce a CSV file containing all responses, linked to demographic and clinical feature data. This CSV is the primary analysis dataset.

## Key Concepts

### Case

A **case** is a de-identified clinical encounter presented to participants for review. In the database, a case is a `visit_occurrence` record. Each case is linked to a `person` (the patient) and to associated clinical data (observations, measurements, drug exposures). Cases are identified by their `visit_occurrence_id`, which serves as the `case_id` throughout the system.

### Person (Patient)

A **person** is a de-identified patient record in the OMOP CDM `person` table. Persons are linked to cases via the `visit_occurrence.person_id` field. Demographic information (age, gender) is derived from person records.

### Visit

A **visit** is a clinical encounter stored in the `visit_occurrence` table. Each visit has a start date, an associated person, and links to all clinical data recorded during that encounter. In AugMed, one visit equals one case.

### Display Config

A **display config** (`display_config` table) defines exactly which clinical features a specific participant sees for a specific case. Each display config has:
- A `user_email` — the participant it belongs to
- A `case_id` — the case it applies to
- A `path_config` — a JSON array of path entries specifying which features to show, and optional style directives (collapse, highlight, top-pin)

Display configs are created by uploading a CSV file via `POST /admin/config/upload`.

### Path Config

The **path config** is the JSON array within a display config that specifies which clinical data nodes to show. Each entry has a `path` (a dot-separated string like `BACKGROUND.Medical History.Fatigue: Yes`) and an optional `style` object. The path syntax mirrors the hierarchical structure of clinical data as displayed in the UI.

### Answer Config

An **answer config** (`answer_config` table) defines the questionnaire structure — the set of questions participants answer for each case. There is one active answer config at a time. It is a JSON document containing an array of question objects, each with a `type`, `title`, `options` (for choice questions), and `required` flag.

### Arm

An **arm** is a researcher-defined experimental condition. AugMed does not have a formal "arm" database table — arms are implicit in the display config assignments. All participants assigned configs that include the AI score path are in the "AI shown" arm; those without it are in the "AI not shown" arm. More complex designs (varying which features are shown) are implemented by creating different sets of display configs.

### Experiment

An **experiment** is a complete research study conducted on the platform. An experiment encompasses: the set of cases loaded, the answer config (questionnaire), the participant roster, the display config assignments (which define the arms), and the resulting answer and analytics data.

### AI Score

The **AI score** is a machine-learning-generated colorectal cancer (CRC) risk score for each patient. It is stored as an observation in the OMOP `observation` table using concept ID `45614722`. The score takes the form `"Colorectal Cancer Score: {value}"` stored in `value_as_string`. Whether a participant sees this score is controlled by including the `RISK ASSESSMENT.CRC risk assessments` path in their display config.

### OMOP CDM

The **OMOP Common Data Model (CDM)** is a standardized schema for electronic health record data. It uses numeric concept IDs (from a controlled vocabulary) to represent clinical entities. AugMed stores all patient clinical data in OMOP format, which enables data from different sources to be used in the platform without changing the application code.

### Concept ID

A **concept ID** is an integer that identifies a clinical entity in the OMOP vocabulary. For example, concept ID `45614722` represents the AI CRC risk score observation. The `concept` table maps concept IDs to human-readable names. When the API displays clinical data, it resolves concept IDs to concept names for the UI.
