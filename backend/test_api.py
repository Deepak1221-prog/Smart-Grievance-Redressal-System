import requests

# Test the API
BASE_URL = "http://localhost:8000"

# Test health endpoint
response = requests.get(f"{BASE_URL}/health")
print(f"✅ Health check: {response.json()}")

# Test root endpoint
response = requests.get(BASE_URL)
print(f"✅ Root: {response.json()}")

# Register a test user
user_data = {
    "email": "citizen@test.com",
    "password": "test123",
    "full_name": "Test Citizen",
    "phone": "9876543210",
    "ward": "Ward 5",
    "address": "Test Address",
    "role": "citizen"
}

response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
if response.status_code == 201:
    print(f"✅ User registered: {response.json()['email']}")
elif response.status_code == 400:
    print(f"⚠️ User already exists")
else:
    print(f"❌ Registration failed: {response.text}")

# Login
login_data = {
    "email": "citizen@test.com",
    "password": "test123"
}

response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
if response.status_code == 200:
    token = response.json()['access_token']
    print(f"✅ Login successful! Token: {token[:20]}...")
else:
    print(f"❌ Login failed: {response.text}")
