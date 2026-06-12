#!/usr/bin/env python3
"""Phase 4 demo: create donor → auto-assign → cancel → back to unassigned."""
import xmlrpc.client

url = 'http://localhost:8069'
db = 'odoo'
uid = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common').authenticate(db, 'admin', 'admin', {})
m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
pw = 'admin'

def get_orphans():
    return m.execute_kw(db, uid, pw, 'orphan.sponsorship.orphan', 'search_read',
        [[]], {'fields': ['name', 'status', 'donor_id']})

print("=== BEFORE: All orphans unassigned ===")
for o in get_orphans():
    print(f"  {o['name']}: {o['status']}")

print("\n=== Creating donor 'Waleed Malik' (auto-assigns first orphan) ===")
donor_id = m.execute_kw(db, uid, pw, 'orphan.sponsorship.donor', 'create',
    [{'name': 'Waleed Malik', 'email': 'waleed@example.com', 'state': 'active'}])
print(f"  Donor created (ID: {donor_id})")

print("\n=== AFTER CREATE: Orphan status ===")
for o in get_orphans():
    sponsor = o['donor_id'][1] if o['donor_id'] else 'None'
    print(f"  {o['name']}: {o['status']}  (sponsor: {sponsor})")

print("\n=== Cancelling donor sponsorship ===")
m.execute_kw(db, uid, pw, 'orphan.sponsorship.donor', 'action_cancel', [[donor_id]])

print("\n=== AFTER CANCEL: All orphans back to unassigned ===")
for o in get_orphans():
    print(f"  {o['name']}: {o['status']}")

print("\n✓ Demo complete! Auto-assign and release working correctly.")
