from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AcademicSubject(models.Model):
    _name = 'academic.subject'
    _description = 'Academic Subject'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    credits = fields.Integer(string='Credits (SKS)', default=2)
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

    _sql_constraints = [
        (
            'code_program_unique',
            'unique(code, program_id)',
            'Subject code must be unique within a program.',
        ),
    ]

    @api.constrains('credits')
    def _check_credits(self):
        for record in self:
            if record.credits <= 0:
                raise ValidationError(_("Credits must be greater than zero."))


class AcademicYear(models.Model):
    _name = 'academic.year'
    _description = 'Academic Year'

    name = fields.Char(string='Name', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )
