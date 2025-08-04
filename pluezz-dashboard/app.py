import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dein-geheimer-schluessel")

# Nutzer laden (Passwörter aus Umgebungsvariablen)
users = {
    "paul": {
        "password": generate_password_hash(os.getenv("PAUL_PASSWORD", "paulpass")),
        "admin": True
    },
    "elias": {
        "password": generate_password_hash(os.getenv("ELIAS_PASSWORD", "eliaspass")),
        "admin": False
    }
}

# Dienste-Liste (für Dropdown)
dienste = [
    "netflix", "spotify", "disneyplus", "gta", "crunchyroll", "youtubepremium",
    "dazn", "nordvpn", "primevideo", "capcutpro", "chatgptplus", "steam",
    "adobecc", "canvapremium", "paramountplus"
]

# Lade accounts.json (oder leeres dict)
def load_accounts():
    try:
        with open("accounts.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Speichere accounts.json
def save_accounts(accounts):
    with open("accounts.json", "w") as f:
        json.dump(accounts, f, indent=4)

# Lade users.json (für Admin neu hinzufügen)
def load_users_file():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Speichere users.json (zusätzlich zu in-memory users)
def save_users_file(users_file):
    with open("users.json", "w") as f:
        json.dump(users_file, f, indent=4)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").lower()
        password = request.form.get("password")
        
        # Zuerst check im hardcodierten users dict (env)
        user = users.get(username)
        
        # Wenn nicht gefunden, check in users.json (für neue user)
        if not user:
            users_file = load_users_file()
            if username in users_file:
                user = users_file[username]
        
        if user and check_password_hash(user["password"], password):
            session["user"] = username
            session["admin"] = user.get("admin", False)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Falscher Benutzername oder Passwort.")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"], admin=session["admin"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("user") or not session.get("admin"):
        flash("Du hast keine Berechtigung für diesen Bereich.")
        return redirect(url_for("login"))
    
    accounts = load_accounts()
    users_file = load_users_file()

    # Lagerstatus: zähle Accounts pro Dienst
    status = {dienst: len(accounts.get(dienst, [])) for dienst in dienste}

    if request.method == "POST":
        if "add_account" in request.form:
            dienst = request.form.get("dienst")
            daten = request.form.get("daten").strip()
            if dienst and daten:
                neue_accounts = [line.strip() for line in daten.splitlines() if line.strip()]
                if dienst not in accounts:
                    accounts[dienst] = []
                accounts[dienst].extend(neue_accounts)
                save_accounts(accounts)
                flash(f"{len(neue_accounts)} Accounts für {dienst} hinzugefügt.")
                return redirect(url_for("admin"))

        elif "add_user" in request.form:
            username = request.form.get("username").lower()
            password = request.form.get("password")
            admin_rechte = bool(request.form.get("admin"))
            if username and password:
                if username in users or username in users_file:
                    flash("Benutzer existiert bereits.")
                else:
                    hashed_pw = generate_password_hash(password)
                    users_file[username] = {"password": hashed_pw, "admin": admin_rechte}
                    save_users_file(users_file)
                    flash(f"Benutzer {username} erfolgreich erstellt.")
                return redirect(url_for("admin"))

    return render_template("admin.html", status=status, dienste=dienste)

if __name__ == "__main__":
    app.run(debug=True)
