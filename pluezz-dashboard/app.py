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

def login_erforderlich(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Bitte zuerst einloggen!")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_erforderlich(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session or not session.get("admin", False):
            flash("Adminrechte erforderlich!")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Env-User (Paul, Elias)
        env_users = {
            "Paul": os.environ.get("PAUL_PASSWORD"),
            "Elias": os.environ.get("ELIAS_PASSWORD")
        }

        if username in env_users and password == env_users[username]:
            session["user"] = username
            session["admin"] = True
            log_speichern(username, "Erfolgreich eingeloggt (Env User)")
            return redirect(url_for("dienst"))

        users = json_laden("users.json")
        for user in users:
            if user.get("name") == username and user.get("password") == password:
                session["user"] = user["name"]
                session["admin"] = user.get("admin", False)
                log_speichern(username, "Erfolgreich eingeloggt (User)")
                return redirect(url_for("dienst"))

        flash("Login fehlgeschlagen!")
    return render_template("login.html")

@app.route("/dienst")
@login_erforderlich
def dienst():
    accounts = json_laden("accounts.json")
    bestand = {dienst: len(accounts.get(dienst, [])) for dienst in ALLE_DIENSTE}
    return render_template("dienst.html", dienste=ALLE_DIENSTE, bestand=bestand)

@app.route("/accounts", methods=["GET", "POST"])
@login_erforderlich
def accounts():
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
            if anzahl <= 0:
                raise ValueError()
        except:
            flash("Bitte eine gültige Anzahl eingeben!")
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
@login_erforderlich
def delete_account(index):
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
@admin_erforderlich
def admin():
    accounts = json_laden("accounts.json")
    users = json_laden("users.json")
    bestand = {dienst: len(accounts.get(dienst, [])) for dienst in ALLE_DIENSTE}

    if request.method == "POST":
        # Accounts Bulk hinzufügen
        if "add_account" in request.form:
            dienst = request.form.get("dienst")
            daten = request.form.get("daten")
            if not dienst or dienst not in ALLE_DIENSTE:
                flash("Ungültiger Dienst")
            elif not daten or daten.strip() == "":
                flash("Accounts dürfen nicht leer sein")
            else:
                if dienst not in accounts:
                    accounts[dienst] = []
                neue_accounts = [zeile.strip() for zeile in daten.strip().splitlines() if zeile.strip()]
                accounts[dienst].extend(neue_accounts)
                json_speichern("accounts.json", accounts)
                log_speichern(session["user"], f"{len(neue_accounts)} Accounts hinzugefügt zu Dienst {dienst}")
                flash(f"{len(neue_accounts)} Accounts erfolgreich hinzugefügt.")

        # Benutzer hinzufügen
        elif "add_user" in request.form:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            admin_check = request.form.get("admin") == "on"
            if not username or not password:
                flash("Benutzername und Passwort dürfen nicht leer sein")
            elif any(u["name"] == username for u in users):
                flash("Benutzer existiert bereits")
            else:
                users.append({"name": username, "password": password, "admin": admin_check})
                json_speichern("users.json", users)
                log_speichern(session["user"], f"Benutzer erstellt: {username}, Admin: {admin_check}")
                flash("Benutzer erfolgreich erstellt")

    return render_template("admin.html", dienste=ALLE_DIENSTE, status=bestand, users=users)

@app.route("/admin/logs")
@admin_erforderlich
def logs():
    logs = json_laden("logs.json")
    logs = sorted(logs, key=lambda x: datetime.strptime(x["zeit"], "%d.%m.%Y %H:%M"), reverse=True)
    return render_template("logs.html", logs=logs)

@app.route("/logout")
@login_erforderlich
def logout():
    user = session.get("user", "Unbekannt")
    session.clear()
    log_speichern(user, "Ausgeloggt")
    flash("Erfolgreich ausgeloggt!")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
