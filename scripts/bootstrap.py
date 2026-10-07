from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import init_db, get_connection
from app.security import hash_password

def bootstrap():
    init_db()
    conn = get_connection()

    demo_users = [
        ("Demo Finder", "26BCE1001", "finder@vitstudent.ac.in", "9876543210", "finder123"),
        ("Demo Claimant", "26BCE1002", "claimant@vitstudent.ac.in", "9876543211", "claim123"),
    ]

    for name, reg_no, email, phone, password in demo_users:
        exists = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO users(name, reg_no, email, phone, password_hash) VALUES (?, ?, ?, ?, ?)",
                (name, reg_no, email, phone, hash_password(password)),
            )

    conn.commit()

    finder = conn.execute("SELECT id FROM users WHERE email='finder@vitstudent.ac.in'").fetchone()
    count = conn.execute("SELECT COUNT(*) AS c FROM listings").fetchone()["c"]

    if finder and count == 0:
        conn.execute(
            """
            INSERT INTO listings(user_id, type, title, description, venue, category, date_seen, verification_question)
            VALUES (?, 'Found', ?, ?, ?, ?, date('now'), ?)
            """,
            (
                finder["id"],
                "Black Casio scientific calculator",
                "Found near the seating area after the afternoon slot. A small label is attached on the back.",
                "SJT",
                "Calculators",
                "What initials are written on the back label?",
            ),
        )
        conn.execute(
            """
            INSERT INTO listings(user_id, type, title, description, venue, category, date_seen, verification_question)
            VALUES (?, 'Found', ?, ?, ?, ?, date('now'), ?)
            """,
            (
                finder["id"],
                "Single wireless earbud",
                "Found close to the food court tables. Case was not present.",
                "Gazebo",
                "Earphones",
                "Which side earbud is missing and what brand is it?",
            ),
        )
        conn.execute(
            """
            INSERT INTO listings(user_id, type, title, description, venue, category, date_seen, verification_question)
            VALUES (?, 'Lost', ?, ?, ?, ?, date('now'), NULL)
            """,
            (
                finder["id"],
                "Blue room key lanyard",
                "Lost while moving between the hostel and academic area.",
                "MH-Q",
                "Room Keys",
            ),
        )

    conn.commit()
    conn.close()
    print("Database bootstrap complete.")
    print("Run: python -m uvicorn app.main:app --reload")
    print("Open: http://127.0.0.1:8000")

if __name__ == "__main__":
    bootstrap()
