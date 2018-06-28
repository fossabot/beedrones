"""
Created on May 11, 2013

@author: darkbk
"""
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch
from ..db_client import TmplManager, TmplManagerError, QueryError

class Template(ClskObject):
    """Template api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'template'

    def is_ready(self):
        """Get ready status."""
        return self._data['isready']

    def get_status(self):
        """Get status."""
        return self._data['status']

    @watch
    def deep_info(self):
        """Extended info. 
        
        *Extended function*
        
        :raises ClskError: raise :class:`.base.ClskError`
        :raises NotImplementedError: If class extended mode is not active or 
                                     hypervisor is not already supported.
        """
        if not self._extended:
            raise NotImplementedError()
        
        # get info from db
        try:
            # get db session
            db_session = self._db_server()
            
            # get virtual machine db manager devices
            manager = TmplManager(db_session)
            template = manager.get_template(self.id)
            
            # close db session
            db_session.close()
            
            return template
        except (QueryError, TmplManagerError) as ex:
            self.logger.error('Error reading configuration from db')
            raise ClskError(ex)
        
        self.logger.info('Get configuration for vm : %s' % self.id)
        
    def get_os_type(self):
        """Get Operating System type
        
        :return: tupla with (ostypeid, ostypename)
        :rtype: str 
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        return (self._data['ostypeid'], self._data['ostypename'])
    
    @watch    
    def delete(self):
        """Deletes a template from the system. All virtual machines using the 
        deleted template will not be affected.
        
        *Async command*

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'deleteTemplate',
                  'id':self.id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deletetemplateresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.name, 
                              'deleteTemplate', res))
            return clsk_job_id
        except KeyError as ex :
            self.logger.error('Error parsing json data: %s' % ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def extract(self, mode='HTTP_DOWNLOAD'):
        """Extracts a template.
        
        *Async command*

        :param mode: the mode of extraction - HTTP_DOWNLOAD [default] or FTP_UPLOAD
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """        
        params = {'command':'extractTemplate',
                  'id':self.id,
                  'mode':mode}
        
        name = self._data['name']
        
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['extracttemplateresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self._data['name'], 
                              'extractTemplate', res))
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
        """Update template
        
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
        params = {'command':'updateTemplate',
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
            res = json.loads(response)['updatetemplateresponse']
            if len(res) > 0:
                self._data = res['template']
                self.logger.debug('Update template %s' % self._data['name'])
                return self._data
            else:
                return None
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def load_in_primary_storage(self, zoneid):
        """Load template into primary storage.
        
        :param zoneid: zone ID of the template to be prepared in primary 
                       storage(s).
        :return: Dictionary with all network configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'prepareTemplate',
                  'templateid':self.id,
                  'zoneid':zoneid}
        
        try:
            response = self.send_request(params)        
            res = json.loads(response)['preparetemplateresponse']
            if len(res) > 0:
                self._data = res['template'][0]
                self.logger.debug('Load template %s primary storage' % self._data['name'])
                return self._data
            else:
                return None
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)        