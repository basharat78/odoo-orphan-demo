from odoo import models, fields


class Orphan(models.Model):
    _name = 'orphan.sponsorship.orphan'
    _description = 'Orphan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    location = fields.Char(string='Location')
    notes = fields.Text(string='Notes')
    status = fields.Selection([
        ('unassigned', 'Unassigned'),
        ('sponsored', 'Sponsored'),
    ], string='Status', default='unassigned', tracking=True)
    donor_id = fields.Many2one('orphan.sponsorship.donor', string='Sponsor', tracking=True)
