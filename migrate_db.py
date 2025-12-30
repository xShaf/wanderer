import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Load env vars
load_dotenv("app.env")

db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("DATABASE_URL not found in app.env. Are you using SQLite? If so, delete wanderer_dev.db to reset.")
    exit()

try:
    print(f"Connecting to database...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check if column exists
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='correct_quizzes';")
    if cur.fetchone():
        print("Column 'correct_quizzes' already exists.")
    else:
        print("Adding column 'correct_quizzes'...")
        cur.execute("ALTER TABLE users ADD COLUMN correct_quizzes INTEGER DEFAULT 0;")
        print("Column added successfully.")
        
    conn.close()
    
except Exception as e:
    print(f"Migration failed: {e}")
