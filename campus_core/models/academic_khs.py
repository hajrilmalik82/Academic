from odoo import api, fields, models
from odoo.exceptions import UserError


class AcademicKhs(models.Model):
    _name = 'academic.khs'
    _description = 'Kartu Hasil Studi (KHS)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='KHS Number', required=True, copy=False,
        readonly=True, default=lambda self: 'New'
    )
    student_id = fields.Many2one(
        'res.partner', string='Student', required=True,
        domain=[('is_student', '=', True)]
    )
    academic_year_id = fields.Many2one(
        'academic.year', string='Academic Year', required=True
    )
    term_type = fields.Selection([
        ('odd', 'Odd'),
        ('even', 'Even')
    ], string='Term Type', required=True)
    khs_line_ids = fields.One2many(
        'academic.khs.line', 'khs_id', string='Grades'
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('academic.khs') or 'New'
        return super().create(vals_list)

    @api.onchange('student_id', 'academic_year_id', 'term_type')
    def _onchange_pull_krs_data(self):
        # Jika ketiga field utama sudah terisi
        if self.student_id and self.academic_year_id and self.term_type:
            # Cari KRS yang sudah di-approve
            krs = self.env['academic.krs'].search([
                ('student_id', '=', self.student_id.id),
                ('academic_year_id', '=', self.academic_year_id.id),
                ('term_type', '=', self.term_type),
                ('state', '=', 'approved')
            ], limit=1)

            # Kosongkan line yang ada sebelumnya (mencegah duplikasi jika user ganti nama mahasiswa)
            lines = [(5, 0, 0)] 

            if krs:
                # Masukkan subject dari KRS ke dalam KHS
                for line in krs.line_ids:
                    lines.append((0, 0, {
                        'subject_id': line.subject_id.id,
                    }))
                self.khs_line_ids = lines
            else:
                self.khs_line_ids = False
                # Munculkan pop-up warning
                return {
                    'warning': {
                        'title': "Informasi KRS",
                        'message': "Tidak ditemukan KRS yang berstatus Approved untuk mahasiswa ini pada periode yang dipilih."
                    }
                }


class AcademicKhsLine(models.Model):
    _name = 'academic.khs.line'
    _description = 'KHS Line'

    khs_id = fields.Many2one(
        'academic.khs', string='KHS', ondelete='cascade'
    )
    subject_id = fields.Many2one(
        'academic.subject', string='Subject', required=True
    )
    schedule_ids = fields.Many2many(
        'academic.class.schedule', string='Schedules'
    )
    grade = fields.Char(string='Nilai Huruf', help="Contoh: A, B, C")
    score = fields.Float(string='Nilai Angka', help="Contoh: 85.0")
