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
#import jsonify



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
             token=None, base_path=None, content_type='application/xml'):
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
        :param content_type: acepted value 'application/json' o 'application/xml'
                            default = 'application/xml'
        :raise OpenstackError:
        """
        if base_path is not None:
            path = base_path + path
        else:
            path = self.path + path
        
        http_headers = {}
        #http_headers['Content-Type'] = 'application/json'
        # valori possibili : 'application/json' o 'application/xml'
        http_headers['Content-Type']=content_type
            
        
        #http_headers['Content-Type']='application/xml'
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
    @watch
    def __init__(self, veeam_conn=None):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        #print self.__class__.__module__+ '.'+self.__class__.__name__
        
        if veeam_conn is not None:
            
            method='POST'
            path='/api/sessionMngr/?v=v1_2'
            
            self.client=VeeamClient(veeam_conn['uri'])
            
            stringaUtenza = veeam_conn['user'] + ":" + veeam_conn['pwd']
            auth_base64=base64.b64encode(stringaUtenza)
            utenza_base64="Basic " + auth_base64
            
            headers = {'Authorization': utenza_base64}

            res,heads=self.client.call(path,method,'',headers,30,None,'')
            #self.logger.debug("response :'%s'" % res)
            #self.logger.debug("headers ")
            
            self.veeam_token=heads[0][1]
            self.logger.debug("veeam_Token :'%s'" % self.veeam_token)

            #'http://tst-veeamsrv.tstsddc.csi.it:9399/api/sessionMngr/?v=v1_2'
            # by sergio self.client = VeeamClient("http://tst-veeamsrv.tstsddc.csi.it:9399") 
            # by sergio self.job = VeeamJob(self, self.client)
            self.jobs=VeeamJob(self, self.client)
            self.jobobjs=VeeamJobIncludes(self,self.client)
            
    
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

    def get_tasks(self):
        method='GET'        
        path='/api/tasks'
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.client.call(path, method,'','', 30, self.veeam_token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    
    def get_task_props(self,taskId):

        method='GET'        
        path='/api/tasks/'+taskId
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.client.call(path, method,'','', 30, self.veeam_token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    
        
    
class VeeamJob(object):
    
    def __init__(self, veeammanager,veeamclient):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        
        self.token=veeammanager.veeam_token        
        self.util=veeamclient  
             
    def get_jobs(self):
        """Get all the jobs configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :raise VeeamError
        """  
        method='GET'
        path='/api/jobs'
        
        try:   
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            jobs=res['EntityReferences']['Ref']
            risultato = {u'status':u'OK',u'status_code':'200',u'data':jobs}
            self.logger.debug("risultato :'%s'" % risultato)
        
            for item in jobs:
                self.logger.info("Nome %s , UID '%s'  , Href '%s' " % (item['@Name'],item['@UID'],item['@Href']))
                
            
            self.logger.debug("--------------------------------------------------keys: %s " % jobs[0].keys())

        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
        
        return (risultato)          

    def get_job_props(self,href):        
        """Get the properties of a single job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='GET'        
        path=path+"?format=Entity"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    
    def edit_job(self,href,XML):
        """Edit the properties of a job backup configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        :param XML : properties to modify in an xml format
                    Example :
                    
                    XML='<?xml version="1.0" encoding="utf-8"?>
                    <Job Type="Job"  
                    xmlns="http://www.veeam.com/ent/v1.0" 
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <JobScheduleOptions>
                            <RetryOptions>
                                <RetryTimes>3</RetryTimes>
                                <RetryTimeout>5</RetryTimeout>
                                <RetrySpecified>true</RetrySpecified>
                            </RetryOptions>        
                            <OptionsDaily Enabled="true">
                                <Kind>Everyday</Kind>
                                <Days>Sunday</Days>
                                <Days>Monday</Days>
                                <Days>Tuesday</Days>
                                <Days>Wednesday</Days>
                                <Days>Thursday</Days>
                                <Days>Friday</Days>
                                <Days>Saturday</Days>
                                <Time>22:00:00.0000000</Time>
                            </OptionsDaily>        
                        </JobScheduleOptions>
                    </Job>'
               
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='PUT'        
        path=path+"?action=edit"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,XML,'', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
           
    def start_job(self,href):
        """Start the backup job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=start"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)

    def stop_job(self,href):
        """Stop the backup job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """
        obj = urlparse(href)
 
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=stop"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)

    def retry_job(self,href):
        """Retry the backup job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        
        obj = urlparse(href)
 
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=retry"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    
    def clone_job(self,href,XML):
        """CLONE the backup job 'href' in a new job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job to clone in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        :param XML : properties to modify in an xml format
                    Example :
                    
                    XML='<?xml version="1.0" encoding="utf-8"?>
                    <JobCloneSpec xmlns="http://www.veeam.com/ent/v1.0" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> 
                        <BackupJobCloneInfo> 
                            <JobName>Prova Cloned Job</JobName> 
                            <FolderName>Prova Cloned Job</FolderName> 
                            <RepositoryUid>urn:veeam:Repository:b03eb865-79eb-4450-bc52-48a7472314ca</RepositoryUid> 
                        </BackupJobCloneInfo> 
                    </JobCloneSpec>'
               
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=clone"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,XML,'', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
        
    def togglescheduleenabled_job(self,href):
        """Enable/disable the backup job configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        
        obj = urlparse(href)
 
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"?action=toggleScheduleEnabled"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
    
class VeeamJobIncludes(object):
    """Manage the objects of a backup jobs """        
    
    def __init__(self, veeammanager,veeamclient):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)
        
        self.token=veeammanager.veeam_token        
        self.util=veeamclient  
             
    def get_includes(self,href):
        """Get all the includes of the backup job 'href' configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='GET'        
        path=path+"/includes"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)

    def get_includes_props(self,href):
        """Get the properties of the include 'href' configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        

        method='GET'        
        path=href
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)

         
    def add_includes(self,href,XML):
        """add a new 'XML' include the backup job 'href' configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job to clone in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        :param XML : properties to modify in an xml format
                    Example :
                    
                XML='<?xml version="1.0" encoding="utf-8"?>
                    <CreateObjectInJobSpec xmlns="http://www.veeam.com/ent/v1.0"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <HierarchyObjRef>urn:VMware:Vm:7f6b6270-1f3b-4dc6-872f-2d1dfc519c00.vm-1401</HierarchyObjRef>
                    <HierarchyObjName>tst-calamari</HierarchyObjName>
                    </CreateObjectInJobSpec>
                    '
               
        :raise VeeamError
        """  
        obj = urlparse(href)
        '''
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        '''
        proto = obj.scheme
        self.logger.debug("proto %s "%proto)

        host, port = obj.netloc.split(':')
        port = int(port)
        self.logger.debug("host %s , port %s" % (host,port))

        path = obj.path
        self.logger.debug("path %s "%path)

        method='POST'        
        path=path+"/includes"
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,XML,'', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
        
    def delete_includes(self,href):
        """DELETE the include 'href' configured on Veeam Enterprise manager server
            the result will be a DICT in this format in unicode UTF8 
            
             risultato =[{u'status':u'OK/ERROR',u'status_code':u'xxxx',u'data':[]}] 
        
        :param href :reference of the job in this format 'http://tst-veeamsrv.tstsddc.csi.it:9399/api/jobs/016bdba9-462a-4b33-a8fc-0dce63735fc3'
        
        :raise VeeamError
        """        

        method='DELETE'        
        path=href
        self.logger.debug("action  %s "%path)
        
        try:
            res=xmltodict(self.util.call(path, method,'','', 30, self.token , '')[0])
            self.logger.debug("risultato :'%s'" % res)
            risultato = {u'status':u'OK',u'status_code':'202',u'data':res}
        except VeeamError as e:
            risultato = {u'status':u'ERROR',u'status_code':e.code,u'data':e.value}
                    
        return(risultato)
        
    

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


