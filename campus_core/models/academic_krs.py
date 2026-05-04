from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AcademicCoursePackage(models.Model):
    _name = 'academic.course.package'
    _description = 'Academic Course Package'

    name = fields.Char(string='Name', required=True)
    program_id = fields.Many2one('academic.program', string='Program', required=True)
    term_type = fields.Selection([('odd', 'Odd'), ('even', 'Even')], string='Term Type', required=True)
    academic_year_id = fields.Many2one('academic.year', string='Academic Year', required=True)
    total_credits = fields.Integer(string='Total Credits', compute='_compute_total_credits', store=True)
    line_ids = fields.One2many('academic.course.package.line', 'package_id', string='Lines')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('line_ids.credits')
    def _compute_total_credits(self):
        for record in self:
            record.total_credits = sum(record.line_ids.mapped('credits'))


class AcademicCoursePackageLine(models.Model):
    _name = 'academic.course.package.line'
    _description = 'Academic Course Package Line'

    package_id = fields.Many2one('academic.course.package', string='Package', ondelete='cascade')
    subject_id = fields.Many2one('academic.subject', string='Subject', required=True)
    credits = fields.Integer(related='subject_id.credits', string='Credits')

    _sql_constraints = [
        (
            'unique_subject_per_package',
            'unique(package_id, subject_id)',
            'A subject can only appear once in a course package.',
        ),
    ]


class AcademicKrs(models.Model):
    _name = 'academic.krs'
    _description = 'Academic KRS'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='KRS Number', required=True, copy=False, readonly=True, default=lambda self: 'New')
    student_id = fields.Many2one('res.partner', string='Student', required=True, domain=[('is_student', '=', True)])
    academic_year_id = fields.Many2one('academic.year', string='Academic Year', required=True)
    term_type = fields.Selection([('odd', 'Odd'), ('even', 'Even')], string='Term Type', required=True)
    package_id = fields.Many2one('academic.course.package', string='Course Package')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved')], string='Status', default='draft', group_expand='_expand_states', tracking=True)
    total_credits = fields.Integer(string='Total Credits', compute='_compute_total_credits', store=True)
    line_ids = fields.One2many('academic.krs.line', 'krs_id', string='KRS Lines')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    _sql_constraints = [
        (
            'unique_student_academic_period',
            'unique(student_id, academic_year_id, term_type)',
            'A student can only have one KRS for the same academic year and term.',
        ),
    ]

    @api.model
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('academic.krs') or 'New'
        return super().create(vals_list)

    @api.depends('line_ids.credits')
    def _compute_total_credits(self):
        for record in self:
            record.total_credits = sum(record.line_ids.mapped('credits'))

    def action_submit(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("Only draft KRS records can be submitted."))
            if not record.line_ids:
                raise ValidationError(_("Please add at least one subject before submitting the KRS."))
            record.state = 'submitted'

    def action_approve(self):
        for record in self:
            if record.state != 'submitted':
                raise ValidationError(_("Only submitted KRS records can be approved."))
            if not self.env.user.has_group('campus_core.group_campus_administrator'):
                raise ValidationError(_("Only campus administrators can approve KRS records."))
            record.state = 'approved'

    def action_set_draft(self):
        for record in self:
            if record.state == 'approved' and not self.env.user.has_group('campus_core.group_campus_administrator'):
                raise ValidationError(_("Only campus administrators can reset an approved KRS to draft."))
            record.state = 'draft'

    def action_load_package(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("Course packages can only be loaded while the KRS is in draft."))
            if record.package_id:
                record.line_ids.unlink()
                lines = []
                for pkg_line in record.package_id.line_ids:
                    lines.append((0, 0, {
                        'subject_id': pkg_line.subject_id.id,
                    }))
                record.write({'line_ids': lines})


class AcademicKrsLine(models.Model):
    _name = 'academic.krs.line'
    _description = 'Academic KRS Line'

    krs_id = fields.Many2one('academic.krs', string='KRS', ondelete='cascade')
    subject_id = fields.Many2one('academic.subject', string='Subject', required=True)
    credits = fields.Integer(related='subject_id.credits', string='Credits')

    _sql_constraints = [
        (
            'unique_subject_per_krs',
            'unique(krs_id, subject_id)',
            'A subject can only appear once in the same KRS.',
        ),
    ]
