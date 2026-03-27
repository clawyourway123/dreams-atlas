"""Search latency benchmark — validates p99 < 10ms SLA.

Usage:
    python backend/benchmark_search.py

Expects embeddings_checkpoint.npy in the project root.
Exits with code 1 if FAISS is unavailable or p99 >= 10ms.
"""
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EMBEDDINGS_PATH = PROJECT_ROOT / "embeddings_checkpoint.npy"
K = 20
N_QUERIES = 1000
P99_THRESHOLD_MS = 10.0


def main():
    if not EMBEDDINGS_PATH.exists():
        print(f"ERROR: {EMBEDDINGS_PATH} not found", file=sys.stderr)
        sys.exit(1)

    vectors = np.load(str(EMBEDDINGS_PATH)).astype("float32")
    n, d = vectors.shape
    print(f"Dataset: {n} vectors x {d} dims")

    try:
        import faiss
    except ImportError:
        print("ERROR: faiss-cpu not installed — cannot validate latency SLA", file=sys.stderr)
        sys.exit(1)

    index = faiss.IndexFlatL2(d)
    index.add(vectors)
    print(f"FAISS index built: {index.ntotal} vectors")

    np.random.seed(42)
    query_indices = np.random.randint(0, n, N_QUERIES)

    latencies_ms = []
    for qi in query_indices:
        qv = vectors[qi].reshape(1, -1)
        t0 = time.perf_counter()
        index.search(qv, K)
        latencies_ms.append((time.perf_counter() - t0) * 1000)

    latencies_ms.sort()
    avg = sum(latencies_ms) / len(latencies_ms)
    p50 = latencies_ms[int(N_QUERIES * 0.50)]
    p95 = latencies_ms[int(N_QUERIES * 0.95)]
    p99 = latencies_ms[int(N_QUERIES * 0.99)]

    print(f"\nFAISS IndexFlatL2 — {N_QUERIES} queries, k={K}")
    print(f"  avg={avg:.2f}ms  p50={p50:.2f}ms  p95={p95:.2f}ms  p99={p99:.2f}ms")

    if p99 < P99_THRESHOLD_MS:
        print(f"  PASS: p99 {p99:.2f}ms < {P99_THRESHOLD_MS}ms")
        sys.exit(0)
    else:
        print(f"  FAIL: p99 {p99:.2f}ms >= {P99_THRESHOLD_MS}ms", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
