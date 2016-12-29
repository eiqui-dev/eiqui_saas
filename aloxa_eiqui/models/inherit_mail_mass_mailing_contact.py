# -*- coding: utf-8 -*-
#################################################################################
#
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
from openerp import models, fields

class MassMailingContact(models.Model):
    _inherit = 'mail.mass_mailing.contact'
    
    web = fields.Char(string='Web', size=255)
    city = fields.Char(string='City', size=64)
    zip = fields.Char(string='Zip', size=12)
    address = fields.Char(string='Address')
    phone = fields.Char(string='Phone', size=16)
    province = fields.Char(string='Province', size=128)
    