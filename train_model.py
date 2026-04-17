"""
train_model.py
==============
Generates a synthetic e-commerce dataset, trains a Random Forest classifier,
and saves the model + scaler to disk.

Run this ONCE before starting the Flask app:
    python train_model.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import pickle
import os

# ──────────────────────────────────────────────
# 1.  Generate a synthetic dataset
# ──────────────────────────────────────────────
np.random.seed(42)
N = 2000  # number of samples

ages             = np.random.randint(18, 70, N)
genders          = np.random.randint(0, 2, N)          # 0 = Female, 1 = Male
time_spent       = np.random.uniform(0.5, 60, N)       # minutes on site
prev_purchases   = np.random.randint(0, 20, N)         # past purchase count
pages_visited    = np.random.randint(1, 30, N)         # pages viewed
cart_items       = np.random.randint(0, 10, N)         # items in cart
discount_used    = np.random.randint(0, 2, N)          # used a discount?

# Simulate purchase probability with a realistic formula
purchase_score = (
    0.3  * (time_spent / 60)
    + 0.25 * (prev_purchases / 20)
    + 0.15 * (cart_items / 10)
    + 0.1  * (pages_visited / 30)
    + 0.1  * discount_used
    + 0.05 * (1 - (abs(ages - 35) / 35))   # age closer to 35 → higher score
    + 0.05 * genders
    + np.random.normal(0, 0.05, N)          # noise
)

will_purchase = (purchase_score > 0.45).astype(int)

df = pd.DataFrame({
    "age":             ages,
    "gender":          genders,
    "time_spent":      time_spent,
    "prev_purchases":  prev_purchases,
    "pages_visited":   pages_visited,
    "cart_items":      cart_items,
    "discount_used":   discount_used,
    "will_purchase":   will_purchase,
})

# Save dataset for reference
df.to_csv("dataset.csv", index=False)
print(f"✅  Dataset saved: dataset.csv  ({N} rows)")
print(f"    Purchase rate: {will_purchase.mean()*100:.1f}%")

# ──────────────────────────────────────────────
# 2.  Feature engineering & train/test split
# ──────────────────────────────────────────────
FEATURES = ["age", "gender", "time_spent", "prev_purchases",
            "pages_visited", "cart_items", "discount_used"]
TARGET   = "will_purchase"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ──────────────────────────────────────────────
# 3.  Scale features
# ──────────────────────────────────────────────
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# ──────────────────────────────────────────────
# 4.  Train Random Forest (primary model)
# ──────────────────────────────────────────────
rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train_scaled, y_train)

rf_preds = rf_model.predict(X_test_scaled)
rf_acc   = accuracy_score(y_test, rf_preds)

print(f"\n🌳  Random Forest Accuracy: {rf_acc*100:.2f}%")
print(classification_report(y_test, rf_preds, target_names=["No Purchase","Purchase"]))

# ──────────────────────────────────────────────
# 5.  Save model + scaler + metadata
# ──────────────────────────────────────────────
model_bundle = {
    "model":    rf_model,
    "scaler":   scaler,
    "features": FEATURES,
    "accuracy": round(rf_acc * 100, 2),
}

with open("model.pkl", "wb") as f:
    pickle.dump(model_bundle, f)

print("\n✅  Model saved: model.pkl")
print("🚀  You can now start the Flask app:  python app.py")
