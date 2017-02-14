# -*- coding: utf-8 -*-
from openerp import models, fields, api


class project_modules(models.Model):
    _name = 'eiqui.project.modules'

    # Fields
    repo_id = fields.Many2one('eiqui.repos')
    commit = fields.Char('Current Commit')
    installed_modules_ids = fields.Many2many('eiqui.modules')