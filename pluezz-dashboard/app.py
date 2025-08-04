from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dein_geheimer_schluessel"  # Ändere das zu was Eigenem

# Pfade zu deinen JSON-Dateien
USERS_FILE = "users.json"
ACCOUNTS_FILE = "accounts.json"
PRICES_FILE = "prices.json"

# Lade JSON-Daten
def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

# Speichere JSON-Daten
def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Check Login
def is_logged_in():
    return "username" in session

def is_admin():
    if not is_logged_in():
        return False
    users = load_json(USERS_FILE)
    username = session["username"]
    return users.get(username, {}).get("admin", False)

@app.route("/")
def index():
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        users = load_json(USERS_FILE)
        user = users.get(username)
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            flash("Erfolgreich eingeloggt!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Falscher Benutzername oder Passwort", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Erfolgreich ausgeloggt.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))
    # Beispiel: zeige Lagerstatus
    accounts = load_json(ACCOUNTS_FILE)
    status = {}
    for dienst, daten in accounts.items():
        status[dienst] = len(daten)
    return render_template("dashboard.html", status=status)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not is_admin():
        flash("Kein Zugriff!", "error")
        return redirect(url_for("login"))

    accounts = load_json(ACCOUNTS_FILE)
    users = load_json(USERS_FILE)
    dienste = list(accounts.keys()) if accounts else []

    # Lagerstatus
    status = {}
    for dienst, daten in accounts.items():
        anzahl = len(daten)
        if anzahl == 0:
            status[dienst] = "Leer"
        elif anzahl < 5:
            status[dienst] = "Nachschub nötig"
        elif anzahl < 10:
            status[dienst] = "Knapp"
        else:
            status[dienst] = "Auf Lager"

    if request.method == "POST":
        if "add_account" in request.form:
            dienst = request.form["dienst"]
            daten_text = request.form["daten"].strip()
            if dienst and daten_text:
                neue_accounts = [line.strip() for line in daten_text.splitlines() if line.strip()]
                if dienst not in accounts:
                    accounts[dienst] = []
                accounts[dienst].extend(neue_accounts)
                save_json(ACCOUNTS_FILE, accounts)
                flash(f"{len(neue_accounts)} Accounts zu {dienst} hinzugefügt.", "success")
                return redirect(url_for("admin"))

        elif "add_user" in request.form:
            username = request.form["username"].strip()
            password = request.form["password"].strip()
            admin_rechte = "admin" in request.form
            if username and password:
                if username in users:
                    flash("Benutzer existiert schon.", "error")
                else:
                    hashed_pw = generate_password_hash(password)
                    users[username] = {"password": hashed_pw, "admin": admin_rechte}
                    save_json(USERS_FILE, users)
                    flash(f"Benutzer {username} erstellt.", "success")
                    return redirect(url_for("admin"))

    return render_template("admin.html", status=status, dienste=dienste)

if __name__ == "__main__":
    app.run(debug=True)
