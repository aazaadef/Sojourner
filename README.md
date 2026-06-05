# Sojourner under Sabotage — Research Artifact

**Paper:** *Teaching Software Testing and Debugging Through a Serious Game: An Empirical Classroom Study with Sojourner under Sabotage*

Submitted to **IEEE TALE 2026**, Pattaya, Thailand.

## Contents

| File/Folder | Description |
|---|---|
| `main.tex` | Full LaTeX source of the paper |
| `analysis.py` | Python replication script (statistics + figures) |
| `data_pre_questionnaire.csv` | Pre-session MCQ and self-confidence responses (N=22) |
| `data_post_questionnaire.csv` | Post-session questionnaire responses (N=21) |
| `telemetry.json` | In-game behavioral telemetry (3,161 events, 22 players) |
| `figures/` | PDF figures used in the paper |

## Reproducing Results

```bash
pip install matplotlib numpy scipy
python analysis.py
```

Outputs Wilcoxon signed-rank test results, Spearman correlations, effect sizes, and regenerates all figures.

## Participants

- N = 22 master's students (Universidade da Beira Interior, Portugal)
- N = 21 post-session responses
- N = 20 matched pre/post pairs used in paired analyses
- N = 21 matched telemetry + survey pairs used in correlation analysis

## Research Questions

- **RQ1:** To what extent does the game improve students' conceptual understanding and self-assessed confidence in software testing and debugging?
- **RQ2:** How do students perceive the game in terms of engagement, perceived learning, usability, and cognitive load?
- **RQ3:** What behavioral patterns emerge from the game's telemetry, and how do they relate to learning outcomes?

## Key Results

| Metric | Value |
|---|---|
| MCQ pre mean | 8.29 / 11 |
| MCQ post mean | 9.14 / 11 |
| Normalized gain (low-baseline) | 0.50 |
| Spearman ρ (progression vs. MCQ gain) | 0.549 (p = 0.006) |
| Spearman ρ (progression vs. test executions) | 0.912 (p < 0.001) |
| Total telemetry events | 3,161 |
| Perceived learning | 4.06 / 5 |
| Engagement | 4.05 / 5 |
| Usability | 4.24 / 5 |

## Game

[Sojourner under Sabotage](https://github.com/se2p/sojourner-under-sabotage) — browser-based serious game for teaching software testing and debugging.

## Institution

Universidade da Beira Interior, Covilhã, Portugal  
Supported by FCT project UIDB/50008/2020 and doctoral grant PRT/BD/155023/2023.
