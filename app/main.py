from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import re

from .database import get_connection, init_db
from .security import hash_password, verify_password, mask_reg_no, mask_email, mask_phone
from .models import VENUES, CATEGORIES, HANDOFF_POINTS

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="VIT Campus Lost & Found Recovery Portal")
app.add_middleware(
    SessionMiddleware,
    secret_key="replace-this-secret-in-production",
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@app.on_event("startup")
def startup():
    init_db()

def current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def require_user(request: Request):
    user = current_user(request)
    if not user:
        return None, RedirectResponse("/login?next=" + request.url.path, status_code=303)
    return user, None

def valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+", email.strip()))

def listing_with_owner(listing_id: int):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT l.*, u.name AS owner_name, u.reg_no, u.email, u.phone
        FROM listings l
        JOIN users u ON u.id = l.user_id
        WHERE l.id = ?
        """,
        (listing_id,),
    ).fetchone()
    conn.close()
    return row

@app.get("/", response_class=HTMLResponse)
def home(request: Request, type: str = "Found", category: str = "", venue: str = ""):
    if type not in ("Lost", "Found"):
        type = "Found"

    query = "SELECT l.* FROM listings l WHERE l.status='Active' AND l.type=?"
    params = [type]

    if category in CATEGORIES:
        query += " AND l.category=?"
        params.append(category)
    else:
        category = ""

    if venue in VENUES:
        query += " AND l.venue=?"
        params.append(venue)
    else:
        venue = ""

    query += " ORDER BY l.created_at DESC"

    conn = get_connection()
    listings = conn.execute(query, params).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": current_user(request),
            "listings": listings,
            "selected_type": type,
            "selected_category": category,
            "selected_venue": venue,
            "venues": VENUES,
            "categories": CATEGORIES,
        },
    )

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request, "mode": "register", "user": current_user(request)})

@app.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    reg_no: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
):
    errors = []
    name = name.strip()
    reg_no = reg_no.strip().upper()
    email = email.strip().lower()
    phone = phone.strip()

    if len(name) < 2:
        errors.append("Name must contain at least 2 characters.")
    if len(reg_no) < 5 or len(reg_no) > 20:
        errors.append("Enter a valid VIT registration number.")
    if not valid_email(email):
        errors.append("Enter a valid email address.")
    if len(re.sub(r"\\D", "", phone)) < 10:
        errors.append("Enter a valid mobile number.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")

    conn = get_connection()
    duplicate = conn.execute(
        "SELECT id FROM users WHERE email=? OR reg_no=?",
        (email, reg_no),
    ).fetchone()

    if duplicate:
        errors.append("An account with that email or registration number already exists.")

    if errors:
        conn.close()
        return templates.TemplateResponse(
            "auth.html",
            {
                "request": request,
                "mode": "register",
                "errors": errors,
                "user": None,
                "form": {"name": name, "reg_no": reg_no, "email": email, "phone": phone},
            },
            status_code=400,
        )

    cur = conn.execute(
        "INSERT INTO users(name, reg_no, email, phone, password_hash) VALUES (?, ?, ?, ?, ?)",
        (name, reg_no, email, phone, hash_password(password)),
    )
    conn.commit()
    request.session["user_id"] = cur.lastrowid
    conn.close()
    return RedirectResponse("/dashboard?welcome=1", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request, "mode": "login", "user": current_user(request)})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), next: str = Form("/dashboard")):
    email = email.strip().lower()
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()

    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            "auth.html",
            {
                "request": request,
                "mode": "login",
                "errors": ["Incorrect email or password."],
                "form": {"email": email},
                "user": None,
            },
            status_code=400,
        )

    request.session["user_id"] = user["id"]
    destination = next if next.startswith("/") else "/dashboard"
    return RedirectResponse(destination, status_code=303)

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/listings/new", response_class=HTMLResponse)
def new_listing_page(request: Request):
    user, redirect = require_user(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "create_listing.html",
        {
            "request": request,
            "user": user,
            "venues": VENUES,
            "categories": CATEGORIES,
        },
    )

@app.post("/listings/new")
def create_listing(
    request: Request,
    type: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    venue: str = Form(...),
    category: str = Form(...),
    date_seen: str = Form(...),
    verification_question: str = Form(""),
):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    errors = []
    title = title.strip()
    description = description.strip()
    verification_question = verification_question.strip()

    if type not in ("Lost", "Found"):
        errors.append("Listing type must be Lost or Found.")
    if venue not in VENUES:
        errors.append("Please choose an official VIT campus venue.")
    if category not in CATEGORIES:
        errors.append("Please choose an allowed item category.")
    if len(title) < 3 or len(title) > 80:
        errors.append("Title must be 3–80 characters.")
    if len(description) < 10 or len(description) > 1200:
        errors.append("Description must be 10–1200 characters.")
    if not date_seen:
        errors.append("Please enter the date the item was lost or found.")
    if type == "Found" and len(verification_question) < 5:
        errors.append("Found items require a private verification question.")

    if errors:
        return templates.TemplateResponse(
            "create_listing.html",
            {
                "request": request,
                "user": user,
                "venues": VENUES,
                "categories": CATEGORIES,
                "errors": errors,
                "form": {
                    "type": type,
                    "title": title,
                    "description": description,
                    "venue": venue,
                    "category": category,
                    "date_seen": date_seen,
                    "verification_question": verification_question,
                },
            },
            status_code=400,
        )

    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO listings(user_id, type, title, description, venue, category, date_seen, verification_question)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user["id"], type, title, description, venue, category, date_seen, verification_question or None),
    )
    conn.commit()
    listing_id = cur.lastrowid
    conn.close()

    return RedirectResponse(f"/listings/{listing_id}?created=1", status_code=303)

@app.get("/listings/{listing_id}", response_class=HTMLResponse)
def listing_detail(request: Request, listing_id: int):
    listing = listing_with_owner(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")

    user = current_user(request)
    existing_claim = None
    if user:
        conn = get_connection()
        existing_claim = conn.execute(
            "SELECT * FROM claims WHERE listing_id=? AND claimant_id=?",
            (listing_id, user["id"]),
        ).fetchone()
        conn.close()

    public_owner = {
        "reg_no": mask_reg_no(listing["reg_no"]),
        "email": mask_email(listing["email"]),
        "phone": mask_phone(listing["phone"]),
    }

    return templates.TemplateResponse(
        "listing.html",
        {
            "request": request,
            "user": user,
            "listing": listing,
            "public_owner": public_owner,
            "existing_claim": existing_claim,
        },
    )

@app.post("/listings/{listing_id}/claim")
def submit_claim(request: Request, listing_id: int, answer: str = Form(...)):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    listing = listing_with_owner(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")
    if listing["status"] != "Active":
        return RedirectResponse(f"/listings/{listing_id}?error=resolved", status_code=303)
    if listing["user_id"] == user["id"]:
        return RedirectResponse(f"/listings/{listing_id}?error=own", status_code=303)
    if listing["type"] != "Found":
        return RedirectResponse(f"/listings/{listing_id}?error=claim-not-needed", status_code=303)

    answer = answer.strip()
    if len(answer) < 2 or len(answer) > 500:
        return RedirectResponse(f"/listings/{listing_id}?error=answer", status_code=303)

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO claims(listing_id, claimant_id, answer) VALUES (?, ?, ?)",
            (listing_id, user["id"], answer),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        return RedirectResponse(f"/listings/{listing_id}?error=duplicate", status_code=303)

    conn.close()
    return RedirectResponse(f"/listings/{listing_id}?claimed=1", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    conn = get_connection()

    my_listings = conn.execute(
        "SELECT * FROM listings WHERE user_id=? ORDER BY created_at DESC",
        (user["id"],),
    ).fetchall()

    incoming_claims = conn.execute(
        """
        SELECT c.*, l.title AS listing_title, l.venue, u.name AS claimant_name
        FROM claims c
        JOIN listings l ON l.id=c.listing_id
        JOIN users u ON u.id=c.claimant_id
        WHERE l.user_id=?
        ORDER BY c.created_at DESC
        """,
        (user["id"],),
    ).fetchall()

    my_claims = conn.execute(
        """
        SELECT c.*, l.title AS listing_title, l.venue, l.status AS listing_status
        FROM claims c
        JOIN listings l ON l.id=c.listing_id
        WHERE c.claimant_id=?
        ORDER BY c.created_at DESC
        """,
        (user["id"],),
    ).fetchall()

    conn.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "my_listings": my_listings,
            "incoming_claims": incoming_claims,
            "my_claims": my_claims,
        },
    )

@app.post("/claims/{claim_id}/decision")
def claim_decision(request: Request, claim_id: int, decision: str = Form(...)):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    if decision not in ("Approved", "Rejected"):
        raise HTTPException(status_code=400, detail="Invalid decision.")

    conn = get_connection()
    claim = conn.execute(
        """
        SELECT c.*, l.user_id AS finder_id, l.status AS listing_status
        FROM claims c
        JOIN listings l ON l.id=c.listing_id
        WHERE c.id=?
        """,
        (claim_id,),
    ).fetchone()

    if not claim:
        conn.close()
        raise HTTPException(status_code=404, detail="Claim not found.")
    if claim["finder_id"] != user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="You cannot review this claim.")
    if claim["listing_status"] != "Active":
        conn.close()
        return RedirectResponse("/dashboard?error=resolved", status_code=303)

    conn.execute(
        "UPDATE claims SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (decision, claim_id),
    )
    conn.commit()
    conn.close()

    return RedirectResponse("/dashboard?updated=1", status_code=303)

@app.get("/claims/{claim_id}/thread", response_class=HTMLResponse)
def claim_thread(request: Request, claim_id: int):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    conn = get_connection()
    claim = conn.execute(
        """
        SELECT c.*, l.title AS listing_title, l.user_id AS finder_id,
               l.status AS listing_status, l.id AS listing_id
        FROM claims c
        JOIN listings l ON l.id=c.listing_id
        WHERE c.id=?
        """,
        (claim_id,),
    ).fetchone()

    if not claim:
        conn.close()
        raise HTTPException(status_code=404, detail="Claim not found.")
    if claim["status"] != "Approved":
        conn.close()
        raise HTTPException(status_code=403, detail="Thread is available only after claim approval.")
    if user["id"] not in (claim["finder_id"], claim["claimant_id"]):
        conn.close()
        raise HTTPException(status_code=403, detail="You cannot access this thread.")

    messages = conn.execute(
        """
        SELECT m.*, u.name AS sender_name
        FROM messages m
        JOIN users u ON u.id=m.sender_id
        WHERE m.claim_id=?
        ORDER BY m.created_at ASC
        """,
        (claim_id,),
    ).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "thread.html",
        {
            "request": request,
            "user": user,
            "claim": claim,
            "messages": messages,
            "handoff_points": HANDOFF_POINTS,
        },
    )

@app.post("/claims/{claim_id}/thread")
def send_message(request: Request, claim_id: int, body: str = Form(...)):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    body = body.strip()
    if len(body) < 1 or len(body) > 600:
        return RedirectResponse(f"/claims/{claim_id}/thread?error=message", status_code=303)

    conn = get_connection()
    claim = conn.execute(
        """
        SELECT c.*, l.user_id AS finder_id
        FROM claims c
        JOIN listings l ON l.id=c.listing_id
        WHERE c.id=?
        """,
        (claim_id,),
    ).fetchone()

    if not claim or claim["status"] != "Approved":
        conn.close()
        raise HTTPException(status_code=403, detail="Messaging is unavailable.")
    if user["id"] not in (claim["finder_id"], claim["claimant_id"]):
        conn.close()
        raise HTTPException(status_code=403, detail="You cannot send messages here.")

    conn.execute(
        "INSERT INTO messages(claim_id, sender_id, body) VALUES (?, ?, ?)",
        (claim_id, user["id"], body),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(f"/claims/{claim_id}/thread?sent=1", status_code=303)

@app.post("/listings/{listing_id}/resolve")
def resolve_listing(request: Request, listing_id: int):
    user, redirect = require_user(request)
    if redirect:
        return redirect

    conn = get_connection()
    listing = conn.execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()
    if not listing:
        conn.close()
        raise HTTPException(status_code=404, detail="Listing not found.")

    allowed = listing["user_id"] == user["id"]

    if not allowed:
        approved_claim = conn.execute(
            "SELECT id FROM claims WHERE listing_id=? AND claimant_id=? AND status='Approved'",
            (listing_id, user["id"]),
        ).fetchone()
        allowed = approved_claim is not None

    if not allowed:
        conn.close()
        raise HTTPException(status_code=403, detail="You cannot resolve this listing.")

    conn.execute("UPDATE listings SET status='Resolved' WHERE id=?", (listing_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/dashboard?resolved=1", status_code=303)
