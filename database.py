import pymysql

timeout = 10
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db="phicareers",
    host="mysql-phicareers-phicareers.a.aivencloud.com",
    password="AVNS__MjBOcYMMK0yhk0J52T",
    read_timeout=timeout,
    port=27509,
    user="avnadmin",
    write_timeout=timeout,
)

def load_jobs_from_db():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM jobs")  # Imports the jobs table
    jobs=[]
    for row in cursor.fetchall():
        jobs.append(row)
    return jobs

def load_job_from_db(uid):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = %s", (uid,))
    info= cursor.fetchone()
    return info

def add_application_to_db(job_id, data):
    cursor = connection.cursor()
    query = "INSERT INTO applications (job_id, full_name, email, linkedin_url, education, work_experience, resume_url) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = (job_id, data['full_name'], data['email'], data['linkedin_url'], data['education'], data['work_experience'], data['resume_url'])
    cursor.execute(query, values)
    connection.commit()