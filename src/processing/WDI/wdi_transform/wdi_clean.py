from pyspark.sql import DataFrame
from pyspark.sql import functions as F

INDICATOR_CODE_MAP = {
    "Unemployment, total (% of total labor force) (modeled ILO estimate)":                   "unemployment_total",
    "Unemployment, youth total (% of total labor force ages 15-24) (modeled ILO estimate)":  "unemployment_youth",
    "Self-employed, total (% of total employment) (modeled ILO estimate)":                   "self_employed_total",
    "Urban population (% of total population)":                                              "urban_population",
    "Urban population growth (annual %)":                                                    "urban_population_growth",
    "Population density (people per sq. km of land area)":                                   "population_density",
    "Population growth (annual %)":                                                          "population_growth",
    "Inflation, consumer prices (annual %)":                                                 "inflation_consumer_prices",
    "Inflation, GDP deflator (annual %)":                                                    "inflation_gdp_deflator",
    "Poverty headcount ratio at $3.00 a day (2021 PPP) (% of population)":                  "poverty_headcount_ratio",
    "Trade (% of GDP)":                                                                      "trade_gdp",
    "Imports of goods and services (current US$)":                                           "imports_goods_services",
    "Exports of goods and services (% of GDP)":                                              "exports_goods_services",
    "Tax revenue (% of GDP)":                                                                "tax_revenue_gdp",
    "GDP (current US$)":                                                                     "gdp",
    "GDP growth (annual %)":                                                                 "gdp_growth",
    "GDP per capita (current US$)":                                                          "gdp_per_capita",
    "GDP per capita growth (annual %)":                                                      "gdp_per_capita_growth",
}

def map_indicator_codes(df: DataFrame) -> DataFrame:
    mapping_expr = F.create_map([F.lit(x) for pair in INDICATOR_CODE_MAP.items() for x in pair])
    return df.withColumn("indicator", mapping_expr[F.col("indicator")])
