"""
Sets up Gmail SMTP in Odoo and tests it.
Run:  python /Users/mac/odoo/setup_gmail.py
"""
import xmlrpc.client
import smtplib
import ssl
import getpass

URL      = "http://localhost:8069"
DB       = "odoo"
USERNAME = "admin"
PASSWORD = "admin"
GMAIL    = "popen9488@gmail.com"

print("=" * 55)
print("  Gmail SMTP Setup for Odoo")
print("=" * 55)
print()
print("Paste your 16-character Gmail App Password below.")
print("(Get it from: myaccount.google.com/apppasswords)")
print("Spaces are stripped automatically.")
print()

app_password = getpass.getpass("App Password: ").replace(" ", "").strip()

if len(app_password) != 16:
    print(f"\nWarning: expected 16 chars, got {len(app_password)}. Continuing anyway.")

# ── 1. Test the credentials directly before touching Odoo ────────────────
print("\nStep 1 — Testing Gmail credentials directly...")
try:
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(GMAIL, app_password)
    server.quit()
    print("  ✅  Gmail login successful!")
except smtplib.SMTPAuthenticationError:
    print("  ❌  Wrong App Password. Generate a fresh one at:")
    print("      https://myaccount.google.com/apppasswords")
    exit(1)
except Exception as e:
    print(f"  ❌  Connection error: {e}")
    exit(1)

# ── 2. Save the mail server in Odoo ──────────────────────────────────────
print("\nStep 2 — Saving SMTP server in Odoo...")
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid    = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

# Remove any existing Gmail server to avoid duplicates
existing = models.execute_kw(DB, uid, PASSWORD,
    "ir.mail_server", "search", [[["smtp_user", "=", GMAIL]]])
if existing:
    models.execute_kw(DB, uid, PASSWORD, "ir.mail_server", "unlink", [existing])
    print(f"  Removed {len(existing)} old record(s).")

server_id = models.execute_kw(DB, uid, PASSWORD, "ir.mail_server", "create", [{
    "name":            "Gmail — Orphan Sponsorship",
    "smtp_host":       "smtp.gmail.com",
    "smtp_port":       587,
    "smtp_encryption": "starttls",
    "smtp_user":       GMAIL,
    "smtp_pass":       app_password,
    "sequence":        1,
}])
print(f"  ✅  Mail server saved (ID {server_id})")

# ── 3. Verify it is in the DB ─────────────────────────────────────────────
print("\nStep 3 — Verifying...")
rec = models.execute_kw(DB, uid, PASSWORD,
    "ir.mail_server", "read", [[server_id]],
    {"fields": ["name", "smtp_host", "smtp_port", "smtp_encryption", "smtp_user"]})[0]
print(f"  Name:       {rec['name']}")
print(f"  Host:       {rec['smtp_host']}")
print(f"  Port:       {rec['smtp_port']}")
print(f"  Security:   {rec['smtp_encryption']}")
print(f"  Username:   {rec['smtp_user']}")

print()
print("=" * 55)
print("  Done! Gmail SMTP is configured in Odoo.")
print("  Create a donor with a real email to test sending.")
print("=" * 55)
print()
