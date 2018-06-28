'''
Created on Sep 6, 2013

@author: darkbk
'''
import pprint

class Datastore(object):
    """ """
    def __init__(self, name, id, dtype, active):
        """ """
        self.name = name
        self.id = id
        self.type = dtype
        self.url = None
        self.timestamp = None
        self.params = {}
        self.policy = {}
        self.active = active
        self.size = {}
        self.hosts = []
        self.vms = []
    
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.get_dict())
    
    def get_dict(self):
        res = {'name':self.name,
               'id':self.id,
               'type':self.type,
               'url':self.url,
               'timestamp':self.timestamp,
               'active':self.active,
               'params':self.params,
               'policy':self.policy,
               'size':self.size,
               'hosts':self.hosts,
               'vms':self.vms}
        return res        

    def set_timestamp(self, timestamp):
        """ """
        self.timestamp = timestamp

    def set_url(self, url):
        """ """
        self.url = url
   
    def set_param(self, name, value):
        """ """
        self.params[name] = value
        
    def set_policy(self, name, value):
        """ """
        self.policy[name] = value

    def set_size(self, name, value):
        """ """
        self.size[name] = value

    def add_host(self, host_name):
        """ """
        self.hosts.append(host_name)

    def add_vm(self, vm_name):
        """ """
        self.vms.append(vm_name)

class DatastoreItem(object):
    """ """
    def __init__(self, name, path, size, itype, permission, itime):
        """ """
        self.name = name
        self.path = path
        self.size = size
        self.type = itype
        self.permission = permission
        self.itime = itime
    
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.get_dict())
    
    def get_dict(self):
        res = {'name':self.name,
               'path':self.path,
               'size':self.size,
               'type':self.type,
               'permission':self.permission,
               'time':self.itime}
        return res    

class Storage(object):
    """Ethernet interface"""
    def __init__(self, name, id, device='disk', driver=None, target=None, 
                       size=None):
        """ """
        self.name = name
        self.id = id
        # device type. Ex. disk, cdrom
        self.device = device
        # driver used to emulate disk. Ex. qemu qcow2
        self.driver = driver
        # 'bus': 'virtio', 'dev': 'vdb'
        self.target = target
        self.size = size
        # datastore refercence
        self.sources = []

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.get_dict())
   
    def get_dict(self):
        res = {'name':self.name,
               'id':self.id,
               'device':self.device,
               'driver':self.driver,
               'target':self.target,
               'size':self.size,
               'sources':self.sources}
        return res        

    def set_source(self, path, type, size, datastore):
        self.sources.append({'path':path,
                             'type':type,
                             'size':size,
                             'datastore':datastore})