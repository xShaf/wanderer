import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    
    # Database Config - Neon SQL (PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        print("WARNING: DATABASE_URL not set. Falling back to SQLite for development.")
        SQLALCHEMY_DATABASE_URI = "sqlite:///wanderer_dev.db"
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MongoDB Config
    MONGO_URI = os.getenv("MONGO_URI")
    
    # Gemini Config
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Admin Config
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
