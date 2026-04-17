"""
app.py
======
Flask backend for the AI-Based E-commerce Customer Purchase Predictor.

Endpoints:
  GET  /              → Home page
  GET  /predict       → Prediction form page
  POST /api/predict   → JSON prediction API
  GET  /dashboard     → Past predictions dashboard
  GET  /api/history   → JSON history of predictions
  DELETE /api/history → Clear all history

Run:
    python app.py
"""

import os
import pickle
import sqlite3
import datetime
import json
from flask import Flask, request, jsonify, render_template, g

# ──────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────
app = Flask(__name__)
DATABASE = "predictions.db"

# ──────────────────────────────────────────────
# Load ML model bundle (model + scaler)
# ──────────────────────────────────────────────
MODEL_PATH = "model.pkl"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        "model.pkl not found. Please run  python train_model.py  first."
    )

with open(MODEL_PATH, "rb") as f:
    bundle = pickle.load(f)

model    = bundle["model"]
scaler   = bundle["scaler"]
FEATURES = bundle["features"]
MODEL_ACC = bundle.get("accuracy", "N/A")

print(f"✅  Model loaded  |  Accuracy: {MODEL_ACC}%  |  Features: {FEATURES}")

# ──────────────────────────────────────────────
# Database helpers (SQLite)
# ──────────────────────────────────────────────
def get_db():
    """Return a database connection for the current request context."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    """Create tables if they don't exist."""
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                age             INTEGER,
                gender          TEXT,
                time_spent      REAL,
                prev_purchases  INTEGER,
                pages_visited   INTEGER,
                cart_items      INTEGER,
                discount_used   INTEGER,
                prediction      TEXT,
                confidence      REAL,
                created_at      TEXT
            )
        """)
        db.commit()

# Initialise DB on startup
init_db()

# ──────────────────────────────────────────────
# Recommendation engine (rule-based)
# ──────────────────────────────────────────────
def get_recommendations(features: dict, prediction: str, confidence: float) -> list:
    """Return tailored recommendations based on user behaviour."""
    recs = []

    if prediction == "Will Not Purchase":
        if features["time_spent"] < 5:
            recs.append("🕐 Engage users longer with interactive product demos or videos.")
        if features["prev_purchases"] == 0:
            recs.append("🎁 Offer a first-time buyer discount to reduce purchase friction.")
        if features["cart_items"] == 0:
            recs.append("🛒 Trigger smart product recommendations to fill the cart.")
        if features["discount_used"] == 0:
            recs.append("🏷️ Send a personalised coupon — discount-sensitive users convert 2×.")
        if confidence < 0.65:
            recs.append("📧 Set up an abandoned-session email sequence for this segment.")
    else:
        if features["cart_items"] > 3:
            recs.append("💡 Suggest bundle deals — high cart volume signals upsell opportunity.")
        if features["prev_purchases"] > 5:
            recs.append("⭐ Invite this customer to your loyalty / VIP programme.")
        if features["time_spent"] > 30:
            recs.append("🔔 Enable wishlist alerts — engaged browsers convert on price drops.")
        recs.append("📦 Offer expedited shipping at checkout to seal the deal.")

    return recs[:4]  # cap at 4 tips

# ──────────────────────────────────────────────
# Routes — Pages
# ──────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict")
def predict_page():
    return render_template("predict.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ──────────────────────────────────────────────
# Routes — API
# ──────────────────────────────────────────────
@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Accepts JSON:
    {
        "age": 28,
        "gender": 1,
        "time_spent": 12.5,
        "prev_purchases": 3,
        "pages_visited": 7,
        "cart_items": 2,
        "discount_used": 1
    }
    Returns prediction, confidence, and recommendations.
    """
    try:
        data = request.get_json(force=True)

        # ── Validate required fields ──────────────────
        required = ["age", "gender", "time_spent", "prev_purchases",
                    "pages_visited", "cart_items", "discount_used"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        # ── Parse & validate values ───────────────────
        age            = int(data["age"])
        gender         = int(data["gender"])           # 0 or 1
        time_spent     = float(data["time_spent"])
        prev_purchases = int(data["prev_purchases"])
        pages_visited  = int(data["pages_visited"])
        cart_items     = int(data["cart_items"])
        discount_used  = int(data["discount_used"])    # 0 or 1

        if not (18 <= age <= 100):
            return jsonify({"error": "Age must be between 18 and 100."}), 400
        if gender not in (0, 1):
            return jsonify({"error": "Gender must be 0 (Female) or 1 (Male)."}), 400
        if time_spent < 0:
            return jsonify({"error": "Time spent cannot be negative."}), 400
        if prev_purchases < 0:
            return jsonify({"error": "Previous purchases cannot be negative."}), 400

        # ── Build feature vector ──────────────────────
        feature_values = [[age, gender, time_spent, prev_purchases,
                           pages_visited, cart_items, discount_used]]
        feature_scaled = scaler.transform(feature_values)

        # ── Predict ───────────────────────────────────
        raw_pred   = model.predict(feature_scaled)[0]
        proba      = model.predict_proba(feature_scaled)[0]
        confidence = round(float(proba[raw_pred]) * 100, 1)

        prediction = "Will Purchase" if raw_pred == 1 else "Will Not Purchase"

        # ── Recommendations ───────────────────────────
        feature_dict = {
            "age": age, "gender": gender, "time_spent": time_spent,
            "prev_purchases": prev_purchases, "pages_visited": pages_visited,
            "cart_items": cart_items, "discount_used": discount_used,
        }
        recommendations = get_recommendations(feature_dict, prediction, confidence / 100)

        # ── Persist to SQLite ─────────────────────────
        db = get_db()
        db.execute("""
            INSERT INTO predictions
              (age, gender, time_spent, prev_purchases, pages_visited,
               cart_items, discount_used, prediction, confidence, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            age,
            "Male" if gender == 1 else "Female",
            time_spent, prev_purchases, pages_visited, cart_items,
            discount_used, prediction, confidence,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
        db.commit()

        return jsonify({
            "prediction":      prediction,
            "confidence":      confidence,
            "will_buy":        bool(raw_pred == 1),
            "recommendations": recommendations,
            "model_accuracy":  MODEL_ACC,
        })

    except ValueError as ve:
        return jsonify({"error": f"Invalid value: {ve}"}), 400
    except Exception as e:
        app.logger.error(f"Prediction error: {e}")
        return jsonify({"error": "Internal server error. Please try again."}), 500


@app.route("/api/history", methods=["GET"])
def api_history():
    """Return the 50 most recent predictions."""
    try:
        db = get_db()
        rows = db.execute("""
            SELECT * FROM predictions
            ORDER BY id DESC
            LIMIT 50
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["DELETE"])
def api_clear_history():
    """Clear all saved predictions."""
    try:
        db = get_db()
        db.execute("DELETE FROM predictions")
        db.commit()
        return jsonify({"message": "History cleared."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return aggregate stats for the dashboard."""
    try:
        db = get_db()
        total = db.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
        buyers = db.execute(
            "SELECT COUNT(*) FROM predictions WHERE prediction='Will Purchase'"
        ).fetchone()[0]
        avg_conf = db.execute("SELECT AVG(confidence) FROM predictions").fetchone()[0]
        avg_age  = db.execute("SELECT AVG(age) FROM predictions").fetchone()[0]
        avg_time = db.execute("SELECT AVG(time_spent) FROM predictions").fetchone()[0]

        return jsonify({
            "total":         total,
            "buyers":        buyers,
            "non_buyers":    total - buyers,
            "buy_rate":      round((buyers / total * 100) if total else 0, 1),
            "avg_confidence": round(avg_conf or 0, 1),
            "avg_age":       round(avg_age or 0, 1),
            "avg_time_spent": round(avg_time or 0, 1),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀  E-commerce Purchase Predictor running at http://127.0.0.1:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
