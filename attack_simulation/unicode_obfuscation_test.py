import requests

REGISTER_URL = "http://127.0.0.1:5000/register"

# Each payload pairs a human-readable description with the actual obfuscated string
PAYLOADS = [
    ("Cyrillic look-alike 'а' instead of Latin 'a'", "аdmin_123"),        # а = U+0430
    ("Full-width Unicode letters", "ａｄｍｉｎ１２３"),                    # fullwidth forms
    ("Zero-width space injected mid-username", "adm\u200bin_123"),        # invisible char
    ("Right-to-left override trick", "admin\u202e123_"),                  # RTL override
    ("Combining diacritical marks stacked on ASCII", "a\u0301dmin_123"),  # a + combining accent
]

print("=== Unicode Obfuscation Test ===")
for description, payload in PAYLOADS:
    r = requests.post(REGISTER_URL, data={
        "username": payload,
        "email": f"test_{abs(hash(payload))}@example.com",
        "password": "TestPass123!"
    })
    blocked = r.status_code == 400
    print(f"Test: {description}")
    print(f"  Raw payload: {payload!r}")
    print(f"  Status: {r.status_code} | Blocked: {blocked}")
    print(f"  Response: {r.json()}")
    print()