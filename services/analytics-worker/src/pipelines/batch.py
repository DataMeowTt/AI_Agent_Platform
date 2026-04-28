import traceback
import pandas as pd
from src.core.logger import logger
from src.pipelines.trend import compute_trend_for_indicator, save_trends_to_analytics
from src.pipelines.anomaly import update_anomaly_scores
from src.pipelines.cluster import run_clustering

TABLES_INDICATORS = {
    "gold_growth_dynamics": [
        "rGDP_growth_YoY", "GDP_growth_YoY", "trend_deviation",
        "GDP_pc_growth_gap", "rolling_mean_5yr"
    ],
    "gold_fiscal_monetary": [
        "govdebt_GDP", "fiscal_balance_GDP", "real_interest_rate",
        "inflation_gap", "inflation_cpi", "tax_revenue_pct_GDP"
    ],
    "gold_crisis_risk": ["REER_deviation", "spending_efficiency"],
    "gold_social_welfare": [
        "poverty_headcount", "poverty_change_5yr", "hcons_growth",
        "unemployment_total", "youth_unemployment_gap"
    ],
    "gold_structural_composition": [
        "GFCF_to_GDP", "GNI_to_GDP", "agri_va_share", "manuf_va_share",
        "food_bev_share_manuf"
    ]
}

def run_all_analytics():
    logger.info("Starting Full Analytics Batch Process")
    
    for table_name, indicators in TABLES_INDICATORS.items():
        for indicator in indicators:
            logger.info(f"Batch Processing: {indicator} in {table_name}")
            try:
                results = compute_trend_for_indicator(table_name, indicator)
                if results:
                    df = pd.DataFrame(results)
                    save_trends_to_analytics(table_name, indicator, df)
                    update_anomaly_scores(table_name, indicator)
            except Exception as e:
                logger.error(f"Error processing {indicator} in {table_name}: {traceback.format_exc()}")

    target_years = [2000, 2010, 2020, 2022]
    for year in target_years:
        logger.info(f"Batch Processing Clustering for year {year}")
        try:
            run_clustering(target_year=year, n_clusters=5)
        except Exception as e:
            logger.error(f"Error processing clustering for {year}: {traceback.format_exc()}")
            
    logger.info("Full Analytics Batch Process Completed")