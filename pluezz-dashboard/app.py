from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dein-geheimer-schluessel")

# Beispiel-Nutzer mit gehashten Passwörtern
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

dienste = [
  "Netflix",
  "Spotify",
  "Disney",
  "Dazn",
  "Paramount",
  "Prime-Video",
  "YouTube-Premium Family",
  "YouTube-Premium Single Account",
  "Crunchyroll Fan Account",
  "Crunchyroll Megafan Account",
  "Steam 0-3 Random Games",
  "Steam 4+ Random Games",
  "Steam Eurotruck Simulator 2",
  "Steam Wallpaper Engine",
  "Steam Counter Strike",
  "Steam Rainbow Six",
  "Steam Supermarket Simulator",
  "Steam Red Dead Redemption 2",
  "Steam Fc 25",
  "Steam Schedule 1",
  "GTA-activation-Key",
  "Server-Member 500",
  "Server-Member 1000",
  "Server-Boost 14x 1 Monat",
  "Server-Boost 14x 3 Monate",
  "Nord-Vpn",
  "CapCut-Pro",
  "Canva",
  "Adobe-Creative-Cloud 1 Monat key",
  "Adobe-Creative-Cloud Livetime Account"
]

def load_accounts():
    try:
        with open("accounts.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {dienst: [] for dienst in dienste}

def save_accounts(accounts):
    with open("accounts.json", "w") as f:
        json.dump(accounts, f, indent=4)

@app.route("/")
def home():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").lower()
        password = request.form.get("password", "")
        user = users.get(username)
        if user and check_password_hash(user["password"], password):
            session["user"] = username
            session["admin"] = user.get("admin", False)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Falscher Benutzername oder Passwort.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect(url_for("login"))

    accounts = load_accounts()
    status = {dienst: len(accounts.get(dienst, [])) for dienst in dienste}
    return render_template("dashboard.html", user=session["user"], admin=session.get("admin", False), status=status)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("user") or not session.get("admin"):
        flash("Du hast keine Berechtigung für diesen Bereich.")
        return redirect(url_for("login"))

    accounts = load_accounts()
    status = {dienst: len(accounts.get(dienst, [])) for dienst in dienste}

    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            dienst = data.get("dienst")
            account = data.get("account")
            if dienst and account and dienst in accounts:
                if account in accounts[dienst]:
                    accounts[dienst].remove(account)
                    save_accounts(accounts)
                    return jsonify({"success": True})
            return jsonify({"success": False, "error": "Account oder Dienst nicht gefunden"}), 400
        else:
            flash("Ungültige Anfrage.")
            return redirect(url_for("admin"))

    return render_template("admin.html", status=status, dienste=dienste)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
