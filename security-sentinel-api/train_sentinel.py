"""
train_sentinel.py
Trains the Isolation Forest and saves ONLY the sklearn IsolationForest object.
The SentinelModel wrapper is rebuilt at load time — no custom class in the .pkl.
"""

import pickle, time, warnings
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sentinel_model import SentinelModel

warnings.filterwarnings("ignore")
RANDOM_STATE = 42
MODEL_PATH   = "sentinel_model.pkl"


def generate_normal_traffic(n=2000):
    rng = np.random.default_rng(RANDOM_STATE)
    return np.column_stack([
        rng.uniform(1, 10, n),
        rng.uniform(500, 8000, n),
        rng.choice([1.0, 0.0], size=n, p=[0.92, 0.08]),
        rng.uniform(8, 22, n),
    ])

def generate_ddos_traffic(n=500):
    rng = np.random.default_rng(RANDOM_STATE + 1)
    return np.column_stack([
        rng.uniform(100, 500, n),
        rng.uniform(5, 80, n),
        rng.choice([1.0, 0.0], size=n, p=[0.05, 0.95]),
        rng.uniform(0, 24, n),
    ])

def generate_bot_traffic(n=200):
    rng = np.random.default_rng(RANDOM_STATE + 2)
    return np.column_stack([
        rng.uniform(15, 40, n),
        rng.uniform(300, 2000, n),
        rng.choice([1.0, 0.0], size=n, p=[0.50, 0.50]),
        rng.uniform(0, 6, n),
    ])

def build_dataset():
    normal = generate_normal_traffic()
    ddos   = generate_ddos_traffic()
    bots   = generate_bot_traffic()
    X = np.vstack([normal, ddos, bots])
    y = np.concatenate([np.ones(len(normal)), -np.ones(len(ddos)), -np.ones(len(bots))])
    print(f"Dataset: {len(X)} samples  |  Normal: {(y==1).sum()}  |  Anomalous: {(y==-1).sum()}\n")
    return X, y

def train(X_train, contamination):
    iso = IsolationForest(n_estimators=300, contamination=contamination,
                          max_samples=256, random_state=RANDOM_STATE, n_jobs=-1)
    model = SentinelModel(iso)
    model.fit(X_train)
    return model

def evaluate(model, X_test, y_test):
    y_pred = model.predict(X_test)
    print(f"Overall Accuracy : {accuracy_score(y_test, y_pred):.2%}")
    print(classification_report(y_test, y_pred, target_names=["Anomaly", "Normal"]))
    ddos_mask = X_test[:, 0] > 60
    if ddos_mask.sum():
        ddos_acc = accuracy_score(y_test[ddos_mask], y_pred[ddos_mask])
        print(f"DDoS Accuracy: {ddos_acc:.2%}")
        assert ddos_acc >= 0.90
        print("DDoS detection >= 90%\n")

# Only the inner IsolationForest is pickled (pure sklearn, no custom class).
# load_model() rewraps it in SentinelModel at runtime.
def save_model(model: SentinelModel, path=MODEL_PATH):
    with open(path, "wb") as f:
        pickle.dump(model.iso_forest, f)
    print(f"Model saved -> {path}")

def load_model(path=MODEL_PATH) -> SentinelModel:
    with open(path, "rb") as f:
        iso_forest = pickle.load(f)
    return SentinelModel(iso_forest)


if __name__ == "__main__":
    print("=" * 50)
    print("  AI Security Sentinel - Training")
    print("=" * 50 + "\n")

    X, y = build_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y)

    print("Training...")
    t0 = time.time()
    model = train(X_train, contamination=(y_train == -1).mean())
    print(f"Done in {time.time()-t0:.2f}s\n")

    evaluate(model, X_test, y_test)
    save_model(model)
    print("All checks passed. Ready for inference.")
