# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Solucións Aloxa S.L. <info@aloxa.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################
from openerp import http, SUPERUSER_ID
from openerp.http import request
import openerp.addons.website_crm.controllers.main as contactus

class eiqui_contactus(contactus.contactus):    
    @http.route(['/crm/contactus'], type='json', auth="public", website=True)
    def contactus(self, **kwargs):
        def dict_to_str(title, dictvar):
            ret = "\n\n%s" % title
            for field in dictvar:
                ret += "\n%s" % field
            return ret

        _TECHNICAL = ['show_info', 'view_from', 'view_callback']  # Only use for behavior, don't stock it
        _BLACKLIST = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'active']  # Allow in description
        _REQUIRED = ['name', 'contact_name', 'email_from', 'description']  # Could be improved including required from model

        post_file = []  # List of file to add to ir_attachment once we have the ID
        post_description = []  # Info to add after the message
        values = {}

        values['medium_id'] = request.registry['ir.model.data'].xmlid_to_res_id(request.cr, SUPERUSER_ID, 'crm.crm_medium_website')
        values['section_id'] = request.registry['ir.model.data'].xmlid_to_res_id(request.cr, SUPERUSER_ID, 'website.salesteam_website_sales')

        for field_name, field_value in kwargs.items():
            if hasattr(field_value, 'filename'):
                post_file.append(field_value)
            elif field_name in request.registry['crm.lead']._fields and field_name not in _BLACKLIST:
                values[field_name] = field_value
            elif field_name not in _TECHNICAL:  # allow to add some free fields or blacklisted field like ID
                post_description.append("%s: %s" % (field_name, field_value))

        if "name" not in kwargs and values.get("contact_name"):  # if kwarg.name is empty, it's an error, we cannot copy the contact_name
            values["name"] = values.get("contact_name")
        # fields validation : Check that required field from model crm_lead exists
        error = set(field for field in _REQUIRED if not values.get(field))

        if error:
            values = dict(values, error=error, kwargs=kwargs.items())
            return {'success':False}

        # description is required, so it is always already initialized
        if post_description:
            values['description'] += dict_to_str(_("Custom Fields: "), post_description)

        if kwargs.get("show_info"):
            post_description = []
            environ = request.httprequest.headers.environ
            post_description.append("%s: %s" % ("IP", environ.get("REMOTE_ADDR")))
            post_description.append("%s: %s" % ("USER_AGENT", environ.get("HTTP_USER_AGENT")))
            post_description.append("%s: %s" % ("ACCEPT_LANGUAGE", environ.get("HTTP_ACCEPT_LANGUAGE")))
            post_description.append("%s: %s" % ("REFERER", environ.get("HTTP_REFERER")))
            values['description'] += dict_to_str(_("Environ Fields: "), post_description)

        lead_id = self.create_lead(request, dict(values, user_id=False), kwargs)
        values.update(lead_id=lead_id)
        if lead_id:
            for field_value in post_file:
                attachment_value = {
                    'name': field_value.filename,
                    'res_name': field_value.filename,
                    'res_model': 'crm.lead',
                    'res_id': lead_id,
                    'datas': base64.encodestring(field_value.read()),
                    'datas_fname': field_value.filename,
                }
                request.registry['ir.attachment'].create(request.cr, SUPERUSER_ID, attachment_value, context=request.context)

        return {'success':True}