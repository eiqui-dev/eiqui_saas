# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Solucións Aloxa S.L. <info@aloxa.eu>
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
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class eiqui_config_settings(models.TransientModel):
    _name = 'eiqui.config.settings'
    _inherit = 'res.config.settings'

    git_username = fields.Char(string="Git Username", size=64)
    git_password = fields.Char(string="Git Password", size=128)
    pags_amarillas_api_user = fields.Char(string="Páginas Amarillas User", size=32)
    pags_amarillas_api_password = fields.Char(string="Páginas Amarillas Password", size=32)

    def get_default_git_username(self, cr, uid, fields, context=None):
        last_id = self.search(cr, uid, [], order='id DESC', limit=1, context=context)
        config_line = self.browse(cr, uid, last_id, context=context)
        return {'git_username': config_line.git_username or ''}

    def get_default_git_password(self, cr, uid, fields, context=None):
        last_id = self.search(cr, uid, [], order='id DESC', limit=1, context=context)
        config_line = self.browse(cr, uid, last_id, context=context)
        return {'git_password': config_line.git_password or ''}

    def get_default_pags_amarillas_api_user(self, cr, uid, fields, context=None):
        last_id = self.search(cr, uid, [], order='id DESC', limit=1, context=context)
        config_line = self.browse(cr, uid, last_id, context=context)
        return {'pags_amarillas_api_user': config_line.pags_amarillas_api_user or ''}

    def get_default_pags_amarillas_api_password(self, cr, uid, fields, context=None):
        last_id = self.search(cr, uid, [], order='id DESC', limit=1, context=context)
        config_line = self.browse(cr, uid, last_id, context=context)
        return {'pags_amarillas_api_password': config_line.pags_amarillas_api_password or ''}
    