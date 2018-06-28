'''
Created on Feb 13, 2016

@author: darkbk
'''
import ujson as json
from logging import getLogger, DEBUG
import httplib
from time import time
import ssl
import re
from beecell.simple import truncate, get_value
from beecell.logger.helper import LoggerHelper
from beecell.perf import watch
from urlparse import urlparse
from urllib import urlencode

class OpenstackError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
    
    def __repr__(self):
        return "OpenstackError: %s" % self.value    
    
    def __str__(self):
        return "OpenstackError: %s" % self.value
    
class OpenstackNotFound(OpenstackError):
    def __init__(self):
        OpenstackError.__init__(self, u'NOT_FOUND', 404)    

class OpenstackClient(object):
    """
    :param uri: Ex. http://172.25.3.51:5000/v3
    :param proxy: proxy server. Ex. ('proxy.it', 3128) [default=None]
    """
    
    def __init__(self, uri, proxy=None):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        
        obj = urlparse(uri)

        self.proto = obj.scheme
        self.path = obj.path
        self.host, self.port = obj.netloc.split(':')
        self.port = int(self.port)
        self.proxy = proxy
        
    @watch
    def call(self, path, method, data='', headers=None, timeout=30, 
             token=None, base_path=None):
        """Http client. Usage:
        
        res = http_client2('https', '/api', 'POST', port=443, data='', headers={})        
        
        :param path: Request path. Ex. /api/
        :param method: Request method. Ex. GET, POST, PUT, DELETE
        :param headers: Request headers. [default={}]. Ex. 
            {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        :param data: Request data. [default={}]. Ex. 
            {'@number': 12524, '@type': 'issue', '@action': 'show'}
        :param timeout: Request timeout. [default=30s]
        :param token: Openstack authorization token [optional]
        :param base_path: base path that replace defualt path set initially
        :raise OpenstackError:
        :raise OpenstackNotFound: If request return 404
        """
        if base_path is not None:
            path = base_path + path
        else:
            path = self.path + path
        
        http_headers = {}
        http_headers[u'Content-Type'] = u'application/json'
        if token is not None:
            http_headers[u'X-Auth-Token'] = token
        if headers is not None:
            http_headers.update(headers)
        
        self.logger.info(u'Send http %s api request to %s://%s:%s%s' % 
                         (method, self.proto, self.host, self.port, path))
        #self.logger.debug('Send headers: %s' % headers)
        if data.lower().find(u'password') < 0:
            self.logger.debug(u'Send [headers=%s] [data=%s]' % 
                              (headers, data))
        else:
            self.logger.debug(u'Send [headers=%s] [data=%s]' % 
                              (headers, u'xxxxxxx'))
        
        try:
            _host = self.host
            _port = self.port
            _headers = http_headers
            if self.proxy is not None:
                _host = self.proxy[0]
                _port = self.proxy[1]
                _headers = {}
                path = u'%s://%s:%s%s' % (self.proto, self.host, self.port, path)
            
            if self.proto == u'http':       
                conn = httplib.HTTPConnection(_host, _port, timeout=timeout)
            else:
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except:
                    pass
                conn = httplib.HTTPSConnection(_host, _port, timeout=timeout)

            if self.proxy is not None:
                conn.set_tunnel(self.host, port=self.port, headers=headers)
                self.logger.debug(u'set proxy %s' % self.proxy)
                headers = None

            conn.request(method, path, data, _headers)
            response = conn.getresponse()
            content_type = response.getheader(u'content-type')
            self.logger.info(u'Response status: %s %s' % 
                              (response.status, response.reason))
        except httplib.HTTPException as ex:
            raise OpenstackError(ex, 400)
        
        # read response
        try:
            res = response.read()
            res_headers = response.getheaders()
            if content_type ==  u'application/octet-stream':
                self.logger.debug(u'Response [content-type=%s] [headers=%s]' % 
                              (content_type, truncate(res_headers)))
            else:
                self.logger.debug(u'Response [content-type=%s] [headers=%s] [data=%s]' % 
                              (content_type, truncate(res_headers), truncate(res)))
            #self.logger.debug(u'Response [content-type=%s] [headers=%s] [data=%s]' % 
            #                  (content_type, truncate(res_headers), res))            
            if content_type is not None and \
               content_type.find(u'application/json') >= 0:
                try:
                    res = json.loads(res)
                except Exception as ex:
                    self.logger.warn(ex)
                    res = res
            conn.close()
        except httplib.HTTPException as ex:
            raise OpenstackError(ex, 400)                
        except Exception as ex:
            raise OpenstackError(ex, 400)

        # get error messages
        if response.status in [400, 401, 403, 404, 405, 408, 409, 413, 415, 
                               500, 503]:
            try:
                excpt = res.keys()[0]
                res = u'%s - %s' % (excpt, res[excpt][u'message'])
            except:
                res = u''
            self.logger.error(u'Response [content-type=%s] [data=%s]' % 
                              (content_type, truncate(res)), exc_info=True)
            
        # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status == 400:
            raise OpenstackError(u'Bad Request%s' % res, 400)
  
        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif response.status == 401:
            raise OpenstackError(u'Unauthorized%s', 401)
        
        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3
        
        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif response.status == 403:
            raise OpenstackError(u'Forbidden%s' % res, 403)
        
        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif response.status == 404:
            raise OpenstackNotFound()
        
        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif response.status == 405:
            raise OpenstackError(u'Method Not Allowed%s' % res, 405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7
        
        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8
        
        # REQUEST_TIMEOUT        408
        elif response.status == 408:
            raise OpenstackError(u'Request timeout%s' % res, 408)
        
        # CONFLICT               409
        elif response.status == 409:
            raise OpenstackError(u'Conflict%s' % res, 409)
            # raise OpenstackError(' conflict', 409)
        
        # Request Entity Too Large          413
        elif response.status == 413:
            raise OpenstackError(u'Request Entity Too Large%s' % res, 413)
        
        # Unsupported Media Type            415
        elif response.status == 415:
            raise OpenstackError(u'Unsupported Media Type%s' % res, 415)
        
        # INTERNAL SERVER ERROR  500
        elif response.status == 500:
            raise OpenstackError(u'Server error%s' % res, 500)
        
        # Service Unavailable  503
        elif response.status == 503:
            raise OpenstackError(u'Service Unavailable%s' % res, 503)         
        
        # OK                     200    HTTP/1.1, RFC 2616, Section 10.2.1
        # CREATED                201    HTTP/1.1, RFC 2616, Section 10.2.2
        # ACCEPTED               202    HTTP/1.1, RFC 2616, Section 10.2.3
        # NON_AUTHORITATIVE_INFORMATION    203    HTTP/1.1, RFC 2616, Section 10.2.4
        # NO_CONTENT             204    HTTP/1.1, RFC 2616, Section 10.2.5
        # RESET_CONTENT          205    HTTP/1.1, RFC 2616, Section 10.2.6
        # PARTIAL_CONTENT        206    HTTP/1.1, RFC 2616, Section 10.2.7
        # MULTI_STATUS           207    WEBDAV RFC 2518, Section 10.2
        elif re.match(u'20[0-9]+', str(response.status)):
            return res, res_headers, response.status
    
class OpenstackManager(object):
    """
    """
    def __init__(self, uri=None, proxy=None, default_region=None):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        # identity service uri
        self.uri = uri
        # http(s) proxy
        self.proxy = proxy
        # region
        self.region = default_region
        
        # openstack proxy objects
        self.identity = OpenstackIdentity(self)
        self.system = None
        self.keypair = None
        self.server = None
        self.volume = None
        self.network = None
        self.image = None
        self.flavor = None
        self.project = None
        self.domain = None
        self.heat = None
        
        # authorization token
        #self.manager.identity.token = None
        # openstack services endpoint
        self.endpoints = None

    def set_region(self, region):
        self.region = region
    
    def authorize(self, user, pwd, project=None, domain=None, version='v3'):
        """
        :param scope: authentication scope. Could be project, domain, unscoped
        """
        # get token from identity service
        if version == 'v3':
            self.identity.get_token(user, pwd, project, domain)
        elif version == 'v2':
            self.identity.get_token_v2(user, pwd, project)
        #self.manager.identity.token = self.identity.token
        
        # import external classes
        from beedrones.openstack.heat import OpenstackHeat
        from beedrones.openstack.swift import OpenstackSwift       
        
        # initialize proxy objects
        self.system = OpenstackSystem(self)
        self.project = OpenstackProject(self)
        self.domain = OpenstackDomain(self)
        self.keypair = OpenstackKeyPair(self)
        self.server = OpenstackServer(self)
        self.volume = OpenstackVolume(self)
        self.network = OpenstackNetwork(self)
        self.image = OpenstackImage(self)
        self.flavor = OpenstackFlavor(self)
        self.heat = OpenstackHeat(self)
        self.swift = OpenstackSwift(self)
        
    @watch
    def ping(self):
        """
        """
        res = self.identity.ping()
        return res
    
    def endpoint(self, service, interface='public'):
        """
        :param service: service name
        :param interface: openstack inerface. Ex. admin, internal, public
                          [default=public]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        # get service endpoints
        endpoints = self.identity.catalog[service]['endpoints']
        for endpoint in endpoints:
            if endpoint['region_id'] == self.region and\
               endpoint['interface'] == interface:
                #self.logger.debug('Get service %s endpoint: %s' % 
                #                  (service, endpoint))
                return endpoint['url']
        raise OpenstackError('Service %s endpoint was not found' % 
                                       (service))
        
    def get_token(self):
        return self.identity.token
    
class OpenstackIdentity(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)        
        
        self.manager = manager
        self.client = OpenstackClient(manager.uri, manager.proxy)
        
        self.token = None
        self.token_expire = None
        # openstack services
        self.catalog = {}
        
        # openstack identity proxy objects
        self.role = OpenstackIdentityRole(manager)
        self.user = OpenstackIdentityUser(manager)
    
    @watch
    def ping(self):
        """
        """
        try:
            self.api()
            return True
        except:
            return False         

    @watch
    def api(self):
        """Get identity api versions.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call('/', 'GET', data='')
        self.logger.debug('Get openstack identity api versions: %s' % truncate(res))
        return res[0]
        
    @watch
    def get_token(self, user, pwd, project, domain):
        """
        :param scope: authentication scope. Could be project or domain
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        scope = 'project'
        credentials = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": user,
                            "domain": {"id": domain},
                            "password": pwd
                        }
                    }
                },
                "scope": None
            }
        }
        if scope == 'project':
            credentials['auth']['scope'] = {"project": {
                                                "name": project,
                                                "domain": {"name": domain}, 
                                            }}
        elif scope == 'domain':
            credentials['auth']['scope'] = {"domain": {
                                                "name": domain,              
                                            }}            
        
        data = json.dumps(credentials)
        res, headers, status = self.client.call('/auth/tokens', 'POST', data=data)
        
        # get token
        self.token = [h[1] for h in headers if h[0] == 'x-subject-token'][0]
        self.token_expire = res['token']['expires_at']
        
        # openstack service catalog
        self._parse_catalog(res['token']['catalog'])   
        
        self.logger.debug('Get authorization token: %s, %s' % (self.token, 
                                                               self.token_expire))
        #self.logger.debug('Service catalog: %s' % self.catalog)

        return {'token':self.token, 'expires_at':self.token_expire}   

    @watch
    def get_token_v2(self, user, pwd, project):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        credentials = {
            "auth": {
                "tenantName": project,
                "passwordCredentials": {
                    "username": user,
                    "password": pwd
                }
            }
        }       
        
        data = json.dumps(credentials)
        path = self.manager.uri
        redux_uri = path.rstrip('v3') + 'v2.0'

        res, headers, status = self.client.call('/tokens', 'POST', data=data, 
                                                base_path=redux_uri)

        # get token
        self.token = res['access']['token']['id']
        self.token_expire = res['access']['token']['expires']
        
        # openstack service catalog
        self._parse_catalog_v2(res['access']['serviceCatalog'])   
        
        self.logger.debug('Get authorization token: %s, %s' % (self.token, self.token_expire))
        #self.logger.debug('Service catalog: %s' % self.catalog)

        return {'token':self.token, 'expires_at':self.token_expire}  

    def _parse_catalog(self, catalog):
        """
        """
        for item in catalog:
            self.catalog[item['name']] = {'name':item['name'],
                                          'type':item['type'], 
                                          'id':item['id'],
                                          'endpoints':item['endpoints']}
        self.logger.debug('Parse openstack service catalog: %s' % truncate(self.catalog))

    def _parse_catalog_v2(self, catalog):
        """
        """
        for item in catalog:
            self.catalog[item['name']] = {'name':item['name'],
                                          'type':item['type'], 
                                          'endpoints':[]}
            endpoint = item['endpoints'][0]
            data = {
                "region_id": endpoint['region'],
                "url": endpoint['publicURL'],
                "region": endpoint['region'],
                "interface": "public",
                "id": endpoint['id']
            }
            self.catalog[item['name']]['endpoints'].append(data)
            
            data = {
                "region_id": endpoint['region'],
                "url": endpoint['adminURL'],
                "region": endpoint['region'],
                "interface": "admin",
                "id": endpoint['id']
            }
            self.catalog[item['name']]['endpoints'].append(data)
            
            data = {
                "region_id": endpoint['region'],
                "url": endpoint['internalURL'],
                "region": endpoint['region'],
                "interface": "internal",
                "id": endpoint['id']
            }
            self.catalog[item['name']]['endpoints'].append(data)              
            
        self.logger.debug('Parse openstack service catalog: %s' % truncate(self.catalog))

    def validate_token(self, token):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        self.client.call('/auth/tokens', 'GET', data='', 
                         headers={'X-Subject-Token':self.token},
                         token=self.token)
        self.logger.debug('Validate authorization token: %s' % self.token)
        return True

    def release_token(self, token=None):
        """
        :param token: token to release. If not specified release inner token [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if token is None:
            token = self.token
            self.token = None
            
        self.client.call('/auth/tokens', 'DELETE', data='', 
                         headers={'X-Subject-Token':token},
                         token=token)
        self.logger.debug('Release authorization token: %s' % token)
        return True

    def get_services(self):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call('/services', 'GET', data='', token=self.token)
        self.logger.debug('Get openstack services: %s' % truncate(res))
        return res[0]['services']
        
    def get_endpoints(self):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call('/endpoints', 'GET', data='', token=self.token)
        self.logger.debug('Get openstack endpoints: %s' % truncate(res))
        return res[0]['endpoints']

    #
    # credentials
    #
    def get_credentials(self, oid=None):
        """In exchange for a set of authentication credentials that the user 
        submits, the Identity service generates and returns a token. A token 
        represents the authenticated identity of a user and, optionally, grants 
        authorization on a specific project or domain. 
        
        :param oid: credential id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/credentials'
        key = 'credentials'
        if oid is not None:
            path = '%s/%s' % (path, oid)
            key = 'credential'
        res = self.client.call(path, 'GET', data='', token=self.token)
        self.logger.debug('Get openstack credentials: %s' % truncate(res))
        try:
            return res[0][key]
        except:
            raise OpenstackError('No credentials found')

    #
    # groups
    #
    def get_groups(self, oid=None):
        """
        
        :param oid: group id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/groups'
        key = 'groups'
        if oid is not None:
            path = '%s/%s' % (path, oid)
            key = 'group'
        res = self.client.call(path, 'GET', data='', token=self.token)
        self.logger.debug('Get openstack groups: %s' % truncate(res))
        try:
            return res[0][key]
        except:
            raise OpenstackError('No groups found')

    #
    # policies
    #
    def get_policies(self, oid=None):
        """
        
        :param oid: policy id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/policies'
        key = 'policies'
        if oid is not None:
            path = '%s/%s' % (path, oid)
            key = 'policy'
        res = self.client.call(path, 'GET', data='', token=self.token)
        self.logger.debug('Get openstack policies: %s' % truncate(res))
        try:
            return res[0][key]
        except:
            raise OpenstackError('No policies found')

    #
    # regions
    #
    def get_regions(self, oid=None):
        """
        
        :param oid: region id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/regions'
        key = 'regions'
        if oid is not None:
            path = '%s/%s' % (path, oid)
            key = 'region'
        res = self.client.call(path, 'GET', data='', token=self.token)
        self.logger.debug('Get openstack regions: %s' % truncate(res))
        try:
            return res[0][key]
        except:
            raise OpenstackError('No regions found')

    #
    # tenants
    #
    def get_tenants(self):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        res = self.client.call('/tenants', 'GET', data='', token=self.token)
        self.logger.debug('Get openstack tenants: %s' % truncate(res))
        return res[0]['tenants']

class OpenstackSystem(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        self.compute = OpenstackClient(manager.endpoint('nova'), manager.proxy)
        self.blockstore = OpenstackClient(manager.endpoint('cinderv2'), manager.proxy)
        self.network = OpenstackClient(manager.endpoint('neutron'), manager.proxy)
        self.heat = OpenstackClient(manager.endpoint('heat'), manager.proxy)
        self.swift = OpenstackClient(manager.endpoint('swift'), manager.proxy)
    
    def compute_api(self):
        """Get compute api versions.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = self.compute.path = '/'
        res = self.compute.call('', 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack compute services: %s' % truncate(res))
        self.compute.path = path
        return res[0]
    
    def compute_services(self):
        """Get compute service.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-services'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack compute services: %s' % truncate(res))
        return res[0]['services']
    
    def compute_zones(self):
        """Get compute availability zones.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-availability-zone/detail'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack availability zone: %s' % truncate(res))
        return res[0]['availabilityZoneInfo']
    
    def compute_hosts(self):
        """Get physical hosts.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-hosts'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack hosts: %s' % truncate(res))
        return res[0]['hosts']
    
    def compute_host_aggregates(self):
        """Get compute host aggregates.
        An aggregate assigns metadata to groups of compute nodes. Aggregates 
        are only visible to the cloud provider.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-aggregates'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack host aggregates: %s' % truncate(res))
        return res[0]['aggregates']
        
    def compute_server_groups(self):
        """Get compute server groups.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-server-groups'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack server groups: %s' % truncate(res))
        return res[0]['server_groups']

    def compute_hypervisors(self):
        """Displays extra statistical information from the machine that hosts 
        the hypervisor through the API for the hypervisor (XenAPI or KVM/libvirt).
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-hypervisors/detail'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack hypervisors: %s' % truncate(res))
        return res[0]['hypervisors']
    
    def compute_hypervisors_statistics(self):
        """Get compute hypervisors statistics.
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-hypervisors/statistics'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack hypervisors statistics: %s' % truncate(res))
        return res[0]['hypervisor_statistics']
    
    def compute_agents(self):
        """Get compute agents.
        Use guest agents to access files on the disk, configure networking, and 
        run other applications and scripts in the guest while it runs. This 
        hypervisor-specific extension is not currently enabled for KVM. Use of 
        guest agents is possible only if the underlying service provider uses 
        the Xen driver.  
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-agents'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack compute agents: %s' % truncate(res))
        return res[0]['agents']    
    
    def storage_services(self):
        """Get storage service.  
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-services'
        res = self.blockstore.call(path, 'GET', data='', 
                                   token=self.manager.identity.token)
        self.logger.debug('Get openstack storage services: %s' % truncate(res))
        return res[0]['services']
    
    def network_agents(self):
        """Get network agents.
        
        :return:
           [...,
            {u'admin_state_up': True,
              u'agent_type': u'Metadata agent',
              u'alive': True,
              u'binary': u'neutron-metadata-agent',
              u'configurations': {u'log_agent_heartbeats': False, u'metadata_proxy_socket': u'/var/lib/neutron/metadata_proxy', u'nova_metadata_ip': u'ctrl-liberty.nuvolacsi.it', u'nova_metadata_port': 8775},
              u'created_at': u'2015-12-22 14:33:59',
              u'description': None,
              u'heartbeat_timestamp': u'2016-05-08 16:21:55',
              u'host': u'ctrl-liberty2.nuvolacsi.it',
              u'id': u'e6c1e736-d25c-45e8-a475-126a13a07332',
              u'started_at': u'2016-04-29 21:31:22',
              u'topic': u'N/A'},
             {u'admin_state_up': True,
              u'agent_type': u'Linux bridge agent',
              u'alive': True,
              u'binary': u'neutron-linuxbridge-agent',
              u'configurations': {u'bridge_mappings': {},
                                  u'devices': 21,
                                  u'interface_mappings': {u'netall': u'enp10s0f1', u'public': u'enp10s0f1.62'},
                                  u'l2_population': True,
                                  u'tunnel_types': [u'vxlan'],
                                  u'tunneling_ip': u'192.168.205.69'},
              u'created_at': u'2015-12-22 14:33:59',
              u'description': None,
              u'heartbeat_timestamp': u'2016-05-08 16:21:55',
              u'host': u'ctrl-liberty2.nuvolacsi.it',
              u'id': u'eb1010c4-ad95-4d8c-b377-6fce6a78141e',
              u'started_at': u'2016-04-29 21:31:22',
              u'topic': u'N/A'}]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/v2.0/agents'
        res = self.network.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack network agents: %s' % truncate(res))
        return res[0]['agents']
    
    def network_service_providers(self):
        """Get network service providers.
        
        :return: [{u'default': True, 
                   u'name': u'haproxy', 
                   u'service_type': u'LOADBALANCER'}]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/v2.0/service-providers'
        res = self.network.call(path, 'GET', data='', 
                                token=self.manager.identity.token)
        self.logger.debug('Get openstack network service providers: %s' % 
                          truncate(res))
        return res[0]['service_providers']
    
    def orchestrator_services(self):
        """Get heat services.
        
        :return: Ex.
              [{u'binary': u'heat-engine',
                u'created_at': u'2016-04-29T20:52:52.000000',
                u'deleted_at': None,
                u'engine_id': u'c1942356-3cf2-4e45-af5e-75334d7e6263',
                u'host': u'ctrl-liberty2.nuvolacsi.it',
                u'hostname': u'ctrl-liberty2.nuvolacsi.it',
                u'id': u'07cf7fbc-22c3-4091-823c-12e297a0cc51',
                u'report_interval': 60,
                u'status': u'up',
                u'topic': u'engine',
                u'updated_at': u'2016-05-09T12:19:55.000000'},
               {u'binary': u'heat-engine',
                u'created_at': u'2016-04-29T20:52:52.000000',
                u'deleted_at': None,
                u'engine_id': u'd7316fa6-2e82-4fe0-94d2-09cbb5ad1bc6',
                u'host': u'ctrl-liberty2.nuvolacsi.it',
                u'hostname': u'ctrl-liberty2.nuvolacsi.it',
                u'id': u'0a40b1ef-91e8-4f63-8c0b-861dbbfdcf31',
                u'report_interval': 60,
                u'status': u'up',
                u'topic': u'engine',
                u'updated_at': u'2016-05-09T12:19:58.000000'},..,]        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path="/services"
        res = self.heat.call(path, 'GET', data='', 
                             token=self.manager.identity.token)
        self.logger.debug('Get openstack orchestrator services: %s' % \
                          truncate(res))
        return res[0]['services']

class OpenstackDomain(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        self.client = OpenstackClient(manager.uri, manager.proxy)
        
    def list(self):
        """
        :param domain: domain id
        :param parent: parent project id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/domains?'
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack domains: %s' % truncate(res))
        return res[0]['domains']
        
    def get(self, oid):
        """
        :param oid: domain id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/domains/%s' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack domains: %s' % truncate(res))
        return res[0]['domain']        
    
    def create(self, name, domain, is_domain=False, description=""):
        """Create domain
        TODO 
        
        :param name:
        :param domain:
        :param is_domain: Indicates whether the project also acts as a domain.
                          Set to true to define this project as both a project 
                          and domain. As a domain, the project provides a name 
                          space in which you can create users, groups, and other 
                          projects. Set to false to define this project as a 
                          regular project that contains only resources.
                          You cannot update this parameter after you create 
                          the project. [default=False] 
        :param description: [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"project": {
                    "description": description,
                    "domain_id": domain,
                    "enabled": True,
                    "name": name,
                    "is_domain": is_domain
                }
        }
        
        path = '/projects'
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack project: %s' % truncate(res))
        return res[0]['project']

    def update(self, oid, name=None, domain=None, enabled=None, 
               description=None):
        """Updates a domain.  TODO
        
        :param oid: user id
        :param name: [optional]
        :param domain: [optional]
        :param enabled: [optional]
        :param description: [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"project": {}}
        
        if name is not None:
            data['project']['name'] = name
        if domain is not None:
            data['project']['domain_id'] = domain
        if enabled is not None:
            data['project']['enabled'] = enabled
        if description is not None:
            data['project']['description'] = description
        
        path = '/projects/%s' % oid
        res = self.client.call(path, 'PATCH', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack project: %s' % truncate(res))
        return res[0]['project']
    
    def delete(self, oid):
        """Deletes a domain. TODO 
        
        :param oid: user id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/projects/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack project: %s' % truncate(res))
        return True

class OpenstackProject(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        self.client = OpenstackClient(manager.uri, manager.proxy)
        self.compute = OpenstackClient(manager.endpoint('nova'), manager.proxy)
        self.blockstore = OpenstackClient(manager.endpoint('cinderv2'), manager.proxy)
        self.network = OpenstackClient(manager.endpoint('neutron'), manager.proxy)        
        
    def list(self, domain=None, parent=None):
        """
        :param domain: domain id
        :param parent: parent project id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/projects'
        query = {}
        if domain is not None:
            query['domain_id'] = domain
        if parent is not None:
            query['parent_id'] = parent
        
        path = '%s?%s' % (path, urlencode(query))
            
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack users: %s' % truncate(res))
        return res[0]['projects']
        
    def get(self, oid=None, name=None):
        """
        :param oid: project id
        :param name: project name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '/projects/%s' % oid
        elif name is not None:
            path = '/projects?name=%s' % name
        else:
            raise OpenstackError('Specify at least project id or name')
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack user: %s' % truncate(res))
        if oid is not None:
            project = res[0]['project']
        elif name is not None:
            project = res[0]['projects'][0]
        
        return project
    
    def create(self, name, domain, is_domain=False, parent_id=None,
               description="", enabled=True):
        """Create project 
        
        :param name: The project name, which must be unique within the owning 
                     domain. The project can have the same name as its domain. 
        :param domain: The ID of the domain for the project.
                       If you omit the domain ID, default is the domain to which 
                       your token is scoped.
        :param parent_id: The ID of the parent project.
                          If you omit the parent project ID, the project is a 
                          top-level project. 
        :param is_domain: Indicates whether the project also acts as a domain.
                          Set to true to define this project as both a project 
                          and domain. As a domain, the project provides a name 
                          space in which you can create users, groups, and other 
                          projects. Set to false to define this project as a 
                          regular project that contains only resources.
                          You cannot update this parameter after you create 
                          the project. [default=False] 
        :param description: [optional] The project description.
        :param enabled: [default=True] Enables or disables the project.         
        :return: 
            {
                "is_domain": true,
                "description": "My new project",
                "links": {
                    "self": "http://localhost:5000/v3/projects/93ebbcc35335488b96ff9cd7d18cbb2e"
                },
                "enabled": true,
                "id": "93ebbcc35335488b96ff9cd7d18cbb2e",
                "parent_id": null,
                "domain_id": "default",
                "name": "myNewProject"
            }
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"project": {
                    "description": description,
                    "domain_id": domain,
                    "enabled": enabled,
                    "name": name,
                    "is_domain": is_domain
                }
        }
        
        if parent_id is not None:
            data[u'project'][u'parent_id'] = parent_id
        
        path = '/projects'
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack project: %s' % truncate(res))
        return res[0]['project']

    def update(self, oid, name=None, domain=None, enabled=None, 
               description=None, parent_id=None):
        """Updates a project. 
        
        :param name: The project name, which must be unique within the owning 
                     domain. The project can have the same name as its domain.
                     [optional] 
        :param domain: The ID of the domain for the project.
                       If you omit the domain ID, default is the domain to which 
                       your token is scoped. [optional] 
        :param parent_id: The ID of the parent project.
                          If you omit the parent project ID, the project is a 
                          top-level project. [optional] 
        :param is_domain: Indicates whether the project also acts as a domain.
                          Set to true to define this project as both a project 
                          and domain. As a domain, the project provides a name 
                          space in which you can create users, groups, and other 
                          projects. Set to false to define this project as a 
                          regular project that contains only resources.
                          You cannot update this parameter after you create 
                          the project. [optional] 
        :param description: [optional] The project description.        
        :param enabled: [optional] Enables or disables the project. 
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {u"project": {}}
        
        if name is not None:
            data[u'project'][u'name'] = name
        if domain is not None:
            data[u'project'][u'domain_id'] = domain
        if enabled is not None:
            data[u'project'][u'enabled'] = enabled
        if description is not None:
            data[u'project'][u'description'] = description
        if parent_id is not None:
            data[u'project'][u'parent_id'] = parent_id            
        
        path = '/projects/%s' % oid
        res = self.client.call(path, 'PATCH', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack project %s: %s' % 
                          (oid, truncate(res)))
        return res[0]['project']
    
    def delete(self, oid):
        """Deletes a project. 
        
        :param oid: user id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/projects/%s' % oid
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack project %s: %s' % 
                          (oid, truncate(res)))
        return True

    def get_quotas(self, oid):
        """
        :param oid: project id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        resp = {}
        path = '/os-quota-sets/%s/detail' % oid
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)        
        resp[u'compute'] = res[0][u'quota_set']
        resp[u'compute'].pop(u'id')

        path = '/os-quota-sets/%s?usage=true' % oid
        res = self.blockstore.call(path, 'GET', data='', 
                                   token=self.manager.identity.token)
        resp[u'block'] = res[0][u'quota_set']
        resp[u'block'].pop(u'id')

        path = '/v2.0/quotas/%s?detail=true' % oid
        res = self.network.call(path, 'GET', data='', 
                                token=self.manager.identity.token)        
        resp[u'network'] = res[0][u'quota']        
         
        self.logger.debug('Get openstack project quotas: %s' % truncate(res))
        return resp
    
    def get_default_quotas(self):
        """Get default quotas
        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        resp = {}
        path = '/os-quota-sets/default'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)        
        resp['compute'] = res[0]['quota_set']

        #path = '/os-quota-sets/defaults'
        #res = self.blockstore.call(path, 'GET', data='', 
        #                           token=self.manager.identity.token)
        #resp['block'] = res[0]['quota_set']
        resp['block'] = None

        path = '/v2.0/quotas/default'
        res = self.network.call(path, 'GET', data='', 
                                token=self.manager.identity.token)        
        resp['network'] = res[0]['quota']        
         
        self.logger.debug('Get openstack project quotas: %s' % truncate(res))
        return resp    
    
    def update_quota(self, oid, quota_type, quota, value):
        """
        :param oid: project id
        :param quota_type: can be compute, block or network
        :param quota: name of quota param to set
        :param vale: value to set
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        resp = None
        data = {u"quota_set": {quota: value}}
        
        if quota_type == 'compute':
            path = '/os-quota-sets/%s' % oid
            res = self.compute.call(path, 'PUT', data=json.dumps(data), 
                                    token=self.manager.identity.token)        
            resp = res[0]['quota_set']

        elif quota_type == 'block':
            path = '/os-quota-sets/%s' % oid
            res = self.blockstore.call(path, 'PUT', data=json.dumps(data), 
                                       token=self.manager.identity.token)
            resp= res[0]['quota_set']

        elif quota_type == 'network':
            path = '/v2.0/quotas/%s' % oid
            res = self.network.call(path, 'PUT', data=json.dumps(data), 
                                    token=self.manager.identity.token)        
            resp = res[0]['quota']        
         
        self.logger.debug('Set openstack project %s quota %s to %s: %s' % 
                          (oid, quota, value, truncate(res)))
        
        return resp

    def get_limits(self):
        """
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        resp = {}
        path = '/limits'
        res = self.compute.call(path, 'GET', data='', 
                                token=self.manager.identity.token)        
        resp['compute'] = res[0]['limits']['absolute']

        path = '/limits'
        res = self.blockstore.call(path, 'GET', data='', 
                                   token=self.manager.identity.token)        
        resp['block'] = res[0]['limits']['absolute']        
         
        self.logger.debug('Get openstack project quotas: %s' % truncate(res))
        return resp 

    def get_members(self, prj_id):
        """
        
        :param prj_id: project id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        resp = {'users':[], 'groups':[]}
        
        # get users
        path = '/users'
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)        
        users = res[0][u'users']
        for i in users:
            path = '/projects/%s/users/%s/roles' % (prj_id, i[u'id'])
            res = self.client.call(path, 'GET', data='', 
                                   token=self.manager.identity.token)

            # append user if has a role whitin the project
            if len(res[0][u'roles']) > 0:
                role = res[0][u'roles'][0]
                resp[u'users'].append({u'id':i[u'id'], 
                                       u'name':i[u'name'], 
                                       u'role_id':role[u'id'], 
                                       u'role_name':role[u'name']})

        self.logger.debug('Get openstack project %s members: %s' % 
                          (prj_id, truncate(res)))
        return resp
    
    def assign_member(self, project_id, user_id, role_id):
        """Grants a role to a user on a project. 
        
        :param project_id: The project ID.
        :param user_id: The user ID.
        :param role_id: The role ID.
        :raises OpenstackError: raise :class:`.OpenstackError` 
        """
        resp = {}
        path = '/projects/%s/users/%s/roles/%s' % (project_id, user_id, role_id)
        res = self.client.call(path, 'PUT', data='', 
                               token=self.manager.identity.token)      
         
        self.logger.debug('Grant role %s to user %s on project %s' % 
                          (project_id, user_id, role_id))
        return True
    
    def remove_member(self, project_id, user_id, role_id):
        """Revokes a role from a user on a project. 
        
        :param project_id: The project ID.
        :param user_id: The user ID.
        :param role_id: The role ID.
        :raises OpenstackError: raise :class:`.OpenstackError` 
        """
        resp = {}
        path = '/projects/%s/users/%s/roles/%s' % (project_id, user_id, role_id)
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)      
         
        self.logger.debug('Revoke role %s to user %s on project %s' % 
                          (project_id, user_id, role_id))
        return True    

class OpenstackIdentityRole(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        self.client = OpenstackClient(manager.uri, manager.proxy)
        
    def list(self, detail=False, name=None):
        """
        :param name: 
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/roles?'
        if detail is True:
            path = '/servers/detail?'
        if name is not None:
            path = '%sname=%s' % (path, name)
            
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack roles: %s' % truncate(res))
        return res[0]['roles']
        
    def get(self, oid):
        """
        :param oid: role id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/roles/%s' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack role: %s' % truncate(res))
        return res[0]['role']
    
    def create(self, ):
        """TODO
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {        
        }

        path = '/roles'
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack role: %s' % truncate(res))
        return res[0]['server']    

    def update(self, oid):
        """TODO
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/roles/%s' % oid
        res = self.client.call(path, 'PUT', data='', token=self.manager.identity.token)
        self.logger.debug('Update openstack role: %s' % truncate(res))
        return res[0]['server']
    
    def delete(self, oid):
        """TODO
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/roles/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack role: %s' % truncate(res))
        return res[0]['server']

    def assignments(self, role=None, group=None, user=None, project=None,
                    domain=None):
        """
        :param role:
        :param group:
        :param user:
        :param project:
        :param domain:
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/role_assignments?'
        if role is not None:
            path = '%srole.id=%s' % (path, role)
        elif group is not None:
            path = '%sgroup.id=%s' % (path, group)
        elif user is not None:
            path = '%suser.id=%s' % (path, user)
            
        if project is not None:
            path = '%s&scope.project.id=%s&include_subtree=true&effective' % (path, project)
        elif domain is not None:
            path = '%s&scope.domain.id=%s#effective' % (path, domain)
            
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack role assignments: %s' % truncate(res))
        return res[0]['role_assignments']

class OpenstackIdentityUser(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        self.client = OpenstackClient(manager.uri, manager.proxy)
        
    def list(self, detail=False, name=None, domain=None):
        """
        :param name: 
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/users?'
        if name is not None:
            path = '%sname=%s' % (path, name)
        if domain is not None:
            path = '%sdomain=%s' % (path, domain)            
            
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack users: %s' % truncate(res))
        return res[0]['users']
        
    def get(self, oid):
        """
        :param oid: role id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/users/%s' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack user: %s' % truncate(res))
        user = res[0]['user']
        
        # get groups
        path = '/users/%s/groups' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack user %s groups: %s' % (oid, truncate(res)))
        user[u'groups '] = res[0]['groups']
        
        # get projects
        path = '/users/%s/projects' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack user %s projects: %s' % (oid, truncate(res)))
        user[u'projects'] = res[0]['projects']
        
        # get roles
        path = '/role_assignments?user.id=%s&effective' % (oid)
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack user %s roles: %s' % (oid, truncate(res)))
        try:
            user[u'roles'] = [r['role'] for r in res[0]['role_assignments']]
        except:
            user[u'roles'] = []
        
        return user
    
    def create(self, name, email, default_project, domain, password, 
               description=""):
        """TODO
        :param name:
        :param email:
        :param default_project:
        :param domain:
        :param password:
        :param description: [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"user": {
                    "default_project_id": default_project,
                    "description": description,
                    "domain_id": domain,
                    "email": email,
                    "enabled": True,
                    "name": name,
                    "password": password
                }
        }
        
        path = '/users'
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack user: %s' % truncate(res))
        return res[0]['user']    

    def update(self, oid, name=None, email=None, default_project=None, 
               domain=None, password=None, enabled=None, description=None):
        """Updates the password for or enables or disables a user. 
        
        :param oid: user id
        :param name: [optional]
        :param email: [optional]
        :param default_project: [optional]
        :param domain: [optional]
        :param password: [optional]
        :param enabled: [optional]
        :param description: [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"user": {}}
        
        if name is not None:
            data['user']['name'] = name
        if email is not None:
            data['user']['email'] = email            
        if default_project is not None:
            data['user']['default_project_id'] = default_project
        if domain is not None:
            data['user']['domain_id'] = domain
        if password is not None:
            data['user']['password'] = password
        if enabled is not None:
            data['user']['enabled'] = enabled
        if description is not None:
            data['user']['description'] = description            
        
        path = '/users/%s' % oid
        res = self.client.call(path, 'PATCH', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack user: %s' % truncate(res))
        return res[0]['user']
    
    def delete(self, oid):
        """Deletes a user. 
        
        :param oid: user id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/users/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack user: %s' % truncate(res))
        return True

    def password(self, oid):
        """Changes the password for a user.
        
        :param oid: user id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/users/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack user: %s' % truncate(res))
        return res[0]['server']

class OpenstackKeyPair(object):
    """Generates, imports, and deletes SSH keys.
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        uri = manager.endpoint('nova')
        # change version from 2 to 2.1
        uri = uri.replace('v2/', 'v2.1/')
        self.client = OpenstackClient(uri, manager.proxy)
        
    def list(self, all_tenants=True):
        """Lists keypairs that are associated with the project
        
        :param all_tenants: if True show server fro all tenanst
        :return: Ex: 
        
            [{u'keypair': {u'fingerprint': u'd2:30:d8:f2:0f:8a:04:e2:2e:1e:87:61:ce:db:42:16',
                           u'name': u'admin',
                           u'public_key': u'ssh-rsa AAAAB3NzaC1y..L Generated-by-Nova'}},..
            ]   
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        query = {}
        path = '/os-keypairs'
        if all_tenants is True:
            query['all_tenants'] = 1
                
        path = '%s?%s' % (path, urlencode(query))           
            
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack key pairs: %s' % truncate(res))
        return res[0]['keypairs']
        
    def get(self, name):
        """Shows details for a keypair that is associated with the project
        
        :param name: key pair name
        :return: Ex: {u'created_at': u'2016-01-15T14:44:17.000000',
                      u'deleted': False,
                      u'deleted_at': None,
                      u'fingerprint': u'd2:30:d8:f2:0f:8a:04:e2:2e:1e:87:61:ce:db:42:16',
                      u'id': 2,
                      u'name': u'admin',
                      u'public_key': u'ssh-rsa AAAA..yUkaL Generated-by-Nova',
                      u'updated_at': None,
                      u'user_id': u'730cd1699f144275811400d41afa7645'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-keypairs/%s' % name
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack key pair %s: %s' % (name, truncate(res)))
        return res[0]['keypair']
    
    def create(self, name, public_key=None):
        """Generates or imports a keypair.
        
        :param name: The name to associate with the keypair. 
        :param public_key: The public ssh key to import. If you omit this value, 
                           a key is generated.
        :return: Ex.
            {u'fingerprint': u'5d:41:ed:f6:d2:86:2d:e4:c0:ef:24:0e:89:e9:cc:24',
             u'name': u'key_prova',
             u'private_key': u'-----BEGIN RSA PRIVATE KEY-----\nMIIEqAIB..mB1X
                             DU=\n-----END RSA PRIVATE KEY-----\n',
             u'public_key': u'ssh-rsa AAA..FFauV Generated-by-Nova',
             u'user_id': u'730cd1699f144275811400d41afa7645'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "keypair": {
                "name": name
            }
        }
        if public_key is not None:
            data['keypair']['public_key'] = public_key
        
        path = '/os-keypairs'
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create/import openstack keypair: %s' % truncate(res))
        return res[0]['keypair']    

    def delete(self, name):
        """Deletes a keypair.
        
        :param name: The keypair name.
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-keypairs/%s' % name
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack keypair %s: %s' % 
                          (name,truncate(res)))
        return res[0]

class OpenstackServer(object):
    """
    
    The server status is returned in the response body. The possible server 
    status values are:

    - ACTIVE. The server is active.
    - BUILDING. The server has not finished the original build process.
    - DELETED. The server is permanently deleted.
    - ERROR. The server is in error.
    - HARD_REBOOT. The server is hard rebooting. This is equivalent to pulling 
      the power plug on a physical server, plugging it back in, and rebooting it.
    - MIGRATING. The server is being migrated to a new host.
    - PASSWORD. The password is being reset on the server.
    - PAUSED. In a paused state, the state of the server is stored in RAM. A 
      paused server continues to run in frozen state.
    - REBOOT. The server is in a soft reboot state. A reboot command was passed 
      to the operating system.
    - REBUILD. The server is currently being rebuilt from an image.
    - RESCUED. The server is in rescue mode. A rescue image is running with the 
      original server image attached.
    - RESIZED. Server is performing the differential copy of data that changed 
      during its initial copy. Server is down for this stage.
    - REVERT_RESIZE. The resize or migration of a server failed for some reason. 
      The destination server is being cleaned up and the original source server 
      is restarting.
    - SOFT_DELETED. The server is marked as deleted but the disk images are 
      still available to restore.
    - STOPPED. The server is powered off and the disk image still persists.
    - SUSPENDED. The server is suspended, either by request or necessity. This 
      status appears for only the XenServer/XCP, KVM, and ESXi hypervisors. 
      Administrative users can suspend an instance if it is infrequently used or 
      to perform system maintenance. When you suspend an instance, its VM state 
      is stored on disk, all memory is written to disk, and the virtual machine 
      is stopped. Suspending an instance is similar to placing a device in 
      hibernation; memory and vCPUs become available to create other instances
    - UNKNOWN. The state of the server is unknown. Contact your cloud provider.
    - VERIFY_RESIZE. System is awaiting confirmation that the server is 
      operational after a move or resize.
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        uri = manager.endpoint('nova')
        # change version from 2 to 2.1
        uri = uri.replace('v2/', 'v2.1/')
        self.client = OpenstackClient(uri, manager.proxy)
        
    def list(self, detail=False, image=None, flavor=None, status=None, 
             host=None, limit=None, marker=None, all_tenants=True):
        """
        :param detail: if True show server details
        :param image: Filters the response by an image, as a UUID. 
        :param flavor: Filters the response by a flavor, as a UUID. A flavor is 
                       a combination of memory, disk size, and CPUs. 
        :param status: Filters the response by a server status, as a string. 
                       For example, ACTIVE. 
        :param host: Filters the response by a host name, as a string. This 
                     query parameter is typically available to only 
                     administrative users. If you are a non-administrative user, 
                     the API ignores this parameter. 
        :param limit: Requests a page size of items. Returns a number of items 
                      up to a limit value. Use the limit parameter to make an 
                      initial limited request and use the ID of the last-seen 
                      item from the response as the marker parameter value in a 
                      subsequent limited request. 
        :param marker: The ID of the last-seen item. Use the limit parameter to 
                       make an initial limited request and use the ID of the 
                       last-seen item from the response as the marker parameter 
                       value in a subsequent limited request. 
        :param all_tenants: if True show server fro all tenanst
        :return: Ex: [{u'OS-DCF:diskConfig': u'AUTO',
                     u'OS-EXT-AZ:availability_zone': u'nova',
                     u'OS-EXT-SRV-ATTR:host': u'comp-liberty2-kvm.nuvolacsi.it',
                     u'OS-EXT-SRV-ATTR:hypervisor_hostname': u'comp-liberty2-kvm.nuvolacsi.it',
                     u'OS-EXT-SRV-ATTR:instance_name': u'instance-00000471',
                     u'OS-EXT-STS:power_state': 1,
                     u'OS-EXT-STS:task_state': None,
                     u'OS-EXT-STS:vm_state': u'active',
                     u'OS-SRV-USG:launched_at': u'2016-03-02T13:02:58.000000',
                     u'OS-SRV-USG:terminated_at': None,
                     u'accessIPv4': u'',
                     u'accessIPv6': u'',
                     u'addresses': {u'vlan307': [{u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:4d:43:3d', u'OS-EXT-IPS:type': u'fixed', u'addr': u'172.25.5.248', u'version': 4}]},
                     u'config_drive': u'',
                     u'created': u'2016-03-02T13:01:47Z',
                     u'flavor': {u'id': u'2', u'links': [{u'href': u'http://ctrl-liberty.nuvolacsi.it:8774/b570fe9ea2c94cb8ba72fe07fa034b62/flavors/2', u'rel': u'bookmark'}]},
                     u'hostId': u'230619bf5e5797da6fd87a623218a1ad1f6aa2cfc4748f079f1f3a73',
                     u'id': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                     u'image': u'',
                     u'key_name': None,
                     u'links': [{u'href': u'http://ctrl-liberty.nuvolacsi.it:8774/v2.1/b570fe9ea2c94cb8ba72fe07fa034b62/servers/b3140030-3a1b-44e7-8bfe-46a4834b4ff3', u'rel': u'self'},
                                {u'href': u'http://ctrl-liberty.nuvolacsi.it:8774/b570fe9ea2c94cb8ba72fe07fa034b62/servers/b3140030-3a1b-44e7-8bfe-46a4834b4ff3', u'rel': u'bookmark'}],
                     u'metadata': {},
                     u'name': u'vlan307-centos72',
                     u'os-extended-volumes:volumes_attached': [{u'id': u'04a619d8-8515-47e3-b676-be61d61ff1f3'}],
                     u'progress': 0,
                     u'security_groups': [{u'name': u'default'}],
                     u'status': u'ACTIVE',
                     u'tenant_id': u'ad576ba1da5344a992463639ca4abf61',
                     u'updated': u'2016-05-02T12:58:17Z',
                     u'user_id': u'c53dbf98272b465fa4663ff530b11ed1'}, .., ]      
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        query = {}
        path = '/servers'
        if detail is True:
            path = '/servers/detail'

        if image is not None:
            query['image'] = image
        if flavor is not None:
            query['flavor'] = flavor
        if status is not None:
            query['status'] = status
        if host is not None:
            query['host'] = host
        if limit is not None:
            query['limit'] = limit
            query['marker'] = marker
        if all_tenants is True:
            query['all_tenants'] = 1
                
        path = '%s?%s' % (path, urlencode(query))           
            
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack servers: %s' % truncate(res))
        return res[0]['servers']
        
    def get(self, oid=None, name=None):
        """
        :param oid: server id
        :param name: Filters the response by a server name, as a string.
                     You can use regular expressions in the query. For example, 
                     the ?name=bob regular expression returns both bob and bobb. 
                     If you must match on only bob, you can use a regular 
                     expression that matches the syntax of the underlying 
                     database server that is implemented for Compute, such as 
                     MySQL or PostgreSQL.
        :return: Ex:{u'OS-DCF:diskConfig': u'AUTO',
                     u'OS-EXT-AZ:availability_zone': u'nova',
                     u'OS-EXT-SRV-ATTR:host': u'comp-liberty2-kvm.nuvolacsi.it',
                     u'OS-EXT-SRV-ATTR:hypervisor_hostname': u'comp-liberty2-kvm.nuvolacsi.it',
                     u'OS-EXT-SRV-ATTR:instance_name': u'instance-00000471',
                     u'OS-EXT-STS:power_state': 1,
                     u'OS-EXT-STS:task_state': None,
                     u'OS-EXT-STS:vm_state': u'active',
                     u'OS-SRV-USG:launched_at': u'2016-03-02T13:02:58.000000',
                     u'OS-SRV-USG:terminated_at': None,
                     u'accessIPv4': u'',
                     u'accessIPv6': u'',
                     u'addresses': {u'vlan307': [{u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:4d:43:3d', u'OS-EXT-IPS:type': u'fixed', u'addr': u'172.25.5.248', u'version': 4}]},
                     u'config_drive': u'',
                     u'created': u'2016-03-02T13:01:47Z',
                     u'flavor': {u'id': u'2', u'links': [{u'href': u'http://ctrl-liberty.nuvolacsi.it:8774/b570fe9ea2c94cb8ba72fe07fa034b62/flavors/2', u'rel': u'bookmark'}]},
                     u'hostId': u'230619bf5e5797da6fd87a623218a1ad1f6aa2cfc4748f079f1f3a73',
                     u'id': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                     u'image': u'',
                     u'key_name': None,
                     u'links': [{u'href': u'http://ctrl-liberty.nuvolacsi.it:8774/v2.1/b570fe9ea2c94cb8ba72fe07fa034b62/servers/b3140030-3a1b-44e7-8bfe-46a4834b4ff3', u'rel': u'self'},
                                {u'href': u'http://ctrl-liberty.nuvolacsi.it:8774/b570fe9ea2c94cb8ba72fe07fa034b62/servers/b3140030-3a1b-44e7-8bfe-46a4834b4ff3', u'rel': u'bookmark'}],
                     u'metadata': {},
                     u'name': u'vlan307-centos72',
                     u'os-extended-volumes:volumes_attached': [{u'id': u'04a619d8-8515-47e3-b676-be61d61ff1f3'}],
                     u'progress': 0,
                     u'security_groups': [{u'name': u'default'}],
                     u'status': u'ACTIVE',
                     u'tenant_id': u'ad576ba1da5344a992463639ca4abf61',
                     u'updated': u'2016-05-02T12:58:17Z',
                     u'user_id': u'c53dbf98272b465fa4663ff530b11ed1'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '/servers/%s' % oid
        elif name is not None:
            path = '/servers/detail?name=%s&all_tenants=1' % name
        else:
            raise OpenstackError('Specify at least project id or name')
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack server: %s' % truncate(res))
        if oid is not None:
            server = res[0]['server']
        elif name is not None:
            server = res[0]['servers'][0]
        
        return server  
    
    def create(self, name, flavor, accessipv4=None, accessipv6=None,
               networks=[], boot_volume_id=None, adminpass=None, description='',
               metadata=None, image=None, security_groups=["default"],
               personality=None, user_data=None, availability_zone=None):
        """Create server
        
        :param name: The server name.
        :param description: [TODO] A free form description of the server. Limited to 
                            255 characters in length. 
        :param flavor: The flavor reference, as a UUID or full URL, for the 
                       flavor for your server instance.
        :param image: The UUID of the image to use for your server instance. 
                      This is not required in case of boot from volume. In all 
                      other cases it is required and must be a valid UUID 
                      otherwise API will return 400. [optional]
        :param accessipv4: [TODO] IPv4 address that should be used to access 
                           this server. [optional]
        :param accessipv6: [TODO] IPv6 address that should be used to access 
                           this server. [optional]
        :param networks: A networks object. Required parameter when there are 
                         multiple networks defined for the tenant. When you do 
                         not specify the networks parameter, the server attaches 
                         to the only network created for the current tenant. 
                         Optionally, you can create one or more NICs on the 
                         server. To provision the server instance with a NIC for 
                         a network, specify the UUID of the network in the uuid 
                         attribute in a networks object. To provision the server 
                         instance with a NIC for an already existing port, 
                         specify the port-id in the port attribute in a networks 
                         object.
                         Starting in microversion 2.32, it's possible to 
                         optionally assign an arbitrary tag to a virtual network 
                         interface, specify the tag attribute in the network 
                         object. An interface's tag is exposed to the guest in 
                         the metadata API and the config drive and is associated 
                         to hardware metadata for that network interface, such 
                         as bus (ex: PCI), bus address (ex: 0000:00:02.0), and 
                         MAC address.
                         - networks.fixed_ip [optional] : A fixed IPv4 address 
                           for the NIC. Valid with a neutron or nova-networks network.
                                              
                         Ex: [{
                                u'uuid':..,
                                u'fixed_ip':..,
                                u'tag':..
                              }],
        :param boot_volume_id: uuid of the root volume used to boot server.
        :param adminpass: [TODO] The administrative password of the server. 
                          [optional]
        :param metadata: Metadata key and value pairs. The maximum size of the 
                         metadata key and value is 255 bytes each. [optional]
                         Ex. {'My Server Name':'Apache1'} 
        :param security_groups: One or more security groups. Specify the name of 
                                the security group in the name attribute. If you 
                                omit this attribute, the API creates the server 
                                in the default security group. [optional]
                                Ex. [{u'name':u''default}]
        :param personality: [TODO] The file path and contents, text only, to 
                            inject into the server at launch. The maximum size 
                            of the file path data is 255 bytes. The maximum 
                            limit is the number of allowed bytes in the decoded, 
                            rather than encoded, data. [optional]
                            Ex. [{'path':'/etc/banner.txt',
                                  'ontents':'ICAgICAgDQoiQSBjb..'}]
        :param user_data: [TODO] Configuration information or scripts to use 
                          upon launch. Must be Base64 encoded.[optional]
                          Ex. "IyEvYmluL2Jhc2gKL2Jpbi9zdQpl..."
        :param availability_zone: The availability zone from which to launch 
                                  the server. When you provision resources, you 
                                  specify from which availability zone you want 
                                  your instance to be built. Typically, you use 
                                  availability zones to arrange OpenStack compute 
                                  hosts into logical groups. An availability 
                                  zone provides a form of physical isolation and 
                                  redundancy from other availability zones. For 
                                  instance, if some racks in your data center 
                                  are on a separate power source, you can put 
                                  servers in those racks in their own availability 
                                  zone. Availability zones can also help separate 
                                  different classes of hardware. By segregating 
                                  resources into availability zones, you can 
                                  ensure that your application resources are 
                                  spread across disparate machines to achieve 
                                  high availability in the event of hardware or 
                                  other failure. [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            u'name': name,
            #u'description':description,
            u'flavorRef': flavor,
            u'security_groups': [],
            u'networks':[],     
        }

        if adminpass is not None:
            data[u'adminPass'] = adminpass 
            
        if accessipv4 is not None:
            data[u'accessIPv4'] = accessipv4             

        if accessipv6 is not None:
            data[u'accessIPv6'] = accessipv6 

        if image is not None:
            data[u'imageRef'] = image        
        
        if metadata is not None:
            data[u'metadata'] = metadata
            
        if user_data is not None:
            data[u'user_data'] = user_data
        
        if availability_zone is not None:
            data[u'availability_zone'] = availability_zone
            
        if personality is not None:
            data[u'personality'] = personality            
        
        for security_group in security_groups:
            data[u'security_groups'].append({u'name':security_group})        
        
        for network in networks:
            data[u'networks'].append({u'uuid':network})
            
        if boot_volume_id is not None:
            data[u'block_device_mapping_v2'] = [{u'uuid':boot_volume_id,
                                                 u'device_name':u'/dev/sda',
                                                 u'source_type':u'volume',
                                                 u'destination_type':u'volume',
                                                 u'boot_index':0}]
        path = u'/servers'
        res = self.client.call(path, u'POST', data=json.dumps({u'server':data}), 
                               token=self.manager.identity.token)
        self.logger.debug(u'Create openstack server: %s' % truncate(res))
        return res[0][u'server']    

    def update(self, oid):
        """Updates the editable attributes of a server.
        
        TODO
        :param oid: server id
        :return:
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s' % oid
        res = self.client.call(path, 'PUT', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack server: %s' % truncate(res))
        return res[0]['server']
    
    def delete(self, oid):
        """Deletes a server.
        
        TODO
        :param oid: server id
        :retunr: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s' % oid
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack server: %s' % truncate(res))
        return res[0]
    
    #
    # information
    #
    def get_state(self, state):
        """Get server power status mapped to vsphere server status. 

        :param int state: index of status in enum 
                       [InfoNoState, 
                        InfoRunning,
                        InfoBlocked,
                        InfoPaused,
                        InfoShutdown,
                        InfoShutoff,
                        InfoCrashed]
        """
        status = [u'noState', u'poweredOn', u'blocked', u'suspended', 
                  u'poweredOff', u'poweredOff', u'crashed']
        return status[int(state)]
    
    def info(self, server, flavor_idx=None, volume_idx=None, image_idx=None):
        """Get server info
        
        :param server: server object obtained from api request
        :param flavor_idx: index of flavor object obtained from api request
        :param volume_idx: index of volume object obtained from api request
        :param image_idx: index of image object obtained from api request
        :return: dict like
        
            {u'cpu': 1,
             u'hostname': None,
             u'ip_address': [],
             u'memory': 2048,
             u'os': u'',
             u'state': u'poweredOff',
             u'template': None,
             u''disk':}        
        """
        try:
            meta = None

            # get flavor info
            if flavor_idx is not None:
                flavor_id = server[u'flavor'][u'id']
                flavor = flavor_idx[flavor_id]
                memory = flavor[u'ram'] or None
                cpu = flavor[u'vcpus'] or None

            # get volume info
            disk = 0
            if volume_idx is not None:
                volumes_ids = server[u'os-extended-volumes:volumes_attached']
                volumes = []
                boot_volume = None
                for volumes_id in volumes_ids:
                    try:
                        vol = volume_idx[volumes_id[u'id']]
                        disk += int(vol[u'size'])
                        volumes.append(vol)
                        if vol[u'bootable'] == u'true':
                            boot_volume = vol
                    except:
                        self.logger.warn(u'Server %s has not boot volume' % 
                                         server[u'name'])
                
            if image_idx is not None:
                # get image from boot volume         
                if server[u'image'] is None \
                    or server[u'image'] == u'' \
                    and boot_volume is not None:
                    meta = boot_volume[u'volume_image_metadata']
                
                # get image
                elif server[u'image'] is not None and server[u'image'] != u'':
                    image = image_idx[server[u'image'][u'id']]
                    meta = image[u'metadata']

            os = u''
            if meta is not None:
                try:
                    os_distro = meta[u'os_distro']
                    os_version = meta[u'os_version']
                    os = u'%s %s' % (os_distro, os_version)
                except:
                    os = u''

            # gte ip addresses
            ipaddresses = []
            for ips in server[u'addresses'].values():
                for ip in ips:
                    ipaddresses.append(ip[u'addr'])

            data = {
                u'os':os,
                u'memory':memory,
                u'cpu':cpu,
                u'state':self.get_state(server[u'OS-EXT-STS:power_state']),
                u'template':None,
                u'hostname':None,
                u'ip_address':ipaddresses,
                u'disk':disk
            }  
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = {}
        
        return data

    def detail(self, server):
        """Get server detail
        
        :param server: server object obtained from api request
        :return: dict like
        
            {u'date': {u'created': u'2016-10-19T12:26:30Z', 
                       u'launched': u'2016-10-19T12:26:39.000000', 
                       u'terminated': None, 
                       u'updated': u'2016-10-19T12:26:39Z'},
             u'flavor': {u'cpu': 1, u'id': u'2', u'memory': 2048},
             u'metadata': {},
             u'networks': [{u'name':None,
                            u'fixed_ips': [{u'ip_address': u'172.25.5.156', 
                                            u'subnet_id': u'54fea9ab-9ba4-4c99-a729-f7ce52cae8fd'}],
                            u'mac_addr': u'fa:16:3e:17:4d:87',
                            u'net_id': u'dc8771c3-f76e-4da6-bb59-e25e67ebb8bb',
                            u'port_id': u'033e6918-13fc-4af1-818d-1bd65e0d3800',
                            u'port_state': u'ACTIVE'}],
             u'opsck:build_progress': 0,
             u'opsck:config_drive': u'',
             u'opsck:disk_config': u'MANUAL',
             u'opsck:image': u'',
             u'opsck:internal_name': u'instance-00000a44',
             u'opsck:key_name': None,
             u'opsck:opsck_user_id': u'730cd1699f144275811400d41afa7645',
             u'os': u'CentOS 7',
             u'state': u'poweredOn',
             u'volumes': [{u'bootable': u'true',
                           u'format': u'qcow2',
                           u'id': u'83935084-f323-4e31-9a2c-478f2826b46f',
                           u'mode': u'rw',
                           u'name': u'server-49405-root-volume',
                           u'size': 20,
                           u'storage': u'cinder-liberty.nuvolacsi.it#RBD',
                           u'type': None}]}        
        """
        try:
            meta = None

            # get flavor info
            flavor_id = server[u'flavor'][u'id']
            flavor = self.manager.flavor.get(oid=flavor_id)
            memory = flavor[u'ram'] or None
            cpu = flavor[u'vcpus'] or None

            # get volume info
            volumes_ids = server[u'os-extended-volumes:volumes_attached']
            volumes = []
            boot_volume = None
            for volumes_id in volumes_ids:
                try:
                    vol = self.manager.volume.get(volumes_id[u'id'])
                    volumes.append(vol)
                    if vol[u'bootable'] == u'true':
                        boot_volume = vol
                except:
                    self.logger.warn(u'Server %s has not boot volume' % 
                                     server[u'name'])
                
            # get image from boot volume         
            if server[u'image'] is None \
                or server[u'image'] == u'' \
                and boot_volume is not None:
                meta = boot_volume[u'volume_image_metadata']
            
            # get image
            elif server[u'image'] is not None and server[u'image'] != u'':
                image = self.manager.image.get(oid=server[u'image'][u'id'])
                meta = image[u'metadata']

            os = u''
            if meta is not None:
                try:
                    os_distro = meta[u'os_distro']
                    os_version = meta[u'os_version']
                    os = u'%s %s' % (os_distro, os_version)
                except:
                    os = u''
                    
            # networks
            networks = self.get_port_interfaces(server[u'id'])
            
            # volumes
            server_volumes = []
            for volume in volumes:
                server_volumes.append({u'id':volume[u'id'],
                                       u'type':volume[u'volume_type'],
                                       u'bootable':volume[u'bootable'],
                                       u'name':volume[u'name'],
                                       u'size':volume[u'size'],
                                       u'format':volume[u'volume_image_metadata'][u'disk_format'],
                                       u'mode':volume[u'metadata'][u'attached_mode'],
                                       u'storage':volume[u'os-vol-host-attr:host']})
            
            data = {
                u'os':os,
                u'state':self.get_state(server[u'OS-EXT-STS:power_state']),
                u'flavor':{
                    u'id':flavor[u'id'],
                    u'memory':memory,
                    u'cpu':cpu,
                },
                u'networks':networks,
                u'volumes':server_volumes,
                u'date':{u'created':server[u'created'],
                         u'updated':server[u'updated'],
                         u'launched':server[u'OS-SRV-USG:launched_at'],
                         u'terminated':server[u'OS-SRV-USG:terminated_at']},
                u'metadata':server[u'metadata'],
                
                u'opsck:internal_name':server[u'OS-EXT-SRV-ATTR:instance_name'],
                u'opsck:opsck_user_id':server[u'user_id'],
                u'opsck:key_name':server[u'key_name'],
                u'opsck:build_progress':get_value(server, u'progress', None),
                u'opsck:image':server[u'image'],
                u'opsck:disk_config':server[u'OS-DCF:diskConfig'],
                u'opsck:config_drive':server[u'config_drive'],           
            }

            return data
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = {}
        
        return data     
    
    @watch
    def security_groups(self, oid):
        """Get server secuirity groups
        
        :param oid: server id
        :return: dict like
        
            [{u'description': u'Default security group',
              u'id': u'1c3537ee-931c-4eb0-9d60-345baaa5a5ed',
              u'name': u'default',
              u'rules': [{u'from_port': None,
                          u'group': {},
                          u'id': u'2b5f88f7-9a17-4439-97df-839d6cf7a0e8',
                          u'ip_protocol': None,
                          u'ip_range': {u'cidr': u'158.102.160.0/24'},
                          u'parent_group_id': u'1c3537ee-931c-4eb0-9d60-345baaa5a5ed',
                          u'to_port': None}],
              u'tenant_id': u'8337fff8a6bd4ae6b5f2255af2526212'}]        
        """
        try:
            path = u'/servers/%s/os-security-groups' % oid
            res = self.client.call(path, u'GET', data=u'', 
                                   token=self.manager.identity.token)
            self.logger.debug(u'Get openstack server security groups: %s' % truncate(res))
            return res[0][u'security_groups']
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = []
        return res
    
    @watch
    def runtime(self, server):
        """Server runtime info
        """
        try: 
            res = {u'boot_time':server[u'OS-SRV-USG:launched_at'],
                   u'availability_zone':{u'name':server[u'OS-EXT-AZ:availability_zone']},                   
                   u'host':{u'id':server[u'hostId'],
                            u'name':server[u'OS-EXT-SRV-ATTR:host']},
                   u'server_state':server[u'OS-EXT-STS:vm_state'],
                   u'task':{server[u'OS-EXT-STS:task_state']}}
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = {}
        
        return res    
    
    @watch
    def diagnostics(self, oid):
        """Shows basic usage data for a server
        
        :param oid: server id
        :return: Ex.{u'cpu0_time': 1040290000000L,
                     u'memory': 2097152,
                     u'memory-actual': 2097152,
                     u'memory-available': 2049108,
                     u'memory-major_fault': 537,
                     u'memory-minor_fault': 2631107,
                     u'memory-rss': 600412,
                     u'memory-swap_in': 0,
                     u'memory-swap_out': 0,
                     u'memory-unused': 1715532,
                     u'tap8ce64ffc-26_rx': 114184031,
                     u'tap8ce64ffc-26_rx_drop': 0,
                     u'tap8ce64ffc-26_rx_errors': 0,
                     u'tap8ce64ffc-26_rx_packets': 1287786,
                     u'tap8ce64ffc-26_tx': 55137281,
                     u'tap8ce64ffc-26_tx_drop': 0,
                     u'tap8ce64ffc-26_tx_errors': 0,
                     u'tap8ce64ffc-26_tx_packets': 267402,
                     u'vda_errors': -1,
                     u'vda_read': 138479104,
                     u'vda_read_req': 8413,
                     u'vda_write': 772407296,
                     u'vda_write_req': 80243}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s/diagnostics' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Shows basic usage data for server %s: %s' % 
                          (oid, truncate(res)))
        return res[0]   
    
    def ping(self, oid):
        """Ping a server
        TODO: does not work
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-fping/%s/' % oid
        path = '/os-fping?all_tenants=1&include=%s' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Ping server %s: %s' % 
                          (oid, truncate(res)))
        return res[0]     
    
    #
    # network
    #    
    def get_port_interfaces(self, oid):
        """List port interfaces for a server
        
        :param oid: server id
        :return: [{u'name':None,
                   u'fixed_ips': [{u'ip_address': u'172.25.5.248', 
                                   u'subnet_id': u'3579e3f7-03ea-44f1-9384-f9f9e0c015de'}],
                   u'mac_addr': u'fa:16:3e:4d:43:3d',
                   u'net_id': u'45b69826-7909-4e37-8c01-85c6c8e63613',
                   u'port_id': u'8ce64ffc-26a2-40e8-af8a-0fa8a4e3aedc',
                   u'port_state': u'ACTIVE'}]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s/os-interface' % oid
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('List port interfaces for server %s: %s' % 
                          (oid, truncate(res)))
        nets = res[0]['interfaceAttachments']
        for item in nets:
            item[u'name'] = None
        return nets
    
    def add_port_interfaces(self, oid, net_id, fixed_ips=None):
        """Add port interface to a server
        
        :param oid: server id
        :param net_id: id of the network to add
        :param fixed_ips: Fixed IP addresses with subnet IDs. [optional]
                          Ex. {u'ip_address': u'172.25.5.248', 
                               u'subnet_id': u'3579e3f7-03ea-44f1-9384-f9f9e0c015de'}
        :return: {u'fixed_ips': [{u'ip_address': u'172.25.4.242', 
                                  u'subnet_id': u'f375e490-1103-4c00-9803-2703e3165271'}],
                  u'mac_addr': u'fa:16:3e:72:1f:6b',
                  u'net_id': u'40803c62-f4b1-4afb-bd94-f773a5c70f7b',
                  u'port_id': u'c4bc3504-bd3b-416f-b924-e40cd0388877',
                  u'port_state': u'DOWN'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "interfaceAttachment": {
                "net_id": net_id
            }
        }
        if fixed_ips is not None:
            data["interfaceAttachment"]["fixed_ips"] = fixed_ips
        path = '/servers/%s/os-interface' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Add port interface for server %s: %s' % 
                          (oid, truncate(res)))
        return res[0]['interfaceAttachment']
    
    def remove_port_interfaces(self, oid, port_id):
        """Remove port interface from a server
        
        :param oid: server id
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s/os-interface/%s' % (oid, port_id)
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Remove port interface %s for server %s: %s' % 
                          (port_id, oid, truncate(res)))
        return res[0]        
    
    def get_virtual_interfaces(self, oid):
        """List virtual interfaces for a server
        TODO: does not work
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s/os-virtual-interfaces' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('List virtual interfaces for server %s: %s' % 
                          (oid, truncate(res)))
        return res[0]
    
    def get_ips(self, oid):
        """List ip addresses a server

        :param oid: server id
        :return: {u'addresses': {u'vlan307': [{u'addr': u'172.25.5.248', u'version': 4}]}}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s/ips' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('List ip addresses for server %s: %s' % 
                          (oid, truncate(res)))
        return res[0]        
    
    #
    # volume
    #    
    def get_volumes(self, oid):
        """List volumes for a server

        :param oid: server id
        :return: [{u'device': u'/dev/vda', 
                   u'id': u'04a619d8-8515-47e3-b676-be61d61ff1f3', 
                   u'serverId': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3', 
                   u'volumeId': u'04a619d8-8515-47e3-b676-be61d61ff1f3'},
                  {u'device': u'/dev/vdb', 
                   u'id': u'930d6924-ebe8-497c-ada3-85d19144aa67', 
                   u'serverId': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3', 
                   u'volumeId': u'930d6924-ebe8-497c-ada3-85d19144aa67'}]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s/os-volume_attachments' % oid
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('List volumes for server %s: %s' % 
                          (oid, truncate(res)))
        return res[0]['volumeAttachments']
    
    def add_volume(self, oid, volume_id):
        """Add volume to a server

        :param oid: server id
        :param volume_id: volume id
        :return: {u'device': u'/dev/vdb', 
                  u'id': u'930d6924-ebe8-497c-ada3-85d19144aa67', 
                  u'serverId': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3', 
                  u'volumeId': u'930d6924-ebe8-497c-ada3-85d19144aa67'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "volumeAttachment": {
                "volumeId": volume_id,
            }
        }
        path = '/servers/%s/os-volume_attachments' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Add volume %s to server %s: %s' % 
                          (volume_id, oid, truncate(res)))
        return res[0]['volumeAttachment']    
    
    def remove_volume(self, oid, volume_id):
        """Remove volume from a server

        :param oid: server id
        :param volume_id: volume id
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s/os-volume_attachments/%s' % (oid, volume_id)
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Remove volume %s from server %s: %s' % 
                          (volume_id, oid, truncate(res)))
        return res[0]
    
    #
    # metadata
    #
    def get_metadata(self, oid):
        """Get server metadata
        
        :param oid: server id
        :return: {"foo": "Foo Value"}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/servers/%s/metadata' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('get server %s metadata: %s' % 
                          (oid, truncate(res)))
        return res[0]['metadata']
    
    def set_metadata_key(self, oid):
        """Set server metadata
        TODO:
        :param oid: server id
        :return: {"foo": "Foo Value"}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        pass
    
    def delete_metadata_key(self, oid):
        """Delete server metadata
        TODO:
        :param oid: server id
        :return: {"foo": "Foo Value"}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        pass    
        
    #
    # actions
    # 
    def get_actions(self, oid, action_id=None):
        """Lists actions for a server or get action details if action_id
        is been specified
        
        :param oid: server id
        :param action_id: action id
        :return: Action list
        
                [{u'action': u'start',
                  u'instance_uuid': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                  u'message': None,
                  u'project_id': u'ad576ba1da5344a992463639ca4abf61',
                  u'request_id': u'req-3e5728bd-1517-4caf-aa23-4f63aaa9e0d3',
                  u'start_time': u'2016-05-02T12:58:15.000000',
                  u'user_id': u'730cd1699f144275811400d41afa7645'},
                 {u'action': u'stop',
                  u'instance_uuid': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                  u'message': None,
                  u'project_id': u'ad576ba1da5344a992463639ca4abf61',
                  u'request_id': u'req-c0d8c0f1-c723-424c-9284-db576639085f',
                  u'start_time': u'2016-05-02T07:46:25.000000',
                  u'user_id': u'730cd1699f144275811400d41afa7645'},
                 {u'action': u'create',
                  u'instance_uuid': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                  u'message': None,
                  u'project_id': u'ad576ba1da5344a992463639ca4abf61',
                  u'request_id': u'req-49dc6673-186a-4fd8-97d4-f5be0f37bb7c',
                  u'start_time': u'2016-03-02T13:01:14.000000',
                  u'user_id': u'c53dbf98272b465fa4663ff530b11ed1'}]
                  
                Action details
                
                {u'action': u'start',
                 u'events': [{u'event': u'compute_start_instance', 
                              u'finish_time': u'2016-05-02T12:58:17.000000', 
                              u'result': u'Success', 
                              u'start_time': u'2016-05-02T12:58:16.000000', 
                              u'traceback': None}],
                 u'instance_uuid': u'b3140030-3a1b-44e7-8bfe-46a4834b4ff3',
                 u'message': None,
                 u'project_id': u'ad576ba1da5344a992463639ca4abf61',
                 u'request_id': u'req-3e5728bd-1517-4caf-aa23-4f63aaa9e0d3',
                 u'start_time': u'2016-05-02T12:58:15.000000',
                 u'user_id': u'730cd1699f144275811400d41afa7645'}
                 
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if action_id is None:
            path = '/servers/%s/os-instance-actions' % oid
            key = 'instanceActions'
        else:
            path = '/servers/%s/os-instance-actions/%s' % (oid, action_id)
            key = 'instanceAction'
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('get openstack server %s actions: %s' % 
                          (oid, truncate(res)))
        return res[0][key]
    
    def start(self, oid):
        """Start server
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"os-start": None}
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Start openstack server: %s' % truncate(res))
        return res[0]
    
    def stop(self, oid):
        """Stop server
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"os-stop": None}
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Stop openstack server: %s' % truncate(res))
        return res[0]
    
    def reboot(self, oid):
        """Reboot server
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "reboot": {
                "type": "HARD"
            }
        }
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Reboot openstack server: %s' % truncate(res))
        return res[0]
    
    def pause(self, oid):
        """Pause server
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"pause": None}
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Pause openstack server: %s' % truncate(res))
        return res[0]
    
    def unpause(self, oid):
        """Unpauses a paused server and changes its status to ACTIVE.
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"unpause": None}
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Unpause openstack server: %s' % truncate(res))
        return res[0]
    
    def lock(self, oid):
        """Lock server
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"lock": None}
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Lock openstack server: %s' % truncate(res))
        return res[0]
    
    def unlock(self, oid):
        """Unlock server
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"unlock": None}
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Unlock openstack server: %s' % truncate(res))
        return res[0]
    
    def set_flavor(self, oid, flavor):
        """Resize a server changing the flavor. A successfully resized server 
        shows a VERIFY_RESIZE status, RESIZED VM status, and finished migration 
        status. If you set the resize_confirm_window option of the Compute 
        service to an integer value, the Compute service automatically 
        confirms the resize operation after the set interval in seconds.
        
        :param oid: server id
        :param flavro: flavor id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "resize": {
                "flavorRef": flavor
            }
        }
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Pause openstack server: %s' % truncate(res))
        return res[0]
    
    def add_security_group(self, oid, security_group):
        """Add security group
        
        :param oid: server id
        :param security_group: security_group name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "addSecurityGroup": {
                "name": security_group
            }
        }
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Add security group %s to openstack server %s: %s' % 
                          (security_group, oid, truncate(res)))
        return res[0]
    
    def remove_security_group(self, oid, security_group):
        """Remove security group
        
        :param oid: server id
        :param security_group: security_group name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "removeSecurityGroup": {
                "name": security_group
            }
        }
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Remove security group %s from openstack server %s: %s' % 
                          (security_group, oid, truncate(res)))
        return res[0]
    
    def get_vnc_console(self, oid):
        """Get vnc console
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "os-getVNCConsole": {
                "type": "novnc"
            }
        }
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack server %s vnc console : %s' % 
                          (oid, truncate(res)))
        resp = res[0]['console']
        return resp

    def create_backup(self, oid, name, bck_type, bck_freq):
        """Create server backup
        
        TODO:
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "createBackup": {
                "name": name,
                "backup_type": bck_type,
                "rotation": bck_freq
            }
        }
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('create openstack server %s backup rule : %s' % 
                          (oid, truncate(res)))
        return res[0]['server']
    
    def reset_state(self, oid, state="active"):
        """Reset server state
        
        :param oid: server id
        :param state: new server state [default=active]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "os-resetState": {
                "state": state
            }
        }
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Reset openstack server %s state : %s' % 
                          (oid, truncate(res)))
        return res[0]['server']
    
    def migrate(self, oid):
        """Migrate server
        
        :param oid: server id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "migrate": None
        }
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Migrate openstack server %s : %s' % 
                          (oid, truncate(res)))
        return res
    
    def live_migrate(self, oid, host=None):
        """Migrate server
        
        :param oid: server id
        :param host: host name [default=None]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "os-migrateLive": {
                "block_migration": False,
                "disk_over_commit": False,
                #"force": False
                "host":host,
            }
        }
        #if host is not None:
        #    data["os-migrateLive"]["host"] = host
        
        path = '/servers/%s/action' % oid
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Live migrate openstack server %s : %s' % 
                          (oid, truncate(res)))
        return res
    
class OpenstackVolume(object):
    """
    Volume Status:
        creating - The volume is being created.
        available - The volume is ready to attach to an instance.
        attaching - The volume is attaching to an instance.
        in-use - The volume is attached to an instance.
        deleting - The volume is being deleted.
        error - A volume creation error occurred.
        error_deleting - A volume deletion error occurred.
        backing-up - The volume is being backed up.
        restoring-backup - A backup is being restored to the volume.
        error_restoring - A backup restoration error occurred.
        error_extending - An error occurred while attempting to extend a volume.
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        uri = manager.endpoint('cinderv2')
        self.client = OpenstackClient(uri, manager.proxy)

    def list(self, detail=False, tenant=None, limit=None, marker=None, 
             all_tenants=True):
        """List volumes
        
        :param tenant: tenant id
        :param limit:  Requests a page size of items. Returns a number of items 
                       up to a limit value. Use the limit parameter to make an 
                       initial limited request and use the ID of the last-seen 
                       item from the response as the marker parameter value in 
                       a subsequent limited request.
        :param marker: The ID of the last-seen item. Use the limit parameter 
                       to make an initial limited request and use the ID of the 
                       last-seen item from the response as the marker parameter 
                       value in a subsequent limited request.        
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return a list of dictionaries (each one is a volume):
        [
            {
                "migration_status": null,
                "attachments": [
                    {
                        "server_id": "f4fda93b-06e0-4743-8117-bc8bcecd651b",
                        "attachment_id": "3b4db356-253d-4fab-bfa0-e3626c0b8405",
                        "host_name": null,
                        "volume_id": "6edbc2f4-1507-44f8-ac0d-eed1d2608d38",
                        "device": "/dev/vdb",
                        "id": "6edbc2f4-1507-44f8-ac0d-eed1d2608d38"
                    }
                ],
                "links": [
                    {
                        "href": "http://23.253.248.171:8776/v2/bab7d5c60cd04..",
                        "rel": "self"
                    },
                    {
                        "href": "http://23.253.248.171:8776/bab7d5c60cd041a0..",
                        "rel": "bookmark"
                    }
                ],
                "availability_zone": "nova",
                "os-vol-host-attr:host": "difleming@lvmdriver-1#lvmdriver-1",
                "encrypted": false,
                "os-volume-replication:extended_status": null,
                "replication_status": "disabled",
                "snapshot_id": null,
                "id": "6edbc2f4-1507-44f8-ac0d-eed1d2608d38",
                "size": 2,
                "user_id": "32779452fcd34ae1a53a797ac8a1e064",
                "os-vol-tenant-attr:tenant_id": "bab7d5c60cd041a0a36f7c4b6e1dd978",
                "os-vol-mig-status-attr:migstat": null,
                "metadata": {
                    "readonly": "False",
                    "attached_mode": "rw"
                },
                "status": "in-use",
                "description": null,
                "multiattach": true,
                "os-volume-replication:driver_data": null,
                "source_volid": null,
                "consistencygroup_id": null,
                "os-vol-mig-status-attr:name_id": null,
                "name": "test-volume-attachments",
                "bootable": "false",
                "created_at": "2015-11-29T03:01:44.000000",
                "volume_type": "lvmdriver-1"
            },..
        ]
        """
        path = u'/volumes'
        if detail is True:
            path = u'/volumes/detail'        
        
        query = {}
        if tenant is not None:
            query[u'tenant_id'] = tenant
        if limit is not None:
            query[u'limit'] = limit
        if marker is not None:
            query[u'marker'] = marker
        if all_tenants is True:
            query[u'all_tenants'] = 1
        
        path = u'%s?%s' % (path, urlencode(query))
        
        res = self.client.call(path, u'GET', data=u'', 
                               token=self.manager.identity.token)
        self.logger.debug(u'Get openstack volumes: %s' % truncate(res))
        return res[0][u'volumes']
        
    def get(self, oid=None, name=None):
        """
        :param oid: volume id
        :param name: volume name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = u'/volumes/%s' % oid
        elif name is not None:
            path = u'/volumes/detail?name=%s' % name
        else:
            raise OpenstackError('Specify at least project id or name')
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack volume: %s' % truncate(res))
        if oid is not None:
            server = res[0]['volume']
        elif name is not None:
            server = res[0]['volumes'][0]
        
        return server    
    
    def create(self, size=None, availability_zone=None, source_volid=None, 
               description=None, multiattach=None, snapshot_id=None,
               name=None, imageRef=None, volume_type=None, metadata=None,
               source_replica=None, consistencygroup_id=None, 
               scheduler_hints=None, tenant_id=None):
        """Create a Volume
        
        :param size - int: The size of the volume, in gibibytes (GiB).
        :param availability_zone [optional] - string: The availability zone.
        :param source_volid [optional] - UUID: The UUID of the source volume. 
            The API creates a new volume with the same size as the source volume.
        :param description [optional] - string: The volume description.
        :param multiattach [optional] - boolean: To enable this volume to attach 
            to more than one server, set this value to true. Default is false.
        :param snapshot_id [optional] - UUID: To create a volume from an existing
            snapshot, specify the UUID of the volume snapshot. The volume is
            created in same availability zone and with same size as the snapshot.
        :param name [optional] - string: The volume name.
        :param imageRef [optional] - UUID: The UUID of the image from which you 
            want to create the volume. Required to create a bootable volume.
        :param volume_type [optional] - string: The volume type. To create an
            environment with multiple-storage back ends, you must specify a
            volume type. Block Storage volume back ends are spawned as children
            to cinder-volume, and they are keyed from a unique queue. They are
            named cinder- volume.HOST.BACKEND. For example, cinder-
            volume.ubuntu.lvmdriver. When a volume is created, the scheduler
            chooses an appropriate back end to handle the request based on the
            volume type. Default is None. For information about how to use
            volume types to create multiple-storage back ends, see Configure
            multiple-storage back ends.
        :param metadata [optional] - dict: One or more metadata key and value 
            pairs that are associated with the volume.
        :param source_replica [optional] - UUID: The UUID of the primary volume 
            to clone.
        :param consistencygroup_id [optional] - UUID: The UUID of the consistency 
            group.
        :param scheduler_hints [optional] - dict: The dictionary of data to send 
            to the scheduler.
        :param tenant_id: The UUID of the tenant in a multi-tenancy cloud.
        :raises OpenstackError: raise :class:`.OpenstackError`
        :return dictionary with the resource created
        
            {
                "status": "creating",
                "migration_status": null,
                "user_id": "0eea4eabcf184061a3b6db1e0daaf010",
                "attachments": [],
                "links": [
                    {
                        "href": "http://23.253.248.171:8776/v2/bab7d5c..",
                        "rel": "self"
                    },
                    {
                        "href": "http://23.253.248.171:8776/bab7d5c60..",
                        "rel": "bookmark"
                    }
                ],
                "availability_zone": "nova",
                "bootable": "false",
                "encrypted": false,
                "created_at": "2015-11-29T03:01:44.000000",
                "description": null,
                "updated_at": null,
                "volume_type": "lvmdriver-1",
                "name": "test-volume-attachments",
                "replication_status": "disabled",
                "consistencygroup_id": null,
                "source_volid": null,
                "snapshot_id": null,
                "multiattach": false,
                "metadata": {},
                "id": "6edbc2f4-1507-44f8-ac0d-eed1d2608d38",
                "size": 2
            }
        """
        data={}

        if tenant_id is not None:
            data[u'tenant_id'] = tenant_id
        if size is not None:
            data[u'size'] = size
        if availability_zone is not None:
            data[u'availability_zone'] = availability_zone
        if source_volid is not None:
            data[u'source_volid'] = source_volid   
        if description is not None:
            data[u'description'] = description   
        if multiattach is not None:
            data[u'multiattach'] = multiattach   
        if snapshot_id is not None:
            data[u'snapshot_id'] = snapshot_id   
        if name is not None:
            data[u'name'] = name   
        if imageRef is not None:
            data[u'imageRef'] = imageRef   
        if volume_type is not None:
            data[u'volume_type'] = volume_type   
        if metadata is not None:
            data[u'metadata'] = metadata   
        if source_replica is not None:
            data[u'source_replica'] = source_replica   
        if consistencygroup_id is not None:
            data[u'consistencygroup_id'] = consistencygroup_id   
        if scheduler_hints is not None:
            data[u'scheduler_hints'] = scheduler_hints   

        path = u'/volumes'
        res = self.client.call(path, u'POST', data=json.dumps({u'volume':data}), 
                               token=self.manager.identity.token)
        self.logger.debug(u'Create openstack volume: %s' % truncate(res))
        return res[0][u'volume']    

    def update(self, oid):
        """TODO
        :param oid: volume id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/volumes/%s' % oid
        res = self.client.call(path, 'PUT', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack volume: %s' % truncate(res))
        return res[0]['volume']
    
    def delete(self, oid):
        """Deletes a volume.
        
        :param oid: volume id
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/volumes/%s' % oid
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack volume: %s' % truncate(res))
        return res[0]
    
    #
    # actions
    #
    
class OpenstackNetwork(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        uri = manager.endpoint('neutron')
        self.client = OpenstackClient(uri, manager.proxy)
        
        self.ver = '/v2.0'
        
        self.ip = OpenstackFloatingIp(self)
        self.subnet = OpenstackSubnet(self)
        self.port = OpenstackPort(self)
        self.router = OpenstackRouter(self)
        self.security_group = OpenstackSecurityGroup(self)

    def list(self, tenant=None, limit=None, marker=None, shared=None,
             segmentation_id=None, network_type=None, external=None,
             physical_network=None):
        """
        :param tenant: tenant id
        :param limit:  Requests a page size of items. Returns a number of items 
                       up to a limit value. Use the limit parameter to make an 
                       initial limited request and use the ID of the last-seen 
                       item from the response as the marker parameter value in 
                       a subsequent limited request.
        :param marker: The ID of the last-seen item. Use the limit parameter 
                       to make an initial limited request and use the ID of the 
                       last-seen item from the response as the marker parameter 
                       value in a subsequent limited request.
        :param segmentation_id: An isolated segment on the physical network. 
                                The network_type attribute defines the 
                                segmentation model. For example, if the 
                                network_type value is vlan, this ID is a vlan 
                                identifier. If the network_type value is gre, 
                                this ID is a gre key. [optional]
        :param network_type: The type of physical network that maps to this 
                             network resource. For example, flat, vlan, vxlan, 
                             or gre. [optional]
        :param external: Indicates whether this network can provide floating IPs 
                         via a router. [optional]
        :param shared: Indicates whether this network is shared 
                       across all projects. [optional]
        :param physical_network: The physical network where this network object 
                                 is implemented. The Networking API v2.0 does 
                                 not provide a way to list available physical 
                                 networks. For example, the Open vSwitch plug-in 
                                 configuration file defines a symbolic name 
                                 that maps to specific bridges on each Compute host.
        :return: Ex.
        
            [{u'admin_state_up': True,
              u'id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02',
              u'mtu': 0,
              u'name': u'public',
              u'port_security_enabled': True,
              u'provider:network_type': u'flat',
              u'provider:physical_network': u'public',
              u'provider:segmentation_id': None,
              u'router:external': True,
              u'shared': True,
              u'status': u'ACTIVE',
              u'subnets': [u'46620b60-76f6-4f1e-a754-dccfc50880c4'],
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}]
            
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/networks' % self.ver
        query = {}
        if tenant is not None:
            query['tenant_id'] = tenant
        if limit is not None:
            query['limit'] = limit
        if marker is not None:
            query['marker'] = marker
        if segmentation_id is not None:
            query['provider:segmentation_id'] = segmentation_id
        if network_type is not None:
            query['provider:network_type'] = network_type
        if external is not None:
            query['router:external'] = external
        if shared is not None:
            query['shared'] = shared
        if physical_network is not None:
            query['provider:physical_network'] = physical_network
            
        path = '%s?%s' % (path, urlencode(query))
        
        # get tenant network
        net = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        
        res = net[0]['networks']
        if tenant is not None:
            # get shared network
            path = '%s/networks?%s' % (self.ver, urlencode({u'shared':True}))
            shared = self.client.call(path, 'GET', data='', 
                                      token=self.manager.identity.token)
            if len(shared) > 0:
                res.extend(shared[0]['networks'])
        self.logger.debug('Get openstack networks: %s' % truncate(res))
        return res
        
    def get(self, oid=None, name=None):
        """
        :param oid: network id
        :param name: network name
        :return: Ex.

             {u'admin_state_up': True,
              u'id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02',
              u'mtu': 0,
              u'name': u'public',
              u'port_security_enabled': True,
              u'provider:network_type': u'flat',
              u'provider:physical_network': u'public',
              u'provider:segmentation_id': None,
              u'router:external': True,
              u'shared': True,
              u'status': u'ACTIVE',
              u'subnets': [u'46620b60-76f6-4f1e-a754-dccfc50880c4'],
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}

        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '%s/networks/%s' % (self.ver, oid)
        elif name is not None:
            path = '%s/networks?name=%s' % (self.ver, name)
        else:
            raise OpenstackError('Specify at least network id or name')
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack network: %s' % truncate(res))
        if oid is not None:
            server = res[0]['network']
        elif name is not None:
            server = res[0]['networks'][0]
        
        return server    
    
    def create(self, name, tenant_id, physical_network, shared=False, 
               qos_policy_id=None, external=False, segments=None,
               network_type='vlan', segmentation_id=None):
        """Creates a network.

        :param name str: The network name.
        :param shared bool: [default=false] Indicates whether this network is 
            shared across all tenants. By default, only administrative users can 
            change this value.
        :param tenant_id id: The UUID of the tenant that 
            owns the network. This tenant can be different from the tenant that 
            makes the create network request. However, only administrative users 
            can specify a tenant UUID other than their own. You cannot change 
            this value through authorization policies.
        :param qos_policy_id id: [optional] Admin-only. The UUID of the QoS 
            policy associated with this network. The policy will need to have 
            been created before the network to associate it with.
        :param external bool: [optional] Indicates whether this network 
            is externally accessible.
        :param segments list: [optional] A list of provider segment objects.
        :param physical_network str: [optional] The physical network 
            where this network object is implemented. The Networking API v2.0 
            does not provide a way to list available physical networks. For 
            example, the Open vSwitch plug-in configuration file defines a 
            symbolic name that maps to specific bridges on each Compute host.
        :param provider:network_type str: [default=vlan] The type of physical 
            network that maps to this network resource. For example, flat, vlan, 
            vxlan, or gre.
        :param provider:segmentation_id str: [optional] An isolated segment on 
            the physical network. The network_type attribute defines the 
            segmentation model. For example, if the network_type value is 
            vlan, this ID is a vlan identifier. If the network_type value is 
            gre, this ID is a gre key. 
        :return: Ex.
            {u'admin_state_up': True,
             u'id': u'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             u'mtu': 0,
             u'name': u'prova-net-01',
             u'port_security_enabled': True,
             u'provider:network_type': u'vlan',
             u'provider:physical_network': u'netall',
             u'provider:segmentation_id': 1900,
             u'router:external': False,
             u'shared': False,
             u'status': u'ACTIVE',
             u'subnets': [],
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}   
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "network": {
                "name": name,
                "tenant_id": tenant_id,
                "admin_state_up": True,
                "port_security_enabled": True,
                "shared": shared,
                "router:external": external,
                "provider:physical_network": physical_network,
                "provider:network_type": network_type,
            }
        }
        
        if qos_policy_id is not None:
            data['network']['qos_policy_id'] = qos_policy_id
        if segments is not None:
            data['network']['segments'] = segments
        if segmentation_id is not None:
            data['network']['provider:segmentation_id'] = segmentation_id              

        path = '%s/networks' % self.ver
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack network: %s' % truncate(res))
        return res[0]['network']    

    def update(self, oid, name=None, shared=None, qos_policy_id=None, 
               external=None, segments=None):
        """Updates a network.
        
        :param name str: [optional] The network name.
        :param shared bool: [optional] Indicates whether this network is 
            shared across all tenants. By default, only administrative users can 
            change this value.
        :param qos_policy_id id: [optional] Admin-only. The UUID of the QoS 
            policy associated with this network. The policy will need to have 
            been created before the network to associate it with.
        :param external bool: [optional] Indicates whether this network 
            is externally accessible.
        :return: Ex.
            {u'admin_state_up': True,
             u'id': u'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             u'mtu': 0,
             u'name': u'prova-net-02',
             u'port_security_enabled': True,
             u'provider:network_type': u'vlan',
             u'provider:physical_network': u'netall',
             u'provider:segmentation_id': 1900,
             u'router:external': False,
             u'shared': False,
             u'status': u'ACTIVE',
             u'subnets': [],
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "network": {
                "admin_state_up": True,
                "port_security_enabled": True
            }
        }
        
        if name is not None:
            data['network']['name'] = name
        if shared is not None:
            data['network']['shared'] = shared
        if external is not None:
            data['network']['router:external'] = external
        #if physical_network is not None:
        #    data['network']['provider:physical_network'] = physical_network
        #if network_type is not None:
        #    data['network']['provider:network_type'] = network_type        
        if qos_policy_id is not None:
            data['network']['qos_policy_id'] = qos_policy_id
        #if segmentation_id is not None:
        #    data['network']['provider:segmentation_id'] = segmentation_id
            
        path = '%s/networks/%s' % (self.ver, oid)
        res = self.client.call(path, 'PUT', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack network: %s' % truncate(res))
        return res[0]['network']
    
    def delete(self, oid):
        """Deletes a network and its associated resources.
        
        :param oid: network id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/networks/%s' % (self.ver, oid)
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack network: %s' % truncate(res))
        return res[0]
    
    #
    # actions
    #

class OpenstackSubnet(object):
    """
    """
    def __init__(self, network):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = network.manager
        uri = self.manager.endpoint('neutron')
        self.client = OpenstackClient(uri, self.manager.proxy)
        self.ver = network.ver

    def list(self, tenant=None, network=None, gateway_ip=None, cidr=None):
        """Lists subnets to which the tenant has access. 
        
        :param tenant: tenant id
        :param network: The ID of the attached network. 
        :param gateway_ip : The gateway IP address.
        :param cidr: The CIDR.
        :return: Ex.
            [{u'allocation_pools': [{u'end': u'172.25.4.250', u'start': u'172.25.4.201'}],
              u'cidr': u'172.25.4.0/24',
              u'dns_nameservers': [u'172.25.5.100'],
              u'enable_dhcp': True,
              u'gateway_ip': u'172.25.4.2',
              u'host_routes': [{u'destination': u'10.102.160.0/24', u'nexthop': u'172.25.4.1'}, {u'destination': u'158.102.160.0/24', u'nexthop': u'172.25.4.1'}],
              u'id': u'f375e490-1103-4c00-9803-2703e3165271',
              u'ip_version': 4,
              u'ipv6_address_mode': None,
              u'ipv6_ra_mode': None,
              u'name': u'sub306',
              u'network_id': u'40803c62-f4b1-4afb-bd94-f773a5c70f7b',
              u'subnetpool_id': None,
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'},...,
             ]    
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/subnets' % self.ver    
        
        query = {}
        if tenant is not None:
            query['tenant_id'] = tenant
        if network is not None:
            query['network_id'] = network
        if gateway_ip  is not None:
            query['gateway_ip '] = gateway_ip
        if cidr  is not None:
            query['cidr '] = cidr 
        path = '%s?%s' % (path, urlencode(query))
        
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack subnets: %s' % truncate(res))
        return res[0]['subnets']
        
    def get(self, oid=None, name=None):
        """Shows details for a subnet. 
        
        :param oid: network id
        :param name: network name
        :return: Ex.
             {u'allocation_pools': [{u'end': u'172.25.4.250', u'start': u'172.25.4.201'}],
              u'cidr': u'172.25.4.0/24',
              u'dns_nameservers': [u'172.25.5.100'],
              u'enable_dhcp': True,
              u'gateway_ip': u'172.25.4.2',
              u'host_routes': [{u'destination': u'10.102.160.0/24', u'nexthop': u'172.25.4.1'}, {u'destination': u'158.102.160.0/24', u'nexthop': u'172.25.4.1'}],
              u'id': u'f375e490-1103-4c00-9803-2703e3165271',
              u'ip_version': 4,
              u'ipv6_address_mode': None,
              u'ipv6_ra_mode': None,
              u'name': u'sub306',
              u'network_id': u'40803c62-f4b1-4afb-bd94-f773a5c70f7b',
              u'subnetpool_id': None,
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '%s/subnets/%s' % (self.ver, oid)
        elif name is not None:
            path = '%s/subnets?display_name=%s' % (self.ver, name)
        else:
            raise OpenstackError('Specify at least subnet id or name')
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack subnets: %s' % truncate(res))
        if oid is not None:
            server = res[0]['subnet']
        elif name is not None:
            server = res[0]['subnets'][0]
        
        return server    
    
    def create(self, name, network_id, tenant_id, gateway_ip, cidr, 
               allocation_pools=None, enable_dhcp=True, host_routes=None,
               dns_nameservers=['8.8.8.7', '8.8.8.8']):
        """Creates a subnet on a network. 
        
        :param name str: The subnet name.
        :param network_id id: The UUID of the attached network.
        :param tenant_id id: The UUID of the tenant who owns the network.
        :param gateway_ip: The gateway IP address.
        :param cidr:  The CIDR. 
        :param allocation_pools: dict like 
            {"allocation_pools":{"start":<start ip>,
                                 "end":<end ip>,}}
        :param enable_dhcp: [default=True] Set to true if DHCP is enabled and 
            false if DHCP is disabled.
        :param dns_nameservers: [default=['8.8.8.7', '8.8.8.8'] A list of DNS 
            name servers for the subnet. Specify each name server as an IP 
            address and separate multiple entries with a space.
        :param host_routes:  A list of host route dictionaries for the subnet. 
            For example:
            [
                {
                  "destination":"0.0.0.0/0",
                  "nexthop":"123.45.67.89"
                },
                {
                  "destination":"192.168.0.0/24",
                  "nexthop":"192.168.0.1"
                }
            ]
        :return: Ex.
            {u'allocation_pools': [{u'end': u'10.108.1.254', 
                                    u'start': u'10.108.1.2'}],
             u'cidr': u'10.108.1.0/24',
             u'dns_nameservers': [],
             u'enable_dhcp': True,
             u'gateway_ip': u'10.108.1.1',
             u'host_routes': [{u'destination': u'0.0.0.0/0', 
                               u'nexthop': u'123.45.67.89'}, 
                              {u'destination': u'192.168.0.0/24', 
                               u'nexthop': u'192.168.0.1'}],
             u'id': u'340de24a-7ca9-42b1-bfec-699110485235',
             u'ip_version': 4,
             u'ipv6_address_mode': None,
             u'ipv6_ra_mode': None,
             u'name': u'prova-net-01-subnet',
             u'network_id': u'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             u'subnetpool_id': None,
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "subnet": {
                "name": name,
                "network_id": network_id,
                "tenant_id": tenant_id,
                "ip_version": 4,
                "cidr": cidr,
                "gateway_ip": gateway_ip,
            }
        }
        if allocation_pools is not None:
            data['subnet']['allocation_pools'] = allocation_pools
        if host_routes is not None:
            data['subnet']['host_routes'] = host_routes
        if enable_dhcp is not None:
            data['subnet']['enable_dhcp'] = enable_dhcp
        if dns_nameservers is not None:
            data['subnet']['dns_nameservers'] = dns_nameservers

        path = '%s/subnets' % self.ver
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack subnet: %s' % truncate(res))
        return res[0]['subnet']    

    def update(self, oid, name=None, network_id=None, tenant_id=None, 
               gateway_ip=None, cidr=None, allocation_pools=None, 
               enable_dhcp=None, host_routes=None, dns_nameservers=None):
        """Update a subnet on a network. 
        
        :param oid: id of the subnet
        :param name str: [optional] The subnet name.
        :param network_id id: [optional] The UUID of the attached network.
        :param tenant_id id: [optional] The UUID of the tenant who owns the network.
        :param gateway_ip: [optional] The gateway IP address.
        :param cidr: [optional] The CIDR. 
        :param allocation_pools: [optional]  dict like 
            {"allocation_pools":{"start":<start ip>,
                                 "end":<end ip>,}}
        :param enable_dhcp: [optional]  Set to true if DHCP is enabled and 
            false if DHCP is disabled.
        :param dns_nameservers: [optional] A list of DNS 
            name servers for the subnet. Specify each name server as an IP 
            address and separate multiple entries with a space.
        :param host_routes:[optional] A list of host route dictionaries for the subnet. 
            For example:
            [
                {
                  "destination":"0.0.0.0/0",
                  "nexthop":"123.45.67.89"
                },
                {
                  "destination":"192.168.0.0/24",
                  "nexthop":"192.168.0.1"
                }
            ]
        :return: Ex.
           [{u'end': u'10.108.1.254', u'start': u'10.108.1.2'}],
             u'cidr': u'10.108.1.0/24',
             u'dns_nameservers': [],
             u'enable_dhcp': True,
             u'gateway_ip': u'10.108.1.1',
             u'host_routes': [{u'destination': u'0.0.0.0/0', u'nexthop': u'123.45.67.89'}, {u'destination': u'192.168.0.0/24', u'nexthop': u'192.168.0.1'}],
             u'id': u'340de24a-7ca9-42b1-bfec-699110485235',
             u'ip_version': 4,
             u'ipv6_address_mode': None,
             u'ipv6_ra_mode': None,
             u'name': u'prova-net-02-subnet',
             u'network_id': u'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             u'subnetpool_id': None,
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "subnet": {
            }
        }
        
        if network_id is not None:
            data['subnet']['network_id'] = network_id
        if tenant_id is not None:
            data['subnet']['tenant_id'] = tenant_id
        if cidr is not None:
            data['subnet']['cidr'] = cidr
        if gateway_ip is not None:
            data['subnet']['gateway_ip'] = gateway_ip
        if name is not None:
            data['subnet']['name'] = name
        if allocation_pools is not None:
            data['subnet']['allocation_pools'] = allocation_pools
        if host_routes is not None:
            data['subnet']['host_routes'] = host_routes
        if enable_dhcp is not None:
            data['subnet']['enable_dhcp'] = enable_dhcp
        if dns_nameservers is not None:
            data['subnet']['dns_nameservers'] = dns_nameservers            
            
        path = '%s/subnets/%s' % (self.ver, oid)
        res = self.client.call(path, 'PUT', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack subnet: %s' % truncate(res))
        return res[0]['subnet']
    
    def delete(self, oid):
        """Deletes a subnet.
        
        :param oid: subnet id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/subnets/%s' % (self.ver, oid)
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack subnet: %s' % truncate(res))
        return res[0]

class OpenstackPort(object):
    """
    """
    def __init__(self, network):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = network.manager
        uri = self.manager.endpoint('neutron')
        self.client = OpenstackClient(uri, self.manager.proxy)
        
        self.manager.identity.token = self.manager.identity.token
        self.ver = network.ver
    
    def list(self, tenant=None, network=None, status=None, device_id=None,
             security_groups=None):
        """Lists ports to which the tenant has access. 
        
        :param tenant: tenant id
        :param network: The ID of the attached network. 
        :param status : The port status. Value is ACTIVE or DOWN. 
        :param device_id: The UUID of the device that uses this port. For 
                          example, a virtual server.
        :param security_groups list: The UUIDs of any attached security groups.
        :return: Ex.
            [{u'admin_state_up': True,
              u'allowed_address_pairs': [],
              u'binding:host_id': u'comp-liberty2-kvm.nuvolacsi.it',
              u'binding:profile': {},
              u'binding:vif_details': {u'port_filter': True},
              u'binding:vif_type': u'bridge',
              u'binding:vnic_type': u'normal',
              u'device_id': u'af0064bb-5c1b-44cb-9cd4-52ac210aa091',
              u'device_owner': u'compute:nova',
              u'dns_assignment': [{u'fqdn': u'host-172-25-4-210.openstacklocal.', u'hostname': u'host-172-25-4-210', u'ip_address': u'172.25.4.210'}],
              u'dns_name': u'',
              u'extra_dhcp_opts': [],
              u'fixed_ips': [{u'ip_address': u'172.25.4.210', u'subnet_id': u'f375e490-1103-4c00-9803-2703e3165271'}],
              u'id': u'070ef967-02b8-4c67-9840-cee1cedd5850',
              u'mac_address': u'fa:16:3e:07:ae:72',
              u'name': u'',
              u'network_id': u'40803c62-f4b1-4afb-bd94-f773a5c70f7b',
              u'port_security_enabled': True,
              u'security_groups': [u'25fce921-3d6f-42a9-bcf2-8ab66e564951'],
              u'status': u'ACTIVE',
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'},..,
            ]        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/ports' % self.ver    
        
        query = {}
        if tenant is not None:
            query['tenant_id'] = tenant
        if network is not None:
            query['network_id'] = network
        if status  is not None:
            query['status'] = status
        if device_id  is not None:
            query['device_id'] = device_id
        if security_groups  is not None:
            query['security_groups'] = security_groups             
        path = '%s?%s' % (path, urlencode(query))
        
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack ports: %s' % truncate(res))
        return res[0]['ports']
        
    def get(self, oid=None, name=None, mac_address=None):
        """Shows details for a port. 
        
        :param oid: port id
        :param name: port name
        :param mac_address: The MAC address of the port.
        :return: Ex.
             {u'admin_state_up': True,
              u'allowed_address_pairs': [],
              u'binding:host_id': u'comp-liberty2-kvm.nuvolacsi.it',
              u'binding:profile': {},
              u'binding:vif_details': {u'port_filter': True},
              u'binding:vif_type': u'bridge',
              u'binding:vnic_type': u'normal',
              u'device_id': u'af0064bb-5c1b-44cb-9cd4-52ac210aa091',
              u'device_owner': u'compute:nova',
              u'dns_assignment': [{u'fqdn': u'host-172-25-4-210.openstacklocal.', u'hostname': u'host-172-25-4-210', u'ip_address': u'172.25.4.210'}],
              u'dns_name': u'',
              u'extra_dhcp_opts': [],
              u'fixed_ips': [{u'ip_address': u'172.25.4.210', u'subnet_id': u'f375e490-1103-4c00-9803-2703e3165271'}],
              u'id': u'070ef967-02b8-4c67-9840-cee1cedd5850',
              u'mac_address': u'fa:16:3e:07:ae:72',
              u'name': u'',
              u'network_id': u'40803c62-f4b1-4afb-bd94-f773a5c70f7b',
              u'port_security_enabled': True,
              u'security_groups': [u'25fce921-3d6f-42a9-bcf2-8ab66e564951'],
              u'status': u'ACTIVE',
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '%s/ports/%s' % (self.ver, oid)
        elif name is not None:
            path = '%s/ports?display_name=%s' % (self.ver, name)
        elif mac_address is not None:
            path = '%s/ports?mac_address=%s' % (self.ver, mac_address)            
        else:
            raise OpenstackError('Specify at least port id or name')
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack port: %s' % truncate(res))
        if oid is not None:
            server = res[0]['port']
        elif name is not None:
            server = res[0]['ports'][0]
        
        return server
    
    def create(self, name, network_id, fixed_ips, host_id=None, profile=None,
               vnic_type=None, device_owner=None, device_id=None, 
               security_groups=None, mac_address=None, tenant_id=None):
        """Creates a port on a network. 
        
        :param name str: A symbolic name for the port. 
        :param network_id id: The UUID of the network.
        :param fixed_ips list: specify the subnet. Ex.
            without ip:
            [{
                "subnet_id": "a0304c3a-4f08-4c43-88af-d796509c97d2",
            },..]
            
            with fixed ip:
            [{
                "subnet_id": "a0304c3a-4f08-4c43-88af-d796509c97d2",
                "ip_address": "10.0.0.2"
            },..]
        :param security_groups: [optional] One or more security group UUIDs.
        :param host_id: [optional] The ID of the host where the port is 
            allocated. In some cases, different implementations can run on 
            different hosts.
        :param profile: [optional] A dictionary that enables the application 
            running on the host to pass and receive virtual network interface 
            (VIF) port-specific information to the plug-in.
        :param vnic_type: [optional] The virtual network interface card (vNIC) 
            type that is bound to the neutron port. A valid value is normal, 
            direct, or macvtap.
        :param device_owner str: [optional] The UUID of the entity that uses 
                                 this port. For example, a DHCP agent.
        :param device_id id: [optional] The UUID of the device that uses this 
                             port. For example, a virtual server.
        :param mac_address: The MAC address of an allowed address pair. [optional] 
        :param allowed_address_pairs: A set of zero or more allowed address 
                                      pairs. An address pair contains an IP 
                                      address and MAC address. [optional]
        :param tenant_id: The ID of the tenant who owns the resource.
        :return: Ex.
            {u'admin_state_up': True,
             u'allowed_address_pairs': [],
             u'binding:host_id': u'',
             u'binding:profile': {},
             u'binding:vif_details': {},
             u'binding:vif_type': u'unbound',
             u'binding:vnic_type': u'normal',
             u'device_id': u'',
             u'device_owner': u'',
             u'dns_assignment': [{u'fqdn': u'host-10-108-1-5.openstacklocal.', 
                                  u'hostname': u'host-10-108-1-5', 
                                  u'ip_address': u'10.108.1.5'}],
             u'dns_name': u'',
             u'fixed_ips': [{u'ip_address': u'10.108.1.5', 
                             u'subnet_id': u'340de24a-7ca9-42b1-bfec-699110485235'}],
             u'id': u'a6899bb8-b654-4246-a0f8-5a4abe79cf4d',
             u'mac_address': u'fa:16:3e:2e:d7:7b',
             u'name': u'prova-net-01-port',
             u'network_id': u'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             u'port_security_enabled': True,
             u'security_groups': [u'25fce921-3d6f-42a9-bcf2-8ab66e564951'],
             u'status': u'DOWN',
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "port": {
                "network_id": network_id,
                "name": name,
                "admin_state_up": True,
                "fixed_ips": fixed_ips,
            }
        }
        if tenant_id is not None:
            data[u'port'][u'tenant_id'] = tenant_id
        if host_id is not None:
            data['port']['binding:host_id'] = host_id
        if profile is not None:
            data['port']['binding:profile'] = profile
        if host_id is not None:
            data['port']['binding:vnic_type'] = vnic_type
        if device_owner is not None:
            data['port']['device_owner'] = device_owner
        if device_id is not None:
            data['port']['device_id'] = device_id
        if security_groups is not None:
            data['port']['security_groups'] = security_groups
        if mac_address is not None:
            data[u'allowed_address_pairs'] = [{u'mac_address':mac_address,
                                               u'ip_address':fixed_ips[0][u'ip_address']}]

        path = '%s/ports' % self.ver
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack port: %s' % truncate(res))
        return res[0]['port']

    def update(self, oid, name, network_id, fixed_ips, host_id=None, 
               profile=None, vnic_type=None, device_owner=None, device_id=None,
               security_groups=None):
        """Update a port on a network. 
        
        :param name str: A symbolic name for the port. 
        :param network_id id: The UUID of the network.
        :param fixed_ips list: specify the subnet. Ex.
            without ip:
            [{
                "subnet_id": "a0304c3a-4f08-4c43-88af-d796509c97d2",
            },..]
            
            with fixed ip:
            [{
                "subnet_id": "a0304c3a-4f08-4c43-88af-d796509c97d2",
                "ip_address": "10.0.0.2"
            },..]
        :param security_groups: [optional] One or more security group UUIDs.
        :param host_id: [optional] The ID of the host where the port is 
            allocated. In some cases, different implementations can run on 
            different hosts.
        :param profile: [optional] A dictionary that enables the application 
            running on the host to pass and receive virtual network interface 
            (VIF) port-specific information to the plug-in.
        :param vnic_type: [optional] The virtual network interface card (vNIC) 
            type that is bound to the neutron port. A valid value is normal, 
            direct, or macvtap.         
        :param device_owner str: [optional] The UUID of the entity that uses 
                                 this port. For example, a DHCP agent.
        :param device_id id: [optional] The UUID of the device that uses this 
                             port. For example, a virtual server. 
        :return: Ex.
            {u'admin_state_up': True,
             u'allowed_address_pairs': [],
             u'binding:host_id': u'',
             u'binding:profile': {},
             u'binding:vif_details': {},
             u'binding:vif_type': u'unbound',
             u'binding:vnic_type': u'normal',
             u'device_id': u'',
             u'device_owner': u'',
             u'dns_assignment': [{u'fqdn': u'host-10-108-1-5.openstacklocal.', 
                                  u'hostname': u'host-10-108-1-5', 
                                  u'ip_address': u'10.108.1.5'}],
             u'dns_name': u'',
             u'fixed_ips': [{u'ip_address': u'10.108.1.5', 
                             u'subnet_id': u'340de24a-7ca9-42b1-bfec-699110485235'}],
             u'id': u'a6899bb8-b654-4246-a0f8-5a4abe79cf4d',
             u'mac_address': u'fa:16:3e:2e:d7:7b',
             u'name': u'prova-net-01-port',
             u'network_id': u'e96c7e29-2190-4fa0-8b8b-885a9dae6915',
             u'port_security_enabled': True,
             u'security_groups': [u'25fce921-3d6f-42a9-bcf2-8ab66e564951'],
             u'status': u'DOWN',
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "port": {
            }
        }
        if network_id is not None:
            data['port']['network_id'] = network_id
        if name is not None:
            data['port']['name'] = name
        if fixed_ips is not None:
            data['port']['fixed_ips'] = fixed_ips
        if host_id is not None:
            data['port']['binding:host_id'] = host_id
        if profile is not None:
            data['port']['binding:profile'] = profile
        if host_id is not None:
            data['port']['binding:vnic_type'] = vnic_type
        if device_owner is not None:
            data['port']['device_owner'] = device_owner
        if device_id is not None:
            data['port']['device_id'] = device_id
        if security_groups is not None:
            data['port']['security_groups'] = security_groups
            
        path = '%s/ports/%s' % (self.ver, oid)
        res = self.client.call(path, 'PUT', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack port: %s' % truncate(res))
        return res[0]['port']
    
    def delete(self, oid):
        """Deletes a port.
        
        :param oid: subnet id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/ports/%s' % (self.ver, oid)
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack port: %s' % truncate(res))
        return res[0]

class OpenstackFloatingIp(object):
    """Manage openstack floating ip
    """
    def __init__(self, network):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        self.manager = network.manager
        uri = self.manager.endpoint('neutron')
        self.client = OpenstackClient(uri, self.manager.proxy)
        uri = self.manager.endpoint('nova')
        # change version from 2 to 2.1
        uri = uri.replace('v2/', 'v2.1/')
        self.nova = OpenstackClient(uri, self.manager.proxy)
        self.ver = network.ver
        
    '''
    def get_fixed_ip(self, ip):
        """Shows details for a fixed IP address.
        
        :param ip: The fixed IP of interest to you. 
        :return: Ex: 
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/os-fixed-ips/%s' % ip
        res = self.nova.call(path, 'GET', data='', 
                             token=self.manager.identity.token)
        self.logger.debug('Get openstack fixed ip %s: %s' % (ip, truncate(res)))
        return res[0]['fixed_ip']'''
    
    def list(self):
        """Lists floating IP addresses associated with the tenant.
        
        :return: Ex: 
            [{u'fixed_ip_address': u'192.168.90.175',
              u'floating_ip_address': u'194.116.110.171',
              u'floating_network_id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02',
              u'id': u'00adbb47-8869-43fb-8054-f4ef4426421b',
              u'port_id': u'ba315146-bc4f-4aba-89d5-695569133975',
              u'router_id': u'd8a4b609-98bf-4acc-9b59-3588564eae23',
              u'status': u'ACTIVE',
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'},...,
            ]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/floatingips' % self.ver
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('List openstack floating ips: %s' % (truncate(res)))
        return res[0]['floatingips']
    
    def get(self, oid):
        """Get floating IP addresses associated with the tenant.
        
        :param oid: id of the floating ip
        :return: Ex: 
             {u'fixed_ip_address': u'192.168.90.175',
              u'floating_ip_address': u'194.116.110.171',
              u'floating_network_id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02',
              u'id': u'00adbb47-8869-43fb-8054-f4ef4426421b',
              u'port_id': u'ba315146-bc4f-4aba-89d5-695569133975',
              u'router_id': u'd8a4b609-98bf-4acc-9b59-3588564eae23',
              u'status': u'ACTIVE',
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/floatingips/%s' % (self.ver, oid)
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack floating ip %s: %s' % 
                          (oid, truncate(res)))
        return res[0]['floatingip']    
    
    def create(self, network_id, tenant_id, port_id):
        """Creates a floating IP, and, if you specify port information, 
        associates the floating IP with an internal port.
        
        :param network_id: id of an external network
        :param tenant_id: id of the tenant owner of the ip
        :param port_id: id of the port to associate with ths floating ip
        :return: Ex: 
            {u'fixed_ip_address': u'172.25.4.210',
             u'floating_ip_address': u'194.116.110.115',
             u'floating_network_id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02',
             u'id': u'3f069a11-26bb-4e09-b929-1d6eaadc64bf',
             u'port_id': u'070ef967-02b8-4c67-9840-cee1cedd5850',
             u'router_id': u'd8a4b609-98bf-4acc-9b59-3588564eae23',
             u'status': u'DOWN',
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "floatingip": {
                "tenant_id": tenant_id,
                "floating_network_id": network_id,
                "port_id": port_id
            }
        }
        
        path = '%s/floatingips' % (self.ver)
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack floating ip over port %s: %s' % 
                          (port_id, truncate(res)))
        return res[0]['floatingip']
    
    def update(self, floatingip_id, network_id=None, tenant_id=None, 
               port_id=None):
        """Updates a floating IP and its association with an internal port.
        
        :param floatingip_id: floatingip id
        :param network_id: [optional] id of an external network
        :param tenant_id: [optional] id of the tenant owner of the ip
        :param port_id: [optional] id of the port to associate with ths floating ip
        :return: Ex: 
             {u'fixed_ip_address': u'192.168.90.175',
              u'floating_ip_address': u'194.116.110.171',
              u'floating_network_id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02',
              u'id': u'00adbb47-8869-43fb-8054-f4ef4426421b',
              u'port_id': u'ba315146-bc4f-4aba-89d5-695569133975',
              u'router_id': u'd8a4b609-98bf-4acc-9b59-3588564eae23',
              u'status': u'ACTIVE',
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "floatingip": {
            }
        }
        
        if tenant_id is not None:
            data['floatingip']['tenant_id'] = tenant_id
        if network_id is not None:
            data['floatingip']['floating_network_id'] = network_id
        if port_id is not None:
            data['floatingip']['port_id'] = port_id
        
        path = '%s/floatingips/%s' % (self.ver, floatingip_id)
        res = self.client.call(path, 'PUT', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack floating ip %s: %s' % 
                          (floatingip_id, truncate(res)))
        return res[0]['floatingip'] 
    
    def delete(self, floatingip_id):
        """Deletes a floating IP and, if present, its associated port.
        
        :param floatingip_id: id of the floating ip
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/floatingips/%s' % (self.ver, floatingip_id)
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack floating ip %s: %s' % 
                          (floatingip_id, truncate(res)))
        return res[0] 

class OpenstackRouter(object):
    """
    """
    def __init__(self, network):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = network.manager
        uri = self.manager.endpoint('neutron')
        self.client = OpenstackClient(uri, self.manager.proxy)
        
        self.manager.identity.token = self.manager.identity.token
        self.ver = network.ver

    def list(self, tenant_id=None):
        """List routers.
        
        :return: Ex.
            [...,
             {u'admin_state_up': True,
              u'distributed': False,
              u'external_gateway_info': 
                  {u'enable_snat': True,
                   u'external_fixed_ips': [
                       {u'ip_address': u'194.116.110.161', 
                        u'subnet_id': u'46620b60-76f6-4f1e-a754-dccfc50880c4'}],
                   u'network_id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02'},
              u'ha': True,
              u'id': u'f49b48de-05de-4942-a21c-7e10ce024025',
              u'name': u'cloudify-management-router',
              u'routes': [],
              u'status': u'ACTIVE',
              u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}]        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        query = {}
        if tenant_id is not None:
            query['tenant_id'] = tenant_id
            
        path = '%s/routers?%s' % (self.ver, urlencode(query))
        
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack routers: %s' % truncate(res))
        return res[0]['routers']
        
    def get(self, oid=None):
        """Get router 
        
        :param oid: router id
        :return: Ex.
            {u'admin_state_up': True,
             u'distributed': False,
             u'external_gateway_info': None,
             u'ha': True,
             u'id': u'39660b87-3319-43d3-9780-e60eb5c5079e',
             u'name': u'router-306',
             u'routes': [{u'destination': u'0.0.0.0/0', u'nexthop': u'172.25.4.18'},
                         {u'destination': u'169.254.169.254/32', u'nexthop': u'172.25.4.201'},
                         {u'destination': u'172.25.0.0/16', u'nexthop': u'172.25.4.1'}],
             u'status': u'ACTIVE',
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '%s/routers/%s' % (self.ver, oid)
        else:
            raise OpenstackError('Specify at least router id')
        res = self.client.call(path, 'GET', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Get openstack router: %s' % truncate(res))
        if oid is not None:
            router = res[0]['router']
        
        return router
    
    def create(self, name, tenant_id, network, external_ips=None, routes=None):
        """Create a router.
        
        :param name: router name
        :param tenant_id: router tenant id
        :param network: router external network id
        :param external_ips: [optional] router external_ips. Ex.
        
            [
                {
                    "subnet_id": "255.255.255.0",
                    "ip": "192.168.10.1"
                }
            ]
            
        :param routes: [optional] A list of dictionary pairs in this format:
        
                [
                  {
                    "nexthop":"IPADDRESS",
                    "destination":"CIDR"
                  }
                ]
                
        :return: Ex.
            {u'admin_state_up': True,
             u'distributed': False,
             u'external_gateway_info': {u'enable_snat': True,
                                        u'external_fixed_ips': [{u'ip_address': u'194.116.110.113', u'subnet_id': u'46620b60-76f6-4f1e-a754-dccfc50880c4'}],
                                        u'network_id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02'},
             u'ha': True,
             u'id': u'22e71dd6-1c74-42c3-9898-cd627957208b',
             u'name': u'prova-router-01',
             u'routes': [],
             u'status': u'ACTIVE',
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "router": {
                "name": name,
                "tenant_id": tenant_id,
                "external_gateway_info": {
                    "network_id": network,
                    "enable_snat": True
                },
                "admin_state_up": True
            }
        }
        if external_ips is not None:
            data['router']['external_gateway_info']['external_fixed_ips'] = external_ips
        if routes is not None:
            data['router']['routes'] = routes

        path = '%s/routers' % self.ver
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack router: %s' % truncate(res))
        return res[0]['router']    

    def update(self, oid, name=None, network=None, external_ips=None, routes=None):
        """Updates a logical router. 
        
        :param oid: [optional] network id
        :param name: [optional] router name
        :param network: [optional] router external network id
        :param external_ips: [optional] router external_ips. Ex.
        
            [
                {
                    "subnet_id": "255.255.255.0",
                    "ip": "192.168.10.1"
                }
            ]
            
        :param routes: [optional] A list of dictionary pairs in this format:
        
                [
                  {
                    "nexthop":"IPADDRESS",
                    "destination":"CIDR"
                  }
                ]
                            
        :return: Ex.
            {u'admin_state_up': True,
             u'distributed': False,
             u'external_gateway_info': {u'enable_snat': True,
                                        u'external_fixed_ips': [{u'ip_address': u'194.116.110.113', u'subnet_id': u'46620b60-76f6-4f1e-a754-dccfc50880c4'}],
                                        u'network_id': u'622a06be-4f21-47fc-9df0-06c9c82fbc02'},
             u'ha': True,
             u'id': u'22e71dd6-1c74-42c3-9898-cd627957208b',
             u'name': u'prova-router-01',
             u'routes': [],
             u'status': u'ACTIVE',
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "router": {
            }
        }
        if name is not None:
            data['router']['name'] = name
        if network is not None:
            data['router']['external_gateway_info'] = {u'network_id':network}
        if network is not None and external_ips is not None:
            data['router']['external_gateway_info']['external_fixed_ips'] = external_ips
        if routes is not None:
            data['router']['routes'] = routes
        
        path = '%s/routers/%s' % (self.ver, oid)
        res = self.client.call(path, 'PUT', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack router: %s' % truncate(res))
        return res[0]['router']
    
    def delete(self, oid):
        """Deletes a logical router and, if present, its external gateway interface.  
        
        :param oid: router id
        :return: None
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/routers/%s' % (self.ver, oid)
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack router: %s' % truncate(res))
        return res[0]
    
    def add_internal_interface(self, oid, subnet):
        """Adds an internal interface to a logical router. 
        
        :param oid: router id
        :param subnet: subnet to add with an internal interface
        :return: Ex.
            {u'id': u'32332281-3ca0-434c-b63a-eb9886a32c20',
             u'port_id': u'1b5482d1-ad45-4efc-ba4a-9a767000fd46',
             u'subnet_id': u'340de24a-7ca9-42b1-bfec-699110485235',
             u'subnet_ids': [u'340de24a-7ca9-42b1-bfec-699110485235'],
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"subnet_id": subnet}
        path = '%s/routers/%s/add_router_interface' % (self.ver, oid)
        res = self.client.call(path, 'PUT', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Adds an internal interface to openstack router %s: %s' % 
                          (oid, truncate(res)))
        return res[0]
    
    def delete_internal_interface(self, oid, subnet):
        """Deletes an internal interface from a logical router. 
        
        :param oid: router id
        :param subnet: subnet to remove from internal interfaces
        :return: Ex.
            {u'id': u'32332281-3ca0-434c-b63a-eb9886a32c20',
             u'port_id': u'1b5482d1-ad45-4efc-ba4a-9a767000fd46',
             u'subnet_id': u'340de24a-7ca9-42b1-bfec-699110485235',
             u'subnet_ids': [u'340de24a-7ca9-42b1-bfec-699110485235'],
             u'tenant_id': u'b570fe9ea2c94cb8ba72fe07fa034b62'}
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"subnet_id": subnet}
        path = '%s/routers/%s/remove_router_interface' % (self.ver, oid)
        res = self.client.call(path, 'PUT', data=json.dumps(data),
                               token=self.manager.identity.token)
        self.logger.debug('Delete an internal interface from openstack router %s: %s' % 
                          (oid, truncate(res)))
        return res[0] 

class OpenstackSecurityGroup(object):
    """
    """
    def __init__(self, network):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = network.manager
        uri = self.manager.endpoint('neutron')
        self.client = OpenstackClient(uri, self.manager.proxy)
        
        self.manager.identity.token = self.manager.identity.token
        self.ver = network.ver

    def list_logging(self, detail=False, tenant=None):
        """List flavors
        
        :param tenant: tenant id    
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/logging/logs' % self.ver    
        
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack security groups log: %s' % truncate(res))
        return res[0]

    def list(self, detail=False, tenant=None):
        """List flavors
        
        :param tenant: tenant id    
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/security-groups' % self.ver    
        
        query = {}
        if tenant is not None:
            query['tenant_id'] = tenant
        path = '%s?%s' % (path, urlencode(query))            
        
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack security groups: %s' % truncate(res))
        return res[0]['security_groups']
        
    def get(self, oid):
        """Get flavor
        
        :param oid: flavor id
        :param name: flavor name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/security-groups/%s' % (self.ver, oid)
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack security group: %s' % truncate(res))
        if oid is not None:
            security_group = res[0]['security_group']
        
        return security_group
    
    def create(self, name, desc, tenant_id):
        """Create new security group
        
        :param name: name
        :param desc: description
        :param tenant_id: tenant_id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {"security_group": {"name": name, 
                                   "description": desc, 
                                   "tenant_id":tenant_id}}

        path = '%s/security-groups' % self.ver
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack security group: %s' % truncate(res))
        return res[0]['security_group']    

    def update(self, oid, name=None, desc=None):
        """TODO
        :param oid: security group id
        :param name: name [optional]
        :param desc: description  [optional]
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {u"security_group": {}}
        if name is not None:
            data[u'security_group'][u'name'] = name
        if desc is not None:
            data[u'security_group'][u'description'] = desc            
        
        path = '%s/security-groups/%s' % (self.ver, oid)
        res = self.client.call(path, 'PUT', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Update openstack security group: %s' % truncate(res))
        return res[0]['security_group']
    
    def delete(self, oid):
        """Remove a security group
        
        :param oid: security group id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/security-groups/%s' % (self.ver, oid)
        res = self.client.call(path, 'DELETE', data='', 
                               token=self.manager.identity.token)
        self.logger.debug('Delete openstack security group: %s' % truncate(res))
        return res[0]
    
    def create_rule(self, security_group, direction, ethertype=None,
                    port_range_min=None, port_range_max=None, protocol=None,
                    remote_group_id=None, remote_ip_prefix=None):
        """Create new security group rule
        
        :param security_group: security group id
        :param direction: ingress or egress: The direction in which the 
                          security group rule is applied. For a compute 
                          instance, an ingress security group rule is applied 
                          to incoming (ingress) traffic for that instance. 
                          An egress rule is applied to traffic leaving the 
                          instance. 
        :param ethertype: Must be IPv4 or IPv6, and addresses represented in 
                          CIDR must match the ingress or egress rules. [optional] 
        :param port_range_min: The minimum port number in the range that is 
                               matched by the security group rule. If the 
                               protocol is TCP or UDP, this value must be less 
                               than or equal to the port_range_max attribute 
                               value. If the protocol is ICMP, this value must 
                               be an ICMP type. [optional] 
        :param port_range_max: The maximum port number in the range that is 
                               matched by the security group rule. The 
                               port_range_min attribute constrains the 
                               port_range_max attribute. If the protocol is 
                               ICMP, this value must be an ICMP type. [optional] 
        :param protocol: The protocol that is matched by the security group 
                         rule. Valid values are null, tcp, udp, and icmp. [optional] 
        :param remote_group_id: The remote group UUID to associate with this 
                                security group rule. You can specify either the 
                                remote_group_id or remote_ip_prefix attribute 
                                in the request body. [optional] 
        :param remote_ip_prefix:  The remote IP prefix to associate with this 
                                  security group rule. You can specify either 
                                  the remote_group_id or remote_ip_prefix 
                                  attribute in the request body. This attribute 
                                  matches the IP prefix as the source IP address 
                                  of the IP packet. [optional] 
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {
            "security_group_rule": {
                "direction": direction,
                "protocol": protocol,
                "security_group_id": security_group
            }
        }
        if remote_ip_prefix is not None:
            data['security_group_rule'].update({"port_range_min":port_range_min,
                                                "port_range_max":port_range_max,
                                                "ethertype":ethertype,
                                                "remote_ip_prefix":remote_ip_prefix})
        elif remote_group_id is not None:
            data['security_group_rule'].update({"port_range_min":port_range_min,
                                                "port_range_max":port_range_max,
                                                "ethertype":ethertype,
                                                "remote_group_id":remote_group_id})

        path = '%s/security-group-rules' % self.ver
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack security group %s rule: %s' % 
                          (security_group, truncate(res)))
        return res[0]['security_group_rule']
    
    def delete_rule(self, ruleid):
        """Remove a security group rule
        
        :param ruleid: rule id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '%s/security-group-rules/%s' % (self.ver, ruleid)
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack security group rule %s: %s' % 
                          (ruleid, truncate(res)))
        return res[0]    
    
    #
    # actions
    #       

class OpenstackImage(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        uri = manager.endpoint('nova')
        self.client = OpenstackClient(uri, manager.proxy)
        
        

    def list(self, detail=False, tenant=None, status=None, mindisk=None, 
             minram=None, itype=None, limit=None, marker=None):
        """
        :param tenant: tenant id
        :param status: Filters the response by an image status, as a string.
                       For example, ACTIVE.
        :param mindisk: Filters the response by a minimum disk size. 
                        For example, 100.
        :param minram: Filters the response by a minimum RAM size. 
                       For example, 512.
        :param itype: Filters the response by an image type. For example, 
                      snapshot or backup. 
        :param limit:  Requests a page size of items. Returns a number of items 
                       up to a limit value. Use the limit parameter to make an 
                       initial limited request and use the ID of the last-seen 
                       item from the response as the marker parameter value in 
                       a subsequent limited request.
        :param marker: The ID of the last-seen item. Use the limit parameter 
                       to make an initial limited request and use the ID of the 
                       last-seen item from the response as the marker parameter 
                       value in a subsequent limited request.        
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/images'
        if detail is True:
            path = '/images/detail'        
        
        query = {}
        if tenant is not None:
            query['tenant_id'] = tenant         
        if status is not None:
            query['status'] = status
        if mindisk is not None:
            query['mindisk'] = mindisk
        if minram is not None:
            query['minram'] = minram
        if itype is not None:
            query['itype'] = itype            
        if limit is not None:
            query['limit'] = limit
        if marker is not None:
            query['marker'] = marker            
        path = '%s?%s' % (path, urlencode(query))
        
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack images: %s' % truncate(res))
        return res[0]['images']
        
    def get(self, oid=None, name=None):
        """
        :param oid: image id
        :param name: image name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        if oid is not None:
            path = '/images/%s' % oid
        elif name is not None:
            path = '/images/detail?name=%s' % name
        else:
            raise OpenstackError('Specify at least project id or name')
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack image: %s' % truncate(res))
        if oid is not None:
            image = res[0]['image']
        elif name is not None:
            image = res[0]['images'][0]
        
        return image    
    
    def create(self, tenant, name, image, flavor, security_groups=["default"], 
               networks=[]):
        """TODO
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {        
        }

        path = '/images'
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack image: %s' % truncate(res))
        return res[0]['image']    

    def update(self, oid):
        """TODO
        :param oid: image id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/images/%s' % oid
        res = self.client.call(path, 'PUT', data='', token=self.manager.identity.token)
        self.logger.debug('Update openstack image: %s' % truncate(res))
        return res[0]['image']
    
    def delete(self, oid):
        """TODO
        :param oid: image id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/images/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack image: %s' % truncate(res))
        return res[0]['image']
    
    #
    # actions
    #
    
class OpenstackFlavor(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)          
        
        self.manager = manager
        uri = manager.endpoint('nova')
        self.client = OpenstackClient(uri, manager.proxy)
        
        

    def list(self, detail=False, tenant=None):
        """List flavors
        
        :param tenant: tenant id    
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors'
        if detail is True:
            path = '/flavors/detail'        
        
        query = {}
        if tenant is not None:
            query['tenant_id'] = tenant
        path = '%s?%s' % (path, urlencode(query))            
        
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack flavors: %s' % truncate(res))
        return res[0]['flavors']
        
    def get(self, oid):
        """Get flavor
        
        :param oid: flavor id
        :param name: flavor name
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s' % oid
        res = self.client.call(path, 'GET', data='', token=self.manager.identity.token)
        self.logger.debug('Get openstack flavor: %s' % truncate(res))
        if oid is not None:
            flavor = res[0]['flavor']
        
        return flavor
    
    def create(self, tenant, name, image, flavor, security_groups=["default"], 
               networks=[]):
        """TODO
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        data = {        
        }

        path = '/flavors'
        res = self.client.call(path, 'POST', data=json.dumps(data), 
                               token=self.manager.identity.token)
        self.logger.debug('Create openstack flavor: %s' % truncate(res))
        return res[0]['flavor']    

    def update(self, oid):
        """TODO
        :param oid: flavor id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s' % oid
        res = self.client.call(path, 'PUT', data='', token=self.manager.identity.token)
        self.logger.debug('Update openstack flavor: %s' % truncate(res))
        return res[0]['flavor']
    
    def delete(self, oid):
        """TODO
        :param oid: flavor id
        :raises OpenstackError: raise :class:`.OpenstackError`
        """
        path = '/flavors/%s' % oid
        res = self.client.call(path, 'DELETE', data='', token=self.manager.identity.token)
        self.logger.debug('Delete openstack flavor: %s' % truncate(res))
        return res[0]['flavor']
    
    #
    # actions
    #     
    
