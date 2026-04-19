CREATE TABLE IF NOT EXISTS gold_crisis_risk (
    country_code            VARCHAR(3)      NOT NULL,
    country                 TEXT            NOT NULL,
    year                    INTEGER         NOT NULL,
    "SovDebtCrisis"         SMALLINT,
    "CurrencyCrisis"        SMALLINT,
    "BankingCrisis"         SMALLINT,
    crisis_composite        SMALLINT,
    crisis_any              SMALLINT,
    "REER_deviation"        DOUBLE PRECISION,
    spending_efficiency     DOUBLE PRECISION,
    govdebt_gdp             DOUBLE PRECISION,
    fiscal_balance_gdp      DOUBLE PRECISION,
    "rGDP_growth_YoY"       DOUBLE PRECISION,
    income_group            TEXT,
    development_group       TEXT,
    completeness_score      DOUBLE PRECISION,
    PRIMARY KEY (country_code, year)
);
