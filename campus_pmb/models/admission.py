from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CampusAdmission(models.Model):
    _name = 'campus.admission'
    _description = 'New Student Admission'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Applicant Name', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    previous_school = fields.Char(string='Previous School', tracking=True)

    registration_date = fields.Date(
        string='Registration Date', default=fields.Date.context_today, tracking=True
    )
    program_id = fields.Many2one(
        'academic.program', string='Program', required=True, tracking=True
    )
    academic_year_id = fields.Many2one(
        'academic.year', string='Academic Year', required=True, tracking=True
    )

    partner_id = fields.Many2one(
        'res.partner', string='Student Profile', readonly=True, tracking=True
    )
    user_id = fields.Many2one(
        'res.users', string='Portal User', readonly=True, tracking=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)

    _sql_constraints = [
        (
            'email_unique',
            'unique(email)',
            'An admission record already exists for this email address.'
        ),
    ]

    def action_in_progress(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only draft applications can be moved to in progress."))
            record.state = 'in_progress'

    def action_reject(self):
        for record in self:
            if record.state not in ('draft', 'in_progress'):
                raise UserError(_("Only draft or in-progress applications can be rejected."))
            record.state = 'rejected'

    def action_pass(self):
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_("Only in-progress applications can be marked as passed."))
            record.state = 'passed'

    def action_create_account(self):
        for record in self:
            if record.state != 'passed':
                raise UserError(_("Only accepted applicants can have a portal account created."))
            
            if not record.email:
                raise UserError(_("Email is required to create a Portal account."))
                
            if record.user_id:
                raise UserError(_("A portal account has already been created."))
                
            # Check if user with this email already exists in the system
            existing_user = self.env['res.users'].search([('login', '=', record.email)], limit=1)
            if existing_user:
                # If exists, just link it to avoid duplicate constraint error
                record.user_id = existing_user.id
                record.partner_id = existing_user.partner_id.id
                # Ensure partner is marked as student
                existing_user.partner_id.is_student = True
                continue
            
            # Create Partner
            partner = self.env['res.partner'].create({
                'name': record.name,
                'email': record.email,
                'phone': record.phone,
                'is_student': True,
                'company_id': self.env.company.id,
            })
            record.partner_id = partner.id

            # Create User
            portal_group = self.env.ref('base.group_portal')
            user = self.env['res.users'].create({
                'name': record.name,
                'login': record.email,
                'partner_id': partner.id,
                'groups_id': [(6, 0, [portal_group.id])],
                'company_id': self.env.company.id,
            })
            record.user_id = user.id
