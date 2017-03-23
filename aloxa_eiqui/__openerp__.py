# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Solucións Aloxa S.L. <info@aloxa.eu>
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


{
    "name": "Aloxa eiqui",
    "version": "0.1",
    "category": "eiqui",
    "icon": "/aloxa_eiqui/static/src/img/company_logo.png",
    "author": "Solucións Aloxa S.L.",
    "description": "Módulo base para solucións aloxa",
    "init_xml": [],
    'external_dependencies': {
        #'python': ['dosa', 'pygithub', 'erppeek', 'configparser'],
    },
    "depends": [
        'project', 
        'website',
        'website_blog',
        'mass_mailing',
        'project_issue',
        'sale',
        'report',
        'account_payment_sale',
    ],
    "data": [
    	'views/res_config.xml',
    	
        'views/project.xml',
        'views/inherit_project_project.xml',
        'views/inherit_res_partner.xml',
        'views/inherit_res_config.xml',
        'views/inherit_blog_post.xml',
        'views/inherit_mass_mailing.xml',
        'views/inherit_mail_mass_mailing_contact.xml',
        'views/repos.xml',
        'views/modules.xml',
        'views/project_modules.xml',
        'views/plan_type.xml',
        'views/vertical.xml',
        'views/actions.xml',
        'views/menus.xml',
        'views/messages.xml',
             
        'views/website/external/compatibility.xml',
        'views/website/external/home.xml',
        
        'views/website/generic.xml',
        'views/website/sign_up.xml',
    	'views/website/panel_plan_list.xml',
        'views/website/panel_plan_detail.xml',
        'views/website/mail_campaign_eiqui.xml',
        
    	'views/reports/report_style.xml',
    	'views/reports/eiqui_report_invoice_document.xml',
        'views/reports/eiqui_report_invoice.xml',
    	'views/reports/eiqui_report_sale_order.xml',
    	'views/reports/eiqui_report_sale_order_document.xml',
    	'views/reports/eiqui_external_layout.xml',
    	'views/reports/eiqui_external_layout_footer.xml',
    	'views/reports/eiqui_external_layout_header.xml',
        
        'data/paper_formats.xml',
        'data/template_mail.xml',
    ],
    
    "demo": [],
    "installable": True,
    "active": False,
}
