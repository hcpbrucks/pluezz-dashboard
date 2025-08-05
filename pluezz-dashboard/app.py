from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import json
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dein-geheimer_schluessel")

dienste = [
    "Netflix", "Spotify", "Disney", "Dazn", "Paramount", "Prime-Video",
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

def load_json_safe(filename, default):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    users = load_json_safe(USERS_FILE, {})
    paul_pw = os.getenv("PAUL_PASSWORD")
    elias_pw = os.getenv("ELIAS_PASSWORD")

    if paul_pw and "paul" not in users:
        users["paul"] = {"password": paul_pw, "admin": True}
    if elias_pw and "elias" not in users:
        users["elias"] = {"password": elias_pw, "admin": True}

    save_json(USERS_FILE, users)
    return users

def save_users(users):
    save_json(USERS_FILE, users)

def load_accounts():
    # Struktur: {dienst: [ {service, email, password}, ... ], ... }
    return load_json_safe(ACCOUNTS_FILE, {dienst: [] for dienst in dienste})

def save_accounts(accounts):
    save_json(ACCOUNTS_FILE, accounts)

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST", "HEAD"])
def login():
    if request.method == "HEAD":
        return ""

    if "user" in session:
        return redirect(url_for("dashboard"))  # Direkt zum Dashboard, wenn schon eingeloggt

    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = load_users()

        user = users.get(username)
        if user and user["password"] == password:
            session["user"] = username
            session["admin"] = user.get("admin", False)
            return redirect(url_for("dashboard"))
        else:
            error = "Ungültiger Benutzername oder Passwort."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    accounts = load_accounts()
    status = {dienst: len(accounts.get(dienst, [])) for dienst in dienste}
    return render_template("dashboard.html", status=status, dienste=dienste)

@app.route("/dienst/<dienst>", methods=["GET", "POST"])
def dienst(dienst):
    if "user" not in session:
        return redirect(url_for("login"))
    if dienst not in dienste:
        abort(404)

    accounts = load_accounts()
    dienst_accounts = accounts.get(dienst, [])
    ausgewählte_accounts = []

    if request.method == "POST":
        if "abrufen" in request.form:
            try:
                anzahl = int(request.form.get("anzahl", 1))
                if anzahl < 1:
                    anzahl = 1
            except ValueError:
                anzahl = 1
            ausgewählte_accounts = dienst_accounts[:anzahl]

        elif "loesche_index" in request.form:
            try:
                index = int(request.form.get("loesche_index"))
                if 0 <= index < len(dienst_accounts):
                    gelöscht = dienst_accounts.pop(index)
                    accounts[dienst] = dienst_accounts
                    save_accounts(accounts)
                    flash(f"Account gelöscht: {gelöscht}")
            except (ValueError, IndexError):
                flash("Fehler beim Löschen.")
            try:
                zuletzt_anzahl = int(request.form.get("anzahl_alt", 1))
                ausgewählte_accounts = dienst_accounts[:zuletzt_anzahl]
            except ValueError:
                ausgewählte_accounts = dienst_accounts
    else:
        ausgewählte_accounts = []

    return render_template("dienst.html", dienst=dienst, accounts=ausgewählte_accounts)

# Route für Account-Löschen aus dashboard oder dienst-Seite
@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "user" not in session:
        return redirect(url_for("login"))
    if not session.get("admin"):
        flash("Du hast keine Berechtigung dafür.")
        return redirect(url_for("dashboard"))

    service = request.form.get("service")
    email = request.form.get("email")

    if not service or not email:
        flash("Ungültige Daten zum Löschen.")
        return redirect(url_for("dashboard"))

    accounts = load_accounts()
    dienst_accounts = accounts.get(service, [])

    # Suche und lösche Account mit passender Email
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
    if "user" not in session or not session.get("admin"):
        flash("Du hast keine Berechtigung für diesen Bereich.")
        return redirect(url_for("login"))

    accounts = load_accounts()
    users = load_users()

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

        if action == "add_account":
            dienst_name = request.form.get("dienst")
            email = request.form.get("email")
            password = request.form.get("password")

            if dienst_name in dienste and email and password:
                acc_obj = {
                    "service": dienst_name,
                    "email": email,
                    "password": password
                }
                accounts.setdefault(dienst_name, []).append(acc_obj)
                save_accounts(accounts)
                flash(f"Account zu {dienst_name} hinzugefügt.")
            else:
                flash("Bitte Dienst, E-Mail und Passwort korrekt angeben.", "error")

        elif action == "add_user":
            username = request.form.get("username")
            password = request.form.get("password")
            admin_flag = request.form.get("admin") == "on"
            if username and password:
                if username in users:
                    flash("Benutzername existiert bereits.", "error")
                else:
                    users[username] = {"password": password, "admin": admin_flag}
                    save_users(users)
                    flash(f"Benutzer {username} hinzugefügt.")
            else:
                flash("Ungültige Eingabe beim Hinzufügen eines Benutzers.", "error")

        return redirect(url_for("admin"))

    return render_template("admin.html", status=status, dienste=dienste, users=users)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
