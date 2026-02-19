# Terminology Glossary

This glossary defines the key terms used throughout AugMed documentation, the API, and the database.

---

## Case

A de-identified clinical encounter presented to participants for review. In the database, a case corresponds to a single `visit_occurrence` record. The `case_id` used throughout the system is the `visit_occurrence_id`.

A case is associated with one patient (person) and contains clinical data recorded during that visit — including observations, measurements, drug exposures, and chief complaints.

Example: "Participant reviewed Case 17" means they reviewed the patient visit with `visit_occurrence_id = 17`.

---

## Person (Patient)

A de-identified patient stored in the OMOP `person` table. Persons are identified by `person_id`. Demographic information — year of birth, gender — is stored directly on the person record. A person may be associated with one or more visits (cases).

In the export data, `person_id` identifies the patient, while `user_id` identifies the research participant reviewing the case.

---

## Visit

A clinical encounter stored in the `visit_occurrence` table. Each visit has a `visit_start_date`, a `person_id`, and a `visit_occurrence_id`. In AugMed, one visit equals one case.

---

## Display Config

A record in the `display_config` table that defines exactly what clinical information a specific participant sees for a specific case. Each display config contains:

- `user_email` — the participant's email address
- `case_id` — the `visit_occurrence_id` of the case
- `path_config` — a JSON array of path entries, each specifying a clinical feature to show and optional display styling

Display configs are created by uploading a CSV file via the admin API. When a participant opens a case, the system looks up their display config and uses it to filter and present only the specified clinical features.

---

## Path Config

The JSON array within a display config that lists which clinical data to show. Each entry is an object with:

- `path` — a dot-separated string identifying a clinical feature (e.g., `BACKGROUND.Medical History.Fatigue: Yes`)
- `style` (optional) — display directives:
  - `collapse: true/false` — whether to collapse this section by default
  - `highlight: true/false` — whether to visually highlight this item
  - `top: <number>` — pins this item to a "key findings" panel, with lower numbers shown first

Path strings follow a hierarchical structure: `{Section}.{Category}.{Feature}: {Value}` for background features, or `RISK ASSESSMENT.{AI Section Name}` to show the AI score section.

---

## Answer Config

A record in the `answer_config` table that defines the questionnaire participants complete for each case. There is typically one active answer config at a time, and all participants use the same questionnaire.

The config is a JSON array of question objects. Each question has:
- `type` — `"Text"`, `"Paragraph"`, `"SingleChoice"`, or `"MultipleChoice"`
- `title` — the question text shown to participants
- `options` — array of choices (for choice questions)
- `required` — whether the question must be answered

---

## Arm

An experimental condition in the study design. AugMed does not store arms as a formal database entity — arms are defined implicitly by the display config assignments. Participants are in the same "arm" if they receive the same pattern of clinical feature visibility across their assigned cases.

Common arm designs:
- **AI shown arm**: display configs include the AI prediction path (e.g., `RISK ASSESSMENT.{Your AI Section}`)
- **AI not shown arm**: display configs do not include that path
- **Feature variation arms**: different subsets of clinical history features are shown

> **Example:** In the CRC screening study, the AI path was `RISK ASSESSMENT.CRC risk assessments`. See [CRC Screening Example](../examples/crc-screening/terminology.md) for details.

---

## Experiment

A complete research study conducted on AugMed. An experiment encompasses: the set of cases loaded into the database, the answer config (questionnaire), the participant roster (users), the display config assignments (which operationalize the arm assignments), and the resulting answer and analytics data.

---

## AI Score

A machine-learning-generated prediction stored in the OMOP `observation` table. The AI score is a study-specific concept — researchers define which OMOP concept ID represents the AI output and how it is formatted. Whether a participant sees the AI score for a given case is controlled by including the corresponding `RISK ASSESSMENT.*` path in their display config.

In export data, `ai_score (shown)` records whether the score was visible to the participant, and `ai_score (value)` records the numeric score value.

> **Example:** In the CRC screening study, the AI score used concept ID `45614722`, stored as `"Colorectal Cancer Score: {value}"`, with risk categories Low (<6), Medium (6-11), High (>11). See [CRC Terminology](../examples/crc-screening/terminology.md).

---

## OMOP CDM

The **Observational Medical Outcomes Partnership Common Data Model (OMOP CDM)** is a standardized schema for electronic health record data. It uses numeric concept IDs from a controlled vocabulary to represent clinical entities — diagnoses, medications, lab values, observations, and more.

AugMed stores all patient clinical data in OMOP tables (`person`, `visit_occurrence`, `observation`, `measurement`, `drug_exposure`, `concept`, etc.). This allows data from different healthcare sources to be used without modifying the application.

---

## Concept ID

An integer that uniquely identifies a clinical entity in the OMOP vocabulary. Concept IDs are resolved to human-readable names via the `concept` table.

Common concept IDs used in AugMed:

| Concept ID | Description |
|-----------|-------------|
| 8507 | Male gender |
| 8532 | Female gender |

The `concept` table stores the full vocabulary. Researchers can query it to find concept IDs for clinical features they want to include in their page configuration. AI score concept IDs are study-specific — see [CRC Terminology](../examples/crc-screening/terminology.md) for an example mapping.

---

## Order ID

In the export data, `order_id` is a sequential integer (1, 2, 3, ...) indicating which case this was for a given participant — i.e., their first case reviewed, second case reviewed, and so on. This allows researchers to study order effects and learning curves.

---

## Task ID

In the `answer` table, `task_id` corresponds to the `display_config.id` (a UUID string) for the specific case configuration. The `task_id` links an answer record back to the exact display config used when the participant reviewed that case.

---

## Person ID vs. User ID

These two identifiers are easy to confuse:

- **`person_id`** — identifies the *patient* in the OMOP database. This is the real clinical record identifier.
- **`user_id`** — identifies the *research participant* (clinician) reviewing the case. In export data, `user_id` is a stable anonymized integer derived from the participant's email address (via SHA-256 hash). The raw `user_email` is not included in exports to protect participant privacy.
