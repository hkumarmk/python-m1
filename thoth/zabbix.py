from pyzabbix import ZabbixAPIException

import logging
import sys

log = logging.getLogger(__name__)
stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)
log.addHandler(stream)
log.setLevel(logging.DEBUG)


class MonitorZabbix(object):

    def __init__(self, mon):
        self.host = Host(mon)
        self.hostgroup = HostGroup(mon)
        self.template = Template(mon)
        self.config = Configuration(mon)


class Host(object):
    interface_type = {'agent': 1,
                      'snmp': 2,
                      'ipmi': 3,
                      'jmx': 4}
    ENABLE = 0
    DISABLE = 1

    def __init__(self, mon):
        self.mon = mon
        self.hostgroup = HostGroup(mon)

    def add(self, name, ip, hostgroups=None, dns_name=None,
            interface_type='agent', port=10050, interface_useip=True):
        """ Add host
        :param name: host name
        :param ip: ip address
        :param hostgroups: list of host groups
        :param dns_name: dns name
        :param port: zabbix agent port
        :param interface_type: Type of interface. Acceptable values: agent,
                snmp, ipmi, jmx
        :param interface_useip: Use IP rather than dns
        :return: dict with hostid

        NOTE: this method only handle primary connectivity interface, you may
         add further interface using HostInterface class
        """
        if not dns_name:
            dns_name = name
        if interface_useip:
            useip = 1
        else:
            useip = 0

        if isinstance(hostgroups, str):
            hostgroups = [hostgroups]

        hostgroup_ids = self.hostgroup.get_hostgroup_ids(hostgroups)

        return self.mon.host.create(
            {
                'host': name,
                'interfaces':
                    [
                        {
                            'type': Host.interface_type[interface_type],
                            'main': 1,
                            'useip': useip,
                            'port': port,
                            'dns': dns_name,
                            'ip': ip
                        }
                    ],
                'groups': hostgroup_ids
            }
        )

    def search(self, filters=None):
        if not filters:
            filters = {}
        try:
            return self.mon.host.get(filter=filters)
        except ZabbixAPIException:
            return []

    def get(self, name):
        return self.search({'name': name})

    def get_id(self, name):
        hosts = self.get(name)
        if hosts:
            return hosts[0].get('hostid', None)
        else:
            return None

    def delete(self, name):
        id = self.get_id(name)
        if id:
            return self.mon.host.delete(id)
        raise Exception

    def update(self, name, hostgroups=None, status=None, **kwargs):
        id = self.get_id(name)
        params = {'hostid': id}
        if hostgroups is not None:
            if isinstance(hostgroups, str):
                hostgroups = [hostgroups]
            params.update({'groups': self.hostgroup.get_hostgroup_ids(hostgroups)})
        if status is not None:
            params.update({'status': status})
        return self.mon.host.update(dict(params, **kwargs))

    def disable(self, name):
        host = self.get(name)
        if host:
            if int(host[0].get('status', None)) == 0:
                return self.update(name, status=Host.DISABLE)
        else:
            return False

    def enable(self, name):
        host = self.get(name)
        if host:
            if int(host[0].get('status', None)) == 1:
                return self.update(name, status=Host.ENABLE)
        else:
            return False

    def get_host_ids(self, hosts):
        """ Return host ids in dict required to submit to zabbix api
        :param hosts: List of host names
        :return: list of host id dict, in the form zabbix api required
        """
        host_ids = []
        if hosts:
            for host in hosts:
                host_ids.append({'hostid': self.get_id(host)})

        return host_ids


class Template(object):

    def __init__(self, mon):
        self.mon = mon
        self.hostgroup = HostGroup(self.mon)
        self.host = Host(self.mon)
        self.config = Configuration(self.mon)

    def add(self, name, hostgroups=None, hosts=None, templates=None):
        params = {'host': name}
        if hostgroups is not None:
            if isinstance(hostgroups, str):
                hostgroups = [hostgroups]
            params.update({'groups': self.hostgroup.get_hostgroup_ids(hostgroups)})
        if hosts is not None:
            params.update({'hosts': self.host.get_host_ids(hosts)})
        if templates is not None:
            params.update({'templates': self.get_template_ids(templates)})
        return self.mon.template.create(params)

    def search(self, filters=None):
        if not filters:
            filters = {}
        try:
            return self.mon.template.get(filter=filters)
        except ZabbixAPIException as e:
            return []

    def get(self, name):
        return self.search({'name': name})

    def get_id(self, name):
        hosts = self.get(name)
        if hosts:
            return hosts[0].get('templateid', None)
        else:
            return None

    def delete(self, name):
        id = self.get_id(name)
        if id:
            return self.mon.template.delete(id)
        raise Exception

    def update(self, name, hostgroups=None, hosts=None, templates=None):
        id = self.get_id(name)
        params = {'templateid': id}
        if hostgroups is not None:
            if isinstance(hostgroups, str):
                hostgroups = [hostgroups]
            params.update({'groups': self.hostgroup.get_hostgroup_ids(hostgroups)})
        if hosts is not None:
            params.update({'hosts': self.host.get_host_ids(hosts)})
        if templates is not None:
            params.update({'templates': self.get_template_ids(templates)})
        return self.mon.template.update(params)

    def get_template_ids(self, templates):
        """ Return template ids in dict required to submit to zabbix api
        :param templates: List of template names
        :return: list of template id dict, in the form zabbix api required
        """
        template_ids = []
        if templates:
            for template in templates:
                template_ids.append({'templateid': self.get_id(template)})

        return template_ids

    def import_(self, config_stream, format='xml'):
        """ Import template
        :param config_stream: serialized string of template config data
        :param format: Format of stream, valid: xml or json
        """
        return self.config.import_config(config_stream, format=format)


class Configuration(object):

    def __init__(self, mon):
        self.mon = mon

    def import_config(self, config_stream, format='xml'):
        """ Import configuration
        :param config_stream: Serialized string of configuration data
        :param format: Format of config_stream, valid arguments: xml, json
        :return: True or False
        """
        rules = {
            'hosts': {
                'createMissing': True,
                'updateExisting': True
            },
            'items': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'applications': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'discoveryRules': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'graphs': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'groups': {
                'createMissing': True
            },
            'images': {
                'createMissing': True,
                'updateExisting': True
            },
            'maps': {
                'createMissing': True,
                'updateExisting': True
            },
            'screens': {
                'createMissing': True,
                'updateExisting': True
            },
            'templateLinkage': {
                'createMissing': True
            },
            'templates': {
                'createMissing': True,
                'updateExisting': True
            },
            'templateScreens': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'triggers': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            }
        }
        return self.mon.confimport(format, config_stream, rules)

    def export_config(self, config):
        pass


class HostGroup(object):

    def __init__(self, mon):
        self.mon = mon

    def add(self, name):
        if not self.get(name):
            try:
                return self.mon.hostgroup.create(name=name)
            except ZabbixAPIException as e:
                print "Error! Got exception while creating hostgroup: %s" % e
                return False
        else:
            print 'Hostgroup named %s already exists' % name
            return False

    def get(self, name):
        try:
            return self.mon.hostgroup.get(filter={'name': name})
        except ZabbixAPIException:
            return []

    def delete(self, name):
        id = self.get_id(name)
        if id:
            return self.mon.hostgroup.delete(id)
        raise Exception

    def get_id(self, name):
        groups = self.get(name)
        if groups:
            return groups[0].get('groupid', None)
        else:
            return None

    def list(self):
        return self.mon.hostgroup.get()

    def get_hostgroup_ids(self, hostgroups):
        """ Return hostgroup ids in dict required to submit to zabbix api
        :param hostgroups: List of hostgroup names
        :return: list of hostgroup id dict, in the form zabbix api required
        """
        hostgroup_ids = []

        if hostgroups:
            for hostgroup in hostgroups:
                hostgroup_ids.append({'groupid': self.get_id(hostgroup)})

        return hostgroup_ids


class HostGroupRegistry(object):
    hostgroups = {}

    def __init__(self, mon):
        self.mon = mon

    def add(self, name):
        hg = HostGroup(self.mon)
        HostGroupRegistry.hostgroups[name] = hg

    def delete(self, name):
        HostGroupRegistry.hostgroups[name].delete(HostGroupRegistry.hostgroups[name].id)

    def list(self):
        print HostGroupRegistry.hostgroups

    def get(self, name):
        print HostGroupRegistry.hostgroups.get(name, None)

    def load(self):
        self.mon.hostgroup.list()

