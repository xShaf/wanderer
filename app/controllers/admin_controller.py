from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.ext import db
from app.models.sql_models import User, AppConfig
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    
    # Get current Gemini Model
    config = AppConfig.query.filter_by(key="gemini_model").first()
    current_model = config.value if config else "gemini-2.0-flash-exp"
    
    return render_template('admin_dashboard.html', users=users, current_model=current_model)

@admin_bp.route('/update_model', methods=['POST'])
@login_required
@admin_required
def update_model():
    model_name = request.form.get('model_name')
    if model_name:
        config = AppConfig.query.filter_by(key="gemini_model").first()
        if not config:
            config = AppConfig(key="gemini_model", value=model_name)
            db.session.add(config)
        else:
            config.value = model_name
        db.session.commit()
        flash(f"Gemini Model updated to {model_name}", "success")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("Cannot delete admin user.", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted.", "success")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    # Prevent self-demotion if desired, but allowing for now (risky!)
    if user.id == current_user.id:
         flash("Cannot change own admin status.", "warning")
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"User {user.username} admin status toggled.", "success")
    return redirect(url_for('admin.dashboard'))
