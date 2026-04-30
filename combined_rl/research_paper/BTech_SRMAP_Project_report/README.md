# BTech SRMAP Project Report Update Guide

This README tracks what must be updated in this SRMAP-format report to match the latest capstone work on:
- MAVLink message prioritization
- Congestion-aware rate control
- RL-based combined scheduling and aggregation

## Report Path
`combined_rl/research_paper/BTech_SRMAP_Project_report/`

## Current Goal
Align this SRMAP report with the latest consolidated manuscript content from:
`combined_rl/research_paper/sn-article.tex`

## Baseline Paper (2021+ Free Access)
Use this as the primary baseline in the Literature Review and comparisons:

- Nguyen, T.-D., Pham Van, T., Le, D.-T., Choo, H.,
  **"Adaptive Clustering and Scheduling for UAV-Enabled Data Aggregation"**,
  *Electronics*, 2024, 13(16):3322.
  DOI: `10.3390/electronics13163322`
  Open Access: `https://www.mdpi.com/2079-9292/13/16/3322`

Optional supporting paper for RL-style scheduling discussion:
- Wang, S., Luo, Z.,
  **"Real-Time Data Collection and Trajectory Scheduling Using a DRL-Lagrangian Framework in Multiple UAVs Collaborative Communication Systems"**,
  *Remote Sensing*, 2024, 16(23):4378.
  DOI: `10.3390/rs16234378`

## File-Wise Update Plan

### 1) Abstract
File: `abstract.tex`
- Add the complete combined-model story (ML + congestion control + RL scheduling/aggregation).
- Include headline outcomes (PDR gain, packet-drop reduction, classifier performance).

### 2) Chapter 1 - Introduction
File: `chapters/chapter_1.tex`
- Update objectives and contributions to include scheduling + aggregation + combined model.
- Add final organization of chapters.

### 3) Chapter 3 - Literature Review
File: `chapters/chapter_3.tex`
- Add a dedicated baseline subsection for ACS (Nguyen et al., 2024).
- Add a comparison table: baseline vs proposed model.
- Clarify research gap: MAVLink semantic prioritization + congestion adaptation + RL joint decision policy.

### 4) Chapter 4 - Design and Methodology
File: `chapters/chapter_4.tex`
- Add RL formulation details:
  - state space
  - action encoding (queue choice + aggregation level)
  - reward terms
  - Q-learning algorithm
- Update workflow figure/text to show the full combined pipeline.

### 5) Chapter 5 - Implementation
File: `chapters/chapter_5.tex`
- Add RL training configuration (alpha, gamma, epsilon, episodes, state/action size).
- Add state discretization buckets and Q-table details.
- Keep implementation reproducibility details explicit.

### 6) Chapter 7 - Results and Discussion
File: `chapters/chapter_7.tex`
- Replace older metrics with latest final metrics from `sn-article.tex`.
- Keep FIFO vs proposed comparison consistent and non-contradictory.
- Add interpretation for trade-offs (throughput vs reliability).

### 7) Chapter 8 - Conclusion and Future Work
File: `chapters/chapter_8.tex`
- Rewrite conclusion around integrated combined framework.
- Add practical future work: hardware validation, multi-UAV scenarios, dynamic priority adaptation.

### 8) References
File: `references.tex`
- Add baseline paper and any new 2021+ references used in added sections.
- Ensure citation keys match chapter usage.

### 9) Front Matter Metadata
File: `BTechProjectTemplate.tex`
- Replace placeholders: title, student names, register numbers, guide, HoD, submission date.

## Recommended Update Sequence
1. `references.tex`
2. `chapter_3.tex`
3. `chapter_4.tex`
4. `chapter_5.tex`
5. `chapter_7.tex`
6. `chapter_8.tex`
7. `chapter_1.tex`
8. `abstract.tex`
9. `BTechProjectTemplate.tex`

## Build/Compile Notes
Use your LaTeX workflow for this template (e.g., `pdflatex` + bibliography pass) and verify:
- No missing citations
- No figure path errors
- Table and figure numbering consistency
- Clean Table of Contents entries

## Done Criteria
The update is complete when:
- Report explicitly covers scheduling, aggregation, and combined model.
- Baseline paper is cited and compared in literature + discussion.
- Results and conclusion align with latest capstone outcomes.
- Document compiles without reference/citation warnings.
