from odoo import fields, models


class CampusBuilding(models.Model):
    _name = 'campus.building'
    _description = 'Campus Building'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    location = fields.Char(string='Location', required=True, help="Contoh: Kampus A Sudirman")
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company)


class CampusRoom(models.Model):
    _name = 'campus.room'
    _description = 'Campus Room'

    name = fields.Char(string='Name', required=True)
    building_id = fields.Many2one('campus.building', string='Building', required=True)
    capacity = fields.Integer(string='Capacity', required=True)
    room_type = fields.Selection([
        ('theory', 'Theory'),
        ('lab', 'Laboratory')
    ], string='Room Type', required=True, default='theory')
    company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company)
