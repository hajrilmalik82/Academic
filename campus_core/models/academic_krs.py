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

    name = fields.Char(string=_('KRS Number'), required=True, copy=False, readonly=True, default=lambda self: 'New')
    student_id = fields.Many2one('res.partner', string=_('Student'), required=True, domain=[('is_student', '=', True)])
    academic_year_id = fields.Many2one('academic.year', string=_('Academic Year'), required=True)
    term_type = fields.Selection([('odd', _('Odd')), ('even', _('Even'))], string=_('Term Type'), required=True)
    
    advisor_id = fields.Many2one('hr.employee', related='student_id.academic_advisor_id', string=_('Academic Advisor'), readonly=True)
    program_id = fields.Many2one('academic.program', related='student_id.program_id', string=_('Study Program'), readonly=True)
    
    package_id = fields.Many2one('academic.course.package', string=_('Course Package'))
    state = fields.Selection([
        ('draft', _('Draft')), 
        ('submitted', _('Waiting for Approval')), 
        ('approved', _('Approved')),
        ('revision', _('Needs Revision')),
        ('rejected', _('Rejected')),
        ('locked', _('Locked'))
    ], string=_('Status'), default='draft', group_expand='_expand_states', tracking=True)
    
    total_credits = fields.Integer(string=_('Total Credits'), compute='_compute_total_credits', store=True)
    line_ids = fields.One2many('academic.krs.line', 'krs_id', string=_('KRS Lines'))
    company_id = fields.Many2one('res.company', string=_('Company'), default=lambda self: self.env.company)

    _sql_constraints = [
        (
            'unique_student_academic_period',
            'unique(student_id, academic_year_id)',
            'A student can only have one KRS per academic year.'
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
            if record.state not in ('draft', 'revision'):
                raise ValidationError(_("Only draft or revision KRS records can be submitted."))
            if not record.line_ids:
                raise ValidationError(_("Please add at least one class before submitting the KRS."))
                
            # 1. Student Status
            if record.student_id.student_status != 'active':
                raise ValidationError(_("Student status must be active to submit a KRS."))
                
            # 2. Period Open
            today = fields.Date.context_today(self)
            if not record.academic_year_id.krs_start_date or not record.academic_year_id.krs_end_date:
                raise ValidationError(_("Academic year KRS period is not configured."))
            if not (record.academic_year_id.krs_start_date <= today <= record.academic_year_id.krs_end_date):
                raise ValidationError(_("Current date is outside the allowed KRS period."))
                
            # 3. Has Advisor
            if not record.advisor_id:
                raise ValidationError(_("The student must have an assigned Academic Advisor."))
                
            # 4. Max SKS Limit (Fixed 24 for now)
            if record.total_credits > 24:
                raise ValidationError(_("Total credits cannot exceed 24 SKS."))
                
            # Validate Line constraints
            taken_subjects = []
            schedules = []
            
            for line in record.line_ids:
                subject = line.subject_id
                
                # 5. Subject Matches Program
                if subject.program_id and record.program_id and subject.program_id != record.program_id:
                    raise ValidationError(_("Subject '%s' does not belong to the student's program.") % subject.name)
                    
                # 6. No Duplicate Subjects
                if subject.id in taken_subjects:
                    raise ValidationError(_("Student cannot take the same subject '%s' twice in one KRS.") % subject.name)
                taken_subjects.append(subject.id)
                
                # 7. Prerequisites Met
                # TODO: Integrate with KHS/Grades later
                # if subject.prerequisite_ids:
                #    check if student passed them
                
                # 8. Class Quota
                class_record = line.class_id
                total_capacity = sum(class_record.schedule_ids.mapped('room_capacity'))
                enrolled_students = len(class_record.student_line_ids)
                if enrolled_students >= total_capacity:
                    raise ValidationError(_("Class '%s' has reached its maximum capacity.") % class_record.name)
                    
                # Collect schedules for overlap check
                for sched in class_record.schedule_ids:
                    schedules.append({
                        'day': sched.day_of_week,
                        'start': sched.start_time,
                        'end': sched.end_time,
                        'name': f"{class_record.name} - {dict(sched._fields['day_of_week'].selection).get(sched.day_of_week)} {sched.start_time}-{sched.end_time}"
                    })
                    
            # 9. No Schedule Overlap
            for i, s1 in enumerate(schedules):
                for j, s2 in enumerate(schedules):
                    if i != j and s1['day'] == s2['day']:
                        if s1['start'] < s2['end'] and s1['end'] > s2['start']:
                            raise ValidationError(_("Schedule overlap detected between:\n%s\n%s") % (s1['name'], s2['name']))

            record.state = 'submitted'

    def action_approve(self):
        for record in self:
            if record.state != 'submitted':
                raise ValidationError(_("Only submitted KRS records can be approved."))
            
            # Security
            user = self.env.user
            if user.employee_id != record.advisor_id and not user.has_group('campus_core.group_campus_administrator'):
                raise ValidationError(_("Only the assigned Academic Advisor or Academic Admin can approve this KRS."))
                
            # Class Enrollment
            for line in record.line_ids:
                existing = self.env['academic.class.student.line'].search([
                    ('class_id', '=', line.class_id.id),
                    ('student_id', '=', record.student_id.id)
                ])
                if not existing:
                    self.env['academic.class.student.line'].create({
                        'class_id': line.class_id.id,
                        'student_id': record.student_id.id,
                        'schedule_ids': [(6, 0, line.class_id.schedule_ids.ids)]
                    })
                    
            record.state = 'approved'

    def action_request_revision(self):
        for record in self:
            record.state = 'revision'

    def action_reject(self):
        for record in self:
            record.state = 'rejected'

    def action_lock(self):
        for record in self:
            record.state = 'locked'

    def action_set_draft(self):
        for record in self:
            if record.state == 'approved' and not self.env.user.has_group('campus_core.group_campus_administrator'):
                raise ValidationError(_("Only campus administrators can reset an approved KRS to draft."))
            record.state = 'draft'


class AcademicKrsLine(models.Model):
    _name = 'academic.krs.line'
    _description = 'Academic KRS Line'

    krs_id = fields.Many2one('academic.krs', string=_('KRS'), ondelete='cascade')
    class_id = fields.Many2one('academic.class', string=_('Class'), required=True)
    subject_id = fields.Many2one('academic.subject', related='class_id.subject_id', string=_('Subject'), store=True)
    credits = fields.Integer(related='subject_id.credits', string=_('Credits'), store=True)

    _sql_constraints = [
        (
            'unique_class_per_krs',
            'unique(krs_id, class_id)',
            'A class can only appear once in the same KRS.'
        ),
    ]
