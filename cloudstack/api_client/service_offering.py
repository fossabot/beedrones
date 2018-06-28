"""
Created on May 10, 2013

@author: darkbk
"""
import ujson as json
from beedrones.cloudstack.api_client import ApiError
from beedrones.cloudstack.api_client import ClskObject, ClskError
from beecell.perf import watch

class ServiceOffering(ClskObject):
    """ServiceOffering api wrapper object.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object
    :type data: dict
    """
    def __init__(self, orchestrator, data):
        """ """  
        ClskObject.__init__(self, orchestrator, data)
        
        self._obj_type = 'serviceoffering'

    @watch
    def update(self, name, displaytext):
        """Update service offering.
        
        :param displaytext: the display text of the service offering to be updated
        :param name: the name of the service offering to be updated
        :return: Dictionary with all network configuration attributes.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateServiceOffering',
                  'id':self.id,
                  'name':name,
                  'displaytext':displaytext}

        try:
            response = self.send_request(params)
            res = json.loads(response)['updateserviceofferingresponse']['serviceoffering']
            self._data = res
            self.logger.debug("Update service offering: %s" % res)
            return self._data
        except KeyError as ex:
            raise ClskError('Service offering %s does not exist' % self.id)
        except ApiError as ex:
            raise ClskError(ex)

    @watch        
    def delete(self):
        """Delete service offering.

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """  
        params = {'command':'deleteServiceOffering',
                  'id':self.id}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            data = res['deleteserviceofferingresponse']['success']
            self.logger.debug("Delete service offering: %s" % data)
            return data
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)   