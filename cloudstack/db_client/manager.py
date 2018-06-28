'''
Created on Apr 18, 2014

@author: darkbk
'''
import logging
from beedrones.cloudstack.db_client import transaction, query
from beedrones.cloudstack.db_client import Base

class ClskManagerError(Exception): pass

class ClskManager(object):
    """
    """
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, session):
        """ """
        self._session = session
    
    def populate_table(self):
        @transaction(self._conn_manager)
        def func(session):
            data = [VirtDomainDeviceType(device='spice_graphics'),
                    VirtDomainDeviceType(device='vnc_graphics'),
                    VirtDomainDeviceType(device='rdp_graphics'),
                    VirtDomainDeviceType(device='video_cirrus'),
                    VirtDomainDeviceType(device='video_qxl'),
                    VirtDomainDeviceType(device='virtio_serial'),
                    VirtDomainDeviceType(device='usb_redirect'),
                    VirtDomainDeviceType(device='sound_card_ac97'),
                    VirtDomainDeviceType(device='sound_card_es1370'),
                    VirtDomainDeviceType(device='sound_card_sb16'),
                    VirtDomainDeviceType(device='sound_card_ich6'),]
            
            session.add_all(data)
            session.commit()
        return func()
    
    """Query method """
    def get_clusters(self):
        """
        Use this function to get cluster list with additional information like
        VMware vCenter password.
        """
        @query(self._session)
        def func(session):
            """
            java -classpath /usr/share/cloudstack-common/lib/jasypt-1.9.0.jar org.jasypt.intf.cli.JasyptPBEStringDecryptionCLI decrypt.sh input="Y3ZfBKd1/0b8Vu9hjDwCIldiJpULLG5v" password="$(cat /etc/cloud/management/key)" verbose=false
            /usr/share/cloudstack-common/lib/

            
            SELECT t1.id, t1.name, t1.uuid, t1.private_ip_address, t1.cluster_id, t1.pod_id, t1.hypervisor_type, t1.hypervisor_version  FROM cloud.host as t1
WHERE status='Up' and type='Routing';
            """
            # get clusters
            sql = ["SELECT * FROM cloud.cluster as t1 WHERE t1.removed is Null"]            
            query = session.query("id", "name", "pod_id", "data_center_id", "hypervisor_type").\
                    from_statement(" ".join(sql)).\
                    params().all()
            
            clusters = []
            for item in query:
                cluster_id = item[0]
                hypervisor = item[4]
                cluster = {'id':cluster_id,
                           'name':item[1],
                           'pod':item[2],
                           'zone':item[3],
                           'hypervisor':hypervisor}
                if hypervisor == 'VMware':
                    # get VMware clusters params
                    sql = ["SELECT * FROM cloud.cluster_details WHERE cluster_id=:cluster_id"]            
                    query2 = session.query("id", "cluster_id", "name", "value").\
                             from_statement(" ".join(sql)).\
                             params(cluster_id=cluster_id).all()
                    # append username and password
                    for item in query2:
                        if query2['name'] == 'username':
                            cluster['username'] = query2['value']
                        elif query2['name'] == 'password':
                            cluster['password'] = query2['value']
                
                clusters.append(cluster)

            return clusters
        return func()
    
    def get_vm(self, vm_id):
        @query(self._conn_manager)
        def func(session):
            vm = session.query(VirtDomain).filter_by(vm_id=vm_id)
            if vm.count() > 0:
                devs = {}
                for device in vm.first().device:
                    devs[device.type.device] = device.config
                data = {'id':vm_id, 'devices':devs}
            else:
                data = None
            
            self.logger.debug('Get virt domain info from db: %s' % vm_id)
            return data
        return func()

    """Add method """
    def add_vm(self, vm_id, devices):
        """
        :param vm_id: cloudstack id of the virtual machine
        :param devices: dict of libvirt devices to set. Es. {'spice':'password:testlab,'}
        """
        @transaction(self._conn_manager)
        def func(session):
            virt_devices = []
            for device, config in devices.iteritems():
                type = session.query(VirtDomainDeviceType).filter_by(device=device).first()
                virt_devices.append(VirtDomainDevice(type, config))
            data = VirtDomain(vm_id, virt_devices)
            session.add(data)
            
            self.logger.debug('Add virt domain to db: %s' % vm_id)
        return func()

    """Update method """
    def update_graphic_password(self, vm_id, password):
        @transaction(self._conn_manager)
        def func(session):
            #vm = session.query(VirtDomain).filter_by(vm_id=vm_id)
            dev = session.query(VirtDomain, VirtDomainDevice, VirtDomainDeviceType).\
                filter(VirtDomain.id==VirtDomainDevice.vm_id).\
                filter(VirtDomainDeviceType.id==VirtDomainDevice.type_id).\
                filter(VirtDomainDeviceType.device.like('%_graphics'))
            
            if dev.count() > 0:
                dev = dev.first()
                dev[1].config = 'password:%s' % password
                return True
            else:
                return False
            
            self.logger.debug('Update virt domain graphic password to db: %s' % vm_id)
        return func()        

    """Delete method """
    def delete_vm(self, vm_id):
        """
        :param items: list of action like 'add', '*'
        """
        @transaction(self._conn_manager)
        def func(session):
            vm = session.query(VirtDomain).filter_by(vm_id=vm_id)
            if vm.count() > 0:
                for device in vm.first().device:
                    session.delete(device)            
                session.delete(vm.first())
                
            self.logger.debug('Delte virt domain from db: %s' % vm_id)
        return func()