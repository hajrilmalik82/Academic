{
    'name': 'Campus HR Academic',
    'version': '17.0.1.0.0',
    'summary': 'Academic Profile for Employees (Lecturers)',
    'description': 'Extends HR Employee to include academic profiles and integrates with Campus Core.',
    'category': 'Human Resources',
    'author': 'Odoo 17 Senior Technical Consultant',
    'depends': ['base', 'hr', 'campus_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
