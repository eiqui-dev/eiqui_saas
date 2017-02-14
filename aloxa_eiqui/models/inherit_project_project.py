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
from openerp import models, fields, api


'''
Modelo que sobreescribe project.project

'''
class project_project(models.Model):
    _inherit='project.project'
    
    # Se hace así para poder enviar correos desde el hilo...
    # Por algún extraño motivo cuando se llama a "send_mail" dede la nueva api, no funciona.
    # TODO: Modificar en versiones superiores de Odoo ¿10.0?
    @api.model
    def send_mail_plan_creation(self, plan_values=None):
        self.ensure_one();
        template_id = False
        if self.server_state == 'created':
            template_id = self.env['ir.model.data'].get_object_reference('aloxa_eiqui', 'plan_created_mail')[1]
        elif self.server_state == 'error':
            template_id = self.env['ir.model.data'].get_object_reference('aloxa_eiqui', 'plan_error_mail')[1]
        if not template_id:
            raise Exception("Can't found template for current plan state")
        try:
            template_rec = self.env['mail.template'].browse(template_id)
            template_rec.with_context(plan_info=plan_values).send_mail(self.id, force_send=True, raise_exception=True)
        except ValueError:
            pass

    final_partner_id = fields.Many2one('res.partner', 'Final Customer')
    repo_modules_ids = fields.Many2many('eiqui.project.modules', string="Project Modules")
    plan_type_id = fields.Many2one('eiqui.plan.type', string="Plan Type")
    odoo_version = fields.Selection([
        ('8.0', '8.0'),
        ('9.0', '9.0')
        ], string='Odoo Version', default='9.0', required=True, readonly=True)
    server_state = fields.Selection([
        ('error', 'Error!'),
        ('creating', 'Creating...'),
        ('created', 'Created'),
        ('deleting', 'Deleting...')
        ], string='Server Sate', default='creating', required=True)#, readonly=True)
    adminpass = fields.Char('Eiqui Admin Password', size=128)
    #credentials = La idea es tener aqui el "aloxapass" en cuanto a eiqui se refiere (postgres, odoo, docker...)
    #recipe = ��Puede ser interesante tener aqui el .ini del cliente??
    #Server_Details = Informaci�n del droplet (RAM, disco, etc...)
