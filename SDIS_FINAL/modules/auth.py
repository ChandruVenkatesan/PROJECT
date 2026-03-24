"""
modules/auth.py
───────────────
Handles: Login · Register · Logout · Profile · Change Password
Blueprint prefix: /auth
"""

import re
import hashlib
from functools import wraps

from flask import (Blueprint, render_template, request,
                   redirect, session, flash, url_for)
from database.db import get_db_connection

auth_bp = Blueprint("auth", __name__)


# ── Helpers ───────────────────────────────────────────────

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def valid_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

def strong_pw(pw: str) -> bool:
    return len(pw) >= 8 and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw)

def log(user_id, action, detail=""):
    conn = get_db_connection()
    conn.execute("INSERT INTO audit_log (user_id, action, detail) VALUES (?,?,?)",
                 (user_id, action, detail))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("docs.dashboard"))
        return f(*args, **kwargs)
    return wrapper


# ── Login ─────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("docs.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Both fields are required.", "error")
            return render_template("login.html")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND is_active=1", (username,)
        ).fetchone()
        conn.close()

        if user and user["password"] == hash_pw(password):
            session.update({"user_id": user["id"],
                            "username": user["username"],
                            "role": user["role"]})
            log(user["id"], "LOGIN", f"User '{username}' signed in.")
            return redirect(url_for("docs.dashboard"))
        flash("Invalid credentials.", "error")

    return render_template("login.html")


# ── Register ──────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email",    "").strip()
        pw       = request.form.get("password", "")
        pw2      = request.form.get("confirm_password", "")

        if not all([username, email, pw, pw2]):
            flash("All fields are required.", "error")
        elif not valid_email(email):
            flash("Invalid email address.", "error")
        elif pw != pw2:
            flash("Passwords do not match.", "error")
        elif not strong_pw(pw):
            flash("Password needs 8+ chars, 1 uppercase, 1 digit.", "error")
        else:
            conn = get_db_connection()
            try:
                conn.execute(
                    "INSERT INTO users (username, email, password) VALUES (?,?,?)",
                    (username, email, hash_pw(pw))
                )
                conn.commit()
                flash("Account created! Please login.", "success")
                return redirect(url_for("auth.login"))
            except Exception:
                flash("Username or email already exists.", "error")
            finally:
                conn.close()

    return render_template("register.html")


# ── Logout ────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    uid = session.get("user_id")
    uname = session.get("username", "?")
    session.clear()
    if uid:
        log(uid, "LOGOUT", f"'{uname}' signed out.")
    return redirect(url_for("auth.login"))


# ── Profile ───────────────────────────────────────────────

@auth_bp.route("/profile")
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id,username,email,role,created_at FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()
    doc_count = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE user_id=? AND is_deleted=0",
        (session["user_id"],)
    ).fetchone()[0]
    conn.close()
    return render_template("profile.html", user=user, doc_count=doc_count)


# ── Change Password ───────────────────────────────────────

@auth_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    old = request.form.get("old_password", "")
    new = request.form.get("new_password", "")
    cnf = request.form.get("confirm_new", "")

    conn = get_db_connection()
    user = conn.execute("SELECT password FROM users WHERE id=?",
                        (session["user_id"],)).fetchone()

    if user["password"] != hash_pw(old):
        flash("Current password is incorrect.", "error")
    elif new != cnf:
        flash("New passwords do not match.", "error")
    elif not strong_pw(new):
        flash("Password needs 8+ chars, 1 uppercase, 1 digit.", "error")
    else:
        conn.execute("UPDATE users SET password=? WHERE id=?",
                     (hash_pw(new), session["user_id"]))
        conn.commit()
        log(session["user_id"], "CHANGE_PASSWORD")
        flash("Password changed successfully.", "success")

    conn.close()
    return redirect(url_for("auth.profile"))
