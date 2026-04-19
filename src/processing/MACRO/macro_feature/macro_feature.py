from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def compute_macro_features(df: DataFrame) -> DataFrame:
    w = Window.partitionBy("country_code").orderBy("year")

    return (
        df
        # decade = (year // 10) * 10
        .withColumn("decade",
            (F.floor(F.col("year") / 10) * 10).cast("double"))

        # GFCF_to_GDP = gfcf_value / gdp_value * 100
        .withColumn("gfcf_to_gdp",
            F.col("gfcf_value") / F.col("gdp_value") * 100)

        # GNI_to_GDP = gni_value / gdp_value
        .withColumn("gni_to_gdp",
            F.col("gni_value") / F.col("gdp_value"))

        # agri_va_share = agri_va / gdp_value * 100
        .withColumn("agri_va_share",
            F.col("agri_va") / F.col("gdp_value") * 100)

        # manuf_va_share = manuf_va / gdp_value * 100
        .withColumn("manuf_va_share",
            F.col("manuf_va") / F.col("gdp_value") * 100)

        # food_bev_share_manuf = va_foodbev / manuf_va * 100
        .withColumn("food_bev_share_manuf",
            F.col("va_foodbev") / F.col("manuf_va") * 100)

        # GDP_growth_YoY = pct_change of gdp_value per country
        .withColumn("gdp_growth_yoy",
            (F.col("gdp_value") - F.lag("gdp_value").over(w))
            / F.lag("gdp_value").over(w) * 100)
    )
