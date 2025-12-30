from flask import Flask
from app.config import Config
from app.ext import db, bcrypt, login_manager, init_mongo

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    with app.app_context():
        init_mongo(app)
        
        # Import Models to ensure they are registered with SQLAlchemy
        from app.models import sql_models

        # Create Tables if they don't exist
        # In production, use migrations (Flask-Migrate)
        db.create_all()

    # Register Blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.main_controller import main_bp
    from app.controllers.admin_controller import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    return app
