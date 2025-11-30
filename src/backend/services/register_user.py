import psycopg2
import bcrypt
import uuid
from src.multi_agent_analyst.db.db_core import conn 


def register_user(email: str, password: str):
    cur = conn.cursor()

    # Hash password
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode()

    # Assign a thread_id for this user
    thread_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO users (email, password_hash, thread_id)
        VALUES (%s, %s, %s)
        RETURNING id, thread_id;
    """, (email, password_hash, thread_id))

    conn.commit()

    user_id, thread_id = cur.fetchone()

    print("User created:")
    print(" user_id:", user_id)
    print(" thread_id:", thread_id)

# register_user("test@example.com", "mysecurepass")