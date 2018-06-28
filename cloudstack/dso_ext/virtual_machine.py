'''
Created on May 11, 2013

@author: darkbk
'''
import json
from .model.vm import VmModelManager
from .model.decorator import TransactionError, QueryError
from .volume import VolumeExt
from gibboncloud.cloudstack.dso import ApiError
from gibboncloud.cloudstack.dso import VirtualMachine, VirtualMachineType
from gibboncloud.cloudstack.dso.base import ClskObjectError
from gibboncloud.cloudstack.dso_ext.base import ApiManagerError
from gibboncloud.virt.domain import VirtDomain, VirtDomainError
from gibbonutil.simple import get_attrib

class VirtualMachineExt(VirtualMachine):
    ''' '''
    
    def __init__(self, clsk_instance, data=None, oid=None):
        """
        """
        self.clsk_instance = clsk_instance
        self.db_manager = VmModelManager(self.clsk_instance.db_manager)
        
        api_client = clsk_instance.get_api_client()
        VirtualMachine.__init__(self, api_client, data=data, oid=oid)
        
        ''' Additional device.
        Qemu supported device : spice_graphics, vlc_graphics, rdp_graphics,
                                video_cirrus, video_qxl, 
                                virtio_serial, usb_redirect, 
                                sound_card_ac97, sound_card_es1370, 
                                sound_card_sb16, sound_card_ich6
        '''
        self._devices = []
    
    def config(self):
        """Describe virtual machine configuration."""
        self.logger.info('Get configuration for vm : %s' % self._id)
 
        info = self.info(cache=True)
        if self.get_state()  != 'Running':
            raise ClskObjectError('Virtual machine is not running.')
        
        # get hypervisor name
        hostname = info['hostname']
        # get vm internal name
        vm_internal_name = info['instancename']
        # get vm hypervisor
        hypervisor = info['hypervisor']
        
        # KVM hypervisor
        if hypervisor == 'KVM':
            try:
                # get connection to qemu server
                qemu_conn = self.clsk_instance.get_hypervisor_conn('qemu', 
                                                                   hostname)
                # create instance of VirtDomain
                virt_domain = VirtDomain(qemu_conn, name=vm_internal_name)
                # get domain info
                info = virt_domain.info()
                # delete vm manager instance
                del virt_domain
                # release libvirt connection
                self.clsk_instance.release_hypervisor_conn('qemu', 
                                                           hostname, 
                                                           qemu_conn)
                
                return info
            except (ApiManagerError, VirtDomainError) as ex:
                self.logger.error('Error reading libvirt domain configuration')
                raise ClskObjectError(ex)
        # other hypervisor
        else:
            return None
        
    def list_volume(self):
        """List virtual machine volume.
        TODO: extend to other hypervisor
        """
        # get qemu disk info
        #disks = self.config()['devices']['disk']

        # get cloudstack volume info
        params = {'command':'listVolumes',
                  'listall':'true',
                  'virtualmachineid':self._id}
        
        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listvolumesresponse']
            if len(res) > 0:
                vols = res['volume']
                volumes = []
                for vol in vols:
                    # create VolumeExt object
                    volume_obj = VolumeExt(self.clsk_instance, data=vol)                    
                    
                    # get volume type
                    vol_type = vol['type']
                                        
                    # create base
                    volume = {'id':vol['id'],
                              'name':vol['name'],
                              'offering':get_attrib(vol, 'diskofferingdisplaytext', ''),
                              'size':vol['size'],
                              'storage':vol['storage'],
                              'type':vol_type,
                              'deviceid':vol['deviceid'],
                              'attached':get_attrib(vol, 'attached', '')}
                    
                    """
                    # set extended info to ROOT volume
                    if self._data['hypervisor'] == 'KVM' and vol_type == 'ROOT':
                        volume['source'] = {}
                        
                        # get storage pool connection info
                        pool_info = volume_obj.get_storagepool_info()
                        volume['source']['type'] = pool_info['type']
                        volume['source']['path'] = pool_info['path']
                        volume['source']['ipaddress'] = pool_info['ipaddress']
                        
                        # find qemu root disk
                        for disk in disks:
                            if (disk['alias']['name'] == 'ide0-0-0' and
                                disk['target']['dev'] == 'hda' or
                                disk['alias']['name'] == 'virtio-disk0' and
                                disk['target']['dev'] == 'vda'):
                                volume['source']['file'] = disk['source']['file'].split('/')[-1]                   
                    """
                    
                    # append volume
                    volumes.append(volume)
                return volumes
                
            else:
                return []
            
        except KeyError as ex:
            raise ClskObjectError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskObjectError(ex)        
        
    """
    @watch_test
    def volume_tree(self):
        try:
            res = self.vol.get_storagepool_info()
            
            #import guestfs
            #g = guestfs.GuestFS(python_return_dict=True)
            #g.add_drive_opts("/home/vm/disk/win7-1.img", readonly=0)
            #g.launch()
            if res['type'] == 'NetworkFilesystem' and res['state'] == 'Up':
                ipaddress = res['ipaddress']
                path = res['path']
                
                
                print ipaddress, path       
            
            fres = self.pp.pformat(res)
            self.logger.debug(fres)
        except ClskObjectError as ex:
            self.logger.error(traceback.format_exc())
            self.fail(ex)
    """

    def append_device(self, devices):
        """"Append additionale devices not supported from cloudstack using
        low level api like libvirt or vpshere api.
        
        :param devices: litst with additional devices : 
                            spice_graphics, vlc_graphics, 
                            video_cirrus, video_qxl,
                            virtio_serial, usb_redirect, sound_card,        
        """
        self.logger.info('Append device to vm : %s' % self._id)
        
        info = self.info(cache=True)
        if self.get_state()  != 'Running':
            raise ClskObjectError('Virtual machine is not running.')        
        
        # get hypervisor name
        hostname = info['hostname']
        # get vm internal name
        vm_internal_name = info['instancename']
        # get vm id
        vm_id = info['id']
        # get vm hypervisor
        hypervisor = info['hypervisor']

        # KVM hypervisor
        if hypervisor == 'KVM':
            '''TO-DO : gestire meglio le operazioni: se una delle due fallisce
            l'altra potrebbe andare a termine senza rendersene conto'''
            
            # append device to libvirt domain  
            try:
                # get connection to qemu server
                qemu_conn = self.clsk_instance.get_hypervisor_conn('qemu', 
                                                                   hostname)    
                # create instance of VirtDomain
                virt_domain = VirtDomain(qemu_conn, name=vm_internal_name)
                # append extra devices
                domain2 = virt_domain.append_device(devices.keys())
                # delete vm manager instance
                del virt_domain
                # release libvirt connection
                self.clsk_instance.release_hypervisor_conn('qemu', 
                                                           hostname, 
                                                           qemu_conn)
            except (ApiManagerError, VirtDomainError) as ex:
                self.logger.error('Error appending devices to libvirt domain')
                raise ClskObjectError(ex)
            
            # save virtual machine devices configuration on db
            try:
                # add new virtual machine reference into db and append device 
                # if it doesn't exists
                if not self.db_manager.get_vm(vm_id):
                    self.db_manager.add_vm(vm_id, devices)              
            except (QueryError, TransactionError) as ex:
                self.logger.error('Error saving libvirt domain extended configuration to db')
                raise ClskObjectError(ex)     
                
        # other hypervisor
        else:
            self.logger.debug('Hypervisor %s doesn\'t support append devices' % (
                                hypervisor))

    def change_graphics_password(self, password):
        """"Append additionale devices not supported from cloudstack using
        low level api like libvirt or vpshere api.
        
        :param devices: litst with additional devices : 
                            spice_graphics, vlc_graphics, 
                            video_cirrus, video_qxl,
                            virtio_serial, usb_redirect, sound_card,        
        """
        self.logger.info('Change password to vm : %s' % self._id)
        
        info = self.info(cache=True)
        if self.get_state()  != 'Running':
            raise ClskObjectError('Virtual machine is not running.')        
        
        # get hypervisor name
        hostname = info['hostname']
        # get vm internal name
        vm_internal_name = info['instancename']
        # get vm id
        vm_id = info['id']        
        # get vm hypervisor
        hypervisor = info['hypervisor']

        # KVM hypervisor
        if hypervisor == 'KVM':
            '''TO-DO : gestire meglio le operazioni: se una delle due fallisce
            l'altra potrebbe andare a termine senza rendersene conto'''
            
            # change password of libvirt domain  
            try:
                # get connection to qemu server
                qemu_conn = self.clsk_instance.get_hypervisor_conn('qemu', 
                                                                   hostname)    
                # create instance of VirtDomain
                virt_domain = VirtDomain(qemu_conn, name=vm_internal_name)
                # change graphics password
                virt_domain.change_graphics_password(password)
                # delete vm manager instance
                del virt_domain                
                # release libvirt connection
                self.clsk_instance.release_hypervisor_conn('qemu', 
                                                           hostname, 
                                                           qemu_conn)
            except (ApiManagerError, VirtDomainError) as ex:
                self.logger.error('Error changing libvirt domain password')
                raise ClskObjectError(ex)
            
            # save password on db
            try:
                self.db_manager.update_graphic_password(vm_id, 'test')             
            except (QueryError, TransactionError) as ex:
                self.logger.error('Error saving libvirt domain password to db')
                raise ClskObjectError(ex)                
            
        # other hypervisor
        else:
            self.logger.debug('Hypervisor %s doesn\'t support graphic device change password' % (
                               hypervisor))        

    def start(self, job_id):
        """Start virtual machine. 
        Async command.
        
        TO-DO : read config from extended database
        
        :param job_id: unique id of the async job
        """
        self.logger.info('Start vm : %s' % self._id)
        
        if self.get_state()  == 'Running':
            raise ClskObjectError('Virtual machine is already running.')             
        
        VirtualMachine.start(self, job_id)
        
        # get virtual machine extended device from db if they are configured
        info = self.info(cache=False)
        # get vm id
        vm_id = info['id']        
        
        try:
            vm = self.db_manager.get_vm(vm_id)
            if vm:
                devices = vm['devices']
                self.append_device(devices)
        except (QueryError, TransactionError) as ex:
            raise ClskObjectError(ex)                 

    def stop(self, job_id):
        """Stop virtual machine.
        Async command.
        
        read config from extended database
        
        TO-DO : read config from extended database
        
        :param job_id: unique id of the async job        
        """
        self.logger.info('Stop vm : %s' % self._id)
        
        if self.get_state()  != 'Running':
            raise ClskObjectError('Virtual machine is not running.')        
        
        VirtualMachine.stop(self, job_id)

    def destroy(self, job_id):
        """Destroy virtual machine.
        Async command."""
        self.logger.info('Destroy vm : %s' % self._id)
           
        VirtualMachine.destroy(self, job_id)
        
        # remove virtual machine extended device from db if they are configured
        info = self.info(cache=True)
        # get vm id
        vm_id = info['id']        
        
        try:
            vm = self.db_manager.get_vm(vm_id)
            if vm:
                self.db_manager.delete_vm(vm_id)
        except (QueryError, TransactionError) as ex:
            raise ClskObjectError(ex)      
            
    def update(self, job_id, devices):
        """Update virtual machine. 
        Async command.
        
        TO-DO : read config from extended database
        
        :param job_id: unique id of the async job
        """
        self.logger.info('Update vm : %s' % self._id)
        
        # get virtual machine extended device from db if they are configured
        info = self.info(cache=True)
        # get vm id
        vm_id = info['id']        
        
        try:
            vm = self.db_manager.get_vm(vm_id)
            if vm:
                # remove old config
                self.db_manager.delete_vm(vm_id)
                # append new devices
                self.append_device(devices)
        except (QueryError, TransactionError) as ex:
            raise ClskObjectError(ex)              