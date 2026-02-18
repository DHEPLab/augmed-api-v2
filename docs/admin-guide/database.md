# Database

The AugMed database is PostgreSQL. It contains two categories of tables: application tables (users, configs, answers, analytics) and OMOP CDM tables (clinical data).

## Schema Overview

```
APPLICATION TABLES
══════════════════════════════════════════════════════════════════

user ──────────────── display_config ──────── answer
  │                        │    │               │
  │ (user_email)           │    │  (task_id)     │
  └────────────────────────┘    └───────────────┘
                                                 │
                            answer_config ───────┘
                              (answer_config_id)

analytics ──── display_config
  (case_config_id = display_config.id)

experiment ──── rl_run
  │ (experiment_id)    │
  │                    │
  └──── display_config ┘
    (experiment_id)  (rl_run_id)

system_config  (standalone — holds page_config JSON)

reset_password_token ──── user
  (user_email)

OMOP CDM TABLES
══════════════════════════════════════════════════════════════════

visit_occurrence ──── person
         │               │
         │ (visit_occurrence_id = case_id in app)
         │
         ├──── observation
         ├──── measurement
         ├──── drug_exposure
         └──── procedure_occurrence

concept  (vocabulary — maps concept_id to concept_name)
```

## Application Tables

### `user`

Stores research participant accounts.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer (PK, auto-increment) | Internal user identifier |
| `name` | varchar(128) | Participant's full name |
| `email` | varchar(128), unique | Participant's email address (primary lookup key) |
| `password` | varchar(192) | Hashed password |
| `salt` | varchar(192) | Password salt |
| `admin_flag` | boolean, default false | True for admin users |
| `position` | varchar(512) | Clinical role |
| `employer` | varchar(512) | Institution |
| `area_of_clinical_ex` | varchar(512) | Clinical specialty |
| `active` | boolean, default false | Must be true for login to succeed |
| `created_timestamp` | timestamp | Account creation time |
| `modified_timestamp` | timestamp | Last modification time |

---

### `display_config`

Defines which clinical features each participant sees for each case. One row = one participant-case assignment with full feature specification.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar (PK) | UUID string — this is the `task_id` / `case_config_id` used throughout the app |
| `user_email` | varchar | Participant's email (links to `user.email`) |
| `case_id` | integer | OMOP `visit_occurrence_id` |
| `path_config` | JSON | Array of path entries specifying visible features (see [Config CSV Format](../reference/config-csv-format.md)) |
| `experiment_id` | varchar(100), nullable | Links to `experiment.experiment_id` (set when created by RL service) |
| `rl_run_id` | integer, nullable | Links to `rl_run.id` (which RL cycle created this config) |
| `arm` | varchar(100), nullable | Which experiment arm this config belongs to |

**Relationships:**
- `display_config.user_email` → `user.email`
- `display_config.case_id` → `visit_occurrence.visit_occurrence_id`
- `display_config.id` → `answer.task_id`
- `display_config.id` → `analytics.case_config_id`
- `display_config.experiment_id` → `experiment.experiment_id` (nullable)
- `display_config.rl_run_id` → `rl_run.id` (nullable)

**Unique constraint:** There is one `display_config` row per `(user_email, case_id)` pair. Uploading a new config CSV replaces all existing rows.

---

### `answer`

Stores participant questionnaire responses. One row = one participant's completed questionnaire for one case.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer (PK, auto-increment) | Internal answer identifier |
| `task_id` | varchar | The `display_config.id` for this assignment |
| `case_id` | integer | OMOP `visit_occurrence_id` |
| `user_email` | varchar(128) | Participant's email |
| `display_configuration` | JSON | Snapshot of `path_config` at time of submission — preserves what was shown even if config changes |
| `answer_config_id` | UUID | Links to `answer_config.id` — which questionnaire version was used |
| `answer` | JSON | Participant's responses: `{question_title: response_value, ...}` |
| `ai_score_shown` | boolean | True if the AI CRC risk score was visible to this participant for this case |
| `created_timestamp` | timestamp | Submission time |
| `modified_timestamp` | timestamp | Last modification |

**Unique constraint:** `(task_id, case_id, user_email)` — one response per assignment.

---

### `answer_config`

Stores questionnaire definitions. Multiple versions may exist; the API uses the most recently created one.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Questionnaire version identifier |
| `config` | JSON | Array of question objects (see [Configuration](configuration.md)) |
| `created_timestamp` | timestamp | When this questionnaire version was created |

---

### `analytics`

Records timing data for each case review. One row = one completed case review session (linked to a `display_config`).

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer (PK, auto-increment) | Internal analytics identifier |
| `user_email` | varchar(128) | Participant's email |
| `case_config_id` | varchar | The `display_config.id` being reviewed |
| `case_id` | integer | OMOP `visit_occurrence_id` |
| `case_open_time` | timestamp with timezone | When participant opened the case |
| `answer_open_time` | timestamp with timezone | When participant opened the answer form |
| `answer_submit_time` | timestamp with timezone | When participant submitted answers |
| `to_answer_open_secs` | float | Seconds from case open to answer form open |
| `to_submit_secs` | float | Seconds from answer form open to submission |
| `total_duration_secs` | float | Total seconds from case open to submission |
| `created_timestamp` | timestamp with timezone | Row creation time |
| `modified_timestamp` | timestamp with timezone | Last modification |

**Unique constraint:** `(user_email, case_config_id)` — one analytics row per participant-assignment pair.

---

### `system_config`

Stores system-wide configuration as JSON. Currently used to store the page configuration (`page_config`) that maps OMOP concept IDs to displayed clinical sections.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(15) (PK) | Config key (e.g., `"page_config"`) |
| `json_config` | JSON | Configuration data |

The `page_config` entry maps each clinical section to concept IDs:

```json
{
  "BACKGROUND": {
    "Family History": [4167217],
    "Social History": {"Smoke": [4041306]},
    "Medical History": [1008364],
    "CRC risk assessments": [45614722]
  },
  "PATIENT COMPLAINT": {
    "Chief Complaint": [38000282]
  },
  "PHYSICAL EXAMINATION": {
    "Abdominal": [4152368]
  }
}
```

---

### `reset_password_token`

Stores temporary tokens for password reset flows.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar (PK) | Token identifier (returned to client, used to reset password) |
| `user_email` | varchar | Participant's email |
| `created_timestamp` | timestamp | Token creation time |

### `experiment`

Stores metadata for adaptive (RL) experiments. Each experiment defines a set of arms to compare and a pool of participant-case assignments.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer (PK, auto-increment) | Internal identifier |
| `experiment_id` | varchar(100), unique | Experiment identifier (format: `exp-{hex12}`) |
| `name` | varchar(200) | Human-readable experiment name |
| `description` | text, nullable | Experiment description |
| `status` | varchar(20), default 'active' | `active`, `paused`, `completed`, `archived` |
| `arms` | JSONB | Array of arm definitions (`[{name, path_config}, ...]`) |
| `case_pool` | JSONB, nullable | Array of `{user_email, case_id}` entries |
| `created_at` | timestamptz | Creation time |
| `updated_at` | timestamptz | Last update time |

---

### `rl_run`

Tracks individual RL cycle executions for an experiment.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer (PK, auto-increment) | Run identifier |
| `experiment_id` | varchar(100) | Links to `experiment.experiment_id` |
| `model_version` | varchar(100), nullable | Algorithm version used |
| `status` | varchar(20), default 'pending' | `pending`, `running`, `completed`, `failed` |
| `triggered_by` | varchar(50), nullable | `manual`, `admin_panel`, or `scheduled` |
| `configs_generated` | integer, nullable | Display configs created |
| `answers_consumed` | integer, nullable | Answers processed |
| `started_at` | timestamptz, nullable | Run start time |
| `completed_at` | timestamptz, nullable | Run end time |
| `run_params` | JSONB, nullable | Runtime parameters and reward config overrides |

---

## OMOP CDM Tables

### `person`

De-identified patient records.

| Column | Type | Description |
|--------|------|-------------|
| `person_id` | integer (PK) | Patient identifier |
| `gender_concept_id` | integer | OMOP concept ID for gender (8507=Male, 8532=Female) |
| `year_of_birth` | integer | Patient's birth year |
| `person_source_value` | varchar | Original source identifier (shown as "person ID" in the UI) |

### `visit_occurrence`

Clinical encounters (cases).

| Column | Type | Description |
|--------|------|-------------|
| `visit_occurrence_id` | integer (PK) | Visit identifier = AugMed `case_id` |
| `person_id` | integer | Links to `person.person_id` |
| `visit_start_date` | date | Date of the clinical visit |
| `visit_concept_id` | integer | Type of visit |

### `observation`

Clinical observations (symptoms, assessments, AI scores, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `observation_id` | integer (PK) | |
| `person_id` | integer | Links to `person.person_id` |
| `visit_occurrence_id` | integer | Links to `visit_occurrence.visit_occurrence_id` |
| `observation_concept_id` | integer | OMOP concept ID for the type of observation |
| `observation_type_concept_id` | integer | How the observation was recorded |
| `value_as_string` | varchar | String value (used for AI score: `"Colorectal Cancer Score: 12"`) |
| `value_as_number` | float | Numeric value |
| `value_as_concept_id` | integer | Coded value |
| `unit_concept_id` | integer | Unit of measurement |
| `qualifier_concept_id` | integer | Qualifier (e.g., "Yes", "No") |
| `observation_datetime` | timestamp | When the observation was recorded |

### `measurement`

Quantitative clinical measurements (vitals, labs).

| Column | Type | Description |
|--------|------|-------------|
| `measurement_id` | integer (PK) | |
| `person_id` | integer | |
| `visit_occurrence_id` | integer | |
| `measurement_concept_id` | integer | Type of measurement |
| `value_as_number` | float | Numeric measurement value |
| `value_as_concept_id` | integer | Coded result |
| `unit_concept_id` | integer | Unit |
| `operator_concept_id` | integer | Operator (e.g., ">", "<") |
| `unit_source_value` | varchar | Original unit string |

### `drug_exposure`

Medication records.

| Column | Type | Description |
|--------|------|-------------|
| `drug_exposure_id` | integer (PK) | |
| `person_id` | integer | |
| `visit_occurrence_id` | integer | |
| `drug_concept_id` | integer | OMOP drug concept |
| `drug_exposure_start_date` | date | Start date |

### `concept`

OMOP vocabulary — maps concept IDs to human-readable names.

| Column | Type | Description |
|--------|------|-------------|
| `concept_id` | integer (PK) | The numeric concept identifier |
| `concept_name` | varchar | Human-readable name shown in the UI |
| `domain_id` | varchar | Domain (e.g., "Observation", "Drug", "Measurement") |
| `vocabulary_id` | varchar | Source vocabulary |
| `concept_class_id` | varchar | Concept class |
| `standard_concept` | varchar | 'S' for standard concepts |

## Related Documentation

- [Data Dictionary](../reference/data-dictionary.md) — Exhaustive column-level documentation
- [OMOP Mapping](../reference/omop-mapping.md) — How concept IDs map to displayed clinical features
- [Configuration](configuration.md) — System config and answer config setup
