# Setting Up an Adaptive Experiment

This guide walks you through creating and running an adaptive experiment using the RL feedback loop.

## Prerequisites

- An active AugMed deployment with the Export API enabled
- The `augmed-rl` service deployed and configured
- Clinical cases loaded in OMOP format
- Ground truth answers (optional, improves reward quality)

## Step 1: Define Your Arms

Decide which clinical feature combinations you want to test. Each arm specifies a set of OMOP feature paths to display.

**Example arms:**

```json
[
  {
    "name": "control",
    "path_config": [
      { "path": "BACKGROUND.Demographics" }
    ]
  },
  {
    "name": "treatment_labs",
    "path_config": [
      { "path": "BACKGROUND.Demographics" },
      { "path": "BACKGROUND.Labs" }
    ]
  },
  {
    "name": "treatment_full",
    "path_config": [
      { "path": "BACKGROUND.Demographics" },
      { "path": "BACKGROUND.Labs" },
      { "path": "BACKGROUND.Medications" }
    ]
  }
]
```

## Step 2: Define Your Case Pool

The case pool specifies which participant-case combinations should receive adaptive assignments.

```json
[
  { "user_email": "clinician1@hospital.org", "case_id": 101 },
  { "user_email": "clinician1@hospital.org", "case_id": 102 },
  { "user_email": "clinician2@hospital.org", "case_id": 101 },
  { "user_email": "clinician2@hospital.org", "case_id": 102 }
]
```

Each entry represents one assignment slot. The RL system will assign each slot to an arm based on current weights.

## Step 3: Create the Experiment

### Via Admin Panel

1. Navigate to `/admin/rl` in the AugMed web app
2. Click **New Experiment**
3. Fill in the experiment name and description
4. Define arms and case pool
5. Click **Create**

### Via API

```bash
curl -X POST https://augmed.dhep.org/api/v1/experiments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI Risk Display Study - Phase 2",
    "description": "Testing impact of additional lab data on diagnostic accuracy",
    "arms": [
      { "name": "control", "path_config": [{"path": "BACKGROUND.Demographics"}] },
      { "name": "treatment", "path_config": [{"path": "BACKGROUND.Demographics"}, {"path": "BACKGROUND.Labs"}] }
    ],
    "case_pool": [
      { "user_email": "clinician1@hospital.org", "case_id": 101 },
      { "user_email": "clinician2@hospital.org", "case_id": 101 }
    ]
  }'
```

The API returns the experiment with a generated `experiment_id` (e.g., `exp-a1b2c3d4e5f6`).

## Step 4: Run the First RL Cycle

The first cycle uses uniform weights (equal allocation across arms) since no answer data exists yet.

### Via Admin Panel

1. Go to the experiment detail page (`/admin/rl/{experiment_id}`)
2. Click **Run Cycle Now**
3. Wait for the run to complete (typically < 30 seconds)
4. Verify configs were generated in the run history table

### Via API

```bash
curl -X POST https://augmed.dhep.org/api/v1/experiments/exp-a1b2c3d4e5f6/runs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"triggered_by": "manual"}'
```

## Step 5: Monitor Progress

### Check Run History

Each run records:
- **Answers consumed**: How many new responses were processed
- **Configs generated**: How many new assignments were created
- **Status**: pending, completed, or failed

### Check Current Weights

After several cycles, arm weights will diverge from uniform. You can see the current allocation by checking the most recent run's parameters.

## Step 6: Automated Scheduling (Optional)

For production use, configure the RL service to run automatically:

- **Daily cron**: EventBridge rule triggers the RL cycle once per day
- **Batch size**: Each cycle processes all new answers since the last run
- **No manual intervention needed** once configured

## Pausing and Resuming

### Pause an Experiment

Pausing prevents new RL cycles from generating configs. Existing assignments remain active.

```bash
curl -X PATCH https://augmed.dhep.org/api/v1/experiments/exp-a1b2c3d4e5f6/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'
```

### Resume

```bash
curl -X PATCH https://augmed.dhep.org/api/v1/experiments/exp-a1b2c3d4e5f6/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

## Reward Configuration

The default reward function uses 70% accuracy / 30% time efficiency. To customize:

```json
{
  "run_params": {
    "reward_config": {
      "accuracy_weight": 0.8,
      "time_weight": 0.2,
      "max_time_secs": 900
    }
  }
}
```

Pass custom `run_params` when triggering a cycle to override defaults for that run.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Cycle generates 0 configs | Empty case pool | Add case pool entries to the experiment |
| All arms get equal weight | Not enough data | Run more cases before the next cycle |
| Cycle fails | RL service can't reach API | Check network/API key configuration |
| Configs not appearing | Experiment paused | Resume the experiment before running a cycle |

## Next Steps

- [Interpreting RL Results](interpreting-results.md)
- [Exporting Data](../researcher-guide/exporting-data.md) for analysis
