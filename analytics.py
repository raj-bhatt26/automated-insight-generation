import numpy as np
import pandas as pd

DEFAULT_INDICATORS = [
    "anc_coverage",
    "institutional_delivery",
    "immunization",
    "high_risk_cases",
]

def load_and_validate(file):
    df = pd.read_csv(file)
    required = {"month", "district", *DEFAULT_INDICATORS}
    missing_cols = required - set(df.columns)
    if missing_cols:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing_cols))}")

    df = df.copy()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df["district"] = df["district"].astype("string").str.strip()
    for col in DEFAULT_INDICATORS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["month", "district"])
    df = df.sort_values(["district", "month"]).reset_index(drop=True)
    return df

def severity_for_indicator(indicator, absolute_change):
    """Assign severity using the indicator's units, not percentage change alone.

    These are demonstration thresholds, not official healthcare standards.
    Coverage indicators are percentages, so use percentage-point changes.
    High-risk cases are counts, so use the absolute number of cases changed.
    """
    if indicator == "high_risk_cases":
        if absolute_change >= 5:
            return "High"
        if absolute_change >= 2:
            return "Medium"
        return "Low"

    # Coverage indicators are expressed as percentages; compare percentage points.
    if absolute_change >= 15:
        return "High"
    if absolute_change >= 8:
        return "Medium"
    return "Low"


def detect_trends(df, indicators, threshold_pct=10.0):
    records = []
    ordered = df.sort_values(["district", "month"])
    for indicator in indicators:
        for district, group in ordered.groupby("district", dropna=True):
            group = group.sort_values("month")
            values = group[["month", indicator]].dropna()
            if len(values) < 2:
                continue
            for i in range(1, len(values)):
                prev_row = values.iloc[i - 1]
                current_row = values.iloc[i]
                prev = float(prev_row[indicator])
                current = float(current_row[indicator])
                absolute_change = current - prev
                if prev == 0:
                    # Relative change is undefined at zero; don't fabricate a percentage.
                    continue
                change_pct = (absolute_change / abs(prev)) * 100
                if abs(change_pct) >= threshold_pct:
                    direction = "increased" if absolute_change > 0 else "decreased"
                    if indicator == "high_risk_cases":
                        magnitude_text = f"by {abs(absolute_change):g} cases ({abs(change_pct):.1f}%)"
                    else:
                        magnitude_text = f"by {abs(absolute_change):.1f} percentage points ({abs(change_pct):.1f}%)"
                    records.append({
                        "type": "trend",
                        "indicator": indicator,
                        "entity": str(district),
                        "period": current_row["month"].strftime("%Y-%m"),
                        "value": current,
                        "prev_value": prev,
                        "change_pct": change_pct,
                        "metric": current,
                        "change": change_pct,
                        "explanation": (
                            f"{indicator.replace('_', ' ').title()} in {district} "
                            f"{direction} {magnitude_text} compared with the previous month."
                        ),
                        "severity": severity_for_indicator(indicator, abs(absolute_change)),
                    })
    return records

def detect_outliers(df, indicators, method="IQR", iqr_multiplier=1.5, z_threshold=3.0):
    records = []
    for indicator in indicators:
        series = pd.to_numeric(df[indicator], errors="coerce").dropna()
        if len(series) < 4:
            continue
        if method == "IQR":
            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            low, high = q1 - iqr_multiplier * iqr, q3 + iqr_multiplier * iqr
            mask = (pd.to_numeric(df[indicator], errors="coerce") < low) | (pd.to_numeric(df[indicator], errors="coerce") > high)
            distance = lambda x: max((low - x) / (iqr or 1), (x - high) / (iqr or 1), 0)
        else:
            mean, std = series.mean(), series.std(ddof=0)
            if std == 0 or np.isnan(std):
                continue
            z = (pd.to_numeric(df[indicator], errors="coerce") - mean) / std
            mask = z.abs() >= z_threshold
            distance = lambda x: abs((x - mean) / std)
        for idx in df.index[mask.fillna(False)]:
            row = df.loc[idx]
            value = float(row[indicator])
            score = distance(value)
            severity = "High" if score >= (3 if method == "IQR" else z_threshold * 1.5) else "Medium" if score >= (1.5 if method == "IQR" else z_threshold) else "Low"
            records.append({
                "type": "outlier",
                "indicator": indicator,
                "entity": str(row["district"]),
                "period": row["month"].strftime("%Y-%m"),
                "value": value,
                "prev_value": np.nan,
                "change_pct": np.nan,
                "metric": value,
                "change": np.nan,
                "severity": severity,
                "explanation": (
                    f"{indicator.replace('_', ' ').title()} for {row['district']} in "
                    f"{row['month']:%Y-%m} is an outlier under the {method} rule "
                    f"(observed value: {value:g})."
                ),
            })
    return records

def detect_correlations(df, indicators, threshold=0.70):
    records = []
    numeric = df[indicators].apply(pd.to_numeric, errors="coerce")
    corr = numeric.corr(method="pearson", min_periods=3)
    for i, first in enumerate(indicators):
        for second in indicators[i + 1:]:
            value = corr.loc[first, second]
            if pd.notna(value) and abs(value) >= threshold:
                severity = "High" if abs(value) >= min(0.95, threshold + 0.20) else "Medium" if abs(value) >= min(0.85, threshold + 0.10) else "Low"
                records.append({
                    "type": "correlation",
                    "indicator": f"{first}:{second}",
                    "entity": "All districts",
                    "period": "All available months",
                    "value": float(value),
                    "prev_value": np.nan,
                    "change_pct": np.nan,
                    "metric": float(value),
                    "change": float(value),
                    "severity": severity,
                    "explanation": (
                        f"{first.replace('_', ' ').title()} and {second.replace('_', ' ').title()} "
                        f"have a Pearson correlation of {value:.2f}. Correlation does not imply causation."
                    ),
                })
    return corr, records

def generate_insights(df, indicators, trend_threshold=10.0, outlier_method="IQR",
                      iqr_multiplier=1.5, z_threshold=3.0, correlation_threshold=0.70):
    records = []
    trend_records = detect_trends(df, indicators, trend_threshold)
    outlier_records = detect_outliers(df, indicators, outlier_method, iqr_multiplier, z_threshold)

    # Flag trends whose previous observation was itself detected as an outlier.
    # This preserves the output schema and helps readers interpret rebounds carefully.
    outlier_keys = {
        (record["indicator"], record["entity"], record["period"])
        for record in outlier_records
    }
    ordered = df.sort_values(["district", "month"])
    previous_period_by_key = {}
    for indicator in indicators:
        for district, group in ordered.groupby("district", dropna=True):
            group = group.sort_values("month")
            valid = group[["month", indicator]].dropna()
            for i in range(1, len(valid)):
                previous_period_by_key[(indicator, str(district), valid.iloc[i]["month"].strftime("%Y-%m"))] = valid.iloc[i - 1]["month"].strftime("%Y-%m")

    for record in trend_records:
        previous_period = previous_period_by_key.get(
            (record["indicator"], record["entity"], record["period"])
        )
        if previous_period and (record["indicator"], record["entity"], previous_period) in outlier_keys:
            record["explanation"] += (
                " The previous month's value was flagged as an outlier, so this change "
                "may partly reflect a rebound from an unusual observation."
            )

    records.extend(trend_records)
    records.extend(outlier_records)
    corr, correlation_records = detect_correlations(df, indicators, correlation_threshold)
    records.extend(correlation_records)
    columns = ["insight_id", "type", "indicator", "entity", "period", "value",
               "prev_value", "change_pct", "metric", "change", "severity", "explanation"]
    insights = pd.DataFrame(records)
    if insights.empty:
        insights = pd.DataFrame(columns=columns)
    else:
        insights.insert(0, "insight_id", [f"INS-{i:04d}" for i in range(1, len(insights) + 1)])
        insights = insights[columns]
    return insights, corr
