import subprocess
import time
import requests
import sys
import os

def run_qa_suite():
    print("==================================================")
    print("       STARTING PHI CAREERS SYSTEM QA SUITE       ")
    print("==================================================")
    
    # 0. Reset database by running seed.sql
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        import db_helper
        
        # Read and execute seed.sql to reset DB state completely
        seed_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'seed.sql')
        with open(seed_path, 'r', encoding='utf-8') as f:
            seed_sql = f.read()
            
        # Strip comments line-by-line first to prevent skipping queries
        lines = seed_sql.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('--'):
                clean_lines.append(line)
        clean_sql = '\n'.join(clean_lines)
        
        # Split queries by semicolon and execute
        queries = clean_sql.split(';')
        for query in queries:
            clean_query = query.strip()
            if clean_query:
                db_helper.execute_query(clean_query)
        print("[0] Reset database using seed.sql successfully.")
    except Exception as e:
        print(f"[-] Warning: Database reset/seeding failed: {e}")

    # 1. Start the Flask server in a subprocess
    print("[1] Launching Flask server subprocess on port 5001...")
    log_file = open("testing/server.log", "w")
    process = subprocess.Popen(
        [sys.executable, "-u", "app.py"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        stdout=log_file,
        stderr=log_file
    )
    
    # Wait for the server to initialize (up to 15 seconds)
    print("Waiting for Flask server to bind to port 5001...")
    server_started = False
    for i in range(15):
        if process.poll() is not None:
            break
        try:
            requests.get("http://localhost:5001/auth/login", timeout=1)
            server_started = True
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            time.sleep(1)
            
    # Verify process started successfully
    if not server_started or process.poll() is not None:
        print("[-] ERROR: Flask server failed to start or bind to port 5001.")
        log_file.close()
        with open("testing/server.log", "r") as f:
            print("Server Logs:\n", f.read())
        sys.exit(1)
        
    session = requests.Session()
    
    try:
        # 2. Test boundary registration cases
        print("[2] Running user registration boundary checks...")
        
        # Test Case A: Empty registration fields (BUG-02)
        r_empty = session.post("http://localhost:5001/auth/register", data={
            "name": "", "email": "valid@email.com", "password": "pass", "confirm_password": "pass", "role": "candidate"
        })
        assert "All fields are required" in r_empty.text, "Failed to reject empty name"
        print("  [OK] Blocked empty input name.")
        
        # Test Case B: Invalid email formatting (BUG-02)
        r_invalid_email = session.post("http://localhost:5001/auth/register", data={
            "name": "Jane", "email": "invalidemail.com", "password": "password123", "confirm_password": "password123", "role": "candidate"
        })
        assert "Please provide a valid email address" in r_invalid_email.text, "Failed to reject invalid email formatting"
        print("  [OK] Blocked invalid email formatting.")

        # Test Case C: Password too short (BUG-13)
        r_short_pw = session.post("http://localhost:5001/auth/register", data={
            "name": "Jane", "email": "jane@email.com", "password": "123", "confirm_password": "123", "role": "candidate"
        })
        assert "Password must be at least 6 characters long" in r_short_pw.text, "Failed to reject short password"
        print("  [OK] Blocked short password (< 6 chars).")

        # Test Case D: Passwords mismatch (BUG-15)
        r_mismatch_pw = session.post("http://localhost:5001/auth/register", data={
            "name": "Jane", "email": "jane@email.com", "password": "password123", "confirm_password": "mismatch123", "role": "candidate"
        })
        assert "Passwords do not match" in r_mismatch_pw.text, "Failed to reject password mismatch"
        print("  [OK] Blocked password mismatch.")

        # Test Case E: Name too long (BUG-14)
        long_name = "A" * 105
        r_long_name = session.post("http://localhost:5001/auth/register", data={
            "name": long_name, "email": "jane@email.com", "password": "password123", "confirm_password": "password123", "role": "candidate"
        })
        assert "Name must be 100 characters or less" in r_long_name.text, "Failed to reject name too long"
        print("  [OK] Blocked name exceeding 100 characters limit.")

        # Test Case F: Email too long (BUG-14)
        long_email = "A" * 100 + "@email.com"
        r_long_email = session.post("http://localhost:5001/auth/register", data={
            "name": "Jane", "email": long_email, "password": "password123", "confirm_password": "password123", "role": "candidate"
        })
        assert "Email must be 100 characters or less" in r_long_email.text, "Failed to reject email too long"
        print("  [OK] Blocked email exceeding 100 characters limit.")

        # 3. Test successful registration and duplicate email check
        print("[3] Running duplicate email sign-up checks...")
        
        # Valid candidate registration
        r_reg_ok = session.post("http://localhost:5001/auth/register", data={
            "name": "QA User", "email": "qa.test@phicareers.com", "password": "password123", "confirm_password": "password123", "role": "candidate"
        }, allow_redirects=True)
        if "Registration successful!" not in r_reg_ok.text:
            print("--- REGISTRATION FAILED ---")
            print("Response URL:", r_reg_ok.url)
            print("Response text length:", len(r_reg_ok.text))
            import re
            flashes = re.findall(r'<li class="alert alert-[^"]+">\s*(.*?)\s*</li>', r_reg_ok.text, re.DOTALL)
            print("Flashes found:", flashes)
            assert False, "Failed valid candidate registration"
        print("  [OK] Registered candidate successfully.")
        
        # Try registering same email again
        r_dup = session.post("http://localhost:5001/auth/register", data={
            "name": "QA User 2", "email": "qa.test@phicareers.com", "password": "password123", "confirm_password": "password123", "role": "candidate"
        })
        assert "An account with that email already exists" in r_dup.text, "Failed to block duplicate email"
        print("  [OK] Blocked duplicate email sign-ups.")

        # Test Case: Employer registration missing company name
        r_emp_fail = session.post("http://localhost:5001/auth/register", data={
            "name": "QA Employer", "email": "qa.employer@phicareers.com", "password": "password123", "confirm_password": "password123", "role": "employer",
            "company_name": ""
        })
        assert "Company name is required for employers." in r_emp_fail.text, "Failed to block empty company name for employer"
        print("  [OK] Blocked employer registration with empty company name.")

        # Test Case: Successful employer registration with company name
        r_emp_ok = session.post("http://localhost:5001/auth/register", data={
            "name": "QA Employer", "email": "qa.employer@phicareers.com", "password": "password123", "confirm_password": "password123", "role": "employer",
            "company_name": "QA Testing Enterprise"
        }, allow_redirects=True)
        assert "Registration successful!" in r_emp_ok.text, "Failed valid employer registration"
        print("  [OK] Registered employer with company successfully.")

        # 4. Test authentication & login bounds
        print("[4] Running authentication and session verification...")
        
        # Test Case A: Invalid login credentials
        r_login_fail = session.post("http://localhost:5001/auth/login", data={
            "email": "qa.test@phicareers.com", "password": "wrongpassword"
        })
        assert "Invalid email or password" in r_login_fail.text, "Failed to reject wrong password"
        print("  [OK] Rejected invalid login credentials.")

        # Test Case B: Successful login
        r_login_ok = session.post("http://localhost:5001/auth/login", data={
            "email": "qa.test@phicareers.com", "password": "password123"
        }, allow_redirects=True)
        assert "QA User" in r_login_ok.text, "Failed to log in with correct credentials"
        print("  [OK] Authenticated valid login session.")

        # 5. Candidate Apply & Save-Draft boundaries
        print("[5] Running candidate application and state machine boundary checks...")

        # Test Case A: Apply to a non-existent job ID (BUG-05)
        r_nonexist_job = session.post("http://localhost:5001/jobs/9999/apply", data={
            "cover_letter": "I want this non-existent job.", "resume_url": "http://drive.com/resume.pdf"
        }, allow_redirects=True)
        assert "Job listing not found." in r_nonexist_job.text, "Failed to block apply to non-existent job"
        print("  [OK] Blocked candidate applying to non-existent job listing.")

        # Test Case B: Apply to a closed job listing (BUG-06)
        # Close job ID 1 in the database
        db_helper.execute_query("UPDATE job_listings SET status = 'closed' WHERE job_id = 1")
        r_closed_job = session.post("http://localhost:5001/jobs/1/apply", data={
            "cover_letter": "I want this closed job.", "resume_url": "http://drive.com/resume.pdf"
        }, allow_redirects=True)
        assert "This job listing is closed and no longer accepting applications." in r_closed_job.text, "Failed to block apply to closed job"
        print("  [OK] Blocked candidate applying to closed job listing.")
        
        # Re-open job ID 1
        db_helper.execute_query("UPDATE job_listings SET status = 'open' WHERE job_id = 1")

        # Test Case C: Save a valid draft
        r_draft = session.post("http://localhost:5001/jobs/1/save-draft", data={
            "cover_letter": "This is a draft letter.", "resume_url": "http://drive.com/resume.pdf"
        }, allow_redirects=True)
        assert "Application draft saved successfully." in r_draft.text, "Failed to save valid draft"
        print("  [OK] Candidate saved application draft successfully.")

        # Test Case D: Submit the application
        r_submit = session.post("http://localhost:5001/jobs/1/apply", data={
            "cover_letter": "This is a submitted letter.", "resume_url": "http://drive.com/resume.pdf"
        }, allow_redirects=True)
        assert "Application submitted successfully!" in r_submit.text, "Failed to submit application"
        print("  [OK] Candidate submitted application successfully.")

        # Test Case E: Demote submitted application back to draft (BUG-08)
        r_demote_draft = session.post("http://localhost:5001/jobs/1/save-draft", data={
            "cover_letter": "Trying to demote.", "resume_url": "http://drive.com/resume.pdf"
        }, allow_redirects=True)
        assert "You cannot save a draft for a submitted application." in r_demote_draft.text, "Failed to block draft demotion"
        print("  [OK] Blocked demoting submitted application to draft.")

        # Test Case F: Overwrite submitted status back to applied (BUG-07)
        r_overwrite_app = session.post("http://localhost:5001/jobs/1/apply", data={
            "cover_letter": "Trying to overwrite.", "resume_url": "http://drive.com/resume.pdf"
        }, allow_redirects=True)
        assert "You have already submitted an application for this job." in r_overwrite_app.text, "Failed to block application overwrite"
        print("  [OK] Blocked overwriting existing active application.")

        # 6. Log out and log in as employer to test job creation validation & status changes
        print("[6] Logging in as Employer to test job creation boundaries & status transitions...")
        session.get("http://localhost:5001/auth/logout") # Log out candidate
        
        # Log in as Alice (seeded employer)
        r_emp_login = session.post("http://localhost:5001/auth/login", data={
            "email": "alice@employer.com", "password": "password123"
        }, allow_redirects=True)
        assert "Alice Johnson" in r_emp_login.text, "Employer login failed"
        print("  [OK] Authenticated employer session successfully.")

        # Test Case A: Post job with negative salary (BUG-03)
        r_neg_salary = session.post("http://localhost:5001/jobs/create", data={
            "title": "Minus Salary Engineer", "location": "Remote", "salary": "-1000", "description": "Negative pay role."
        }, allow_redirects=True)
        assert "Salary must be a positive number." in r_neg_salary.text, "Failed to block negative salary"
        print("  [OK] Blocked job listings with negative salaries.")

        # Test Case B: Post job with overflow salary (BUG-11)
        r_overflow_salary = session.post("http://localhost:5001/jobs/create", data={
            "title": "Mega Salary PM", "location": "Remote", "salary": "100000000", "description": "100M pay role."
        }, allow_redirects=True)
        assert "Salary must be less than 100,000,000." in r_overflow_salary.text, "Failed to block overflow salary"
        print("  [OK] Blocked job listings with overflow salaries (>= 100M).")

        # Test Case C: Post job with excessively long title (BUG-16)
        long_title = "A" * 105
        r_long_title = session.post("http://localhost:5001/jobs/create", data={
            "title": long_title, "location": "Remote", "salary": "120000", "description": "Standard desc."
        }, allow_redirects=True)
        assert "Title must be 100 characters or less." in r_long_title.text, "Failed to block excessively long title"
        print("  [OK] Blocked job listings with titles exceeding 100 characters.")

        # Test Case D: Employer updating status of a candidate draft (BUG-09)
        # John Smith has application ID 2 in draft state
        r_update_draft = session.post("http://localhost:5001/applications/2/status", data={
            "status": "reviewed"
        }, allow_redirects=True)
        assert "Cannot update status of a draft application." in r_update_draft.text, "Failed to block employer updating draft"
        print("  [OK] Blocked employer from modifying candidate drafts.")

        # Test Case E: Employer updates application 1 status to 'hired' and checks for candidate email
        print("  Testing employer hiring candidate and sending email...")
        
        # Clear mock_emails directory before testing to make verification clean
        import shutil
        mock_emails_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mock_emails')
        if os.path.exists(mock_emails_dir):
            shutil.rmtree(mock_emails_dir)
            
        r_update_hired = session.post("http://localhost:5001/applications/1/status", data={
            "status": "hired"
        }, allow_redirects=True)
        assert "Candidate application status updated to &#39;hired&#39;." in r_update_hired.text, "Failed to update status to hired"
        
        # Verify db status reflects hired
        hired_app = db_helper.fetch_one("SELECT status FROM applications WHERE application_id = 1")
        assert hired_app['status'] == 'hired', "Application status in database is not 'hired'"
        
        # Verify mock email file exists and content is correct
        assert os.path.exists(mock_emails_dir), "mock_emails directory not created"
        email_files = os.listdir(mock_emails_dir)
        assert len(email_files) > 0, "No mock email files generated"
        
        hired_email_file = None
        for f in email_files:
            if 'hired' in f and 'jane_candidate_com' in f:
                hired_email_file = f
                break
        assert hired_email_file is not None, "Jane candidate hired email file not found"
        
        with open(os.path.join(mock_emails_dir, hired_email_file), 'r', encoding='utf-8') as f:
            email_content = f.read()
            assert "To: jane@candidate.com" in email_content, "Recipient email mismatch"
            assert "Congratulations!" in email_content, "Email subject/body missing 'Congratulations!'"
            assert "hired" in email_content, "Email content missing 'hired'"
            assert "Backend Software Engineer" in email_content, "Email content missing job title"
            assert "Stripe" in email_content, "Email content missing company name"
        print("  [OK] Successfully hired candidate and verified email notification.")

        # Test Case F: Employer updates application 3 status to 'rejected' and checks for candidate email
        print("  Testing employer rejecting candidate and sending email...")
        r_update_rejected = session.post("http://localhost:5001/applications/3/status", data={
            "status": "rejected"
        }, allow_redirects=True)
        assert "Candidate application status updated to &#39;rejected&#39;." in r_update_rejected.text, "Failed to update status to rejected"
        
        # Verify db status reflects rejected
        rejected_app = db_helper.fetch_one("SELECT status FROM applications WHERE application_id = 3")
        assert rejected_app['status'] == 'rejected', "Application status in database is not 'rejected'"
        
        email_files = os.listdir(mock_emails_dir)
        rejected_email_file = None
        for f in email_files:
            if 'rejected' in f and 'jane_candidate_com' in f:
                rejected_email_file = f
                break
        assert rejected_email_file is not None, "Jane candidate rejected email file not found"
        
        with open(os.path.join(mock_emails_dir, rejected_email_file), 'r', encoding='utf-8') as f:
            email_content = f.read()
            assert "To: jane@candidate.com" in email_content, "Recipient email mismatch"
            assert "decided to move forward with other candidates" in email_content, "Email body missing standard rejection text"
            assert "Cloud Product Manager" in email_content, "Email content missing job title"
            assert "Microsoft" in email_content, "Email content missing company name"
        print("  [OK] Successfully rejected candidate and verified email notification.")

        # Test Case G: Job Update & Delete validations
        print("  Running job update & delete validation and security checks...")
        
        # 1. Unauthorized Job Update
        # Alice tries to update Bob's job (job_id 3)
        r_unauth_update = session.post("http://localhost:5001/jobs/3/update", data={
            "title": "Hacked Title", "location": "Remote", "salary": "120000", "description": "Hacked desc", "status": "open"
        }, allow_redirects=True)
        assert "Job listing not found or unauthorized." in r_unauth_update.text, "Failed to block unauthorized job update"
        
        # Verify job 3 was not updated
        job3 = db_helper.fetch_one("SELECT title FROM job_listings WHERE job_id = 3")
        assert job3['title'] != "Hacked Title", "Unauthorized job update succeeded!"
        print("    [OK] Blocked unauthorized job update.")
        
        # 2. Boundary check: Negative Salary
        r_neg_sal = session.post("http://localhost:5001/jobs/1/update", data={
            "title": "New Title", "location": "Remote", "salary": "-500", "description": "Desc", "status": "open"
        }, allow_redirects=True)
        assert "Salary must be a positive number." in r_neg_sal.text, "Failed to block negative salary on update"
        
        # 3. Boundary check: Overflow Salary
        r_over_sal = session.post("http://localhost:5001/jobs/1/update", data={
            "title": "New Title", "location": "Remote", "salary": "100000000", "description": "Desc", "status": "open"
        }, allow_redirects=True)
        assert "Salary must be less than 100,000,000." in r_over_sal.text, "Failed to block overflow salary on update"
        print("    [OK] Blocked invalid salary values on update.")
        
        # 4. Successful Job Update
        r_valid_update = session.post("http://localhost:5001/jobs/1/update", data={
            "title": "Updated Backend Engineer", 
            "location": "Chicago, IL", 
            "salary": "140000", 
            "description": "Updated description text.", 
            "status": "closed"
        }, allow_redirects=True)
        assert "Job listing updated successfully!" in r_valid_update.text, "Failed to update job listing with valid data"
        
        # Verify changes in DB
        job1 = db_helper.fetch_one("SELECT * FROM job_listings WHERE job_id = 1")
        assert job1['title'] == "Updated Backend Engineer", "Title not updated in DB"
        assert job1['location'] == "Chicago, IL", "Location not updated in DB"
        assert float(job1['salary']) == 140000.0, "Salary not updated in DB"
        assert job1['description'] == "Updated description text.", "Description not updated in DB"
        assert job1['status'] == "closed", "Status not updated in DB"
        print("    [OK] Successfully updated own job listing and verified DB changes.")
        
        # 5. Unauthorized Job Delete
        # Alice tries to delete Bob's job (job_id 3)
        r_unauth_delete = session.post("http://localhost:5001/jobs/3/delete", allow_redirects=True)
        assert "Job listing not found or unauthorized." in r_unauth_delete.text, "Failed to block unauthorized job deletion"
        
        # Verify job 3 still exists
        job3_check = db_helper.fetch_one("SELECT * FROM job_listings WHERE job_id = 3")
        assert job3_check is not None, "Unauthorized job deletion succeeded!"
        print("    [OK] Blocked unauthorized job deletion.")
        
        # 6. Successful Job Delete
        # First verify Application 1 exists for job 1
        app1_pre = db_helper.fetch_one("SELECT * FROM applications WHERE application_id = 1")
        assert app1_pre is not None, "Application 1 should exist before job deletion"
        
        # Delete job 1
        r_valid_delete = session.post("http://localhost:5001/jobs/1/delete", allow_redirects=True)
        assert "Job listing deleted successfully!" in r_valid_delete.text, "Failed to delete job listing"
        
        # Verify job 1 is deleted from DB
        job1_check = db_helper.fetch_one("SELECT * FROM job_listings WHERE job_id = 1")
        assert job1_check is None, "Job 1 still exists in database!"
        
        # Verify cascade deletion of Application 1
        app1_post = db_helper.fetch_one("SELECT * FROM applications WHERE application_id = 1")
        assert app1_post is None, "Application 1 was not cascadingly deleted!"
        print("    [OK] Successfully deleted own job listing and verified cascade deletion of applications.")

        # 7. Test SQL injection sanitization (Penetration check)
        print("[7] Running SQL injection sanitization verification...")
        session.get("http://localhost:5001/auth/logout") # Log out employer to hit login page
        r_sql_inj = session.post("http://localhost:5001/auth/login", data={
            "email": "' OR '1'='1", "password": "password"
        })
        assert "Invalid email or password" in r_sql_inj.text, "SQL injection check failed"
        print("  [OK] Sanitized SQL injection payload successfully.")
        
        print("\n==================================================")
        print("       ALL SYSTEM QA TESTS PASSED SUCCESSFULLY!   ")
        print("==================================================")
        
    except AssertionError as ae:
        print(f"\n[-] QA TEST FAILURE: {ae}", file=sys.stderr)
        process.terminate()
        try:
            log_file.close()
        except:
            pass
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] QA RUN ERROR: {e}", file=sys.stderr)
        process.terminate()
        try:
            log_file.close()
        except:
            pass
        sys.exit(1)
        
    # Clean up and stop server
    print("Shutting down Flask test server...")
    process.terminate()
    process.wait()
    try:
        log_file.close()
    except:
        pass
    print("QA suite completed.")

if __name__ == "__main__":
    run_qa_suite()
