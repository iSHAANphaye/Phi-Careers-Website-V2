# Phi Careers

Phi Careers is a streamlined, responsive recruitment agency platform and job board. The application enables candidates to register, browse open jobs, track their applications (including saving drafts), and lets employers post listings, manage company profiles, and review/update candidate application statuses.

---

## 🚀 Key Features

*   **Role-Based Dashboards**: Separated dashboards and workflows tailored for both **Candidates** and **Employers**.
*   **Job Management**: Employers can publish job listings with salary validation limits and track all incoming applications.
*   **Interactive Application Pipeline**: Candidates can save applications as drafts or submit them with custom cover letters and resume links.
*   **Security & Auth Guards**: Clean session authentication utilizing security blueprints, parameterized SQL statements to prevent SQL injections, and bcrypt password hashing.
*   **MySQL Pool Database Helpers**: Custom, thread-safe connection pooling for clean, atomic query execution using `mysql-connector-python`.
*   **Docker Containerization**: Easily orchestrate the MySQL database service out-of-the-box.

---

## 🛠️ Tech Stack

*   **Backend Framework**: Python & Flask
*   **Database**: MySQL
*   **HTML Templates**: Jinja2 (using modern CSS styled in `style.css`)
*   **Containerization**: Docker & Docker Compose
*   **HTTP Server**: Gunicorn (for production environment)

---

## ⚙️ Project Structure

```
Phi Careers/
├── static/
│   └── css/style.css       # Platform-wide CSS stylesheet
├── templates/              # Jinja2 layout templates
│   ├── auth/               # Login and registration views
│   ├── candidate/          # Candidate application tracking dashboard
│   ├── employer/           # Employer job posting dashboard
│   ├── base.html           # Main shared wrapper layout
│   └── index.html          # Public landing page with featured jobs
├── testing/                # Automated QA suite
│   ├── qa_issue_matrix.md  # Tracked software bugs & QA statuses
│   ├── run_qa.py           # Core QA verification runner script
│   ├── test_app.py         # App endpoint unit tests
│   └── test_auth.py        # Authentication flow validation
├── app.py                  # Main Flask application entry point
├── auth.py                 # Authentication blueprint & route guards
├── db_helper.py            # MySQL pooled connection helper
├── schema.sql              # Database schema tables setup
├── seed.sql                # Mock database seed data script
├── docker-compose.yml      # MySQL docker database configuration
└── requirements.txt        # Python library dependencies
```

---

## 💻 Getting Started

### Prerequisites
*   [Python 3.8+](https://www.python.org/)
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (to run the MySQL database)

### Installation

1. Clone the repository and navigate to the directory:
   ```bash
   cd "Phi Careers"
   ```

2. Spin up the MySQL database container:
   ```bash
   docker compose up -d
   ```
   *(This starts the MySQL database on port `3307` and automatically executes `schema.sql` to initialize the database tables)*

3. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows (cmd/PowerShell):
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure Environment Variables:
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_flask_secret_session_key
   DB_HOST=127.0.0.1
   DB_PORT=3307
   DB_USER=root
   DB_PASSWORD=rootpassword
   DB_NAME=phi_careers
   ```

---

## 🏃 Running the Application

### 1. Seed Database (Optional)
To populate the MySQL database tables with mock jobs and initial users:
```bash
# Enter the mysql container or run manually against the container port:
mysql -h 127.0.0.1 -P 3307 -u root -p phi_careers < seed.sql
```

### 2. Start Flask Server
Run the local development server:
```bash
python app.py
```
*   **Web App URL**: [http://localhost:5001](http://localhost:5001)

### 3. Run Automated Tests & QA Suites
Ensure everything functions correctly:
```bash
python -m unittest testing/test_auth.py
python -m unittest testing/test_app.py
python testing/run_qa.py
```
