#!/usr/bin/env python

'''
Created on Autumn 2016

@author: MikeBeauty
'''

from logging import getLogger
from beecell.perf import watch
from sys import version_info
import ssl
from urllib3.util.ssl_ import create_urllib3_context
import requests

import base64
from xmltodict import parse as xmltodict
import httplib
import json
import re 
from urlparse import urlparse



from beecell.simple import get_class_props, truncate, str2uni, get_value,\
    get_attrib


#from beecell.simple import get_class_props, truncate, str2uni, get_value,\
#    get_attrib
#from beecell.perf import watch
#from beecell.xml_parser import xml2dict
#from xmltodict import parse as xmltodict

class VeeamClient(object):
    """ """
    
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
            res = http_client2('https', '/api', 'POST',
                                port=443, data='', headers={})        
        
        :param path: Request path. Ex. /api/
        :param method: Request method. Ex. GET, POST, PUT, DELETE
        :param headers: Request headers. [default={}]. Ex. 
                        {"Content-type": "application/x-www-form-urlencoded",
                         "Accept": "text/plain"}
        :param data: Request data. [default={}]. Ex. 
                       {'@number': 12524, '@type': 'issue', '@action': 'show'}
        :param timeout: Request timeout. [default=30s]
        :param token: Openstack authorization token [optional]
        :param base_path: base path that replace defualt path set initially
        :raise OpenstackError:
        """
        if base_path is not None:
            path = base_path + path
        else:
            path = self.path + path
        
        http_headers = {}
        http_headers['Content-Type'] = 'application/json'
        if token is not None:
            http_headers['X-RestSvcSessionId'] = token
        if headers is not None:
            http_headers.update(headers)
        
        self.logger.debug('Send http %s request to %s://%s:%s%s' % 
                          (method, self.proto, self.host, self.port, path))
        self.logger.debug('Send headers: %s' % http_headers)
        if data.lower().find('password') < 0:
            self.logger.debug('Send data: %s' % data)
        else:
            self.logger.debug('Send data: XXXXXXXXX')
            self.logger.debug('Send data: %s' % data)
        try:
            _host = self.host
            _port = self.port
            _headers = http_headers
            if self.proxy is not None:
                _host = self.proxy[0]
                _port = self.proxy[1]
                _headers = {}
                path = "%s://%s:%s%s" % (self.proto, self.host, self.port, path)
            
            if self.proto == 'http':       
                conn = httplib.HTTPConnection(_host, _port, timeout=timeout)
            else:
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except:
                    pass
                conn = httplib.HTTPSConnection(_host, _port, timeout=timeout)

            if self.proxy is not None:
                conn.set_tunnel(self.host, port=self.port, headers=headers)
                self.logger.debug("set proxy %s" % self.proxy)
                headers = None

            conn.request(method, path, data, _headers)
            response = conn.getresponse()
            content_type = response.getheader('content-type')
            self.logger.debug('Response status: %s' % response.status)
            self.logger.debug('Response content-type: %s' % content_type)
        except httplib.HTTPException as ex:
            raise VeeamError(ex, 400)
        
        # read response
        try:
            res = response.read()
            res_headers = response.getheaders()
            self.logger.debug('Response data: %s' % truncate(res, 200))
            self.logger.debug('Response headers: %s' % truncate(res_headers, 200))
            if content_type is not None and \
               content_type.find('application/json') >= 0:
                try:
                    res = json.loads(res)
                except Exception as ex:
                    self.logger.warn(ex)
                    res = res
            conn.close()
        except httplib.HTTPException as ex:
            raise VeeamError(ex, 400)                
        except Exception as ex:
            raise VeeamError(ex, 400)

        # get error messages
        if response.status in [400, 401, 403, 404, 405, 408, 409, 413, 415, 
                               500, 503]:
            try:
                excpt = res.keys()[0]
                res = '%s - %s' % (excpt, res[excpt][u'message'])
            except:
                res = ''            
            
            '''
            if u'NeutronError' in res.keys():
                res = u' - %s' % res[u'NeutronError'][u'message']
            elif u'badRequest' in res.keys():
                res = u' - %s' % res[u'badRequest'][u'message']
            elif u'computeFault' in res.keys():
                res = u' - %s' % res[u'computeFault'][u'message']
            else:                        
                try:
                    res = ' - %s' % res[u'error'][u'message']
                except:
                    res = ''
            '''
                    
        # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status == 400:
            raise VeeamError('Bad Request%s' % res, 400)
  
        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif response.status == 401:
            raise VeeamError('Unauthorized%s', 401)
        
        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3
        
        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif response.status == 403:
            raise VeeamError('Forbidden%s' % res, 403)
        
        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif response.status == 404:
            raise VeeamError('Not Found%s' % res, 404)
        
        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif response.status == 405:
            raise VeeamError('Method Not Allowed%s' % res, 405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7
        
        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8
        
        # REQUEST_TIMEOUT        408
        elif response.status == 408:
            raise VeeamError('Request timeout%s' % res, 408)
        
        # CONFLICT               409
        elif response.status == 409:
            raise VeeamError('Conflict%s' % res, 409)
            # raise OpenstackError(' conflict', 409)
        
        # Request Entity Too Large          413
        elif response.status == 413:
            raise VeeamError('Request Entity Too Large%s' % res, 413)
        
        # Unsupported Media Type            415
        elif response.status == 415:
            raise VeeamError('Unsupported Media Type%s' % res, 415)
        
        # INTERNAL SERVER ERROR  500
        elif response.status == 500:
            raise VeeamError('Server error%s' % res, 500)
        
        # Service Unavailable  503
        elif response.status == 503:
            raise VeeamError('Service Unavailable%s' % res, 503)         
        
        # OK                     200    HTTP/1.1, RFC 2616, Section 10.2.1
        # CREATED                201    HTTP/1.1, RFC 2616, Section 10.2.2
        # ACCEPTED               202    HTTP/1.1, RFC 2616, Section 10.2.3
        # NON_AUTHORITATIVE_INFORMATION    203    HTTP/1.1, RFC 2616, Section 10.2.4
        # NO_CONTENT             204    HTTP/1.1, RFC 2616, Section 10.2.5
        # RESET_CONTENT          205    HTTP/1.1, RFC 2616, Section 10.2.6
        # PARTIAL_CONTENT        206    HTTP/1.1, RFC 2616, Section 10.2.7
        # MULTI_STATUS           207    WEBDAV RFC 2518, Section 10.2
        elif re.match('20[0-9]+', str(response.status)):
            return res, res_headers
      
class VeeamError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
    
    def __repr__(self):
        return "VeeamError: %s" % self.value    
    
    def __str__(self):
        return "VeeamError: %s" % self.value

class VeeamManager(object):
    """
    :param veeam_conn: vcenter connection params {'host':, 'port':, 'user':, 
                                                    'pwd':, 'verified':False}
    """
    def __init__(self, veeam_conn=None):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        #print self.__class__.__module__+ '.'+self.__class__.__name__
        
        if veeam_conn is not None:
            self.veeam_id = "%s:%s" % (veeam_conn['host'], 
                                         veeam_conn['port'])
            
            self._get_veeam_connection(veeam_conn['host'], 
                                         veeam_conn['port'], 
                                         veeam_conn['user'], 
                                         veeam_conn['pwd'], 
                                         verified=veeam_conn['verified'])
            
            #print(self.veeam_token)
            # by sergio self.client = VeeamClient("http://tst-veeamsrv.tstsddc.csi.it:9399") 
            # by sergio self.job = VeeamJob(self, self.client)
        
    
    @watch
    def _get_veeam_connection(self, host, port, user, password, verified=False):
        """Effettua la connessione al server e mi restituisce il token in caso di autenticazione corretta"""
        try:
            '''
            ctx = None
            if verified is False:
                # python >= 2.7.9
                if version_info.major==2 and version_info.minor==7 and \
                   version_info.micro>8:                
                    ctx = ssl._create_unverified_context()
                # python < 2.7.8
                elif version_info.major==2 and version_info.minor==7 and \
                   version_info.micro<9:
                    ctx = create_urllib3_context(cert_reqs=ssl.CERT_NONE)
                else:
                    ctx = None
            '''
             
            self.veeamservice = 'http://<<server>>:<<port>>/api/'
            
            self.veeamservice = self.veeamservice.replace("<<server>>", host)
            self.veeamservice = self.veeamservice.replace("<<port>>", port)
            
            # mi costruisco l'header di connessione
            stringaUtenza = user + ":" + password
            auth_base64=base64.b64encode(stringaUtenza)
            utenza_base64="Basic " + auth_base64
            
            headers = {'Authorization': utenza_base64}
            
            conn_uri=self.veeamservice + 'sessionMngr/?v=v1_2'
            self.logger.debug("URI to connect :'%s'" % (conn_uri))
            
            r = requests.post(conn_uri, headers=headers)
            

            if r.status_code == 201:
                #ss
                self.veeam_token = r.headers['x-restsvcsessionid']
                self.logger.info("Connect veeam %s. Current token id: %s" % (
                                host, self.veeam_token))
            else:                
                self.logger.error('The user name or password is incorrect', exc_info=True)
                raise VeeamError('The user name or password is incorrect',r.status_code)
            
        except requests.ConnectionError as error:
            self.logger.error(error, exc_info=True)
            raise VeeamError(error, code=0)
        except Exception as error:
            self.logger.error(error, exc_info=True)
            raise VeeamError(error, code=0)

    @watch
    def ping_veeam(self):
        """Ping veeam server.
        
        :return: True if ping ok, False otherwise
        
        
        """

        try:
            headers = {'X-RestSvcSessionId': self.veeam_token}
            self.logger.debug("Header to send :'%s'" % headers)
            
            conn_uri=self.veeamservice + 'logonSessions'
            self.logger.debug("URI to connect :'%s'" % (conn_uri))
            
            r = requests.get(conn_uri, headers=headers)
            
            if r.status_code == 200:
                self.logger.info("Ping veeam %s : OK"%conn_uri)
                #self.logger.debug("Body : %s"%r.text)
            else:
                self.logger.error("Ping veeam %s : KO ; status_code = %s "%(conn_uri,r.status_code))
                raise VeeamError("Ping veeam %s : KO"%conn_uri,r.status_code)
                return False                             
        except Exception as error:
            #self.logger.error("Ping veeam %s : KO ; Err : %s"%(self.veeam_id,error))
            return False
        return True

class VeeamJob(object):
    
    def __init__(self, veeammanager,veeamclient):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        
        self.token=veeammanager.veeam_token        
        self.util=veeamclient  
             
    def get_jobs(self):
        """Get the veeam backup server configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :raise VeeamError
        """  
        method='GET'
        path='/api/jobs'
           
        res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
        jobs=res['EntityReferences']['Ref']
        risultato = {u'status':u'OK',u'status_code':'200',u'data':jobs}
        self.logger.debug("risultato :'%s'" % risultato)
        for item in jobs:
            self.logger.info("Nome %s" % item['@Name'])
            self.logger.info("UID %s" % item['@UID'])
        
        self.logger.debug("--------------------------------------------------keys: %s " % jobs[0].keys())
        return (risultato)          
       
    
    def start_job(self):
        pass

    def stop_job(self):
        pass

    def retry_job(self):
        pass
    
    def clone_job(self):
        pass
    
    
    
    
    
    pass




'''


        veeam = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'160610555',
                 'pwd':'Admin$201606', 'verified':False}

        
        self.util=VeeamManager(veeam)




'''

# prod 
'''             
veeam = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'160610555',
                 'pwd':'Admin$201606', 'verified':False}
   



prova= VeeamManager(veeam)
print(prova.veeam_token)

#get_class_props(VeeamManager)     
'''

# test 
'''
veeamTest = {'host':'tst-veeamsrv.tstsddc.csi.it', 'port':'9399',
                 'user':'Administrator',
                 'pwd':'cs1$topix', 'verified':False}
'''

'''             
veeam = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'160610555',
                 'pwd':'Admin$201606', 'verified':False}
'''
veeamProd = {'host':'veeambackup.csi.it', 'port':'9399',
                 'user':'160610555',
                 'pwd':'Admin$201606', 'verified':False}


veeamTest = {'host':'tst-veeamsrv.tstsddc.csi.it', 'port':'9399',
                 'user':'Administrator',
                 'pwd':'cs1$topix', 'verified':False}


#mieijobs=VeeamJob(VeeamManager(veeamTest)).get_jobs()
'''
if mieijobs['status']=='OK' :
    
    print mieijobs['data']['jobs']
else:
    print mieijobs['data']
#print mieijobs.token

#print mieijobs.get_jobs()
'''


