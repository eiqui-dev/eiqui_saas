# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Soluci�ns Aloxa S.L. <info@aloxa.eu>
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
#===============================================================================
# # REMOTE DEBUG
#import pydevd
# 
# # ...
# 
# # breakpoint
#pydevd.settrace("10.0.3.1")
#===============================================================================
from openerp import models, fields, api, _
import requests
import re
import urllib
import base64


#
# CONTACT DEFINITION
#
class Contact:
    def __init__(self, mail, name=None, web=None, address=None, city=None, phone=None, province=None, zipcode=None):
        self.mail = mail
        self.name = name
        self.web = web
        self.address = address
        self.city = city
        self.phone = phone
        self.province = province
        self.zipcode = zipcode


#
# IMPORT CONTACTS (RECURSIVE)
#   
def import_contacts_paxinas_galegas(contacts, activity, city, npag=1):
    E_URL = u'http://www.paxinasgalegas.es'
    frmt_page = u'/resultados.aspx?tipo=1&ncom=&aynom=%s&cllnom=&epinom=%s&pagina=%d' % (urllib.quote_plus(city), urllib.quote_plus(activity), npag-1)
    print frmt_page
    r = requests.post('%s%s' % (E_URL, frmt_page))
    if r.status_code == 200:
        # Get Pagination
        res_founds = re.finditer(r'<p class="numero[^"]*">(?:<a[^>]*>)?(\d+)', r.text)
        pags = [int(res.group(1)) for res in res_founds]
        if len(pags) == 0:
            pags = [1]
            
        # Get Contacts
        in_company = False
        lines = r.text.split('\n')
        for line in lines:
            res = re.search(r'data-name=\"([^\"]+)\".+data-telf=\"([^\"]+)\".+data-mail=\"([^\"]+)\".+data-empuri=\"([^\"]+)\"', line)
            if res:
                in_company = Contact(mail=res.group(3),
                                        name=res.group(1),
                                        phone=res.group(2),
                                        web=res.group(4))
            if in_company:
                res = re.search(r'class=\"calle\">([^<]+)<', line)
                if res:
                    in_company.address=res.group(1)
                res = re.search(r'class=\"municipio font-weight-bold\">([^<]+)<', line)
                if res:
                    in_company.city=res.group(1)
                    contacts.append(in_company)
                    in_company =  False
        
        # Recursive Call
        if npag <= pags[-1:][0]:
            import_contacts_paxinas_galegas(contacts, activity=activity, city=city, npag=npag+1)
    else:
        raise Exception("Unespected Error!")
    
# Por defecto usan 15 lineas por pagina... nosotros ponemos a 30 para ir el doble de rápido
def import_contacts_paginas_amarillas(contacts, api_user, api_pass, activity, city, npag=1, rows=30):
    E_URL = u'https://www.paginasamarillas.es'
    frmt_page = u'/mactions/searchResults?where=%s&what=%s&rows=%d&seed=123&page=%d&format=json' % (urllib.quote_plus(city), urllib.quote_plus(activity), rows, npag)
    print frmt_page
    
    auth_str = base64.encodestring('%s:%s' % (api_user, api_pass)).strip()
    headers = {
        # Yes.. i'm the app...
        'User-Agent': 'AndroidPA 4.2.4 Dalvik/2.1.0 (Linux; U; Android 6.0.1; Galaxy Nexus Build/MOB31K)',
        'X-Client-Identifier': '7563686172',
        'Authorization': 'Basic %s' % auth_str,
        'X-Application-Name': 'YellSearch',
    }
    r = requests.post('%s%s' % (E_URL, frmt_page), json={}, headers=headers)
    if r.status_code == 200:
        data = r.json()
        total_regs = data['totaldocuments']
        total_pags = total_regs/rows
        
        ads = data['advertisements']
        for l in ads:
            adv_loc_info = l['locationinfo']
            
            if 'email' in l['locationinfo'][0]:
                adv_loc_info = l['locationinfo'][0]
                ncontact = Contact(
                    mail = 'email' in adv_loc_info and adv_loc_info['email'] or '',
                    name = 'name' in l['basicinfo'] and l['basicinfo']['name'] or '',
                    phone = 'telephone' in adv_loc_info and adv_loc_info['telephone'] or '',
                    address = 'cam' in adv_loc_info and adv_loc_info['cam'] or '',
                    city = 'locality' in adv_loc_info and adv_loc_info['locality'] or '',
                    province = 'province' in adv_loc_info and adv_loc_info['province'] or '',
                    zipcode = 'postcode' in adv_loc_info and adv_loc_info['postcode'] or '')
                if 'urls' in l['basicinfo'] and 'web' in l['basicinfo']['urls']:
                    ncontact.web = l['basicinfo']['urls']['web'] 
                contacts.append(ncontact)
        
        # Recursive call
        if npag < total_pags:
            import_contacts_paginas_amarillas(contacts, api_user=api_user, api_pass=api_pass, activity=activity, city=city, npag=npag+1, rows=rows)

    
class mail_mass_mailing_list(models.Model):
    _inherit='mail.mass_mailing.list'

    @api.multi
    def import_contacts(self):
        mail_mass_mailing_obj = self.env['mail.mass_mailing.contact']
        mails_list_ids = []
        config = self.env['eiqui.config.settings'].search([], order='id DESC', limit=1)
        for record in self:
            contacts = []
            import_contacts_paxinas_galegas(contacts, activity=record.name, city='')
            import_contacts_paginas_amarillas(contacts, 
                                            api_user=config.pags_amarillas_api_user, 
                                            api_pass=config.pags_amarillas_api_password, 
                                            activity=record.name, city='')
            for contact in contacts:
                record_data = {
                    'email': contact.mail, 
                    'name': contact.name,
                    'zip': contact.zipcode,
                    'city': contact.city,
                    'address': contact.address,
                    'phone': contact.phone,
                    'province': contact.province,
                    'list_id': record.id,
                }
                mass_mailing_contact = mail_mass_mailing_obj.search([('email', '=', contact.mail)], limit=1)
                if not mass_mailing_contact:
                    mail_mass_mailing_obj.create(record_data)
            mails_list_ids.append(record.id)
                
        return {
            'name': _('Paxinas Galegas Contacts'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'mail.mass_mailing.contact',
            'context': {},
            'domain':[('list_id','in',mails_list_ids)],
        }
