import psycopg2

conn = psycopg2.connect(
    dbname="multi_analyst",
    user="glebkle",
    password="123",
    host="localhost",
    port=5432
)


def get_conn(thread_id):
    conn = psycopg2.connect(
    dbname="multi_analyst",
    user="glebkle",
    password="123",
    host="localhost",
    port=5432
)

    cur = conn.cursor()

    if thread_id is not None:
        cur.execute(f"SET search_path TO {thread_id}, public;")

    return conn