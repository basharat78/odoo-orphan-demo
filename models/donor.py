import logging
import json
try:
    import requests as _requests
except ImportError:
    _requests = None

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

SENDER       = 'mbasharat596@gmail.com'
SENDER_NAME  = 'Orphan Sponsorship Team'
BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'


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
        if self.state != 'active':
            return
        unassigned = self.env['orphan.sponsorship.orphan'].search(
            [('status', '=', 'unassigned')], limit=1
        )
        if unassigned:
            unassigned.write({'status': 'sponsored', 'donor_id': self.id})
            self._send_assignment_email(unassigned)

    # ── email body builder ────────────────────────────────────────────────
    def _build_email(self, orphan):
        gender  = 'Boy' if orphan.gender == 'male' else 'Girl'
        subject = f'You are now sponsoring {orphan.name} — Orphan Sponsorship Confirmation'
        body = f"""
<div style="font-family:Arial,sans-serif;max-width:620px;margin:0 auto;background:#f0f4f0;">
  <div style="background:#1F7A4A;padding:36px 30px;text-align:center;border-radius:10px 10px 0 0;">
    <h1 style="color:#fff;margin:0;font-size:26px;">Orphan Sponsorship Program</h1>
    <p style="color:#a8d5b5;margin:8px 0 0;font-size:14px;">Sponsorship Confirmation</p>
  </div>
  <div style="background:#fff;padding:36px 30px;">
    <p style="font-size:17px;color:#222;margin-top:0;">Dear <strong>{self.name}</strong>,</p>
    <p style="color:#555;line-height:1.7;font-size:15px;">
      Congratulations and thank you for your generous heart! Your sponsorship has been
      confirmed. You have been matched with a child who will benefit greatly from your support.
    </p>
    <div style="background:#f8fdf9;border:1px solid #c3e6cb;border-left:5px solid #1F7A4A;
                border-radius:8px;padding:24px 28px;margin:28px 0;">
      <h2 style="color:#1F7A4A;margin:0 0 18px;font-size:17px;">Your Sponsored Child</h2>
      <table style="width:100%;border-collapse:collapse;font-size:15px;">
        <tr>
          <td style="padding:8px 0;color:#888;width:35%;border-bottom:1px solid #eee;">Full Name</td>
          <td style="padding:8px 0;color:#222;font-weight:bold;border-bottom:1px solid #eee;">{orphan.name}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#888;border-bottom:1px solid #eee;">Age</td>
          <td style="padding:8px 0;color:#222;border-bottom:1px solid #eee;">{orphan.age or 'N/A'} years old</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#888;border-bottom:1px solid #eee;">Gender</td>
          <td style="padding:8px 0;color:#222;border-bottom:1px solid #eee;">{gender}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#888;border-bottom:1px solid #eee;">City</td>
          <td style="padding:8px 0;color:#222;border-bottom:1px solid #eee;">{orphan.location or 'N/A'}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#888;vertical-align:top;">About</td>
          <td style="padding:8px 0;color:#555;font-style:italic;">{orphan.notes or 'N/A'}</td>
        </tr>
      </table>
    </div>
    <p style="color:#555;line-height:1.7;font-size:15px;">
      Your sponsorship provides this child with hope, security, and a brighter future.
      Every contribution you make directly impacts their life. We are deeply grateful
      for your kindness and commitment.
    </p>
    <p style="color:#555;font-size:15px;margin-bottom:0;">
      With sincere gratitude,<br/>
      <strong style="color:#1F7A4A;">Orphan Sponsorship Team</strong>
    </p>
  </div>
  <div style="background:#f0f4f0;padding:18px 30px;text-align:center;border-radius:0 0 10px 10px;">
    <p style="color:#aaa;font-size:12px;margin:0;">This email was sent from the Orphan Sponsorship Program.</p>
  </div>
</div>"""
        return subject, body

    # ── send via Brevo HTTP API (works on Railway) ────────────────────────
    def _send_via_brevo_api(self, orphan, api_key):
        subject, body = self._build_email(orphan)
        payload = {
            "sender":      {"name": SENDER_NAME, "email": SENDER},
            "to":          [{"email": self.email, "name": self.name}],
            "subject":     subject,
            "htmlContent": body,
        }
        resp = _requests.post(
            BREVO_API_URL,
            headers={"api-key": api_key, "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=15,
        )
        if resp.status_code in (200, 201):
            _logger.info('Brevo API: email sent to %s (%s) for orphan %s.',
                         self.name, self.email, orphan.name)
        else:
            _logger.error('Brevo API error %s: %s', resp.status_code, resp.text)

    # ── send via Odoo SMTP (works locally) ───────────────────────────────
    def _send_via_odoo_smtp(self, orphan):
        subject, body = self._build_email(orphan)
        mail_server = self.env['ir.mail_server'].search([], limit=1)
        mail = self.env['mail.mail'].sudo().create({
            'subject':        subject,
            'body_html':      body,
            'email_from':     SENDER,
            'email_to':       self.email,
            'auto_delete':    True,
            'mail_server_id': mail_server.id if mail_server else False,
        })
        mail.send()
        _logger.info('SMTP: email sent to %s (%s) for orphan %s.',
                     self.name, self.email, orphan.name)

    # ── main dispatcher ───────────────────────────────────────────────────
    def _send_assignment_email(self, orphan):
        if not self.email:
            _logger.warning('Donor %s has no email — skipping.', self.name)
            return
        try:
            api_key = self.env['ir.config_parameter'].sudo().get_param('brevo.api.key')
            if api_key and _requests:
                self._send_via_brevo_api(orphan, api_key)
            else:
                self._send_via_odoo_smtp(orphan)
        except Exception:
            _logger.exception('Failed to send assignment email to %s.', self.email)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.state == 'active':
                rec._auto_assign_orphan()
        return records
