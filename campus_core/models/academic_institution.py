from odoo import fields, models


class AcademicFaculty(models.Model):
    _name = 'academic.faculty'
    _description = 'Academic Faculty'

    name = fields.Char(string='Name', required=True)
    dean_id = fields.Many2one('hr.employee', string="Head of Faculty / Dean")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )


class AcademicProgram(models.Model):
    _name = 'academic.program'
    _description = 'Academic Program'

    name = fields.Char(string='Name', required=True)
    faculty_id = fields.Many2one(
        'academic.faculty', string='Faculty', required=True
    )
    head_id = fields.Many2one('hr.employee', string="Head of Program")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )
