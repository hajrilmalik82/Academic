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
        cls.academic_year = cls.env['academic.year'].create({
            'name': '2026/2027',
            'krs_start_date': '2026-01-01',
            'krs_end_date': '2026-12-31',
        })
        cls.advisor_user = cls.env['res.users'].create({
            'name': 'Advisor User',
            'login': 'advisor@example.com',
            'email': 'advisor@example.com',
        })
        cls.advisor = cls.env['hr.employee'].create({
            'name': 'Academic Advisor',
            'user_id': cls.advisor_user.id,
            'is_lecturer': True,
        })
        cls.student = cls.env['res.partner'].create({
            'name': 'Student One',
            'is_student': True,
            'program_id': cls.program.id,
            'academic_advisor_id': cls.advisor.id,
            'student_status': 'active',
        })
        cls.subject = cls.env['academic.subject'].create({
            'name': 'Algorithms',
            'code': 'CS101',
            'credits': 3,
            'term_type': 'odd',
            'program_id': cls.program.id,
        })
        cls.building = cls.env['campus.building'].create({
            'name': 'Main Building',
            'location': 'Campus A',
        })
        cls.room = cls.env['campus.room'].create({
            'name': 'Room 101',
            'building_id': cls.building.id,
            'capacity': 30,
            'room_type': 'theory',
        })
        cls.academic_class = cls._create_class(cls.subject, 8.0, 10.0)

    @classmethod
    def _create_class(cls, subject, start_time, end_time, room=None):
        academic_class = cls.env['academic.class'].create({
            'subject_id': subject.id,
            'academic_year_id': cls.academic_year.id,
            'start_date': '2026-09-01',
        })
        cls.env['academic.class.schedule'].create({
            'class_id': academic_class.id,
            'day_of_week': '0',
            'start_time': start_time,
            'end_time': end_time,
            'room_id': (room or cls.room).id,
        })
        return academic_class

    def _create_krs(self, term_type='odd', class_record=None):
        return self.env['academic.krs'].create({
            'student_id': self.student.id,
            'academic_year_id': self.academic_year.id,
            'term_type': term_type,
            'line_ids': [(0, 0, {'class_id': (class_record or self.academic_class).id})],
        })

    def test_krs_unique_per_student_year_and_term(self):
        self._create_krs(term_type='odd')
        self._create_krs(term_type='even')

        with self.assertRaises(Exception):
            self._create_krs(term_type='odd')

    def test_krs_requires_lines_before_submit(self):
        krs = self.env['academic.krs'].create({
            'student_id': self.student.id,
            'academic_year_id': self.academic_year.id,
            'term_type': 'odd',
        })

        with self.assertRaises(ValidationError):
            krs.action_submit()

    def test_krs_locked_records_cannot_be_edited(self):
        krs = self._create_krs()
        krs.action_submit()
        krs.with_user(self.advisor_user).action_approve()
        krs.action_lock()

        with self.assertRaises(ValidationError):
            krs.write({'term_type': 'even'})

    def test_krs_prerequisite_requires_passing_grade(self):
        prerequisite = self.env['academic.subject'].create({
            'name': 'Basic Programming',
            'code': 'CS100',
            'credits': 3,
            'term_type': 'odd',
            'program_id': self.program.id,
        })
        advanced = self.env['academic.subject'].create({
            'name': 'Advanced Algorithms',
            'code': 'CS201',
            'credits': 3,
            'term_type': 'odd',
            'program_id': self.program.id,
            'prerequisite_ids': [(6, 0, [prerequisite.id])],
        })
        advanced_class = self._create_class(advanced, 11.0, 13.0)
        krs = self._create_krs(class_record=advanced_class)

        with self.assertRaises(ValidationError):
            krs.action_submit()

    def test_khs_requires_approved_or_locked_krs(self):
        with self.assertRaises(ValidationError):
            self.env['academic.khs'].create({
                'student_id': self.student.id,
                'academic_year_id': self.academic_year.id,
                'term_type': 'odd',
            })

    def test_room_capacity_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self.env['campus.room'].create({
                'name': 'Invalid Room',
                'building_id': self.building.id,
                'capacity': 0,
                'room_type': 'theory',
            })

    def test_schedule_end_time_after_start_time(self):
        with self.assertRaises(ValidationError):
            self.env['academic.class.schedule'].create({
                'class_id': self.academic_class.id,
                'day_of_week': '1',
                'start_time': 10.0,
                'end_time': 9.0,
                'room_id': self.room.id,
            })

    def test_grade_conversion_and_term_gpa(self):
        krs = self._create_krs()
        krs.action_submit()
        krs.with_user(self.advisor_user).action_approve()

        khs = self.env['academic.khs'].create({
            'student_id': self.student.id,
            'academic_year_id': self.academic_year.id,
            'term_type': 'odd',
            'line_ids': [(0, 0, {
                'subject_id': self.subject.id,
                'numeric_grade': 80.0,
            })],
        })

        self.assertEqual(khs.line_ids.letter_grade, 'A')
        self.assertEqual(khs.line_ids.grade_points, 4.0)
        self.assertEqual(khs.term_gpa, 4.0)

    def test_grade_scale_boundaries(self):
        line_model = self.env['academic.khs.line']

        self.assertEqual(line_model._get_grade_from_score(79.99), ('A-', 3.75))
        self.assertEqual(line_model._get_grade_from_score(80.0), ('A', 4.0))
        self.assertEqual(line_model._get_grade_from_score(39.99), ('E', 0.0))
        self.assertEqual(line_model._get_grade_from_score(40.0), ('D', 1.0))

    def test_numeric_grade_range(self):
        krs = self._create_krs()
        krs.action_submit()
        krs.with_user(self.advisor_user).action_approve()

        with self.assertRaises(Exception):
            self.env['academic.khs'].create({
                'student_id': self.student.id,
                'academic_year_id': self.academic_year.id,
                'term_type': 'odd',
                'line_ids': [(0, 0, {
                    'subject_id': self.subject.id,
                    'numeric_grade': 101.0,
                })],
            })
