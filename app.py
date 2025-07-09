# AutoWorth‑AI • Flask back‑end


from pathlib import Path
from flask import Flask, render_template, request, jsonify
import pandas as pd
import joblib

# ──────────────────────────────────────────────────────────────
# 1.  Flask app — nothing fancy, just the default instance
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)

# ──────────────────────────────────────────────────────────────
# 2.  File paths + load data / model
#     (using pathlib keeps things OS‑agnostic on Render, Windows, etc.)
# ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent / "CAR PRICE"

CSV_PATH  = BASE_DIR / "Cardetails.csv"
MODEL_PATH = BASE_DIR / "Model" / "car_model.pkl"

# load the dataset we use for lookups
df = pd.read_csv(CSV_PATH)

# load the trained scikit‑learn pipeline (once per process)
model = joblib.load(MODEL_PATH)

# ──────────────────────────────────────────────────────────────
# 3.  Derive helper columns if the raw CSV doesn’t have them
# ──────────────────────────────────────────────────────────────
if {"brand", "model"}.issubset(df.columns) is False:
    df["brand"] = df["name"].str.split().str[0]
    df["model"] = df.apply(
        lambda r: r["name"].replace(r["brand"] + " ", "", 1),
        axis=1
    )

# after the optional patch, build lookup dictionaries
brand_models = (
    df.groupby("brand")["model"]
      .unique()
      .apply(list)
      .to_dict()
)

model_years = (
    df.groupby(["brand", "model"])["year"]
      .unique()
      .apply(lambda arr: sorted(arr.tolist()))
      .to_dict()               # key = (brand, model) tuple
)

# ──────────────────────────────────────────────────────────────
# 4.  Routes:   dropdown helpers  +  home page  +  prediction
# ──────────────────────────────────────────────────────────────
@app.route("/brand_models")
def get_brand_models():
    """Return { brand: [model, …], … } for the first dropdown."""
    return jsonify(brand_models)


@app.route("/years/<brand>/<model>")
def get_years(brand: str, model: str):
    """Return a list of valid years for the selected brand/model combo."""
    return jsonify(model_years.get((brand, model), []))


@app.route("/")
def home():
    """Serve the main HTML page."""
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    """
    Receive a JSON body describing a single car and return the
    estimated resale price.  All feature names must match what
    the model was trained on.
    """
    try:
        data = request.get_json(force=True)
        input_df = pd.DataFrame([data])
        price = int(model.predict(input_df)[0])
        return jsonify({"prediction": price})
    except Exception as err:
        return jsonify({"error": str(err)}), 400

# ──────────────────────────────────────────────────────────────
# 5.  Entrypoint
#     Bind to the PORT environment variable if Render supplies it;
#     otherwise fall back to 5000 for local development.
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
