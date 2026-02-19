# Analyzing Results

This guide provides example code for common analyses using the AugMed export CSV. Both R and Python examples are provided.

## Before You Start

Obtain the export CSV by running the export script:

```bash
cd script/answer_export
python export_answers_to_csv.py
```

The output file will be named `answers_data_YYYYMMDD_HHMMSS.csv`. Rename it to something descriptive for your analysis (e.g., `augmed_study1_data.csv`).

See [Exporting Data](exporting-data.md) for a full description of all columns.

## Key Variables

The most important analysis variables are:

- **Treatment indicator**: `ai_score (shown)` — "Yes" if participant saw the AI score, "No" if not
- **AI score value**: `ai_score (value)` — the numeric AI prediction score
- **Primary outcome**: study-specific response columns from your answer config
- **Secondary outcome**: study-specific response columns from your answer config
- **Timing**: `total_duration_secs` — seconds from case open to submission
- **Order effect**: `order_id` — sequential case number for this participant
- **Patient features**: `Family History.*`, `Medical History.*` columns — ground truth patient values
- **Feature visibility**: `*.*(shown)` columns — which features were visible to the participant

## R Examples

### Load and Prepare Data

```r
library(tidyverse)

# Load data
df <- read_csv("augmed_study1_data.csv")

# Convert types
df <- df %>%
  mutate(
    ai_shown = (ai_score_shown == "Yes"),
    risk_assessment = as.integer(risk_assessment),
    total_duration_mins = total_duration_secs / 60,

    # Create factor for categorical outcome (customize levels for your study)
    outcome_factor = factor(primary_outcome,
      levels = c("Level 1", "Level 2", "Level 3"))
  )

# Quick summary
summary(df)
```

Note: Column names with spaces and parentheses need backticks in R:

```r
# Access columns with special characters
df$`ai_score (shown)`
df$`Family History.Cancer (shown)`
```

Or rename them at import:

```r
df <- read_csv("augmed_study1_data.csv") %>%
  rename(
    ai_shown_flag = `ai_score (shown)`,
    ai_score_value = `ai_score (value)`,
    fh_cancer_shown = `Family History.Cancer (shown)`,
    mh_fatigue_shown = `Medical History.Fatigue (shown)`
  )
```

### Descriptive Statistics

```r
# Completion by arm
df %>%
  group_by(ai_shown) %>%
  summarize(
    n_responses = n(),
    n_participants = n_distinct(user_id),
    n_cases = n_distinct(person_id),
    mean_risk = mean(risk_assessment, na.rm = TRUE),
    sd_risk = sd(risk_assessment, na.rm = TRUE)
  )

# Distribution of risk assessments
df %>%
  count(risk_assessment) %>%
  mutate(pct = round(100 * n / sum(n), 1))

# Average review time by arm
df %>%
  group_by(ai_shown) %>%
  summarize(
    mean_duration_secs = mean(total_duration_secs, na.rm = TRUE),
    median_duration_secs = median(total_duration_secs, na.rm = TRUE)
  )
```

### Primary Analysis: Effect of AI Score on Risk Assessment

```r
# OLS with participant and case fixed effects
library(lfe)

model_ols <- felm(
  risk_assessment ~ ai_shown | user_id + person_id | 0 | user_id,
  data = df
)
summary(model_ols)

# Ordinal logistic regression (no fixed effects)
library(MASS)
df$risk_factor <- as.ordered(df$risk_assessment)
model_ord <- polr(risk_factor ~ ai_shown, data = df, Hess = TRUE)
summary(model_ord)
```

### Effect of AI Score Value on Risk Assessment

For participants who were shown the AI score, test whether the score magnitude influenced their risk assessment:

```r
ai_shown_df <- df %>%
  filter(ai_shown == TRUE, !is.na(ai_score_value))

model_ai_value <- lm(
  risk_assessment ~ ai_score_value + age + gender,
  data = ai_shown_df
)
summary(model_ai_value)
```

### Feature Shown/Value Analysis

Test whether showing a specific feature (e.g., blood stained stool) influences risk assessment:

```r
# Effect of showing rectal bleeding on risk
model_feature <- lm(
  risk_assessment ~
    `Medical History.Rectal Bleeding (shown)` +
    `Medical History.Rectal Bleeding (value)` +
    ai_shown + age + gender,
  data = df
)
summary(model_feature)
```

### Categorical Outcome Analysis

```r
# Proportion selecting a specific response by arm
df %>%
  mutate(selected_option = (primary_outcome == "Target Option")) %>%
  group_by(ai_shown) %>%
  summarize(
    pct_selected = mean(selected_option, na.rm = TRUE),
    n = n()
  )

# Chi-square test for independence
table_recs <- table(df$primary_outcome, df$ai_shown)
chisq.test(table_recs)
```

> **Example:** For CRC-specific analysis code (colonoscopy recommendation rates, screening factor levels), see [CRC Experiment Config](../examples/crc-screening/experiment-config.md).

## Python Examples

### Load and Prepare Data

```python
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv("augmed_study1_data.csv")

# Rename columns with special characters for easier access
rename_map = {
    "ai_score (shown)": "ai_shown",
    "ai_score (value)": "ai_score_value",
}

# Rename all feature columns
for col in df.columns:
    if " (shown)" in col:
        new_name = col.replace(" (shown)", "_shown").replace(".", "_").replace("/", "_")
        rename_map[col] = new_name
    elif " (value)" in col:
        new_name = col.replace(" (value)", "_value").replace(".", "_").replace("/", "_")
        rename_map[col] = new_name

df = df.rename(columns=rename_map)

# Convert types
df["ai_shown_bool"] = df["ai_shown"] == "Yes"
df["total_duration_mins"] = df["total_duration_secs"] / 60
df["risk_assessment"] = pd.to_numeric(df["risk_assessment"], errors="coerce")

print(f"Rows: {len(df)}")
print(f"Unique participants: {df['user_id'].nunique()}")
print(f"Unique cases: {df['person_id'].nunique()}")
```

### Descriptive Statistics

```python
# Summary by arm
summary = (
    df
    .groupby("ai_shown_bool")
    .agg(
        n_responses=("risk_assessment", "count"),
        n_participants=("user_id", "nunique"),
        mean_risk=("risk_assessment", "mean"),
        sd_risk=("risk_assessment", "std"),
        mean_duration_secs=("total_duration_secs", "mean")
    )
    .round(2)
)
print(summary)

# Risk assessment distribution
print(df["risk_assessment"].value_counts(normalize=True).sort_index().mul(100).round(1))
```

### Primary Analysis: OLS with Fixed Effects

```python
from linearmodels import PanelOLS
import statsmodels.api as sm

# Two-way fixed effects (participant + case)
df_panel = df.set_index(["user_id", "person_id"])
model = PanelOLS(
    df_panel["risk_assessment"],
    sm.add_constant(df_panel[["ai_shown_bool"]]),
    entity_effects=True,
    time_effects=True
)
result = model.fit(cov_type="clustered", cluster_entity=True)
print(result.summary)
```

### Visualization

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Distribution of risk assessments by arm
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for i, (arm_label, arm_bool) in enumerate([("No AI Score", False), ("AI Score Shown", True)]):
    arm_df = df[df["ai_shown_bool"] == arm_bool]
    counts = arm_df["risk_assessment"].value_counts().sort_index()
    axes[i].bar(counts.index, counts.values)
    axes[i].set_title(arm_label)
    axes[i].set_xlabel("Risk Assessment (1=Very Low, 5=Very High)")
    axes[i].set_ylabel("Count")

plt.tight_layout()
plt.savefig("risk_distribution_by_arm.png", dpi=150)
plt.show()

# Average review time by case order
timing_by_order = df.groupby("order_id")["total_duration_mins"].mean()
plt.figure(figsize=(10, 4))
plt.plot(timing_by_order.index, timing_by_order.values, marker="o")
plt.xlabel("Case Order (1 = first case reviewed)")
plt.ylabel("Average Duration (minutes)")
plt.title("Review Time by Case Order")
plt.grid(True)
plt.savefig("timing_by_order.png", dpi=150)
plt.show()
```

## Working with Feature Columns

The feature shown/value columns follow a consistent naming convention. After renaming, you can work with them programmatically:

```python
# Get all "shown" feature columns
shown_cols = [c for c in df.columns if c.endswith("_shown") and c != "ai_shown"]

# Compute how many features each participant saw per case
df["n_features_shown"] = df[shown_cols].apply(
    lambda row: row.astype(str).str.lower().isin(["true", "yes"]).sum(),
    axis=1
)

# Correlation between number of features shown and risk assessment
print(df[["n_features_shown", "risk_assessment"]].corr())
```

## Study-Specific Analysis

For study-specific analysis scripts, create a dedicated analysis repository with:
- Study-specific data handling procedures
- IRB-approved analysis plans
- Pre-registered analysis code

## Related Documentation

- [Exporting Data](exporting-data.md) — How to produce the export CSV
- [Data Dictionary](../reference/data-dictionary.md) — Column definitions
- [Terminology](../getting-started/terminology.md) — Key concepts
