# -*- coding: utf-8 -*-
import re
from subprocess import Popen, PIPE
from github import Github, GithubException
import erppeek
import configparser
import fileinput
import binascii
import os
#import time

CWD = '/dockerbuild'
EIQUI_CLIENTNAME_REGEX = r'^\w{4,12}$'

# Obtiene el nombre del repositorio y el hash del commit más reciente
# INPUT
#    git_user [string]    El nombre de usuario en git para usar en las peticiones con github
#    git_pass [string]    La contraseña del usuario
#    repo     [string]    El repositorio a inspeccionar (puede ser la baliza)
#    branch   [string]    La rama de la que obtener la información
#
# RETURN
#    Tupla: Con los datos si todo fué bien.
#    Lanzará una excepción si algo fué mal.
#
def get_repo_commit_info(git_user, git_pass, repo, branch):
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
    master = github_repo.get_git_ref('heads/%s' % branch)
    base_commit = github_repo.get_git_commit(master.object.sha)
    return (user_repo, base_commit.sha)

# Inserta repositorios a la receta.
# Si el repositorio existe en la receta, se actualiza.
# INPUT
#    client    [string]       El nombre del cliente
#    repos   [list:string]    Lista de repositorios a añadir
#    branch  [string]         Rama
#    is_test [bool]           Si se trata de la instancia para test
#
# RETURN
#    -Nada-
#
def add_repos_to_client_recipe(client, repos, branch, git_user='', git_pass='', is_test=False):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    path_file = '%s/builds/%s/odoo/%s.cfg' % (CWD, client, 'test' if is_test else 'prod')
    config = configparser.ConfigParser()
    config.read(path_file)
    for repo in repos:
	(name, sha) = get_repo_commit_info(git_user, git_pass, repo, branch)
        # Si es OCB se trata de otra forma
	if name.lower() == 'ocb':
	    nrepo = "git %s odoo %s depth=10" % (repo, sha)
            config['openerp']['version'] = nrepo
        else:
	    nrepo = "git %s parts/%s %s" % (repo, name, sha)
            addons = 'addons' in config['openerp'] and config['openerp']['addons'].split('\n') or []
            found = False
            for (id, addon) in enumerate(addons):
                results = re.search(r'^git\s([^\s]+)', addon)
                if results and results.group(1) == repo:
                    addons[id] = nrepo
                    found = True
                    break
            if not found:
                addons.append(nrepo)
            config['openerp']['addons'] = '\n'.join(addons)
    with open(path_file, 'w') as configfile:
        config.write(configfile)
    # Cambiar 'addons =' por 'addons +='
    # FIXME: No me parece una solucion elegante
    file = fileinput.input(path_file, inplace=1)
    for line in file:
        line = line.replace('addons =', 'addons +=').rstrip()
        print line
    file.close()

# Recolecta informacion de la receta.
# INPUT
#    client  [string]    El nombre del cliente
#    is_test [bool]      Si se trata de la instancia para test
#
# RETURN
#    Diccionario con los datos recolectados.
#
def get_client_recipe_info(client, is_test=False):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    path_file = '%s/builds/%s/odoo/%s.cfg' % (CWD, client, 'test' if is_test else 'prod')
    config = configparser.ConfigParser()
    config.read(path_file)
    values = ['xmlrpc_port', 'admin_passwd', 'db_user', 'db_password', 'data_dir', 'logfile']
    result = {}
    for val in values:
        valname = 'options.%s' % val
        result.update({val: valname in config['openerp'] and config['openerp'][valname] or ''})
    return result

# Wrapper para llamar a los script de eiqui
# INPUT
#    script [string]    El nombre del script (sin 'ei_')
#    params [list]      Lista de parametros para pasar al script
#
# RETURN
#    Tupla: El código de salida del script, lo que imprimió por stdout y lo que imprimió por stderr
#
def call_eiqui_script(script, params):
    eiquiscript = "sudo %s/ei_%s %s" % (CWD, script, ' '.join(params))
    proc = Popen(eiquiscript, shell=True, universal_newlines=True, stdout=PIPE, stderr=PIPE, cwd=CWD)
    (out, err) = proc.communicate()
    return (proc.returncode, out, err)

def create_client(client):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    (rcode, out, err) = call_eiqui_script("crear_host", ['-c',"'%s'" % client])
    #print "OUT:\n%s\n\nERROR:\n%s\n" % (out,err)
    if rcode == 0:
        return True
    raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode,out,err))

def remove_client(client, full=False):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    params = ['-c',"'%s'" % client]
    if full:
        params += ['-b','-v']
    (rcode, out, err) = call_eiqui_script("borrar_host", params)
    #print "OUT:\n%s\n\nERROR:\n%s\n" % (out,err)
    if rcode == 0:
        return True
    raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode,out,err))

def update_client_buildbot(client, is_test=False):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    (rcode, out, err) = call_eiqui_script("actualizar_buildout", ['-c',"'%s'" % client,'-t' if is_test else '-p'])
    #print "OUT:\n%s\n\nERROR:\n%s\n" % (out,err)
    if rcode == 0:
        return True
    raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode,out,err))


# Construir la url del host
# INPUT
#    client  [string]    El nombre del client
#    is_test [bool]      Si se trata de la instancia para test
#
# RETURN
#    String: Url del host
#
def get_client_host_url(client, is_test=False, is_host=False):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    schema = 'http'
    if is_host:
        return '%s://host.%s.eiqui.com' % (schema, client)
    elif is_test:
        return '%s://test.%s.eiqui.com' % (schema, client)
    return '%s://%s.eiqui.com' % (schema, client)

# Crear una base de datos para Odoo
# INPUT
#    url          [string]    URL de la instancia Odoo
#    masterpasswd [string]    Contraseña maestra de Odoo
#    dbname       [string]    Nombre de la nueva base de datos
#    lang         [string]    Idioma a usar en formato ISO-639
#    adminpasswd  [string]    Contraseña para el usuario admin de la nueva base de datos
#
# RETURN
#    Bool: True si todo fue bien
#
def odoo_create_db(url, masterpasswd, dbname, lang, adminpasswd):
    try:
    	client = erppeek.Client(url)
        res = client.create_database(masterpasswd, dbname, lang=lang, user_password=adminpasswd)
    except:
        raise
    return res == 1

# Instala los modulos que pueda en la instacia indicada de Odoo
# INPUT
#    url        [string]         URL de la instancia Odoo
#    dbname     [string]         Nombre de la base de datos
#    user       [string]         Nombre del usuario
#    userpasswd [string]         Contraseña del usuario
#    modules    [list:string]    Lista de modulos a instalar (nombre técnico)
#
# RETURN
#    Bool: True si alguno fue bien
#
def odoo_install_modules(url, dbname, user, userpasswd, modules):
    try:
    	client = erppeek.Client(url, db=dbname, user=user, password=userpasswd)
        client.install(*modules)
    except:
        raise
    return True

def prepare_client_instance(client, repos, branch, modules_installed=None, git_user='', git_pass='', is_test=False):
    try:
        adminpasswd = binascii.hexlify(os.urandom(4)).decode()
        if repos and len(repos) > 0:
            add_repos_to_client_recipe(client, repos, branch, git_user=git_user, git_pass=git_pass, is_test=is_test)
            update_client_buildbot(client, is_test)
        inst_info = get_client_recipe_info(client, is_test)
        odoo_url_host = '%s:8069' % get_client_host_url(client, is_test, True)
        #time.sleep(15) # No somos impacientes y esperamos a que se asiente todo...
        res = odoo_create_db(odoo_url_host, inst_info['admin_passwd'], client, 'es_ES', adminpasswd)
        if res:
            if modules_installed and len(modules_installed) > 0:
                res = odoo_install_modules(odoo_url_host, client, 'admin', adminpasswd, modules_installed)
                if not res:
                    print 'WARNING: Errors while installing modules!'
    except:
        raise
    return (inst_info, adminpasswd, get_client_host_url(client, is_test, False))
