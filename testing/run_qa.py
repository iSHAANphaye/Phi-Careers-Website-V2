import subprocess
import time
import requests
import sys
import os

def run_qa_suite():
    print("==================================================")
    print("       STARTING PHI CAREERS SYSTEM QA SUITE       ")
    print("==================================================")
    
    # 0. Clean up any existing QA test user & applications from database
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        import db_helper
        db_helper.execute_query("DELETE FROM users WHERE email = %s", ("qa.test@phicareers.com",))
        db_helper.execute_query("DELETE FROM applications WHERE user_id = 7 or job_id = 9999")
        # Ensure job ID 1 is open
        db_helper.execute_query("UPDATE job_listings SET status = 'open' WHERE job_id = 1")
        print("[0] Cleaned up database test records successfully.")
    except Exception as e:
        print(f"[-] Warning: Database cleanup failed: {e}")

    # 1. Start the Flask server in a subprocess
    print("[1] Launching Flask server subprocess on port 5001...")
    log_file = open("testing/server.log", "w")
    process = subprocess.Popen(
        [sys.executable, "-u", "app.py"],
        cwd="d:/Antigravity dev/Phi Careers",
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
