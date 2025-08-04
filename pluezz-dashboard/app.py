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

ALLE_DIENSTE = [
    "Netflix", "Spotify", "Disney", "Dazn", "Paramount", "Prime-Video",
    "YouTube-Premium", "Crunchyroll", "Steam", "GTA Activation Key",
    "NordVPN", "CapCut-Pro", "Canva", "Adobe Creative Cloud"
]

def json_laden(dateiname):
    pfad = os.path.join(BASE_DIR, dateiname)
    if not os.path.exists(pfad):
        return {}
    with open(pfad, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def json_speichern(dateiname, daten):
    with open(os.path.join(BASE_DIR, dateiname), "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)

def log_speichern(user, aktion):
    logs = json_laden("logs.json")
    if not isinstance(logs, list):
        logs = []
    logs.append({
        "user": user,
        "aktion": aktion,
        "zeit": datetime.now().strftime("%d.%m.%Y %H:%M")
    })
    json_speichern("logs.json", logs)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = json_laden("users.json")
        for user in users.get("users", []):
            if user["name"] == username and user["password"] == password:
                session["user"] = user["name"]
                session["admin"] = user.get("admin", False)
                log_speichern(username, "Erfolgreich eingeloggt")
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
        dienst = request.form.get("dienst")
        anzahl = int(request.form.get("anzahl", 0))
        loeschen = request.form.get("loeschen") == "on"

        if dienst in accounts and len(accounts[dienst]) >= anzahl > 0:
            ausgabe = accounts[dienst][:anzahl]
            if loeschen:
                accounts[dienst] = accounts[dienst][anzahl:]
                json_speichern("accounts.json", accounts)
                log_speichern(session["user"], f"{anzahl}x {dienst} abgerufen & gelöscht")
            else:
                log_speichern(session["user"], f"{anzahl}x {dienst} abgerufen (nicht gelöscht)")
        else:
            flash("Nicht genug Accounts verfügbar oder ungültige Anzahl!")

    return render_template("start.html", dienste=ALLE_DIENSTE, ausgabe=ausgabe)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")

    accounts = json_laden("accounts.json")
    if request.method == "POST":
        dienst = request.form.get("dienst")
        account_text = request.form.get("account")

        if dienst and account_text:
            if dienst not in accounts:
                accounts[dienst] = []
            accounts[dienst].append(account_text.strip())
            json_speichern("accounts.json", accounts)
            log_speichern(session["user"], f"Account zu {dienst} hinzugefügt")
            flash(f"Account zu {dienst} hinzugefügt.")
        else:
            flash("Bitte Dienst und Account angeben.")

    return render_template("admin.html", dienste=ALLE_DIENSTE)

@app.route("/admin/logs")
def logs():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")
    logs = json_laden("logs.json")
    if not isinstance(logs, list):
        logs = []
    logs.sort(key=lambda x: x["zeit"], reverse=True)
    return render_template("logs.html", logs=logs)

@app.route("/logout")
def logout():
    user = session.get("user", "Unbekannt")
    session.clear()
    log_speichern(user, "Ausgeloggt")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
