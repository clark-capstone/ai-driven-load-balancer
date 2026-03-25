"""
Request Pre-processor for AI Security Sentinel v2
Converts raw HTTP request objects into 12-dimensional numerical feature vectors.

Enhanced with 8 new features for improved attack detection:
- Network flow characteristics (packet count, byte ratios)
- Protocol anomalies (SYN floods, fragmentation, TTL issues)
- Behavioral patterns (port diversity, header entropy)

Backward compatible: Accepts 4-feature input, auto-pads to 12.
"""

import numpy as np
import time
from datetime import datetime
from typing import Any, Optional

# Common legitimate user agents (partial match list)
COMMON_USER_AGENTS = [
    "mozilla", "chrome", "safari", "firefox", "edge",
    "opera", "curl", "python-requests", "axios", "wget"
]

# Feature indices for clarity
FEAT_REQUEST_RATE = 0
FEAT_PAYLOAD_SIZE = 1
FEAT_PKT_COUNT = 2
FEAT_BYTE_RATIO = 3
FEAT_SYN_FLOOD = 4
FEAT_HEADER_ENTROPY = 5
FEAT_PORT_DIVERSITY = 6
FEAT_TTL_ANOMALY = 7
FEAT_FRAGMENTATION = 8
FEAT_PROTOCOL_ABUSE = 9
FEAT_IS_COMMON_UA = 10
FEAT_TIME_OF_DAY = 11

# Feature count
NUM_FEATURES = 12


def _compute_pkt_count(request: dict[str, Any]) -> float:
    """
    Feature 2: Total packet count in the flow.
    
    Attacks often have distinctive packet patterns:
    - DDoS floods: many small packets
    - Slow attacks: few packets spread over time
    
    Input: 'pkt_count' (packets) or None to infer from payload_size
    Default: Estimate based on payload size (assume ~1500 byte MTU)
    """
    if "pkt_count" in request:
        return float(request.get("pkt_count", 1.0))
    
    payload_size = float(request.get("payload_size", 0))
    if payload_size == 0:
        return 1.0
    
    # Estimate packets assuming ~1500 byte MTU
    return float(max(1.0, payload_size / 1500.0))


def _compute_byte_ratio(request: dict[str, Any]) -> float:
    """
    Feature 3: Ratio of payload bytes to total bytes.
    
    Anomalies:
    - Very low (<0.3): Excessive headers (possible evasion/scanning)
    - Very high (>0.95): Minimal headers (abnormal)
    - Normal: 0.6-0.95 for legitimate traffic
    
    Input: 'payload_size' and 'total_bytes', or inference
    Default: Normal ratio (0.8)
    """
    if "byte_ratio" in request:
        return float(request.get("byte_ratio", 0.8))
    
    payload = float(request.get("payload_size", 0))
    total_bytes = float(request.get("total_bytes", payload + 200))  # Estimate headers ~200B
    
    if total_bytes == 0:
        return 0.8
    
    return np.clip(payload / total_bytes, 0.0, 1.0)


def _compute_syn_flood(request: dict[str, Any]) -> float:
    """
    Feature 4: Ratio of SYN flags in TCP connection setup.
    
    High SYN ratio (>0.5) indicates possible SYN flood attack.
    
    Input: 'syn_flag_count', 'total_flags' or None
    Default: Normal ratio (0.1)
    """
    if "syn_flood_ratio" in request:
        return float(request.get("syn_flood_ratio", 0.1))
    
    syn_flags = float(request.get("syn_flag_count", 0))
    total_flags = float(request.get("total_flags", 1.0))
    
    if total_flags == 0:
        return 0.1
    
    ratio = syn_flags / max(total_flags, 1.0)
    return np.clip(ratio, 0.0, 1.0)


def _compute_header_entropy(request: dict[str, Any]) -> float:
    """
    Feature 5: Approximate packet header entropy/variation.
    
    Metrics:
    - Low entropy: Malformed headers (possible attack)
    - High entropy: Good variation (normal)
    
    Input: 'header_entropy', 'pkt_size_max', 'pkt_size_min' or None
    Default: Normal entropy (normalized value ~0.5)
    """
    if "header_entropy" in request:
        # If provider supplies entropy directly, normalize to [0, 1]
        return np.clip(float(request.get("header_entropy", 0.5)) / 1000.0, 0.0, 1.0)
    
    # Compute from packet size variation (max - min)
    pkt_max = float(request.get("pkt_size_max", 1500.0))
    pkt_min = float(request.get("pkt_size_min", 40.0))
    
    # Normalize: 0=no variation (anomalous), 1=high variation (normal)
    variation = (pkt_max - pkt_min) / 1500.0
    return np.clip(variation, 0.0, 1.0)


def _compute_port_diversity(request: dict[str, Any]) -> float:
    """
    Feature 6: Destination port diversity.
    
    Port scanning & reconnaissance:
    - Low diversity (0.0): Single common port (normal)
    - High diversity (1.0): Many unusual ports (scanning)
    
    Input: 'dest_port' (single port or list) or 'port_diversity'
    Default: Common port (0.0 diversity)
    """
    if "port_diversity" in request:
        return np.clip(float(request.get("port_diversity", 0.0)), 0.0, 1.0)
    
    dest_port = request.get("dest_port", 80)
    
    # Convert to int if possible
    try:
        port = int(dest_port)
    except (ValueError, TypeError):
        return 0.0
    
    # Common legitimate ports: 80, 443, 22, 3389, 25, 53, 21, 25
    common_ports = {80, 443, 22, 3389, 25, 53, 21, 1433, 3306, 5432, 27017}
    
    if port in common_ports:
        return 0.0  # Common port = low diversity
    else:
        return 1.0  # Unusual port = high diversity


def _compute_ttl_anomaly(request: dict[str, Any]) -> float:
    """
    Feature 7: Time-To-Live (TTL) anomaly detection.
    
    Normal TTL values: 64, 128, 255 (OS defaults)
    Anomalies suggest spoofed IPs, proxies, or forwarded packets.
    
    Input: 'ttl' or None
    Default: Normal TTL (0.0 = no anomaly)
    """
    if "ttl_anomaly" in request:
        return np.clip(float(request.get("ttl_anomaly", 0.0)), 0.0, 1.0)
    
    ttl = request.get("ttl", 64)
    
    try:
        ttl = int(ttl)
    except (ValueError, TypeError):
        return 0.0
    
    # Check if TTL is one of normal values
    normal_ttls = {64, 128, 255, 32}  # Also include 32 for some systems
    
    if ttl in normal_ttls:
        return 0.0  # Normal
    else:
        # Anomalous: return scaled distance from nearest normal
        distances = [abs(ttl - n) for n in normal_ttls]
        return np.clip(min(distances) / 128.0, 0.0, 1.0)


def _compute_fragmentation(request: dict[str, Any]) -> float:
    """
    Feature 8: IP fragmentation indicator.
    
    IP fragmentation can indicate evasion techniques or unusual traffic patterns.
    
    Input: 'ip_fragmented' (bool/int) or 'ipv4_ihl' or None
    Default: Not fragmented (0.0)
    """
    if "fragmentation" in request:
        return float(request.get("fragmentation", 0.0))
    
    if "ip_fragmented" in request:
        return 1.0 if request.get("ip_fragmented") else 0.0
    
    # Heuristic: Check IPv4 IHL (Internet Header Length)
    # IHL > 5 indicates IP options, possible fragmentation
    ipv4_ihl = request.get("ipv4_ihl", 5)
    try:
        ihl = int(ipv4_ihl)
        return 1.0 if ihl > 5 else 0.0
    except (ValueError, TypeError):
        return 0.0


def _compute_protocol_abuse(request: dict[str, Any]) -> float:
    """
    Feature 9: Protocol abuse indicator.
    
    Non-standard protocol usage (e.g., HTTPS on port 80, weird TCP flags)
    
    Input: 'protocol', 'dest_port' or 'protocol_abuse'
    Default: Normal (0.0)
    """
    if "protocol_abuse" in request:
        return np.clip(float(request.get("protocol_abuse", 0.0)), 0.0, 1.0)
    
    protocol = request.get("protocol", "TCP").upper()
    dest_port = request.get("dest_port", 80)
    
    try:
        port = int(dest_port)
    except (ValueError, TypeError):
        port = 80
    
    # Check protocol-port mismatch
    # Common mismatches that indicate abuse
    abuse_indicators = {
        ("TCP", 53),    # DNS should be UDP
        ("ICMP", 80),   # HTTPS/web should be TCP
        ("ICMP", 443),
        ("TCP", 161),   # SNMP usually UDP
    }
    
    if (protocol, port) in abuse_indicators:
        return 1.0
    else:
        return 0.0


def _compute_is_common_ua(request: dict[str, Any]) -> float:
    """
    Feature 10: Is common user agent (legitimacy indicator).
    
    1.0 if User-Agent is recognized browser/tool
    0.0 if unknown or missing (possible bot/crawler)
    """
    if "is_common_user_agent" in request:
        return float(request.get("is_common_user_agent", 1.0))
    
    ua = str(request.get("user_agent", "")).lower()
    
    if any(agent in ua for agent in COMMON_USER_AGENTS):
        return 1.0
    else:
        return 0.0


def _compute_time_of_day(request: dict[str, Any]) -> float:
    """
    Feature 11: Time of day (0-23 hour).
    
    Some attacks are more common at certain hours.
    """
    if "time_of_day" in request:
        return float(request.get("time_of_day", 12.0))
    
    ts = request.get("timestamp", None)
    if ts is not None:
        try:
            hour = datetime.fromtimestamp(float(ts)).hour
        except (ValueError, OSError):
            hour = datetime.now().hour
    else:
        hour = datetime.now().hour
    
    return float(hour)


def extract_features(request: dict[str, Any], expected_features: Optional[int] = None) -> np.ndarray:
    """
    Convert a raw HTTP request JSON object into a 12-dimensional feature vector.

    **Input Fields** (all optional with safe defaults):
        Standard (legacy 4-feature API):
        - timestamp       (float)  : Unix timestamp of the request
        - payload_size    (int)    : Content-Length or body size in bytes
        - user_agent      (str)    : User-Agent header string
        - request_rate    (float)  : Requests/second from this IP
        
        Enhanced (new 8 features):
        - pkt_count       (int)    : Total packets in connection
        - total_bytes     (int)    : Total bytes including headers
        - syn_flag_count  (int)    : Number of SYN flags
        - total_flags     (int)    : Total TCP flags
        - header_entropy  (float)  : Header variation metric
        - pkt_size_max    (int)    : Max packet size
        - pkt_size_min    (int)    : Min packet size
        - dest_port       (int)    : Destination port number
        - ttl             (int)    : Time-to-live value
        - ip_fragmented   (bool)   : IP fragmentation present
        - ipv4_ihl        (int)    : IPv4 Internet Header Length
        - protocol        (str)    : Protocol (TCP/UDP/ICMP)
        - port_diversity  (float)  : [0,1] unique port ratio
        - syn_flood_ratio (float)  : [0,1] SYN flag ratio
        - ttl_anomaly     (float)  : [0,1] TTL anomaly score

    **Returns**:
        np.ndarray of shape (12,) with dtype float32:
            Features are normalized to approximate [0, 1] range to match training data.
            [request_rate, payload_size, pkt_count, byte_ratio,
             syn_flood, header_entropy, port_diversity, ttl_anomaly,
             fragmentation, protocol_abuse, is_common_ua, time_of_day]

    **Latency SLA**: <10ms for feature extraction

    **Example**:
        >>> request = {
        ...     "request_rate": 5.0,
        ...     "payload_size": 512,
        ...     "user_agent": "Mozilla/5.0",
        ...     "dest_port": 443,
        ...     "protocol": "TCP"
        ... }
        >>> features = extract_features(request)
        >>> features.shape
        (12,)
    """
    start = time.perf_counter()

    features = np.zeros(NUM_FEATURES, dtype=np.float32)

    # 0. request_rate — requests per second from this IP, normalized to [0, 1]
    # Typical range: 0-1000 req/s, scale to 0-1 by dividing by 1000
    request_rate_raw = float(request.get("request_rate", 1.0))
    features[FEAT_REQUEST_RATE] = np.clip(request_rate_raw / 1000.0, 0.0, 1.0)

    # 1. payload_size — body/content size in bytes, normalized to [0, 1]
    # Typical range: 0-10000 bytes, scale to 0-1 by dividing by 10000
    payload_size_raw = float(request.get("payload_size", 0.0))
    features[FEAT_PAYLOAD_SIZE] = np.clip(payload_size_raw / 10000.0, 0.0, 1.0)

    # 2. pkt_count — total packet count, normalized to [0, 1]
    # Typical range: 1-100 packets, scale to 0-1
    pkt_count_raw = _compute_pkt_count(request)
    features[FEAT_PKT_COUNT] = np.clip(pkt_count_raw / 100.0, 0.0, 1.0)

    # 3. byte_ratio — payload-to-total-bytes ratio (already in 0-1 range)
    features[FEAT_BYTE_RATIO] = _compute_byte_ratio(request)

    # 4. syn_flood — SYN flag ratio (already in 0-1 range)
    features[FEAT_SYN_FLOOD] = _compute_syn_flood(request)

    # 5. header_entropy — packet header variation, normalized to [0, 1]
    # Typical range: 0-1500 bytes variation
    header_entropy_raw = _compute_header_entropy(request)
    features[FEAT_HEADER_ENTROPY] = np.clip(header_entropy_raw / 1500.0, 0.0, 1.0)

    # 6. port_diversity — destination port diversity (already in 0-1 range)
    features[FEAT_PORT_DIVERSITY] = _compute_port_diversity(request)

    # 7. ttl_anomaly — TTL anomaly detection (already in 0-1 range)
    features[FEAT_TTL_ANOMALY] = _compute_ttl_anomaly(request)

    # 8. fragmentation — IP fragmentation indicator (already in 0-1 range)
    features[FEAT_FRAGMENTATION] = _compute_fragmentation(request)

    # 9. protocol_abuse — protocol misuse indicator (already in 0-1 range)
    features[FEAT_PROTOCOL_ABUSE] = _compute_protocol_abuse(request)

    # 10. is_common_user_agent — legitimate UA indicator (already in 0-1 range)
    features[FEAT_IS_COMMON_UA] = _compute_is_common_ua(request)

    # 11. time_of_day — hour of day (0-23), normalize to [0, 1]
    time_of_day_raw = _compute_time_of_day(request)
    features[FEAT_TIME_OF_DAY] = np.clip(time_of_day_raw / 24.0, 0.0, 1.0)

    # Verify SLA
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 10, f"Pre-processor exceeded 10ms SLA: {elapsed_ms:.2f}ms"

    return features


def batch_extract(requests: list[dict[str, Any]]) -> np.ndarray:
    """
    Vectorise a list of request dicts into a 2-D feature matrix (N x 12).
    
    Args:
        requests: List of request dictionaries
        
    Returns:
        np.ndarray of shape (N, 12) with normalized features
    """
    return np.stack([extract_features(r) for r in requests])
