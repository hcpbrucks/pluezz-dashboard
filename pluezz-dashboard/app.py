import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os

# --- Dateipfade ---
ACCOUNTS_FILE = "accounts.json"
USERS_FILE = "users.json"

# --- Dienste mit (optionalen) Icon-Pfaden (Platzhalter) ---
dienste = [
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
    "Server Member 500",
    "Server Member 1000",
    "Server Boost 14x 1 Monat",
    "Server Boost 14x 3 Monate",
    "Adobe-Creative-Cloud 1 Monat key",
    "Adobe-Creative-Cloud Livetime Account",
    "Netflix",
    "Spotify",
    "Disney",
    "Dazn",
    "Paramount",
    "Prime-Video",
    "Nord-Vpn",
    "CapCut-Pro",
    "Canva",
    "GTA-activation-Key"
]

# --- Standard-Admin ---
DEFAULT_ADMIN = {
    "Paul": {
        "password": "Pluezzshop",
        "role": "admin"
    }
}

# --- Hilfsfunktionen JSON Laden/Speichern ---
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

accounts = load_json(ACCOUNTS_FILE, {d: [] for d in dienste})
users = load_json(USERS_FILE, DEFAULT_ADMIN)

# --- Farb-Codierung Bestandsstatus ---
def get_status_color(count):
    if count == 0:
        return "red", "Leer"
    elif count < 5:
        return "orange", "Nachschub nötig"
    elif count < 10:
        return "yellow", "Knapp"
    else:
        return "green", "Auf Lager"

# --- Login Fenster ---
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("320x180")
        self.resizable(False, False)

        tk.Label(self, text="Benutzername").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        tk.Label(self, text="Passwort").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Login", command=self.try_login).pack(pady=10)

        self.username_entry.focus_set()

    def try_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if username in users and users[username]["password"] == password:
            self.destroy()
            MainWindow(username, users[username]["role"])
        else:
            messagebox.showerror("Fehler", "Falsche Login-Daten!")

# --- Hauptfenster mit Tabs ---
class MainWindow(tk.Tk):
    def __init__(self, username, role):
        super().__init__()
        self.title(f"Account-Manager - Angemeldet als {username} ({role})")
        self.geometry("900x600")
        self.minsize(800, 500)

        self.username = username
        self.role = role

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.create_overview_tab()
        self.create_restock_tab()
        if self.role == "admin":
            self.create_admin_tab()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.mainloop()

    # --- Übersicht mit Suchfilter ---
    def create_overview_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Übersicht")

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill="x", pady=5, padx=5)
        ttk.Label(search_frame, text="Suchen:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        search_entry.bind("<KeyRelease>", self.update_overview_list)

        # Treeview mit Spalten Dienst, Anzahl, Status
        columns = ("Dienst", "Anzahl", "Status")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=300 if col=="Dienst" else 100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Account abrufen", command=self.on_account_abrufen).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Löschen", command=self.on_account_loeschen).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Aktualisieren", command=self.update_overview_list).pack(side="left", padx=5)

        self.update_overview_list()

    def update_overview_list(self, event=None):
        filter_text = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for dienst, acc_list in accounts.items():
            if filter_text and filter_text not in dienst.lower():
                continue
            count = len(acc_list)
            color, status = get_status_color(count)
            self.tree.insert("", "end", values=(dienst, count, status), tags=(color,))
        # Farben zuweisen
        self.tree.tag_configure("red", foreground="red")
        self.tree.tag_configure("orange", foreground="orange")
        self.tree.tag_configure("yellow", foreground="goldenrod")
        self.tree.tag_configure("green", foreground="green")

    def on_account_abrufen(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte Dienst auswählen")
            return
        dienst = self.tree.item(selected[0])["values"][0]
        if len(accounts[dienst]) == 0:
            messagebox.showerror("Fehler", "Keine Accounts verfügbar")
            return
        account = accounts[dienst].pop(0)
        save_json(ACCOUNTS_FILE, accounts)
        messagebox.showinfo("Account abgerufen", f"Account für {dienst}:\n{account}")
        self.update_overview_list()

    def on_account_loeschen(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte Dienst auswählen")
            return
        dienst = self.tree.item(selected[0])["values"][0]
        if len(accounts[dienst]) == 0:
            messagebox.showerror("Fehler", "Keine Accounts zum Löschen vorhanden")
            return

        # Liste der Accounts anzeigen, um zu löschen
        AccountDeleteWindow(self, dienst)

    # --- Restock Tab ---
    def create_restock_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Restock")

        ttk.Label(frame, text="Dienst auswählen:").pack(pady=5)
        self.restock_service_var = tk.StringVar()
        self.restock_service = ttk.Combobox(frame, textvariable=self.restock_service_var, values=dienste, state="readonly")
        self.restock_service.pack()

        ttk.Label(frame, text="Account-Daten (z.B. Email:Passwort oder Key):").pack(pady=5)
        self.restock_entry = ttk.Entry(frame, width=80)
        self.restock_entry.pack(pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Account hinzufügen", command=self.add_account).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Aus Datei laden", command=self.load_accounts_from_file).pack(side="left", padx=5)

    def add_account(self):
        dienst = self.restock_service_var.get()
        data = self.restock_entry.get().strip()
        if not dienst:
            messagebox.showerror("Fehler", "Bitte Dienst auswählen")
            return
        if not data:
            messagebox.showerror("Fehler", "Bitte Account-Daten eingeben")
            return
        accounts[dienst].append(data)
        save_json(ACCOUNTS_FILE, accounts)
        messagebox.showinfo("Erfolg", "Account hinzugefügt")
        self.restock_entry.delete(0, "end")

    def load_accounts_from_file(self):
        datei = filedialog.askopenfilename(title="Accounts-Datei öffnen", filetypes=[("Textdateien", "*.txt"), ("Alle Dateien", "*.*")])
        if not datei:
            return
        dienst = self.restock_service_var.get()
        if not dienst:
            messagebox.showerror("Fehler", "Bitte Dienst auswählen bevor Sie eine Datei laden")
            return
        try:
            with open(datei, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            accounts[dienst].extend(lines)
            save_json(ACCOUNTS_FILE, accounts)
            messagebox.showinfo("Erfolg", f"{len(lines)} Accounts zu {dienst} hinzugefügt")
        except Exception as e:
            messagebox.showerror("Fehler", f"Datei konnte nicht geladen werden:\n{e}")

    # --- Admin Tab ---
    def create_admin_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Admin")

        ttk.Label(frame, text="Benutzerverwaltung").pack(pady=10)

        self.user_listbox = tk.Listbox(frame)
        self.user_listbox.pack(fill="both", expand=True, padx=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Benutzer hinzufügen", command=self.admin_add_user).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Benutzer löschen", command=self.admin_delete_user).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Aktualisieren", command=self.admin_update_user_list).pack(side="left", padx=5)

        self.admin_update_user_list()

    def admin_update_user_list(self):
        self.user_listbox.delete(0, tk.END)
        for user, info in users.items():
            self.user_listbox.insert(tk.END, f"{user} ({info['role']})")

    def admin_add_user(self):
        dialog = UserDialog(self, "Benutzer hinzufügen")
        self.wait_window(dialog)
        if dialog.result:
            username, password, role = dialog.result
            if username in users:
                messagebox.showerror("Fehler", "Benutzer existiert bereits")
                return
            users[username] = {"password": password, "role": role}
            save_json(USERS_FILE, users)
            self.admin_update_user_list()
            messagebox.showinfo("Erfolg", f"Benutzer {username} hinzugefügt")

    def admin_delete_user(self):
        selected = self.user_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte Benutzer auswählen")
            return
