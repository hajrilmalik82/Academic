from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request

class CampusPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'krs_count' in counters:
            values['krs_count'] = request.env['academic.krs'].search_count([
                ('student_id', '=', partner.id)
            ])
        if 'khs_count' in counters:
            values['khs_count'] = request.env['academic.khs'].search_count([
                ('student_id', '=', partner.id)
            ])
        return values

    @http.route(['/my/krs', '/my/krs/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_krs(self, page=1, **kw):
        partner = request.env.user.partner_id
        domain = [('student_id', '=', partner.id)]
        
        KrsObj = request.env['academic.krs']
        krs_records = KrsObj.search(domain)
        
        values = self._prepare_portal_layout_values()
        values.update({
            'krs_records': krs_records,
            'page_name': 'krs',
            'default_url': '/my/krs',
        })
        return request.render("campus_portal.portal_my_krs", values)

    @http.route(['/my/khs', '/my/khs/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_khs(self, page=1, **kw):
        partner = request.env.user.partner_id
        domain = [('student_id', '=', partner.id)]
        
        KhsObj = request.env['academic.khs']
        khs_records = KhsObj.search(domain)
        
        values = self._prepare_portal_layout_values()
        values.update({
            'khs_records': khs_records,
            'page_name': 'khs',
            'default_url': '/my/khs',
        })
        return request.render("campus_portal.portal_my_khs", values)
