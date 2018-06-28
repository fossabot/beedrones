'''
Created on Sep 6, 2013

@author: darkbk
'''
import pprint

class VirtualMachine(object):
    """ """
    def __init__(self, name, id, os, type):
        """ """
        self.name = name
        self.id = id
        # RUNNING, SHUTOFF, PAUSED
        self.status = None
        self.os = os
        # vm, template
        self.type = type
        # vnc, ssh, ...
        self.ports = {}
        
        self.params = {}
        self.policy = {}
        
        self.resource = Resource()
    
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.get_dict())
    
    def get_dict(self):
        res = {'name':self.name,
               'id':self.id,
               'status':self.status,
               'os':self.os,
               'type':self.type,
               'ports':self.ports,
               'params':self.params,
               'policy':self.policy,
               'resource':self.resource.get_dict()}
        return res        

    def set_status(self, status):
        """ Set virtual machine status.
        
        :params status: select a value between RUNNING, SHUTOFF, PAUSED
        """
        self.status = status

    def set_port(self, name, value):
        """ """
        self.ports[name] = value

    def set_params(self, name, value):
        """ """
        self.params[name] = value
        
    def set_policy(self, name, value):
        """ """
        self.policy[name] = value

class Resource(object):
    """ """
    def __init__(self):
        """ """
        # freq. in MHz
        self.cpu = {'core':1, 'socket':1, 'freq':1000}
        # memory in kbyte
        self.memory = {'max':1000000, 'used':0}

    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.get_dict())
    
    def get_dict(self):
        res = {'cpu':self.cpu,
               'memory':self.memory}
        return res
       
    def set_cpu(self, core, socket, freq):
        self.cpu = {'core':core, 'socket':socket, 'freq':freq}
        
    def set_memory_max(self, max):
        self.memory['max'] = max
        
    def set_memory_used(self, used):
        self.memory['used'] = used    