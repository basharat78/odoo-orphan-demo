from odoo import models, fields, api


class Donor(models.Model):
    _name = 'orphan.sponsorship.donor'
    _description = 'Donor / Sponsor'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    state = fields.Selection([
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='active', tracking=True)
    orphan_ids = fields.One2many(
        'orphan.sponsorship.orphan', 'donor_id', string='Sponsored Orphans'
    )
    orphan_count = fields.Integer(compute='_compute_orphan_count', string='# Orphans')

    @api.depends('orphan_ids')
    def _compute_orphan_count(self):
        for rec in self:
            rec.orphan_count = len(rec.orphan_ids)

    def action_activate(self):
        self.state = 'active'
        self._auto_assign_orphan()
        return True

    def action_cancel(self):
        self.state = 'cancelled'
        self.orphan_ids.write({'status': 'unassigned', 'donor_id': False})
        return True

    def _auto_assign_orphan(self):
        """Assign the first available unsponsored orphan to this donor."""
        if self.state != 'active':
            return
        unassigned = self.env['orphan.sponsorship.orphan'].search(
            [('status', '=', 'unassigned')], limit=1
        )
        if unassigned:
            unassigned.write({'status': 'sponsored', 'donor_id': self.id})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.state == 'active':
                rec._auto_assign_orphan()
        return records
