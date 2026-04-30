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


class AcademicSubject(models.Model):
    _name = 'academic.subject'
    _description = 'Academic Subject'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    credits = fields.Integer(string='Credits', default=2)
    term_type = fields.Selection([
        ('odd', 'Odd'),
        ('even', 'Even'),
        ('both', 'Both')
    ], string='Term Type', required=True)
    program_id = fields.Many2one(
        'academic.program', string='Program', required=True
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )


class AcademicYear(models.Model):
    _name = 'academic.year'
    _description = 'Academic Year'

    name = fields.Char(string='Name', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )
