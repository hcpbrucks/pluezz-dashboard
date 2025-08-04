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

        # Einzelnen Account hinzufügen (über Dropdown + Textfeld)
        elif "add_single_account" in request.form:
            dienst = request.form.get("dienst_single")
            account_daten = request.form.get("account_data", "").strip()
            if not dienst or dienst not in ALLE_DIENSTE:
                flash("Ungültiger Dienst")
            elif not account_daten:
                flash("Account-Daten dürfen nicht leer sein")
            else:
                if dienst not in accounts:
                    accounts[dienst] = []
                accounts[dienst].append(account_daten)
                json_speichern("accounts.json", accounts)
                log_speichern(session["user"], f"1 Account hinzugefügt zu Dienst {dienst}")
                flash(f"Account erfolgreich hinzugefügt.")

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
