import sys
import time
import requests

def run_test(url):
    # Simulate a load test / perf test
    # If the URL contains v2, let's pretend it has a performance regression to show the demo failing
    start = time.time()
    
    # In a real app we'd actually hit the URL, but here we just simulate
    # v1 is fast (25ms), v2 is slow (150ms) - SLA is 50ms
    if "v2" in url:
        time.sleep(0.15)
        elapsed_ms = 150
    else:
        time.sleep(0.025)
        elapsed_ms = 25
        
    print(f"Elapsed: {elapsed_ms}ms")
    
    if elapsed_ms > 50:
        print(f"SLA Violated! Expected < 50ms, got {elapsed_ms}ms", file=sys.stderr)
        sys.exit(1)
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    run_test(sys.argv[1])
