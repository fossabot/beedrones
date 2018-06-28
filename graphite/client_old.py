'''
Created on 28 ott 2016

@author: darkbk, igna

defininizione classe graphite per ricercare dentro lo stesso i dati relativi al carico e 
definizione classe per tabella environments
'''
import json
import requests
from pprint import pprint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence

class MyError(Exception):
    pass

Base_Environments = declarative_base()
class Environments(Base_Environments):
    __tablename__='environments'
    id =  Column(Integer, Sequence('servers_id_seq'), primary_key=True)
    name = Column(String(50), nullable=False)
    uri = Column(String(150), nullable=False)

    def __repr__(self):
        return "Environments: {}>".format(self.name)

class Graphite():
    """
    this class is to get cpu usage for an host or a vm from graphite
    """
    def __init__(self,  **params):
        """
        :param uri: graphite uri
        :param environ: environment name
        """
        if not 'environ' in params.keys():
            raise MyError("missing environ parameter")
        else:
            self.environ = params['environ']
        if not 'uri' in params.keys():
            raise MyError("missing uri parameter")
        else:
            self.uri = params['uri']

    def get_cpu_usage(self, **params):
        """get cpu usage in last min as absolute values average
        :param name: vm/phisical host name
        :param min: minutes
        :param platform: 'kvm_vm' for a kvm vm 
                 'vmware_vm' for a vmware vm 
                 'host' for a physical host 
                 'kvm_host' for a kvm compute node
                 'vmware_host' for vmware compute node

        :param min: usage period in minutes
        """
        if not 'name' in params.keys():
            raise MyError("missing name parameter")
        else:
            name = params['name']

        if not 'platform' in params.keys():
            raise MyError("missing platform parameter")
        else:
            if (params['platform'] != "host") and \
            (params['platform'] != "kvm_host") and \
            (params['platform'] != "vmware_host") and \
            (params['platform'] != "vmware_vm") and \
            (params['platform'] != "kvm_vm"):
                raise MyError("platform must be 'host' or 'kvm_host' or 'vmware_host' or 'vmware_vm' or 'kvm_vm'")
            platform = params['platform']
        if not 'min' in params.keys():
            raise MyError("missing min parameter")
        else:
            min = params['min']

        minutes=min
        """
        check if the vm/host name is present in graphite
        """
        result, text = self.find_graphite_element(name, platform, self.environ, self.uri) 
        if not result:
            return False, text
        path=text

        if platform == 'kvm_vm':
            target = "absolute("+path+"."+name+".libvirt.virt_cpu_total"+")"
        if platform == 'kvm_host':
            target = "absolute("+path+"."+name+".cpu-*.cpu-system"+")"
        payload = {'target': target, 'from': "-"+str(minutes)+"min", 'format': 'json'}
        try:
            r = requests.get(self.uri+"/render", params=payload)
        except Exception as e:
            return False, e
        
        dictio=json.loads(r.text)
        average=self.calculate(dictio)
        return True, average


    def get_mem_used(self, **params):
        """get mem used (bytes)  in last min as absolute values average
        :param name: vm/phisical host name
        :param min: minutes
        :param platform: 'kvm_vm' for a kvm vm 
                 'vmware_vm' for a vmware vm 
                 'host' for a physical host 
                 'kvm_host' for a kvm compute node
                 'vmware_host' for vmware compute node

        :param min: usage period in minutes
        """
        if not 'name' in params.keys():
            raise MyError("missing name parameter")
        else:
            name = params['name']

        if not 'platform' in params.keys():
            raise MyError("missing platform parameter")
        else:
            if (params['platform'] != "host") and \
            (params['platform'] != "kvm_host") and \
            (params['platform'] != "vmware_host") and \
            (params['platform'] != "vmware_vm") and \
            (params['platform'] != "kvm_vm"):
       
                raise MyError("platform must be 'host' or 'kvm_host' or 'vmware_host' or 'vmware_vm' or 'kvm_vm'")
            platform = params['platform']
        if not 'min' in params.keys():
            raise MyError("missing min parameter")
        else:
            minutes = params['min']

        """
        check if the vm/host name is present in graphite
        """
        result, text = self.find_graphite_element(name, platform, self.environ, self.uri) 
        if not result:
            return False, text
        path=text

        if platform == 'kvm_vm':
                return False, "only total memory is returned for kvm_vm"
        if platform == 'kvm_host':
            target = "absolute("+path+"."+name+".memory.memory-used"+")"
        payload = {'target': target, 'from': "-"+str(minutes)+"min", 'format': 'json'}
        try:
            r = requests.get(self.uri+"/render", params=payload)
        except Exception as e:
            return False, e
        
        dictio=json.loads(r.text)
        average=self.calculate(dictio)
        return True, average

    def get_mem_free(self, **params):
        """get mem free (bytes)  in last min as absolute values average
        :param name: vm/phisical host name
        :param min: minutes
        :param platform: 'kvm_vm' for a kvm vm 
                 'vmware_vm' for a vmware vm 
                 'host' for a physical host 
                 'kvm_host' for a kvm compute node
                 'vmware_host' for vmware compute node

        :param min: usage period in minutes
        """
        if not 'name' in params.keys():
            raise MyError("missing name parameter")
        else:
            name = params['name']

        if not 'platform' in params.keys():
            raise MyError("missing platform parameter")
        else:
            if (params['platform'] != "host") and \
            (params['platform'] != "kvm_host") and \
            (params['platform'] != "vmware_host") and \
            (params['platform'] != "vmware_vm") and \
            (params['platform'] != "kvm_vm"):
       
                raise MyError("platform must be 'host' or 'kvm_host' or 'vmware_host' or 'vmware_vm' or 'kvm_vm'")
            platform = params['platform']
        if not 'min' in params.keys():
            raise MyError("missing min parameter")
        else:
            minutes = params['min']

        """
        check if the vm/host name is present in graphite
        """
        result, text = self.find_graphite_element(name, platform, self.environ, self.uri) 
        if not result:
            return False, text
        path=text

        if platform == 'kvm_vm':
                return False, "only total memory is returned for kvm_vm"
        if platform == 'kvm_host':
            target = "absolute("+path+"."+name+".memory.memory-free"+")"
        payload = {'target': target, 'from': "-"+str(minutes)+"min", 'format': 'json'}
        try:
            r = requests.get(self.uri+"/render", params=payload)
        except Exception as e:
            return False, e
        
        dictio=json.loads(r.text)
        average=self.calculate(dictio)
        return True, average


    def get_mem_buffered(self, **params):
        """get mem buffered (bytes)  in last min as absolute values average
        :param name: vm/phisical host name
        :param min: minutes
        :param platform: 'kvm_vm' for a kvm vm 
                 'vmware_vm' for a vmware vm 
                 'host' for a physical host 
                 'kvm_host' for a kvm compute node
                 'vmware_host' for vmware compute node

        :param min: usage period in minutes
        """
        if not 'name' in params.keys():
            raise MyError("missing name parameter")
        else:
            name = params['name']

        if not 'platform' in params.keys():
            raise MyError("missing platform parameter")
        else:
            if (params['platform'] != "host") and \
            (params['platform'] != "kvm_host") and \
            (params['platform'] != "vmware_host") and \
            (params['platform'] != "vmware_vm") and \
            (params['platform'] != "kvm_vm"):
       
                raise MyError("platform must be 'host' or 'kvm_host' or 'vmware_host' or 'vmware_vm' or 'kvm_vm'")
            platform = params['platform']
        if not 'min' in params.keys():
            raise MyError("missing min parameter")
        else:
            minutes = params['min']

        """
        check if the vm/host name is present in graphite
        """
        result, text = self.find_graphite_element(name, platform, self.environ, self.uri) 
        if not result:
            return False, text
        path=text

        if platform == 'kvm_vm':
                return False, "only total memory is returned for kvm_vm"
        if platform == 'kvm_host':
            target = "absolute("+path+"."+name+".memory.memory-buffered"+")"
        payload = {'target': target, 'from': "-"+str(minutes)+"min", 'format': 'json'}
        try:
            r = requests.get(self.uri+"/render", params=payload)
        except Exception as e:
            return False, e
        
        dictio=json.loads(r.text)
        average=self.calculate(dictio)
        return True, average

    def get_mem_cached(self, **params):
        """get mem cached (bytes)  in last min as absolute values average
        :param name: vm/phisical host name
        :param min: minutes
        :param platform: 'kvm_vm' for a kvm vm 
                 'vmware_vm' for a vmware vm 
                 'host' for a physical host 
                 'kvm_host' for a kvm compute node
                 'vmware_host' for vmware compute node

        :param min: usage period in minutes
        """
        if not 'name' in params.keys():
            raise MyError("missing name parameter")
        else:
            name = params['name']

        if not 'platform' in params.keys():
            raise MyError("missing platform parameter")
        else:
            if (params['platform'] != "host") and \
            (params['platform'] != "kvm_host") and \
            (params['platform'] != "vmware_host") and \
            (params['platform'] != "vmware_vm") and \
            (params['platform'] != "kvm_vm"):
       
                raise MyError("platform must be 'host' or 'kvm_host' or 'vmware_host' or 'vmware_vm' or 'kvm_vm'")
            platform = params['platform']
        if not 'min' in params.keys():
            raise MyError("missing min parameter")
        else:
            minutes = params['min']

        """
        check if the vm/host name is present in graphite
        """
        result, text = self.find_graphite_element(name, platform, self.environ, self.uri) 
        if not result:
            return False, text
        path=text

        if platform == 'kvm_vm':
                return False, "only total memory is returned for kvm_vm"
        if platform == 'kvm_host':
            target = "absolute("+path+"."+name+".memory.memory-cached"+")"
        payload = {'target': target, 'from': "-"+str(minutes)+"min", 'format': 'json'}
        try:
            r = requests.get(self.uri+"/render", params=payload)
        except Exception as e:
            return False, e
        
        dictio=json.loads(r.text)
        average=self.calculate(dictio)
        return True, average

    def get_mem_total(self, **params):
        """get mem total (bytes)  in last min as absolute values average
        :param name: vm/phisical host name
        :param min: minutes
        :param platform: 'kvm_vm' for a kvm vm 
                 'vmware_vm' for a vmware vm 
                 'host' for a physical host 
                 'kvm_host' for a kvm compute node
                 'vmware_host' for vmware compute node

        :param min: usage period in minutes
        """
        if not 'name' in params.keys():
            raise MyError("missing name parameter")
        else:
            name = params['name']

        if not 'platform' in params.keys():
            raise MyError("missing platform parameter")
        else:
            if (params['platform'] != "host") and \
            (params['platform'] != "kvm_host") and \
            (params['platform'] != "vmware_host") and \
            (params['platform'] != "vmware_vm") and \
            (params['platform'] != "kvm_vm"):
       
                raise MyError("platform must be 'host' or 'kvm_host' or 'vmware_host' or 'vmware_vm' or 'kvm_vm'")
            platform = params['platform']
        if not 'min' in params.keys():
            raise MyError("missing min parameter")
        else:
            minutes = params['min']

        """
        check if the vm/host name is present in graphite
        """
        result, text = self.find_graphite_element(name, platform, self.environ, self.uri) 
        if not result:
            return False, text
        path=text

        if platform == 'kvm_vm':
            target = "absolute("+path+"."+name+".libvirt.memory-total"+")"
        if platform == 'kvm_host':
        #    target = "absolute("+path+"."+name+".memory.memory-used"+")"
        #    return False, "method not yet defined for kvm_host"
            rs, freemem=self.get_mem_free(name=name, min=minutes, platform=platform)
            if not rs:
                return False, rs
            rs, usedmem=self.get_mem_used(name=name, min=minutes, platform=platform)
            if not rs:
                return False, rs
            rs, cachedmem=self.get_mem_cached(name=name, min=minutes, platform=platform)
            if not rs:
                return False, rs
            rs, bufferedmem=self.get_mem_buffered(name=name, min=minutes, platform=platform)
            if not rs:
                return False, rs
            return True, bufferedmem+cachedmem+usedmem+freemem
        payload = {'target': target, 'from': "-"+str(minutes)+"min", 'format': 'json'}
        try:
            r = requests.get(self.uri+"/render", params=payload)
        except Exception as e:
            return False, e
        
        dictio=json.loads(r.text)
        average=self.calculate(dictio)
        return True, average

    @staticmethod 
    def find_graphite_element(element, platform, environ, uri):
        """check the graphite tree to find an element (host or vm)
        :param element: vm/phisical host name
        :param platform: 'kvm_vm' for a kvm vm 
                 'vmware_vm' for a vmware vm 
                 'host' for a physical host 
                 'kvm_host' for a kvm compute node
                 'vmware_host' for vmware compute node
        :param environ: envrontment name
        :param uri: graphite uti
        """
        if (platform != "host") and \
        (platform != "kvm_host") and \
        (platform != "vmware_host") and \
        (platform != "vmware_vm") and \
        (platform != "kvm_vm"):
                return False, "platform must be 'host' or 'kvm_host' or 'vmware_host' or 'vmware_vm' or 'kvm_vm'"
        if platform == 'kvm_host' or platform == 'kvm_vm':
            params = { 'query': environ+'.kvm.*' }
            
        headers = { 'Content-Type': 'application/json' }
        uri=uri+"/metrics/expand/?find'"
        retval=""
        try:
            f=requests.get(uri, headers=headers, params=params)
        except Exception as e:
            return False, e
        mydict=json.loads(f.text)
        listan = mydict['results']
        listmetrix = []
        for x in listan:
            listmetrix.append({'value':  x.rsplit('.', 1)[1], 'path': x.split('.')[:-1]})

        ele=""
        path=""
        for val in listmetrix:
            if val['value'] == element:
                ele= val['value']
                for x in val['path']:
                    if path:
                        path = path+"."+x
                    else:
                        path = x
        if ele:
            pass
        else:
            return False, element+": not found"
        return True, path

    @staticmethod 
    def calculate(dictio):
        """receives   dictionary of numbers from class methods and returns the average
        :param dictio: dictionary containing the numbers
        """
        lista = []
        for i in range(0, len(dictio)):
            for l in range (0, len(dictio[i]['datapoints'])):
                if dictio[i]['datapoints'][l][0]:
                    lista.append(dictio[i]['datapoints'][l][0])

        if len(lista) == 0:
            return False, "no data found"            
        return sum(lista) / float(len(lista))