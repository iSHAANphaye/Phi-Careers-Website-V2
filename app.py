import os
from flask import Flask, redirect, url_for, render_template, request, session, flash
from auth import auth_bp, login_required, role_required
import db_helper
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
    user_id = session['user_id']
    role = session['role']
    
    # Fetch user data to pass profile statistics (frictionless forms)
    user_profile = db_helper.fetch_one("SELECT name, email FROM users WHERE user_id = %s", (user_id,))
    
    if role == 'candidate':
        # Fetch active job listings, including any draft data for the logged-in candidate
        jobs_query = """
            SELECT j.*, c.name as company_name, a.cover_letter as draft_cover_letter, a.current_step as draft_step
            FROM job_listings j
            JOIN companies c ON j.company_id = c.company_id
            LEFT JOIN applications a ON j.job_id = a.job_id AND a.user_id = %s AND a.status = 'draft'
            WHERE j.status = 'open'
            ORDER BY j.created_at DESC
        """
        jobs = db_helper.fetch_all(jobs_query, (user_id,))
        
        # Fetch all candidate applications with live statuses for the tracking pipeline
        apps_query = """
            SELECT a.*, j.title as job_title, c.name as company_name
            FROM applications a
            JOIN job_listings j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            WHERE a.user_id = %s
            ORDER BY a.updated_at DESC
        """
        applications = db_helper.fetch_all(apps_query, (user_id,))
        
        return render_template(
            'candidate/dashboard.html', 
            user=user_profile, 
            jobs=jobs, 
            applications=applications
        )
        
    elif role == 'employer':
        # Get or create a default company for simple setup
        company = db_helper.fetch_one("SELECT * FROM companies LIMIT 1")
        if not company:
            company_id = db_helper.execute_query(
                "INSERT INTO companies (name, website, description) VALUES (%s, %s, %s)",
                ("Phi Careers Corp", "https://phicareers.com", "A recruitment agency.")
            )
        else:
            company_id = company['company_id']
            
        # Fetch all jobs posted
        jobs_query = """
            SELECT j.*, c.name as company_name
            FROM job_listings j
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY j.created_at DESC
        """
        jobs = db_helper.fetch_all(jobs_query)
        
        # Fetch all applications received for jobs
        apps_query = """
            SELECT a.*, u.name as candidate_name, u.email as candidate_email, j.title as job_title
            FROM applications a
            JOIN users u ON a.user_id = u.user_id
            JOIN job_listings j ON a.job_id = j.job_id
            ORDER BY a.updated_at DESC
        """
        applications = db_helper.fetch_all(apps_query)
        
        return render_template(
            'employer/dashboard.html', 
            user=user_profile, 
            jobs=jobs, 
            applications=applications
        )

# Candidate Apply Route
@app.route('/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
@role_required('candidate')
def apply_job(job_id):
    user_id = session['user_id']
    cover_letter = request.form.get('cover_letter', '').strip()
    resume_url = request.form.get('resume_url', '').strip()
    
    if not cover_letter or not resume_url:
        flash("Resume path and cover letter are required to submit an application.", "error")
        return redirect(url_for('dashboard'))
        
    try:
        # Parameterized upsert using ON DUPLICATE KEY UPDATE
        apply_query = """
            INSERT INTO applications (user_id, job_id, status, current_step, cover_letter, resume_url, applied_at)
            VALUES (%s, %s, 'applied', 2, %s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
            status = 'applied', current_step = 2, cover_letter = VALUES(cover_letter), 
            resume_url = VALUES(resume_url), applied_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        """
        db_helper.execute_query(apply_query, (user_id, job_id, cover_letter, resume_url))
        flash("Application submitted successfully!", "success")
    except Exception as e:
        flash("Failed to submit application. Please try again.", "error")
        print(f"Apply Error: {e}")
        
    return redirect(url_for('dashboard'))

# Candidate Save Draft Route
@app.route('/jobs/<int:job_id>/save-draft', methods=['POST'])
@login_required
@role_required('candidate')
def save_draft(job_id):
    user_id = session['user_id']
    cover_letter = request.form.get('cover_letter', '').strip()
    resume_url = request.form.get('resume_url', '').strip()
    
    try:
        # Parameterized upsert for draft state
        draft_query = """
            INSERT INTO applications (user_id, job_id, status, current_step, cover_letter, resume_url)
            VALUES (%s, %s, 'draft', 2, %s, %s)
            ON DUPLICATE KEY UPDATE
            status = 'draft', current_step = 2, cover_letter = VALUES(cover_letter), 
            resume_url = VALUES(resume_url), updated_at = CURRENT_TIMESTAMP
        """
        db_helper.execute_query(draft_query, (user_id, job_id, cover_letter, resume_url))
        flash("Application draft saved successfully.", "success")
    except Exception as e:
        flash("Failed to save draft. Please try again.", "error")
        print(f"Draft Error: {e}")
        
    return redirect(url_for('dashboard'))

# Employer Create Job Listing Route
@app.route('/jobs/create', methods=['POST'])
@login_required
@role_required('employer')
def create_job():
    title = request.form.get('title', '').strip()
    location = request.form.get('location', '').strip()
    salary = request.form.get('salary', '').strip()
    description = request.form.get('description', '').strip()
    
    if not title or not location or not salary or not description:
        flash("All job listing fields are required.", "error")
        return redirect(url_for('dashboard'))
        
    try:
        # Get or create a company to associate listing with
        company = db_helper.fetch_one("SELECT * FROM companies LIMIT 1")
        if not company:
            company_id = db_helper.execute_query(
                "INSERT INTO companies (name, website, description) VALUES (%s, %s, %s)",
                ("Phi Careers Corp", "https://phicareers.com", "A recruitment agency.")
            )
        else:
            company_id = company['company_id']
            
        insert_query = """
            INSERT INTO job_listings (company_id, title, description, location, salary, status)
            VALUES (%s, %s, %s, %s, %s, 'open')
        """
        db_helper.execute_query(insert_query, (company_id, title, description, location, salary))
        flash("Job listing published successfully!", "success")
    except Exception as e:
        flash("Failed to publish job listing. Please try again.", "error")
        print(f"Create Job Error: {e}")
        
    return redirect(url_for('dashboard'))

# Employer Update Applicant Status Route
@app.route('/applications/<int:app_id>/status', methods=['POST'])
@login_required
@role_required('employer')
def update_app_status(app_id):
    new_status = request.form.get('status', '').strip()
    
    if new_status not in ['reviewed', 'rejected', 'hired']:
        flash("Invalid status transition.", "error")
        return redirect(url_for('dashboard'))
        
    try:
        update_query = "UPDATE applications SET status = %s WHERE application_id = %s"
        db_helper.execute_query(update_query, (new_status, app_id))
        flash(f"Candidate application status updated to '{new_status}'.", "success")
    except Exception as e:
        flash("Failed to update status. Please try again.", "error")
        print(f"Status Update Error: {e}")
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Start the local development server
    app.run(debug=True, port=5001)
