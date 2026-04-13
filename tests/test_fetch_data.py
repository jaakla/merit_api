from merit_api import MeritAPI
import os
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
print("Customers:", client.customers.get_list()[:1])
print("\nItems:", client.items.get_list()[:1])
