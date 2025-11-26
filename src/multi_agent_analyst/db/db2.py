import psycopg2

conn = psycopg2.connect(
    dbname="multi_analyst",
    user="glebkle",
    password="123",
    host="localhost",
    port=5432
)