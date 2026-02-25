import requests
from pathlib import Path

def test_chat_with_data():
    url = "http://127.0.0.1:8000/api/chat_with_data"
    
    # Use local real sales data
    file_path = Path("data/sales_data_sample.csv")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    print(f"Testing endpoint {url} with {file_path.name}...")
    
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "text/csv")}
        data = {
            "query": "What is the total sales and what's the trend?",
            "validation_mode": "lenient",
            "persist": True
        }
        
        try:
            # Bypass proxies
            session = requests.Session()
            session.trust_env = False
            
            response = session.post(url, files=files, data=data)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("\n=== Chat Response ===")
                print(result.get("chat_response"))
                
                print("\n=== Validation Summary ===")
                print(result.get("validation", {}).get("summary"))
                
                print("\n=== Analytics KPIs ===")
                kpis = result.get("analytics", {}).get("kpis", [])
                for kpi in kpis:
                    print(f"- {kpi.get('label')}: {kpi.get('value')}")
            else:
                print("Error Response:")
                print(response.text)
                
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_chat_with_data()
