# cd "C:\Users\ishaan phaye\Desktop\VS Code\Web Dev Course\Phi-Careers-Website-V2"
# conda activate webd
# To run server, use command: flask --app app run --debug

from flask import Flask, render_template, jsonify
from database import load_jobs_from_db

app = Flask(__name__)

@app.route("/")
def hello_html():
    jobs=load_jobs_from_db()
    return render_template('home.html',jobs=jobs, company_name='Phi')

# Another way to add dynamic data using Json and API
@app.route("/api/jobs")
def list_jobs():
    jobs=load_jobs_from_db()
    return jsonify(jobs)