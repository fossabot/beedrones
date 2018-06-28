'''
Created on May 10, 2013

@author: darkbk
'''
import urllib
import urllib2
import json
import logging

class ProxyError(Exception): pass
class ProxyResponseError(Exception): pass

class ProxyApi(object):
    """Proxy for cloudstack api based on flask
    """
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, api_url, timeout=30):
        ''' '''
        self._api_url = api_url
        self._timeout = timeout
        self._error = None
        
        self._params = None

    def set_timeout(self, timeout):
        self._timeout = timeout

    def set_proxy(self, proxy, user=None):
        """ Set http proxy server.
        
        :param proxy: 'http://www.example.com:3128/'
        :param user: tupla with (username, password)
        """
        proxy_handler = urllib2.ProxyHandler({'http':proxy})
        proxy_auth_handler = urllib2.ProxyBasicAuthHandler()
        if user:
            proxy_auth_handler.add_password('realm', 'host', user[0], user[1])
        
        opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
        urllib2.install_opener(opener)

    def get_request(self, request):
        self._parse_in_request(request)
        self._filter_in_request()
        response = self._send_in_request()
        return response

    def _parse_in_request(self, request):
        """Parse input api request """
        error = None
        self.logger.debug("Http method: %s" % request.method)
        if request.method == 'GET':
            self._params = request.args.to_dict()
            self.logger.debug("Request params: %s" % self._params)
        
        elif request.method == 'POST':
            self._params = request.form.to_dict()
            self.logger.debug("Request params: %s" % self._params)

    def _filter_in_request(self):
        """Filter input api request """
        pass

    def _send_in_request(self):
        """Redirect input api request to cloudstack api.
        """
        try:
            req_params = urllib.urlencode(self._params)
        except Exception as ex:
            raise ProxyError('Error signing request string')        
        
        try:
            self.logger.debug('Send api request to: %s' % self._api_url)
            self.logger.debug('Request params: %s' % req_params)
            self.logger.debug('Request timeout: %s' % self._timeout)
            if len(self._params) > 0:
                f = urllib2.urlopen(self._api_url, req_params, self._timeout)
                response = f.read()
                self.logger.debug('Response length: %s' % len(response))
                f.close() 
                return response
            else:
                return "{'command':'ping', 'message':'ok'}" 
        except (urllib2.URLError) as ex:
            self._error = json.loads(ex.fp.readline()).values()
            raise ProxyResponseError()
        except (IOError) as ex:
            raise ProxyError(ex)