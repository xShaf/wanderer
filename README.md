# Wanderer Bot 🌌

Wanderer Bot is a feature-rich, Genshin Impact-themed AI chat application built with **Flask** and **Google Gemini**. It allows users to chat with a knowledgeable "Traveler" persona, take interactive quizzes, track their adventure progress, and manage their journey through a responsive dashboard.

## ✨ Features

*   **AI Chat with Grounding**: Powered by Google's `google-genai` SDK. Includes Search Grounding to provide up-to-date answers about crucial game updates (e.g., "What is in Version 6.2?").
*   **Interactive Quizzes**: Generate Genshin-themed trivia questions dynamically.
*   **Gamification**:
    *   **EXP System**: Earn points for chatting and answering quizzes correctly.
    *   **Trophies**: Track your correct answers with a trophy counter.
*   **Dual Database Architecture**:
    *   **PostgreSQL (Neon SQL)**: Manages users, configuration, and scores.
    *   **MongoDB**: Stores chat logs and quiz history for scalable retrieval.
*   **Admin Dashboard**:
    *   Dynamically switch between Gemini Models (e.g., `gemini-2.5-flash`, `gemini-1.5-pro`).
    *   Manage registered users (promote/delete).
*   **Responsive Design**: Fully optimized for Desktop and Mobile devices using Bootstrap 5.

## 🛠️ Tech Stack

*   **Backend**: Python, Flask (MVC Pattern)
*   **Database**: PostgreSQL (via SQLAlchemy), MongoDB (via PyMongo)
*   **AI**: Google GenAI SDK (Gemini 2.0/1.5)
*   **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
*   **Auth**: Flask-Login, Bcrypt

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone <repository_url>
cd wanderer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
**Crucial Step**: You must create a file named `app.env` in the root directory. This file holds your secrets.

#### `app.env` Template
Copy the following into your `app.env` file:

```properties
# 1. Application Secret (Required for sessions)
SECRET_KEY=your_generated_secret_key_here

# 2. Databases
# PostgreSQL Connection String
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# MongoDB Connection String
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/wanderer_chat?retryWrites=true&w=majority

# 3. Google AI (Gemini)
GEMINI_API_KEY=

# 4. Admin Defaults
ADMIN_USERNAME=admin
```

#### Where to get these keys?

| Variable | Description | Where to obtain? |
| :--- | :--- | :--- |
| `SECRET_KEY` | Secures user sessions. | Run `python -c 'import secrets; print(secrets.token_hex(16))'` in your terminal to generate one. |
| `DATABASE_URL` | Connects to PostgreSQL. | Create a project at **[Neon.tech](https://neon.tech)**. Copy the connection string from the Dashboard. |
| `MONGO_URI` | Connects to MongoDB. | Create a cluster at **[MongoDB Atlas](https://www.mongodb.com/atlas)**. Go to "Connect" > "Drivers" to get your URI. Replace `<password>` with your database user password. |
| `GEMINI_API_KEY` | Powers the AI Chat. | Get a free API key from **[Google AI Studio](https://aistudio.google.com/app/apikey)**. |
| `ADMIN_USERNAME` | Default admin name. | Set this to whatever you want your admin script to use (e.g., `admin` or `paimon`). |

> [!NOTE]
> If you do not provide `DATABASE_URL`, the app will fallback to a local SQLite database (`wanderer_dev.db`) for development.

### 4. Database Setup
The application will automatically create SQL tables on first run.
To add the latest schema changes (like Trophies column) if updating from an older version:
```bash
python migrate_db.py
```

### 5. Create an Admin User
Use the helper script to create your first admin:
```bash
python create_admin.py admin <your_password>
```

### 6. Run the Application
```bash
python run.py
```
Visit `http://localhost:5000` in your browser.

## 📖 Usage Guide

### User
1.  **Register/Login**: Create an account to start your journey.
2.  **Dashboard**:
    *   **Chat**: Ask questions about Teyvat.
    *   **Quiz**: Enter a topic (e.g., "Archons") and click "Generate Question".
    *   **History**: Check the "Quiz History" tab to see past results.
    *   **Stats**: View your EXP and Trophies on the right panel.

### Admin
1.  Log in with an account marked as `is_admin`.
2.  Click the **Admin Panel** button on the dashboard.
3.  **Model Configuration**: Change the active AI model to handle rate limits or test new features.
4.  **User Management**: View user stats or ban (delete) users.

## 📂 Project Structure

```
wanderer/
├── app/
│   ├── controllers/      # Route logic (Auth, Main, Admin)
│   ├── models/           # DB Models (SQL & Mongo)
│   ├── services/         # Gemini AI Service
│   ├── static/           # CSS, JS, Images, Fonts
│   ├── templates/        # HTML Templates (Jinja2)
│   ├── __init__.py       # App Factory
│   ├── config.py         # Config Class
│   └── ext.py            # Extensions Init
├── app.env               # Environment Variables (Ignored in Git)
├── create_admin.py       # Admin creation script
├── migrate_db.py         # DB Migration script
├── run.py                # Entry Point
└── wanderer.py           # Legacy file (Reference)
```

---
*Ad Astra Abyssosque!* ✨
