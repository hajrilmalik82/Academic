from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean(string="Is a Student", default=False)
    nim = fields.Char(string="Student ID (NIM)")

    khs_ids = fields.One2many(
        'academic.khs', 'student_id', string='KHS Records'
    )
    cgpa = fields.Float(
        string='CGPA', compute='_compute_cgpa', store=True,
        digits=(5, 2), readonly=True
    )

    @api.depends('khs_ids.total_grade_points', 'khs_ids.total_credits')
    def _compute_cgpa(self):
        for record in self:
            total_credits = sum(khs.total_credits for khs in record.khs_ids)
            total_grade_points = sum(khs.total_grade_points for khs in record.khs_ids)
            record.cgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
