'''
Created on Jul 29, 2013

@author: darkbk
'''
from .models import Volumes
from .models import VmInstances

class QueryManager(object):
    """ """
    def __init__(self, session):
        """ """
        self.session = session

    def get_vm_and_volume_info(self):
        """ """
        fields = ["VM name", 
            "zone", 
            "pod", 
            "host", 
            "hyper", 
            "state", 
            "vol name", 
            "vol folder", 
            "vol path"]
        data = []
        for vol, vm in self.session.query(Volumes, VmInstances).\
                            filter(Volumes.instance_id==VmInstances.id).\
                            filter(VmInstances.state!='Expunging').\
                            order_by(VmInstances.data_center_id,
                                     VmInstances.pod_id,
                                     VmInstances.host_id,).\
                            all():    
            data.append([vm.name, 
                        vm.data_center_id, 
                        vm.pod_id, 
                        vm.host_id, 
                        vm.hypervisor_type, 
                        vm.state, 
                        vol.name, 
                        vol.folder, 
                        vol.path])
        return {'fields':fields, 'data':data}