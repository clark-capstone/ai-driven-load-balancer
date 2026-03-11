"""
SentinelModel — Hybrid anomaly detector.
Kept in its own file so pickle can always resolve the class path.
"""

import numpy as np
from sklearn.ensemble import IsolationForest

DDOS_RATE_THRESHOLD    = 60.0
DDOS_PAYLOAD_THRESHOLD = 150.0


class SentinelModel:
    """
    Hybrid anomaly detector:
      1. Hard rules catch clear DDoS bursts instantly.
      2. Isolation Forest handles the behavioural grey-zone (bots, slow attacks).

    predict() mirrors sklearn convention:  1 = normal,  -1 = anomaly
    """

    def __init__(self, iso_forest: IsolationForest,
                 rate_threshold: float    = DDOS_RATE_THRESHOLD,
                 payload_threshold: float = DDOS_PAYLOAD_THRESHOLD):
        self.iso_forest        = iso_forest
        self.rate_threshold    = rate_threshold
        self.payload_threshold = payload_threshold

    def _rule_based(self, X: np.ndarray) -> np.ndarray:
        is_ddos = (X[:, 0] > self.rate_threshold) & (X[:, 1] < self.payload_threshold)
        return np.where(is_ddos, -1, 0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        rule_preds = self._rule_based(X)
        if_preds   = self.iso_forest.predict(X)
        return np.where(rule_preds != 0, rule_preds, if_preds)

    def fit(self, X: np.ndarray) -> "SentinelModel":
        self.iso_forest.fit(X)
        return self
