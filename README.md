# VIT Recover — Campus Lost & Found Portal

A privacy-first recovery platform for the VIT campus community, designed to replace messy WhatsApp lost-and-found groups with structured listings, private ownership verification, and secure in-app handoff coordination.

## Features

- Separate **Lost** and **Found** feeds
- VIT campus venue tagging only
- Category tags for common student items
- Student registration and login
- Public masking of registration number, email and phone number
- Finder-defined private ownership challenge
- Claim verification requests with **Approve / Reject**
- Private in-app handoff thread after approval
- Suggested safe on-campus meetup checkpoints
- Either party can mark an item **Resolved**
- Resolved items disappear from active boards
- Robust backend validation and clear UI states
- SQLite database for simple local setup

## Tech stack

- FastAPI
- SQLite
- Jinja2
- Vanilla JavaScript
- HTML/CSS

## Quick start

```bash
git clone https://github.com/Man1sh28/vit-recover.git
cd vit-recover

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python scripts/bootstrap.py
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/bootstrap.py
python -m uvicorn app.main:app --reload
```

## Demo accounts

### Finder
- Email: `finder@vitstudent.ac.in`
- Password: `finder123`

### Claimant
- Email: `claimant@vitstudent.ac.in`
- Password: `claim123`

## Workflow

1. A student posts a **Found** item.
2. The finder adds a private verification question.
3. A claimant answers the ownership challenge.
4. The finder reviews the claim privately.
5. The finder approves or rejects it.
6. Approved parties gain access to a private handoff thread.
7. They choose a safe campus checkpoint.
8. Either party marks the item resolved after return.

## Allowed VIT venues

### Academic blocks
SJT, TT, PRP, SMV, MB, GDN, CDMM

### Men's hostels
MH-A through MH-T

### Ladies' hostels
LH-A through LH-J

### Food courts
Gazebo, Food Mall, DC

### Other
Central Library, Sports Complex

## Categories

- ID Cards
- Room Keys
- Calculators
- Lab Equipment
- Earphones
- Wallets

## Privacy model

Public listings never reveal a student's full registration number, email address or phone number. Claims are verified privately, and approved users coordinate through the in-app thread rather than exchanging personal contact information publicly.

## Project structure

```text
vit-recover/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── security.py
│   ├── templates/
│   └── static/
├── scripts/
│   └── bootstrap.py
├── requirements.txt
└── README.md
```

## Production notes

Before public deployment, move the session secret into an environment variable and add HTTPS, CSRF protection, rate limiting, email verification, moderation, PostgreSQL, and institutional SSO.
