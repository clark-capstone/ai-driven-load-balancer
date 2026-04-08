"""
FastAPI Inference Server for AI Security Sentinel v2

Endpoint: POST /score
- Accepts: HTTP request features (JSON dict)
- Returns: {"result": "block" | "allow", "confidence": 0.0-1.0}

Features:
- FastAPI auto-documentation at /docs (Swagger)
- Health check at /health
- Backward compatible with 4-feature API
- Auto-pads 4-feature requests to 12-feature format
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import time

from preprocessor import extract_features
from train_sentinel import load_model

# Initialize FastAPI app
app = FastAPI(
    title="AI Security Sentinel API v2",
    description="Real-time threat detection for load balancers",
    version="2.0.0"
)

# Load model (v2 with 12 features)
try:
    model, thresholds = load_model("sentinel_model_v2.pkl", "sentinel_thresholds_v2.json")
    MODEL_VERSION = "v2"
except (FileNotFoundError, Exception) as e:
    # Fallback to v1 if v2 not available
    print(f"⚠️  v2 model not found: {e}")
    print("   Attempting to load v1 model (4 features)...")
    try:
        from train_sentinel import load_model as load_model_v1
        model = load_model_v1("sentinel_model.pkl")
        thresholds = {
            "ddos_rate_threshold": 60.0,
            "ddos_payload_threshold": 150.0
        }
        MODEL_VERSION = "v1"
        print("✓ Loaded v1 model (fallback mode)\n")
    except Exception as e2:
        print(f"❌ Failed to load any model: {e2}")
        raise


def is_degenerate_model(model) -> bool:
    estimators = getattr(model.iso_forest, "estimators_", [])
    if not estimators:
        return True

    return all(est.tree_.node_count <= 1 for est in estimators)


def compute_threat_confidence(features: np.ndarray, prediction: int, rule_triggered: bool) -> float:
    request_rate = float(features[0])
    payload_size = float(features[1])
    syn_flood = float(features[4])
    port_diversity = float(features[6])
    ttl_anomaly = float(features[7])
    fragmentation = float(features[8])
    protocol_abuse = float(features[9])
    common_user_agent = float(features[10])

    payload_risk = 1.0 - min(payload_size * 2.0, 1.0)
    user_agent_risk = 1.0 - common_user_agent

    weighted_risk = (
        request_rate * 0.30
        + payload_risk * 0.18
        + syn_flood * 0.14
        + port_diversity * 0.12
        + ttl_anomaly * 0.08
        + fragmentation * 0.08
        + protocol_abuse * 0.06
        + user_agent_risk * 0.04
    )
    weighted_risk = float(np.clip(weighted_risk, 0.0, 1.0))

    if rule_triggered:
        return float(max(0.93, weighted_risk))

    if prediction == -1:
        return float(max(0.72, weighted_risk))

    return float(min(weighted_risk, 0.68))


def should_block_request(request: "RequestFeatures", features: np.ndarray, thresholds: dict) -> tuple[bool, str | None]:
    request_rate_feature = float(features[0])
    payload_feature = float(features[1])
    raw_request_rate = float(request.request_rate)
    raw_payload_size = int(request.payload_size)

    ddos_rule = (
        request_rate_feature > thresholds["ddos_rate_threshold"]
        and payload_feature < thresholds["ddos_payload_threshold"]
    )
    if ddos_rule:
        return True, "DDoS_rate_volume_check"

    # Repeated-hit demo rule for real browser/curl bursts against the same local service.
    burst_rule = raw_request_rate >= 20.0 and raw_payload_size <= 256
    if burst_rule:
        return True, "burst_rate_small_payload"

    return False, None


class RequestFeatures(BaseModel):
    """
    HTTP request features for threat detection (12-dimensional).
    
    All fields optional with safe defaults.
    """
    # Original 4 features (always available)
    request_rate: float = Field(default=1.0, description="Requests per second from source IP")
    payload_size: int = Field(default=0, description="Request body size in bytes")
    user_agent: str = Field(default="", description="User-Agent header")
    timestamp: Optional[float] = Field(default=None, description="Unix timestamp of request")
    
    # Enhanced 8 features (optional for backward compatibility)
    pkt_count: Optional[int] = Field(default=None, description="Total packets in flow")
    total_bytes: Optional[int] = Field(default=None, description="Total bytes (headers + payload)")
    syn_flag_count: Optional[int] = Field(default=None, description="Number of SYN flags")
    total_flags: Optional[int] = Field(default=None, description="Total TCP flags")
    header_entropy: Optional[float] = Field(default=None, description="Header entropy score")
    pkt_size_max: Optional[int] = Field(default=None, description="Max packet size")
    pkt_size_min: Optional[int] = Field(default=None, description="Min packet size")
    dest_port: int = Field(default=80, description="Destination port number")
    ttl: int = Field(default=64, description="Time-to-live value")
    ip_fragmented: bool = Field(default=False, description="IP fragmentation present")
    ipv4_ihl: int = Field(default=5, description="IPv4 Internet Header Length")
    protocol: str = Field(default="TCP", description="Protocol (TCP/UDP/ICMP)")
    
    class Config:
        example = {
            "request_rate": 5.2,
            "payload_size": 1024,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "timestamp": 1711270000.0,
            "dest_port": 443,
            "protocol": "TCP",
            "ttl": 64
        }


class ThreatScore(BaseModel):
    """Response format for threat detection."""
    result: str = Field(..., description="'allow' or 'block'")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    model_version: str = Field(..., description="Model version used")
    inference_ms: float = Field(..., description="Inference latency in milliseconds")
    metadata: dict = Field(default_factory=dict, description="Additional info (rule triggered, etc.)")


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    model_version: str
    model_loaded: bool


@app.get("/health", response_model=HealthCheck, tags=["System"])
def health_check():
    """
    Health check endpoint.
    
    Returns model status and version information.
    """
    return {
        "status": "healthy",
        "model_version": MODEL_VERSION,
        "model_loaded": model is not None
    }


@app.post("/score", response_model=ThreatScore, tags=["Inference"])
def score_request(request: RequestFeatures) -> ThreatScore:
    """
    Score a network request for threat level.
    
    Accepts HTTP request metadata and returns a classification:
    - **allow** (1): Legitimate traffic
    - **block** (-1): Detected anomaly/threat
    
    Features are extracted from the request JSON and processed through
    the hybrid anomaly detection model (hard rules + Isolation Forest).
    
    Example request:
    ```json
    {
      "request_rate": 5.2,
      "payload_size": 1024,
      "user_agent": "Mozilla/5.0",
      "dest_port": 443
    }
    ```
    
    Example response:
    ```json
    {
      "result": "allow",
      "confidence": 0.95,
      "model_version": "v2",
      "inference_ms": 2.3,
      "metadata": {}
    }
    ```
    """
    start_time = time.perf_counter()
    
    try:
        # Convert request to dict for feature extraction (exclude None values)
        request_dict = {k: v for k, v in request.dict().items() if v is not None}
        
        # Extract 12 features from request
        features = extract_features(request_dict)
        
        if features.shape[0] != 12:
            raise ValueError(f"Expected 12 features, got {features.shape[0]}")
        
        # Add batch dimension for model
        features_batch = np.array([features], dtype=np.float32)
        
        # Make prediction
        prediction = model.predict(features_batch)[0]
        
        rule_triggered, rule_name = should_block_request(request, features, thresholds)

        # Determine result
        result = "block" if prediction == -1 or rule_triggered else "allow"

        # Metadata
        metadata = {
            "prediction_score": float(prediction),
        }

        if is_degenerate_model(model):
            confidence = compute_threat_confidence(features, prediction, rule_triggered)
            metadata["anomaly_score"] = None
            metadata["confidence_source"] = "feature_heuristic"
            metadata["model_warning"] = "Isolation Forest scores are constant; using heuristic confidence"
        else:
            decision_score = model.iso_forest.score_samples(features_batch)[0]
            confidence = 1.0 / (1.0 + np.exp(decision_score))  # Sigmoid normalization
            confidence = float(np.clip(confidence, 0.0, 1.0))
            metadata["anomaly_score"] = float(decision_score)
            metadata["confidence_source"] = "isolation_forest"

        if rule_name is not None:
            metadata["rule_triggered"] = rule_name
        
        inference_time = (time.perf_counter() - start_time) * 1000  # milliseconds
        
        return ThreatScore(
            result=result,
            confidence=confidence,
            model_version=MODEL_VERSION,
            inference_ms=inference_time,
            metadata=metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")


@app.post("/batch_score", tags=["Inference"])
def batch_score(requests: list[RequestFeatures]) -> dict:
    """
    Score multiple requests in a single batch.
    
    Useful for bulk threat assessment.
    
    Returns:
    - List of classifications
    - Summary statistics
    """
    start_time = time.perf_counter()
    
    try:
        results = []
        for req in requests:
            result = score_request(req)
            results.append(result.dict())
        
        inference_time = (time.perf_counter() - start_time) * 1000
        
        block_count = sum(1 for r in results if r["result"] == "block")
        allow_count = sum(1 for r in results if r["result"] == "allow")
        avg_confidence = np.mean([r["confidence"] for r in results])
        
        return {
            "results": results,
            "summary": {
                "total": len(results),
                "blocked": block_count,
                "allowed": allow_count,
                "block_rate": block_count / len(results) if results else 0,
                "avg_confidence": float(avg_confidence),
                "batch_inference_ms": inference_time
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing batch: {str(e)}")


@app.get("/", tags=["Documentation"])
def root():
    """
    Welcome endpoint with API documentation.
    
    Visit /docs for interactive Swagger UI.
    Visit /redoc for ReDoc documentation.
    """
    return {
        "name": "AI Security Sentinel API v2",
        "version": "2.0.0",
        "model_version": MODEL_VERSION,
        "endpoints": {
            "health": "GET /health",
            "score": "POST /score",
            "batch_score": "POST /batch_score",
            "docs": "GET /docs",
            "redoc": "GET /redoc"
        },
        "description": "Real-time threat detection for load balancers using ML-based anomaly detection"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("  🔐 AI Security Sentinel API v2")
    print("  Model: " + MODEL_VERSION)
    print("="*60 + "\n")
    print("Starting server on http://localhost:8000")
    print("API Docs: http://localhost:8000/docs\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
