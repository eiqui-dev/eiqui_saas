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

    final_partner_id = fields.Many2one('res.partner', 'Final Customer')
    repo_modules_ids = fields.Many2many('eiqui.project.modules', string="Project Modules")
    plan_type_id = fields.Many2one('eiqui.project.type', string="Plan Type")
    server_state = fields.Selection([
        ('error', 'Error!'),
        ('creating', 'Creating...'),
        ('created', 'Created'),
        ('deleting', 'Deleting...')
        ], string='Server Sate', default='creating', required=True, readonly=True)
    #credentials = La idea es tener aqui el "aloxapass" en cuanto a eiqui se refiere (postgres, odoo, docker...)
    #recipe = ��Puede ser interesante tener aqui el .ini del cliente??
    #Server_Details = Informaci�n del droplet (RAM, disco, etc...)
    
    
    

