import os
import json
import csv
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file

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
                answers TEXT NOT NULL,  -- stored as JSON string
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
            c.execute(
                'INSERT INTO responses (answers, timestamp) VALUES (?, ?)',
                (json.dumps(answers), timestamp)
            )
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
        rows = c.fetchall()

    groups = {}  # keys: frozenset of columns, values: list of responses in that group
    for row in rows:
        rid, raw_answers, timestamp = row
        answers = json.loads(raw_answers)
        columns = frozenset(answers.keys())
        if columns not in groups:
            groups[columns] = []
        groups[columns].append({
            "id": rid,
            "timestamp": timestamp,
            "answers": answers
        })

    # Sort groups by number of responses or creation order (optional)
    # Here just convert to list of tuples for template:
    grouped_responses = []
    for cols, resps in groups.items():
        # Sort responses by id ascending
        sorted_resps = sorted(resps, key=lambda r: r['id'])
        grouped_responses.append({
            "columns": sorted(cols),
            "responses": sorted_resps
        })

    # Sort groups by number of responses descending (optional)
    grouped_responses.sort(key=lambda g: len(g['responses']), reverse=True)

    return render_template('results.html', grouped_responses=grouped_responses)

@app.route('/export_csv')
def export_csv():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT answers, timestamp FROM responses ORDER BY id')
        rows = c.fetchall()

    # Collect all headers
    all_rows = []
    all_keys = set()
    for raw_answers, timestamp in rows:
        answers = json.loads(raw_answers)
        all_keys.update(answers.keys())
        answers['Timestamp'] = timestamp
        all_rows.append(answers)

    headers = sorted(all_keys) + ['Timestamp']
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'responses_export.csv')

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    return send_file(csv_path, as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
