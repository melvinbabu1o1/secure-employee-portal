import requests
import time

TARGET = "http://127.0.0.1:5000/login"
USERNAME = "rakes123"  # use an account that actually exists

print("=== Brute Force Test ===")
for i in range(1, 8):
    r = requests.post(TARGET, data={"username": USERNAME, "password": f"wrongpass{i}"})
    data = r.json()
    print(f"Attempt {i}: status={r.status_code}, response={data}")

    if "locked" in str(data).lower():
        print("\n✅ Account lockout triggered as expected.")
        break

    time.sleep(0.3)