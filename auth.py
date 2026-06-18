from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import db_helper
import re

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# Create the authentication blueprint
auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to protect routes from unauthenticated traffic."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator to restrict routes based on user role (candidate/employer)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if session.get('role') not in roles:
                flash("You do not have permission to view this page.", "error")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'candidate').strip()
        
        if not name or not email or not password or role not in ['candidate', 'employer']:
            flash("All fields are required and role must be valid.", "error")
            return redirect(url_for('auth.register'))
            
        if not EMAIL_REGEX.match(email):
            flash("Please provide a valid email address.", "error")
            return redirect(url_for('auth.register'))
            
        # Check if user already exists
        existing_user = db_helper.fetch_one(
            "SELECT user_id FROM users WHERE email = %s", 
            (email,)
        )
        if existing_user:
            flash("An account with that email already exists.", "error")
            return redirect(url_for('auth.register'))
            
        # Hash password and insert user safely using parameterized query
        pw_hash = generate_password_hash(password)
        try:
            db_helper.execute_query(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                (name, email, pw_hash, role)
            )
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash("An error occurred during registration. Please try again.", "error")
            print(f"Registration Error: {e}")
            
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Parameterized SELECT to prevent SQL injection
        user = db_helper.fetch_one(
            "SELECT * FROM users WHERE email = %s", 
            (email,)
        )
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            session['role'] = user['role']
            flash("Welcome back!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "error")
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))
