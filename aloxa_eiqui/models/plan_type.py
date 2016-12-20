# -*- coding: utf-8 -*-
from openerp import models, fields

class project_type(models.Model):
    _name = 'eiqui.plan.type'
    _inherits = {'product.template':'product_tmpl_id'}
    
    #Fields
    product_tmpl_id = fields.Many2one('product.template', 
                                      string="Product Template", 
                                      required=True, 
                                      ondelete='cascade')
    ram = fields.Integer('RAM (Bytes)')
    storage = fields.Integer('Storage Size (Bytes)')
