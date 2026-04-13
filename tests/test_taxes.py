from merit_api import MeritAPI
import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_ID = os.getenv("MERIT_API_ID")
API_KEY = os.getenv("MERIT_API_KEY")

if not API_ID or not API_KEY:
    print("Please set MERIT_API_ID and MERIT_API_KEY environment variables (or create a .env file).")
    exit(1)

client = MeritAPI(API_ID, API_KEY)

print("Fetching tax rates...")
try:
    taxes = client.taxes.get_list()
    print(f"Successfully fetched {len(taxes)} tax rates.")
    if taxes:
        print("First tax rate:")
        print(json.dumps(taxes[0], indent=2))
except Exception as e:
    print(f"Error fetching taxes: {e}")
