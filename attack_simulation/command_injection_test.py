import requests

LOGIN_URL = "http://127.0.0.1:5000/login"
EXPORT_URL = "http://127.0.0.1:5000/employees/export"

session = requests.Session()
session.post(LOGIN_URL, data={"username": "rakes123", "password": "MySecret123!"})

PAYLOADS = [
    "report; rm -rf exports",
    "report && whoami",
    "report | cat /etc/passwd",
    "report`whoami`",
    "report$(whoami)",
    "../../../etc/passwd",          # path traversal attempt, bonus check
    "report && del /F /Q C:\\*",    # Windows-flavored injection attempt
]

print("=== OS Command Injection Test (real endpoint) ===")
for payload in PAYLOADS:
    r = session.post(EXPORT_URL, data={"archive_name": payload})
    blocked = r.status_code == 400
    print(f"Payload: {payload!r}")
    print(f"  Status: {r.status_code} | Blocked: {blocked}")
    print(f"  Response: {r.json()}")
    print()

# Confirm legitimate use still works
print("Legitimate input test:")
r = session.post(EXPORT_URL, data={"archive_name": "legit_export_test"})
print(f"  Status: {r.status_code}, Response: {r.json()}")