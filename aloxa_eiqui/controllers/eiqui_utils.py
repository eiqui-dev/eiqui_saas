# -*- coding: utf-8 -*-
import re
from subprocess import Popen, PIPE
from github import Github, GithubException
import erppeek
import configparser
import fileinput
import binascii
from shutil import copyfile
import os
import time
import logging
import requests
_logger = logging.getLogger(__name__)

CWD = '/dockerbuild'
CWD_BUILDS = '%s/builds' % CWD
ADMIN_USER = 'admin'
EIQUI_USER = 'eiqui'
EIQUI_LOGIN = 'info@aloxa.eu'
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
    instance_mode = 'test' if is_test else 'prod'
    path_file = '%s/%s/%s/%s.cfg' % (CWD_BUILDS, client, instance_mode, instance_mode)
    config = configparser.ConfigParser()
    config.read(path_file)
    repos = list(set(repos))  # Remove duplicate values
    for repo in repos:
        (name, sha) = get_repo_commit_info(git_user, git_pass, repo, branch)
        # Si es OCB se trata de otra forma
        if name.lower() == 'ocb':
            nrepo = "git %s odoo %s depth=1" % (repo, sha)
            config['openerp']['version'] = nrepo
        else:
            nrepo = "git %s parts/%s %s" % (repo, name, sha)
            addons = 'addons' in config['openerp'] and config['openerp']['addons'].split('\n') or []
            found = False
            for (index, addon) in enumerate(addons):
                results = re.search(r'^git\s([^\s]+)', addon)
                if results and results.group(1) == repo:
                    addons[index] = nrepo
                    found = True
                    break
            if not found:
                addons.append(nrepo)
    config['openerp']['addons'] = '\n'.join(addons)
    with open(path_file, 'w') as configfile:
        config.write(configfile)
    # Cambiar 'addons =' por 'addons +='
    # FIXME: No me parece una solucion elegante
    cfg_file = fileinput.input(path_file, inplace=1)
    for line in cfg_file:
        line = line.replace('addons =', 'addons +=').rstrip()
        print line
    cfg_file.close()


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
    instance_mode = 'test' if is_test else 'prod'
    path_file = os.path.join(CWD_BUILDS, client, instance_mode, '%s.cfg' % instance_mode)
    config = configparser.ConfigParser()
    result = {}
    if any(config.read(path_file)):
        values = ['xmlrpc_port', 'admin_passwd', 'db_user', 'db_password', 'data_dir', 'logfile']
        for val in values:
            valname = 'options.%s' % val
            result.update({val: valname in config['openerp'] and config['openerp'][valname] or ''})
        return result
    return False


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


def create_droplet(client):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')

    (rcode, out, err) = call_eiqui_script("crear_host", ['droplet', '-c', "'%s'" % client])
    if rcode != 0:
        raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode, out, err))
    return True


def create_client(client, branch="9.0", is_test=False):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')

    (rcode, out, err) = call_eiqui_script("crear_host", ['dockers', '-c', "'%s'" % client, '-v', "'%s'" % branch])
    if rcode != 0:
        raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode, out, err))
    (rcode, out, err) = call_eiqui_script("crear_host", ['proxy', '-c', "'%s'" % client])
    if rcode != 0:
        raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode, out, err))
    (rcode, out, err) = call_eiqui_script("crear_host", ['setup', '-c', "'%s'" % client])
    if rcode != 0:
        raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode, out, err))
    (rcode, out, err) = call_eiqui_script("crear_host", ['push', '-c', "'%s'" % client])
    if rcode != 0:
        raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode, out, err))
    return True


def create_client_instance(client, is_test=False):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    (rcode, out, err) = call_eiqui_script("crear_instancia", ['-c', "'%s'" % client, is_test and '-t' or '-d'])
    if rcode == 0:
        return True
    raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode,out,err))


def monitor_client(client):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    (rcode, out, err) = call_eiqui_script("monitorizar_host", ['-c',"'%s'" % client])
    if rcode == 0:
        return True
    raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode,out,err))


def create_snapshot(client):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    (rcode, out, err) = call_eiqui_script("crear_snapshot", ['-c',"'%s'" % client])
    if rcode == 0:
        return True
    raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode,out,err))


def restore_snapshot(client, snapshot):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    (rcode, out, err) = call_eiqui_script("resturar_snapshot", ['-c',"'%s'" % client])
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
    if rcode == 0:
        return True
    raise Exception('Return Code: %d\nOut: %s\nErr: %s\n' % (rcode,out,err))


def update_client_buildbot(client, is_test=False):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    (rcode, out, err) = call_eiqui_script("actualizar_buildout", ['-c', "'%s'" % client, is_test and '-t' or '-p'])
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
    if is_host and is_test:
        return '%s://test.%s.eiqui.com:8169' % (schema, client)
    elif is_host:
        return '%s://host.%s.eiqui.com:8069' % (schema, client)
    elif is_test:
        return '%s://test.%s.eiqui.com' % (schema, client)
    return '%s://%s.eiqui.com' % (schema, client)


def create_user(server_host, dbname, adminuser, adminpasswd, newuser, newlogin, newpasswd):
    try:
        client = erppeek.Client(str(server_host))
        client.login(adminuser, password=adminpasswd, database=dbname)
        res = client.create('res.users', {'name':newuser, 'login':newlogin, 'new_password':newpasswd})
    except:
        raise
    return res == 1


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
def odoo_create_db(server_host, masterpasswd, dbname, lang, adminpasswd):
    try:
        client = erppeek.Client(str(server_host))
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
        client = erppeek.Client(str(url), db=dbname, user=user, password=userpasswd)
        client.install(*modules)
    except:
        raise
    return True

def prepare_client_recipe(client, repos, branch, git_user='', git_pass=''):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    try:
        # Produccion
        if repos and any(repos):
            add_repos_to_client_recipe(client, repos, branch, git_user=git_user, git_pass=git_pass, is_test=False)
            update_client_buildbot(client, False)
    except:
        raise
    

def prepare_client_instance(client, repos, branch, modules_installed=None, git_user='', git_pass=''):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    try:
        base_url = get_client_host_url(client, False, False)
        adminpasswd = binascii.hexlify(os.urandom(4)).decode()
        # Produccion
        inst_info = get_client_recipe_info(client, False)
        if not inst_info:
            raise Exception("Error! Can't read recipe data")
        _logger.info(inst_info)
        odoo_url_host = get_client_host_url(client, False, True)
        time.sleep(15)  # No somos impacientes y esperamos a que se asiente todo...
        res = odoo_create_db(odoo_url_host, inst_info['admin_passwd'], client, 'es_ES', adminpasswd)
        if res:
            if modules_installed and any(modules_installed):
                res = odoo_install_modules(odoo_url_host, client, ADMIN_USER, adminpasswd, modules_installed)
                if not res:
                    print 'WARNING: Errors while installing modules!'
            create_user(odoo_url_host, client, ADMIN_USER, adminpasswd, EIQUI_USER, EIQUI_LOGIN, inst_info['admin_passwd'])
    except:
        raise
    return (inst_info, adminpasswd, base_url)


def rebuild_test_instance(client, adminpasswd):
    if not re.match(EIQUI_CLIENTNAME_REGEX, client):
        raise Exception('Invalid Client Name!')
    try:
        copyfile('%s/%s/prod/prod.cfg' % (CWD_BUILDS, client), '%s/%s/test/test.cfg' % (CWD_BUILDS, client))
        create_client_test(client)
        odoo_url_host = get_client_host_url(client, True, True)
        client = erppeek.Client(str(odoo_url_host))
        db_list = client.db.list()
        for db in db_list:
            client.login(ADMIN_USER, password=adminpasswd, database=db) 
            # Install "Test Ribbon" Module
            client.install(*('web_environment_ribbon'))
            # Remove Mail Data
            record_ids = client.search("fetchmail.server", [()])
            client.unlink("fetchmail.server", record_ids)
            record_ids = client.search("ir.mail_server", [()])
            client.unlink("ir.mail_server", record_ids) 
    except:
        raise