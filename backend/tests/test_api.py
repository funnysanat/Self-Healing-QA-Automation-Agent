import json
import sys

def run_test(api_file_path):
    with open(api_file_path, 'r') as f:
        data = json.load(f)
        
    assert "status" in data, "API should return a status field"
    assert "transaction_id" in data, "API should return a transaction_id for the checkout"
    assert "message" in data, "API should return a message field"
    print("API test passed successfully!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <api_file_path>")
        sys.exit(1)
    run_test(sys.argv[1])