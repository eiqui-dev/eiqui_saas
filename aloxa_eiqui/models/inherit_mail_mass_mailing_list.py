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


# IMPORTACION DE CORREOS ELECTRONICOS DE 'PAXINAS GALEGAS'
# Parametros de la web:
#    - ncom
#    - aynom: Ciudad
#    - cllnom:
#    - epinom: Actividad
#    - pagina: Pagina
def import_contacts_paxinas_galegas(mails, activity, city="", npag=1):
    HOST="http://www.paxinasgalegas.es"
    PAGE_PAG="/resultados.aspx?tipo=1&ncom=&aynom=%s&cllnom=&epinom=%s&pagina=%d"

    frmt_page = PAGE_PAG % (urllib.quote_plus(city),urllib.quote_plus(activity),npag-1)
    r = requests.post('%s%s' % (HOST, frmt_page))
    if r.status_code == 200:
        # Obtener numero pags
        pags = [1]
        if re.search(r'<div id="dvPagNumeracion" class="numeracion">', r.text):
            res_founds = re.finditer(r'<p class="numero[^"]*">(?:<a[^>]*>)?(\d+)', r.text)
            pags = [int(res.group(1)) for res in res_founds]
            
        if r.status_code == 200:
            # Obtener Correos
            res_founds = re.finditer(r'data-name="([^"]+)".+data-mail="([^"]+)"', r.text)
            has_mails = False
            for res in res_founds:
                mails.update({res.group(2):res.group(1)})
                has_mails = True
        else:
            print "Error ocurred while import mails from page %d of '%s'" % (npag, activity)
        
        if npag <= pags[-1:][0]:
            import_contacts_paxinas_galegas(mails, activity=activity, city=city, npag=npag+1)
    else:
        raise Exception("Unespected Error!")
        
    if len(mails) == 0:
        raise Exception("No mails found!")
    return mails
    
    
class mail_mass_mailing_list(models.Model):
    _inherit='mail.mass_mailing.list'

    @api.multi
    def import_contacts(self):
        mail_mass_mailing_obj = self.env['mail.mass_mailing.contact']
        mails_list_ids = []
        for record in self:
            mails = {}
            import_contacts_paxinas_galegas(mails, activity=record.name)
            for mail in mails:
                record_data = {
                    'email': mail, 
                    'name': mails[mail],
                    'list_id': record.id,
                }
                mass_mailing_contact = mail_mass_mailing_obj.search([('email', '=', mail)], limit=1)
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
