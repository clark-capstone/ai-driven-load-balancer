import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from fastapi import FastAPI
from preprocessor import extract_features
from sentinel_model import SentinelModel
from train_sentinel import load_model

app = FastAPI()
model = load_model("sentinel_model.pkl")

@app.post("/score")
def score_request(request: dict):
    features = extract_features(request)
    prediction = model.predict(np.array([features]))[0]  # 👈 wrap in np.array
    return {"result": "block" if prediction == -1 else "allow"}