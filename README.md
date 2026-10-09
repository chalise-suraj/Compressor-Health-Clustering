# Compressor Health Clustering

Historical clustering and monitoring prototype for the MetroPT-3 Air Compressor dataset. The dashboard is offline and reads saved outputs; it does not connect to live equipment. K-Means clusters describe operating patterns and are not health grades or failure probabilities.

## Run the workflow

Use the project virtual environment and run the notebooks in order:

1. `notebooks/01_data_understanding.ipynb`
2. `notebooks/02_feature_engineering.ipynb`
3. `notebooks/03_kmeans_clustering.ipynb`
4. `notebooks/04_condition_monitoring.ipynb`

Save notebook outputs after each run. Notebook 02 creates window features; notebook 03 creates the fitted pipeline and cluster assignments; notebook 04 creates monitoring summaries.

## Launch the dashboard

From the project root, with the project environment active:

```powershell
streamlit run app.py
```

The dashboard requires the saved files in `data/processed/` and model metadata in `models/`. If they are missing, run the notebooks in order.

## Method and limitations

The current workflow uses non-overlapping 5-minute windows, splits long timestamp gaps, and evaluates a chronological holdout. The saved k=4 pipeline is exploratory; notebook 03 found that k=3 warrants comparison. Reported air-leak/high-stress periods are retrospective annotations and are not row-level labels. Cluster shifts and distance alerts need investigation and do not confirm faults or provide prospective prediction.
