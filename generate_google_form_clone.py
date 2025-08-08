import os

project_structure = {
"instruction.txt": """# Setup Instructions

1. Create a virtual environment:
   python -m venv venv

2. Activate the virtual environment:
   venv\\Scripts\\activate   (on Windows)
   source venv/bin/activate   (on macOS/Linux)

3. Install requirements
pip install -r requirements.txt

4. Run app
python app.py
""",

"sample_questions.csv": """What is your name?,text
How old are you?,number
Do you like Python?,radio""",

    ".gitignore": """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# SQLite database
*.db

# Flask uploads
uploads/

# Environment files
.env

# OS files
.DS_Store
Thumbs.db
""",
    "requirements.txt": """
Flask==2.3.3
""",
    "app.py": """
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import csv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DB_NAME = 'questions.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                type TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                answers TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')

@app.route('/', methods=['GET', 'POST'])
def form():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT id, question, type FROM questions')
        questions = c.fetchall()

    if request.method == 'POST':
        answers = {}
        for q in questions:
            qid, question, qtype = q
            answer = request.form.get(f'q_{qid}', '')
            answers[question] = answer

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            timestamp = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
            c.execute('INSERT INTO responses (answers, timestamp) VALUES (?, ?)', (str(answers), timestamp))
            conn.commit()
        return render_template('success.html')

    return render_template('form.html', questions=questions)

@app.route('/admin', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['csv_file']
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            with sqlite3.connect(DB_NAME) as conn:
                c = conn.cursor()
                c.execute('DELETE FROM questions')
                with open(filepath, newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if len(row) >= 2:
                            question, qtype = row
                            c.execute('INSERT INTO questions (question, type) VALUES (?, ?)', (question, qtype))
                conn.commit()
            return redirect(url_for('form'))
    return render_template('index.html')

@app.route('/results')
def results():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT id, answers, timestamp FROM responses ORDER BY id DESC')
        responses = c.fetchall()
    return render_template('results.html', responses=responses)

@app.route('/export_csv')
def export_csv():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT answers, timestamp FROM responses ORDER BY id')
        data = c.fetchall()

    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'responses_export.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Answers', 'Timestamp'])
        for row in data:
            writer.writerow(row)

    return send_file(csv_path, as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

""",
    "templates": {
        "index.html": """
<!-- templates/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Upload</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <h1>Upload CSV File</h1>
    <form action="/admin" method="POST" enctype="multipart/form-data">
        <input type="file" name="csv_file" required>
        <button type="submit">Upload</button>
    </form>
    <p><a href="{{ url_for('form') }}">Go to Form</a> | <a href="{{ url_for('results') }}">View Results</a></p>
</body>
</html>
""",
"results.html": """<!-- templates/results.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Results</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <style>
        table {
            border-collapse: collapse;
            width: 90%;
            margin: 20px auto;
        }
        th, td {
            border: 1px solid #999;
            padding: 10px;
            text-align: left;
            vertical-align: top;
            white-space: pre-wrap;
            font-family: monospace;
        }
        th {
            background-color: #eee;
        }
        .container {
            text-align: center;
            margin: 20px;
        }
    </style>
</head>
<body>
    <h1 style="text-align:center;">All Responses</h1>
    <div class="container">
        <a href="{{ url_for('export_csv') }}"><button>Export to CSV</button></a>
        <p><a href="{{ url_for('form') }}">Back to Form</a> | <a href="{{ url_for('index') }}">Admin Upload</a></p>
    </div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Answers</th>
                <th>Timestamp (UTC)</th>
            </tr>
        </thead>
        <tbody>
            {% for r in responses %}
            <tr>
                <td>{{ r[0] }}</td>
                <td>{{ r[1] }}</td>
                <td>{{ r[2] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
""",

        "form.html": """
<!-- templates/form.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Form</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <h1>Please Fill the Form</h1>
    <form method="POST">
        {% for q in questions %}
            <div class="form-group">
                <label>{{ q[1] }}</label>
                {% if q[2] == 'text' %}
                    <input type="text" name="q_{{ q[0] }}" required>
                {% elif q[2] == 'number' %}
                    <input type="number" name="q_{{ q[0] }}" required>
                {% elif q[2] == 'radio' %}
                    <input type="radio" name="q_{{ q[0] }}" value="Yes" required> Yes
                    <input type="radio" name="q_{{ q[0] }}" value="No"> No
                {% else %}
                    <input type="text" name="q_{{ q[0] }}">
                {% endif %}
            </div>
        {% endfor %}
        <button type="submit">Submit</button>
    </form>
    <p><a href="{{ url_for('index') }}">Admin Upload</a> | <a href="{{ url_for('results') }}">View Results</a></p>
</body>
</html>""",
        "success.html": """<!-- templates/success.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Success</title>
</head>
<body>
    <h1>Thanks for submitting the form!</h1>
    <a href="{{ url_for('form') }}">Submit Again</a> | <a href="{{ url_for('results') }}">View Results</a>
</body>
</html>"""
    },
    "static": {
        "style.css": """body {
    font-family: Arial, sans-serif;
    margin: 40px;
    padding: 0;
    background: #f2f2f2;
}

h1 {
    color: #333;
}

.form-group {
    margin-bottom: 15px;
}

input[type="text"],
input[type="number"] {
    padding: 8px;
    width: 300px;
}

button {
    padding: 10px 20px;
    background-color: #0066cc;
    color: white;
    border: none;
    cursor: pointer;
}"""
    },
    "uploads": {}
}


def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n')  # Add trailing newline

if __name__ == '__main__':
    print("Creating Google Forms clone project structure...")
    create_structure('.', project_structure)
    print("✅ Done! Navigate to your project directory and run 'python app.py'")
