'''
Created on May 11, 2013

@author: darkbk
'''
import os
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from beecell.simple import get_attrib
from beedrones.virt import VirtDomain, VirtDomainError, VirtManagerError
from beedrones.cloudstack.db_client import VmManager, QueryError, TransactionError
from .template import Template
from .iso import Iso
from .volume import Volume

class VirtualMachine(ClskObject):
    """VirtualMachine api wrapper object.
    
    TODO: cloudstack save details in table 'user_vm_details' use this table to 
          change custom configurations 
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        # attributes
        self._obj_type = 'instance'
        self._tag_type = 'UserVm'

    @watch
    def configuration(self):
        """Hypervisor virtual machine configuration 
        
        *Extended function*
        
        :raises ClskError: raise :class:`.base.ClskError`
        :raises NotImplementedError: If class extended mode is not active or 
                                     hypervisor is not already supported.
        """
        if self.is_extended() is False:
            raise NotImplementedError()
        
        if self.state != 'Running':
            raise ClskError('Virtual machine is not running.')
        
        # get hypervisor name
        hostname = self.hostname
        # get instance internal name
        vm_internal_name = self.instancename
        # get vm hypervisor
        hypervisor_type = self.hypervisor
        
        # KVM hypervisor
        if hypervisor_type == 'KVM':
            try:
                # get connection to qemu server
                virt_server = self.get_hypervisor(hostname).get_conn()
                # create instance of VirtDomain
                virt_domain = VirtDomain(virt_server, name=vm_internal_name)
                # get domain info
                info = virt_domain.info()
                # release libvirt connection
                virt_server.disconnect()
                del virt_server
                del virt_domain                
                return info
            except (VirtManagerError, VirtDomainError) as ex:
                self.logger.error('Error reading libvirt domain configuration')
                raise ClskError(ex)
        # other hypervisor
        else:
            raise NotImplementedError()
        
        self.logger.info('Get configuration for instance : %s' % self.id)

    @watch
    def list_volumes(self):
        """List virtual machine volumes.
        """
        # get virtual machine info
        params = {'command':'listVolumes',
                  'listall':'true',
                  'virtualmachineid':self.id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listvolumesresponse']
            if len(res) > 0:
                vols = res['volume']
                volumes = []
                for vol in vols:
                    volumes.append(Volume(self._orchestrator, vol))
                return volumes
            else:
                return []
            
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def get_root_volume(self):
        """Get root volume."""
        vols = self.list_volumes()
        for vol in vols:
            if vol.type == 'ROOT':
                return vol

    @watch
    def attach_volume(self, volumeid):
        """Attaches a disk volume to the virtual machine.
        
        *Async command*
        
        :param str volumeid: the ID of the volume to attach

        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'attachVolume',
                  'id':volumeid,
                  'virtualmachineid':self.id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['attachvolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'attachVolume', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch        
    def detach_volume(self, volumeid):
        """Detaches a disk volume from the virtual machine.
        
        *Async command*
        
        :param str volumeid: the ID of the volume to detach

        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'detachVolume',
                  'id':volumeid}       

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['detachvolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'detachVolume', res))                 
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    def list_nics(self):
        """List virtual machine nics."""
        return self._data['nic']

    @watch
    def start(self, hostid=None):
        """Start virtual machine.
        
        *Async command*
        
        :param str hostid: id of the host where start instance [optional]
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError` 
        """
        if self.state == 'Running':
            raise ClskError('Virtual machine is already running.')         
        
        params = {'command':'startVirtualMachine',
                  'id':self.id}
        
        if hostid:
            params['hostid'] = hostid

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['startvirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'startVirtualMachine', res))                 
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def stop(self, forced=False):
        """Stop virtual machine.
        
        *Async command*
        
        :param boolean forced: Force stop the instance [optional] [default=False] 
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """
        if self.state != 'Running':
            raise ClskError('Virtual machine is not running.')        
        
        # stop virtual machine using hypervisor capabilities
        if self.is_extended():
            # get hypervisor name
            hostname = self.hostname
            # get instance internal name
            vm_internal_name = self.instancename
            # get vm hypervisor
            hypervisor_type = self.hypervisor       
            
            # KVM hypervisor
            if hypervisor_type == 'KVM':
                try:
                    # get connection to qemu server
                    virt_server = self.get_hypervisor(hostname).get_conn()
                    # create instance of VirtDomain
                    virt_domain = VirtDomain(virt_server, name=vm_internal_name)
                    virt_domain.shutdown()
                    # release libvirt connection
                    virt_server.disconnect()
                    del virt_server
                    del virt_domain
                except (VirtManagerError, VirtDomainError) as ex:
                    self.logger.error('Vm %s can not be stopped using libvirt' % self.id)
                
            # other hypervisor
            else:
                pass

        params = {'command':'stopVirtualMachine',
                  'id':self.id,
                  'forced':forced}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['stopvirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'stopVirtualMachine', res))
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def reboot(self):
        """Reboots virtual machine.
        
        *Async command*
        
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """
        if self.state != 'Running':
            raise ClskError('Virtual machine is not running.')        
        
        # reboot virtual machine using hypervisor capabilities
        if self.is_extended():
            # get hypervisor name
            hostname = self.hostname
            # get vm internal name
            vm_internal_name = self.instancename
            # get vm hypervisor
            hypervisor_type = self.hypervisor       
            
            # KVM hypervisor
            if hypervisor_type == 'KVM':
                try:
                    # get connection to qemu server
                    virt_server = self.get_hypervisor(hostname).get_conn()
                    # create instance of VirtDomain
                    virt_domain = VirtDomain(virt_server, name=vm_internal_name)
                    virt_domain.reboot()
                    # release libvirt connection
                    virt_server.disconnect()
                    del virt_server
                    del virt_domain
                except (VirtManagerError, VirtDomainError) as ex:
                    self.logger.error('Vm %s can not be stopped using libvirt' % self.id)     
                
            # other hypervisor
            # - reboot virtual machine using cloudstack
            # TODO replace with custom hypervisor code
            else:
                params = {'command':'rebootVirtualMachine',
                          'id':self.id}
        
                try:
                    response = self.send_request(params)
                    res = json.loads(response)
                    clsk_job_id = res['rebootvirtualmachineresponse']['jobid']
                    return clsk_job_id
                except KeyError as ex:
                    raise ClskError('Error parsing json data: %s' % ex)
                except ApiError as ex:
                    raise ClskError(ex)
            
        # reboot virtual machine using cloudstack
        else:
            params = {'command':'rebootVirtualMachine',
                      'id':self.id}
    
            try:
                response = self.send_request(params)
                res = json.loads(response)
                clsk_job_id = res['rebootvirtualmachineresponse']['jobid']
                self.logger.debug('Start job over %s.%s - %s: %s' % (
                                  self._obj_type, self.name, 
                                  'rebootVirtualMachine', res))
                return clsk_job_id
            except KeyError as ex:
                raise ClskError('Error parsing json data: %s' % ex)
            except ApiError as ex:
                raise ClskError(ex)

    @watch
    def destroy(self):
        """Destroy virtual machine.
        
        *Async command*
        
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """
        # stop virtual machine using hypervisor capabilities
        if self.is_extended() and self.state == 'Running':
            # get hypervisor name
            hostname = self.hostname
            # get instance internal name
            vm_internal_name = self.instancename
            # get instance hypervisor
            hypervisor_type = self.hypervisor       
            
            # KVM hypervisor
            if hypervisor_type == 'KVM':
                try:
                    # get connection to qemu server
                    virt_server = self.get_hypervisor(hostname).get_conn()
                    # create instance of VirtDomain
                    virt_domain = VirtDomain(virt_server, name=vm_internal_name)
                    virt_domain.shutdown()
                    # release libvirt connection
                    virt_server.disconnect()
                    del virt_server
                    del virt_domain
                except (VirtManagerError, VirtDomainError) as ex:
                    self.logger.error('Vm %s can not be stopped using libvirt' % self.id)
                
            # other hypervisor
            else:
                pass     
        
        params = {'command':'destroyVirtualMachine',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['destroyvirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'destroyVirtualMachine', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)  

    @watch
    def expunge(self):
        """Expunge a virtual machine. Once expunged, it cannot be recoverd.
        
        *Async command*
        
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """       
        params = {'command':'expungeVirtualMachine',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['expungevirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'expungeVirtualMachine', res))               
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex) 

    @watch
    def restore(self, templateid=None):
        """Restore a instance to original template/ISO or new template/ISO.
        
        *Async command*

        :param templateid: an optional template Id to restore instance from the new 
                           template. This can be an ISO id in case of restore 
                           instance deployed using ISO.
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """       
        params = {'command':'restoreVirtualMachine',
                  'virtualmachineid':self.id}
        
        if templateid:
            params['templateid'] = templateid

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['restorevirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'restoreVirtualMachine', res))                     
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def migrate(self, hostid=None, storageid=None):
        """Migrate virtual machine.
        
        *Async command*
        
        :param str hostid: Cloudstack host id
        :param str storageid: Cloudstack storage id
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'migrateVirtualMachine',
                  'virtualmachineid':self.id}
        if hostid:
            params['hostid'] = hostid
        elif storageid:
            params['storageid'] = storageid            

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['migratevirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'migrateVirtualMachine', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def assign(self, account, domainid, networkids):
        """Change ownership of a instance from one account to another. A root 
        administrator can reassign a instance from any account to any other account 
        in any domain. A domain administrator can reassign a instance to any account 
        in the same domain. instance must be stopped.
        
        :param str account: account name of the new instance owner.
        :param str domainid: domain id of the new instance owner.
        :param str networkids: list of new network ids in which the moved instance 
                               will participate.
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'assignVirtualMachine',
                  'virtualmachineid':self.id,
                  'account':account,
                  'domainid':domainid,
                  'networkids':networkids}       

        try:
            response = self.send_request(params)
            res = json.loads(response)
            self._data = res['assignvirtualmachineresponse']['virtualmachine']
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def update(self, displayname):
        """Updates properties of a virtual machine. The instance has to be stopped 
        and restarted for the new properties to take effect. 
        UpdateVirtualMachine does not first check whether the instance is stopped. 
        Therefore, stop the instance manually before issuing this call.
        
        TODO: manage device introduced using details
        
        :param str displayname: user generated name
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateVirtualMachine',
                  'id':self.id,
                  'displayname':displayname}       

        try:
            response = self.send_request(params)
            res = json.loads(response)
            self._data = res['updatevirtualmachineresponse']['virtualmachine']
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def attach_iso(self, iso_id):
        """Attaches an ISO to a virtual machine.
        
        *Async command*
        
        :param str iso_id: the ID of the ISO file
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'attachIso',
                  'id':iso_id,
                  'virtualmachineid':self.id}       

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['attachisoresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'attachIso', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def detach_iso(self, iso_id):
        """Detaches any ISO file (if any) currently attached to a virtual machine.
        
        *Async command*

        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'detachIso',
                  'id':iso_id,
                  'virtualmachineid':self.id}       

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['detachisoresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'detachIso', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    '''
    @watch
    def get_ext_devices(self):
        """"Get additional devices not supported by cloudstack using
        low level api like libvirt or vpshere api.
    
        *Extended function*
            
        :return: Dictionary with extra devices
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        :raises NotImplementedError: If class extended mode is not active or 
                                     hypervisor is not already supported.  
        """
        if self.is_extended() is False:
            raise NotImplementedError()
        
        if self.state != 'Running':
            raise ClskError('Virtual machine is not running.')
        
        # get instance hypervisor
        hypervisor_type = self._data['hypervisor']       
        
        # Kinstance hypervisor
        if hypervisor_type == 'KVM':
            # save virtual machine devices configuration on db
            try:
                # get db session
                db_session = self._db_server()
                
                # get virtual machine db manager devices
                manager = VmManager(db_session)
                devices = manager.get_virt_domain(self.id)['devices']
                
                # close db session
                db_session.close()
                
                return devices
            except (QueryError, TransactionError) as ex:
                self.logger.error('Error adding libvirt domain extended configuration to db')
                raise ClskError(ex)            
            
        # other hypervisor
        else:
            raise NotImplementedError()
        
        self.logger.info('Get extra devices for vm : %s' % self.id)

    @watch
    def append_ext_devices(self, devices):
        """"Append additional devices not supported by cloudstack using
        low level api like libvirt or vpshere api.
        
        *Extended function*
        
        :param devices: litst with additional devices : 
                            spice_graphics, vlc_graphics, 
                            video_cirrus, video_qxl,
                            virtio_serial, usb_redirect, sound_card,
        :raises ClskError: raise :class:`.base.ClskError`
        :raises NotImplementedError: If class extended mode is not active or 
                                     hypervisor is not already supported.  
        """
        if self.is_extended() is False:
            raise NotImplementedError()
        
        if self.state != 'Running':
            raise ClskError('Virtual machine is not running.')
        
        # get hypervisor name
        hostname = self._data['hostname']
        # get vm internal name
        vm_internal_name = self._data['instancename']
        # get vm hypervisor
        hypervisor_type = self._data['hypervisor']       
        
        # KVM hypervisor
        if hypervisor_type == 'KVM':
            try:
                # get connection to qemu server
                virt_server = self._hypervisors[hostname].get_conn()
                # create instance of VirtDomain
                virt_domain = VirtDomain(virt_server, name=vm_internal_name)
                # append extra devices
                virt_domain.append_device(devices.keys())
                # release libvirt connection
                virt_server.disconnect()
                del virt_server
                del virt_domain
            except (VirtDomainError) as ex:
                self.logger.error('Devices are not appended to vm %s' % self.id)
                raise ClskError(ex)
            
            # save virtual machine devices configuration on db
            try:
                db_session = self._db_server()
                manager = VmManager(db_session)
                # add new virtual machine reference into db and append device 
                try:
                    manager.add_virt_domain(self.id, devices)
                except TransactionError:
                    manager.append_virt_domain_devices(self.id, devices)
                
                #if not manager.get_virt_domain(self.id):
                    
            except (QueryError, TransactionError) as ex:
                self.logger.error('Vm %s devices configuration is not stored on db' % self.id)
                raise ClskError(ex)            
            
        # other hypervisor
        else:
            raise NotImplementedError()
        
        self.logger.info('Append device to vm : %s' % self.id)

    @watch
    def remove_ext_devices(self):
        """"Remove additional devices not supported by cloudstack using
        low level api like libvirt or vpshere api.
        
        *Extended function*
        
        :raises ClskError: raise :class:`.base.ClskError`
        :raises NotImplementedError: If class extended mode is not active or 
                                     hypervisor is not already supported.  
        """
        if self.is_extended() is False:
            raise NotImplementedError()
        
        if self.state != 'Stopped':
            raise ClskError('Virtual machine is not stopped. Stop before remove devices')
        
        # get hypervisor name
        hostname = self._data['hostname']
        # get vm internal name
        vm_internal_name = self._data['instancename']
        # get vm hypervisor
        hypervisor_type = self._data['hypervisor']       
        
        # KVM hypervisor
        if hypervisor_type == 'KVM':
            try:
                db_session = self._db_server()
                manager = VmManager(db_session)
                # remove virtual machine device from db
                manager.delete_virt_domain_devices(self.id)    
            except (QueryError, TransactionError) as ex:
                self.logger.error('Vm %s devices configuration is not stored on db' % self.id)
                raise ClskError(ex)            
            
        # other hypervisor
        else:
            raise NotImplementedError()
        
        self.logger.info('Remove device from vm : %s' % self.id)
    '''

    @watch
    def change_password(self):
        """Resets the password for virtual machine. The virtual machine must be 
        in a "Stopped" state and the template must already support this feature 
        for this command to take effect.
        
        *Async command*
        
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError` 
        """
        params = {'command':'resetPasswordForVirtualMachine',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['resetpasswordforvirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'resetPasswordForVirtualMachine', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def change_graphics_password(self, password):
        """"Change graphics password for virtual machine.
        
        *Extended function*
        
        :param devices: litst with additional devices : 
                            spice_graphics, vlc_graphics, 
                            video_cirrus, video_qxl,
                            virtio_serial, usb_redirect, sound_card,
        :raises ClskError: raise :class:`.base.ClskError`
        :raises NotImplementedError: If class extended mode is not active or 
                                     hypervisor is not already supported.        
        """
        if self.is_extended() is False:
            raise NotImplementedError()
        
        if self.state != 'Running':
            raise ClskError('Virtual machine is not running.')
        
        # get hypervisor name
        hostname = self.hostname
        # get instance internal name
        vm_internal_name = self.instancename
        # get instance hypervisor
        hypervisor_type = self.hypervisor
        
        # KVM hypervisor
        if hypervisor_type == 'KVM':
            try:
                # get connection to qemu server
                virt_server = self.get_hypervisor(hostname).get_conn()
                # create instance of VirtDomain
                virt_domain = VirtDomain(virt_server, name=vm_internal_name)
                # change graphics password
                virt_domain.change_graphics_password(password)
                # release libvirt connection
                virt_server.disconnect()
                del virt_server
                del virt_domain
            except (VirtDomainError) as ex:
                self.logger.error('Devices are not appended to instance %s' % self.id)
                raise ClskError(ex)
            
            '''
            # save virtual machine devices configuration on db
            try:
                db_session = self._db_server()
                manager = VmManager(db_session)
                # add new virtual machine reference into db and append device 
                try:
                    manager.add_virt_domain(self.id, devices)
                except TransactionError:
                    manager.append_virt_domain_devices(self.id, devices)
                
                #if not manager.get_virt_domain(self.id):
                    
            except (QueryError, TransactionError) as ex:
                self.logger.error('Vm %s devices configuration is not stored on db' % self.id)
                raise ClskError(ex)            
            '''
        # other hypervisor
        else:
            raise NotImplementedError()
        
        self.logger.info('Change password to instance : %s' % self.id)

    @watch
    def get_graphic_connection(self, graphic_type):
        """"Get graphics connection params for virtual machine.
        
        *Extended function*
        
        :param graphic_type: spice or vnc
        :return: Virtual Machine password
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`  
        """
        if self.is_extended() is False:
            raise NotImplementedError()
        
        if self.state != 'Running':
            raise ClskError('Virtual machine %s is not running.' % self.name)
        
        # get hypervisor name
        hostname = self.hostname
        # get instance internal name
        vm_internal_name = self.instancename
        # get vm hypervisor
        hypervisor_type = self.hypervisor
        
        # KVM hypervisor
        if hypervisor_type == 'KVM':
            try:
                conn = None
            
                # get connection to qemu server
                virt_server = self.get_hypervisor(hostname).get_conn()            
                # create instance of VirtDomain
                virt_domain = VirtDomain(virt_server, name=vm_internal_name)
                # get graphics password
                deep_data = virt_domain.info()
                
                # get graphic password
                try:
                    # get graphic data
                    graphics = deep_data['devices']['graphics']
                    if type(graphics) is not list:
                        graphics = [graphics]
                    
                    for graphic in graphics:
                        print graphic['type'], graphic_type
                        if graphic['type'] == graphic_type:
                            conn = graphic
                            break
                except Exception as ex:
                    self.logger.error(ex)
                    raise ClskError(ex)
                
                if conn is None:
                    raise ClskError('%s connection is not provided for instance %s' % (
                                    graphic_type, self.name))
                
                # release libvirt connection
                virt_server.disconnect()
                del virt_server
                del virt_domain
                
                return conn
            except (VirtDomainError) as ex:
                self.logger.error('No graphics device defined for instance %s' % self.name)
                raise ClskError(ex)
            
        # other hypervisor
        else:
            raise ClskError('Hypervisor %s is not supported' % hypervisor_type)
        
        self.logger.info('Change password to instance : %s' % self.name)

    @watch
    def get_graphic_connection_status(self, graphic_type):
        """"Get graphics connection status for virtual machine.
        
        *Extended function*
        
        :param graphic_type: spice or vnc
        :return: Virtual Machine password
        :rtype: str        
        :raises ClskError: raise :class:`.base.ClskError`  
        """
        if self.is_extended() is False:
            raise NotImplementedError()
        
        if self.state != 'Running':
            raise ClskError('Virtual machine %s is not running.' % self.name)
        
        # get hypervisor name
        hostname = self.hostname
        # get instance internal name
        vm_internal_name = self.instancename
        # get instance hypervisor
        hypervisor_type = self.hypervisor
        
        # KVM hypervisor
        if hypervisor_type == 'KVM':
            try:
                conn = None
                
                # get connection to qemu server
                virt_server = self.get_hypervisor(hostname).get_conn()
                # create instance of VirtDomain
                virt_domain = VirtDomain(virt_server, name=vm_internal_name)
                # get graphics password
                #deep_data = virt_domain.info()
                
                # get graphic status
                if graphic_type == 'spice':
                    res = virt_domain.spice_connection_status()
                elif graphic_type == 'vnc':
                    res = virt_domain.vnc_connection_status()                    
                else:
                    raise VirtDomainError("%s connection status is not supported" % 
                                          graphic_type)
                
                # release libvirt connection
                virt_server.disconnect()
                del virt_server
                del virt_domain
                
                return res
            except (VirtDomainError) as ex:
                self.logger.error(ex)
                raise ClskError(ex)
            
        # other hypervisor
        else:
            raise ClskError('Hypervisor %s is not supported' % hypervisor_type)
        
        self.logger.info('Get %s graphic connection status for instance : %s' % (
                            graphic_type, self.name))

    @watch
    def create_vv_file(self, graphic_type, directory='/tmp', hostname=None, port=None):
        """Create vv file that can be used to connect virtual machine using
        virt-viewer.
        
        :param graphic_type: spice or vnc
        
        The current list of [virt-viewer] keys is:
        - version: string
        - type: string, mandatory, values: "spice" (later "vnc" etc..)
        - host: string
        - port: int
        - tls-port: int
        - username: string
        - password: string
        - disable-channels: string list
        - tls-ciphers: string
        - ca: string PEM data (use \n to seperate the lines)
        - host-subject: string
        - fullscreen: int (0 or 1 atm)
        - title: string
        - toggle-fullscreen: string in spice hotkey format
        - release-cursor: string in spice hotkey format
        - smartcard-insert: string in spice hotkey format
        - smartcard-remove: string in spice hotkey format
        - secure-attention: string in spice hotkey format
        - enable-smartcard: int (0 or 1 atm)
        - enable-usbredir: int (0 or 1 atm)
        - color-depth: int
        - disable-effects: string list
        - enable-usb-autoshare: int
        - usb-filter: string
        - secure-channels: string list
        - delete-this-file: int (0 or 1 atm)
        - proxy: proxy URL, like http://user:pass@foobar:8080
        
        :param directory: server directory where vv file is created [defult=/tmp]
        :raises ClskError: raise :class:`.base.ClskError`
        """
        # hypervisor KVM
        if self.state == 'Running':
            name = self.name
            # get hypervisor name
            if hostname is None:
                hostname = self.hostname      
            # get instance hypervisor
            hypervisor_type = self.hypervisor
            deep_data = self.configuration()     
            
            # KVM hypervisor
            if hypervisor_type == 'KVM':
                # get connection info from proxy
                graphics = deep_data['devices']['graphics']
                if type(graphics) is not list:
                    graphics = [graphics]

                conn = None
                for graphic in graphics:
                    if graphic['type'] == graphic_type:
                        conn = graphic
                        break
                
                if conn is None:
                    raise ClskError('%s connection is not provided for instance %s' % (
                                        graphic_type, name))
                print conn
                try:
                    passwd = conn['passwd']
                except:
                    passwd = ""
                    self.logger.warning("No password defined for graphic device of instance: %s" % name)

                if port is None:
                    port = conn['port']

                # create remote-viewer connection file
                filedata = ['[virt-viewer]',
                            'type=%s' % conn['type'],
                            'title=%s' % name,
                            'host=%s' % hostname,
                            'port=%s' % port,
                            'password=%s' % passwd,
                            'enable-smartcard=1',
                            'disable-effects=font-smooth,animation',
                            'cache-size=10000000',
                            'enable-usbredir=1',
                            'delete-this-file=1']
                
                filename = "%s.vv" % name
                filepath = "%s/%s" % (directory, filename)
                
                spice_file = open(filepath, "w")
                spice_file.write('\n'.join(filedata))
                spice_file.close()
                
                self.logger.debug("Create vv file for instance: %s" % name)
            else:
                raise ClskError('Hypervisor %s is not supported' % hypervisor_type)
            
            return True

    @watch
    def remove_vv_file(self, directory='/tmp'):
        """Remove vv file.
        
        :param name: name of the virtual machine associated to vv file
        """
        filename = "%s.vv" % self.name
        filepath = "%s/%s" % (directory, filename)
        
        if os.path.exists(filepath) == True:
            os.remove(filepath)

    @watch
    def create_template(self, name, displaytext, ostypeid=None):
        """Create a template from the ROOT disk of the virtual machine.
        Virtual machine must be stopped. 
        
        *Async command*
        
        :param str iso_id: the ID of the ISO file
        :raises ClskError: raise :class:`.base.ClskError`
        """
        if self.state == 'Running':
            raise ClskError('Virtual machine is already running.')        
        
        # get template info
        if ostypeid is None and 'templateid' in self._data:
            try:
                template = Template(self._api_client, oid=self._data['templateid'])
                ostypeid = template.get_os_type()[0]
            except:
                template = Iso(self._api_client, oid=self._data['templateid'])
                ostypeid = template.get_os_type()[0]
                            
            
        #print self.get_root_volume().id
        #print ostypeid
        params = {'command':'createTemplate',
                  'displaytext':displaytext,
                  'name':name,
                  'ostypeid':ostypeid,
                  'ispublic':True,
                  'volumeid':self.get_root_volume().id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['createtemplateresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'createTemplate', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    # snapshot / backup TODO   

    @watch        
    def create_snapshot(self, name):
        """TODO"""
        raise NotImplementedError()
    
    @watch    
    def revert_to_snapshot(self, name):
        """TODO"""
        raise NotImplementedError()

    @watch    
    def delete_snapshot(self, name):
        """TODO"""
        raise NotImplementedError()