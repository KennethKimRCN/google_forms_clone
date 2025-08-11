import os
import json
import csv
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DB_NAME = 'questions.db'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        c.execute('SELECT id, question, type FROM questions ORDER BY id')
        questions = c.fetchall()

    if request.method == 'POST':
        answers = {}
        uploaded_image = None
        upload_question_id = None

        for q in questions:
            qid, question, qtype = q
            if question.startswith('종이로 출력 후 TBM을 실시하였다면'):
                file = request.files.get(f'q_{qid}')
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        file.seek(0, os.SEEK_END)
                        file_length = file.tell()
                        file.seek(0)
                        if file_length > 50 * 1024 * 1024:
                            return "File size exceeds 50MB limit", 400
                        filename = secure_filename(file.filename)
                        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(save_path)
                        uploaded_image = filename
                        upload_question_id = qid
                        answers[question] = filename
                    else:
                        return "Invalid file type", 400
                else:
                    answers[question] = request.form.get(f'q_{qid}', '')
            else:
                if qid in range(1, 10) and qtype == 'radio':
                    if uploaded_image:
                        answer = request.form.get(f'q_{qid}', '')
                    else:
                        answer = request.form.get(f'q_{qid}', '')
                        if not answer:
                            return f"Question {qid} is required", 400
                else:
                    answer = request.form.get(f'q_{qid}', '')
                    if qtype in ['text', 'number', 'radio'] and not uploaded_image:
                        if not answer:
                            return f"Question {qid} is required", 400
                answers[question] = answer

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            timestamp = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
            c.execute(
                'INSERT INTO responses (answers, timestamp) VALUES (?, ?)',
                (json.dumps(answers, ensure_ascii=False), timestamp)
            )
            conn.commit()
        return "success"

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
                with open(filepath, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if len(row) >= 2:
                            question = ','.join(row[:-1]).strip()
                            qtype = row[-1].strip()
                            question = question.strip('"')
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

    groups = {}
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

    grouped_responses = []
    for cols, resps in groups.items():
        sorted_resps = sorted(resps, key=lambda r: r['id'])
        grouped_responses.append({
            "columns": sorted(cols),
            "responses": sorted_resps
        })

    grouped_responses.sort(key=lambda g: len(g['responses']), reverse=True)

    return render_template('results.html', grouped_responses=grouped_responses)

@app.route('/export_csv')
def export_csv():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT answers, timestamp FROM responses ORDER BY id')
        rows = c.fetchall()

    all_rows = []
    all_keys = set()
    for raw_answers, timestamp in rows:
        answers = json.loads(raw_answers)
        all_keys.update(answers.keys())
        answers['Timestamp'] = timestamp
        all_rows.append(answers)

    headers = sorted(all_keys) + ['Timestamp']
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'responses_export.csv')

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    return send_file(csv_path, as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
