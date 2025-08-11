# YKO Solution Tool Box Meeting Form

This is a Flask-based questionnaire application for conducting Tool Box Meetings (TBM) at YKO Solution.  
It supports CSV-based question uploads, dynamic form rendering, file uploads, response storage, and CSV export.

## Features
- Dynamic questionnaire rendering from CSV upload
- File upload support (images only, max 50MB)
- Conditional required fields (radio buttons not required if image uploaded)
- Stores responses in SQLite database as JSON
- Admin interface for uploading new questionnaires
- Results viewing interface
- Export all responses as CSV
- Success modal after submission

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tbm-form.git
cd tbm-form
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install flask werkzeug
```

3. Ensure the `uploads` folder exists (will be auto-created on run).

## Usage

1. Run the app:
```bash
python app.py
```

2. Open in browser:
```
http://127.0.0.1:5000
```

3. Admin page:
```
http://127.0.0.1:5000/admin
```
Upload a CSV questionnaire (see format below).

4. Form page:
```
http://127.0.0.1:5000/
```
Fill in the questionnaire and submit.

5. Results page:
```
http://127.0.0.1:5000/results
```

6. Export CSV:
```
http://127.0.0.1:5000/export_csv
```

## CSV Format
Example questionnaire CSV:
```csv
작성자의 이름을 기입하십시오. (예: 홍길동),text
소속 회사를 기입하십시오.,text
프로젝트 명을 기입하십시오. (예 : HYCO_21),text
TBM 참석자의 이름을 모두 기입하십시오. (예: 홍길동, 이순신 2명),text
종이로 출력 후 TBM을 실시하였다면 TBM 시트를 SCAN 또는 촬영 후 사진을 Upload해 주십시오. (이 경우 하시 1~9번은 Check하지 않아도 됩니다),file
1. 허가된 이동 경로를 따라 이동하고 있습니까?,radio
2. 작업하는 구역에서 화재 발생 시 대피 경로를 미리 확인하였습니까?,radio
3. 이동 간 Site규정에서 요구하는 개인 보호 장비는 착용하고 있습니까?,radio
4. JSA 결과는 토의 되었습니까? JSA 항목을 기술하시오.,radio
5. JSA 결과에서는 작업과 관련된 위험을 모두 제시하고 있습니까?,radio
6. 엔지니어의 건강 상태는 양호합니까?,radio
7. 작업허가서에 허가권자의 승인은 득하였습니까?,radio
8. 방문 현장의 안전규정에 맞는 필요한 개인 보호 장비는 모두 준비되어 있습니까?,radio
9. Rack Room, CCR에서 작업 간 안전 보호 장비는 착용하였습니까?,radio
10. 1번~9번 항목 중 "아니오"라고 답변한 경우의 조치 내용에 대해서 기술하시오. (없으면 "PASS"를 입력),text
11. 기타 특이사항이 있을 경우 기술하시오. (없으면 "PASS"를 입력),text
12. 위 사실과 다름 없음을 선언합니다.,checkbox
```

## File Upload Rules
- Allowed file types: `png`, `jpg`, `jpeg`, `gif`, `bmp`
- Max file size: 50MB

## Technology Stack
- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **File Storage:** Local uploads folder

## License
This project is licensed under the MIT License.
