"""
Created on May 10, 2013

@author: darkbk
"""
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch

class Alert(ClskObject):
    """Alert api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict 
    """ 
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'alert'

    '''
    def info(self, cache=True):
        """Describe alert
        
        :return: Dictionary with all network configuration attributes.
        :rtype: dict       
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listAlerts',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listalertsresponse']
            print res
            if 'alert' in res:
                self._data = res['alert'][0]
                self.logger.debug('Get alert %s description' % self.id)
                return self._data
            else:
                raise ApiError('Alert %s does not exist.' % self.id)
        except KeyError:
            raise ClskError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
    '''

    @watch
    def archive(self):
        """Archive the alert.

        :return: archive response
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError`    
        """  
        params = {'command':'archiveAlerts',
                  'ids':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            data = res['archivealertsresponse']['success']
            self.logger.debug('Archive alert %s' % self.id)
            return data
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def delete(self):
        """Delete the alert.

        :return: delete response
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError`    
        """  
        params = {'command':'deleteAlerts',
                  'ids':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            data = res['deletealertsresponse']['success']
            self.logger.debug('Delete alert %s' % self.id)
            return data
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)