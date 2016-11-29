# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions

class vertical(models.Model):
    _name = 'eiqui.vertical'
    
    #Fields
    name = fields.Char('Name', translate=True)
    image = fields.Binary('Image')
    description = fields.Char('Summary', translate=True)
    modules = fields.Many2many('eiqui.modules','vertical_ids')
    