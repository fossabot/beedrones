'''
Created on May 11, 2013

@author: darkbk
'''
import json
from .model.vm import VmModelManager
from .model.decorator import TransactionError, QueryError
from .volume import VolumeExt
from gibboncloud.cloudstack.dso import ApiError
from gibboncloud.cloudstack.dso import VirtualRouter, VirtualMachineType
from gibboncloud.cloudstack.dso.base import ClskObjectError
from gibboncloud.cloudstack.dso_ext.base import ApiManagerError
from gibboncloud.virt.domain import VirtDomain, VirtDomainError
from gibbonutil.simple import get_attrib

class VirtualRouterExt(VirtualRouter):
    ''' '''
    
    def __init__(self, clsk_instance, data=None, oid=None):
        """
        """
        self.clsk_instance = clsk_instance
        self.db_manager = VmModelManager(self.clsk_instance.db_manager)
        
        api_client = clsk_instance.get_api_client()
        VirtualRouter.__init__(self, api_client, data=data, oid=oid)