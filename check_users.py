import pymysql
import os
from dotenv import load_dotenv

load_dotenv("Backend/.env")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

def check_users():
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, email FROM users")
        users = cursor.fetchall()
        for u in users:
            print(f"User ID: {u['id']} - Email: {u['email']}")
    conn.close()

if __name__ == "__main__":
    check_users()
