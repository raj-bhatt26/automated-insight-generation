
from pathlib import Path

from narwhals import corr

from analytics import (
    DEFAULT_INDICATORS,
    load_and_validate,
    generate_insights,
)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "healthcare.csv"

def main():
    print("1. Loading dataset...")
    df = load_and_validate(CSV_PATH)

    print(f"Rows: {len(df)}")
    print(f"Districts: {df['district'].nunique()}")
    print(f"Date range: {df['month'].min()} to {df['month'].max()}")

    print("\n2. Checking missing values...")
    print(df.isna().sum().to_string())

    print("\n3. Generating insights...")
    insights, corr = generate_insights(
        df,
        DEFAULT_INDICATORS,
        trend_threshold=10,
        outlier_method="IQR",
        iqr_multiplier=1.5,
        z_threshold=3.0,
        correlation_threshold=0.70,
    )

    print(f"\nTotal insights: {len(insights)}")

    if not insights.empty:
        print("\nInsight counts by type:")
        print(insights["type"].value_counts().to_string())

        print("\nInsight counts by severity:")
        print(insights["severity"].value_counts().to_string())

        print("\nSample generated insights:")
        print(
            insights[
                ["type", "indicator", "entity",
                 "severity", "explanation"]
            ].head(10).to_string(index=False)
        )

        output_path = BASE_DIR / "outputs" / "insights.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        insights.to_csv(output_path, index=False)
        print(f"\nSaved insights to: {output_path}")

        print("\nOutlier details:")
        outliers = insights[insights["type"] == "outlier"]

        if outliers.empty:
            print("No outliers detected.")
        else:
            print(
        outliers[
            [
                "indicator",
                "entity",
                "period",
                "value",
                "severity",
                "explanation",
            ]
        ].to_string(index=False)
    )

        print("\nHigh-severity trend details:")
        high_trends = insights[
    (insights["type"] == "trend")
    & (insights["severity"] == "High")
]

    print(
    high_trends[
        [
            "indicator",
            "entity",
            "period",
            "prev_value",
            "value",
            "change_pct",
            "severity",
        ]
    ].head(15).to_string(index=False)
)

    print("\nCorrelation matrix:")
    print(corr.round(3).to_string())

if __name__ == "__main__":
    main()
