"""
train_sentinel.py - v2
Train the Isolation Forest on real network data (CICIDS2018) or synthetic data.

Key Improvements:
1. Loads from CICIDS2018 real network attack dataset (440K+ samples)
2. Supports 12 features instead of 4
3. Auto-tunes hard rule thresholds based on data percentiles
4. Implements 5-fold cross-validation for robustness
5. Saves both model and metadata (thresholds, feature importance)

Persistence:
- Only the sklearn IsolationForest is pickled (pure sklearn, no custom classes)
- SentinelModel wrapper is rebuilt at load time
- Thresholds are saved separately in THRESHOLDS_PATH
"""

import os
import sys
import pickle
import time
import warnings
import json
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict

# Import data loader and model
try:
    from data_loader import load_cicids2018, load_fallback_data
except ImportError:
    print("Warning: data_loader not found, will use synthetic data only")
    load_cicids2018 = None
    load_fallback_data = None

from sentinel_model import SentinelModel

warnings.filterwarnings("ignore")

# Configuration
RANDOM_STATE = 42
MODEL_PATH = "sentinel_model_v2.pkl"
THRESHOLDS_PATH = "sentinel_thresholds_v2.json"
EVALUATION_PATH = "evaluation_report_v2.txt"

# Hard rule thresholds (will be auto-tuned)
DEFAULT_DDOS_RATE_THRESHOLD = 60.0
DEFAULT_DDOS_PAYLOAD_THRESHOLD = 150.0


def auto_tune_thresholds(X_train: np.ndarray, y_train: np.ndarray, 
                        contamination: float = 0.05) -> Dict[str, float]:
    """
    Auto-tune hard rule thresholds based on training data percentiles.
    
    The rule: request_rate > threshold AND payload_size < threshold = ANOMALY
    
    Strategy:
    - Set request_rate threshold = 95th percentile of normal traffic (benign)
    - Set payload_size threshold = 5th percentile of attack traffic
    
    This minimizes false positives while catching DDoS patterns.
    
    Args:
        X_train: Training features (N, 12)
        y_train: Training labels (1=benign, -1=attack)
        contamination: Expected contamination rate (default 0.05 = 5% for production)
        
    Returns:
        Dict with tuned thresholds
    """
    print("🔧 Auto-tuning hard rule thresholds...")
    
    # Extract features 0 and 1 (request_rate and payload_size)
    request_rate = X_train[:, 0]
    payload_size = X_train[:, 1]
    
    # Benign traffic: y_train == 1
    benign_mask = y_train == 1
    attack_mask = y_train == -1
    
    # Threshold: 95th percentile of benign request rate
    rate_threshold = np.percentile(request_rate[benign_mask], 95) if benign_mask.sum() > 0 else DEFAULT_DDOS_RATE_THRESHOLD
    
    # Threshold: 5th percentile of attack payload size
    payload_threshold = np.percentile(payload_size[attack_mask], 5) if attack_mask.sum() > 0 else DEFAULT_DDOS_PAYLOAD_THRESHOLD
    
    thresholds = {
        "ddos_rate_threshold": float(rate_threshold),
        "ddos_payload_threshold": float(payload_threshold),
        "contam_rate": float(contamination)  # Use the conservative contamination for production
    }
    
    print(f"   Request Rate Threshold: {rate_threshold:.2f} req/s")
    print(f"   Payload Size Threshold: {payload_threshold:.2f} bytes")
    print(f"   Contamination Rate: {thresholds['contam_rate']:.2%}\n")
    
    return thresholds


def generate_synthetic_training_data(n_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fallback: Generate synthetic 12-feature training data.
    
    Used when CICIDS2018 is not available.
    
    Args:
        n_samples: Total samples to generate
        
    Returns:
        Tuple of (X, y) with 12 features
    """
    print("⚠️  Generating synthetic training data (CICIDS2018 not available)")
    print("    Real data recommended for production models\n")
    
    rng = np.random.default_rng(RANDOM_STATE)
    
    # Normal traffic (1000 samples, 12 features)
    normal = np.column_stack([
        rng.uniform(1, 10, 1000),           # 0: request_rate
        rng.uniform(500, 8000, 1000),       # 1: payload_size
        rng.uniform(5, 50, 1000),           # 2: pkt_count
        rng.uniform(0.6, 0.95, 1000),       # 3: byte_ratio
        rng.uniform(0.01, 0.1, 1000),       # 4: is_syn_flood
        rng.uniform(10, 500, 1000),         # 5: header_entropy
        rng.uniform(0.0, 0.2, 1000),        # 6: port_diversity
        rng.uniform(0.0, 0.1, 1000),        # 7: ttl_anomaly
        rng.uniform(0.0, 0.05, 1000),       # 8: fragmentation
        rng.uniform(0.0, 0.02, 1000),       # 9: protocol_abuse
        np.ones(1000),                      # 10: is_common_user_agent
        rng.uniform(8, 22, 1000),           # 11: time_of_day
    ])
    
    # DDoS traffic (500 samples)
    ddos = np.column_stack([
        rng.uniform(100, 500, 500),         # High request rate
        rng.uniform(5, 80, 500),            # Low payload
        rng.uniform(20, 200, 500),
        rng.uniform(0.05, 0.2, 500),
        rng.uniform(0.5, 1.0, 500),         # High SYN flooding
        rng.uniform(1, 100, 500),
        rng.uniform(0.0, 0.3, 500),
        rng.uniform(0.0, 0.15, 500),
        rng.uniform(0.0, 0.1, 500),
        rng.uniform(0.0, 0.05, 500),
        rng.uniform(0.0, 0.2, 500),
        rng.uniform(0, 24, 500),
    ])
    
    # Bot traffic (200 samples)
    bot = np.column_stack([
        rng.uniform(15, 40, 200),           # Moderate request rate
        rng.uniform(300, 2000, 200),
        rng.uniform(10, 100, 200),
        rng.uniform(0.4, 0.7, 200),
        rng.uniform(0.1, 0.3, 200),
        rng.uniform(5, 300, 200),
        rng.uniform(0.2, 0.8, 200),         # Higher port diversity (curiosity)
        rng.uniform(0.1, 0.4, 200),
        rng.uniform(0.1, 0.3, 200),
        rng.uniform(0.1, 0.4, 200),
        rng.uniform(0.0, 0.5, 200),
        rng.uniform(0, 6, 200),             # Mostly night activity
    ])
    
    X = np.vstack([normal, ddos, bot])
    y = np.concatenate([
        np.ones(len(normal)),
        -np.ones(len(ddos)),
        -np.ones(len(bot))
    ])
    
    print(f"Synthetic Dataset: {len(X)} samples  |  Normal: {(y==1).sum()}  |  Anomalous: {(y==-1).sum()}\n")
    
    return X, y


def load_training_data(use_real_data: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load training data from CICIDS2018 (real) or synthetic fallback.
    
    Args:
        use_real_data: If True, attempt CICIDS2018. If False, generate synthetic.
        
    Returns:
        Tuple of (X_train, y_train, X_test, y_test)
    """
    print("=" * 60)
    print("  Loading Training Data")
    print("=" * 60 + "\n")
    
    if use_real_data:
        try:
            X_train, y_train, X_test, y_test = load_cicids2018(test_size=0.25)
            
            if X_train is not None:
                print("✓ CICIDS2018 data loaded successfully\n")
                return X_train, y_train, X_test, y_test
        except Exception as e:
            print(f"⚠️  Failed to load CICIDS2018: {e}")
            print("Falling back to synthetic data...\n")
    
    # Fallback to synthetic data
    X, y = generate_synthetic_training_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
    )
    
    return X_train, y_train, X_test, y_test


def train_model(X_train: np.ndarray, y_train: np.ndarray, 
                contamination: float) -> Tuple[SentinelModel, Dict]:
    """
    Train the Isolation Forest model with auto-tuned thresholds.
    
    Args:
        X_train: Training features (N, 12)
        y_train: Training labels
        contamination: Fraction of anomalies in training set (use 0.05 for production)
        
    Returns:
        Tuple of (trained_model, thresholds_dict)
    """
    print("=" * 60)
    print("  Training Isolation Forest")
    print("=" * 60 + "\n")
    
    # Auto-tune thresholds with conservative contamination
    thresholds = auto_tune_thresholds(X_train, y_train, contamination=contamination)
    
    # Train model
    print("Training model...")
    t0 = time.time()
    
    iso_forest = IsolationForest(
        n_estimators=300,
        contamination=contamination,
        max_samples=256,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    
    iso_forest.fit(X_train)
    
    elapsed = time.time() - t0
    print(f"✓ Training complete in {elapsed:.2f}s\n")
    
    # Wrap in SentinelModel with tuned thresholds
    model = SentinelModel(
        iso_forest,
        rate_threshold=thresholds["ddos_rate_threshold"],
        payload_threshold=thresholds["ddos_payload_threshold"]
    )
    
    return model, thresholds


def evaluate_model(model: SentinelModel, X_test: np.ndarray, y_test: np.ndarray, 
                   X_val: np.ndarray = None, y_val: np.ndarray = None) -> Dict:
    """
    Comprehensive model evaluation with multiple metrics.
    
    Args:
        model: Trained SentinelModel
        X_test: Test features
        y_test: Test labels
        X_val: Optional validation features
        y_val: Optional validation labels
        
    Returns:
        Dict with evaluation metrics
    """
    print("=" * 60)
    print("  Model Evaluation")
    print("=" * 60 + "\n")
    
    metrics = {}
    
    # Evaluate on test set
    y_pred_test = model.predict(X_test)
    
    test_accuracy = accuracy_score(y_test, y_pred_test)
    test_precision = precision_score(y_test, y_pred_test, zero_division=0)
    test_recall = recall_score(y_test, y_pred_test, zero_division=0)
    test_f1 = f1_score(y_test, y_pred_test, zero_division=0)
    
    print("📊 Test Set Metrics:")
    print(f"   Accuracy:  {test_accuracy:.4f} ({test_accuracy:.2%})")
    print(f"   Precision: {test_precision:.4f} ({test_precision:.2%})")
    print(f"   Recall:    {test_recall:.4f} ({test_recall:.2%})")
    print(f"   F1-Score:  {test_f1:.4f}\n")
    
    metrics["test_accuracy"] = float(test_accuracy)
    metrics["test_precision"] = float(test_precision)
    metrics["test_recall"] = float(test_recall)
    metrics["test_f1"] = float(test_f1)
    
    # Detailed classification report
    print("Classification Report (Test Set):")
    print(classification_report(y_test, y_pred_test, target_names=["Attack", "Benign"]))
    
    # DDoS-specific accuracy
    if X_test.shape[1] >= 1:
        ddos_mask = X_test[:, 0] > 60
        if ddos_mask.sum() > 0:
            ddos_acc = accuracy_score(y_test[ddos_mask], y_pred_test[ddos_mask])
            print(f"DDoS Accuracy (request_rate > 60): {ddos_acc:.2%}")
            metrics["ddos_accuracy"] = float(ddos_acc)
    
    # Validate on validation set if provided
    if X_val is not None and y_val is not None:
        y_pred_val = model.predict(X_val)
        val_accuracy = accuracy_score(y_val, y_pred_val)
        print(f"\n✓ Validation Accuracy: {val_accuracy:.2%}")
        metrics["val_accuracy"] = float(val_accuracy)
    
    print()
    return metrics


def cross_validate(X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> Dict:
    """
    Perform k-fold cross-validation to assess generalization.
    
    Args:
        X: Features
        y: Labels
        n_splits: Number of folds
        
    Returns:
        Dict with per-fold and average metrics
    """
    print("=" * 60)
    print("  Cross-Validation (5-Fold)")
    print("=" * 60 + "\n")
    
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    
    fold_scores = {"accuracy": [], "precision": [], "recall": [], "f1": []}
    
    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y), 1):
        X_cv_train, X_cv_val = X[train_idx], X[val_idx]
        y_cv_train, y_cv_val = y[train_idx], y[val_idx]
        
        # Train on this fold
        contam = (y_cv_train == -1).mean()
        iso = IsolationForest(
            n_estimators=300,
            contamination=contam,
            max_samples=256,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        iso.fit(X_cv_train)
        model_cv = SentinelModel(iso)
        
        # Evaluate
        y_pred_cv = model_cv.predict(X_cv_val)
        acc = accuracy_score(y_cv_val, y_pred_cv)
        prec = precision_score(y_cv_val, y_pred_cv, zero_division=0)
        rec = recall_score(y_cv_val, y_pred_cv, zero_division=0)
        f1 = f1_score(y_cv_val, y_pred_cv, zero_division=0)
        
        fold_scores["accuracy"].append(acc)
        fold_scores["precision"].append(prec)
        fold_scores["recall"].append(rec)
        fold_scores["f1"].append(f1)
        
        print(f"Fold {fold}: Acc={acc:.4f}, Prec={prec:.4f}, Rec={rec:.4f}, F1={f1:.4f}")
    
    print(f"\nAverage Accuracy:  {np.mean(fold_scores['accuracy']):.4f} ± {np.std(fold_scores['accuracy']):.4f}")
    print(f"Average Precision: {np.mean(fold_scores['precision']):.4f} ± {np.std(fold_scores['precision']):.4f}")
    print(f"Average Recall:    {np.mean(fold_scores['recall']):.4f} ± {np.std(fold_scores['recall']):.4f}")
    print(f"Average F1-Score:  {np.mean(fold_scores['f1']):.4f} ± {np.std(fold_scores['f1']):.4f}\n")
    
    return fold_scores


def save_model(model: SentinelModel, thresholds: Dict, path: str = MODEL_PATH, 
               thresholds_path: str = THRESHOLDS_PATH):
    """
    Save model and thresholds to disk.
    
    Args:
        model: Trained SentinelModel
        thresholds: Dict of tuned thresholds
        path: Path to save model pickle
        thresholds_path: Path to save thresholds JSON
    """
    print("=" * 60)
    print("  Saving Model")
    print("=" * 60 + "\n")
    
    # Save Isolation Forest (only the sklearn part)
    with open(path, "wb") as f:
        pickle.dump(model.iso_forest, f)
    print(f"✓ Model saved → {path}")
    
    # Save thresholds for reproducibility
    with open(thresholds_path, "w") as f:
        json.dump(thresholds, f, indent=2)
    print(f"✓ Thresholds saved → {thresholds_path}\n")


def load_model(path: str = MODEL_PATH, thresholds_path: str = THRESHOLDS_PATH) -> Tuple[SentinelModel, Dict]:
    """
    Load model and thresholds from disk.
    
    Args:
        path: Path to model pickle
        thresholds_path: Path to thresholds JSON
        
    Returns:
        Tuple of (model, thresholds_dict)
    """
    with open(path, "rb") as f:
        iso_forest = pickle.load(f)
    
    with open(thresholds_path, "r") as f:
        thresholds = json.load(f)
    
    model = SentinelModel(
        iso_forest,
        rate_threshold=thresholds["ddos_rate_threshold"],
        payload_threshold=thresholds["ddos_payload_threshold"]
    )
    
    return model, thresholds


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  🔐 AI Security Sentinel v2 - Training")
    print("  Real Data + 12 Features + Auto-Tuned Thresholds")
    print("=" * 60 + "\n")
    
    # Load data
    X_train, y_train, X_test, y_test = load_training_data(use_real_data=True)
    
    # Further split train into train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=RANDOM_STATE, stratify=y_train
    )
    
    print(f"📊 Data Split:")
    print(f"   Train: {len(X_train):,}")
    print(f"   Val:   {len(X_val):,}")
    print(f"   Test:  {len(X_test):,}\n")
    
    # Train model with 12 features
    # Use conservative contamination rate (5%) for production
    # CICIDS2018 has 27% attacks, but in production most traffic is legitimate
    # Lower contamination = less aggressive anomaly detection = fewer false positives
    actual_contam = (y_train == -1).mean()
    production_contam = min(0.05, actual_contam)  # Use 5% or actual if lower
    model, thresholds = train_model(X_train, y_train, contamination=production_contam)
    
    # Evaluate on validation and test sets
    evaluate_model(model, X_val, y_val, X_test, y_test)
    
    # Cross-validate for robustness
    cv_scores = cross_validate(X_train, y_train, n_splits=5)
    
    # Save model
    save_model(model, thresholds)
    
    print("=" * 60)
    print("  ✓ Training Complete!")
    print("  Model v2 ready for inference")
    print("=" * 60 + "\n")
