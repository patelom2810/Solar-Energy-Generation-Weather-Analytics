# Raw Solar Data Drops

Drop new solar generation CSV files into this directory for automated ingestion by the ETL pipeline:

```bash
python -m etl.run_pipeline
```

### Supported Drop Formats:
- **Daily Drops**: CSV with `date`, `generation_kwh`, `consumption_kwh`, etc.
- **Hourly Drops**: CSV with `date`, `hour_ts`, `generation_kwh`, `consumption_kwh`, etc.

The pipeline automatically scans, cleans, validates bounds, deduplicates, and idempotently upserts records into MySQL and updates the analytical datasets in `data/`.
