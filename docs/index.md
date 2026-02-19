# AugMed Platform Documentation

## What is AugMed?

AugMed is a clinical case review platform built for the UNC-Chapel Hill DHEP Lab as part of the NIH AIM-AHEAD project. It supports research on AI-augmented medical decision-making by presenting clinicians with de-identified patient cases drawn from real electronic health record data (structured in the OMOP Common Data Model) and collecting their diagnostic assessments, risk ratings, and screening recommendations.

Each participant sees a carefully controlled subset of clinical information — determined by the researcher's experimental design — which may or may not include an AI-generated colorectal cancer (CRC) risk score. This controlled information disclosure is the core experimental mechanism: by varying which features each participant sees, researchers can measure how AI assistance, clinical history details, and other factors influence clinical judgment.

## Who This Documentation Is For

This documentation is written for:

- **Researchers** who want to design and run experiments using the platform, export data, and analyze results. No programming background is assumed for the researcher-facing guides.
- **Administrators** who manage deployment, database configuration, and system maintenance.
- **Developers** who need to understand the API, database schema, or extend the platform.

## Quick Links

### Deploy

- [One-Click Deploy (Railway)](getting-started/one-click-deploy.md) — Deploy in under 5 minutes, no technical setup required
- [Self-Hosted Deploy (Docker Compose)](getting-started/self-hosted-deploy.md) — Run on your own machine or server
- [Development Setup](getting-started/quick-start.md) — Set up a local development environment

### Getting Started

- [Platform Overview](getting-started/overview.md) — Architecture, how experiments work, key concepts
- [Quick Start Guide](getting-started/quick-start.md) — Set up a local development instance
- [Terminology Glossary](getting-started/terminology.md) — Definitions of all key terms

### Researcher Guide

- [Creating Experiments](researcher-guide/creating-experiments.md) — Design arms, build config files, upload assignments
- [Managing Participants](researcher-guide/managing-participants.md) — Bulk user creation, activation, monitoring
- [Monitoring Progress](researcher-guide/monitoring-progress.md) — Track completion rates and timing
- [Exporting Data](researcher-guide/exporting-data.md) — Run the export script, understand the CSV output
- [Analyzing Results](researcher-guide/analyzing-results.md) — R and Python examples for common analyses

### Admin Guide

- [Deployment](admin-guide/deployment.md) — AWS infrastructure, CI/CD, environment variables
- [Database](admin-guide/database.md) — Schema overview, key tables, relationships
- [Configuration](admin-guide/configuration.md) — System config, answer configs, display config format
- [Troubleshooting](admin-guide/troubleshooting.md) — Common issues, logs, health checks

### Adaptive Experiments (RL)

- [Overview](adaptive-experiments/overview.md) — How adaptive experimentation works with Thompson Sampling
- [Setting Up an Adaptive Experiment](adaptive-experiments/setting-up-rl.md) — Step-by-step guide to creating and running RL experiments
- [Interpreting Results](adaptive-experiments/interpreting-results.md) — Understanding arm weights, rewards, and statistical analysis

### Reference

- [API Reference](reference/api-reference.md) — All REST endpoints with request/response formats
- [Data Dictionary](reference/data-dictionary.md) — Every table and column with types and descriptions
- [Config CSV Format](reference/config-csv-format.md) — Detailed specification for display config uploads
- [OMOP Mapping](reference/omop-mapping.md) — How OMOP concept IDs map to displayed clinical features

---

## Live Site

The production instance of AugMed is available at: [https://augmed1.dhep.org/](https://augmed1.dhep.org/)

## Repositories

- **Backend API** (this repository): Flask + PostgreSQL
- **Frontend**: [augmed-app-v2](https://github.com/DHEPLab/augmed-app-v2) (React + TypeScript)
- **RL Service**: [augmed-rl](https://github.com/DHEPLab/augmed-rl) (FastAPI, Thompson Sampling)
- **Infrastructure**: [augmed-infra](https://github.com/DHEPLab/augmed-infra) (Terraform, AWS)
