"""Force re-analysis of the 3 most recent sessions to pick up new AggregateItem format."""
import sys, os, json
from dotenv import load_dotenv
load_dotenv("Backend/.env")
sys.path.insert(0, os.path.join(os.getcwd(), "Backend"))

from core.database import get_db
from core import models

db = next(get_db())
sessions = db.query(models.Session).order_by(models.Session.created_at.desc()).limit(5).all()

# Force-wipe analytics_result for recent sessions so they get regenerated
for s in sessions:
    print(f"Clearing session {s.id} ({s.filename})...")
    s.analytics_result = None
    db.add(s)

db.commit()
print("Done! Sessions will be re-analyzed on next dashboard load.")
db.close()
