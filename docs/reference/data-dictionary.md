# Data Dictionary

This document provides exhaustive column-level documentation for all AugMed database tables.

## Application Tables

---

### `user`

Stores research participant accounts.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | INTEGER | No | auto-increment | Primary key |
| `name` | VARCHAR(128) | Yes | — | Participant full name |
| `email` | VARCHAR(128) | No | — | Email address; unique; used as the primary identifier throughout the app |
| `password` | VARCHAR(192) | Yes | — | Bcrypt-hashed password |
| `salt` | VARCHAR(192) | Yes | — | Password salt |
| `admin_flag` | BOOLEAN | No | false | True for admin users who can access admin endpoints |
| `position` | VARCHAR(512) | Yes | — | Clinical role (e.g., "Attending Physician", "Nurse Practitioner") |
| `employer` | VARCHAR(512) | Yes | — | Institution or organization name |
| `area_of_clinical_ex` | VARCHAR(512) | Yes | — | Clinical specialty or area of expertise |
| `active` | BOOLEAN | No | false | Must be true for the participant to log in |
| `created_timestamp` | TIMESTAMP | No | now() | Row creation time |
| `modified_timestamp` | TIMESTAMP | No | now() | Last update time; auto-updates on change |

**Indexes:**
- `user.email` — unique index (used for all lookups)

---

### `display_config`

Defines which clinical features each participant sees for each case.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | VARCHAR | No | — | Primary key; UUID string generated at upload time |
| `user_email` | VARCHAR | Yes | — | Participant email; links to `user.email` |
| `case_id` | INTEGER | Yes | — | OMOP `visit_occurrence.visit_occurrence_id` |
| `path_config` | JSON | Yes | null | Array of path entry objects specifying visible clinical features |
| `experiment_id` | VARCHAR(100) | Yes | null | Links to `experiment.experiment_id` (if RL-managed) |
| `rl_run_id` | INTEGER | Yes | null | Links to `rl_run.id` (which RL cycle created this config) |
| `arm` | VARCHAR(100) | Yes | null | Which experiment arm this config belongs to |

**`path_config` structure:**

```json
[
  {
    "path": "BACKGROUND.Medical History.Fatigue: Yes",
    "style": {
      "collapse": false,
      "highlight": true,
      "top": 1.0
    }
  },
  {
    "path": "RISK ASSESSMENT.AI Predictions"
  }
]
```

Each entry has:
- `path` (string, required): Dot-separated path identifying the clinical feature
- `style` (object, optional): Display directives — `collapse` (bool), `highlight` (bool), `top` (float)

---

### `answer`

Stores participant questionnaire responses.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | INTEGER | No | auto-increment | Primary key |
| `task_id` | VARCHAR | Yes | — | `display_config.id` for this assignment |
| `case_id` | INTEGER | Yes | — | OMOP `visit_occurrence.visit_occurrence_id` |
| `user_email` | VARCHAR(128) | Yes | — | Participant email |
| `display_configuration` | JSON | Yes | null | Snapshot of the `path_config` used when this answer was submitted |
| `answer_config_id` | UUID | Yes | — | Links to `answer_config.id` — questionnaire version used |
| `answer` | JSON | Yes | null | Participant responses: `{question_title: response_value}` |
| `ai_score_shown` | BOOLEAN | No | false | True if the AI prediction was visible to this participant for this case |
| `created_timestamp` | TIMESTAMP | No | now() | Submission time |
| `modified_timestamp` | TIMESTAMP | No | now() | Last update time |

**Unique constraint:** `(task_id, case_id, user_email)` — prevents duplicate submissions.

**`answer` JSON example:**

```json
{
  "How would you assess this patient's risk level?": "Moderate Risk",
  "How confident are you in your assessment?": "2 - Somewhat Confident",
  "What would you recommend for this patient?": "Option A",
  "What additional information would be useful for making your recommendation?": "Would like to know more about the patient's recent lab results."
}
```

---

### `answer_config`

Stores questionnaire definitions.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | UUID | No | uuid_generate_v4() | Primary key |
| `config` | JSON | No | — | Array of question objects |
| `created_timestamp` | TIMESTAMP | No | now() | When this questionnaire version was created |

**`config` JSON structure:**

```json
[
  {
    "type": "SingleChoice",
    "title": "Question text",
    "options": ["Option A", "Option B"],
    "required": true
  },
  {
    "type": "Paragraph",
    "title": "Free text question",
    "required": false
  }
]
```

Valid `type` values: `"Text"`, `"Paragraph"`, `"SingleChoice"`, `"MultipleChoice"`

---

### `analytics`

Records timing data for each case review session.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | INTEGER | No | auto-increment | Primary key |
| `user_email` | VARCHAR(128) | No | — | Participant email |
| `case_config_id` | VARCHAR | No | — | `display_config.id` for this review session |
| `case_id` | INTEGER | No | — | OMOP `visit_occurrence.visit_occurrence_id` |
| `case_open_time` | TIMESTAMP WITH TIMEZONE | No | — | When participant opened the case |
| `answer_open_time` | TIMESTAMP WITH TIMEZONE | No | — | When participant opened the answer form |
| `answer_submit_time` | TIMESTAMP WITH TIMEZONE | No | — | When participant submitted answers |
| `to_answer_open_secs` | FLOAT | No | — | Seconds from case open to answer form open (case review time) |
| `to_submit_secs` | FLOAT | No | — | Seconds from answer form open to submission (answer time) |
| `total_duration_secs` | FLOAT | No | — | Total seconds from case open to submission |
| `created_timestamp` | TIMESTAMP WITH TIMEZONE | No | now() | Row creation time |
| `modified_timestamp` | TIMESTAMP WITH TIMEZONE | No | now() | Last update time |

**Unique constraint:** `(user_email, case_config_id)` — one analytics row per participant-assignment.

---

### `system_config`

Stores system-wide JSON configuration.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | VARCHAR(15) | No | — | Primary key; configuration key (e.g., `"page_config"`) |
| `json_config` | JSON | Yes | null | Configuration data |

**Known entries:**

| `id` | Description |
|------|-------------|
| `page_config` | Maps clinical sections to OMOP concept IDs |

---

### `reset_password_token`

Stores temporary tokens for the password reset flow.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | VARCHAR | No | — | Primary key; token string returned to client |
| `user_email` | VARCHAR | Yes | — | Email address for this reset request |
| `created_timestamp` | TIMESTAMP | Yes | — | Token creation time |

---

### `experiment`

Stores experiment metadata for adaptive (RL) experiments.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | INTEGER | No | auto-increment | Primary key |
| `experiment_id` | VARCHAR(100) | No | — | Unique experiment identifier (format: `exp-{hex12}`) |
| `name` | VARCHAR(200) | No | — | Human-readable experiment name |
| `description` | TEXT | Yes | — | Experiment description |
| `status` | VARCHAR(20) | No | 'active' | Experiment status: `active`, `paused`, `completed`, `archived` |
| `arms` | JSONB | No | — | Array of arm definitions (name + path_config) |
| `case_pool` | JSONB | Yes | — | Array of participant-case assignments |
| `created_at` | TIMESTAMPTZ | No | now() | Creation time |
| `updated_at` | TIMESTAMPTZ | No | now() | Last update time |

**Unique constraint:** `experiment_id`

---

### `rl_run`

Tracks individual RL (reinforcement learning) cycle executions.

| Column | PostgreSQL Type | Nullable | Default | Description |
|--------|----------------|----------|---------|-------------|
| `id` | INTEGER | No | auto-increment | Primary key |
| `experiment_id` | VARCHAR(100) | Yes | — | Links to `experiment.experiment_id` |
| `model_version` | VARCHAR(100) | Yes | — | Algorithm version used (e.g., `thompson_v1`) |
| `status` | VARCHAR(20) | No | 'pending' | Run status: `pending`, `running`, `completed`, `failed` |
| `triggered_by` | VARCHAR(50) | Yes | — | Who triggered the run: `manual`, `admin_panel`, `scheduled` |
| `configs_generated` | INTEGER | Yes | — | Number of display configs created by this run |
| `answers_consumed` | INTEGER | Yes | — | Number of new answers processed in this run |
| `started_at` | TIMESTAMPTZ | Yes | — | When the run started executing |
| `completed_at` | TIMESTAMPTZ | Yes | — | When the run finished |
| `run_params` | JSONB | Yes | — | Runtime parameters (reward config overrides, etc.) |

**Foreign key:** `experiment_id` → `experiment.experiment_id`

---

## OMOP CDM Tables

Only the columns used by AugMed are documented here. Full OMOP CDM documentation is at [ohdsi.github.io/CommonDataModel](https://ohdsi.github.io/CommonDataModel/).

---

### `person`

| Column | PostgreSQL Type | Description |
|--------|----------------|-------------|
| `person_id` | INTEGER (PK) | Patient identifier |
| `gender_concept_id` | INTEGER | OMOP concept ID for gender |
| `year_of_birth` | INTEGER | Patient's year of birth |
| `person_source_value` | VARCHAR | Original EHR identifier shown in UI |

---

### `visit_occurrence`

| Column | PostgreSQL Type | Description |
|--------|----------------|-------------|
| `visit_occurrence_id` | INTEGER (PK) | Visit identifier = AugMed `case_id` |
| `person_id` | INTEGER | Links to `person.person_id` |
| `visit_start_date` | DATE | Visit date (used to compute patient age at visit) |
| `visit_concept_id` | INTEGER | Type of clinical visit |

---

### `observation`

| Column | PostgreSQL Type | Description |
|--------|----------------|-------------|
| `observation_id` | INTEGER (PK) | Observation identifier |
| `person_id` | INTEGER | Links to `person.person_id` |
| `visit_occurrence_id` | INTEGER | Links to `visit_occurrence.visit_occurrence_id` |
| `observation_concept_id` | INTEGER | Type of observation |
| `observation_type_concept_id` | INTEGER | How observation was recorded |
| `observation_datetime` | TIMESTAMP | When observation was recorded |
| `value_as_string` | VARCHAR | String value (used for AI score, symptom values) |
| `value_as_number` | FLOAT | Numeric value |
| `value_as_concept_id` | INTEGER | Coded value (resolves to concept name) |
| `unit_concept_id` | INTEGER | Unit of measurement |
| `qualifier_concept_id` | INTEGER | Qualifier (e.g., negation) |
| `unit_source_value` | VARCHAR | Original unit string from source |

---

### `measurement`

| Column | PostgreSQL Type | Description |
|--------|----------------|-------------|
| `measurement_id` | INTEGER (PK) | Measurement identifier |
| `person_id` | INTEGER | Links to `person.person_id` |
| `visit_occurrence_id` | INTEGER | Links to `visit_occurrence.visit_occurrence_id` |
| `measurement_concept_id` | INTEGER | Type of measurement |
| `measurement_datetime` | TIMESTAMP | When measurement was taken |
| `value_as_number` | FLOAT | Numeric measurement value |
| `value_as_concept_id` | INTEGER | Coded result |
| `unit_concept_id` | INTEGER | Unit of measurement |
| `operator_concept_id` | INTEGER | Relational operator (e.g., greater than) |
| `unit_source_value` | VARCHAR | Original unit string |

**Special handling:** Measurement concept ID `40490382` (BMI) is converted from numeric percentile to categorical display (Underweight/Normal/Overweight/Obese) by the case service.

---

### `drug_exposure`

| Column | PostgreSQL Type | Description |
|--------|----------------|-------------|
| `drug_exposure_id` | INTEGER (PK) | Drug exposure identifier |
| `person_id` | INTEGER | Links to `person.person_id` |
| `visit_occurrence_id` | INTEGER | Links to `visit_occurrence.visit_occurrence_id` |
| `drug_concept_id` | INTEGER | OMOP drug concept |
| `drug_exposure_start_date` | DATE | Start date |
| `drug_exposure_end_date` | DATE | End date |

---

### `concept`

The OMOP vocabulary table — maps concept IDs to human-readable names.

| Column | PostgreSQL Type | Description |
|--------|----------------|-------------|
| `concept_id` | INTEGER (PK) | Numeric concept identifier |
| `concept_name` | VARCHAR | Human-readable name displayed in the UI |
| `domain_id` | VARCHAR | Domain (e.g., "Observation", "Drug", "Measurement", "Gender") |
| `vocabulary_id` | VARCHAR | Source vocabulary (e.g., "SNOMED", "RxNorm") |
| `concept_class_id` | VARCHAR | Concept class |
| `standard_concept` | VARCHAR | 'S' for standard OMOP concepts |
| `concept_code` | VARCHAR | Source code |
| `valid_start_date` | DATE | When this concept became valid |
| `valid_end_date` | DATE | When this concept expires |
| `invalid_reason` | VARCHAR | Why the concept is invalid, if applicable |

---

## Key Concept IDs Reference

| Concept ID | Concept Name | Domain | Used For |
|-----------|-------------|--------|---------|
| *(study-specific)* | AI prediction observation | Observation | Study-specific AI model output |
| 8507 | MALE | Gender | Male gender |
| 8532 | FEMALE | Gender | Female gender |
| 40490382 | BMI (body mass index) centile | Measurement | BMI, displayed as range |

## Related Documentation

- [Database](../admin-guide/database.md) — Schema overview with ER relationships
- [OMOP Mapping](omop-mapping.md) — How concept IDs map to displayed clinical sections
- [Exporting Data](../researcher-guide/exporting-data.md) — Export CSV column definitions
