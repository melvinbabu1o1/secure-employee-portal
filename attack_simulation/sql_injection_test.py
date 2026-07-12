import requests

TARGET = "http://127.0.0.1:5000/login"

PAYLOADS = [
    "' OR '1'='1",
    "admin'--",
    "' UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL--",
    "'; DROP TABLE users;--",
]

print("=== SQL Injection Test ===")
for payload in PAYLOADS:
    r = requests.post(TARGET, data={"username": payload, "password": "irrelevant"})
    blocked = r.status_code in (400, 401, 403)
    print(f"Payload: {payload!r}")
    print(f"  Status: {r.status_code} | Blocked: {blocked}")
    print(f"  Response: {r.json()}")
    print()