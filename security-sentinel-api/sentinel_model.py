"""
SentinelModel — Hybrid anomaly detector.
Kept in its own file so pickle can always resolve the class path.
"""

import numpy as np
from sklearn.ensemble import IsolationForest

# Hard rule thresholds for obvious DDoS patterns
# Features are normalized to [0,1] range by StandardScaler in data_loader  
# These thresholds match the normalized feature scale (0-1)
# SAFE DEFAULTS: Only trigger on EXTREME attack patterns
DDOS_RATE_THRESHOLD    = 0.99  # >990 req/s in normalized space = extreme DDoS only
DDOS_PAYLOAD_THRESHOLD = 0.01  # <100 bytes in normalized space = extremely small payloads


class SentinelModel:
    """
    Hybrid anomaly detector:
      1. Hard rules catch EXTREME obvious DDoS patterns (rate > 0.9 & payload < 0.1).
      2. Isolation Forest handles subtle anomalies (bots, slow attacks, protocol abuse).

    Strategy: Hard rules for classic DDoS (high rate + small payload).
              Isolation Forest for behavioral/protocol anomalies.

    predict() mirrors sklearn convention:  1 = normal,  -1 = anomaly
    """

    def __init__(self, iso_forest: IsolationForest,
                 rate_threshold: float    = DDOS_RATE_THRESHOLD,
                 payload_threshold: float = DDOS_PAYLOAD_THRESHOLD):
        self.iso_forest        = iso_forest
        self.rate_threshold    = rate_threshold
        self.payload_threshold = payload_threshold

    def _rule_based(self, X: np.ndarray) -> np.ndarray:
        # Classic DDoS pattern: very high rate AND very low payload
        is_ddos = (X[:, 0] > self.rate_threshold) & (X[:, 1] < self.payload_threshold)
        return np.where(is_ddos, -1, 0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        rule_preds = self._rule_based(X)
        if_preds   = self.iso_forest.predict(X)
        return np.where(rule_preds != 0, rule_preds, if_preds)

    def fit(self, X: np.ndarray) -> "SentinelModel":
        self.iso_forest.fit(X)
        return self
