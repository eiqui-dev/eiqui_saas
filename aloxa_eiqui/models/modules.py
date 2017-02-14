# -*- coding: utf-8 -*-
from docutils.core import publish_string
from openerp import models, fields, api, exceptions
from openerp.addons.base.module.module import MyWriter
from openerp.tools import html_sanitize


class modules(models.Model):
    _name = 'eiqui.modules'
    
    @api.depends('original_guide')
    def _get_original_guide(self):
        overrides = {
            'embed_stylesheet': False,
            'doctitle_xform': False,
            'output_encoding': 'unicode',
            'xml_declaration': False,
        }
        for module in self:
            output = publish_string(source=module.original_guide or '', 
                                    settings_overrides=overrides, writer=MyWriter())
            module.original_guide_html = html_sanitize(output)
            
    @api.multi
    def _get_repo_branch(self):
        for record in self:
            record.repo_branch = record.repo_id and record.repo_id.branch or ''


    #Fields
    name = fields.Char('Name')
    original_description = fields.Char('Original Description', translate=True, readonly=True)
    eiqui_description = fields.Char('Eiqui Description', translate=True)
    original_app = fields.Boolean('Original APP', readonly=True)
    installable = fields.Boolean('Installable', readonlu=True, default=True)
    eiqui_app = fields.Boolean('eiqui APP')
    author = fields.Char('Author')
    original_image = fields.Binary('Original Image', readonly=True)
    eiqui_image = fields.Binary('eiqui Image')
    repo_id = fields.Many2one('eiqui.repos', 'Repository')
    original_guide = fields.Text('Original Guide', readonly=True)
    eiqui_guide = fields.Text('eiqui Guide')
    original_guide_html = fields.Html(compute='_get_original_guide', string='Guide HTML', readonly=True)
    original_summary = fields.Char(string='Original Summary', readonly=True)
    eiqui_summary = fields.Char(string='Eiqui Summary')
    odoo_version_id = fields.Many2one('eiqui.odoo.versions', string='Odoo Version')
    tags_ids = fields.Many2many('eiqui.modules.tags', string='Tags')
    vertical_ids = fields.Many2many('eiqui.vertical', 'modules', string='Vertical')
    Reviewed = fields.Boolean('Reviewed')
    folder = fields.Char('Folder Name')
    repo_branch = fields.Char('Repository Branch', compute='_get_repo_branch')
    

class modules_tags(models.Model):
    _name='eiqui.modules.tags'
     
    #Fields
    name = fields.Char('Name', translate=True)