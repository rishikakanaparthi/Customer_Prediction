# PurchaseIQ — AI-Based E-commerce Customer Purchase Predictor

A full-stack web application that predicts whether a customer will purchase a product based on their browsing behaviour, using a **Random Forest** classifier (90.5% accuracy).

---

## 📁 Project Structure

```
ecommerce_predictor/
├── app.py               ← Flask backend + API endpoints
├── train_model.py       ← ML training script (run once)
├── model.pkl            ← Saved model bundle (auto-generated)
├── dataset.csv          ← Synthetic training dataset (auto-generated)
├── predictions.db       ← SQLite database (auto-created)
├── requirements.txt     ← Python dependencies
├── templates/
│   ├── index.html       ← Home page
│   ├── predict.html     ← Prediction form page
│   └── dashboard.html   ← History & analytics dashboard
└── static/
    ├── css/style.css    ← All styles
    └── js/
        ├── main.js      ← Home page JS
        ├── predict.js   ← Form validation + API call
        └── dashboard.js ← Charts + history table
```

---

## 🚀 Quick Start (Local)

### 1. Prerequisites
- Python 3.9 or higher
- pip

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Train the ML model *(run once)*
```bash
python train_model.py
```
This generates `dataset.csv` and `model.pkl`.

### 4. Start the Flask server
```bash
python app.py
```

### 5. Open in your browser
```
http://127.0.0.1:5000
```

---

## 🧠 ML Model Details

| Property       | Value                      |
|---------------|---------------------------|
| Algorithm     | Random Forest Classifier  |
| n_estimators  | 200 trees                 |
| max_depth     | 8                         |
| Accuracy      | ~90.5%                    |
| Training data | 2 000 synthetic records   |
| Scaler        | StandardScaler            |

### Input features:
| Feature         | Type    | Range      | Description                    |
|----------------|---------|------------|-------------------------------|
| age             | int     | 18–100     | Customer age                  |
| gender          | int     | 0 or 1     | 0 = Female, 1 = Male          |
| time_spent      | float   | ≥ 0        | Minutes spent on the site     |
| prev_purchases  | int     | ≥ 0        | Number of historical orders   |
| pages_visited   | int     | ≥ 1        | Pages viewed in this session  |
| cart_items      | int     | ≥ 0        | Items currently in cart       |
| discount_used   | int     | 0 or 1     | Whether a coupon was applied  |

---

## 🌐 API Reference

### `POST /api/predict`
**Request body (JSON):**
```json
{
  "age": 28,
  "gender": 1,
  "time_spent": 12.5,
  "prev_purchases": 3,
  "pages_visited": 7,
  "cart_items": 2,
  "discount_used": 1
}
```

**Response:**
```json
{
  "prediction": "Will Purchase",
  "confidence": 87.3,
  "will_buy": true,
  "recommendations": ["⭐ Invite this customer to your loyalty programme."],
  "model_accuracy": 90.5
}
```

### `GET /api/history`
Returns the 50 most recent predictions as a JSON array.

### `DELETE /api/history`
Clears all stored predictions.

### `GET /api/stats`
Returns aggregate statistics (buy rate, average confidence, etc.).

---

## ☁️ Deployment

### Option A — Heroku
```bash
# Install Heroku CLI, then:
echo "web: python app.py" > Procfile
heroku create your-app-name
git init && git add . && git commit -m "initial"
heroku git:remote -a your-app-name
git push heroku main
```
Set `PORT` env var; update `app.run(port=int(os.environ.get("PORT", 5000)))`.

### Option B — Railway / Render
1. Push project to GitHub
2. Connect repo in Railway / Render dashboard
3. Set Start Command: `python app.py`
4. Deploy — done!

### Option C — Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python train_model.py
CMD ["python", "app.py"]
```
```bash
docker build -t purchaseiq .
docker run -p 5000:5000 purchaseiq
```

---

## ✅ Features Implemented

- [x] Random Forest ML model (90.5% accuracy)
- [x] Confidence scores for every prediction
- [x] Rule-based recommendation engine
- [x] SQLite persistence for prediction history
- [x] Prediction Dashboard with charts
- [x] Form validation (client + server side)
- [x] Responsive mobile-friendly UI
- [x] Loading animation on prediction
- [x] Error handling throughout

---

## 📝 License
MIT — free to use, modify, and deploy.
