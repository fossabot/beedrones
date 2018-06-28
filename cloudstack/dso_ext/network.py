'''
Created on March 3, 2014

@author: darkbk
'''
import json
from .virtual_machine import VirtualMachineExt
from gibboncloud.cloudstack.dso.virtual_machine import VirtualMachine
from gibboncloud.cloudstack.dso import Network
from gibboncloud.cloudstack.dso.base import ClskObjectError, ApiError
from gibboncloud.cloudstack.dso_ext.base import ApiManagerError
from gibboncloud.virt.domain import VirtDomain, VirtDomainError

class NetworkExt(Network):
    ''' '''
    def __init__(self, clsk_instance, data=None, oid=None):
        ''' '''
        self.clsk_instance = clsk_instance
        #self.db_manager = VmModelManager(self.clsk_instance.db_manager)
        
        api_client = clsk_instance.get_api_client()
        Network.__init__(self, api_client, data=data, oid=oid)
        
    def list_all_virtual_machines(self):
        '''List all clusters'''
        vms = self.list_virtual_machines()
        vms.extend(self.list_routers())
        return vms
    
    def list_routers(self):
        '''List all system vms'''
        params = {'command':'listRouters',
                  'networkid':self._id,
                  'domainid':self.info()['domainid']
                 }
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listroutersresponse']
            if len(res) > 0:
                data = res['router']
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachineExt(self.clsk_instance, data=item)
            vms.append(vm)
        return vms         
        
    def list_virtual_machines(self):
        '''List all virtual machines.'''
        params = {'command':'listVirtualMachines',
                  'listall':True,
                  'networkid':self._id,
                 }
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listvirtualmachinesresponse']
            if len(res) > 0:
                data = res['virtualmachine']
            else:
                return []
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskObjectError(ex)
        
        vms = []
        for item in data:
            # create Account instance
            vm = VirtualMachineExt(self.clsk_instance, data=item)
            vms.append(vm)
        return vms        