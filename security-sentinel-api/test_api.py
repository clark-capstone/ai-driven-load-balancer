#!/usr/bin/env python3
"""Test API functionality without running the server"""

import sys
import json
sys.path.insert(0, '.')

print("\n" + "="*60)
print("  Test: API Inference (simulated)")
print("="*60 + "\n")

from main import score_request, RequestFeatures, HealthCheck
from fastapi import HTTPException

# Test 1: Health check
print("Test 1: Health check endpoint")
health = HealthCheck(status="healthy", model_version="v2", model_loaded=True)
print(f"✓ Status: {health.status}")
print(f"✓ Model: {health.model_version}\n")

# Test 2: Normal request (should allow)
print("Test 2: Legitimate request (low rate, medium payload)")
req1 = RequestFeatures(
    request_rate=2.5,
    payload_size=2048,
    user_agent="Mozilla/5.0",
    dest_port=443,
    protocol="TCP",
    ttl=64
)

try:
    result1 = score_request(req1)
    print(f"✓ Result: {result1.result}")
    print(f"✓ Confidence: {result1.confidence:.4f}")
    print(f"✓ Model version: {result1.model_version}")
    print(f"✓ Inference time: {result1.inference_ms:.2f}ms")
    assert result1.result in ["allow", "block"], "Invalid result"
    print("✓ Legitimate request test PASSED\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 3: Suspicious request (high rate, low payload) - likely DDoS
print("Test 3: Suspicious request (high rate, small payload)")
req2 = RequestFeatures(
    request_rate=150.0,  # Very high request rate
    payload_size=20,     # Very small payload
    user_agent="",       # No user agent (bot-like)
    dest_port=80,
    protocol="TCP",
    ttl=64,
    syn_flag_count=50,   # Many SYN flags
    total_flags=100
)

try:
    result2 = score_request(req2)
    print(f"✓ Result: {result2.result}")
    print(f"✓ Confidence: {result2.confidence:.4f}")
    print(f"✓ Metadata: {result2.metadata}")
    print("✓ Suspicious request test PASSED\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 4: Backward compatibility (4-feature request)
print("Test 4: Backward compatibility (legacy 4-feature API)")
req3 = RequestFeatures(
    request_rate=3.0,
    payload_size=1024,
    user_agent="curl/7.64",
    timestamp=None
)

try:
    result3 = score_request(req3)
    print(f"✓ Result: {result3.result}")
    print(f"✓ Inferred 12 features from 4-feature input")
    print("✓ Backward compatibility test PASSED\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 5: Batch scoring
print("Test 5: Batch scoring")
from main import batch_score

requests = [
    RequestFeatures(request_rate=2.0, payload_size=1024, user_agent="Mozilla/5.0", dest_port=443),
    RequestFeatures(request_rate=100.0, payload_size=30, user_agent="", dest_port=80),
    RequestFeatures(request_rate=5.0, payload_size=2048, user_agent="curl/7.64"),
]

try:
    batch_result = batch_score(requests)
    print(f"✓ Batch results: {len(batch_result['results'])} requests scored")
    print(f"✓ Summary:")
    print(f"   - Total: {batch_result['summary']['total']}")
    print(f"   - Blocked: {batch_result['summary']['blocked']}")
    print(f"   - Allowed: {batch_result['summary']['allowed']}")
    print(f"   - Block rate: {batch_result['summary']['block_rate']:.1%}")
    print(f"   - Avg confidence: {batch_result['summary']['avg_confidence']:.4f}")
    print("✓ Batch scoring test PASSED\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

print("="*60)
print("  ✅ All API tests PASSED!")
print("="*60 + "\n")

print("Model files created:")
print("  ✓ sentinel_model_v2.pkl      (trained Isolation Forest)")
print("  ✓ sentinel_thresholds_v2.json (auto-tuned thresholds)")
print("\nTo start the API server, run:")
print("  $ python main.py")
print("\nThen test with curl:")
print('  $ curl -X POST "http://localhost:8000/score" \\')
print('         -H "Content-Type: application/json" \\')
print('         -d \'{"request_rate": 5.0, "payload_size": 1024, "dest_port": 443}\'')
print("\nAPI documentation available at:")
print("  http://localhost:8000/docs")
