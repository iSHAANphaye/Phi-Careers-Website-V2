import sys
import os

# Add project path to sys.path to import modules
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from werkzeug.security import generate_password_hash, check_password_hash
import db_helper

def test_auth_logic():
    print("--- Starting Standalone Database Auth Verification ---")
    
    # 1. Test Password Hashing
    test_pwd = "SuperSecretPassword123!"
    print(f"Original Password: {test_pwd}")
    
    hashed = generate_password_hash(test_pwd)
    print(f"Hashed Password (Werkzeug): {hashed}")
    assert hashed != test_pwd, "Password was not hashed!"
    
    match = check_password_hash(hashed, test_pwd)
    print(f"Checking correct password: {match}")
    assert match is True, "Password match verification failed!"
    
    mismatch = check_password_hash(hashed, "WrongPassword!")
    print(f"Checking incorrect password: {mismatch}")
    assert mismatch is False, "Incorrect password passed verification!"
    print("[OK] Password hashing & validation verified successfully.")
    
    # 2. Test Parameterized Database Queries (SQL Injection Prevention)
    test_name = "Test Candidate"
    test_email = "test.candidate@phicareers.com"
    test_role = "candidate"
    
    # Clean up user if they already exist
    print("Cleaning up old test users...")
    db_helper.execute_query("DELETE FROM users WHERE email = %s", (test_email,))
    
    # Insert new user with parameterized query
    print("Inserting test user using parameterized query...")
    insert_query = """
        INSERT INTO users (name, email, password_hash, role) 
        VALUES (%s, %s, %s, %s)
    """
    last_id = db_helper.execute_query(insert_query, (test_name, test_email, hashed, test_role))
    print(f"User inserted successfully. Assigned ID: {last_id}")
    assert last_id > 0, "Insert execution failed!"
    
    # Retrieve user using parameterized query
    print("Fetching test user from database...")
    select_query = "SELECT * FROM users WHERE email = %s"
    user = db_helper.fetch_one(select_query, (test_email,))
    
    assert user is not None, "Failed to retrieve user from DB!"
    print(f"Retrieved User: ID={user['user_id']}, Name={user['name']}, Email={user['email']}, Role={user['role']}")
    
    # Verify password against hash from database
    db_match = check_password_hash(user['password_hash'], test_pwd)
    print(f"Verifying password against retrieved DB hash: {db_match}")
    assert db_match is True, "DB password check failed!"
    print("[OK] Parameterized DB insert, select, and hash matching verified successfully.")
    
    # Clean up test user
    print("Cleaning up test user from database...")
    db_helper.execute_query("DELETE FROM users WHERE user_id = %s", (user['user_id'],))
    
    user_check = db_helper.fetch_one("SELECT * FROM users WHERE email = %s", (test_email,))
    assert user_check is None, "Clean up failed!"
    print("[OK] Database cleanup complete.")
    
    print("\n--- ALL SECURITY TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    try:
        test_auth_logic()
    except AssertionError as ae:
        print(f"\n[ERROR] Assertion Failed: {ae}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error encountered: {e}", file=sys.stderr)
        sys.exit(1)
