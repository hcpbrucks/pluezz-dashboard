import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dein_geheimer_schluessel")

# Liste der Dienste (Produkte)
dienste = [
    "Netflix", "Spotify", "Disney+", "Dazn", "Paramount", "Prime-Video",
    "YouTube-Premium Family", "YouTube-Premium Single Account",
    "Crunchyroll Fan Account", "Crunchyroll Megafan Account",
    "Steam 0-3 Random Games", "Steam 4+ Random Games",
    "Steam Eurotruck Simulator 2", "Steam Wallpaper Engine", "Steam Counter Strike",
    "Steam Rainbow Six", "Steam Supermarket Simulator", "Steam Red Dead Redemption 2",
    "Steam Fc 25", "Steam Schedule 1", "GTA-activation-Key", "Server-Member 500",
    "Server-Member 1000", "Server-Boost 14x 1 Monat", "Server-Boost 14x 3 Monate",
    "Nord-Vpn", "CapCut-Pro", "Canva", "Adobe-Creative-Cloud 1 Monat key",
    "Adobe-Creative-Cloud Livetime Account"
]

USERS_FILE = "users.json"
ACCOUNTS_FILE = "accounts.json"

# --- Hilfsfunktionen zum Laden und Speichern der JSON-Daten ---

def load_json_safe(filename, default):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Benutzerverwaltung ---

def load_users():
    users = load_json_safe(USERS_FILE, {})

    # Falls Umgebungsvariablen gesetzt, Admins hinzufügen (z.B. Paul, Elias)
    paul_pw = os.getenv("PAUL_PASSWORD")
    elias_pw = os.getenv("ELIAS_PASSWORD")

    changed = False
    if paul_pw and "paul" not in users:
        users["paul"] = {
            "password": generate_password_hash(paul_pw),
            "admin": True
        }
        changed = True
    if elias_pw and "elias" not in users:
        users["elias"] = {
            "password": generate_password_hash(elias_pw),
            "admin": True
        }
        changed = True

    if changed:
        save_users(users)

    return users

def save_users(users):
    save_json(USERS_FILE, users)

# --- Accountverwaltung ---

def load_accounts():
    data = load_json_safe(ACCOUNTS_FILE, None)
    if data is None or not isinstance(data, dict):
        return {dienst: [] for dienst in dienste}
    # Fehlende Dienste ergänzen
    for d in dienste:
        if d not in data:
            data[d] = []
    return data

def save_accounts(accounts):
    save_json(ACCOUNTS_FILE, accounts)

# --- Session Checks ---

def is_logged_in():
    return "username" in session

def is_admin():
    return session.get("admin", False)

# --- Routen ---

@app.route("/")
def home():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        user = users.get(username)

        if user and check_password_hash(user["password"], password):
            session["username"] = username
            session["admin"] = user.get("admin", False)
            flash(f"Willkommen, {username}!")
            return redirect(url_for("dashboard"))
        else:
            error = "Ungültiger Benutzername oder Passwort."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    flash("Erfolgreich ausgeloggt.")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))
    accounts = load_accounts()
    status = {dienst: len(accounts.get(dienst, [])) for dienst in dienste}
    return render_template("dashboard.html", status=status, dienste=dienste)

@app.route("/dienst/<dienst>", methods=["GET", "POST"])
def dienst(dienst):
    if not is_logged_in():
        return redirect(url_for("login"))
    if dienst not in dienste:
        abort(404)

    accounts = load_accounts()
    dienst_accounts = accounts.get(dienst, [])
    ausgewaehlte_accounts = dienst_accounts[:]  # Standard: alle anzeigen

    if request.method == "POST":
        if "abrufen" in request.form:
            try:
                anzahl = int(request.form.get("anzahl", 1))
                if anzahl < 1:
                    anzahl = 1
            except ValueError:
                anzahl = 1
            ausgewaehlte_accounts = dienst_accounts[:anzahl]

        elif "loesche_index" in request.form and is_admin():
            try:
                index = int(request.form.get("loesche_index"))
                if 0 <= index < len(dienst_accounts):
                    geloescht = dienst_accounts.pop(index)
                    accounts[dienst] = dienst_accounts
                    save_accounts(accounts)
                    flash(f"Account gelöscht: {geloescht}")
            except (ValueError, IndexError):
                flash("Fehler beim Löschen.")
            try:
                zuletzt_anzahl = int(request.form.get("anzahl_alt", len(dienst_accounts)))
                ausgewaehlte_accounts = dienst_accounts[:zuletzt_anzahl]
            except ValueError:
                ausgewaehlte_accounts = dienst_accounts

    return render_template("dienst.html", dienst=dienst, accounts=ausgewaehlte_accounts)

@app.route("/add_account", methods=["POST"])
def add_account():
    if not is_logged_in() or not is_admin():
        flash("Du hast keine Berechtigung dafür.")
        return redirect(url_for("login"))

    dienst_name = request.form.get("dienst")
    email = request.form.get("email")
    password = request.form.get("password")

    if dienst_name in dienste and email and password:
        accounts = load_accounts()
        acc_obj = {"email": email, "password": password}
        accounts.setdefault(dienst_name, []).append(acc_obj)
        save_accounts(accounts)
        flash(f"Account für {dienst_name} hinzugefügt.")
        return redirect(url_for("dienst", dienst=dienst_name))
    else:
        flash("Bitte Dienst, E-Mail und Passwort korrekt angeben.", "error")
        return redirect(url_for("dashboard"))

@app.route("/delete_account", methods=["POST"])
def delete_account():
    if not is_logged_in() or not is_admin():
        flash("Du hast keine Berechtigung dafür.")
        return redirect(url_for("login"))

    service = request.form.get("service")
    email = request.form.get("email")

    if not service or not email:
        flash("Ungültige Daten zum Löschen.")
        return redirect(url_for("dashboard"))

    accounts = load_accounts()
    dienst_accounts = accounts.get(service, [])
    neu_accounts = [acc for acc in dienst_accounts if acc.get("email") != email]

    if len(neu_accounts) == len(dienst_accounts):
        flash("Account nicht gefunden oder bereits gelöscht.", "error")
    else:
        accounts[service] = neu_accounts
        save_accounts(accounts)
        flash(f"Account für {email} bei {service} gelöscht.")

    return redirect(url_for("dashboard"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not is_logged_in() or not is_admin():
        flash("Zugriff nur für Admins!")
        return redirect(url_for("login"))

    users = load_users()
    accounts = load_accounts()

    # Status je Dienst (Anzahl und Ampel)
    status = {}
    for dienst in dienste:
        count = len(accounts.get(dienst, []))
        if count > 10:
            icon = "🟢"
        elif 5 <= count <= 10:
            icon = "🟠"
        elif 1 <= count < 5:
            icon = "🔴"
        else:
            icon = "❌"
        status[dienst] = {"count": count, "icon": icon}

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_user":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            admin_flag = request.form.get("admin") == "on"
            if username and password:
                if username in users:
                    flash("Benutzername existiert bereits.", "error")
                else:
                    users[username] = {
                        "password": generate_password_hash(password),
                        "admin": admin
                    }
