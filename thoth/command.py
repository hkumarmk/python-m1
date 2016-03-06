import argparse
import sys
from thoth import get_driver

def main(argv = sys.argv[1:]):
    ops = {'hostgroup': {'add': 'add',
                   'delete': 'delete',
                   'update': 'update',
                   'list': 'list',
                   'get': 'get'},
     'template': {'add': 'add',
                  'delete': 'delete',
                  'update': 'update',
                  'list': 'list',
                  'get': 'get',
                  'import': 'import_'},
     'host': {'add': 'add',
              'get': 'get',
              'id': 'get_id',
              'delete': 'delete',
              'update': 'update',
              'list': 'search',
              'disable': 'disable',
              'enable': 'enable'}}

    def file_as_string(parser, arg):
        try:
            with open(arg, 'r') as f:
                return f.read()
        except:
            parser.error('The file %s does not exist!' % arg)

    ap_name = argparse.ArgumentParser(add_help=False)
    ap_name.add_argument('name', type=str, help='Name of the object')
    ap_name_opt = argparse.ArgumentParser(add_help=False)
    ap_name_opt.add_argument('--name', type=str, required=True, help='Name of the object')
    ap_force = argparse.ArgumentParser(add_help=False)
    ap_force.add_argument('-f', '--force', action='store_true', help='Force the action')
    ap_host_params = argparse.ArgumentParser(add_help=False)
    ap_host_params.add_argument('--ip', type=str, help='host IP address')
    ap_host_params.add_argument('--dns-name', type=str, help='host dns name')
    ap_host_params.add_argument('--hostgroups', type=str, nargs='+', help='hostgroups')
    ap_host_params.add_argument('--templates', type=str, nargs='+', help='templates')
    ap_host_params.add_argument('--interface-type', type=str, choices=['agent',
     'snmp',
     'jmx',
     'ipmi'], default='agent', help='interface type')
    ap_template_params = argparse.ArgumentParser(add_help=False)
    ap_template_params.add_argument('--hostgroups', type=str, nargs='+', help='hostgroups')
    ap_template_params.add_argument('--templates', type=str, nargs='+', help='templates')
    ap_template_params.add_argument('--hosts', type=str, nargs='+', help='hosts')
    ap = argparse.ArgumentParser(description='Manage monitors')
    ap.add_argument('-s', '--server', type=str, help='Zabbix server')
    sp = ap.add_subparsers(dest='resource', help='Resource to manage')
    p_hg = sp.add_parser('hostgroup', help='manage hostgroup')
    sp_hg = p_hg.add_subparsers(dest='action')
    p_hg_add = sp_hg.add_parser('add', parents=[ap_name], help='Add hosgrgoups')
    p_hg_get = sp_hg.add_parser('get', parents=[ap_name], help='Get specific hosgrgoup details')
    p_hg_delete = sp_hg.add_parser('delete', parents=[ap_name], help='delete hostgroup')
    p_hg_list = sp_hg.add_parser('list', help='List hostgroups')
    p_host = sp.add_parser('host', help='manage hosts')
    sp_host = p_host.add_subparsers(dest='action')
    p_host_add = sp_host.add_parser('add', parents=[ap_name_opt, ap_host_params], help='Add hosts')
    p_host_get = sp_host.add_parser('get', parents=[ap_name], help='Get specific host details')
    p_host_id = sp_host.add_parser('id', parents=[ap_name], help='Get specific host id')
    p_host_delete = sp_host.add_parser('delete', parents=[ap_name], help='delete hosts')
    p_host_list = sp_host.add_parser('list', help='List hosts')
    p_host_update = sp_host.add_parser('update', parents=[ap_name_opt, ap_host_params], help='Update hosts')
    p_host_disable = sp_host.add_parser('disable', parents=[ap_name], help='Disable monitoring for this host')
    p_host_enable = sp_host.add_parser('enable', parents=[ap_name], help='Enable monitoring for this host')
    p_template = sp.add_parser('template', help='manage templates')
    sp_template = p_template.add_subparsers(dest='action')
    p_template_add = sp_template.add_parser('add', parents=[ap_name_opt, ap_template_params], help='Add templates')
    p_template_get = sp_template.add_parser('get', parents=[ap_name], help='Get specific template details')
    p_template_id = sp_template.add_parser('id', parents=[ap_name], help='Get specific template id')
    p_template_delete = sp_template.add_parser('delete', parents=[ap_name], help='delete templates')
    p_template_list = sp_template.add_parser('list', help='List templates')
    p_template_update = sp_template.add_parser('update', parents=[ap_name_opt, ap_template_params], help='Update templates')
    p_template_import = sp_template.add_parser('import', help='Get specific template details')
    p_template_import.add_argument('config_stream', type=lambda x: file_as_string(p_template_import, x), help='Name of the template file')
    args = ap.parse_args()
    if args.server:
        p = get_driver('zabbix', 'http://' + args.server)
    else:
        p = get_driver('zabbix')
    param_dict = {key:vars(args)[key] for key in vars(args) if key not in ('action', 'provider', 'resource', 'server')}
    print getattr(getattr(p, args.resource), ops[args.resource][args.action])(**param_dict)
    return True


if __name__ == '__main__':
    sys.exit(not main(sys.argv[1:]))
