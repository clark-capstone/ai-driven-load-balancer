"""
Data Loader for CICIDS2018 Network Intrusion Detection Dataset

This module handles:
1. Downloading CICIDS2018 from public source
2. Loading and preprocessing the dataset
3. Mapping CICIDS2018 raw features → 12-feature normalized space
4. Splitting into train/val/test with stratification
5. Handling missing values and outliers

CICIDS2018 Source: https://www.unb.ca/cic/datasets/ids-2018.html
Download: ~9.6 GB (contains CSV for different attack scenarios)

Example Usage:
    X_train, y_train, X_test, y_test = load_cicids2018()
    model.fit(X_train, y_train)
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Tuple


# CICIDS2018 CSV columns that map to our 12 features
# (These are actual column names from the dataset)
FEATURE_MAPPING = {
    "request_rate": ["Fwd Packets/s", "Bwd Packets/s"],  # Will combine
    "payload_size": ["Fwd Header Length", "Fwd Payload Length"],
    "pkt_count": ["Total Fwd Packets", "Total Backward Packets"],
    "byte_ratio": ["Fwd Header Length", "Fwd Payload Length", "Bwd Header Length", "Bwd Payload Length"],
    "is_syn_flood": ["FIN Flag Count", "SYN Flag Count", "RST Flag Count"],
    "header_entropy": ["Fwd Header Length"],  # Proxy feature
    "port_diversity": ["Destination Port"],  # Will compute unique ports
    "ttl_anomaly": [],  # Not directly in CICIDS2018, will use heuristic
    "fragmentation": ["Fwd Packet Length Max", "Fwd Packet Length Min"],
    "protocol_abuse": ["Protocol"],  # TCP/UDP/ICMP
    "is_common_user_agent": [None],  # Not available in network flow data (set to safe default)
    "time_of_day": [],  # Will extract from timestamp if available
}


def download_cicids2018():
    """
    Download CICIDS2018 dataset from public archives.
    
    Note: This is a large dataset (9.6 GB). For development, you can:
    1. Download manually from: https://www.unb.ca/cic/datasets/ids-2018.html
    2. Extract to: ./data/cicids2018/
    3. Place CSV files in that directory
    
    Returns:
        str: Path to downloaded/extracted data directory
    """
    data_dir = "data/cicids2018"
    
    if os.path.exists(data_dir) and len(os.listdir(data_dir)) > 0:
        print(f"✓ CICIDS2018 data found at {data_dir}")
        return data_dir
    
    print(f"⚠️  CICIDS2018 data not found at {data_dir}")
    print("\nTo continue, download CICIDS2018 manually:")
    print("1. Visit: https://www.unb.ca/cic/datasets/ids-2018.html")
    print("2. Download the CSV files (Friday-WorkingHours.pcap_ISCX.csv recommended for testing)")
    print("3. Extract to: ./data/cicids2018/")
    print("\nAlternatively, place individual CSV files in the data directory:")
    print("   python data_loader.py --prepare-sample")
    
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def load_cicids2018_csv(file_path: str) -> pd.DataFrame:
    """
    Load a single CICIDS2018 CSV file.
    
    Args:
        file_path: Path to CICIDS2018 CSV file
        
    Returns:
        pandas.DataFrame with loaded data
    """
    print(f"Loading {os.path.basename(file_path)}...")
    
    # Load with error handling for common issues
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None
    
    # CICIDS2018 has various column name formats; normalize them
    df.columns = df.columns.str.strip()
    
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)[:10]}...")  # Show first 10
    
    return df


def is_attack(label: str) -> int:
    """
    Convert CICIDS2018 label to binary: normal (1) or attack (-1).
    
    CICIDS2018 labels:
    - 'BENIGN': Legitimate traffic
    - 'DDoS attacks-LOIC-HTTP': DDoS attack
    - 'DDoS attacks-LOIC-UDP': DDoS attack
    - 'Bot': Botnet traffic
    - 'Brute Force -Web': Web brute-force
    - 'Infiltration': Data exfiltration
    - And many more attack types
    
    Args:
        label: Label string from CICIDS2018
        
    Returns:
        int: 1 for benign, -1 for attack
    """
    if isinstance(label, str):
        label = label.strip().upper()
    
    if label == "BENIGN":
        return 1
    else:
        return -1  # All non-benign are attacks for our binary model


def extract_12_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert CICIDS2018 dataframe to our 12-feature space.
    
    Features (12):
    1. request_rate: Packets per second (forward + backward)
    2. payload_size: Average payload bytes per packet
    3. pkt_count: Total packet count in flow
    4. byte_ratio: Payload-to-total-bytes ratio (indicates padding attacks)
    5. is_syn_flood: Ratio of SYN flags (TCP connection flood indicator)
    6. header_entropy: Approximate entropy of packet headers
    7. port_diversity: Number of unique destination ports accessed
    8. ttl_anomaly: Time-to-live anomaly (spoofed/forwarded packets)
    9. fragmentation: IP fragmentation presence (evasion technique)
    10. protocol_abuse: Non-standard protocol usage (1.0 if anomalous)
    11. is_common_user_agent: Safe default (1.0 for network flows - no UA in network data)
    12. time_of_day: Hour of day (0-23)
    
    Args:
        df: CICIDS2018 dataframe
        
    Returns:
        Tuple of (X: (N, 12) feature array, y: (N,) labels)
    """
    N = len(df)
    X = np.zeros((N, 12), dtype=np.float32)
    
    # Helper function to safe-get column
    def get_or_zero(col_name, default=0.0):
        """Safely retrieve column, return default if missing."""
        if col_name in df.columns:
            return df[col_name].fillna(default).values
        else:
            return np.full(N, default, dtype=float)
    
    # 1. request_rate: Fwd + Bwd packets per second
    fwd_rate = get_or_zero(" Fwd Packets/s", 0.0)
    bwd_rate = get_or_zero(" Bwd Packets/s", 0.0)
    X[:, 0] = fwd_rate + bwd_rate
    
    # 2. payload_size: Average payload size
    fwd_payload = get_or_zero(" Fwd Payload Length", 0.0)
    bwd_payload = get_or_zero(" Bwd Payload Length", 0.0)
    total_payload = fwd_payload + bwd_payload
    pkt_count_col = get_or_zero(" Total Fwd Packets", 1.0)
    X[:, 1] = np.divide(total_payload, pkt_count_col, where=(pkt_count_col > 0), out=np.zeros_like(total_payload))
    
    # 3. pkt_count: Total packets (fwd + bwd)
    total_bwd_packets = get_or_zero(" Total Backward Packets", 0.0)
    X[:, 2] = pkt_count_col + total_bwd_packets
    
    # 4. byte_ratio: Payload bytes / Total bytes (indicates padding)
    total_bytes = total_payload + get_or_zero(" Total Header Length", 1.0)
    X[:, 3] = np.divide(total_payload, total_bytes, where=(total_bytes > 0), out=np.zeros_like(total_payload))
    
    # 5. is_syn_flood: High ratio of SYN flags (connection flood)
    syn_flags = get_or_zero(" SYN Flag Count", 0.0)
    fin_flags = get_or_zero(" FIN Flag Count", 0.0)
    rst_flags = get_or_zero(" RST Flag Count", 0.0)
    total_flags = np.maximum(syn_flags + fin_flags + rst_flags, 1)
    X[:, 4] = np.divide(syn_flags, total_flags, where=(total_flags > 0), out=np.zeros_like(syn_flags))
    
    # 6. header_entropy: Proxy = avg packet size variation (max - min)
    pkt_len_max = get_or_zero(" Fwd Packet Length Max", 0.0)
    pkt_len_min = get_or_zero(" Fwd Packet Length Min", 0.0)
    X[:, 6] = pkt_len_max - pkt_len_min  # Will normalize later
    
    # 7. port_diversity: Destination port variation (0.0 if same port, 1.0 if diverse)
    # CICIDS2018 has fixed ports per flow, so we use destination port as proxy
    # High variation = likely port scanning
    dest_port = get_or_zero(" Destination Port", 80.0)
    # Normalize to 0-1: common ports (80, 443, 22) = low diversity, rare = high
    X[:, 7] = np.where(np.isin(dest_port, [80, 443, 22, 3389, 25, 53]), 0.0, 1.0)
    
    # 8. ttl_anomaly: TTL anomaly detection
    if " TTL" in df.columns:
        ttl = df[" TTL"].fillna(64).values
        # Normal TTL: 64, 128, 255. Anomaly if far from these
        X[:, 8] = np.where(np.isin(ttl, [64, 128, 255]), 0.0, 1.0)
    else:
        X[:, 8] = 0.0  # Default: assume normal
    
    # 9. fragmentation: IP fragmentation presence
    if " IPv4 IHL" in df.columns:
        ihl = df[" IPv4 IHL"].fillna(5).values
        X[:, 9] = np.where(ihl > 5, 1.0, 0.0)  # IHL > 5 indicates IP options (possible fragmentation)
    else:
        X[:, 9] = 0.0
    
    # 10. protocol_abuse: Non-standard protocol usage
    if " Protocol" in df.columns:
        protocol = df[" Protocol"].fillna(6).values  # Default to TCP (6)
        # TCP=6, UDP=17, ICMP=1: normal. Others are anomalous
        X[:, 10] = np.where(np.isin(protocol, [6, 17, 1]), 0.0, 1.0)
    else:
        X[:, 10] = 0.0
    
    # 11. is_common_user_agent: Safe default (1.0 = assume legitimate for network flows)
    # Network flow data doesn't have HTTP headers, so default to legitimate
    X[:, 11] = 1.0
    
    # Extract labels
    label_col = " Label" if " Label" in df.columns else "Label"
    y = np.array([is_attack(label) for label in df[label_col].values], dtype=int)
    
    return X, y


def normalize_features(X: np.ndarray, scaler=None, fit=False) -> Tuple[np.ndarray, object]:
    """
    Normalize features to 0-1 range using StandardScaler.
    
    Args:
        X: Feature matrix (N, 12)
        scaler: Pre-fitted StandardScaler (for test set). If None, fit new one.
        fit: If True, fit scaler on X and return it
        
    Returns:
        Tuple of (normalized_X, scaler_object)
    """
    if scaler is None:
        scaler = StandardScaler()
        scaler.fit(X)
    
    X_normalized = scaler.transform(X)
    # Clip to [-3, 3] to handle outliers, then scale to [0, 1]
    X_normalized = np.clip(X_normalized, -3, 3)
    X_normalized = (X_normalized + 3) / 6
    
    return X_normalized, scaler


def load_cicids2018(test_size=0.25, val_size=0.20, random_state=42, 
                    limit_samples=None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load CICIDS2018, preprocess, and split into train/val/test.
    
    This is the main entry point for loading CICIDS2018 data.
    
    Args:
        test_size: Fraction of data for test set (from overall data)
        val_size: Fraction of training data reserved for validation
        random_state: Random seed for reproducibility
        limit_samples: Max samples to load (for testing). If None, load all.
        
    Returns:
        Tuple of (X_train, y_train, X_test, y_test)
        Each X is shape (N, 12) with normalized features in [0, 1]
        Each y is shape (N,) with values {1 (benign), -1 (attack)}
    """
    print("=" * 60)
    print("  CICIDS2018 Data Loader")
    print("=" * 60 + "\n")
    
    data_dir = download_cicids2018()
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    
    if not csv_files:
        print("\n❌ No CSV files found in", data_dir)
        print("\nTo use this data loader:")
        print("1. Download CICIDS2018 from: https://www.unb.ca/cic/datasets/ids-2018.html")
        print("2. Extract CSV files to:", data_dir)
        print("\nFor now, using synthetic data fallback...")
        return None, None, None, None
    
    print(f"Found {len(csv_files)} CSV file(s):\n")
    
    # Load all CSV files
    dfs = []
    for csv_file in sorted(csv_files)[:1]:  # Start with first file for testing
        file_path = os.path.join(data_dir, csv_file)
        df = load_cicids2018_csv(file_path)
        if df is not None:
            dfs.append(df)
    
    if not dfs:
        print("❌ Failed to load any data")
        return None, None, None, None
    
    # Concatenate all loaded files
    df = pd.concat(dfs, ignore_index=True)
    
    if limit_samples and len(df) > limit_samples:
        df = df.sample(n=limit_samples, random_state=random_state)
    
    print(f"\n📊 Total samples: {len(df)}")
    
    # Extract features and labels
    print("🔧 Extracting 12 features...")
    X, y = extract_12_features(df)
    
    # Count labels
    n_attacks = (y == -1).sum()
    n_benign = (y == 1).sum()
    print(f"   Benign: {n_benign:,}  |  Attacks: {n_attacks:,}")
    print(f"   Attack ratio: {n_attacks/len(y):.1%}\n")
    
    # Normalize features to 0-1 range using StandardScaler
    print("📏 Normalizing features to [0, 1]...")
    X, scaler = normalize_features(X, fit=True)
    
    # Split into train/test
    print("✂️  Splitting train/test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # Further split train into train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=val_size/(1-test_size), 
        random_state=random_state, stratify=y_train
    )
    
    print(f"   Train: {len(X_train):,}  |  Val: {len(X_val):,}  |  Test: {len(X_test):,}\n")
    
    print("✓ CICIDS2018 loaded successfully!")
    print(f"  Features: (12,) shape")
    print(f"  Classes: 1 (benign), -1 (attack)")
    print("=" * 60 + "\n")
    
    return X_train, y_train, X_test, y_test


def load_fallback_data(n_samples=5000, random_state=42):
    """
    Fallback synthetic data generator if CICIDS2018 not available.
    Used for model training when real data isn't downloadable yet.
    
    Args:
        n_samples: Total samples to generate
        random_state: Random seed
        
    Returns:
        Tuple of (X_train, y_train, X_test, y_test) with 12 features
    """
    print("⚠️  Using fallback synthetic data (CICIDS2018 not available)")
    print("    For production, download and use real CICIDS2018 data\n")
    
    rng = np.random.default_rng(random_state)
    
    # Generate normal traffic (1000 samples)
    normal = np.column_stack([
        rng.uniform(1, 10, 1000),           # request_rate
        rng.uniform(500, 8000, 1000),       # payload_size
        rng.uniform(5, 50, 1000),           # pkt_count
        rng.uniform(0.6, 0.95, 1000),       # byte_ratio
        rng.uniform(0.01, 0.1, 1000),       # is_syn_flood
        rng.uniform(10, 500, 1000),         # header_entropy
        rng.uniform(0.0, 0.2, 1000),        # port_diversity
        rng.uniform(0.0, 0.1, 1000),        # ttl_anomaly
        rng.uniform(0.0, 0.05, 1000),       # fragmentation
        rng.uniform(0.0, 0.02, 1000),       # protocol_abuse
        np.ones(1000),                      # is_common_user_agent
        rng.uniform(8, 22, 1000),           # time_of_day
    ])
    
    # Generate DDoS traffic (500 samples)
    ddos = np.column_stack([
        rng.uniform(100, 500, 500),         # request_rate (very high)
        rng.uniform(5, 80, 500),            # payload_size (small)
        rng.uniform(20, 200, 500),          # pkt_count
        rng.uniform(0.05, 0.2, 500),        # byte_ratio (low padding)
        rng.uniform(0.5, 1.0, 500),         # is_syn_flood (many SYNs)
        rng.uniform(1, 100, 500),           # header_entropy
        rng.uniform(0.0, 0.3, 500),         # port_diversity
        rng.uniform(0.0, 0.15, 500),        # ttl_anomaly
        rng.uniform(0.0, 0.1, 500),         # fragmentation
        rng.uniform(0.0, 0.05, 500),        # protocol_abuse
        rng.uniform(0.0, 0.2, 500),         # is_common_user_agent (low for bots)
        rng.uniform(0, 24, 500),            # time_of_day
    ])
    
    # Generate bot traffic (200 samples)
    bot = np.column_stack([
        rng.uniform(15, 40, 200),           # request_rate (moderate-high)
        rng.uniform(300, 2000, 200),        # payload_size (varied)
        rng.uniform(10, 100, 200),          # pkt_count
        rng.uniform(0.4, 0.7, 200),         # byte_ratio
        rng.uniform(0.1, 0.3, 200),         # is_syn_flood
        rng.uniform(5, 300, 200),           # header_entropy
        rng.uniform(0.2, 0.8, 200),         # port_diversity (curious)
        rng.uniform(0.1, 0.4, 200),         # ttl_anomaly
        rng.uniform(0.1, 0.3, 200),         # fragmentation
        rng.uniform(0.1, 0.4, 200),         # protocol_abuse
        rng.uniform(0.0, 0.5, 200),         # is_common_user_agent (mixed)
        rng.uniform(0, 6, 200),             # time_of_day (mostly night)
    ])
    
    X = np.vstack([normal, ddos, bot])
    y = np.concatenate([np.ones(len(normal)), -np.ones(len(ddos)), -np.ones(len(bot))])
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=y
    )
    
    print(f"Dataset: {len(X)} samples  |  Normal: {(y==1).sum()}  |  Anomalous: {(y==-1).sum()}\n")
    
    return X_train, y_train, X_test, y_test


if __name__ == "__main__":
    # Example usage
    X_train, y_train, X_test, y_test = load_cicids2018(limit_samples=10000)
    
    if X_train is None:
        print("Falling back to synthetic data...")
        X_train, y_train, X_test, y_test = load_fallback_data()
    
    print(f"X_train shape: {X_train.shape}")
    print(f"y_train shape: {y_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"y_test shape: {y_test.shape}")
