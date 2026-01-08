import requests
import json

BASE_URL = "http://localhost:8000"

user_data = {
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
    "phone": "1234567890",
    "ward": "Ward 1",
    "address": "123 Test Street",
    "role": "citizen"
}

print("Sending registration request...")
print(f"Data: {json.dumps(user_data, indent=2)}")

response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code != 201:
    print("\n❌ Registration failed!")
    print("Check the backend terminal for detailed error logs")
else:
    print("\n✅ Registration successful!")
    print(f"User data: {json.dumps(response.json(), indent=2)}")
