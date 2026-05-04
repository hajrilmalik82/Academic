{
    'name': 'Campus PMB (Admissions)',
    'version': '17.0.1.0.0',
    'summary': 'New Student Admission with Auto User Creation',
    'description': """
        This module manages new student admissions.
        When a candidate is passed, the system automatically creates their 
        Partner profile and Portal User account.
    """,
    'category': 'Education',
    'author': 'Hajril',
    'depends': ['base', 'mail', 'campus_core', 'portal'],
    'data': [
        'security/pmb_security.xml',
        'security/ir.model.access.csv',
        'views/admission_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
