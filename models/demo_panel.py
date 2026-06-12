from odoo import models, fields, api
from datetime import datetime

ORPHANS_DATA = [
    ('Ahmed Ali',       7,  'male',   'Karachi',    'Loves football'),
    ('Fatima Hassan',   9,  'female', 'Lahore',     'Top student in class'),
    ('Yusuf Khan',      5,  'male',   'Islamabad',  'Very energetic child'),
    ('Aisha Malik',     11, 'female', 'Peshawar',   'Dreams of becoming a doctor'),
    ('Omar Siddiqui',   8,  'male',   'Multan',     'Enjoys drawing'),
    ('Zainab Qureshi',  6,  'female', 'Quetta',     'Loves to sing'),
    ('Hassan Raza',     10, 'male',   'Faisalabad', 'Excellent at mathematics'),
    ('Maryam Chaudhry', 12, 'female', 'Hyderabad',  'Wants to be a teacher'),
    ('Abdullah Sheikh', 4,  'male',   'Rawalpindi', 'Youngest in the program'),
    ('Noor Bibi',       8,  'female', 'Sialkot',    'Kind and helpful'),
]

DONORS_DATA = [
    ('Waleed Malik',   'waleed@example.com',      '+92-300-1234567'),
    ('Sara Ahmed',     'sara.ahmed@example.com',  '+92-321-2345678'),
    ('Bilal Hussain',  'bilal.h@example.com',     '+92-333-3456789'),
    ('Amina Farooq',   'amina.f@example.com',     '+92-345-4567890'),
    ('Khalid Mehmood', 'khalid.m@example.com',    '+92-312-5678901'),
]


class DemoPanel(models.Model):
    _name = 'orphan.sponsorship.demo'
    _description = 'Demo Control Panel'

    name = fields.Char(default='Orphan Sponsorship Demo')
    activity_log = fields.Text(string='Activity Log', readonly=True, default='')

    # ── computed summary fields shown in the view ─────────────────────────
    orphan_total     = fields.Integer(compute='_compute_stats')
    orphan_unassigned = fields.Integer(compute='_compute_stats')
    orphan_sponsored  = fields.Integer(compute='_compute_stats')
    donor_active      = fields.Integer(compute='_compute_stats')

    @api.depends('activity_log')
    def _compute_stats(self):
        Orphan = self.env['orphan.sponsorship.orphan']
        Donor  = self.env['orphan.sponsorship.donor']
        for rec in self:
            rec.orphan_total      = Orphan.search_count([])
            rec.orphan_unassigned = Orphan.search_count([('status', '=', 'unassigned')])
            rec.orphan_sponsored  = Orphan.search_count([('status', '=', 'sponsored')])
            rec.donor_active      = Donor.search_count([('state', '=', 'active')])

    @api.model
    def get_or_create(self):
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({'name': 'Orphan Sponsorship Demo', 'activity_log': ''})
        return rec

    @api.model
    def open_demo_panel(self):
        return self.get_or_create()._reopen()

    # ── private helpers ───────────────────────────────────────────────────
    def _log(self, lines):
        ts = datetime.now().strftime('%H:%M:%S')
        block = f"\n[{ts}]\n" + "\n".join(lines) + "\n" + ("─" * 50)
        self.activity_log = block + "\n" + (self.activity_log or '')

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ── STEP 1 : load orphans ─────────────────────────────────────────────
    def action_step1_load_orphans(self):
        existing = self.env['orphan.sponsorship.orphan'].search_count([])
        if existing:
            self._log([f'⚠  {existing} orphan(s) already loaded.',
                       'Use "Reset Demo" first, then run Step 1 again.'])
            return self._reopen()

        log = ['📂  Reading orphans_data.xlsx ...', '']
        for name, age, gender, location, notes in ORPHANS_DATA:
            self.env['orphan.sponsorship.orphan'].create({
                'name': name, 'age': age, 'gender': gender,
                'location': location, 'notes': notes, 'status': 'unassigned',
            })
            log.append(f'  + {name:<22}  {age} yrs  {location:<12}  → Unassigned')
        log += ['', f'✅  {len(ORPHANS_DATA)} orphans imported — all Unassigned',
                'Ready for Step 2: Import Donors']
        self._log(log)
        return self._reopen()

    # ── STEP 2 : import donors (triggers auto-assign) ─────────────────────
    def action_step2_add_donors(self):
        if not self.env['orphan.sponsorship.orphan'].search_count([]):
            self._log(['⚠  No orphans found. Run Step 1 first.'])
            return self._reopen()

        log = ['📂  Reading donors_data.xlsx ...', '']
        for name, email, phone in DONORS_DATA:
            donor = self.env['orphan.sponsorship.donor'].create({
                'name': name, 'email': email, 'phone': phone, 'state': 'active',
            })
            assigned = self.env['orphan.sponsorship.orphan'].search(
                [('donor_id', '=', donor.id)], limit=1)
            if assigned:
                log.append(f'  + Donor: {name:<22} → auto-assigned → {assigned.name}')
            else:
                log.append(f'  + Donor: {name:<22} → no orphan available')
        log += ['', f'✅  {len(DONORS_DATA)} donors imported — auto-assign complete',
                'Ready for Step 3: Cancel Donors']
        self._log(log)
        return self._reopen()

    # ── STEP 3 : cancel donors (releases orphans) ─────────────────────────
    def action_step3_cancel_donors(self):
        donors = self.env['orphan.sponsorship.donor'].search([('state', '=', 'active')])
        if not donors:
            self._log(['⚠  No active donors to cancel.'])
            return self._reopen()

        log = ['🔄  Cancelling all active donors ...', '']
        for donor in donors:
            orphan_names = ', '.join(donor.orphan_ids.mapped('name')) or 'none'
            donor.action_cancel()
            log.append(f'  - Cancelled: {donor.name:<22} → released: {orphan_names}')
        log += ['', f'✅  All donors cancelled — all orphans back to Unassigned',
                'Demo complete! Use "Reset Demo" to run again.']
        self._log(log)
        return self._reopen()

    # ── RESET ─────────────────────────────────────────────────────────────
    def action_reset(self):
        donors  = self.env['orphan.sponsorship.donor'].search([])
        orphans = self.env['orphan.sponsorship.orphan'].search([])
        d, o = len(donors), len(orphans)
        donors.unlink()
        orphans.unlink()
        self.activity_log = ''
        self._log([f'🗑  Reset complete — deleted {d} donor(s) and {o} orphan(s).',
                   'All clear. Start fresh with Step 1.'])
        return self._reopen()
