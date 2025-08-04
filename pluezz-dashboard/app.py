import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for

BASE_DIR = os.getcwd()

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "Pluezzzzshop")

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
        if dateiname == "accounts.json":
            # Bei accounts.json immer ein dict zurückgeben
            return {}
        else:
            return []
    with open(pfad, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            if dateiname == "accounts.json":
                return {}
            else:
                return []

def json_speichern(dateiname, daten):
    with open(os.path.join(BASE_DIR, dateiname), "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)

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

        env_users = {
            "Paul": os.environ.get("PAUL_PASSWORD"),
            "Elias": os.environ.get("ELIAS_PASSWORD")
        }

        if username in env_users and password == env_users[username]:
            session["user"] = username
            session["admin"] = True
            log_speichern(username, "Erfolgreich eingeloggt")
            return redirect("/dienst")

        users = json_laden("users.json")
        for user in users:
            if user["name"] == username and user["password"] == password:
                session["user"] = user["name"]
                session["admin"] = user.get("admin", False)
                log_speichern(username, "Erfolgreich eingeloggt")
                return redirect("/dienst")

        flash("Login fehlgeschlagen!")
    return render_template("login.html")

@app.route("/dienst", methods=["GET"])
def dienst():
    if "user" not in session:
        return redirect("/")
    accounts = json_laden("accounts.json")
    bestand = {}
    for dienst in ALLE_DIENSTE:
        bestand[dienst] = len(accounts.get(dienst, []))
    return render_template("dienst.html", dienste=ALLE_DIENSTE, bestand=bestand)

@app.route("/accounts", methods=["GET", "POST"])
def accounts():
    if "user" not in session:
        return redirect("/")
    accounts = json_laden("accounts.json")
    ausgabe = []
    if request.method == "POST":
        dienst = request.form.get("dienst")
        anzahl = request.form.get("anzahl")
        if not dienst or dienst not in ALLE_DIENSTE:
            flash("Ungültiger Dienst ausgewählt!")
            return redirect(url_for("accounts"))
        try:
            anzahl = int(anzahl)
        except:
            flash("Bitte eine gültige Zahl eingeben!")
            return redirect(url_for("accounts"))
        if anzahl <= 0:
            flash("Anzahl muss größer als 0 sein!")
            return redirect(url_for("accounts"))
        vorhanden = len(accounts.get(dienst, []))
        if anzahl > vorhanden:
            flash(f"Nicht genug Accounts vorhanden! ({vorhanden} verfügbar)")
            return redirect(url_for("accounts"))
        ausgabe = accounts[dienst][:anzahl]
        session["last_ausgabe_dienst"] = dienst
        session["last_ausgabe_count"] = anzahl
        log_speichern(session["user"], f"{anzahl}x {dienst} abgerufen (nicht gelöscht)")
    return render_template("accounts.html", dienste=ALLE_DIENSTE, ausgabe=ausgabe)

@app.route("/accounts/delete/<int:index>", methods=["POST"])
def delete_account(index):
    if "user" not in session:
        return redirect("/")
    dienst = session.get("last_ausgabe_dienst")
    if not dienst:
        flash("Kein Dienst ausgewählt")
        return redirect(url_for("accounts"))
    accounts = json_laden("accounts.json")
    if dienst in accounts and 0 <= index < len(accounts[dienst]):
        account_weg = accounts[dienst].pop(index)
        json_speichern("accounts.json", accounts)
        log_speichern(session["user"], f"Account gelöscht bei Dienst {dienst}: {account_weg}")
        flash("Account erfolgreich gelöscht")
    else:
        flash("Ungültiger Account Index")
    return redirect(url_for("accounts"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")
    accounts = json_laden("accounts.json")
    users = json_laden("users.json")
    bestand = {dienst: len(accounts.get(dienst, [])) for dienst in ALLE_DIENSTE}

    if request.method == "POST":
        # Account hinzufügen
        if "add_account" in request.form:
            dienst = request.form.get("dienst")
            account = request.form.get("account")
            if not dienst or dienst not in ALLE_DIENSTE:
                flash("Ungültiger Dienst")
            elif not account or account.strip() == "":
                flash("Account darf nicht leer sein")
            else:
                if dienst not in accounts:
                    accounts[dienst] = []
                accounts[dienst].append(account.strip())
                json_speichern("accounts.json", accounts)
                log_speichern(session["user"], f"Account hinzugefügt zu Dienst {dienst}: {account.strip()}")
                flash("Account erfolgreich hinzugefügt")

        # User hinzufügen
        if "add_user" in request.form:
            username = request.form.get("username")
            password = request.form.get("password")
            admin_check = request.form.get("admin_check") == "on"
            if not username or not password:
                flash("Benutzername und Passwort dürfen nicht leer sein")
            else:
                if any(u["name"] == username for u in users):
                    flash("Benutzer existiert bereits")
                else:
                    users.append({"name": username, "password": password, "admin": admin_check})
                    json_speichern("users.json", users)
                    log_speichern(session["user"], f"Benutzer erstellt: {username}, Admin: {admin_check}")
                    flash("Benutzer erfolgreich erstellt")

    return render_template("admin.html", dienste=ALLE_DIENSTE, bestand=bestand, users=users)

@app.route("/admin/logs")
def logs():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")
    logs = json_laden("logs.json")
    logs = sorted(logs, key=lambda x: datetime.strptime(x["zeit"], "%d.%m.%Y %H:%M"), reverse=True)
    return render_template("logs.html", logs=logs)

@app.route("/logout")
def logout():
    user = session.get("user", "Unbekannt")
    session.clear()
    log_speichern(user, "Ausgeloggt")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
