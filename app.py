# app.py  ── full, working version ──────────────────────────────────
from pathlib import Path
from flask import Flask, render_template, request, jsonify
import pandas as pd
import joblib

# ── 1.  Init Flask first ───────────────────────────────────────────
app = Flask(__name__)

# ── 2.  Load CSV & build brand‑model map ───────────────────────────
# ── 2.  Load CSV & build brand‑model map ───────────────────────────
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

df = pd.read_csv(os.path.join(BASE_DIR, "Cardetails.csv"))

# ✅ Add brand/model columns if missing
if 'brand' not in df.columns or 'model' not in df.columns:
    df['brand'] = df['name'].str.split().str[0]
    df['model'] = df.apply(
        lambda r: r['name'].replace(r['brand'] + ' ', '', 1),
        axis=1
    )

# ✅ Now safe to build brand → models mapping
brand_models = (df.groupby("brand")["model"]
                  .unique()
                  .apply(list)
                  .to_dict())

# ----------  NEW: (brand, model) → list of years  ----------
model_years = (
    df.groupby(["brand", "model"])["year"]
      .unique()
      .apply(lambda arr: sorted(arr.tolist()))
      .to_dict()          # key = (brand, model) tuple
)

# ----------  NEW: endpoint that returns valid years  ----------
@app.route("/years/<brand>/<model>")
def years_api(brand, model):
    years = model_years.get((brand, model), [])
    return jsonify(years)



# ── 3.  Tiny API for dropdown ──────────────────────────────────────
@app.route("/brand_models")
def brand_models_api():
    return jsonify(brand_models)

# ── 4.  Main pages & prediction ────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

# Load trained ML pipeline once
model = joblib.load("Model/car_model.pkl")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        input_df = pd.DataFrame([data])
        pred = model.predict(input_df)[0]
        return jsonify({"prediction": int(pred)})
    except Exception as e:
        return jsonify({"error": str(e)})

# ── 5.  Run dev server ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
