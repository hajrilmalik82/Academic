from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAcademicRules(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.faculty = cls.env['academic.faculty'].create({'name': 'Engineering'})
        cls.program = cls.env['academic.program'].create({
            'name': 'Computer Science',
            'faculty_id': cls.faculty.id,
        })
        cls.academic_year = cls.env['academic.year'].create({'name': '2026/2027'})
        cls.student = cls.env['res.partner'].create({
            'name': 'Student One',
            'is_student': True,
        })
        cls.subject = cls.env['academic.subject'].create({
            'name': 'Algorithms',
            'code': 'CS101',
            'credits': 3,
            'term_type': 'odd',
            'program_id': cls.program.id,
        })

    def test_krs_unique_per_period(self):
        self.env['academic.krs'].create({
            'student_id': self.student.id,
            'academic_year_id': self.academic_year.id,
            'term_type': 'odd',
        })

        with self.assertRaises(Exception):
            self.env['academic.krs'].create({
                'student_id': self.student.id,
                'academic_year_id': self.academic_year.id,
                'term_type': 'odd',
            })

    def test_krs_requires_lines_before_submit(self):
        krs = self.env['academic.krs'].create({
            'student_id': self.student.id,
            'academic_year_id': self.academic_year.id,
            'term_type': 'odd',
        })

        with self.assertRaises(ValidationError):
            krs.action_submit()

    def test_khs_requires_approved_krs(self):
        with self.assertRaises(ValidationError):
            self.env['academic.khs'].create({
                'student_id': self.student.id,
                'academic_year_id': self.academic_year.id,
                'term_type': 'odd',
            })

    def test_room_capacity_must_be_positive(self):
        building = self.env['campus.building'].create({
            'name': 'Main Building',
            'location': 'Campus A',
        })

        with self.assertRaises(ValidationError):
            self.env['campus.room'].create({
                'name': 'Room 101',
                'building_id': building.id,
                'capacity': 0,
                'room_type': 'theory',
            })

    def test_schedule_end_time_after_start_time(self):
        building = self.env['campus.building'].create({
            'name': 'Science Building',
            'location': 'Campus A',
        })
        room = self.env['campus.room'].create({
            'name': 'Room 201',
            'building_id': building.id,
            'capacity': 30,
            'room_type': 'theory',
        })
        academic_class = self.env['academic.class'].create({
            'subject_id': self.subject.id,
            'academic_year_id': self.academic_year.id,
            'start_date': '2026-09-01',
        })

        with self.assertRaises(ValidationError):
            self.env['academic.class.schedule'].create({
                'class_id': academic_class.id,
                'day_of_week': '0',
                'start_time': 10.0,
                'end_time': 9.0,
                'room_id': room.id,
            })
