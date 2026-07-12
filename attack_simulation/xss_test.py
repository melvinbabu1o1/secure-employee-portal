import requests

LOGIN_URL = "http://127.0.0.1:5000/login"
EMPLOYEE_URL = "http://127.0.0.1:5000/employee"
LIST_URL = "http://127.0.0.1:5000/employees"

session = requests.Session()

print("=== XSS Test ===")

# Log in first
login_response = session.post(LOGIN_URL, data={"username": "rakes123", "password": "MySecret123!"})
print("Login response:", login_response.status_code, login_response.json())

# Attempt to inject a script tag as a full_name
payload = "<script>alert('XSS')</script>"
r = session.post(EMPLOYEE_URL, data={
    "full_name": payload,
    "age": 25,
    "salary": 40000,
    "phone": "9998887776",
    "department": "HR"
})
print("Create response:", r.json())

# Fetch it back and check it's escaped, not raw
r = session.get(LIST_URL)
employees = r.json()
last = employees[-1]
print("Stored full_name:", last['full_name'])

if "<script>" in last['full_name']:
    print("\n❌ VULNERABLE: raw script tag stored unescaped.")
else:
    print("\n✅ SAFE: payload was escaped, not stored as executable HTML.")