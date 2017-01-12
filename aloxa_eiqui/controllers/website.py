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
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import simplejson
import re
import thread
import math
import traceback

import openerp
from openerp import http, models, api, exceptions, SUPERUSER_ID, _
from openerp.http import request
from openerp.api import Environment
from openerp.addons.website.models.website import slug
import openerp.addons.web.controllers.main as webmain
from . import eiqui_utils
import logging
import dosa
_logger = logging.getLogger(__name__)

class QueryURL(object):
    def __init__(self, path='', **args):
        self.path = path
        self.args = args

    def __call__(self, path=None, **kw):
        if not path:
            path = self.path
        for k,v in self.args.items():
            kw.setdefault(k,v)
        l = []
        for k,v in kw.items():
            if v:
                if isinstance(v, list) or isinstance(v, set):
                    l.append(werkzeug.url_encode([(k,i) for i in v]))
                else:
                    l.append(werkzeug.url_encode([(k,v)]))
        if l:
            path += '?' + '&'.join(l)
        return path
    
class EiquiWebsite(webmain.Home):
    
    @http.route('/', auth="public", type="http", website=True)
    def index(self, **kw):
        blog_posts = request.env['blog.post'].sudo().search([('website_published', '=', True)], order='create_date desc', limit=10)
        values = {'blog_posts': blog_posts}
        return request.website.render("aloxa_eiqui.home_page", values)
        
    @http.route('/panel/search', auth="user", type="http", methods=['POST'], website=True)
    def _panel_search(self, search=None, **kw):
        user = request.env['res.users'].browse([request.uid])
        domain = [('final_partner_id', '=', user.partner_id.id)]
        if search:
            domain.append(('name', 'ilike', '%%%s%%' % search))
        projects = request.env['project.project'].search(domain, order='create_date desc', limit=10)
        
        values = {
            'projects':projects,
            'search':search,
        }
        return request.website.render("aloxa_eiqui.panel_plans_list", values)
    
    @http.route('/panel', auth="user", type="http", website=True)
    def panel(self, **kw):        
        user_id = request.env['res.users'].browse([request.uid])
        keep = QueryURL('/panel', search='', attrib=None)
        
        messages = request.env['eiqui.messages'].search([
            '|',
            ('project_id.final_partner_id', '=', user_id.partner_id.id), 
            ('project_id', '=', False),
        ])
        
        values = {
            'keep':keep, 
            'user':user_id,
            'messages':messages,
        }

        return request.website.render("aloxa_eiqui.panel_page", values)
    
    @http.route('/panel/plan/<int:plan_id>', auth="user", type="http", website=True)
    def panel_plan(self, plan_id, **kw):   
        user_id = request.env['res.users'].browse([request.uid])
        project = request.env['project.project'].search([('final_partner_id', '=', user_id.partner_id.id), ('id', '=', plan_id)])
        if not project or project.server_state != 'created':
            raise werkzeug.exceptions.NotFound()
        
        messages = request.env['eiqui.messages'].search([
            ('project_id', '=', plan_id),
        ])
        
        values = {'project':project, 'user':user_id, 'messages':messages}

        return request.website.render("aloxa_eiqui.panel_plan_page", values)
    
    @http.route(['/panel/plan/<int:plan_id>/<string:section>',
                 '/panel/plan/<int:plan_id>/<string:section>/<int:pag>',], auth="user", type="http", methods=['POST'], website=True)
    def panel_plan_section(self, plan_id, section, search=None, module_filter='all', pag=0, **kw):
        NUM_REGS = 20.0
        attrib_list = request.httprequest.args.getlist('attrib')
        #attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        #attrib_set = set([v[1] for v in attrib_values])
        
        user_id = request.env['res.users'].browse([request.uid])
        project = request.env['project.project'].search([('final_partner_id', '=', user_id.partner_id.id), ('id', '=', plan_id)])
        if not project:
            raise werkzeug.exceptions.NotFound()
        
        values = {'project':project, 'user':user_id}

        if section == 'modules_apps':
            # SEARCH HELPER
            keep = QueryURL('/panel/plan/%d/modules_apps' % project.id, search='', attrib=attrib_list)
            # DEFAULT VALUES
            modules_installed = project.repo_modules_ids.mapped('installed_modules_ids')
            modules = []
            domain = ['|',('repo_id.plan_ids','in', [plan_id]),('repo_id.plan_ids', '=', False)]
            # SEARCH
            if search:
                domain.append(('name', 'ilike', '%%%s%%' % search))
            # FILTERS
            filter_name = _('All')
            if module_filter == 'apps':
                domain.append(('eiqui_app', '=', True))
                filter_name = _('APPs')
            elif module_filter == 'not_installed':
                modules_installed_ids = [x.id for x in modules_installed]
                domain.append(('id', 'not in', modules_installed_ids))
                filter_name = _('Not Installed')
            elif module_filter == 'installed':
                modules_installed_ids = [x.id for x in modules_installed]
                domain.append(('id', 'in', modules_installed_ids))
                filter_name = _('Installed')
            # GET MODULES
            modules = request.env['eiqui.modules'].search(domain, offset=pag*NUM_REGS, limit=NUM_REGS, order='repo_id DESC')
            total_modules_count = request.env['eiqui.modules'].search_count(domain)
            # RENDER TEMPLATE
            values.update({'modules':modules, 
                           'modules_installed':modules_installed,
                           'total_modules_count': total_modules_count,
                           'num_pages':int(math.ceil(total_modules_count/NUM_REGS)), 
                           'cur_page':pag,
                           'search':search,
                           'module_filter':module_filter,
                           'filter_name':filter_name,
                           'num_regs': NUM_REGS,
                           'keep':keep,})
            return request.website.render("aloxa_eiqui.panel_plan_modules_apps_page", values)
        elif section == 'maintenance':
            return request.website.render("aloxa_eiqui.panel_plan_maintenance_page", values)
        elif section == 'tasks_issues':
            return request.website.render("aloxa_eiqui.panel_plan_tasks_issues_page", values)
        elif section == 'server':
            return request.website.render("aloxa_eiqui.panel_plan_server_page", values)
        elif section == 'access_control':
            return request.website.render("aloxa_eiqui.panel_plan_access_control_page", values)
        elif section == 'general':
            return request.website.render("aloxa_eiqui.panel_plan_general_page", values)
        elif section == 'advance':
            return request.website.render("aloxa_eiqui.panel_plan_advance_page", values)
        
        return request.website.render("aloxa_eiqui.panel_plan_charts_page", values)
        
    @http.route('/alta', auth="public", type="http", website=True)
    def alta(self):    
        country_orm = request.env['res.country']
        country_ids = country_orm.search([])
        values = dict({'countries':country_ids})
    
        return request.website.render("aloxa_eiqui.signup_page", values)
    
    @http.route(['/_get_states'], auth="public", type='json', website=True)
    def get_states(self, country_id):
        if not country_id or country_id == '':
            return { 'states': [] }
        
        state_orm = request.env['res.country.state']
        state_ids = state_orm.search([('country_id.id', '=', country_id)])
        
        states = []
        for state in state_ids:
            states.append([state.id,state.name])
            
        return { 'states': states }
    
    @http.route(['/_get_bzip'], auth="public", type='json', website=True)
    def get_bzip(self, zip_name):
        if not zip_name or zip_name == '':
            return { 'bzip': [] }
        
        better_zip_orm = request.env['res.better.zip']
        better_zip_id = better_zip_orm.sudo().search([('name', '=', zip_name)], limit=1)
            
        return { 'bzip': [better_zip_id.id,better_zip_id.name,better_zip_id.state_id.id,better_zip_id.country_id.id,better_zip_id.city] }
    
    @http.route(['/_check_domain_status'], auth="public", type='json', website=True)
    def check_domain_status(self, **kw):
        if not 'domain' in kw or not kw['domain']:
            return { 'check': False }
        
        proj_id = request.env['project.project'].sudo().search([('name','=ilike',kw['domain'])])
        if proj_id:
            return { 'check': False }
        
        # Check if exist record domain in Digital Ocean
        doClient = dosa.Client(api_key=request.website.digital_ocean_api_key)
        dr = doClient.DomainRecords(domain='eiqui.com')
        resp = dr.list()
        if not resp[0] == 200:
            return { 'check': False }
        domain_recs = resp[1]['domain_records']
        if [d for d in domain_recs if d['name'] and d['name'].lower()==kw['domain'].lower()]:
            return { 'check': False }
        
        return { 'check': True }
    
    @http.route(['/_check_email_status'], auth="public", type='json', website=True)
    def check_email_status(self, **kw):
        if not 'email' in kw or not kw['email']:
            return { 'check': False }
        
        user_id = request.env['res.users'].sudo().search([('login','=ilike',kw['email'])])
        return { 'check': False if user_id else True }
        
    @http.route(['/_create_user'], type='json', auth="public", website=True)
    def create_user(self, **kw):
        # Validations
        if len([x for x in 
                ('name','email','password','domain','phone','country','city','street','zip') 
                if x not in kw or (x in kw and kw[x] == '')]) > 0:
            return { 'error': True, 'errormsg': "Error creating account! Missing parameters :/" }
        
        # Check Data
        if not re.match(r'^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$', kw['email']):
            return { 'error': True, 'errormsg': "Email appear to be invalid" }
        if not re.match(eiqui_utils.EIQUI_CLIENTNAME_REGEX, kw['domain']):
            return { 'error': True, 'errormsg': "Domain appear to be invalid" }
        if request.env['project.project'].sudo().search([('name','=ilike',kw['domain'])]):
            return { 'error': True, 'errormsg': "Domain currently in use!" }
        if request.env['res.users'].sudo().search([('login','=ilike',kw['email'])]):
            return { 'error': True, 'errormsg': "Email currently in use!" }
        
        # Create User
        try:
            db, login, password_f = request.registry['res.users'].signup(request.cr, 
                                                SUPERUSER_ID, 
                                                {
                                                    'name': kw['name'],
                                                    'login': kw['email'],
                                                    'password': kw['password'],
                                                    'active': True,
                                                })
            request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        except:
            return { 'error' : True, 'errormsg': 'Unexpected error during user creation...' }
        
        uid = request.session.authenticate(db, login, password_f)
        if not uid:
            return { 'error' : True, 'errormsg': "Authentification failed!" }
        
        ##############
        # FIXME: A partir de aqui uso "sudo" para testeo.. pero se tiene que cambiar y dar los permisos necesarios!!!
        ##########################
        # Create Partner      
        regData = {
            'name': kw['name'],
            'email': kw['email'],
            'customer': True,
            'active': False, # De momento no activo
            'is_manager': True,
            #'vat': kw['cnif'],
            'street': kw['street'],
            'street2': kw['street2'] if 'street2' in kw else None,
            'state_id': int(kw['state']) if 'state' in kw and not kw['state'] == '' else None,
            'zip': kw['zip'],
            'city': kw['city'],
            'phone': kw['phone'],
            'country_id': int(kw['country']),
        }
        #if kw['image'].filename:
        #    regData.update({'image': base64.encodestring(kw['image'].read())});
        
        user_id = request.env['res.users'].sudo(user=uid).browse(uid)
        if not user_id.partner_id.exists():
            return { 'error' : True, 'errormsg': "Can't create the partner!" }
        user_id.partner_id.sudo(user=uid).write(regData)

        return { 'check': True if user_id and user_id.exists() else False }
    
    @http.route(['/_get_plan_status'], auth="user", type='json', website=True)  
    def _get_plan_status(self, plan_id):
        proj_id = request.env['project.project'].browse([plan_id])
        if not proj_id:
            return { 'error' : True, 'errormsg': "Invalid project id!" }
        return { 'check':True, 'status':proj_id.server_state }
              
          
    @http.route(['/_create_plan'], auth="user", type='json', website=True)  
    def _create_plan(self, domain):
        domain = domain.lower()
        if not re.match(eiqui_utils.EIQUI_CLIENTNAME_REGEX, domain):
            return { 'error': True, 'errormsg': _("Invalid Domain Name: '%s'") % domain }
        
        res = self.check_domain_status(domain=domain)
        if not res['check']:
            return { 'error': True, 'errormsg': _("Domain '%s' in use! Please select another one...") % domain }
        user_id = request.env['res.users'].sudo().browse(request.uid)
        # Create Project
        regData = {
            'name': domain,
            'user_id': None,
            'partner_id': user_id.partner_id.id,
            'alias_name': domain,
            'final_partner_id': user_id.partner_id.id
        }
        proj_id = request.env['project.project'].sudo().create(regData)
        if not proj_id or not proj_id.exists():
            request.env['project.issue'].create({
                'name': _('Error creating plan project'),
                'description': _("One error ocurred while creating the project (%s) for '%s'..." % (domain, user_id.name)),
                'priority': '2',
            })
            return { 'error': True, 'errormsg': _("Can't create the plan! Please try again in few minutes...") }
        # En ocasiones el hilo aun no puede ver el nuevo proyecto creado
        # forzamos que se guarden los cambios para asegurarnos de que el hilo pueda ver el nuevo proyecto
        request.cr.commit()
        kwargs = {'uid': request.uid, 'db': request.db, 'project_id': proj_id.id}
        thread.start_new_thread(self._thread_create_docker, (kwargs,))
        return { 'check': True }
        
    def _thread_create_docker(self, kwargs):
        with openerp.sql_db.db_connect(kwargs.get('db')).cursor() as new_cr:
            with Environment.manage(): 
                env = Environment(new_cr, kwargs.get('uid'), {})
                project = env['project.project'].browse([kwargs.get('project_id')])
                try:
                    if not project:
                        raise Exception(_("The project appears doesn't exists!"))
                    # Crear cliente
                    eiqui_utils.create_client(project.name)
                    # Preparar Odoo (Produccion)
                    eiqui_config = env['eiqui.config.settings'].search([], order="id DESC", limit=1)
                    git_username = None
                    git_password = None
                    if eiqui_config:
                        git_username = eiqui_config.git_username
                        git_password = eiqui_config.git_password
                    repos = []
                    modules = []
                    is_test = False
                    (inst_info, adminpasswd, odoo_url) = eiqui_utils.prepare_client_instance(project.name, 
                                                        repos, 
                                                        '8.0', 
                                                        modules_installed=modules,
                                                        git_user=git_username,
                                                        git_pass=git_password,
                                                        is_test=is_test)
                    project.write({'server_state':'created'})
                    # Send Creation Mail
                    try:
                        project.send_mail_plan_creation({
                            'inst_info': inst_info,
                            'adminpasswd': adminpasswd,
                            'url': odoo_url,
                        })
                    except:
                        pass
                except Exception:
                    env['project.issue'].create({
                        'name': _('Error while creating a new plan'),
                        'description': traceback.format_exc(),
                        'project_id': project.id,
                        'priority': '2',
                    })
                    project.write({'server_state':'error'})
                    # Send Error Mail
                    try:
                        project.send_mail_plan_creation()
                    except:
                        pass
                    # Revert all changes
                    #try:
                    #    eiqui_utils.remove_client(project.name, full=True)
                    #except:
                    #    pass