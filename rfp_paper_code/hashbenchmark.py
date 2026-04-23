import hashlib
import time

def benchmark_hash(hash_func, data, iterations=100000):
    start = time.time()
    for _ in range(iterations):
        h = hash_func()
        h.update(data)
        h.digest()
    end = time.time()
    return end - start

def main():
    data = b"benchmark test data" * 1000
    iterations = 100000

    hash_functions = {
        'md5': lambda: hashlib.md5(),
        'sha1': lambda: hashlib.sha1(),
        'sha256': lambda: hashlib.sha256(),
        'blake2b': lambda: hashlib.blake2b(),
        'blake2s': lambda: hashlib.blake2s(),
    }

    print(f"Benchmarking with {iterations} iterations on {len(data)} bytes of data:")
    for name, func in hash_functions.items():
        elapsed = benchmark_hash(func, data, iterations)
        print(f"{name:8}: {elapsed:.4f} seconds")

if __name__ == "__main__":
    main()