import os
from re import match


def _get_zabbix(server = None, password = None, user = None):
    from pyzabbix import ZabbixAPI
    import thoth.zabbix as zabbix
    zabbix_server = server if server else os.environ.get('ZABBIX_SERVER', 'http://127.0.0.1')
    zabbix_user = user if user else os.environ.get('ZABBIX_USER', 'Admin')
    zabbix_password = password if password else os.environ.get('ZABBIX_PASSWORD', 'zabbix')
    if zabbix_server and not match('^http[s]*://', zabbix_server):
        zabbix_server = 'http://' + zabbix_server
    zbx = ZabbixAPI(zabbix_server)
    zbx.login(zabbix_user, zabbix_password)
    return zabbix.MonitorZabbix(zbx)


def get_driver(provider, *args, **kwargs):
    """ Idea is to have different supported drivers.
    :param provider: Provider name
    :return:
    """
    return _get_zabbix(*args, **kwargs)
