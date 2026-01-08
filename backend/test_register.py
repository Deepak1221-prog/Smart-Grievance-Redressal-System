import requests
import json

BASE_URL = "http://localhost:8000"

# Try to register
user_data = {
    "email": "newuser@test.com",
    "password": "test123",
    "full_name": "New User",
    "phone": "9876543210",
    "ward": "Ward 1",
    "address": "Test Address",
    "role": "citizen"
}

print("Attempting registration...")
print(f"Data: {json.dumps(user_data, indent=2)}")

response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 201:
    print("\n✅ Registration successful!")
else:
    print("\n❌ Registration failed!")
    print("Check the backend terminal for detailed error")
