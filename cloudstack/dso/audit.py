'''
Created on Dec 5, 2013

@author: darkbk
'''
import json
from .base import ClskObject, ClskObjectError, ApiError

class Audit(ClskObject):
    ''' '''
    def __init__(self, api_client, data=None, oid=None):
        ''' '''
        ClskObject.__init__(self, api_client, data=data, oid=oid)

        # load event type
        self._list_event_types()

    @property
    def event_types(self):
        """Get event types."""
        return self._event_types

    def _list_event_types(self):
        '''List all event types.'''
        params = {'command':'listEventTypes',
                  'listall':'true',
                 }
        
        response = self.send_api_request(params)
        
        try:
            self._event_type = json.loads(response)['listeventtypesresponse']['eventtype']
            return self._event_type
        except:
            raise ApiError('Error parsing json data.')

    def list_events(self, page=0, pagesize=20, startdate=None, enddate=None, 
                    type=None, level=None,
                    account=None, domain_id=None, project_id=None):
        '''List all events.
        
        :param level: INFO, WARN, ERROR
        :param startdate: yyyy-MM-dd HH:mm:ss
        :param enddate: yyyy-MM-dd HH:mm:ss
        '''
        params = {'command':'listEvents',
                  'page':page,
                  'pagesize':pagesize,
                 }
        if type: params['type'] = type
        if level: params['level'] = level
        if startdate: params['startdate'] = startdate
        if enddate: params['enddate'] = enddate
        if domain_id:
            params['domainid'] = domain_id
            if enddate: params['account'] = account
            elif enddate: params['project_id'] = project_id
        
        try:
            response = self.send_api_request(params)
        except ApiError:
            return self._error
        
        try:
            data = json.loads(response)['listeventsresponse']['event']
            return data
        except:
            raise ApiError('Error parsing json data.')