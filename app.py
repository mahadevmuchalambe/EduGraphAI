import sqlite3
import os
from pathlib import Path
from functools import wraps

from flask import (
    Flask, request, redirect, url_for,
    session, render_template_string, flash,
    send_from_directory, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "edugraph.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-to-a-random-secret-before-deployment"

UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)


ALLOWED_EXTENSIONS = {"pdf"}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'professor'))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                unit TEXT NOT NULL,
                material_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (professor_id) REFERENCES users(id)
            )
        """)




PAGE_STYLE = """
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, sans-serif;
    color: #172033;
    background: #f4f7fc;
}

a { text-decoration: none; }

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    padding: 16px 6%;
    background: white;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #173b75;
    font-size: 21px;
    font-weight: bold;
}

.brand img {
    width: 75px;
    height: 75px;
    object-fit: contain;
}

.nav-links {
    display: flex;
    gap: 12px;
    align-items: center;
}

.btn {
    display: inline-block;
    padding: 13px 23px;
    border-radius: 9px;
    font-weight: bold;
    background: #ffffff;
    color: #204b91;
    border: 1px solid #ffffff;
}

.btn-primary {
    background: #3478f6;
    color: white;
    border-color: #3478f6;
}

.hero {
    min-height: 590px;
    display: flex;
    align-items: center;
    padding: 75px 8%;
    color: white;
    background:
        linear-gradient(90deg,
            rgba(7, 20, 48, .88),
            rgba(7, 20, 48, .52)),
     url('/static/campus.png') center/cover no-repeat;
}

.hero-content {
    max-width: 720px;
}

.eyebrow {
    display: inline-block;
    padding: 9px 14px;
    border: 1px solid #ffffff66;
    border-radius: 30px;
    background: #ffffff15;
    font-size: 14px;
}

.hero h1 {
    font-size: clamp(38px, 5vw, 64px);
    line-height: 1.1;
    margin: 24px 0 16px;
}

.hero p {
    font-size: 18px;
    line-height: 1.8;
    color: #e3eaf8;
    max-width: 620px;
}

.hero-actions {
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    margin-top: 28px;
}

.features {
    padding: 55px 7%;
    text-align: center;
}

.features h2 {
    font-size: 30px;
    color: #183a70;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 22px;
    margin-top: 30px;
}

.feature {
    background: white;
    padding: 28px 22px;
    border-radius: 16px;
    text-align: left;
    box-shadow: 0 8px 28px #132b4c0b;
    border: 1px solid #e6ebf4;
}

.feature .symbol {
    font-size: 30px;
}

.feature h3 {
    color: #244f95;
}

.feature p {
    line-height: 1.7;
    color: #596579;
}

footer {
    padding: 22px;
    text-align: center;
    color: #64748b;
    background: white;
}

.card {
    background: white;
    width: min(420px, 92%);
    margin: 65px auto;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 8px 30px #0001;
}

h2 { color: #3155c6; text-align: center; }

input, select {
    width: 100%;
    padding: 12px;
    margin: 8px 0 16px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}

button {
    width: 100%;
    background: #3155c6;
    color: white;
    padding: 12px;
    border: 0;
    border-radius: 8px;
    cursor: pointer;
}

.message {
    background: #fef3c7;
    padding: 10px;
    border-radius: 8px;
}

.center { text-align: center; }

@media (max-width: 700px) {
    .navbar { padding: 14px 5%; }
    .brand { font-size: 16px; }
    .brand img { width: 42px; height: 42px; }
    .nav-links { gap: 6px; }
    .nav-links .btn { padding: 10px 12px; }
    .hero { min-height: 520px; padding: 55px 7%; }
    .feature-grid { grid-template-columns: 1fr; }
}
</style>
"""




@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">
        <title>DBATU ScholarAI | Academic Assistant</title>
        {{ style|safe }}
    </head>
    <body>

        <nav class="navbar">
            <a class="brand" href="{{ url_for('home') }}">
              <img src="{{ url_for('static',
    filename='DBATU Logo.png') }}"
    alt="DBATU University Logo">
                <span>DBATU ScholarAI</span>
            </a>

            <div class="nav-links">
                <a class="btn"
                   href="{{ url_for('login') }}">Login</a>
                <a class="btn btn-primary"
                   href="{{ url_for('register') }}">Sign Up</a>
            </div>
        </nav>

        <section class="hero">
            <div class="hero-content">
                <span class="eyebrow">
                    DBATU Lonere • AI-Powered Learning
                </span>

                <h1>Learn Smarter.<br>Study Better.</h1>

                <p>
                    Your academic companion for understanding
                    concepts, exploring professors' notes and
                    learning with AI. Find relevant study material
                    and get detailed answers grounded in your notes.
                </p>

                <div class="hero-actions">
                    <a class="btn btn-primary"
                       href="{{ url_for('register') }}">
                        Get Started →
                    </a>
                    <a class="btn"
                       href="{{ url_for('login') }}">
                        Student / Professor Login
                    </a>
                </div>
            </div>
        </section>

        <section class="features">
            <h2>Everything You Need to Learn</h2>
            <p>Your study material, connected with AI.</p>

            <div class="feature-grid">
                <article class="feature">
                    <div class="symbol">📚</div>
                    <h3>Smart Study Assistant</h3>
                    <p>
                        Ask academic questions and get detailed,
                        structured answers using relevant content
                        from uploaded notes.
                    </p>
                </article>

                <article class="feature">
                    <div class="symbol">🔎</div>
                    <h3>Notes & PDF Search</h3>
                    <p>
                        Find relevant notes, assignments and
                        source pages without searching every PDF
                        manually.
                    </p>
                </article>

                <article class="feature">
                    <div class="symbol">🧠</div>
                    <h3>Knowledge Graph</h3>
                    <p>
                        Connect subjects, concepts and related
                        topics to support context-aware learning.
                    </p>
                </article>
            </div>
        </section>

        <footer>
            DBATU ScholarAI · AI-Powered Academic Learning
            <br>
            A student project — not an official university service.
        </footer>

    </body>
    </html>
    """, style=PAGE_STYLE)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        saved_email = request.cookies.get("saved_email", "")
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        if not name or not email or len(password) < 8:
            flash("Enter all details. Password must be at least 8 characters.")
        elif role not in ("student", "professor"):
            flash("Select a valid account role.")
        else:
            try:
                with get_db() as conn:
                    conn.execute(
                        """INSERT INTO users
                        (name, email, password_hash, role)
                        VALUES (?, ?, ?, ?)""",
                        (name, email, generate_password_hash(password), role)
                    )
                flash("Account created! Please log in.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("This email is already registered.")

    return render_template_string("""
    <!doctype html>
    <html><head><title>Sign Up</title>{{ style|safe }}</head>
    <body><div class="card">
        <h1>Create Account</h1>
        {% for message in get_flashed_messages() %}
            <p class="message">{{ message }}</p>
        {% endfor %}
        <form method="post">
            <label>Full Name</label>
            <input name="name" required maxlength="100">

            <label>Email</label>
            <input name="email" type="email" required maxlength="254">

            <label>Password (minimum 8 characters)</label>
            <input name="password" type="password" minlength="8" required>

            <label>Register as</label>
            <select name="role" required>
                <option value="">Choose your role</option>
                <option value="student">Student</option>
                <option value="professor">Professor</option>
            </select>
            <button type="submit">Create Account</button>
        </form>
        <p class="center">Already registered? <a href="{{ url_for('login') }}">Login</a></p>
    </div></body></html>
    """, style=PAGE_STYLE)


@app.route("/login", methods=["GET", "POST"])

def login():
    saved_email = request.cookies.get("saved_email", "")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]

            response = redirect(url_for("dashboard"))

            if request.form.get("remember") == "yes":
                response.set_cookie(
                    "saved_email",
                    email,
                    max_age=30 * 24 * 60 * 60,
                    httponly=True,
                    samesite="Lax"
                )
            else:
                response.delete_cookie("saved_email")

            return response

        flash("Invalid email or password.")

    return render_template_string("""
    <!doctype html>
    <html>
    <head>
        <title>Login</title>
        {{ style|safe }}
    </head>
    <body>
        <div class="card">
            <h1>Welcome Back</h1>

            {% for message in get_flashed_messages() %}
                <p class="message">{{ message }}</p>
            {% endfor %}

            <form method="post">
                <label>Email</label>
                <input
                    name="email"
                    type="email"
                    autocomplete="username"
                    value="{{ saved_email }}"
                    required
                >

                <label>Password</label>
                <input
                    name="password"
                    type="password"
                    autocomplete="current-password"
                    required
                >

                <label style="display:flex; align-items:center; gap:8px; margin:12px 0;">
                    <input
                        type="checkbox"
                        name="remember"
                        value="yes"
                        style="width:auto; margin:0;"
                    >
                    Remember my email
                </label>

                <button type="submit">Login</button>
            </form>

            <p class="center">
                New user? <a href="{{ url_for('register') }}">Sign up</a>
            </p>
        </div>
    </body>
    </html>
    """, style=PAGE_STYLE, saved_email=saved_email)



def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    if user["role"] == "professor":
        heading = "Professor Dashboard"
        description = "Upload and manage academic study materials."
    else:
        heading = "Student Dashboard"
        description = "Ask questions about your professors' study materials."


    with get_db() as conn:
        subjects = conn.execute(
            """
            SELECT DISTINCT subject
            FROM materials
            WHERE subject IS NOT NULL AND TRIM(subject) != ''
            ORDER BY subject
            """
        ).fetchall()

    subjects = [row["subject"] for row in subjects]

    with get_db() as conn:
        materials = conn.execute(
            """
            SELECT id, title, subject
            FROM materials
            ORDER BY subject, title
            """
        ).fetchall()
    return render_template_string("""
    
<!doctype html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ heading }}</title>
    {{ style|safe }}


    <style>
        /* PROFESSOR DASHBOARD */
        .professor-layout {
            display: flex;
            min-height: 100vh;
            background: #f5f6fc;
            color: #202044;
        }

        .professor-sidebar {
            width: 250px;
            flex-shrink: 0;
            padding: 28px 18px;
            background: #17172f;
            color: white;
        }

        .professor-brand {
            font-size: 25px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }

        .professor-brand span {
            color: #a78bfa;
        }

        .professor-subtitle {
            margin: 9px 0 34px;
            color: #aaaac8;
            font-size: 11px;
            letter-spacing: 1.2px;
        }

        .professor-nav {
            display: block;
            padding: 14px;
            margin-bottom: 9px;
            border-radius: 11px;
            color: #d6d6ee;
            text-decoration: none;
            transition: background .2s ease;
        }

        .professor-nav:hover {
            background: #292947;
        }

        .professor-nav.active {
            background: linear-gradient(120deg, #4f46e5, #7c3aed);
            color: white;
        }

        .professor-main {
            flex: 1;
            min-width: 0;
            padding: 34px;
        }

        .professor-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            margin-bottom: 28px;
        }

        .professor-topbar h1 {
            margin: 0 0 8px;
            font-size: 28px;
            color: #202044;
        }

        .professor-topbar p,
        .professor-panel p {
            margin: 0;
            color: #777995;
            line-height: 1.6;
        }

        .professor-profile {
            padding: 13px 17px;
            background: white;
            border: 1px solid #e6e7f2;
            border-radius: 13px;
            white-space: nowrap;
        }

        .professor-hero {
            padding: 34px;
            margin-bottom: 24px;
            border-radius: 22px;
            color: white;
            background: linear-gradient(120deg, #4338ca, #7c3aed, #8b5cf6);
            box-shadow: 0 14px 35px #4f46e522;
        }

        .professor-eyebrow {
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1.5px;
            color: #e4ddff;
        }

        .professor-hero h2 {
            margin: 16px 0 12px;
            text-align: left;
            color: white;
            font-size: 28px;
        }

        .professor-hero p {
            margin: 0 0 24px;
            color: #f0edff;
            line-height: 1.7;
        }

        .professor-upload-btn {
            display: inline-block;
            padding: 13px 20px;
            border-radius: 11px;
            background: white;
            color: #5541c8;
            font-weight: bold;
            text-decoration: none;
        }

        .professor-upload-btn:hover {
            background: #f0edff;
        }

        .professor-stats {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }

        .professor-stat,
        .professor-panel {
            padding: 24px;
            border: 1px solid #e7e8f5;
            border-radius: 18px;
            background: white;
            box-shadow: 0 8px 25px #24245b06;
        }

        .professor-stat-icon {
            margin-bottom: 12px;
            font-size: 28px;
        }

        .professor-stat h3 {
            margin: 0 0 9px;
            color: #282452;
        }

        .professor-stat p {
            margin: 0 0 14px;
            color: #777995;
            line-height: 1.6;
        }

        .professor-stat a,
        .professor-action-link {
            color: #5b4bc4;
            text-decoration: none;
            font-weight: bold;
        }

        .professor-panel h2 {
            margin: 0 0 10px;
            text-align: left;
            color: #282452;
        }

        .professor-action-link {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 22px;
            padding: 17px;
            border: 1px solid #e7e4ff;
            border-radius: 14px;
            background: #faf9ff;
            color: #292452;
        }

        .professor-action-icon {
            font-size: 27px;
        }

        .professor-action-link small {
            display: inline-block;
            margin-top: 6px;
            color: #777995;
            font-weight: normal;
            line-height: 1.5;
        }

        @media (max-width: 760px) {
            .professor-layout {
                display: block;
            }

            .professor-sidebar {
                width: 100%;
                padding: 20px;
            }

            .professor-subtitle {
                margin-bottom: 20px;
            }

            .professor-main {
                padding: 18px;
            }

            .professor-topbar {
                align-items: flex-start;
                flex-direction: column;
            }

            .professor-hero {
                padding: 24px;
            }

            .professor-hero h2 {
                font-size: 23px;
            }

            .professor-stats {
                grid-template-columns: 1fr;
            }
        }

    <style>
        body {
            margin: 0;
            background: #f4f5ff;
            font-family: Arial, sans-serif;
            color: #1e1b4b;
        }

        .student-layout {
            display: flex;
            min-height: 100vh;
        }

        .student-sidebar {
            width: 245px;
            flex-shrink: 0;
            background: #17172f;
            color: white;
            padding: 28px 18px;
            box-sizing: border-box;
        }

        .student-brand {
            font-size: 23px;
            font-weight: bold;
            margin-bottom: 8px;
        }

        .student-brand span {
            color: #a78bfa;
        }

        .student-subtitle {
            color: #aaaac8;
            font-size: 13px;
            margin-bottom: 34px;
        }

        .student-nav {
            display: block;
            padding: 13px 14px;
            margin-bottom: 8px;
            border-radius: 10px;
            color: #d6d6ee;
            text-decoration: none;
        }

        .student-nav.active {
            background: linear-gradient(120deg, #4f46e5, #7c3aed);
            color: white;
        }

        .student-main {
            flex: 1;
            min-width: 0;
            padding: 34px;
        }

        .student-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            margin-bottom: 28px;
        }

        .student-topbar h1 {
            font-size: 28px;
            margin: 0 0 8px;
        }

        .student-muted {
            color: #777995;
            line-height: 1.6;
        }

        .student-profile {
            background: white;
            border: 1px solid #e5e7f5;
            padding: 12px 16px;
            border-radius: 14px;
            font-size: 14px;
        }

        .student-hero {
            background: linear-gradient(120deg, #4338ca, #7c3aed, #8b5cf6);
            padding: 30px;
            color: white;
            border-radius: 22px;
            margin-bottom: 24px;
            box-shadow: 0 14px 35px #4f46e522;
        }

        .student-hero h2 {
            color: white;
            font-size: 25px;
            margin: 0 0 12px;
        }

        .student-hero p {
            color: #f0edff;
            line-height: 1.7;
            margin: 0;
        }

        .student-stats {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }

        .student-stat {
            background: white;
            border: 1px solid #e7e8f5;
            border-radius: 18px;
            padding: 22px;
        }

        .student-stat-icon {
            font-size: 24px;
            margin-bottom: 12px;
        }

        .student-stat h3 {
            margin: 0 0 8px;
            color: #282452;
        }

        .student-chat-card {
            background: white;
            border: 1px solid #e3e5f3;
            border-radius: 22px;
            padding: 26px;
            box-shadow: 0 8px 30px #24245b08;
        }

        .student-chat-card h2 {
            margin-top: 0;
            color: #282452;
        }

        .student-chat-card label {
            display: block;
            margin: 18px 0 8px;
            font-weight: bold;
            font-size: 14px;
        }

        .student-chat-card #subject,
        .student-chat-card #question {
            width: 100%;
            box-sizing: border-box;
            padding: 14px;
            border: 1px solid #d9daf0;
            border-radius: 12px;
            background: #fbfbff;
            font-size: 15px;
            color: #252347;
        }

        .student-chat-card #question {
            resize: vertical;
            font-family: Arial, sans-serif;
            line-height: 1.6;
        }

        .student-chat-card #subject:focus,
        .student-chat-card #question:focus {
            outline: 2px solid #a5b4fc;
            border-color: #6366f1;
        }

        .student-ask-button {
            margin-top: 18px;
            padding: 14px 24px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(120deg, #4f46e5, #7c3aed);
            color: white;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
        }

        .student-ask-button:hover {
            filter: brightness(1.08);
        }

        .student-answer {
            white-space: pre-wrap;
            overflow-wrap: anywhere;
            line-height: 1.8;
            margin-top: 20px;
        }

        .student-answer:not(:empty) {
            background: #f5f3ff;
            border-left: 4px solid #7c3aed;
            border-radius: 12px;
            padding: 20px;
        }

        .student-sources {
            overflow-wrap: anywhere;
            margin-top: 18px;
        }

        .student-sources a {
            color: #4f46e5;
            font-weight: bold;
        }

        .student-logout {
            display: inline-block;
            margin-top: 30px;
            color: #5b4bc4;
            text-decoration: none;
            font-weight: bold;
        }

        @media (max-width: 760px) {
            .student-layout {
                display: block;
            }

            .student-sidebar {
                width: 100%;
                padding: 18px;
            }

            .student-subtitle {
                margin-bottom: 18px;
            }

            .student-main {
                padding: 18px;
            }

            .student-topbar {
                align-items: flex-start;
                flex-direction: column;
            }

            .student-hero {
                padding: 23px;
            }

            .student-stats {
                grid-template-columns: 1fr;
            }

            .student-chat-card {
                padding: 18px;
            }
        }
    </style>
</head>

    

<body>
{% if user["role"] == "student" %}

<div class="student-layout">
    <aside class="student-sidebar">
        <div class="student-brand">EduGraph<span>AI</span></div>
        <div class="student-subtitle">STUDENT WORKSPACE</div>

        <a class="student-nav active" href="{{ url_for('dashboard') }}">▦ Dashboard</a>
        <a class="student-nav" href="#study-assistant">✦ Study Assistant</a>
        <a class="student-nav" href="#study-resources">▤ Study Resources</a>
        <a class="student-nav" href="{{ url_for('logout') }}">↪ Logout</a>
    </aside>

    <main class="student-main">
        <div class="student-topbar">
            <div>
                <h1>Student Dashboard</h1>
                <div class="student-muted">Your AI-powered study space</div>
            </div>
            <div class="student-profile">👤 {{ user["name"] }}</div>
        </div>

        <section class="student-hero">
            <h2>Welcome back, {{ user["name"] }}! 👋</h2>
            <p>Learn smarter and find answers directly from your professor's notes.</p>
        </section>

        <section class="student-stats">
            <div class="student-stat">
                <div class="student-stat-icon">📚</div>
                <h3>Your Subjects</h3>
                <div class="student-muted">{{ subjects|length }} subjects available</div>
            </div>
            <div class="student-stat">
                <div class="student-stat-icon">✨</div>
                <h3>AI Study Assistant</h3>
                <div class="student-muted">Get help from uploaded study materials</div>
            </div>
        </section>

        <section class="student-chat-card" id="study-assistant">
            <h2>✦ Ask Your AI Study Assistant</h2>
            <p class="student-muted">Choose a subject and enter your question.</p>

            <form id="chat-form">
                <label for="subject">Select Subject</label>
                <select id="subject" name="subject" required>
                    <option value="">-- Choose a subject --</option>
                    {% for subject in subjects %}
                    <option value="{{ subject }}">{{ subject }}</option>
                    {% endfor %}
                </select>

                <label for="question">Your Question</label>
                <textarea id="question" rows="4" maxlength="1000"
                    placeholder="Example: Explain generalization in DBMS..."
                    required></textarea>

                <button class="student-ask-button" type="submit">✦ Ask AI</button>
            </form>

            <div id="chat-status" class="student-muted" role="status"></div>
            <div id="chat-answer" class="student-answer"></div>
            <div id="chat-sources" class="student-sources"></div>
        </section>

        <div id="study-resources"></div>
    </main>
</div>

{% else %}


<div class="professor-layout">
    <aside class="professor-sidebar">
        <div class="professor-brand">EduGraph<span>AI</span></div>
        <p class="professor-subtitle">PROFESSOR WORKSPACE</p>

        <a class="professor-nav active" href="{{ url_for('dashboard') }}">▦ Dashboard</a>
        <a class="professor-nav" href="{{ url_for('professor_materials') }}">↑ Upload Materials</a>
        <a class="professor-nav" href="{{ url_for('professor_materials') }}">▤ My Materials</a>
        <a class="professor-nav" href="{{ url_for('logout') }}">↪ Logout</a>
    </aside>

    <main class="professor-main">
        <header class="professor-topbar">
            <div>
                <h1>Professor Dashboard</h1>
                <p>Manage your academic resources in one place.</p>
            </div>
            <div class="professor-profile">👤 {{ user["name"] }}</div>
        </header>

        <section class="professor-hero">
            <span class="professor-eyebrow">YOUR TEACHING WORKSPACE</span>
            <h2>Welcome back, {{ user["name"] }}! 👋</h2>
            <p>Upload your notes and help students learn smarter with AI.</p>
            <a class="professor-upload-btn" href="{{ url_for('professor_materials') }}">
                + Upload Study Material
            </a>
        </section>

        <section class="professor-stats">
            <div class="professor-stat">
                <div class="professor-stat-icon">📚</div>
                <h3>Study Materials</h3>
                <p>Manage your uploaded PDFs</p>
                <a href="{{ url_for('professor_materials') }}">View materials →</a>
            </div>

            <div class="professor-stat">
                <div class="professor-stat-icon">✨</div>
                <h3>AI-Powered Learning</h3>
                <p>Your indexed notes can help students get answers.</p>
            </div>
        </section>

        <section class="professor-panel">
            <div>
                <h2>Quick Actions</h2>
                <p>Keep your teaching materials organized and accessible.</p>
            </div>
            <a class="professor-action-link" href="{{ url_for('professor_materials') }}">
                <span class="professor-action-icon">📄</span>
                <span>
                    <strong>Upload a new PDF</strong><br>
                    <small>Add notes, assignments or previous year papers</small>
                </span>
                <span>→</span>
            </a>
        </section>
    </main>
</div>


{% endif %}

<script>
document.getElementById("chat-form")?.addEventListener("submit", async function(event) {
    event.preventDefault();

    const question = document.getElementById("question").value.trim();
    const subject = document.getElementById("subject").value;
    const statusBox = document.getElementById("chat-status");
    const answerBox = document.getElementById("chat-answer");
    const sourcesBox = document.getElementById("chat-sources");

    if (!subject || !question) {
        statusBox.textContent = "Please select a subject and enter a question.";
        return;
    }

    statusBox.textContent = "Searching notes. Please wait...";
    answerBox.textContent = "";
    sourcesBox.replaceChildren();

    try {
        const formData = new FormData();
        formData.append("question", question);
        formData.append("subject", subject);

        const response = await fetch("/student/chat", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.answer || data.error || "Request failed.");
        }

        answerBox.textContent = data.answer || "No answer returned.";
        statusBox.textContent = "Answer ready.";

        if (data.sources && data.sources.length > 0) {
            const heading = document.createElement("h3");
            heading.textContent = "📚 Source PDFs";
            sourcesBox.appendChild(heading);

            data.sources.forEach(function(source) {
                const item = document.createElement("div");
                item.style.marginBottom = "16px";

                const title = document.createElement("p");
                title.textContent = source.title + " (" + source.filename + ")";
                item.appendChild(title);

                const pages = document.createElement("p");
                pages.textContent = "Relevant page(s): " + source.pages.join(", ");
                item.appendChild(pages);

                const link = document.createElement("a");
                link.href = source.url + "#page=" + source.pages[0];
                link.target = "_blank";
                link.rel = "noopener";
                link.className = "btn btn-primary";
                link.textContent = "Open Source PDF";
                item.appendChild(link);
                sourcesBox.appendChild(item);
            });
        }
    } catch (error) {
        statusBox.textContent = "Could not get an answer: " + error.message;
    }
});
</script>
</body></html>

    """, heading=heading, description=description,
         user=user, style=PAGE_STYLE, subjects=subjects, materials=materials)



@app.route("/professor/materials", methods=["GET", "POST"])
@login_required
def professor_materials():
    import uuid
    import pymupdf

    with get_db() as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

    if not user or user["role"] != "professor":
        return "Access denied: professors only.", 403

    message = ""

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()

        unit = request.form.get("unit", "").strip()
        material_type = request.form.get(
            "material_type", ""
        ).strip()
        file = request.files.get("pdf")

        if not all([title, subject, unit, material_type, file]):
            message = "Please complete all fields and select a PDF."

        elif material_type not in ("Notes", "Assignment", "PYQ"):
            message = "Please select a valid material type."

        elif not file.filename or not file.filename.lower().endswith(".pdf"):
            message = "Only PDF files are allowed."

        else:
            original_name = secure_filename(file.filename)

            if not original_name:
                message = "Invalid filename."

            else:
                stored_name = f"{uuid.uuid4().hex}.pdf"
                save_path = UPLOAD_FOLDER / stored_name

                try:
                    file.save(save_path)

                    # Check that the PDF can actually be opened.
                    with pymupdf.open(save_path) as pdf:
                        if pdf.page_count == 0:
                            raise ValueError("PDF has no pages.")

                   
                    # Save the material record only after validation.
                    with get_db() as conn:
                        cursor = conn.execute(
                            """
                            INSERT INTO materials (
                                professor_id, title, subject, unit,
                                material_type, filename, stored_filename
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                session["user_id"],
                                title,
                                subject,
                                unit,
                                material_type,
                                original_name,
                                stored_name
                            )
                        )
                        material_id = cursor.lastrowid

                   



                    # Automatically index the PDF for AI search.
                    try:
                        from rag_engine import index_pdf

                        chunk_count = index_pdf(material_id, stored_name)

                        message = (
                            f"PDF uploaded and indexed successfully! "
                            f"{chunk_count} text chunks are ready for AI search."
                        )

                    except Exception:
                        app.logger.exception("PDF indexing failed")
                        message = (
                            "PDF uploaded successfully, but AI indexing failed. "
                            "Check the server terminal for details."
                        )

                    # Build the Knowledge Graph separately.
                    try:
                        from graph_engine import index_pdf_graph

                        graph_count = index_pdf_graph(material_id, stored_name)

                        app.logger.info(
                            "Knowledge Graph created: %s relationships for material %s",
                            graph_count,
                            material_id
                        )

                    except Exception:
                        app.logger.exception("Knowledge Graph indexing failed")

                except Exception:
                    if save_path.exists():
                        save_path.unlink()

                    app.logger.exception("PDF upload failed")
                    message = (
                        "Upload failed. Check the PDF and "
                        "the server terminal for details."
                    )

    with get_db() as conn:
        materials = conn.execute(
            """
            SELECT id, title, subject, unit, material_type,
                   filename, uploaded_at
            FROM materials
            WHERE professor_id = ?
            ORDER BY id DESC
            """,
            (session["user_id"],)
        ).fetchall()


  
    return render_template_string(
        """
        <!doctype html>
        <html>
        <head>

            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1">
            <title>Upload Study Material</title>
            {{ style|safe }}
        </head>
        <body>
            <div class="card">
                <h2>Professor — Upload Material</h2>

                {% if message %}
                    <p class="message">{{ message }}</p>
                {% endif %}

                <form method="post"
                      enctype="multipart/form-data">
                    <label>Material Title</label>
                    <input name="title" required maxlength="150"
                           placeholder="Introduction to NLP">

                    <label>Subject</label>
                    <input name="subject" required maxlength="100"
                           placeholder="Natural Language Processing">

                    <label>Unit</label>
                    <input name="unit" required maxlength="50"
                           placeholder="Unit 1">

                    <label>Material Type</label>
                    <select name="material_type" required>
                        <option value="">Choose type</option>
                        <option value="Notes">Notes</option>
                        <option value="Assignment">Assignment</option>
                        <option value="PYQ">Previous Year Questions</option>
                    </select>

                    <label>Select PDF</label>
                    <input type="file" name="pdf"
                           accept=".pdf,application/pdf" required>

                    <button type="submit">Upload PDF</button>
                </form>

                <hr>
                <h2>Your Uploaded Materials</h2>

                {% for item in materials %}
    <div style="border: 1px solid #ddd; padding: 15px;
                border-radius: 10px; margin: 12px 0;">
        <strong>{{ item["title"] }}</strong><br>
        Subject: {{ item["subject"] }}<br>
        Unit: {{ item["unit"] }}<br>
        Type: {{ item["material_type"] }}<br>
        File: {{ item["filename"] }}<br>
        Uploaded: {{ item["uploaded_at"] }}

        <form method="post"
              action="{{ url_for('delete_material', material_id=item['id']) }}"
              onsubmit="return confirm('Are you sure you want to delete this PDF? This cannot be undone.');"
              style="margin-top: 12px;">
            <button type="submit"
                    style="background: #dc2626; color: white;">
                Delete PDF
            </button>
        </form>
    </div>
{% else %}
    <p>No materials uploaded yet.</p>
{% endfor %}

                <p>
                    <a href="{{ url_for('dashboard') }}">
                        Back to Dashboard
                    </a>
                </p>
            </div>
        </body>
        </html>
        """,
        style=PAGE_STYLE,
        message=message,
        materials=materials
    )
@app.route("/professor/material/<int:material_id>/delete", methods=["POST"])
@login_required
def delete_material(material_id):
    with get_db() as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        if not user or user["role"] != "professor":
            abort(403)

        material = conn.execute(
            """
            SELECT id, stored_filename
            FROM materials
            WHERE id = ? AND professor_id = ?
            """,
            (material_id, session["user_id"])
        ).fetchone()

        if not material:
            abort(404)

        stored_filename = material["stored_filename"]

        # Delete the AI-indexed chunks first.
        conn.execute(
            "DELETE FROM material_chunks WHERE material_id = ?",
            (material_id,)
        )

        # Delete the database record.
        conn.execute(
            "DELETE FROM materials WHERE id = ? AND professor_id = ?",
            (material_id, session["user_id"])
        )

    # Delete the uploaded PDF file.
    file_path = UPLOAD_FOLDER / stored_filename
    if file_path.exists():
        file_path.unlink()

    return redirect(url_for("professor_materials"))


@app.route("/student/chat", methods=["POST"])
@login_required
def student_chat():
    with get_db() as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

    if not user or user["role"] != "student":
        return {"error": "Students only."}, 403

    question = request.form.get("question", "").strip()
    subject = request.form.get("subject", "").strip()

    if not question:
        return {"answer": "Please enter a question."}, 400

    if len(question) > 1000:
        return {
            "answer": "Question is too long. Keep it under 1000 characters."
        }, 400

    if not subject:
        return {"answer": "Please select a subject."}, 400

    try:
        from rag_engine import answer_question, search_materials
        from graph_engine import search_graph

        results = search_materials(
            question,
            top_k=4,
            subject=subject
        )

        if not results:
            return {
                "answer": "No indexed study material was found for this subject.",
                "sources": []
            }, 404

       
        # Search the Knowledge Graph for the materials
        # already retrieved by RAG.
        graph_results = []

        for mid in dict.fromkeys(
            item["material_id"] for item in results
        ):
            try:
                matches = search_graph(
                    question,
                    material_id=mid,
                    limit=6
                )
                graph_results.extend(matches)

            except Exception:
                app.logger.exception(
                    "Knowledge Graph search failed for material %s",
                    mid
                )

        # Generate the answer AFTER graph search finishes.
        answer = answer_question(
            question,
            subject=subject,
            results=results,
            graph_results=graph_results
        )


        material_ids = list(dict.fromkeys(
            item["material_id"] for item in results
        ))

        placeholders = ",".join("?" for _ in material_ids)

        with get_db() as conn:
            rows = conn.execute(
                f"""
                SELECT id, title, filename
                FROM materials
                WHERE id IN ({placeholders})
                """,
                material_ids
            ).fetchall()

        material_lookup = {row["id"]: row for row in rows}
        source_map = {}

        for result in results:
            mid = result["material_id"]
            material = material_lookup.get(mid)

            if material is None:
                continue

            if mid not in source_map:
                source_map[mid] = {
                    "title": material["title"],
                    "filename": material["filename"],
                    "pages": [],
                    "url": url_for("student_pdf", material_id=mid)
                }

            page = result["page_number"]

            if page not in source_map[mid]["pages"]:
                source_map[mid]["pages"].append(page)

        # Include graph evidence pages in the existing sources.
        for item in graph_results:
            mid = item["material_id"]
            source = source_map.get(mid)

            if source is not None:
                page = item["page_number"]

                if page not in source["pages"]:
                    source["pages"].append(page)
        sources = list(source_map.values())

        for source in sources:
            source["pages"].sort()

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception:
        app.logger.exception("Student chatbot failed")
        return {
            "answer": "Sorry, an error occurred. Please check the server terminal.",
            "sources": []
        }, 500


@app.route("/student/material/<int:material_id>")
@login_required
def student_pdf(material_id):
    with get_db() as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        material = conn.execute(
            "SELECT stored_filename FROM materials WHERE id = ?",
            (material_id,)
        ).fetchone()

    if not user or user["role"] != "student":
        abort(403)

    if not material:
        abort(404)

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        material["stored_filename"],
        as_attachment=False
    )




@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
