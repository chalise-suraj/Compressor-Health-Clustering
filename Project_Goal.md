# Project Goal — Compressor Health Clustering

<p align="center">
  <img src="https://img.shields.io/badge/Focus-Operating%20behavior-147D74?style=for-the-badge" alt="Operating behavior analysis">
  <img src="https://img.shields.io/badge/Data-MetroPT--3-3776AB?style=for-the-badge" alt="MetroPT-3 data">
  <img src="https://img.shields.io/badge/Stage-Historical%20prototype-B87924?style=for-the-badge" alt="Historical prototype">
</p>

> **Current status:** the four-notebook workflow, exploratory k=4 pipeline, historical monitoring outputs, and local Streamlit dashboard are available. The final cluster count and any operational alarm criteria are **not yet validated**.

## 1. Aim

Build a clear, reproducible analysis of the MetroPT-3 air-compressor sensor data that discovers recurring operating behaviors, tracks how those behaviors change over time, and investigates whether unusual patterns align with documented air-leak/high-stress periods.

The project is intended to help a reader or engineer inspect historical compressor behavior and decide which periods merit further investigation. It is a research and demonstration prototype, not a live maintenance system.

## 2. Questions the project should answer

1. What is the actual time cadence, data quality, and continuity of the supplied sensor record?
2. What non-overlapping time window gives useful sensor summaries without crossing long timestamp gaps?
3. Which sensor-feature patterns form stable, interpretable operating groups?
4. Do cluster frequencies and sensor patterns change between earlier and later periods?
5. Which windows are unusually distant from their assigned cluster’s training examples, and do unusual runs persist?
6. How do these exploratory patterns compare with the dataset’s coarse reported event periods?
7. What evidence, validation, and data would be required before making a fault-detection or predictive-maintenance claim?

## 3. Data and scope

The project uses the [MetroPT-3 dataset from the UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/791/metropt%2B3%2B), stored locally under `data/raw/` with its data-description PDF. The CSV contains 1,516,948 chronological rows, one timestamp, and 15 sensor signals spanning February to September 2020.

The dataset does not provide row-level fault labels. Four reported air-leak/high-stress time periods are available as retrospective annotations. Those periods are useful for exploratory comparison, but they do not provide enough evidence to claim reliable warning or fault detection.

### In scope

- Inspect sensor schema, cadence, missingness, duplicates, timestamp order, gaps, distributions, and signal types.
- Preserve raw data and chronology; exclude the sequential source index from features.
- Compare window durations, split windows at long gaps, and keep low-coverage records available for review.
- Engineer interpretable sensor summaries and compare plausible K-Means cluster counts.
- Use a chronological holdout and fit learned preprocessing on the training data only.
- Describe clusters from their measured profiles and temporal behavior without assigning unsupported health labels.
- Define transparent exploratory distance and persistence rules, and compare them cautiously with documented event periods.
- Save a reusable clustering pipeline and a professional offline dashboard for reviewing saved results.

### Out of scope for the current prototype

- Live IoT ingestion, streaming inference, or automated equipment control.
- Confirmed fault diagnosis, maintenance scheduling, or remaining-useful-life estimates.
- Health grades, failure probabilities, or production alarm thresholds derived from K-Means alone.
- Claims of prospective early warning based only on retrospective event overlap.

## 4. Analysis and modeling workflow

1. **Data understanding** — verify the supplied file, its schema, timestamps, sampling cadence, data quality, sensor distributions, and the accompanying event documentation.
2. **Window design** — compare candidate durations using the observed cadence and operating-state dwell behavior. Preserve chronology and break segments at timestamp gaps greater than 30 seconds.
3. **Feature engineering** — summarize analog sensors, represent binary states as fractions, add a selected state-transition count, and keep time/coverage identifiers outside the clustering matrix.
4. **Preprocessing** — use median imputation and robust scaling, fitting both transformations on the training interval only.
5. **Cluster evaluation** — compare candidate k values with inertia, sampled silhouette, cluster balance, stability, and the usefulness of the resulting profiles. Do not select k from a single metric.
6. **Chronological evaluation** — reserve the latest 20% of eligible windows as a holdout and assign its labels without refitting the training pipeline.
7. **Condition monitoring** — track operating-state mix, center distances, and persistent unusual runs; describe every threshold as exploratory until validated.
8. **Event review** — compare findings with the reported dates, distinguish retrospective overlap from prospective warning, and document source inconsistencies and evaluation limits.
9. **Communication and reuse** — save the model/schema/assignments, explain findings and limitations in notebooks and Markdown, and provide a dashboard over saved outputs.

## 5. Current saved-run snapshot

- The observed median sensor interval is **10 seconds**. The supplied source description says 1 Hz, so the actual observed cadence is documented as a discrepancy.
- Five-minute windows contain a median of about 30 source rows. The 80% coverage rule admitted **50,437** of **50,584** windows to clustering; **147** remained unassigned.
- The saved model is **provisional k=4**. In the candidate comparison, sampled training silhouette was highest at **k=3 (0.9429)**, compared with **0.9375 for k=4**.
- Cluster 0 accounts for **88.74%** of training assignments and **95.25%** of holdout assignments. Cluster 1 decreases from **2,935** training windows to **8** holdout windows. These changes warrant review, not fault labeling.
- The monitoring rule produced **484** individual distance alerts and **7** windows in qualifying persistent runs. No persistent flags overlapped the reported events or ended within 24 hours before them.
- All four reported event periods fall inside the model training interval. Event comparison is retrospective and in-sample, not independent validation.

These numbers summarize the current saved outputs. See [Model.md](Model.md) for methodology, saved artifacts, and detailed interpretation.

## 6. Deliverables

1. Four sequential notebooks for data understanding, feature engineering, clustering, and condition monitoring.
2. Processed window features, metadata, and cluster assignments that can be traced to their source windows.
3. A reusable fitted preprocessing-plus-K-Means pipeline with its feature schema and metadata.
4. Saved event, distance-alert, persistence, and transition summaries for retrospective review.
5. An offline Streamlit dashboard that reads saved outputs, supports filtering, and exports selected window records.
6. Project documentation that explains how to run the work, what the current model does, and where the evidence stops.

## 7. Definition of a successful research prototype

- The notebooks can be run in order from the documented project environment and use actual source files rather than fabricated results.
- Long gaps are not interpolated across, time order is preserved, and preprocessing is fitted only on the training period.
- The model and dashboard use a consistent saved feature schema and give traceable window-level outputs.
- Candidate cluster counts are reviewed using multiple diagnostics and are not described as health categories.
- Reported events are clearly identified as coarse annotations, and event comparisons are not presented as independent validation when they fall in training data.
- Charts are readable, correctly labeled, and appropriate to the question; the dashboard is clearly marked as historical/offline.
- Conclusions distinguish observed pattern changes from confirmed faults, prediction, and validated alarm performance.

## 8. Limitations and risks

- **One asset and period:** the supplied history covers one compressor in one operational setting. Generalization to other compressors or future periods is unknown.
- **Cadence discrepancy:** the observed median interval is 10 seconds, while the source documentation describes 1 Hz. The project uses the observed timestamps.
- **Unobserved gaps:** 331 gaps exceed 30 seconds, including a gap of about 48 hours. The cause of the gaps is not inferred.
- **Window averaging:** five-minute summaries can merge behavior that changes on shorter time scales; some observed state-pattern median dwell times are below one minute.
- **Feature redundancy:** `TP3` and `Reservoirs` are strongly correlated, and multiple summaries per sensor can overweight related dimensions.
- **Unsupervised labels:** K-Means does not know fault status. Cluster numbers are arbitrary and no health score or probability is produced.
- **Model selection:** k=4 is saved for review, while k=3 had the strongest sampled silhouette; k=4 clusters 2 and 3 have nearly indistinguishable selected profiles.
- **Temporal change:** a cluster nearly disappears in holdout. This may reflect changing operation, coverage, or an over-specific partition; it must be investigated.
- **Event annotations:** event intervals are coarse and not row-level verified labels. The source has an inconsistent maintenance-date note for event 2.
- **No independent event validation:** all four event periods occur during training. The current results cannot establish prospective warning, sensitivity, or false-alarm rate.
- **Unvalidated alert rules:** cluster-specific 99th-percentile distances and the three-window persistence rule are exploratory review thresholds, not engineering limits.
- **Offline dashboard:** the app reads saved files and does not ingest live measurements or issue validated operational alarms.

## 9. Priorities before making stronger claims

1. Refit and compare k=3 with k=4, including cluster profiles, state mix, initialization stability, and later-period behavior.
2. Review correlated features and decide whether all repeated analog summaries and both correlated pressure signals are justified.
3. Verify event and maintenance timestamps against authoritative source documentation.
4. Evaluate against trustworthy fault intervals using an evaluation design that keeps the tested events out of training and threshold calibration.
5. Measure event coverage, warning lead time, false alarms, missed events, and the effects of changing threshold/persistence choices.
6. Obtain more periods and, before deployment, data from additional machines or validated operating conditions.
7. Only after engineering review and prospective validation consider real-time ingestion or operational alarm use.

The current outcome is a reproducible **exploratory analysis**, not a validated predictive-maintenance product. For the model’s technical details, see [Model.md](Model.md); for setup and notebook order, see [README.md](README.md).
