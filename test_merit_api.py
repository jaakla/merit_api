from merit_api import MeritAPI
import json
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_connection():
    # Using the credentials from the environment
    API_ID = os.getenv("MERIT_API_ID")
    API_KEY = os.getenv("MERIT_API_KEY")
    
    if not API_ID or not API_KEY:
        print("Please set MERIT_API_ID and MERIT_API_KEY environment variables (or create a .env file).")
        return
    
    client = MeritAPI(API_ID, API_KEY)
    
    print("--- Testing Merit API Connection ---")
    
    try:
        # 1. Test Customers
        print("\n[1] Testing customers.get_list()...")
        customers = client.customers.get_list()
        print(f"Success! Found {len(customers)} customers.")
        
        # 2. Test Items
        print("\n[2] Testing items.get_list()...")
        items = client.items.get_list()
        print(f"Success! Found {len(items)} items.")
        
        # 3. Test Banks
        print("\n[3] Testing financial.get_banks()...")
        banks = client.financial.get_banks()
        print(f"Success! Found {len(banks)} banks.")

        # 4. Test Projects
        print("\n[4] Testing financial.get_projects()...")
        projects = client.financial.get_projects()
        print(f"Success! Found {len(projects)} projects.")
        
    except Exception as e:
        print(f"\n[!] Error during testing: {e}")

if __name__ == "__main__":
    test_connection()
