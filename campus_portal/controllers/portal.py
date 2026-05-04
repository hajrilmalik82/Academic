from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CampusPortal(CustomerPortal):
    _items_per_page = 20

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
        total = KrsObj.search_count(domain)
        pager = request.website.pager(
            url='/my/krs',
            total=total,
            page=page,
            step=self._items_per_page,
        )
        krs_records = KrsObj.search(
            domain,
            limit=self._items_per_page,
            offset=pager['offset'],
            order='academic_year_id desc, id desc',
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'krs_records': krs_records,
            'pager': pager,
            'page_name': 'krs',
            'default_url': '/my/krs',
        })
        return request.render("campus_portal.portal_my_krs", values)

    @http.route(['/my/khs', '/my/khs/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_khs(self, page=1, **kw):
        partner = request.env.user.partner_id
        domain = [('student_id', '=', partner.id)]

        KhsObj = request.env['academic.khs']
        total = KhsObj.search_count(domain)
        pager = request.website.pager(
            url='/my/khs',
            total=total,
            page=page,
            step=self._items_per_page,
        )
        khs_records = KhsObj.search(
            domain,
            limit=self._items_per_page,
            offset=pager['offset'],
            order='academic_year_id desc, id desc',
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'khs_records': khs_records,
            'pager': pager,
            'page_name': 'khs',
            'default_url': '/my/khs',
        })
        return request.render("campus_portal.portal_my_khs", values)
