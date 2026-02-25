import pymysql
import os
from dotenv import load_dotenv
import json

# Load from Backend/.env
load_dotenv("Backend/.env")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

print(f"Connecting to {DB_HOST} (DB: {DB_NAME})...")

def check_sessions():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, user_id, dataset_id, filename, validation_report, analytics_result FROM sessions ORDER BY id DESC LIMIT 10")
            sessions = cursor.fetchall()
            
            if not sessions:
                print("No sessions found in database.")
                return

            for s in sessions:
                print(f"--- Session ID: {s['id']} (User: {s['user_id']}) ---")
                print(f"Filename: {s['filename']}")
                
                try:
                    val = json.loads(s['validation_report']) if s['validation_report'] else {}
                    print(f"Validation Status: {val.get('status', 'Unknown')}")
                except:
                    print("Validation Status: (Invalid JSON)")
                
                try:
                    anal_raw = s['analytics_result']
                    anal = json.loads(anal_raw) if anal_raw else {}
                    print(f"Analytics Status: {anal.get('status', 'Unknown')}")
                    print(f"Full Result: {anal_raw[:500]}...") # Print first 500 chars
                    
                    if anal.get('status') == 'PROCESSING':
                        print("  (!) Still processing...")
                    elif anal.get('status') == 'ERROR':
                        print(f"  (X) Error: {anal.get('error')}")
                    else:
                        kpis = anal.get('kpis', [])
                        print(f"  KPIs: {len(kpis)}")
                        aggs = anal.get('aggregates', {})
                        print(f"  Aggregates: {list(aggs.keys())}")
                except Exception as e:
                    print(f"Analytics Error parsing: {e}")
                print("\n")
                
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_sessions()
