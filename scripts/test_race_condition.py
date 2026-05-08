import threading
import requests

# 1. SETUP - Change these to match your actual routes and a valid user
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login" # Adjust path if needed
BOOKING_URL = f"{BASE_URL}/api/v1/bookings/"

# Replace with a user you know exists in your DB
LOGIN_DATA = {"username": "nikhil_test_final_v2@example.com", "password": "password123"} 

def get_token():
    print("Fetching Auth Token...")
    response = requests.post(LOGIN_URL, data=LOGIN_DATA)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Login Failed: {response.json()}")
        return None

TOKEN = get_token()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

PAYLOAD = {
    "trip_id": 1,
    "seat_ids": [7]
}

def make_booking(user_thread_id):
    try:
        # We use the same seat_id for everyone to trigger the Race Condition
        response = requests.post(BOOKING_URL, json=PAYLOAD, headers=HEADERS)
        detail = response.json().get('detail', 'Success')
        print(f"Thread {user_thread_id}: Status {response.status_code} - {detail}")
    except Exception as e:
        print(f"Thread {user_thread_id}: Request Failed - {e}")

if TOKEN:
    print("--- Starting Authenticated Race Condition Test ---")
    threads = []
    for i in range(5):
        t = threading.Thread(target=make_booking, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    print("--- Test Complete ---")
else:
    print("Could not start test without valid token.")