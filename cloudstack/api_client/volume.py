'''
Created on May 10, 2013

@author: darkbk
'''
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch

class Volume(ClskObject):
    """Volume api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'volume'
    
    @watch
    def attach(self, virtualmachineid):
        """Attaches the disk volume to a virtual machine.
        
        *Async command*
        
        :param str virtualmachineid: the ID of the virtual machine

        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'attachVolume',
                  'id':self.id,
                  'virtualmachineid':virtualmachineid}       

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
    def detach(self, virtualmachineid):
        """Detaches the disk volume from a virtual machine.
        
        *Async command*
        
        :param str virtualmachineid: the ID of the virtual machine

        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'detachVolume',
                  'id':self.id}       

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['detachvolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self._data['name'], 
                              'detachVolume', res))              
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
    
    @watch
    def delete(self):
        '''Deletes the disk volume.
        
        :raises ClskError: raise :class:`.base.ClskError`        
        '''
        params = {'command':'deleteVolume',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['deletevolumeresponse']
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
        
        if not res['success']:
            raise ClskError(res['displaytext'])
        
        self.logger.debug('Delete volume %s' % self.name)
        return True

    @watch
    def extract(self):
        """Extracts the disk volume.
        
        *Async command*
        
        :param str virtualmachineid: the ID of the virtual machine

        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'extractVolume',
                  'id':self.id,
                  'mode':'HTTP_DOWNLOAD',
                  'zoneid':self._data['zoneid']}       

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['extractvolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'extractVolume', res))              
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
    @watch
    def migrate(self, storageid):
        """Migrate the disk volume.
        
        *Async command*
        
        :param str virtualmachineid: the ID of the virtual machine

        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'migrateVolume',
                  'volumeid':self.id,
                  'livemigrate':True}       

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['migratevolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'migrateVolume', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
    @watch
    def resize(self, diskofferingid, size=None):
        """Resizes the disk volume.
        
        *Async command*
        
        :param diskofferingid: new disk offering id
        :param size: New volume size in G [optional]

        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'resizeVolume',
                  'id':self.id,
                  'shrinkok':True,
                  'diskofferingid':diskofferingid}
        
        if size:
            params['size'] = size 

        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['resizevolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'resizeVolume', res))             
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)