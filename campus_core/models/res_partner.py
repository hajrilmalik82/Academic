from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean(string=_("Is a Student"), default=False)
    nim = fields.Char(string=_("Student ID (NIM)"))
    
    academic_advisor_id = fields.Many2one('hr.employee', string=_("Academic Advisor"))
    program_id = fields.Many2one('academic.program', string=_("Study Program"))
    student_status = fields.Selection([
        ('active', _('Active')),
        ('leave', _('On Leave')),
        ('graduated', _('Graduated')),
        ('dropout', _('Drop Out'))
    ], default='active', string=_("Status"))
    batch_year = fields.Char(string=_("Batch / Generation"))

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
