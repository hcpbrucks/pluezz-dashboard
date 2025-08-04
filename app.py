from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os

app = Flask(__name__)
app.secret_key = 'Pluezzzshop'

# Nutzer laden
def load_users():
    with open("users.json", "r") as f:
        return json.load(f)

# Accounts laden
def load_accounts():
    with open("accounts.json", "r") as f:
        return json.load(f)

# Preise laden
def load_prices():
    with open("prices.json", "r") as f:
        return json.load(f)

# Accounts speichern
def save_accounts(data):
    with open("accounts.json", "w") as f:
        json.dump(data, f, indent=4)

# Nutzer speichern
def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        pw = request.form["password"]
        users = load_users()
        for user in users:
            if user["name"] == name and user["password"] == pw:
                session["user"] = name
                session["admin"] = user["admin"]
                return redirect(url_for("dashboard"))
        flash("Login fehlgeschlagen")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    accounts = load_accounts()
    stock = {dienst: len(daten) for dienst, daten in accounts.items()}
    return render_template("dashboard.html", stock=stock, is_admin=session.get("admin", False))

@app.route("/dienst/<dienst>", methods=["GET", "POST"])
def dienst_view(dienst):
    if "user" not in session:
        return redirect("/")
    accounts = load_accounts()
    if request.method == "POST":
        anzahl = int(request.form["anzahl"])
        if anzahl <= len(accounts[dienst]):
            ausgabe = accounts[dienst][:anzahl]
            if request.form.get("loeschen"):
                accounts[dienst] = accounts[dienst][anzahl:]
                save_accounts(accounts)
            return render_template("dienst.html", dienst=dienst, ausgabe=ausgabe, max=len(accounts[dienst]))
        else:
            flash("Nicht genug Accounts auf Lager")
    return render_template("dienst.html", dienst=dienst, ausgabe=None, max=len(accounts[dienst]))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or not session.get("admin"):
        return redirect("/")
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
    if "user" not in session or not session.get("admin"):
        return redirect("/")
    dienst = request.form["dienst"]
    daten = request.form["daten"]
    accounts = load_accounts()
    neu = daten.strip().splitlines()
    accounts.setdefault(dienst, []).extend(neu)
    save_accounts(accounts)
    flash("Account(s) hinzugefügt")
    return redirect("/admin")

@app.route("/admin/add_user", methods=["POST"])
def add_user():
    if "user" not in session or not session.get("admin"):
        return redirect("/")
    name = request.form["username"]
    pw = request.form["password"]
    admin = request.form.get("admin") == "on"
    users = load_users()
    users.append({"name": name, "password": pw, "admin": admin})
    save_users(users)
    flash("Nutzer hinzugefügt")
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
