#!/usr/bin/env python3
"""Script to load sample orphan data into Odoo via RPC."""
import xmlrpc.client

url = 'http://localhost:8069'
db = 'odoo'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("ERROR: Could not authenticate. Make sure Odoo is running.")
    exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

orphans = [
    {'name': 'Ahmed Ali', 'age': 7, 'gender': 'male', 'location': 'Karachi'},
    {'name': 'Fatima Hassan', 'age': 9, 'gender': 'female', 'location': 'Lahore'},
    {'name': 'Yusuf Khan', 'age': 5, 'gender': 'male', 'location': 'Islamabad'},
    {'name': 'Aisha Malik', 'age': 11, 'gender': 'female', 'location': 'Peshawar'},
    {'name': 'Omar Siddiqui', 'age': 8, 'gender': 'male', 'location': 'Multan'},
]

print("Creating 5 orphans...")
for orphan in orphans:
    orphan_id = models.execute_kw(db, uid, password,
        'orphan.sponsorship.orphan', 'create', [orphan])
    print(f"  Created: {orphan['name']} (ID: {orphan_id})")

all_orphans = models.execute_kw(db, uid, password,
    'orphan.sponsorship.orphan', 'search_read',
    [[]], {'fields': ['name', 'status'], 'limit': 10})
print(f"\nAll orphans ({len(all_orphans)} total):")
for o in all_orphans:
    print(f"  {o['name']} — {o['status']}")

print("\nSample data loaded! Open http://localhost:8069 in your browser.")
print("Login: admin / admin")
print("Go to: Orphan Sponsorship > Orphans")
