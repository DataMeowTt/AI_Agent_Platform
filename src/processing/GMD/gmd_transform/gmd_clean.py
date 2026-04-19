NUMERIC_COLS = {
    "rGDP":          "rgdp",
    "rGDP_pc_USD":   "rgdp_pc_usd",
    "hcons_GDP":     "hcons_gdp",
    "govdebt_GDP":   "govdebt_gdp",
    "govtax_GDP":    "govtax_gdp",
    "SovDebtCrisis": "sov_debt_crisis",
    "CurrencyCrisis":"currency_crisis",
    "BankingCrisis": "banking_crisis",
    "exports_GDP":   "exports_gdp",
    "imports_GDP":   "imports_gdp",
    "govrev_GDP":    "govrev_gdp",
    "govexp_GDP":    "govexp_gdp",
    "ltrate":        "ltrate",
    "infl":          "infl",
    # Helper columns — used for feature computation, not output
    "REER":          "reer",
    "hcons_USD":     "hcons_usd",
}

# income_group is string — handled separately for ordinal encoding
STRING_COLS = {
    "income_group": "income_group",
}
