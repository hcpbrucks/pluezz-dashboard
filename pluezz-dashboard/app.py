import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = 'Pluezzzzshop'

ALLE_DIENSTE = [
    "Netflix",
    "Spotify Single Account",
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
    "Steam Account with Eurotruck Simulator 2",
    "Steam Account with Wallpaper Engine",
    "Steam Account with Counter Strike",
    "Steam Account with Rainbow Six",
    "Steam Account with Supermarket Simulator",
    "Steam Account with Red Dead Redemption 2",
    "Steam Account with FC 25",
    "Steam Account with Schedule 1",
    "GTA Activation Key",
    "Server-Member 500",
    "Server-Member 1000",
    "Server-Boost 14x 1 Monat",
    "Server-Boost 14x 3 Monate",
    "Nord-Vpn",
    "CapCut-Pro",
    "Canva",
    "Adobe-Creative-Cloud 1 Monat Key",
    "Adobe-Creative-Cloud Livetime Account"
]

def load_json(path):
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        return []
    with open(full_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(path, data):
    with open(os.path.join(BASE_DIR, path), "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    return load_json("users.json")

def save_users(data):
    save_json("users.json", data)

def load_accounts():
    data = load_json("accounts.json")
    return data if isinstance(data, dict) else {}

def save_accounts(data):
    save_json("accounts.json", data)

def load_prices():
    return load_json("prices.json")

@app.route("/", methods=["GET", "POST", "HEAD"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        pw = request.form["password"]
        users = load_users()
        for user in users:
            if user["name"] == name and user["password"] == pw:
                session["user"] = name
                session["admin"] = user.get("admin", False)
                return redirect(url_for("dashboard"))
        flash("Login fehlgeschlagen")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    accounts = load_accounts()
    stock = {}
    for dienst in ALLE_DIENSTE:
        if dienst in accounts and isinstance(accounts[dienst], list):
            stock[dienst] = len(accounts[dienst])
        else:
            stock[dienst] = 0
    return render_template("dashboard.html", stock=stock, is_admin=session.get("admin", False))

@app.route("/dienst/<dienst>", methods=["GET", "POST"])
def dienst_view(dienst):
    if "user" not in session:
        return redirect(url_for("login"))
    accounts = load_accounts()
    if dienst not in accounts:
        flash("Dienst nicht gefunden")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        try:
            anzahl = int(request.form["anzahl"])
        except (ValueError, KeyError):
            flash("Ungültige Anzahl")
            return redirect(url_for("dienst_view", dienst=dienst))

        if 0 < anzahl <= len(accounts[dienst]):
            ausgabe = accounts[dienst][:anzahl]
            return render_template("dienst.html", dienst=dienst, ausgabe=ausgabe, max=len(accounts[dienst]))
        else:
            flash("Nicht genug Accounts auf Lager oder ungültige Anzahl")
            return redirect(url_for("dienst_view", dienst=dienst))

    return render_template("dienst.html", dienst=dienst, ausgabe=None, max=len(accounts.get(dienst, [])))

@app.route("/dienst/<dienst>/delete_account", methods=["POST"])
def delete_account(dienst):
    if "user" not in session:
        return redirect(url_for("login"))
    account_to_delete = request.form.get("account")
    if not account_to_delete:
        flash("Kein Account angegeben zum Löschen.")
        return redirect(url_for("dienst_view", dienst=dienst))
    accounts = load_accounts()
    if dienst in accounts and account_to_delete in accounts[dienst]:
        accounts[dienst].remove(account_to_delete)
        save_accounts(accounts)
        flash(f"Account '{account_to_delete}' wurde gelöscht.")
    else:
        flash("Account nicht gefunden.")
    return redirect(url_for("dienst_view", dienst=dienst))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or not session.get("admin", False):
        return redirect(url_for("login"))
    accounts = load_accounts()
    status = {}
    for dienst, daten in accounts.items():
        menge = len(daten)
        if menge == 0:
            s = "❌ Leer"
        elif menge < 5:
            s = "🔴 Nachschub nötig"
        elif menge <= 10:
            s = "🟠 Knapp"
        else:
            s = "🟢 Auf Lager"
        status[dienst] = f"{menge} ({s})"
    return render_template("admin.html", status=status)

@app.route("/admin/add_account", methods=["POST"])
def add_account():
    if "user" not in session or not session.get("admin", False):
        return redirect(url_for("login"))
    dienst = request.form["dienst"]
    daten = request.form["daten"]
    accounts = load_accounts()
    neu = daten.strip().splitlines()
    accounts.setdefault(dienst, []).extend(neu)
    save_accounts(accounts)
    flash("Account(s) hinzugefügt")
    return redirect(url_for("admin"))

@app.route("/admin/add_user", methods=["POST"])
def add_user():
    if "user" not in session or not session.get("admin", False):
        return redirect(url_for("login"))
    name = request.form["username"]
    pw = request.form["password"]
    admin_flag = request.form.get("admin") == "on"
    users = load_users()
    users.append({"name": name, "password": pw, "admin": admin_flag})
    save_users(users)
    flash("Nutzer hinzugefügt")
    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
