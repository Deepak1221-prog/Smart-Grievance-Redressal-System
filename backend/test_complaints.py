import requests

BASE_URL = "http://localhost:8000"

# Step 1: Register a user
print("1. Registering user...")
register_data = {
    "email": "testuser@example.com",
    "password": "test123",
    "full_name": "Test User",
    "phone": "1234567890",
    "ward": "Ward 5",
    "address": "123 Test Street",
    "role": "citizen"
}

register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)

if register_response.status_code == 201:
    print("✅ User registered successfully!")
elif register_response.status_code == 400:
    print("⚠️ User already exists, proceeding to login...")
else:
    print(f"❌ Registration failed: {register_response.text}")
    exit()

# Step 2: Login to get token
print("\n2. Logging in...")
login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": "citizen@test.com",  # Use the user from test_api.py
    "password": "test123"
})


if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit()

token = login_response.json()['access_token']
print(f"✅ Login successful! Token: {token[:30]}...")

# Step 3: Set up headers with authentication
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Step 4: Create a complaint
print("\n3. Creating complaint...")
complaint_data = {
    "title": "Broken Street Light",
    "description": "The street light on Main Street has been broken for 3 days",
    "category": "street_lights",
    "ward": "Ward 5",
    "location": "Main Street, near Park",
    "is_anonymous": False
}

complaint_response = requests.post(
    f"{BASE_URL}/api/complaints/",
    json=complaint_data,
    headers=headers
)

print(f"Status Code: {complaint_response.status_code}")
print(f"Response: {complaint_response.text}")

if complaint_response.status_code == 201:
    print("\n✅ Complaint created successfully!")
    complaint = complaint_response.json()
    print(f"Complaint ID: {complaint['complaint_id']}")
    print(f"Title: {complaint['title']}")
    print(f"Category: {complaint['category']}")
    print(f"Priority: {complaint['priority']}")
    print(f"Status: {complaint['status']}")
    print(f"Sentiment Score: {complaint['sentiment_score']}")
else:
    print(f"\n❌ Failed to create complaint")
    print("Check the backend terminal for detailed errors")

# Step 5: List all complaints
print("\n4. Listing complaints...")
list_response = requests.get(
    f"{BASE_URL}/api/complaints/",
    headers=headers
)

if list_response.status_code == 200:
    complaints = list_response.json()
    print(f"✅ Found {len(complaints)} complaint(s)")
    for c in complaints:
        print(f"  - {c['complaint_id']}: {c['title']} [{c['status']}]")
else:
    print(f"❌ Failed to list complaints: {list_response.text}")
