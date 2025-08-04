import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash

BASE_DIR = os.getcwd()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Pluezzzzshop")

# Liste aller Dienste
ALLE_DIENSTE = [
    "Netflix", "Spotify", "Disney", "Dazn", "Paramount", "Prime-Video",
    "YouTube-Premium", "Crunchyroll", "Steam", "GTA Activation Key",
    "NordVPN", "CapCut-Pro", "Canva", "Adobe Creative Cloud"
]

# Hilfsfunktion: JSON laden
def json_laden(dateiname):
    pfad = os.path.join(BASE_DIR, dateiname)
    if not os.path.exists(pfad):
        if dateiname == "accounts.json":
            # Bei accounts.json initial alle Dienste mit leeren Listen anlegen
            return {dienst: [] for dienst in ALLE_DIENSTE}
        if dateiname == "users.json":
            # Users initial leer anlegen
            return {"users": []}
        if dateiname == "logs.json":
            return []
        return {}
    with open(pfad, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# Hilfsfunktion: JSON speichern
def json_speichern(dateiname, daten):
    with open(os.path.join(BASE_DIR, dateiname), "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)

# Log schreiben
def log_schreiben(user, aktion):
    logs = json_laden("logs.json")
    logs.append({
        "user": user,
        "aktion": aktion,
        "zeit": datetime.now().strftime("%d.%m.%Y %H:%M")
    })
    json_speichern("logs.json", logs)

# Login-Seite
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = json_laden("users.json")["users"]

        # Wenn users.json leer ist, legen wir 2 Standardaccounts an (Paul und Elias) mit PW aus Umgebungsvariablen
        if not users:
            users = [
                {"name": "Paul", "password": os.environ.get("PAUL_PASSWORD", "Pluezzshop"), "admin": True},
                {"name": "Elias", "password": os.environ.get("ELIAS_PASSWORD", "geheim"), "admin": False},
            ]
            json_speichern("users.json", {"users": users})

        # Login prüfen
        for user in users:
            if user["name"].lower() == username.lower() and user["password"] == password:
                session["user"] = user["name"]
                session["admin"] = user.get("admin", False)
                log_schreiben(user["name"], "eingeloggt")
                return redirect("/start")

        flash("Login fehlgeschlagen! Falscher Benutzername oder Passwort.")

    return render_template("login.html")

# Startseite mit Übersicht aller Dienste + Lageranzahl + Links
@app.route("/start")
def start():
    if "user" not in session:
        return redirect("/")
    accounts = json_laden("accounts.json")
    # Verfügbarkeit pro Dienst zählen
    lager = {dienst: len(accounts.get(dienst, [])) for dienst in ALLE_DIENSTE}
    return render_template("start.html", user=session["user"], admin=session.get("admin", False), lager=lager)

# Seite zum Accounts abrufen und ggf. löschen
@app.route("/accounts", methods=["GET", "POST"])
def accounts_page():
    if "user" not in session:
        return redirect("/")
    accounts = json_laden("accounts.json")
    ausgabe = []
    max_anzahl = 0
    dienst_auswahl = None

    if request.method == "POST":
        dienst = request.form.get("dienst")
        dienst_auswahl = dienst
        try:
            anzahl = int(request.form.get("anzahl", "0"))
        except ValueError:
            flash("Bitte eine gültige Anzahl eingeben!")
            return redirect("/accounts")

        if dienst not in ALLE_DIENSTE:
            flash("Ungültiger Dienst ausgewählt!")
            return redirect("/accounts")

        verfuegbar = len(accounts.get(dienst, []))
        max_anzahl = verfuegbar

        if anzahl <= 0:
            flash("Bitte eine Anzahl größer 0 eingeben!")
            return redirect("/accounts")
        if anzahl > verfuegbar:
            flash(f"Es sind nur {verfuegbar} Accounts von {dienst} verfügbar.")
            return redirect("/accounts")

        ausgabe = accounts[dienst][:anzahl]
        # Speichere die Auswahl in Session, damit wir die Accounts zum Löschen zeigen können
        session["letzte_ausgabe"] = {"dienst": dienst, "accounts": ausgabe}

    # Falls wir schon vorher ausgegeben haben (z.B. nach Reload), aus Session holen
    if "letzte_ausgabe" in session and not ausgabe:
        letzte = session["letzte_ausgabe"]
        dienst_auswahl = letzte["dienst"]
        ausgabe = letzte["accounts"]
        max_anzahl = len(accounts.get(dienst_auswahl, []))

    return render_template("accounts.html", dienste=ALLE_DIENSTE, ausgabe=ausgabe, dienst_auswahl=dienst_auswahl, max_anzahl=max_anzahl)

# Route zum Löschen eines einzelnen Accounts aus der letzten Ausgabe
@app.route("/accounts/delete/<int:index>", methods=["POST"])
def delete_account(index):
    if "user" not in session:
        return redirect("/")
    if "letzte_ausgabe" not in session:
        flash("Keine Accounts zum Löschen ausgewählt.")
        return redirect("/accounts")

    letzte = session["letzte_ausgabe"]
    dienst = letzte["dienst"]
    accounts = json_laden("accounts.json")

    # Prüfen ob Index gültig
    if index < 0 or index >= len(letzte["accounts"]):
        flash("Ungültiger Index zum Löschen.")
        return redirect("/accounts")

    # Account aus gesamtem Lager entfernen
    account_to_delete = letzte["accounts"][index]
    if dienst in accounts and account_to_delete in accounts[dienst]:
        accounts[dienst].remove(account_to_delete)
        json_speichern("accounts.json", accounts)
        log_schreiben(session["user"], f"Account gelöscht: {account_to_delete} aus {dienst}")

        # Aus Session-Ausgabe entfernen
        letzte["accounts"].pop(index)
        session["letzte_ausgabe"] = letzte
        flash("Account gelöscht.")
    else:
        flash("Account nicht gefunden.")

    return redirect("/accounts")

# Adminbereich: Lagerübersicht, Accounts hinzufügen, User hinzufügen
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or not session.get("admin", False):
        return redirect("/")

    accounts = json_laden("accounts.json")
    users = json_laden("users.json")
    message = ""

    if request.method == "POST":
        # Unterscheidung: accounts hinzufügen oder user hinzufügen
        if "add_account" in request.form:
            dienst = request.form.get("dienst")
            account = request.form.get("account")

            if not dienst or not account or dienst not in ALLE_DIENSTE:
                flash("Bitte Dienst und Account richtig angeben.")
            else:
                if dienst not in accounts:
                    accounts[dienst] = []
                accounts[dienst].append(account.strip())
                json_speichern("accounts.json", accounts)
                log_schreiben(session["user"], f"Account hinzugefügt: {account} zu {dienst}")
                flash(f"Account zu {dienst} hinzugefügt.")

        elif "add_user" in request.form:
            username = request.form.get("username")
            password = request.form.get("password")
            admin_check = request.form.get("admin_check") == "on"

            if not username or not password:
                flash("Bitte Benutzername und Passwort angeben.")
            else:
                # Benutzer hinzufügen (falls noch nicht vorhanden)
                existing_usernames = [u["name"].lower() for u in users.get("users", [])]
                if username.lower() in existing_usernames:
                    flash("Benutzername existiert bereits!")
                else:
                    users.setdefault("users", []).append({
                        "name": username,
                        "password": password,
                        "admin": admin_check
                    })
                    json_speichern("users.json", users)
                    log_schreiben(session["user"], f"Benutzer hinzugefügt: {username} (Admin: {admin_check})")
                    flash(f"Benutzer {username} hinzugefügt.")

    # Lagerübersicht für Admin
    lager = {dienst: len(accounts.get(dienst, [])) for dienst in ALLE_DIENSTE}
    return render_template("admin.html", user=session["user"], lager=lager, dienste=ALLE_DIENSTE)

# Logout
@app.route("/logout")
def logout():
    user = session.get("user", "Unbekannt")
    session.clear()
    log_schreiben(user, "ausgeloggt")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
