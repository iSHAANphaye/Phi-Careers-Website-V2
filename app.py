import os
# pyrefly: ignore [missing-import]
from flask import Flask, redirect, url_for, render_template, request, session, flash
from auth import auth_bp, login_required, role_required
import db_helper
# pyrefly: ignore [missing-import]
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
    # Fetch a preview of the 3 most recently posted open job listings
    featured_query = """
        SELECT j.*, c.name as company_name
        FROM job_listings j
        JOIN companies c ON j.company_id = c.company_id
        WHERE j.status = 'open'
        ORDER BY j.created_at DESC
        LIMIT 3
    """
    featured_jobs = []
    try:
        featured_jobs = db_helper.fetch_all(featured_query)
    except Exception as e:
        print(f"Failed to fetch featured jobs: {e}")
        
    return render_template('index.html', featured_jobs=featured_jobs)

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
        company = db_helper.fetch_one("SELECT * FROM companies WHERE user_id = %s", (user_id,))
        if not company:
            try:
                company_id = db_helper.execute_query(
                    "INSERT INTO companies (user_id, name, website, description) VALUES (%s, %s, %s, %s)",
                    (user_id, "Phi Careers Corp", "https://phicareers.com", "A recruitment agency.")
                )
                # Fetch the newly created company record
                company = db_helper.fetch_one("SELECT * FROM companies WHERE company_id = %s", (company_id,))
            except Exception as e:
                flash("Failed to initialize company. Please try again.", "error")
                print(f"Company Initialization Error: {e}")
                return render_template('employer/dashboard.html', user=user_profile, jobs=[], company=None, applications=[])
        
        company_id = company['company_id']
            
        # Fetch all jobs posted by this company
        jobs_query = """
            SELECT j.*, c.name as company_name
            FROM job_listings j
            JOIN companies c ON j.company_id = c.company_id
            WHERE j.company_id = %s
            ORDER BY j.created_at DESC
        """
        jobs = db_helper.fetch_all(jobs_query, (company_id,))
        
        # Fetch all applications received for this company's jobs
        apps_query = """
            SELECT a.*, u.name as candidate_name, u.email as candidate_email, j.title as job_title
            FROM applications a
            JOIN users u ON a.user_id = u.user_id
            JOIN job_listings j ON a.job_id = j.job_id
            WHERE a.status != 'draft' AND j.company_id = %s
            ORDER BY a.updated_at DESC
        """
        applications = db_helper.fetch_all(apps_query, (company_id,))
        
        return render_template(
            'employer/dashboard.html', 
            user=user_profile, 
            company=company,
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
        
    # BUG-05 & BUG-06: Check if job exists and is open
    job = db_helper.fetch_one("SELECT status FROM job_listings WHERE job_id = %s", (job_id,))
    if not job:
        flash("Job listing not found.", "error")
        return redirect(url_for('dashboard'))
    if job['status'] != 'open':
        flash("This job listing is closed and no longer accepting applications.", "error")
        return redirect(url_for('dashboard'))
        
    # BUG-07: Verify candidate has not already submitted an application
    existing_app = db_helper.fetch_one("SELECT status FROM applications WHERE user_id = %s AND job_id = %s", (user_id, job_id))
    if existing_app and existing_app['status'] != 'draft':
        flash("You have already submitted an application for this job.", "error")
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
    
    # BUG-05 & BUG-06: Check if job exists and is open
    job = db_helper.fetch_one("SELECT status FROM job_listings WHERE job_id = %s", (job_id,))
    if not job:
        flash("Job listing not found.", "error")
        return redirect(url_for('dashboard'))
    if job['status'] != 'open':
        flash("This job listing is closed and cannot save draft.", "error")
        return redirect(url_for('dashboard'))
        
    # BUG-08: Verify candidate is not demoting a submitted application to draft
    existing_app = db_helper.fetch_one("SELECT status FROM applications WHERE user_id = %s AND job_id = %s", (user_id, job_id))
    if existing_app and existing_app['status'] != 'draft':
        flash("You cannot save a draft for a submitted application.", "error")
        return redirect(url_for('dashboard'))
        
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
        
    # BUG-16: Enforce job title, location, description length boundaries
    if len(title) > 100:
        flash("Title must be 100 characters or less.", "error")
        return redirect(url_for('dashboard'))
    if len(location) > 100:
        flash("Location must be 100 characters or less.", "error")
        return redirect(url_for('dashboard'))
    if len(description) > 1000:
        flash("Description must be 1000 characters or less.", "error")
        return redirect(url_for('dashboard'))
        
    try:
        salary_val = float(salary)
        # BUG-03: Enforce positive salary bounds
        if salary_val < 0:
            flash("Salary must be a positive number.", "error")
            return redirect(url_for('dashboard'))
        # BUG-11: Enforce salary upper-bound (under DECIMAL(10,2) overflow limit)
        if salary_val >= 100000000:
            flash("Salary must be less than 100,000,000.", "error")
            return redirect(url_for('dashboard'))
    except ValueError:
        flash("Invalid salary format. Please enter a valid number.", "error")
        return redirect(url_for('dashboard'))
        
    user_id = session['user_id']
    try:
        # Get or create a company to associate listing with
        company = db_helper.fetch_one("SELECT * FROM companies WHERE user_id = %s", (user_id,))
        if not company:
            company_id = db_helper.execute_query(
                "INSERT INTO companies (user_id, name, website, description) VALUES (%s, %s, %s, %s)",
                (user_id, "Phi Careers Corp", "https://phicareers.com", "A recruitment agency.")
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

# Employer Update Job Listing Route
@app.route('/jobs/<int:job_id>/update', methods=['POST'])
@login_required
@role_required('employer')
def update_job(job_id):
    title = request.form.get('title', '').strip()
    location = request.form.get('location', '').strip()
    salary = request.form.get('salary', '').strip()
    description = request.form.get('description', '').strip()
    status = request.form.get('status', '').strip()
    
    if not title or not location or not salary or not description or not status:
        flash("All job listing fields are required.", "error")
        return redirect(url_for('dashboard'))
        
    if len(title) > 100:
        flash("Title must be 100 characters or less.", "error")
        return redirect(url_for('dashboard'))
    if len(location) > 100:
        flash("Location must be 100 characters or less.", "error")
        return redirect(url_for('dashboard'))
    if len(description) > 1000:
        flash("Description must be 1000 characters or less.", "error")
        return redirect(url_for('dashboard'))
    if status not in ['open', 'closed']:
        flash("Invalid status selection.", "error")
        return redirect(url_for('dashboard'))
        
    try:
        salary_val = float(salary)
        if salary_val < 0:
            flash("Salary must be a positive number.", "error")
            return redirect(url_for('dashboard'))
        if salary_val >= 100000000:
            flash("Salary must be less than 100,000,000.", "error")
            return redirect(url_for('dashboard'))
    except ValueError:
        flash("Invalid salary format. Please enter a valid number.", "error")
        return redirect(url_for('dashboard'))
        
    user_id = session['user_id']
    try:
        company = db_helper.fetch_one("SELECT * FROM companies WHERE user_id = %s", (user_id,))
        if not company:
            flash("Company profile not found.", "error")
            return redirect(url_for('dashboard'))
            
        # Verify job ownership
        job = db_helper.fetch_one("SELECT * FROM job_listings WHERE job_id = %s AND company_id = %s", (job_id, company['company_id']))
        if not job:
            flash("Job listing not found or unauthorized.", "error")
            return redirect(url_for('dashboard'))
            
        update_query = """
            UPDATE job_listings 
            SET title = %s, description = %s, location = %s, salary = %s, status = %s 
            WHERE job_id = %s
        """
        db_helper.execute_query(update_query, (title, description, location, salary_val, status, job_id))
        flash("Job listing updated successfully!", "success")
    except Exception as e:
        flash("Failed to update job listing. Please try again.", "error")
        print(f"Update Job Error: {e}")
        
    return redirect(url_for('dashboard'))

# Employer Delete Job Listing Route
@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required('employer')
def delete_job(job_id):
    user_id = session['user_id']
    try:
        company = db_helper.fetch_one("SELECT * FROM companies WHERE user_id = %s", (user_id,))
        if not company:
            flash("Company profile not found.", "error")
            return redirect(url_for('dashboard'))
            
        # Verify job ownership
        job = db_helper.fetch_one("SELECT * FROM job_listings WHERE job_id = %s AND company_id = %s", (job_id, company['company_id']))
        if not job:
            flash("Job listing not found or unauthorized.", "error")
            return redirect(url_for('dashboard'))
            
        delete_query = "DELETE FROM job_listings WHERE job_id = %s"
        db_helper.execute_query(delete_query, (job_id,))
        flash("Job listing deleted successfully!", "success")
    except Exception as e:
        flash("Failed to delete job listing. Please try again.", "error")
        print(f"Delete Job Error: {e}")
        
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
        
    # Check if application exists
    app_record = db_helper.fetch_one("SELECT status FROM applications WHERE application_id = %s", (app_id,))
    if not app_record:
        flash("Application not found.", "error")
        return redirect(url_for('dashboard'))
        
    # BUG-09: Block employers from modifying or updating draft applications
    if app_record['status'] == 'draft':
        flash("Cannot update status of a draft application.", "error")
        return redirect(url_for('dashboard'))
        
    try:
        update_query = "UPDATE applications SET status = %s WHERE application_id = %s"
        db_helper.execute_query(update_query, (new_status, app_id))
        flash(f"Candidate application status updated to '{new_status}'.", "success")
        
        # Trigger email notification for hired or rejected transitions
        if new_status in ['hired', 'rejected']:
            details_query = """
                SELECT 
                    u.email AS candidate_email,
                    u.name AS candidate_name,
                    j.title AS job_title,
                    c.name AS company_name
                FROM applications a
                JOIN users u ON a.user_id = u.user_id
                JOIN job_listings j ON a.job_id = j.job_id
                JOIN companies c ON j.company_id = c.company_id
                WHERE a.application_id = %s
            """
            details = db_helper.fetch_one(details_query, (app_id,))
            if details:
                from email_helper import send_status_email
                send_status_email(
                    recipient_email=details['candidate_email'],
                    candidate_name=details['candidate_name'],
                    job_title=details['job_title'],
                    company_name=details['company_name'],
                    status=new_status
                )
    except Exception as e:
        flash("Failed to update status. Please try again.", "error")
        print(f"Status Update Error: {e}")
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Start the local development server
    app.run(debug=True, port=5001)
