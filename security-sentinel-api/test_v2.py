#!/usr/bin/env python3
"""Quick test of the v2 implementation"""

import sys
sys.path.insert(0, '.')

print("\n" + "="*60)
print("  Test 1: Preprocessor (12 features)")
print("="*60 + "\n")

from preprocessor import extract_features
import numpy as np

request1 = {
    'request_rate': 5.0,
    'payload_size': 1024,
    'user_agent': 'Mozilla/5.0',
    'dest_port': 443,
    'protocol': 'TCP',
    'ttl': 64
}

features = extract_features(request1)
print(f"✓ Features shape: {features.shape}")
print(f"✓ Features dtype: {features.dtype}")
print(f"✓ Feature vector: {features}")
assert features.shape == (12,), f"Expected shape (12,), got {features.shape}"
assert features.dtype == np.float32, f"Expected dtype float32, got {features.dtype}"
print("✓ Preprocessor test PASSED\n")

print("="*60)
print("  Test 2: Training script (synthetic data)")
print("="*60 + "\n")

from train_sentinel import load_training_data, train_model, evaluate_model

X_train, y_train, X_test, y_test = load_training_data(use_real_data=False)
print(f"✓ Train set: {X_train.shape}")
print(f"✓ Test set: {X_test.shape}")
assert X_train.shape[1] == 12, f"Expected 12 features, got {X_train.shape[1]}"
print("✓ Data loading test PASSED\n")

print("="*60)
print("  Test 3: Model training")
print("="*60 + "\n")

from sklearn.model_selection import train_test_split
X_train_split, X_val, y_train_split, y_val = train_test_split(
    X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
)

model, thresholds = train_model(X_train_split, y_train_split, contamination=(y_train_split == -1).mean())
print(f"✓ Model trained successfully")
print(f"✓ Rate threshold: {thresholds['ddos_rate_threshold']:.2f}")
print(f"✓ Payload threshold: {thresholds['ddos_payload_threshold']:.2f}")
print("✓ Model training test PASSED\n")

print("="*60)
print("  Test 4: Inference")
print("="*60 + "\n")

y_pred = model.predict(X_test[:10])
print(f"✓ Predictions shape: {y_pred.shape}")
print(f"✓ Sample predictions: {y_pred}")
assert y_pred.shape == (10,), f"Expected shape (10,), got {y_pred.shape}"
print("✓ Inference test PASSED\n")

print("="*60)
print("  Test 5: Model evaluation")
print("="*60 + "\n")

metrics = evaluate_model(model, X_test, y_test)
print(f"✓ Test Accuracy: {metrics['test_accuracy']:.4f}")
print(f"✓ Evaluation test PASSED\n")

print("\n" + "="*60)
print("  ✅ All tests PASSED!")
print("="*60 + "\n")
print("Next steps:")
print("1. Train full model: python train_sentinel.py")
print("2. Start API server: python main.py")
print("3. Test API: curl -X POST http://localhost:8000/score ...")
