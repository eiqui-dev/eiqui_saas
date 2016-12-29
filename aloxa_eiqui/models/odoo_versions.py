# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions


class odoo_versions(models.Model):
    _name='eiqui.odoo.versions'
     
    #Fields
    name = fields.Char('Name')