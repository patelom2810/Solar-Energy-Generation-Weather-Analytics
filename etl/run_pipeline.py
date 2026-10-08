"""
ETL Pipeline CLI Runner for Solar Energy Analytics.
Usage:
    python -m etl.run_pipeline [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--full-refresh] [--retrain]
"""
import sys
import os
import uuid
import logging
import argparse
from datetime import datetime, date, timedelta
from typing import Optional
from dotenv import load_dotenv

# Ensure root directory is on PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from etl.extract import extract_all, DEFAULT_LATITUDE, DEFAULT_LONGITUDE
from etl.transform import transform_all
from etl.load import load_all, record_etl_run, init_etl_tables
from etl.retrain import evaluate_and_retrain_model

load_dotenv()

# Structured logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("etl.pipeline")


def parse_arguments():
    """Parse command line arguments for ETL pipeline."""
    parser = argparse.ArgumentParser(
        description="Solar Energy Analytics - Automated Data Ingestion & Model Pipeline"
    )
    parser.add_argument(
        '--start',
        type=str,
        default=os.getenv('ETL_START_DATE', '2026-02-01'),
        help="Extraction start date (YYYY-MM-DD). Default: 2026-02-01 or ETL_START_DATE env var."
    )
    parser.add_argument(
        '--end',
        type=str,
        default=os.getenv('ETL_END_DATE', '2026-05-02'),
        help="Extraction end date (YYYY-MM-DD). Default: 2026-05-02 or ETL_END_DATE env var."
    )
    parser.add_argument(
        '--full-refresh',
        action='store_true',
        help="Execute full historical backfill and recreate MySQL tables."
    )
    parser.add_argument(
        '--retrain',
        action='store_true',
        default=os.getenv('ETL_RETRAIN_ON_RUN', 'false').lower() in ('true', '1', 'yes'),
        help="Trigger model evaluation and retraining after data ingestion."
    )
    parser.add_argument(
        '--lat',
        type=float,
        default=DEFAULT_LATITUDE,
        help=f"Latitude coordinate. Default: {DEFAULT_LATITUDE}"
    )
    parser.add_argument(
        '--lon',
        type=float,
        default=DEFAULT_LONGITUDE,
        help=f"Longitude coordinate. Default: {DEFAULT_LONGITUDE}"
    )
    parser.add_argument(
        '--raw-dir',
        type=str,
        default='data/raw',
        help="Directory path to scan for raw solar CSV drops. Default: data/raw"
    )
    return parser.parse_args()


def run_pipeline(
    start_date: str,
    end_date: str,
    full_refresh: bool = False,
    retrain: bool = False,
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    raw_dir: str = 'data/raw'
) -> int:
    """
    Execute full ETL pipeline with structured logging and status tracking.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    start_time = datetime.now()
    
    logger.info("=" * 70)
    logger.info(f"🚀 Starting ETL Pipeline [ID: {run_id}]")
    logger.info(f"   Date Range : {start_date} -> {end_date}")
    logger.info(f"   Coordinates: ({latitude}, {longitude})")
    logger.info(f"   Full Refresh: {full_refresh} | Retrain: {retrain}")
    logger.info("=" * 70)
    
    counts = {}
    retrain_summary = None
    
    try:
        # Phase 0: Initialize MySQL DDL if full-refresh or first run
        if full_refresh:
            logger.info("Reinitializing ETL tables DDL...")
            init_etl_tables()
            
        # Phase 1: Extraction
        logger.info("[Step 1/4] Extracting meteorological and solar data...")
        extracted_data = extract_all(
            start_date=start_date,
            end_date=end_date,
            raw_dir=raw_dir,
            latitude=latitude,
            longitude=longitude
        )
        
        # Phase 2: Transformation
        logger.info("[Step 2/4] Transforming, deduping, and engineering features...")
        transformed_data = transform_all(extracted_data)
        
        # Phase 3: Loading
        logger.info("[Step 3/4] Idempotently upserting into MySQL & refreshing CSVs...")
        counts = load_all(
            transformed_data,
            full_refresh=full_refresh,
            data_dir='data'
        )
        
        # Phase 4: Optional Model Retraining
        if retrain:
            logger.info("[Step 4/4] Evaluating candidate model retraining...")
            df_features = transformed_data.get('daily_features')
            if df_features is not None and len(df_features) > 0:
                retrain_summary = evaluate_and_retrain_model(df_features)
            else:
                logger.warning("No feature-engineered daily records available for retraining.")
        else:
            logger.info("[Step 4/4] Model retraining skipped (--retrain not specified).")
            
        end_time = datetime.now()
        duration = round((end_time - start_time).total_seconds(), 2)
        
        # Record successful execution
        record_etl_run(
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            status="success",
            records_processed=counts,
            retrain_summary=retrain_summary,
            error_message=None
        )
        
        logger.info("=" * 70)
        logger.info(f"✅ ETL Pipeline completed successfully in {duration}s!")
        for tbl, count in counts.items():
            logger.info(f"   - {tbl:22s}: {count} records upserted")
        if retrain_summary:
            status_text = "Updated" if retrain_summary.get('improved') else "Retained"
            logger.info(f"   - Model Retraining    : {status_text} ({retrain_summary.get('candidate_metrics', {})})")
        logger.info("=" * 70)
        return 0
        
    except Exception as e:
        end_time = datetime.now()
        logger.error(f"❌ ETL Pipeline failed: {e}", exc_info=True)
        record_etl_run(
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            status="failed",
            records_processed=counts,
            retrain_summary=retrain_summary,
            error_message=str(e)
        )
        return 1


def main():
    args = parse_arguments()
    exit_code = run_pipeline(
        start_date=args.start,
        end_date=args.end,
        full_refresh=args.full_refresh,
        retrain=args.retrain,
        latitude=args.lat,
        longitude=args.lon,
        raw_dir=args.raw_dir
    )
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
