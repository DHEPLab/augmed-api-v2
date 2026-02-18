# Adaptive Experiments Overview

AugMed supports **adaptive experimentation** through a reinforcement learning (RL) feedback loop that automatically adjusts which clinical information is shown to participants based on their performance.

## What Is Adaptive Experimentation?

In a traditional A/B test, participants are randomly assigned to fixed arms for the duration of the study. Adaptive experimentation changes this: the system learns which arms produce better outcomes and shifts allocation toward the better-performing conditions over time.

AugMed uses **Thompson Sampling**, a multi-armed bandit algorithm, to balance:

- **Exploration** — trying all arms to gather information
- **Exploitation** — favoring arms that have historically performed better

## How It Works

```
1. Clinicians complete case reviews
      ↓
2. RL service fetches completed answers via Export API
      ↓
3. Reward calculator scores each response
   (accuracy vs ground truth + time efficiency)
      ↓
4. Thompson Sampling updates arm weights
      ↓
5. New display configurations are generated
   (proportional to updated weights)
      ↓
6. Configurations are written back via Batch Config API
      ↓
7. Next clinician sees cases with updated feature display
```

Each cycle processes all new answers since the last run and generates fresh assignments for all participants in the experiment's case pool.

## Key Concepts

### Arms

An **arm** defines a set of clinical features to display. For example:

- **Control arm**: Shows only Demographics
- **Treatment arm**: Shows Demographics + Lab Results + AI Risk Score

Arms are defined when creating an experiment and stay fixed throughout.

### Reward Function

The reward function converts a clinician's response into a scalar score (0 to 1). The default reward combines:

| Component | Weight | Description |
|-----------|--------|-------------|
| Accuracy | 70% | How closely the response matches ground truth |
| Time Efficiency | 30% | Faster completion is better (capped at 10 minutes) |

Reward weights are configurable per experiment.

### Thompson Sampling

Thompson Sampling maintains a **Beta distribution** for each arm, parameterized by successes and failures. Each cycle:

1. Sample from each arm's posterior distribution
2. Compute allocation weights from samples
3. Assign participants proportionally to weights

Arms with higher observed rewards get assigned more frequently, while underperforming arms are still occasionally selected to ensure continued learning.

## Architecture

The RL system consists of three components:

| Component | Location | Role |
|-----------|----------|------|
| Export API | `augmed-api` (`/api/v1/export/*`) | Provides answer data for reward computation |
| RL Service | `augmed-rl` (`/api/rl/v1/*`) | Runs the bandit algorithm and generates configs |
| Experiment API | `augmed-api` (`/api/v1/experiments/*`) | Manages experiment metadata and run history |

The RL service is a standalone FastAPI application that communicates with the main API via HTTP.

## When to Use Adaptive Experiments

Adaptive experiments are appropriate when:

- You have **multiple arms** to compare (2+)
- The study has **enough participants** for meaningful signal (20+ per arm)
- You want to **minimize exposure** to inferior conditions
- The **outcome is measurable** within each case review session

For studies with very few participants or where all arms must receive equal exposure (e.g., for regulatory requirements), use the standard static randomization instead.

## Next Steps

- [Setting Up an Adaptive Experiment](setting-up-rl.md)
- [Interpreting RL Results](interpreting-results.md)
