from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean(string="Is a Student", default=False)
    nim = fields.Char(string="NIM (Student ID)")
