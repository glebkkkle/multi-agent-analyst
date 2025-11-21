import os
import sqlite3

# Directory of THIS file:
# /.../multi_agent_analyst/src/multi_agent_analyst/db/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate up to project root:
# /.../multi_agent_analyst/
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

DB_PATH = os.path.join(PROJECT_ROOT, "data", "company_data.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
