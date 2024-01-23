# cd "C:\Users\ishaan phaye\Desktop\VS Code\Web Dev Course\Python-Flask-Backend"
# conda activate webd
# To run server, use command: flask --app app run --debug

from flask import Flask, render_template, jsonify

app = Flask(__name__)

JOBS = [
{
    'id': 1,
    'title': 'Data Analyst',
    'location': 'Bengaluru, India',
    'salary': 'Rs. 11,00,000'
},
{
    'id': 2,
    'title': 'Data Scientist',
    'location': 'Pune, India',
    'salary': 'Rs. 27,00,000'
},
{
    'id': 3,
    'title': 'Frontend Engineer',
    'location': 'Remote',
    # 'salary': 'Rs. 12,00,000'
},
{
    'id': 4,
    'title': 'Backend Engineer',
    'location': 'San Francisco, USA',
    'salary': '$120,000'
},
{
    'id': 5,
    'title': 'ML Engineer',
    'location': 'New York, USA',
    'salary': '$150,000'
}
]

@app.route("/")
def hello_html():
    return render_template('home.html',jobs=JOBS, company_name='Phi')

# Another way to add dynamic data using Json and API
@app.route("/api/jobs")
def list_jobs():
    return jsonify(JOBS)