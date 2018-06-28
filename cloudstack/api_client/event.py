"""
Created on May 10, 2013

@author: darkbk
"""
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch

class Event(ClskObject):
    """Event api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'event'

    '''
    @watch
    def info(self):
        """Describe event
        
        :return: Dictionary with all network configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listEvents',
                  'id':self.id,}

        try:
            response = self .send_request(params)
            res = json.loads(response)['listeventsresponse']
            if 'alerts' in res:
                self._data = res['event'][0]
                self.logger.debug('Get event %s description' % self.id)
                return self._data
            else:
                raise ApiError('Event %s does not exist.' % self.id)
            return self._data
        except KeyError:
            raise ApiError('Error parsing json data.')
        except ApiError as ex:
            raise ClskError(ex)
    '''

    @watch
    def archive(self):
        """Archive the event.

        :return: archive response
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError`    
        """  
        params = {'command':'archiveEvents',
                  'ids':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            data = res['archiveeventsresponse']['success']
            self.logger.debug('Archive event %s' % self.id)
            return data
        except (KeyError, TypeError) as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def delete(self):
        """Delete the event.

        :return: delete response
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError`
        """  
        params = {'command':'deleteEvents',
                  'ids':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            data = res['deleteeventsresponse']['success']
            self.logger.debug('Delete event %s description' % self.id)
            return data
        except (KeyError, TypeError) as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)