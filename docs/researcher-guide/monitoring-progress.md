# Monitoring Progress

This guide explains how to check completion rates, review timing data, and identify participants who need follow-up.

## Overview of Data Available

AugMed records two types of data as participants complete cases:

1. **Answer records** — the questionnaire responses submitted for each case
2. **Analytics records** — timing data: when the participant opened the case, when they opened the answer form, and when they submitted

Both are linked by `user_email` and `case_id` (or `case_config_id` for analytics). Use these tables together to monitor progress.

## Overall Completion Rate

Count how many cases have been completed across all participants:

```sql
SELECT
    COUNT(*) AS total_submissions,
    COUNT(DISTINCT user_email) AS participants_who_submitted,
    COUNT(DISTINCT case_id) AS unique_cases_reviewed
FROM answer;
```

Compare against total assignments:

```sql
SELECT
    (SELECT COUNT(*) FROM display_config) AS total_assignments,
    (SELECT COUNT(*) FROM answer) AS total_completions,
    ROUND(
        100.0 * (SELECT COUNT(*) FROM answer) /
        NULLIF((SELECT COUNT(*) FROM display_config), 0), 1
    ) AS completion_pct;
```

## Per-Participant Progress

```sql
SELECT
    dc.user_email,
    COUNT(DISTINCT dc.id) AS assigned,
    COUNT(DISTINCT a.id) AS completed,
    COUNT(DISTINCT dc.id) - COUNT(DISTINCT a.id) AS remaining,
    ROUND(
        100.0 * COUNT(DISTINCT a.id) /
        NULLIF(COUNT(DISTINCT dc.id), 0), 1
    ) AS pct_complete
FROM display_config dc
LEFT JOIN answer a
    ON a.task_id = dc.id
    AND a.user_email = dc.user_email
GROUP BY dc.user_email
ORDER BY pct_complete DESC;
```

## Timing Analytics

The `analytics` table records three timestamps per case review:

| Column | Description |
|--------|-------------|
| `case_open_time` | When the participant first opened the case |
| `answer_open_time` | When the participant opened the answer/questionnaire form |
| `answer_submit_time` | When the participant submitted their answers |

Derived columns (computed and stored by the API):

| Column | Formula |
|--------|---------|
| `to_answer_open_secs` | `answer_open_time - case_open_time` |
| `to_submit_secs` | `answer_submit_time - answer_open_time` |
| `total_duration_secs` | `answer_submit_time - case_open_time` |

### Average Time per Case

```sql
SELECT
    ROUND(AVG(to_answer_open_secs), 1) AS avg_case_review_secs,
    ROUND(AVG(to_submit_secs), 1) AS avg_answer_completion_secs,
    ROUND(AVG(total_duration_secs), 1) AS avg_total_duration_secs,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_duration_secs) AS median_duration_secs
FROM analytics;
```

### Unusually Fast Submissions

Identify submissions that may indicate inattentive responding (total duration under 60 seconds):

```sql
SELECT
    user_email,
    case_config_id,
    case_id,
    total_duration_secs,
    answer_submit_time
FROM analytics
WHERE total_duration_secs < 60
ORDER BY total_duration_secs ASC;
```

### Attention Check Performance

The system automatically inserts an attention check question every 10 cases per participant. Participants should select "All of the above" on this question. You can identify attention check failures by examining the answer JSON:

```sql
SELECT
    a.user_email,
    a.case_id,
    a.answer,
    a.created_timestamp
FROM answer a
WHERE a.answer::text LIKE '%Attention Check%'
   OR a.answer::text LIKE '%just clicking%';
```

!!! note
    The attention check is dynamically injected by the API and not stored in `answer_config`. It appears for the 10th, 20th, 30th, etc. case for each participant.

## Checking Answer Data

View raw answer submissions:

```sql
SELECT
    a.id,
    a.user_email,
    a.case_id,
    a.ai_score_shown,
    a.created_timestamp,
    a.answer
FROM answer a
ORDER BY a.created_timestamp DESC
LIMIT 20;
```

The `answer` column is a JSON object where keys are question titles and values are participant responses. For example:

```json
{
  "How would you assess this patient's risk level?": "Moderate Risk",
  "How confident are you in your assessment?": "2 - Somewhat Confident",
  "What would you recommend for this patient?": "Option A"
}
```

## Who Has Not Yet Started

Find participants with accounts and case assignments but no submissions:

```sql
SELECT
    u.email,
    u.name,
    u.active,
    COUNT(DISTINCT dc.id) AS cases_assigned
FROM "user" u
JOIN display_config dc ON dc.user_email = u.email
WHERE NOT EXISTS (
    SELECT 1 FROM answer a WHERE a.user_email = u.email
)
GROUP BY u.email, u.name, u.active
ORDER BY cases_assigned DESC;
```

## Export for Analysis

For full data export including all timing and response data joined together, use the export script. See [Exporting Data](exporting-data.md) for instructions.

## API Endpoint for Cases

Participants see their case list through `GET /api/cases` (requires JWT). This returns the participant's next incomplete case. You can monitor this indirectly by checking the `answer` table: a participant who has no remaining answers has completed all assigned cases.

## Related Documentation

- [Exporting Data](exporting-data.md) — Run the CSV export script for full analysis
- [Managing Participants](managing-participants.md) — Add participants, reset passwords
- [Data Dictionary](../reference/data-dictionary.md) — Full schema for analytics and answer tables
