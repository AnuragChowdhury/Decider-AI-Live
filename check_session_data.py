"""Quick diagnostic: print session 40/41 stored analytics."""
import sys, os, json
from dotenv import load_dotenv
load_dotenv("Backend/.env")
sys.path.insert(0, os.path.join(os.getcwd(), "Backend"))

from core.database import get_db
from core import models

db = next(get_db())
sessions = db.query(models.Session).order_by(models.Session.created_at.desc()).limit(3).all()

for s in sessions:
    print(f"\n=== Session {s.id} ({s.filename}) ===")
    try:
        data = json.loads(s.analytics_result) if s.analytics_result else {}
    except:
        data = {}
    
    kpis = data.get("kpis", [])
    aggregates = data.get("aggregates", {})
    print(f"  KPIs: {len(kpis)}")
    for k in kpis:
        print(f"    - {k.get('id')}: {k.get('value')}")
    
    print(f"  Aggregates: {len(aggregates)}")
    for key, val in aggregates.items():
        if isinstance(val, list):
            print(f"    - {key}: LIST with {len(val)} rows")
        elif isinstance(val, dict):
            d = val.get("data")
            row_count = len(d) if d else 0
            print(f"    - {key}: DICT, data has {row_count} rows")
        else:
            print(f"    - {key}: {type(val)}")

db.close()
