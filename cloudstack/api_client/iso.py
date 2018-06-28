'''
Created on May 11, 2013

@author: darkbk
'''
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
        
class Iso(ClskObject):
    """Iso api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'iso'
    
    def is_ready(self):
        """Get ready status."""
        return self._data['isready']

    def get_status(self):
        """Get status."""
        return self._data['status']
    
    def get_os_type(self):
        """Get Operating System type
        
        :return: tupla with (ostypeid, ostypename)
        :rtype: str 
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        return (self._data['ostypeid'], self._data['ostypename'])
    
    @watch
    def delete(self):
        """Deletes a iso from the system.
        
        *Async command*

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteIso',
                  'id':self.id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deleteisosresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'deleteIso', res))
            return clsk_job_id
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch       
    def extract(self, mode='HTTP_DOWNLOAD'):
        """Extracts an iso.
        
        *Async command*

        :param mode: the mode of extraction - HTTP_DOWNLOAD [default] or FTP_UPLOAD
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'extractIso',
                  'id':self.id,
                  'mode':mode}
        
        name = self._data['name']
        
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['extractisoresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self._data['name'], 
                              'extractIso', res))
            return clsk_job_id
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex) 

    @watch    
    def update(self, bootable=None, displaytext=None, format=None, 
                     isdynamicallyscalable=None, isrouting=None,
                     name=None, ostypeid=None, passwordenabled=None):
        """Update iso
        
        :param bootable: true if image is bootable, false otherwise
        :param displaytext: the display text of the image
        :param format: the format for the image
        :param isdynamicallyscalable: true if template/ISO contains XS/VMWare 
                                      tools inorder to support dynamic scaling 
                                      of VM cpu/memory
        :param isrouting: true if the template type is routing i.e., if 
                          template is used to deploy router
        :param name: the name of the image file
        :param ostypeid: the ID of the OS type that best represents the OS of 
                         this image.
        :param passwordenabled: true if the image supports the password reset 
                                feature; default is false
        :return: 
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateIso',
                  'id':self.id}
        
        if bootable:
            params['bootable'] = bootable
        if displaytext:
            params['displaytext'] = displaytext
        if format:
            params['format'] = format
        if isdynamicallyscalable:
            params['isdynamicallyscalable'] = isdynamicallyscalable
        if isrouting:
            params['isrouting'] = isrouting    
        if name:
            params['name'] = name
        if ostypeid:
            params['ostypeid'] = ostypeid
        if passwordenabled:
            params['passwordenabled'] = passwordenabled        
        
        try:
            response = self.send_request(params)        
            res = json.loads(response)['updateisoresponse']
            if len(res) > 0:
                self._data = res['iso']
                self.logger.debug('Update iso %s' % self._data['name'])
                return self._data
            else:
                return None
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)