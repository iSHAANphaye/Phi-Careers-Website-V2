import subprocess
import time
import requests
import sys
import os

def verify_app_startup():
    print("--- Starting Flask Application Integration Tests ---")
    
    # Start app.py in a background process
    print("Launching Flask server subprocess...")
    process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd="d:/Antigravity dev/Phi Careers",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to start
    print("Waiting for server to bind to port 5001...")
    time.sleep(3)
    
    # Verify that the process is still running
    if process.poll() is not None:
        print("[ERROR] Flask server failed to start. Exit code:", process.poll())
        stdout, stderr = process.communicate()
        print("Stdout:\n", stdout)
        print("Stderr:\n", stderr)
        sys.exit(1)
        
    try:
        # 1. Test landing page at root
        print("Testing root URL landing page...")
        r_root = requests.get("http://localhost:5001/", allow_redirects=False)
        print(f"Root status: {r_root.status_code}")
        assert r_root.status_code == 200, f"Expected 200 OK, got {r_root.status_code}"
        assert "Your Next Career Milestone Starts Here" in r_root.text, "Landing page title missing"
        
        # 2. Test login page content
        print("Testing login page rendering...")
        r_login = requests.get("http://localhost:5001/auth/login")
        print(f"Login GET status: {r_login.status_code}")
        assert r_login.status_code == 200, f"Expected 200, got {r_login.status_code}"
        assert "Log In - Phi Careers" in r_login.text, "Login page title missing"
        assert 'name="email"' in r_login.text, "Email field missing"
        assert 'name="password"' in r_login.text, "Password field missing"
        print("[OK] Login page HTML rendered successfully.")
        
        # 3. Test register page content
        print("Testing registration page rendering...")
        r_register = requests.get("http://localhost:5001/auth/register")
        print(f"Register GET status: {r_register.status_code}")
        assert r_register.status_code == 200, f"Expected 200, got {r_register.status_code}"
        assert "Sign Up - Phi Careers" in r_register.text, "Register page title missing"
        assert 'name="role"' in r_register.text, "Role selector missing"
        print("[OK] Registration page HTML rendered successfully.")
        
        print("\n--- ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ---")
        
    except AssertionError as ae:
        print(f"\n[ERROR] Integration check failed: {ae}", file=sys.stderr)
        process.terminate()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Request error: {e}", file=sys.stderr)
        process.terminate()
        sys.exit(1)
        
    # Terminate the server process cleanly
    print("Stopping Flask server...")
    process.terminate()
    process.wait()
    print("Integration tests finished.")

if __name__ == "__main__":
    verify_app_startup()
