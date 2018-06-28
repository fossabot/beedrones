import os
os.environ['http_proxy']=''
import ujson as json
import logging
import urllib
import urllib2
import base64
import hashlib
import hmac
from gevent import Timeout
from beecell.perf import watch

class ApiError(Exception): pass
class ApiClient(object):
    """Base client to send request to cloudstack api.
    
    Configure **gibbon.cloud** logger to log data.
    
    :param base_url: Base cloudstack api url http://host:port/api
    :type base_url: str
    :param api_key: Cloudstack public key
    :type api_key: str
    :param sec_key: Cloudstack secret key
    :type sec_key: str
    """
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, base_url, api_key, sec_key):
        """ """
        # cloudstack url
        self.base_url = base_url
        self.api_key = api_key
        self.sec_key = sec_key
        
        self._timeout = 5 #30s
        
        self._error = None
        self._gevent_async = False

    def set_timeout(self, timeout):
        """Set http connection timeout """
        self._timeout = timeout

    def set_proxy(self, proxy, user=None):
        """ Set http proxy server.
        
        :param proxy: proxy server 'http://www.example.com:3128/'
        :param user: tupla with (username, password)
        """
        proxy_handler = urllib2.ProxyHandler({'http':proxy})
        proxy_auth_handler = urllib2.ProxyBasicAuthHandler()
        if user:
            proxy_auth_handler.add_password('realm', 'host', user[0], user[1])
        
        opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
        urllib2.install_opener(opener)

    def set_gevent_async(self, async):
        """If set to True enable non blocking http request based on gevent."""
        self._gevent_async = async      
    
    @watch
    def send_api_request(self, init_params):
        """Send request to api.
        
        :param dict init_params: Request params
        :return: http request response
        :rtype: str
        :raises ApiError: raise :class:`ApiError` if there are some error during connection.
        """
        # gevent based api request
        if self._gevent_async:
            timeout = Timeout(self._timeout)
            timeout.start()
            try:
                #self.logger.debug('START')
                res = self._send_api_request(init_params)
                #self.logger.debug('STOP')
            except Timeout:
                err = 'Gevent timeout after : %ss' % self._timeout
                self.logger.error(err)
                raise ApiError(err)
            except ApiError:
                raise
            finally:
                timeout.cancel()
        # blocking api request
        else:
            res = self._send_api_request(init_params, timeout=self._timeout)
        
        return res

    def _send_api_request(self, init_params, timeout=None):
        """Send request to api.
        
        :param dict init_params: Request params
        :return: http request response
        :rtype: str
        :raises ApiError: raise :class:`ApiError` if there are some error during connection.
        """
        response = None

        init_params["apiKey"] = self.api_key
        init_params["response"] = "json"
        request = zip(init_params.keys(), init_params.values())
        request.sort(key=lambda x: x[0].lower())
    
        request_url = "&".join(["=".join([r[0], urllib.quote_plus(str(r[1]))])
                               for r in request])
        hashStr = "&".join(["=".join([r[0].lower(),
                           str.lower(urllib.quote_plus(str(r[1]))).replace("+",
                           "%20")]) for r in request])
    
        hashed = hmac.new(self.sec_key, hashStr, hashlib.sha1).digest()
        sig = urllib.quote_plus(base64.encodestring(hashed).strip())
        request_url += "&signature=%s" % sig
        #request_url = "%s://%s:%s%s?%s" % (protocol, host, port, path, request_url)
        request_url = "%s?%s" % (self.base_url, request_url)

        try:
            self.logger.debug("Request sent: %s" % request_url)
            if timeout:
                connection = urllib2.urlopen(request_url, timeout=timeout)
            else:
                connection = urllib2.urlopen(request_url)
            response = connection.read()
        except urllib2.HTTPError, e:
            err = "%s: %s" % (e, e.info().getheader('X-Description'))
            self.logger.error(err)
            raise ApiError("Error sending http request: %s" % err)
        except urllib2.URLError, e:
            err = e.reason
            self.logger.error(err)
            raise ApiError("Error sending http request: %s" % err)              
    
        self.logger.debug("Response length received: %s" % len(response))
    
        return response

    @watch
    def query_async_job(self, clsk_job_id):
        """Retrieves the current status of asynchronous job.
        
        :param clsk_job_id: Cloudstack job id
        :return: aync job response
        :rtype: str
        :raises ApiError: raise :class:`ApiError` if there are some error during connection.        
        """
        # make request
        params = {'command':'queryAsyncJobResult',
                  'jobid':clsk_job_id}
                
        res = self.send_api_request(params)
            
        try:
            # get response
            job_res = json.loads(res)['queryasyncjobresultresponse']
            self.logger.debug('Query async job %s: %s' % (clsk_job_id, job_res))
            return job_res
        except KeyError as ex:
            raise ApiError(ex)
    
    @watch
    def list_async_jobs(self, account=None, domainid=None, isrecursive=None,
                              page=None, pagesize=None, startdate=None):
        """Retrieves the current status of asynchronous job.
        
        :param account: list resources by account. Must be used with the 
                        domainId parameter.
        :param domainid: list only resources belonging to the domain specified
        :param isrecursive: defaults to false, but if true, lists all resources 
                            from the parent specified by the domainId till leaves.
        :param page:
        :param pagesize:
        :param startdate: the start date of the async job
        
        :return: aync job response
        :rtype: str
        :raises ApiError: raise :class:`ApiError` if there are some error during connection.        
        """
        params = {'command':'listAsyncJobs',
                  'listall':True}

        if account:
            params['account'] = account
        if domainid:
            params['domainid'] = domainid
        if isrecursive:
            params['isrecursive'] = isrecursive
        if page:
            params['page'] = page
        if pagesize:
            params['pagesize'] = pagesize
        if startdate:
            params['startdate'] = startdate

        response = self.send_api_request(params)

        try:
            res = json.loads(response)['listasyncjobsresponse']
            if len(res) > 0:
                data = res['asyncjobs']
                self.logger.debug('List async jobs: %s' % len(data))
                return data
            else:
                return []
        except KeyError as ex:
            raise ApiError('Error parsing json data: %s' % ex)  
    
    @watch
    def list_apis(self, name=None):
        """Lists all available apis on the server, provided by the Api 
        Discovery plugin.
        Be carefully, this function require some seconds to respond and response
        is very big. 
        
        :param str name: API name
        :return: list apis
        :rtype: list
        :raises ApiError: raise :class:`ApiError` if there are some error during connection.        
        """
        # make request
        params = {'command':'listApis'}

        if name:
            params['name'] = name
                
        res = self.send_api_request(params)
            
        try:
            # get response
            res = json.loads(res)['listapisresponse']['api']
            self.logger.debug('List server api: %s' % (res))
            return res
        except KeyError as ex:
            raise ApiError(ex)

class ClskError(Exception): pass
class ClskObject(object):
    """Base cloudstack object use when interact with api.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object. [optional]
    :type data: dict or None
    :param oid: set oid for current object. [optional]
    :type data: str or None
    """
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, orchestrator, data):
        """ """
        self._orchestrator = orchestrator
        #self._name = None
        #self.id = oid
        self._obj_type = ''
        self._tag_type = '' # type used by tag api
        self._tag_type_allowed = ['UserVm', 'Template', 'ISO', 'Volume',
                                  'Snapshot', 'GuestNetwork', 'LBrule',
                                  'PFrule', 'Firewallrule', 'SecurityGroup', 
                                  'PublicIPAddress',  'Project', 'Vpc',
                                  'NetworkACL', 'StaticRoute']
        
        # set custom cloudstack attributes as class attributes
        try:
            self.name = ''
            for k,v in data.iteritems():
                if type(v) is str or type(v) is unicode:
                    v = v.decode('UTF8')
                self.__setattr__(k, v)
        except Exception as ex:
            self.logger.warning(ex)
            
        #print self.__dict__
        
        """
        if data:
            # assign name and id from data
            self._name = data['name']
            self.id = data['id']
        elif oid:
            # call info api
            self.info()
        else:
            raise ClskError('At least oid or data must be supplied.')
        """

    def __getattr__(self, name):
        return None    
    
    def __str__(self):
        return "<%s id='%s', name='%s'>" % (self._obj_type, 
                                            self.id, 
                                            self.name)
        
    def __repr__(self):
        return "<%s id='%s', name='%s'>" % (self._obj_type, 
                                            self.id,
                                            self.name)

    @property
    def obj_type(self):
        """Get object type."""
        return self._obj_type

    @property
    def async(self):
        return self._orchestrator._api_client._gevent_async

    def is_extended(self):
        return self._orchestrator.is_extended()    

    def get_hypervisor(self, hid):
        return self._orchestrator.hypervisor(hid)

    def open_db_session(self):
        db_session = self._orchestrator.open_db_session()
        return db_session

    def send_request(self, params):
        """Send api client if orchestrator is active.
        
        :param dict params: Request params
        :return: Api response
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`        
        """        
        return self._orchestrator.send_request(params)

    @watch
    def list_tags(self):
        """List resource tag(s)
        
        :return: Dictionary with following key:
                account: the account associated with the tag
                customer: customer associated with the tag
                domain: the domain associated with the tag
                domainid: the ID of the domain associated with the tag
                key: tag key name
                project: the project name where tag belongs to
                projectid: the project id the tag belongs to
                resourceid: id of the resource
                resourcetype: resource type
                value: tag value    
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listTags',
                  'resourceid':self.id}

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)['listtagsresponse']
            if len(res) > 0:
                data = res['tag']
                self.logger.debug('Get cloudstack %s configurations: %s' % (self.id, data))
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data
    
    @watch    
    def create_tags(self, tags):
        """Creates resource tag(s). Type supoorted are:
            UserVm
            Template
            ISO
            Volume
            Snapshot
            Guest Network
            LBrule
            PFrule
            Firewallrule
            Security Group
            PublicIPAddress
            Project
            Vpc
            NetworkACL
            StaticRoute.
        See https://cwiki.apache.org/confluence/display/CLOUDSTACK/Resource+Tags.
        
        *Async command*
        
        :param list tags: list of tuple with key and value. Ex. [(key0, value0), ..] 
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError` 
        """        
        if not self._tag_type in self._tag_type_allowed:
            raise ClskError('Create tag is not allowed for this resource type.')         
        
        params = {'command':'createTags',
                  'resourceIds':self.id,
                  'resourceType':self._tag_type}
        
        index = 0
        for item in tags:
            params['tags['+str(index)+'].key'] = item[0]
            params['tags['+str(index)+'].value'] = item[1]
            index += 1

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['createtagsresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def delete_tags(self, tags):
        """Deleting resource tag(s). Delete tags matching key/value pairs.
        Type supoorted are:
            UserVm
            Template
            ISO
            Volume
            Snapshot
            Guest Network
            LBrule
            PFrule
            Firewallrule
            Security Group
            PublicIPAddress
            Project
            Vpc
            NetworkACL
            StaticRoute.
        See https://cwiki.apache.org/confluence/display/CLOUDSTACK/Resource+Tags.
        
        *Async command*
        
        :param list tags: list of tuple with key and value. Ex. [(key0, value0), ..] 
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError` 
        """        
        if not self._tag_type in self._tag_type_allowed:
            raise ClskError('Create tag is not allowed for this resource type.')         
        
        params = {'command':'deleteTags',
                  'resourceIds':self.id,
                  'resourceType':self._tag_type}
        
        index = 0
        for item in tags:
            params['tags['+str(index)+'].key'] = item[0]
            params['tags['+str(index)+'].value'] = item[1]
            index += 1

        try:
            response = self._api_client.send_api_request(params)
            res = json.loads(response)
            clsk_job_id = res['deletetagsresponse']['jobid']
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)



from .orchestrator import ClskOrchestrator 

"""
from .virtual_machine import VirtualMachine
from .virtual_router import VirtualRouter
from .system_virtual_machine import SystemVirtualMachine

from .volume import Volume
from .sdn import SDN
from .template import Template
from .iso import Iso
from .domain import Domain
from .account import Account
from .event import Event
from .zone import Zone
from .alert import Alert
from .cluster import Cluster
from .pod import Pod
from .host import Host
from .service_offering import ServiceOffering
from .network_offering import NetworkOffering
from .disk_offering import DiskOffering
from .region import Region
"""