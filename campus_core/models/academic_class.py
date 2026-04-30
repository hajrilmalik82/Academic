from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta
import math


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
                
                # Convert float time to datetime
                start_hour = int(math.floor(schedule.start_time))
                start_minute = int(round((schedule.start_time - start_hour) * 60))
                end_hour = int(math.floor(schedule.end_time))
                end_minute = int(round((schedule.end_time - end_hour) * 60))
                
                start_dt = fields.Datetime.to_datetime(session_date).replace(
                    hour=start_hour, minute=start_minute
                )
                end_dt = fields.Datetime.to_datetime(session_date).replace(
                    hour=end_hour, minute=end_minute
                )

                sessions.append((0, 0, {
                    'name': f"Session {i+1}: {self.name}",
                    'start_datetime': start_dt,
                    'end_datetime': end_dt,
                    'room_id': schedule.room_id.id,
                }))
        
        self.write({'session_ids': sessions})


class AcademicClassSchedule(models.Model):
    _name = 'academic.class.schedule'
    _description = 'Academic Class Schedule'

    class_id = fields.Many2one('academic.class', string='Class', ondelete='cascade')
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Day of Week', required=True)
    start_time = fields.Float(string='Start Time', required=True)
    end_time = fields.Float(string='End Time', required=True)
    room_id = fields.Many2one('campus.room', string='Room', required=True, domain=[('room_type', '=', 'theory')])
    room_capacity = fields.Integer(related='room_id.capacity', string='Capacity', readonly=True)
    lecturer_id = fields.Many2one('hr.employee', string='Lecturer')
    enrolled_count = fields.Integer(string='Enrolled', compute='_compute_capacity_display')
    capacity_display = fields.Char(string='Capacity (Max/Filled)', compute='_compute_capacity_display')

    @api.depends('room_capacity', 'class_id.student_line_ids.schedule_ids')
    def _compute_capacity_display(self):
        for record in self:
            enrolled = len(record.class_id.student_line_ids.filtered(lambda s: record.id in s.schedule_ids.ids))
            record.enrolled_count = enrolled
            record.capacity_display = f"{record.room_capacity} / {enrolled}"

    def _compute_display_name(self):
        for record in self:
            day_dict = dict(self._fields['day_of_week'].selection)
            day_name = day_dict.get(record.day_of_week, '')
            start = '{0:02d}:{1:02d}'.format(
                int(record.start_time), int(round((record.start_time % 1) * 60))
            ) if record.start_time else ''
            end = '{0:02d}:{1:02d}'.format(
                int(record.end_time), int(round((record.end_time % 1) * 60))
            ) if record.end_time else ''
            record.display_name = f"{day_name} ({start} - {end})"

    @api.constrains('day_of_week', 'start_time', 'end_time', 'room_id', 'lecturer_id', 'class_id')
    def _check_schedule_overlap(self):
        for record in self:
            # Check room overlap
            domain_room = [
                ('id', '!=', record.id),
                ('room_id', '=', record.room_id.id),
                ('day_of_week', '=', record.day_of_week),
                ('academic_year_id', '=', record.class_id.academic_year_id.id),
                ('start_time', '<', record.end_time),
                ('end_time', '>', record.start_time),
            ]
            # Since academic_year_id is on class, we need to join or map
            # A simpler approach using ORM search:
            overlap_room = self.search([
                ('id', '!=', record.id),
                ('room_id', '=', record.room_id.id),
                ('day_of_week', '=', record.day_of_week),
                ('class_id.academic_year_id', '=', record.class_id.academic_year_id.id),
                ('start_time', '<', record.end_time),
                ('end_time', '>', record.start_time),
            ])
            if overlap_room:
                raise ValidationError(f"Room overlap detected on {record.display_name}")

            # Check lecturer overlap
            overlap_lecturer = self.search([
                ('id', '!=', record.id),
                ('lecturer_id', '=', record.lecturer_id.id),
                ('day_of_week', '=', record.day_of_week),
                ('class_id.academic_year_id', '=', record.class_id.academic_year_id.id),
                ('start_time', '<', record.end_time),
                ('end_time', '>', record.start_time),
            ])
            if overlap_lecturer:
                raise ValidationError(f"Lecturer overlap detected on {record.display_name}")


class AcademicClassStudentLine(models.Model):
    _name = 'academic.class.student.line'
    _description = 'Academic Class Student Line'

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


class AcademicClassSession(models.Model):
    _name = 'academic.class.session'
    _description = 'Academic Class Session'

    name = fields.Char(string='Name', required=True)
    class_id = fields.Many2one('academic.class', string='Class', ondelete='cascade')
    start_datetime = fields.Datetime(string='Start Datetime', required=True)
    end_datetime = fields.Datetime(string='End Datetime', required=True)
    room_id = fields.Many2one('campus.room', string='Room')
    lecturer_id = fields.Many2one('hr.employee', string='Lecturer')
