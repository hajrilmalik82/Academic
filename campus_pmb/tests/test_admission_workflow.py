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

    def _add_verified_required_document(self, admission):
        document = admission.document_line_ids[:1]
        document.received = True
        return document

    def test_admission_state_flow_is_enforced(self):
        admission = self._create_admission()
        self.assertNotEqual(admission.registration_number, 'New')

        with self.assertRaises(UserError):
            admission.action_accept()

        admission.action_submit()
        admission.action_start_document_review()
        admission.document_line_ids.write({'received': True})
        admission.action_verify_documents()
        admission.payment_reference = 'PAY-001'
        admission.action_verify_payment()
        admission.action_accept()
        self.assertEqual(admission.state, 'accepted')

        with self.assertRaises(UserError):
            admission.action_reject()

    def test_document_verification_requires_required_documents(self):
        admission = self._create_admission('document@example.com')
        admission.action_submit()
        admission.action_start_document_review()

        with self.assertRaises(UserError):
            admission.action_verify_documents()

        admission.document_line_ids.write({'received': True})
        admission.action_verify_documents()
        self.assertEqual(admission.state, 'payment_pending')

    def test_create_account_requires_accepted_admission(self):
        admission = self._create_admission('second@example.com')

        with self.assertRaises(UserError):
            admission.action_create_account()

    def test_create_account_creates_student_portal_user(self):
        admission = self._create_admission('accepted@example.com')
        admission.action_submit()
        admission.action_start_document_review()
        admission.document_line_ids.write({'received': True})
        admission.action_verify_documents()
        admission.payment_reference = 'PAY-002'
        admission.action_verify_payment()
        admission.action_accept()
        admission.action_register()

        self.assertEqual(admission.state, 'registered')
        self.assertTrue(admission.partner_id.is_student)
        self.assertEqual(admission.user_id.login, 'accepted@example.com')
        self.assertIn(self.env.ref('base.group_portal'), admission.user_id.groups_id)
