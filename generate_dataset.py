import os
import numpy as np
import pandas as pd

# Illustrative synthetic data for development/demo only; not real healthcare statistics.
rng = np.random.default_rng(42)
districts = ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Mehsana",
             "Bhavnagar", "Kutch", "Anand", "Gandhinagar", "Jamnagar"]
months = pd.date_range("2026-03-01", periods=6, freq="MS")
rows = []
for j, district in enumerate(districts):
    base_anc = 76 + (j % 5) * 3
    base_delivery = 82 + (j % 4) * 2
    base_imm = 86 + (j % 3) * 2
    base_risk = 10 + (j % 6)
    for i, month in enumerate(months):
        anc = base_anc + i * rng.normal(0.5, 1.0) + rng.normal(0, 1.2)
        delivery = base_delivery + i * 0.4 + rng.normal(0, 1.2)
        immunization = base_imm + i * 0.3 + rng.normal(0, 1.0)
        risk = max(1, round(base_risk + i * 0.3 + rng.normal(0, 1.5)))
        rows.append([month.strftime("%Y-%m-%d"), district,
                     round(float(np.clip(anc, 40, 99)), 1),
                     round(float(np.clip(delivery, 50, 99)), 1),
                     round(float(np.clip(immunization, 50, 99)), 1), risk])

df = pd.DataFrame(rows, columns=["month", "district", "anc_coverage",
                                 "institutional_delivery", "immunization", "high_risk_cases"])
# Inject a couple of intentional anomalies to demonstrate detection.
df.loc[(df["district"] == "Mehsana") & (df["month"] == "2026-06-01"), "anc_coverage"] = 42.0
df.loc[(df["district"] == "Mehsana") & (df["month"] == "2026-06-01"), "high_risk_cases"] = 28
df.loc[(df["district"] == "Ahmedabad") & (df["month"] == "2026-08-01"), "anc_coverage"] = 69.0

os.makedirs("data", exist_ok=True)
df.to_csv("data/healthcare.csv", index=False)
print(f"Created data/healthcare.csv with {len(df)} rows.")
print("Reminder: this is synthetic demonstration data, not official healthcare data.")
