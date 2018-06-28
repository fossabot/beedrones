'''
Created on May 10, 2013

@author: darkbk
'''
import os
os.environ['http_proxy']=''
import urllib
import urllib2
import json
from hashlib import sha1
import hmac
import binascii
import sys
import logging
import time
import copy
from gibbonutil.simple import id_gen
from gibbonutil.logger import Event, JobEvent, LoggerHelper, AMQPHandlerError

class ApiError(Exception): pass
class ClskObjectError(Exception): pass

class ApiClient(object):
    """
    Configure 'gibbon.cloud' logger to log data.
    """
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, base_url, api_key, sec_key):
        ''' '''
        # cloudstack url
        self.base_url = base_url
        self.api_key = api_key
        self.sec_key = sec_key
        
        self._timeout = 30 #30s
        
        self._error = None

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

    def send_api_request(self, init_params):
        '''
        HMAC SHA-1 with secret key
        Base64 encode the resulting byte array in UTF-8
        :param proxies: proxy server {'http': 'http://www.someproxy.com:3128'}
        '''
        params = copy.deepcopy(init_params)
        
        if params != None and type(params) is dict:
            params['apiKey'] = self.api_key
            params['response'] = 'json'
        else:
            raise ApiError('Params are not specify correctly.')
    
        try:
            # import collection
            if sys.version_info < (2, 7):
                import ordereddict
                sortedParams = ordereddict.OrderedDict(sorted(params.items()))
            else:
                import collections
                sortedParams = collections.OrderedDict(sorted(params.items()))
        except ImportError:
            self.logger.error('OrderedDict import raise error. If python version\
                           < 2.7 install collections module.')
            raise ApiError('OrderedDict import raise error. If python version\
                           < 2.7 install collections module.') 
        
        try:
            raw = urllib.urlencode(sortedParams).lower()
            
            # create sign for request string
            hashed = hmac.new(self.sec_key, raw, sha1)
            sign = binascii.b2a_base64(hashed.digest())[:-1]
            
            # add signature to request params
            params['signature'] = sign
            req_params = urllib.urlencode(params)
        except Exception as ex:
            self.logger.error('Error signing request string')
            raise ApiError('Error signing request string')

        try:
            self.logger.debug('Query cloudstack api - START - url: %s?%s' % (
                self.base_url, req_params))
            
            f = urllib2.urlopen(self.base_url, req_params, self._timeout)
            response = f.read()
            f.close()
            del params
            self.logger.debug('Query cloudstack api - STOP')
            return response
        except (urllib2.URLError) as ex:
            try:
                self._error = json.loads(ex.fp.readline()).values()
                err = self._error[0]['errortext']
            except:
                err = ex.reason
                
            self.logger.error(err)
            raise ApiError("Error sending http request: %s" % err)
        except (IOError) as ex:
            self.logger.error(ex)
            raise ApiError(ex)

    def query_async_job(self, job_id, clsk_job_id, timeout=1200, delta=5):
        '''Query async job.
        
        :param timeout: job query timeout [default = 1200s]
        :param delta: job query pool period [default = 5s]
        '''
        if not job_id:
            raise ApiError("Portal job id must be specified.")

        params = {'command':'queryAsyncJobResult',
                  'jobid':clsk_job_id}
        
        # loop until job has finished
        self.logger.debug("Query cloudstack job %s - START" % job_id)
        try:
            # create data
            data = {'id':job_id, 'status':2, 'elapsed':0, 
                    'clsk_job_id':clsk_job_id, 'error':''}
            # send job change event
            JobEvent(id_gen(),
                     data,
                     transaction=job_id,
                     user=None,
                     source_addr=None,
                     dest_addr=None).publish()        
        except (AMQPHandlerError, Exception) as ex:      
            self.logger.error(ex)
        
        # start loop
        timeout = int(timeout)
        start = time.time()
        while timeout > 0:
            # sleep a litte
            time.sleep(delta)
            timeout = timeout - delta
            
            # send api request - raise ApiError
            res = self.send_api_request(params)
            try:
                job_res = json.loads(res)['queryasyncjobresultresponse']
                jobstatus = job_res['jobstatus']
            except KeyError as ex:
                raise ApiError(ex)
            
            # cloudstack job error
            if jobstatus == 2:
                jobresult = job_res["jobresult"]
                self.logger.error('Query cloudstack job %s (%s) - ERROR - %s, %s' % (
                    job_id, clsk_job_id, jobresult["errorcode"], jobresult["errortext"]))
                raise ApiError("Async-job %s failed. Error %s, %s" % (
                    job_id, jobresult["errorcode"], jobresult["errortext"]))
                                       
            # cloudstack job completed
            elif jobstatus == 1:
                elapsed = time.time() - start
                self.logger.debug("Query cloudstack job  %s (%s) - STOP - %ss" % (
                                  job_id, clsk_job_id, elapsed))
                jobresult = job_res["jobresult"]
                return jobresult
            
            # cloudstack job run
            elapsed = round(time.time() - start, 2)
            self.logger.debug("Query cloudstack job  %s (%s) - RUN - %ss" % (
                              job_id, clsk_job_id, elapsed))
            # publish job status event
            try:
                # change data
                data['status'] = 4 #RUN
                data['elapsed'] = elapsed
                data['error'] = ''
                # send job change event
                JobEvent(id_gen(),
                         data,
                         transaction=job_id,
                         user=None,
                         source_addr=None,
                         dest_addr=None).publish()        
            except (AMQPHandlerError, Exception) as ex:      
                self.logger.error(ex)         
        
        # timeout
        raise ApiError("Query cloudstack job %s (%s) : TIMEOUT" % (job_id, clsk_job_id))

class ClskObject(object):
    ''' '''
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, api_client, data=None, oid=None):
        '''
        :param data: set data for current object
        :param oid: set oid for current object. Data will be ask to api
        '''
        self._api_client = api_client
        self._name = None
        self._id = oid
        self._obj_type = None
        self._data = data
        
        if data:
            # assign name and id from data
            self._name = data['name']
            self._id = data['id']
        elif oid:
            # call info api
            self.info(cache=False)            
        else:
            raise ClskObjectError('At least oid or data must be supply.')

    @property
    def name(self):
        """Get name."""
        return self._name
    
    @property
    def id(self):
        """Get id."""
        return self._id

    @property
    def obj_type(self):
        """Get object type."""
        return self._obj_type

    def info(self, cache=True):
        '''Object info'''
        # use cached data and don't call api
        if cache and self._data != None:
            return self._data    