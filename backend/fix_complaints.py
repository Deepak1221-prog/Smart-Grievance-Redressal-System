import requests
import json

BASE_URL = "http://localhost:8000"

# Register user
print("Registering user...")
reg = requests.post(f"{BASE_URL}/api/auth/register", json={
    "email": "testcitizen@example.com",
    "password": "pass123",
    "full_name": "Test Citizen",
    "phone": "9999999999",
    "ward": "Ward 1",
    "address": "Test Address",
    "role": "citizen"
})
print(f"Register: {reg.status_code} - {reg.text[:100]}")

# Login
print("\nLogging in...")
login = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": "testcitizen@example.com",
    "password": "pass123"
})
print(f"Login: {login.status_code}")

if login.status_code != 200:
    print("Login failed!")
    exit()

token = login.json()['access_token']
print(f"Token: {token[:30]}...")

# File complaint
print("\nFiling complaint...")
headers = {"Authorization": f"Bearer {token}"}
complaint = requests.post(
    f"{BASE_URL}/api/complaints/",
    json={
        "title": "Test Complaint",
        "description": "This is a test complaint",
        "category": "other",
        "ward": "Ward 1",
        "location": "Test Location",
        "is_anonymous": False
    },
    headers=headers
)

print(f"Complaint Status: {complaint.status_code}")
print(f"Response: {complaint.text}")

if complaint.status_code == 201:
    print("\n✅ SUCCESS! Complaint filed!")
    print(json.dumps(complaint.json(), indent=2))
else:
    print("\n❌ FAILED! Check backend logs")
