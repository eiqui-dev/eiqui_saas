# -*- coding: utf-8 -*-
from openerp import models, fields

class project_type(models.Model):
    _name = 'eiqui.project.type'
    
    #Fields
    name = fields.Char('Name')
    ram = fields.Integer('Ram Bytes')
    storage = fields.Integer('Storage Size Bytes')
