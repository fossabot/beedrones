'''
Created on Sep 6, 2013

@author: darkbk
'''
import pprint

class GenericInterface(object):
    """ """
    def __init__(self, name, itype, active):
        """ """
        self.name = name
        self.type = itype
        self.params = {}
        self.policy = {}
        self.active = active
    
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.get_dict())
    
    def get_dict(self):
        res = {'name':self.name,
               'type':self.type,
               'active':self.active,
               'params':self.params,
               'policy':self.policy}
        return res        
    
    def set_param(self, name, value):
        """ """
        self.params[name] = value
        
    def set_policy(self, name, value):
        """ """
        self.policy[name] = value

class Interface(GenericInterface):
    """Ethernet interface"""
    def __init__(self, name, active, mac):
        """ """
        super(Interface, self).__init__(name, 'ethernet', active)
        
        self.mac = mac
        self.protocol = []
    
    def get_dict(self):
        res = super(Interface, self).get_dict()
        res.update({'mac':self.mac,
                    'protocol':self.protocol})
        return res      

    def add_ip_protocol(self, family, address, subnet, bootproto='static'):
        """
        Example:
            
            obj.add_ip_protocol('ipv4', '10.102.90.3', '24')
            obj.add_ip_protocol('ipv6', 'fe80::ea39:35ff:feba:8158', '64')
            obj.add_ip_protocol('ipv4', '10.102.90.14', '255.255.255.0')
            obj.add_ip_protocol('ipv4', None, None, bootproto='dhcp')
            {'family': 'ipv4',
                'ip': {'address': '10.102.90.3', 'prefix': '24'}},
               {'family': 'ipv6',
                'ip': {'address': 'fe80::ea39:35ff:feba:8158',
                       'prefix': '64'}}
        """
        self.protocol.append({'bootproto':bootproto,
                              'family':family,
                              'ip':{'address':address, 'subnet':subnet}})

class BondInterface(GenericInterface):
    """Ethernet interface"""
    def __init__(self, name, active):
        """ """
        super(BondInterface, self).__init__(name, 'bond', active)
        
        # list of interface
        self.ports = []
    
    def get_dict(self):
        res = super(BondInterface, self).get_dict()
        res.update({'ports':[port.get_dict() for port in self.ports]})
        return res      

    def add_port(self, port):
        """Use to add an interface
        """
        self.ports.append(port)
        
class Bridge(GenericInterface):
    """Ethernet interface"""
    def __init__(self, name, active):
        """ """
        super(Bridge, self).__init__(name, 'bridge', active)

        self.protocol = []
        # list of interface and bond interface
        self.ports = []
        # list of sub-bridge or sub-vswitch
        self.port_groups = []
    
    def get_dict(self):
        res = super(Bridge, self).get_dict()
        res.update(
            {'protocol':self.protocol,
             'ports':[port.get_dict() for port in self.ports],
             'port_groups':[grp.get_dict() for grp in self.port_groups]})
        return res      

    def add_ip_protocol(self, family, address, subnet, bootproto='static'):
        """
        Example:
            
            obj.add_ip_protocol('ipv4', '10.102.90.3', '24')
            obj.add_ip_protocol('ipv6', 'fe80::ea39:35ff:feba:8158', '64')
            obj.add_ip_protocol('ipv4', '10.102.90.14', '255.255.255.0')
            obj.add_ip_protocol('ipv4', bootproto='dhcp')
            {'family': 'ipv4',
                'ip': {'address': '10.102.90.3', 'prefix': '24'}},
               {'family': 'ipv6',
                'ip': {'address': 'fe80::ea39:35ff:feba:8158',
                       'prefix': '64'}}
        """
        self.protocol.append({'bootproto':bootproto,
                              'family':family,
                              'ip':{'address':address, 'subnet':subnet}})
        
    def add_port(self, port):
        """Use to add an interface or a bond interface
        """
        self.ports.append(port)

    def add_port_group(self, port_group):
        """Use to add a sub-bridge or a sub-vswitch
        """
        self.port_groups.append(port_group)

class VSwtich(Bridge):
    """Ethernet interface"""
    def __init__(self, name, active):
        """ """
        super(VSwtich, self).__init__(name, active)
        self.type = 'vswitch'
        
class Network(object):
    """ """
    def __init__(self, name, active):
        """ """
        self.name = name
        self.vms = []
        self.params = {}
        self.policy = {}
        self.active = active
    
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.get_dict())
    
    def get_dict(self):
        res = {'name':self.name,
               'vms':self.vms,
               'active':self.active,
               'params':self.params,
               'policy':self.policy}
        return res        
    
    def set_param(self, name, value):
        """ """
        self.params[name] = value
        
    def set_policy(self, name, value):
        """ """
        self.policy[name] = value
    
    def add_vm(self, vm):
        self.vms.append(vm)