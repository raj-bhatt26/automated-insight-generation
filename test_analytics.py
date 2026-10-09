
import pandas as pd

from analytics import (
    detect_trends,
    detect_outliers,
    detect_correlations,
)


def test_trends():
    df = pd.DataFrame({
        "month": pd.to_datetime([
            "2026-01-01",
            "2026-02-01",
            "2026-03-01",
        ]),
        "district": ["TestDistrict"] * 3,
        "anc_coverage": [50.0, 60.0, 45.0],
    })

    results = detect_trends(
        df, ["anc_coverage"], threshold_pct=10
    )

    assert len(results) == 2, results
    assert abs(results[0]["change_pct"] - 20.0) < 1e-9
    assert abs(results[1]["change_pct"] + 25.0) < 1e-9

    print("PASS: Trend increases and decreases")


def test_outliers():
    df = pd.DataFrame({
        "district": ["TestDistrict"] * 21,
        "month": pd.date_range(
            "2026-01-01", periods=21, freq="D"
        ),
        "high_risk_cases": [10.0] * 20 + [100.0],
    })

    for method in ["IQR", "Z-score"]:
        results = detect_outliers(
            df, ["high_risk_cases"], method=method
        )

        assert any(
            r["value"] == 100.0 for r in results
        ), f"{method} failed: {results}"

    print("PASS: IQR and Z-score outlier detection")


def test_correlations():
    df = pd.DataFrame({
        "anc_coverage": [1, 2, 3, 4, 5],
        "institutional_delivery": [2, 4, 6, 8, 10],
        "immunization": [5, 1, 4, 2, 3],
    })

    indicators = [
        "anc_coverage",
        "institutional_delivery",
        "immunization",
    ]

    corr, results = detect_correlations(
        df, indicators, threshold=0.70
    )

    assert abs(
        corr.loc["anc_coverage", "institutional_delivery"] - 1.0
    ) < 1e-9

    assert any(
        r["indicator"] == "anc_coverage:institutional_delivery"
        for r in results
    ), results

    assert all(
        abs(r["value"]) >= 0.70 for r in results
    ), results

    print("PASS: Correlation calculation and threshold")


if __name__ == "__main__":
    test_trends()
    test_outliers()
    test_correlations()
    print("\nAll analytics tests passed!")
