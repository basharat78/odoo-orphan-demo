"""
Excel → Odoo Demo  (Orphan Sponsorship)
========================================
Reads orphans_data.xlsx and donors_data.xlsx, imports them into Odoo
via XML-RPC, and shows the auto-assign / unassign flow step-by-step.

Usage:
    source /Users/mac/odoo-venv/bin/activate
    python /Users/mac/odoo/demo_excel_import.py
"""

import xmlrpc.client
import openpyxl
import time

# ── Odoo connection ──────────────────────────────────────────────────────────
URL      = "http://localhost:8069"
DB       = "odoo"
USERNAME = "admin"
PASSWORD = "admin"

ORPHAN_XLSX = "/Users/mac/odoo/orphans_data.xlsx"
DONOR_XLSX  = "/Users/mac/odoo/donors_data.xlsx"

SEP  = "─" * 62
SEP2 = "═" * 62


# ── helpers ──────────────────────────────────────────────────────────────────
def connect():
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid    = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        raise SystemExit("❌  Cannot connect to Odoo. Is it running on port 8069?")
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
    return uid, models


def read_excel(path):
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if any(v is not None for v in row):          # skip blank rows
            rows.append(dict(zip(headers, row)))
    return rows


def print_status(uid, models):
    """Print current orphan assignment table."""
    orphans = models.execute_kw(DB, uid, PASSWORD,
        'orphan.sponsorship.orphan', 'search_read',
        [[]], {'fields': ['name', 'age', 'location', 'status', 'donor_id'], 'order': 'name'})
    print(f"\n{'Name':<22} {'Age':>4}  {'Location':<14} {'Status':<12}  Sponsor")
    print(SEP)
    for o in orphans:
        sponsor = o['donor_id'][1] if o['donor_id'] else "—"
        status  = "✅ Sponsored" if o['status'] == 'sponsored' else "⬜ Unassigned"
        print(f"{o['name']:<22} {o['age']:>4}  {o['location'] or '':<14} {status:<12}  {sponsor}")


def cleanup_previous(uid, models):
    """Remove any records from a previous demo run."""
    orphan_ids = models.execute_kw(DB, uid, PASSWORD,
        'orphan.sponsorship.orphan', 'search', [[('name', 'like', '')]])
    donor_ids  = models.execute_kw(DB, uid, PASSWORD,
        'orphan.sponsorship.donor',  'search', [[('name', 'like', '')]])

    if donor_ids or orphan_ids:
        print("  Cleaning up previous demo data...")
        # unlink donors first (releases orphans), then orphans
        if donor_ids:
            models.execute_kw(DB, uid, PASSWORD,
                'orphan.sponsorship.donor', 'unlink', [donor_ids])
        if orphan_ids:
            models.execute_kw(DB, uid, PASSWORD,
                'orphan.sponsorship.orphan', 'unlink', [orphan_ids])
        print("  Done.\n")


# ── main demo ────────────────────────────────────────────────────────────────
def main():
    print(f"\n{SEP2}")
    print("  ORPHAN SPONSORSHIP  —  Excel Import & Auto-Assign Demo")
    print(SEP2)

    print("\n🔌 Connecting to Odoo …")
    uid, models = connect()
    print(f"   Connected  (uid={uid})\n")

    # ── STEP 0 : clean up ────────────────────────────────────────────────────
    print(SEP)
    print("STEP 0 — Clearing any previous demo data")
    print(SEP)
    cleanup_previous(uid, models)

    # ── STEP 1 : import orphans ──────────────────────────────────────────────
    print(SEP)
    print("STEP 1 — Reading  orphans_data.xlsx")
    print(SEP)
    orphan_rows = read_excel(ORPHAN_XLSX)
    print(f"   Found {len(orphan_rows)} orphan records in the file.\n")

    orphan_ids = []
    for r in orphan_rows:
        rec_id = models.execute_kw(DB, uid, PASSWORD,
            'orphan.sponsorship.orphan', 'create', [{
                'name':     r.get('Full Name'),
                'age':      int(r.get('Age') or 0),
                'gender':   'male' if str(r.get('Gender', '')).lower() == 'male' else 'female',
                'location': r.get('City / Location'),
                'notes':    r.get('Notes'),
                'status':   'unassigned',
            }])
        orphan_ids.append(rec_id)
        print(f"   ➕  Imported orphan: {r['Full Name']}  (ID {rec_id})")

    print(f"\n   ✅  {len(orphan_ids)} orphans imported — all UNASSIGNED")
    print("\n📋 Current state after importing orphans:")
    print_status(uid, models)

    input("\n  ↵  Press ENTER to import donors and watch auto-assign …\n")

    # ── STEP 2 : import donors (triggers auto-assign per donor) ─────────────
    print(SEP)
    print("STEP 2 — Reading  donors_data.xlsx  &  importing donors")
    print("         (Each donor is created as 'active' → auto-assign fires)")
    print(SEP)
    donor_rows = read_excel(DONOR_XLSX)
    print(f"   Found {len(donor_rows)} donor records in the file.\n")

    donor_ids = []
    for r in donor_rows:
        rec_id = models.execute_kw(DB, uid, PASSWORD,
            'orphan.sponsorship.donor', 'create', [{
                'name':  r.get('Full Name'),
                'email': r.get('Email'),
                'phone': r.get('Phone'),
                'state': 'active',
            }])
        donor_ids.append(rec_id)

        # fetch which orphan was just assigned
        assigned = models.execute_kw(DB, uid, PASSWORD,
            'orphan.sponsorship.orphan', 'search_read',
            [[('donor_id', '=', rec_id)]],
            {'fields': ['name']})
        orphan_name = assigned[0]['name'] if assigned else "none available"
        print(f"   ➕  Donor:  {r['Full Name']:<20}  →  auto-assigned  ➜  {orphan_name}")
        time.sleep(0.3)   # small pause so output is readable live

    print(f"\n   ✅  {len(donor_ids)} donors imported")
    print("\n📋 Current state after importing donors:")
    print_status(uid, models)

    input("\n  ↵  Press ENTER to cancel ALL donors and watch orphans release …\n")

    # ── STEP 3 : cancel all donors → orphans go back to unassigned ──────────
    print(SEP)
    print("STEP 3 — Cancelling all donors  (releasing orphans)")
    print(SEP)

    for did in donor_ids:
        donor = models.execute_kw(DB, uid, PASSWORD,
            'orphan.sponsorship.donor', 'read',
            [[did]], {'fields': ['name', 'orphan_ids']})[0]
        # call the cancel button method
        models.execute_kw(DB, uid, PASSWORD,
            'orphan.sponsorship.donor', 'action_cancel', [[did]])
        print(f"   ❌  Cancelled donor: {donor['name']:<20}  "
              f"({len(donor['orphan_ids'])} orphan(s) released)")
        time.sleep(0.3)

    print(f"\n   ✅  All donors cancelled")
    print("\n📋 Final state — all orphans unassigned:")
    print_status(uid, models)

    print(f"\n{SEP2}")
    print("  DEMO COMPLETE  🎉")
    print(f"  View results at  http://localhost:8069/web#action=orphan_sponsorship")
    print(SEP2)
    print()


if __name__ == "__main__":
    main()
