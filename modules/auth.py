"""
modules/auth.py
───────────────
Login · Register · Logout · Profile · Change Password
Blueprint prefix: /auth
"""

import re
import hashlib
from functools import wraps
from flask import (Blueprint, render_template, request,
                   redirect, session, flash, url_for)
from database.db import get_db_connection, log_action

auth_bp = Blueprint("auth", __name__)


# ── Helpers ───────────────────────────────────────────────

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

def strong_pw(pw):
    return (len(pw) >= 8
            and any(c.isupper() for c in pw)
            and any(c.isdigit() for c in pw))

def _fix_dates(row):
    if row is None:
        return None
    return {k: (str(v) if hasattr(v, 'strftime') else v) for k, v in row.items()}

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
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND is_active=1",
            (username,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and user["password"] == hash_pw(password):
            session.update({
                "user_id":  user["id"],
                "username": user["username"],
                "role":     user["role"]
            })
            log_action(user["id"], "LOGIN", f"'{username}' signed in.")
            return redirect(url_for("docs.dashboard"))

        flash("Invalid username or password.", "error")

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
            flash("Password needs 8+ chars, 1 uppercase letter, 1 digit.", "error")
        else:
            conn = get_db_connection()
            cur  = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s,%s,%s)",
                    (username, email, hash_pw(pw))
                )
                conn.commit()
                flash("Account created! Please login.", "success")
                return redirect(url_for("auth.login"))
            except Exception:
                flash("Username or email already exists.", "error")
            finally:
                cur.close()
                conn.close()

    return render_template("register.html")


# ── Logout ────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    uid   = session.get("user_id")
    uname = session.get("username", "?")
    session.clear()
    if uid:
        log_action(uid, "LOGOUT", f"'{uname}' signed out.")
    return redirect(url_for("auth.login"))


# ── Profile ───────────────────────────────────────────────

@auth_bp.route("/profile")
@login_required
def profile():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, username, email, role, created_at FROM users WHERE id=%s",
        (session["user_id"],)
    )
    user = _fix_dates(cur.fetchone())
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM documents WHERE user_id=%s AND is_deleted=0",
        (session["user_id"],)
    )
    doc_count = cur.fetchone()["cnt"]
    cur.close()
    conn.close()
    return render_template("profile.html", user=user, doc_count=doc_count)


# ── Change Password ───────────────────────────────────────

@auth_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    old = request.form.get("old_password", "")
    new = request.form.get("new_password", "")
    cnf = request.form.get("confirm_new",  "")

    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT password FROM users WHERE id=%s", (session["user_id"],))
    user = cur.fetchone()

    if user["password"] != hash_pw(old):
        flash("Current password is incorrect.", "error")
    elif new != cnf:
        flash("New passwords do not match.", "error")
    elif not strong_pw(new):
        flash("Password needs 8+ chars, 1 uppercase, 1 digit.", "error")
    else:
        cur.execute(
            "UPDATE users SET password=%s WHERE id=%s",
            (hash_pw(new), session["user_id"])
        )
        conn.commit()
        log_action(session["user_id"], "CHANGE_PASSWORD")
        flash("Password changed successfully.", "success")

    cur.close()
    conn.close()
    return redirect(url_for("auth.profile"))