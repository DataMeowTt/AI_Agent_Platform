from src.utils.gold_utils import load_silver
from src.storage.connect import get_engine
from src.storage.schema_loader import create_all_tables
from src.processing_analysis import (
    gold_growth_dynamics,
    gold_structural_composition,
    gold_fiscal_monetary,
    gold_crisis_risk,
    gold_social_welfare,
)


def main() -> None:
    print("Connecting to Postgres...")
    engine = get_engine()

    print("Creating schemas...")
    create_all_tables(engine)

    print("\nLoading silver layer...")
    silver = load_silver()
    print(f"Silver rows: {len(silver):,}")

    gold_growth_dynamics.run(silver, engine)
    gold_structural_composition.run(silver, engine)
    gold_fiscal_monetary.run(silver, engine)
    gold_crisis_risk.run(silver, engine)
    gold_social_welfare.run(silver, engine)

    print("\nAll gold tables loaded into Postgres.")


if __name__ == "__main__":
    main()
