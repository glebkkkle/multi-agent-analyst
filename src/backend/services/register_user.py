import bcrypt
import uuid
# 1. Change the import to get_conn
from src.multi_agent_analyst.db.db_core import get_conn 

def register_user(email: str, password: str):
    # 2. Use a context manager for the connection
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Hash password
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode()

            # Assign a thread_id for this user
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"

            try:
                cur.execute("""
                    INSERT INTO users (email, password_hash, thread_id)
                    VALUES (%s, %s, %s)
                    RETURNING id, thread_id;
                """, (email, password_hash, thread_id))

                # 3. Commit the transaction
                conn.commit()

                user_id, thread_id = cur.fetchone()

                print("User created successfully:")
                print(f" user_id: {user_id}")
                print(f" thread_id: {thread_id}")
                
                return {"user_id": user_id, "thread_id": thread_id}

            except Exception as e:
                conn.rollback() # Roll back if the insert fails (e.g., duplicate email)
                print(f"Error registering user: {e}")
                raise e

# Example usage:
# register_user("test@example.com", "mysecurepass")