import subprocess
import time
import requests
import sys
import os

def run_qa_suite():
    print("==================================================")
    print("       STARTING PHI CAREERS SYSTEM QA SUITE       ")
    print("==================================================")
    
    # 0. Clean up any existing QA test user from database
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        import db_helper
        db_helper.execute_query("DELETE FROM users WHERE email = %s", ("qa.test@phicareers.com",))
        print("[0/6] Cleaned up existing QA test user from database.")
    except Exception as e:
        print(f"[-] Warning: Database cleanup failed: {e}")

    # 1. Start the Flask server in a subprocess
    print("[1/6] Launching Flask server subprocess on port 5001...")
    process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd="d:/Antigravity dev/Phi Careers",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to initialize
    time.sleep(3)
    
    # Verify process started successfully
    if process.poll() is not None:
        print("[-] ERROR: Flask server failed to start.")
        stdout, stderr = process.communicate()
        print("Stderr:\n", stderr)
        sys.exit(1)
        
    session = requests.Session()
    
    try:
        # 2. Test boundary registration cases
        print("[2/6] Running boundary checks on user registration...")
        
        # Test Case A: Empty registration fields
        r_empty = session.post("http://localhost:5001/auth/register", data={
            "name": "", "email": "valid@email.com", "password": "pass", "role": "candidate"
        })
        assert "All fields are required" in r_empty.text, "Failed to reject empty name"
        print("  [OK] Successfully blocked empty input name.")
        
        # Test Case B: Invalid email formatting
        r_invalid_email = session.post("http://localhost:5001/auth/register", data={
            "name": "Jane", "email": "invalidemail.com", "password": "pass", "role": "candidate"
        })
        assert "Please provide a valid email address" in r_invalid_email.text, "Failed to reject invalid email formatting"
        print("  [OK] Successfully blocked invalid email formatting.")

        # 3. Test duplicate registration
        print("[3/6] Running duplicate email sign-up check...")
        
        # Seed user (first time should succeed or already exist)
        session.post("http://localhost:5001/auth/register", data={
            "name": "QA User", "email": "qa.test@phicareers.com", "password": "password123", "role": "candidate"
        })
        # Try registering same email again
        r_dup = session.post("http://localhost:5001/auth/register", data={
            "name": "QA User 2", "email": "qa.test@phicareers.com", "password": "password123", "role": "candidate"
        })
        assert "An account with that email already exists" in r_dup.text, "Failed to block duplicate email"
        print("  [OK] Successfully blocked duplicate email sign-ups.")

        # 4. Test authorization & login bounds
        print("[4/6] Running authentication verification...")
        
        # Test Case A: Invalid login credentials
        r_login_fail = session.post("http://localhost:5001/auth/login", data={
            "email": "qa.test@phicareers.com", "password": "wrongpassword"
        })
        assert "Invalid email or password" in r_login_fail.text, "Failed to reject wrong password"
        print("  [OK] Successfully rejected invalid password during login.")

        # Test Case B: Successful login
        r_login_ok = session.post("http://localhost:5001/auth/login", data={
            "email": "qa.test@phicareers.com", "password": "password123"
        }, allow_redirects=True)
        assert "QA User" in r_login_ok.text, "Failed to log in with correct credentials"
        print("  [OK] Logged in successfully with valid credentials.")

        # 5. Log out and log in as employer to test job creation validation
        print("[5/6] Logging in as Employer to test job posting boundaries...")
        
        session.get("http://localhost:5001/auth/logout") # Log out candidate
        
        # Log in as Alice (seeded employer)
        r_emp_login = session.post("http://localhost:5001/auth/login", data={
            "email": "alice@employer.com", "password": "password123"
        }, allow_redirects=True)
        assert "Alice Johnson" in r_emp_login.text, "Employer login failed"
        
        # Test Case: Post job with negative salary
        r_neg_salary = session.post("http://localhost:5001/jobs/create", data={
            "title": "Minus Salary Engineer", "location": "Remote", "salary": "-1000", "description": "Negative pay role."
        }, allow_redirects=True)
        assert "Salary must be a positive number" in r_neg_salary.text, "Failed to block negative salary"
        print("  [OK] Successfully blocked negative salary job postings.")

        # 6. Test SQL injection sanitization (Penetration check)
        print("[6/6] Running SQL injection sanitization verification...")
        session.get("http://localhost:5001/auth/logout") # Log out employer to hit login page
        r_sql_inj = session.post("http://localhost:5001/auth/login", data={
            "email": "' OR '1'='1", "password": "password"
        })
        assert "Invalid email or password" in r_sql_inj.text, "SQL injection check failed"
        print("  [OK] Successfully sanitized SQL injection payload.")
        
        print("\n==================================================")
        print("       ALL SYSTEM QA TESTS PASSED SUCCESSFULLY!   ")
        print("==================================================")
        
    except AssertionError as ae:
        print(f"\n[-] QA TEST FAILURE: {ae}", file=sys.stderr)
        process.terminate()
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] QA RUN ERROR: {e}", file=sys.stderr)
        process.terminate()
        sys.exit(1)
        
    # Clean up and stop server
    print("Shutting down Flask test server...")
    process.terminate()
    process.wait()
    print("QA suite completed.")

if __name__ == "__main__":
    run_qa_suite()
