# Platform Overview

## Architecture

AugMed has four main components that work together:

```
React Frontend  →  Flask API  →  PostgreSQL Database
(augmed-app-v2)    (augmed-api-v2)  (OMOP CDM + app tables)
                       ↑
                   RL Service
                   (augmed-rl)
```

**React Frontend** (`augmed-app-v2`): The web interface that participants use. It displays clinical case information, manages the review workflow, and submits answers. The frontend communicates with the API over HTTPS using JWT tokens for authentication.

**Flask API** (`augmed-api-v2`): The backend server, written in Python. It handles authentication, retrieves and formats case data, stores participant responses, and records timing analytics. All data access goes through this API — the frontend never touches the database directly.

**RL Service** (`augmed-rl`): The adaptive experimentation service, built with FastAPI. It uses Thompson Sampling to dynamically adjust experimental arm assignments based on participant outcomes. The RL service communicates with the API via the export endpoint to fetch response data and update arm weights. See [Adaptive Experiments](../adaptive-experiments/overview.md) for details.

**PostgreSQL Database**: Stores two categories of data:
1. **OMOP CDM tables** — the de-identified clinical data (patients, visits, observations, measurements, drug exposures, concept definitions)
2. **Application tables** — users, experiment configurations, participant responses, and analytics

The platform can be deployed in several ways — from a one-click Railway template to a full AWS infrastructure. See [Deployment](../admin-guide/deployment.md) for all options.

## How Experiments Work

A typical AugMed experiment follows this flow:

### 1. Load Clinical Cases

The researcher (or a data engineer) loads de-identified patient cases into the database in OMOP format. Each case corresponds to a clinical visit (`visit_occurrence`) linked to a patient (`person`) who has associated observations, measurements, drug exposures, and other clinical data.

### 2. Configure the Questionnaire

An administrator uploads an **answer config** — a JSON document defining the questionnaire that participants will complete for each case. This specifies each question's type (free text, single choice, multiple choice), wording, and options.

### 3. Design Experimental Arms

The researcher defines which clinical features each participant will see for each case. This is the core of the experimental design. A participant assigned to the "AI shown" arm sees the AI prediction; one assigned to the "no AI" arm does not. Feature visibility is controlled at a per-feature, per-case, per-user level.

### 4. Upload the Display Config

The researcher prepares a CSV file mapping each participant email to each case they should review, specifying exactly which clinical features they should see. This CSV is uploaded via the admin API and stored as **display configs** in the database.

### 5. Participants Review Cases

Participants log in, see a list of their assigned cases (one at a time, in order), review the clinical information, and submit the questionnaire. The platform records their answers along with precise timing data.

### 6. Export and Analyze

After data collection, the researcher exports data via the export API (`/api/v1/export/`) to produce structured response data linked to demographic and clinical feature data. The export API supports both programmatic access (authenticated with the `EXPORT_API_KEY`) and manual CSV downloads. The RL service also uses this API to fetch outcomes for adaptive arm assignment.

For adaptive experiments, the RL service continuously monitors outcomes and adjusts arm weights using Thompson Sampling. See [Adaptive Experiments](../adaptive-experiments/overview.md) for details.

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

An **arm** is a researcher-defined experimental condition. AugMed does not have a formal "arm" database table — arms are implicit in the display config assignments. All participants assigned configs that include the AI prediction path are in the "AI shown" arm; those without it are in the "AI not shown" arm. More complex designs (varying which features are shown) are implemented by creating different sets of display configs.

### Experiment

An **experiment** is a complete research study conducted on the platform. An experiment encompasses: the set of cases loaded, the answer config (questionnaire), the participant roster, the display config assignments (which define the arms), and the resulting answer and analytics data.

### AI Score

The **AI score** is a machine-learning-generated prediction for each patient, stored as an observation in the OMOP `observation` table. The specific concept ID, score format, and display label are configured per study. Whether a participant sees the AI score is controlled by including the corresponding `RISK ASSESSMENT.*` path in their display config.

> **Example:** In the CRC screening study, the AI score used concept ID `45614722` with format `"Colorectal Cancer Score: {value}"`. See [CRC Terminology](../examples/crc-screening/terminology.md).

### OMOP CDM

The **OMOP Common Data Model (CDM)** is a standardized schema for electronic health record data. It uses numeric concept IDs (from a controlled vocabulary) to represent clinical entities. AugMed stores all patient clinical data in OMOP format, which enables data from different sources to be used in the platform without changing the application code.

### Concept ID

A **concept ID** is an integer that identifies a clinical entity in the OMOP vocabulary. The `concept` table maps concept IDs to human-readable names. When the API displays clinical data, it resolves concept IDs to concept names for the UI. AI score concept IDs are study-specific and configured in the page config.
