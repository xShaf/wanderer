from dotenv import load_dotenv
import os

# Load env vars from app.env
load_dotenv("app.env")

from app import create_app
from app.ext import db, bcrypt
from app.models.sql_models import User

app = create_app()

def create_admin(username, password):
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"User {username} already exists.")
            return

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password_hash=hashed_password, is_admin=True)
        db.session.add(user)
        db.session.commit()
        print(f"Admin user {username} created successfully.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>")
    else:
        create_admin(sys.argv[1], sys.argv[2])
