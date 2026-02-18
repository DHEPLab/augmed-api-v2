# Interpreting RL Results

This guide explains how to read and analyze the output of adaptive experiments.

## Understanding Arm Weights

After each RL cycle, Thompson Sampling produces **allocation weights** for each arm. These weights reflect the algorithm's current belief about each arm's relative performance.

**Example output:**

```json
{
  "weights": {
    "control": 0.25,
    "treatment_labs": 0.45,
    "treatment_full": 0.30
  }
}
```

This means:
- 25% of new assignments go to the control arm
- 45% go to the labs treatment arm (currently favored)
- 30% go to the full treatment arm

### What the Weights Mean

- **Higher weight = better observed performance** on the reward metric
- **Weights shift gradually** — a single cycle won't cause dramatic changes
- **Early cycles** produce weights close to uniform (not enough data to differentiate)
- **Weights never reach 0** — Thompson Sampling always explores all arms

### When to Trust the Weights

| Condition | Reliability |
|-----------|------------|
| < 10 responses per arm | Low — weights are mostly noise |
| 10-50 responses per arm | Moderate — trends are emerging |
| 50+ responses per arm | High — weights reflect real performance differences |

## Reward Scores

Each clinician response receives a reward score between 0 and 1.

### Default Reward Components

**Accuracy (70% weight):**
- Compares the clinician's answer to ground truth
- Exact match on all fields = 1.0
- Partial match = proportion of matching fields
- No ground truth available = 1.0 (assumes correct)

**Time Efficiency (30% weight):**
- `1 - (duration / max_time)` where max_time defaults to 600 seconds
- Faster responses score higher
- Responses over max_time get 0 for this component
- Missing duration data uses max_time (conservative estimate)

### Example Reward Calculations

| Accuracy | Duration | Reward |
|----------|----------|--------|
| 1.0 (exact match) | 60s | 0.7 × 1.0 + 0.3 × 0.9 = **0.97** |
| 0.5 (partial match) | 120s | 0.7 × 0.5 + 0.3 × 0.8 = **0.59** |
| 0.0 (wrong) | 300s | 0.7 × 0.0 + 0.3 × 0.5 = **0.15** |

## Analyzing Run History

### Key Metrics Per Run

| Metric | Description |
|--------|-------------|
| `answers_consumed` | New responses processed since last run |
| `configs_generated` | New assignments created |
| `started_at` / `completed_at` | Run timing |
| `triggered_by` | `manual`, `admin_panel`, or `scheduled` |

### Trends to Watch

1. **Answers consumed decreasing**: Participants are completing fewer cases — may indicate fatigue or technical issues
2. **Configs generated = 0**: Case pool is empty or experiment is paused
3. **Weights converging**: One arm is clearly outperforming — consider ending the experiment early
4. **Weights staying uniform**: No detectable difference between arms after many cycles

## Exporting Data for Analysis

### Export Answer Data

```bash
curl "https://augmed.dhep.org/api/v1/export/answers?since=2025-01-01" \
  -H "X-API-Key: YOUR_EXPORT_KEY" \
  -H "Accept: text/csv"
```

The export includes:
- `arm`: Which arm the participant was assigned to
- `experiment_id`: Links back to the experiment
- `rl_run_id`: Which RL cycle generated the assignment
- `answer`: The clinician's response
- `total_duration_secs`: Time spent on the case

### Analyzing in R

```r
library(tidyverse)

answers <- read_csv("export.csv")

# Compare accuracy across arms
answers %>%
  group_by(arm) %>%
  summarize(
    n = n(),
    mean_duration = mean(total_duration_secs, na.rm = TRUE),
    .groups = "drop"
  )

# Track weight evolution over time
# (Requires joining with RL run data)
```

### Analyzing in Python

```python
import pandas as pd

answers = pd.read_csv("export.csv")

# Basic arm comparison
summary = answers.groupby("arm").agg(
    count=("answer_id", "count"),
    mean_duration=("total_duration_secs", "mean"),
).reset_index()

print(summary)
```

## Statistical Considerations

### Sample Size

Thompson Sampling works with small samples but produces more reliable results with larger ones. As a rule of thumb:

- **Minimum**: 10 responses per arm before weights become meaningful
- **Recommended**: 50+ responses per arm for publication-quality results
- **Ideal**: 100+ responses per arm for robust inference

### Regret Analysis

Thompson Sampling minimizes **cumulative regret** — the total performance lost by not always choosing the best arm. After the experiment, you can calculate:

```
Regret = Σ (best_arm_mean - chosen_arm_reward)
```

Lower regret indicates the algorithm quickly identified and favored the best arm.

### Causal Inference

Because adaptive experiments change allocation over time, standard A/B test analysis (e.g., two-sample t-test) may be biased. For causal estimates, consider:

- **Inverse probability weighting (IPW)**: Weight each observation by 1/probability of assignment
- **Augmented IPW (AIPW)**: More efficient estimator combining IPW with outcome modeling
- **Bayesian posterior analysis**: Use the final Beta distributions directly

The allocation probability for each observation is deterministic given the run's weights and the participant's index, making IPW straightforward to compute.

## When to End an Experiment

Consider ending when:

1. **Clear winner**: One arm's weight exceeds 0.7 for 5+ consecutive cycles
2. **No difference**: Weights remain within 0.05 of uniform after 100+ responses per arm
3. **Sufficient data**: Enough responses collected for the planned analysis
4. **External factors**: Study timeline reached or IRB-specified stopping rules met

To end an experiment:

```bash
curl -X PATCH https://augmed.dhep.org/api/v1/experiments/exp-a1b2c3d4e5f6/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```
