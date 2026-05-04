from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, time, timedelta
import pytz


class AcademicClass(models.Model):
    _name = 'academic.class'
    _description = 'Academic Class'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Class Name', compute='_compute_class_name', store=True, tracking=True)
    subject_id = fields.Many2one('academic.subject', string='Subject', required=True, tracking=True)
    academic_year_id = fields.Many2one('academic.year', string='Academic Year', required=True, tracking=True)
    start_date = fields.Date(string='Start Date', required=True, tracking=True, help="Used as the starting point to generate 14 sessions.")
    class_capacity_display = fields.Char(string='Total Class Capacity', compute='_compute_class_capacity_display')
    schedule_ids = fields.One2many('academic.class.schedule', 'class_id', string='Schedules')
    student_line_ids = fields.One2many('academic.class.student.line', 'class_id', string='Students')
    session_ids = fields.One2many('academic.class.session', 'class_id', string='Sessions')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('subject_id', 'academic_year_id')
    def _compute_class_name(self):
        for record in self:
            if record.subject_id and record.academic_year_id:
                record.name = f"{record.subject_id.name} - {record.academic_year_id.name}"
            else:
                record.name = "New Class"

    @api.depends('schedule_ids.room_capacity', 'student_line_ids')
    def _compute_class_capacity_display(self):
        for record in self:
            total_capacity = sum(record.schedule_ids.mapped('room_capacity'))
            total_students = len(record.student_line_ids)
            record.class_capacity_display = f"{total_capacity} / {total_students}"

    def action_generate_sessions(self):
        self.ensure_one()
        if not self.start_date:
            raise ValidationError("Please set a Start Date to generate sessions.")
        if not self.schedule_ids:
            raise ValidationError("Please define at least one schedule to generate sessions.")

        self.session_ids.unlink()

        # Get user's timezone; fall back to UTC if not set
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')

        sessions = []
        for schedule in self.schedule_ids:
            current_date = fields.Date.from_string(self.start_date)
            # Find the first date matching schedule.day_of_week
            # weekday() returns 0 for Monday, 6 for Sunday
            target_weekday = int(schedule.day_of_week)
            days_ahead = target_weekday - current_date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            first_session_date = current_date + timedelta(days=days_ahead)

            for i in range(14):
                session_date = first_session_date + timedelta(weeks=i)

                # Extract hours and minutes from Float fields
                start_hour = int(schedule.start_time)
                start_minute = int(round((schedule.start_time - start_hour) * 60))
                end_hour = int(schedule.end_time)
                end_minute = int(round((schedule.end_time - end_hour) * 60))

                # Combine date + time as naive local datetime, then convert to UTC
                local_start_dt = datetime.combine(session_date, time(start_hour, start_minute))
                local_end_dt = datetime.combine(session_date, time(end_hour, end_minute))

                utc_start_dt = user_tz.localize(local_start_dt).astimezone(pytz.utc).replace(tzinfo=None)
                utc_end_dt = user_tz.localize(local_end_dt).astimezone(pytz.utc).replace(tzinfo=None)

                sessions.append((0, 0, {
                    'name': f"Session {i + 1}: {self.name}",
                    'start_datetime': utc_start_dt,
                    'end_datetime': utc_end_dt,
                    'room_id': schedule.room_id.id,
                    'lecturer_id': schedule.lecturer_id.id,
                }))

        self.write({'session_ids': sessions})




class AcademicClassStudentLine(models.Model):
    _name = 'academic.class.student.line'
    _description = 'Academic Class Student Line'
    _sql_constraints = [
        (
            'student_class_unique',
            'unique(student_id, class_id)',
            'A student can only be enrolled once in the same class.',
        ),
    ]

    class_id = fields.Many2one('academic.class', string='Class', ondelete='cascade')
    student_id = fields.Many2one('res.partner', string='Student', required=True, domain=[('is_student', '=', True)])
    schedule_ids = fields.Many2many('academic.class.schedule', string='Schedules', domain="[('class_id', '=', class_id)]")

    @api.constrains('student_id', 'class_id')
    def _check_krs_approval(self):
        for record in self:
            if not record.student_id or not record.class_id:
                continue

            krs_line = self.env['academic.krs.line'].search([
                ('krs_id.student_id', '=', record.student_id.id),
                ('krs_id.state', '=', 'approved'),
                ('krs_id.academic_year_id', '=', record.class_id.academic_year_id.id),
                ('subject_id', '=', record.class_id.subject_id.id)
            ], limit=1)

            if not krs_line:
                raise ValidationError(f"Gagal! Mahasiswa {record.student_id.name} belum mendaftarkan KRS untuk Mata Kuliah {record.class_id.subject_id.name} pada tahun ajaran ini, atau status KRS belum di-Approve.")

    @api.constrains('schedule_ids')
    def _check_schedule_capacity(self):
        for record in self:
            for schedule in record.schedule_ids:
                enrolled = self.search_count([
                    ('class_id', '=', record.class_id.id),
                    ('schedule_ids', 'in', schedule.id),
                ])
                if enrolled > schedule.room_capacity:
                    raise ValidationError(
                        f"Schedule {schedule.display_name} exceeds room capacity."
                    )


class AcademicClassSession(models.Model):
    _name = 'academic.class.session'
    _description = 'Academic Class Session'

    name = fields.Char(string='Name', required=True)
    class_id = fields.Many2one('academic.class', string='Class', ondelete='cascade')
    start_datetime = fields.Datetime(string='Start Datetime', required=True)
    end_datetime = fields.Datetime(string='End Datetime', required=True)
    room_id = fields.Many2one('campus.room', string='Room')
    lecturer_id = fields.Many2one('hr.employee', string='Lecturer')

    @api.constrains('start_datetime', 'end_datetime')
    def _check_session_datetime(self):
        for record in self:
            if (
                record.start_datetime
                and record.end_datetime
                and record.end_datetime <= record.start_datetime
            ):
                raise ValidationError("Session end datetime must be after start datetime.")
