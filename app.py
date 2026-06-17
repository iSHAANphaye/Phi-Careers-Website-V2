import os
from flask import Flask, redirect, url_for, render_template_string, session
from auth import auth_bp, login_required
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

app = Flask(__name__)
# Secure token session initialization using protected secret key
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")

# Register Authentication Blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Render dashboard showing custom welcome message based on role
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phi Careers - Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f8fafc; color: #334155; padding: 50px; }
            .card { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
            h2 { color: #0f172a; margin-top: 0; }
            .meta { color: #64748b; font-size: 14px; margin-bottom: 20px; }
            .btn { display: inline-block; background-color: #ef4444; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold; }
            .btn:hover { background-color: #dc2626; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Welcome, {{ session['name'] }}!</h2>
            <p class="meta">Role: <strong>{{ session['role'] | capitalize }}</strong></p>
            <p>You have successfully logged into the recruitment platform. This dashboard will contain your job listings and applications.</p>
            <a href="{{ url_for('auth.logout') }}" class="btn">Log Out</a>
        </div>
    </body>
    </html>
    """)

if __name__ == '__main__':
    # Start the local development server
    app.run(debug=True, port=5000)
