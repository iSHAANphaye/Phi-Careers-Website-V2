# QA Test Cases & Bug Log

Hey, here's the list of test cases I mapped out for the QA evaluation, along with the bugs I caught and patched in the codebase.

## 1. Test Flows & Boundaries

### E2E Happy Paths
*   **Candidate Portal**: Signup -> Login -> Check landing page -> Apply modal (pre-fills details) -> Save draft -> Submit app -> Track in pipeline.
*   **Employer Portal**: Signup -> Login -> Post new job -> View active listings -> Review candidate applications and change statuses.

### Edge cases & boundaries I checked:
*   Form fields left empty on registration/login.
*   Malformed emails (missing @, invalid domain extensions).
*   Insecure passwords (too short or just spaces).
*   Duplicate signups.
*   Salary bounds (negative numbers, or crazy high values like 100M+).
*   SQL injection attempts in the login form.
*   Broken workflows (like candidates trying to downgrade active apps to drafts, or employers trying to touch drafts).
*   UI breaks when descriptions/cover letters contain quotes or newlines.

---

## 2. Bugs Found & Patched

Here is the tracker of the 16 bugs I resolved during the QA cycle:

| Bug ID | Description | Severity | File | Status | What I fixed |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **BUG-01** | Employer dashboard shows draft applications. | High | `app.py` | Fixed | Added `WHERE a.status != 'draft'` filter to applicant query. |
| **BUG-02** | Registration allows invalid email addresses. | Medium | `auth.py` | Fixed | Added regex format checking on signup. |
| **BUG-03** | Salary input accepts negative values. | Low | `app.py` | Fixed | Added validation to block values < 0. |
| **BUG-04** | Port conflict on port 5000 with vaatika backend. | Medium | `app.py` | Fixed | Shifted Flask app to listen on port 5001. |
| **BUG-05** | Candidate can apply to a non-existent job ID. | High | `app.py` | Fixed | Checked job existence in DB before allowing submission. |
| **BUG-06** | Candidate can apply to closed job listings. | High | `app.py` | Fixed | Blocked applying if job status is not 'open'. |
| **BUG-07** | Candidate can overwrite rejected/hired status back to applied. | High | `app.py` | Fixed | Added status check; block updates if status is not 'draft'. |
| **BUG-08** | Candidate can demote a submitted application back to draft. | High | `app.py` | Fixed | Added status check to save-draft route to block demoting. |
| **BUG-09** | Employer can update status of draft applications. | Medium | `app.py` | Fixed | Added check in status update route to reject drafts. |
| **BUG-10** | Description single quotes break JS onclick handler on dashboard. | Medium | `dashboard.html` | Fixed | Switched job card click handler to use HTML5 data attributes. |
| **BUG-11** | Salaries >= 100M crash database DECIMAL(10,2) column. | Low | `app.py` | Fixed | Enforced upper limit of < 100,000,000 on salary input. |
| **BUG-12** | Quotes in cover letters break employer dashboard alert onclick. | Medium | `dashboard.html` | Fixed | Rendered cover letter inside hidden div; fetched via DOM. |
| **BUG-13** | Sign-up allows short (< 6 chars) or whitespace-only passwords. | Medium | `auth.py` | Fixed | Added length check and password whitespace stripping. |
| **BUG-14** | Extremely long Name/Email (over 100 chars) crash database. | Low | `auth.py` | Fixed | Enforced max length limits (<= 100 characters) on inputs. |
| **BUG-15** | Missing password confirmation on register page. | Medium | `register.html` | Fixed | Added confirm_password field and matching check in backend. |
| **BUG-16** | Job title/location exceeding VARCHAR length limits crash DB. | Low | `app.py` | Fixed | Added length limits to title (<=100) and location (<=100). |
