# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _
from openerp.addons.web.http import request
import re
from github import Github, GithubException
import ast

def get_repo_info(git_user, git_pass, repo, branch):
    results = re.search('https?:\/\/(?:www\.)?github\.com\/(.+)\/([^\.]+)', repo)
    if not results:
        raise Exception("Invalid repository url")
    
    user_login = results.group(1)
    user_repo = results.group(2)

    try:
        gGithubClient = Github(git_user, git_pass)
    except AssertionError:
        raise Exception("Can't login on github!")
    
    github_user = None
    github_repo = None
    try:
        github_user = gGithubClient.get_user(login=user_login)
        github_repo = github_user.get_repo(user_repo)
    except GithubException:
        raise Exception("Can't read '%s' repositories or reached the maximum of requests!" % user_login)

    dirs = []
    base_dir = '.'
    # OCB Repository it's the Odoo base from Community. Have more stuff than only modules.
    if user_login.lower() == 'oca' and user_repo.lower() == 'ocb':
        base_dir = 'addons'
    try:
        dirs = github_repo.get_dir_contents(base_dir, branch)    
    except GithubException:
        raise Exception("Branch '%s' not exists! repository omitted..." % branch)
    
    master = github_repo.get_git_ref('heads/%s' % branch)
    base_commit = github_repo.get_git_commit(master.object.sha)
    
    modulesInfo = {}
    has_odoo_modules = False
    for d in dirs:
        if d.type == 'dir':
            # Get Info
            try:
                openerp_file_path = '%s/__openerp__.py' % (d.name)
                if not base_dir == '.':
                    openerp_file_path = '%s/%s/__openerp__.py' % (base_dir,d.name)
                openerp_file = github_repo.get_contents(openerp_file_path, branch)
                openerpObj = ast.literal_eval(openerp_file.decoded_content)
                modulesInfo[d.name]={}
                modulesInfo[d.name]['folder'] = d.name
                modulesInfo[d.name]['api_url'] = d.git_url
                for key in ('name','author','summary','description','application','installable'):
                    modulesInfo[d.name][key] = None
                    if key in openerpObj:
                        if isinstance(openerpObj[key], str): 
                            modulesInfo[d.name][key] = openerpObj[key].strip().replace('%','<porcentaje>') if key in openerpObj else None
                        else:
                            modulesInfo[d.name][key] = openerpObj[key]
                has_odoo_modules = True
                print "   - %s" % d.name    
            except GithubException:
                print "   x %s: isn't an odoo module. Ignored!" % d.name
            
            # Si es un modulo se intentan obtener los datos restantes
            if d.name in modulesInfo:
                # Get Guide
                modulesInfo[d.name]['guide'] = None
                README = ['README.rst', 'README.md', 'README.txt']
                for readme_file in README:
                    readme_file_path = '%s/%s' % (d.name,readme_file)
                    if not base_dir == '.':
                        readme_file_path = '%s/%s/%s' % (base_dir,d.name,readme_file)
                    try:    
                        modulesInfo[d.name]['guide'] = github_repo.get_contents(readme_file_path, 
                                                                                branch)
                    except GithubException:
                        pass
                    if 'guide' in modulesInfo[d.name]:
                        break
                
                # Get Icon
                modulesInfo[d.name]['icon_image'] = None
                icon_file_path = '%s/static/description/icon.png' % d.name
                if not base_dir == '.':
                    icon_file_path = '%s/%s/static/description/icon.png' % (base_dir,d.name)  
                try:
                    modulesInfo[d.name]['icon_image'] = github_repo.get_contents(icon_file_path, branch)
                except GithubException:
                    pass
                
    if has_odoo_modules:
        return (base_commit.sha, modulesInfo)
    
    return (base_commit.sha, None)


class repos(models.Model):
    _name='eiqui.repos'
    
    @api.multi
    @api.depends('url','branch')
    def import_git_odoo_modules(self):
        eiqui_config = self.env['eiqui.config.settings'].search([], order="id DESC", limit=1)
        git_username = None
        git_password = None
        if eiqui_config:
            git_username = eiqui_config.git_username
            git_password = eiqui_config.git_password

        modules_obj = self.env['eiqui.modules']
        for record in self:
            try:
                repo_hash, repo_info = get_repo_info(git_username, git_password, record.url, record.branch) or {}
                if not repo_info:
                    raise Exception("Invalid Repository! No Odoo modules found.")
            except Exception as e:
                raise exceptions.ValidationError(str(e))
            
            self.commit = repo_hash
            
            repos_ids = []
            for module in repo_info:
                record_data = {
                    'name': repo_info[module]['name'], 
                    'author': repo_info[module]['author'],
                    'original_description': repo_info[module]['description'],
                    'original_summary': repo_info[module]['summary'],
                    'original_app': repo_info[module]['application'] or True,
                    'installable': repo_info[module]['installable'] or True,
                }
                if repo_info[module]['icon_image']:
                    record_data.update({'original_image': repo_info[module]['icon_image'].content})
                if repo_info[module]['guide']:
                    record_data.update({'original_guide': repo_info[module]['guide'].decoded_content})
                
                module_id = modules_obj.search([('repo_id','=',record.id), 
                                                ('folder','=',repo_info[module]['folder'])], limit=1)
                if not module_id:
                    record_data.update({
                        'repo_id': record.id,
                        'folder': repo_info[module]['folder']
                    })
                    modules_obj.create(record_data)
                else:
                    module_id.write(record_data)
                    
            record.last_import_date = fields.Date.today()
            repos_ids.append(record.id)
        return self.get_modules_view()
        
    @api.multi
    def _get_num_modules(self):
        modules_obj = self.env['eiqui.modules']
        for record in self:
            record.num_modules = modules_obj.search_count([('repo_id', '=', record.id)])
            
    @api.multi
    def get_modules_view(self):
        repos_ids = []
        for record in self:
            repos_ids.append(record.id)
            
        return {
            'name': _('Git Odoo Modules'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'eiqui.modules',
            'context': {},
            'domain':[('repo_id','in',repos_ids)],
        }
    
    @api.one
    @api.constrains('url', 'branch')
    def _check_description(self):
        count = self.search_count([('url', '=', self.url),('branch', '=', self.branch)])
        if count > 1:
            raise exceptions.ValidationError("Already exists a record with this combination of url repository and branch!")
    
     
    #Fields
    name = fields.Char('Name')
    url = fields.Char('Url Repository', required=True)
    branch = fields.Char('Branch', required=True)
    description = fields.Text(string='Description', translate=True)
    num_modules = fields.Integer(compute='_get_num_modules', string="Num. Modules")
    last_import_date = fields.Date(string="Last Import Date", readonly=True)
    commit = fields.Char('Current Commit', readonly=True)
    plan_ids = fields.Many2many('project.project', string="Plans Associated")