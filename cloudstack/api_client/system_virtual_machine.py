'''
Created on May 21, 2014

@author: darkbk
'''
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch

class SystemVirtualMachine(ClskObject):
    """SystemVirtualMachine api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        # attributes
        self._type = None 
        self._obj_type = 'sysvm'
        self._domain_id = None

    @watch
    def start(self, job_id):
        """Start system virtual machine. 
        
        *Async command*
        
        """
        params = {'command':'startSystemVm',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['startsystemvmresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def stop(self, job_id):
        """Stop system virtual machine.
        
        *Async command*
        
        """        
        params = {'command':'stopSystemVm',
                  'id':self.id,
                  'forced':True}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['stopsystemvmresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def destroy(self, job_id):
        """Destroy system virtual machine.
        
        *Async command*
        """        
        params = {'command':'destroySystemVm',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['destroysystemvmresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def migrate(self, job_id, hostid):
        """Migrate system virtual machine.
        
        *Async command*
        """        
        params = {'command':'migrateSystemVm',
                  'virtualmachineid':self.id,
                  'hostid':hostid}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['migratesystemvmresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch        
    def change_service_offering(self, job_id, serviceofferingid):
        """Changes the service offering for a system vm (console proxy or 
        secondary storage). The system vm must be in a "Stopped" state for 
        this command to take effect.
        
        :param str serviceofferingid: the service offering ID to apply to the domain router
        """        
        params = {'command':'changeServiceForSystemVm',
                  'id':self.id,
                  'serviceofferingid':serviceofferingid}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            data = res['changeserviceforsystemvmresponse']['jobid']
            return data
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch        
    def create_vv_file(self, directory='/tmp'):
        """Create vv file that can be used to connect virtual machine using
        virt-viewer.
        
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
        """
        # hypervisor KVM
        if self.state == 'Running':
            name = self._data['name']
            # get hypervisor name
            hostname = self._data['hostname']
            # get vm hypervisor
            hypervisor_type = self._data['hypervisor']
            deep_data = self.deep_info()       
            
            # KVM hypervisor
            if hypervisor_type == 'KVM':
                # get connection info from proxy
                graphic = deep_data['devices']['graphics']
                try:
                    passwd = graphic['passwd']
                except:
                    passwd = ""
                    self.logger.warning("No password defined for graphic device of vm: %s" % name)

                # create remote-viewer connection file
                filedata = ['[virt-viewer]',
                            'type=%s' % graphic['type'],
                            'title=%s' % name,
                            'host=%s' % hostname,
                            'port=%s' % graphic['port'],
                            'password=%s' % passwd,
                            'enable-smartcard=1',
                            #'color-depth=24',
                            #'disable-effects=1',
                            'enable-usbredir=1',
                            'delete-this-file=1']
                
                filename = "%s.vv" % name
                filepath = "%s/%s" % (directory, filename)
                
                spice_file = open(filepath, "w")
                spice_file.write('\n'.join(filedata))
                spice_file.close()
                
                self.logger.debug("Create vv file for vm: %s" % name)
            else:
                raise NotImplementedError()