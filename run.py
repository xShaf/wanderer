from dotenv import load_dotenv
import os

# Load env vars from app.env in the current directory
load_dotenv("app.env")

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
