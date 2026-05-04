from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAdmissionWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.faculty = cls.env['academic.faculty'].create({'name': 'Business'})
        cls.program = cls.env['academic.program'].create({
            'name': 'Management',
            'faculty_id': cls.faculty.id,
        })
        cls.academic_year = cls.env['academic.year'].create({'name': '2026/2027'})

    def _create_admission(self, email='applicant@example.com'):
        return self.env['campus.admission'].create({
            'name': 'Applicant One',
            'email': email,
            'program_id': self.program.id,
            'academic_year_id': self.academic_year.id,
        })

    def test_admission_state_flow_is_enforced(self):
        admission = self._create_admission()

        with self.assertRaises(UserError):
            admission.action_pass()

        admission.action_in_progress()
        admission.action_pass()
        self.assertEqual(admission.state, 'passed')

        with self.assertRaises(UserError):
            admission.action_reject()

    def test_create_account_requires_passed_admission(self):
        admission = self._create_admission('second@example.com')

        with self.assertRaises(UserError):
            admission.action_create_account()

    def test_create_account_creates_student_portal_user(self):
        admission = self._create_admission('accepted@example.com')
        admission.action_in_progress()
        admission.action_pass()
        admission.action_create_account()

        self.assertTrue(admission.partner_id.is_student)
        self.assertEqual(admission.user_id.login, 'accepted@example.com')
        self.assertIn(self.env.ref('base.group_portal'), admission.user_id.groups_id)
