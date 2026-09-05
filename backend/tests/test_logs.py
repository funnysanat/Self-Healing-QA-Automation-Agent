import sys

def run_test(log_file_path):
    try:
        with open(log_file_path, 'r') as f:
            logs = f.readlines()
            
        for idx, line in enumerate(logs):
            if "[ERROR]" in line or "[FATAL]" in line:
                error_details = "".join(logs[idx:idx+5]).strip()
                print(f"Log Test Failed: Found error in logs.\n{error_details}", file=sys.stderr)
                sys.exit(1)
                
        print("Log Test Passed: No critical errors found.")
    except Exception as e:
        print(f"Error reading log file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_logs.py <log_file_path>")
        sys.exit(1)
    run_test(sys.argv[1])
