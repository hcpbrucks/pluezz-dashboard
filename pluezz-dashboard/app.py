import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash

BASE_DIR = os.getcwd()

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "Pluezzzzshop")

# Alle Dienste
ALLE_DIENSTE = [
    "Netflix", "Spotify Single Account", "Disney", "Dazn", "Paramount", "Prime-Video",
    "YouTube-Premium Family", "YouTube-Premium Single Account", "Crunchyroll Fan Account",
    "Crunchyroll Megafan Account", "Steam 0-3 Random Games", "Steam 4+ Random Games",
    "Steam Account with Eurotruck Simulator 2", "Steam Account with Wallpaper Engine",
    "Steam Account with Counter Strike", "Steam Account with Rainbow Six",
    "Steam Account with Supermarket Simulator", "Steam Account with Red Dead Redemption 2",
    "Steam Account with FC 25", "Steam Account with Schedule 1", "GTA Activation Key",
    "Server-Member 500", "Server-Member 1000", "Server-Boost 14x 1 Monat",
    "Server-Boost 14x 3 Monate", "Nord-Vpn", "CapCut-Pro", "Canva",
    "Adobe-Creative-Cloud 1 Monat Key", "Adobe-Creative-Cloud Livetime Account"
]

def json_laden(dateiname):
    pfad = os.path.join(BASE_DIR, dateiname)
    if not os.path.exists(pfad):
        return []
    with open(pfad, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def json_speichern(dateiname, daten):
    with open(os.path.join(BASE_DIR, dateiname), "w") as f:
        json.dump(daten, f, indent=4)

def log_speichern(user, aktion):
    logs = json_laden("logs.json")
    logs.append({
        "user": user,
        "aktion": aktion,
        "zeit": datetime.now().strftime("%d.%m.%Y %H:%M")
    })
    json_speichern("logs.json", logs)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Login über Umgebungsvariablen (Paul + Elias)
        env_users = {
            "Paul": os.environ.get("PAUL_PASSWORD"),
            "Elias": os.environ.get("ELIAS_PASSWORD")
        }

        if username in env_users and password == env_users[username]:
            session["user"] = username
            session["admin"] = True  # Beide sind Admin
            return redirect("/start")

        # Login über users.json (für manuell erstellte User)
        users = json_laden("users.json")
        for user in users:
            if user["name"] == username and user["password"] == password:
                session["user"] = user["name"]
                session["admin"] = user.get("admin", False)
                return redirect("/start")

        flash("Login fehlgeschlagen!")
    return render_template("login.html")

@app.route("/start", methods=["GET", "POST"])
def start():
    if "user" not in session:
        return redirect("/")
    accounts = json_laden("accounts.json")
    ausgabe = []
    if request.method == "POST":
        dienst = request.form["dienst"]
        anzahl = int(request.form["anzahl"])
        loeschen = request.form.get("loeschen") == "on"
        if dienst in accounts and len(accounts[dienst]) >= anzahl:
            ausgabe = accounts[dienst][:anzahl]
            if loeschen:
                accounts[dienst] = accounts[dienst][anzahl:]
                json_speichern("accounts.json", accounts)
                log_speichern(session["user"], f"{anzahl}x {dienst} abgerufen & gelöscht")
            else:
                log_speichern(session["user"], f"{anzahl}x {dienst} abgerufen (nicht gelöscht)")
    return render_template("dienst.html", dienste=ALLE_DIENSTE, ausgabe=ausgabe)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    if not session.get("admin", False):
        return redirect("/start")
    accounts = json_laden("accounts.json")
    stock = {dienst: len(accounts.get(dienst, [])) for dienst in ALLE_DIENSTE}
    return render_template("dashboard.html", stock=stock)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")
    accounts = json_laden("accounts.json")
    status = {}
    for dienst in ALLE_DIENSTE:
        menge = len(accounts.get(dienst, []))
        if menge == 0:
            st = "❌ Leer"
        elif menge < 5:
            st = "🔴 Nachschub nötig"
        elif menge <= 10:
            st = "🟠 Knapp"
        else:
            st = "🟢 Auf Lager"
        status[dienst] = f"{menge} ({st})"
    return render_template("admin.html", status=status)

@app.route("/admin/logs")
def logs():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")
    logs = json_laden("logs.json")
    return render_template("logs.html", logs=logs)

@app.route("/admin/add_account", methods=["POST"])
def add_account():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")
    dienst = request.form["dienst"]
    daten = request.form["daten"]
    neu = daten.strip().splitlines()
    accounts = json_laden("accounts.json")
    accounts.setdefault(dienst, []).extend(neu)
    json_speichern("accounts.json", accounts)
    log_speichern(session["user"], f"{len(neu)}x {dienst} hinzugefügt")
    return redirect("/admin")

@app.route("/admin/add_user", methods=["POST"])
def add_user():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")
    users = json_laden("users.json")
    users.append({
        "name": request.form["username"],
        "password": request.form["password"],
        "admin": request.form.get("admin") == "on"
    })
    json_speichern("users.json", users)
    log_speichern(session["user"], f"Neuer User {request.form['username']} hinzugefügt")
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
