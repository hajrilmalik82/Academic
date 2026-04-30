from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_lecturer = fields.Boolean(string="Is a Lecturer", default=False)
    nidn = fields.Char(string="NIDN (Nomor Induk Dosen Nasional)")
    academic_rank = fields.Selection([
        ('asisten_ahli', 'Asisten Ahli'),
        ('lektor', 'Lektor'),
        ('lektor_kepala', 'Lektor Kepala'),
        ('guru_besar', 'Guru Besar')
    ], string="Academic Rank")
    faculty_id = fields.Many2one('academic.faculty', string="Faculty")
    program_id = fields.Many2one(
        'academic.program', 
        string="Program", 
        domain="[('faculty_id', '=', faculty_id)]"
    )
