'''
Created on Sep 25, 2015

@author: darkbk

pip install -U pyOpenSSL
pip install -U xmltodict

'''
from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim
import inspect
from logging import getLogger
import time
import base64
import ssl
import httplib
import re
import traceback
import OpenSSL
from urllib3.util.ssl_ import create_urllib3_context
from sys import version_info
import ujson as json
from beecell.simple import get_class_props, truncate, str2uni, get_value,\
    get_attrib
from beecell.perf import watch
from beecell.xml_parser import xml2dict
from xmltodict import parse as xmltodict
#from lxml import etree
from urllib import urlencode
from xml.etree import ElementTree
from xml.etree.ElementTree import tostring,SubElement

class VsphereError(Exception):
    def __init__(self, value, code=0):
        self.value = value
        self.code = code
        Exception.__init__(self, value, code)
    
    def __repr__(self):
        return "VsphereError: %s" % self.value    
    
    def __str__(self):
        return "VsphereError: %s" % self.value
    
class VsphereNotFound(VsphereError):
    def __init__(self):
        VsphereError.__init__(self, u'NOT_FOUND', 404)

class VsphereManager(object):
    """
    :param vcenter_conn: vcenter connection params {'host':, 'port':, 'user':, 
                                                    'pwd':, 'verified':False}
    :param nsx_manager_conn: nsx manager connection params {'host':, 'port':443, 
                                                            'user':'admin', 'pwd':,
                                                            'verified':False,
                                                            'timeout':5}
    """
    
    TASK_SUCCESS = vim.TaskInfo.State.success
    TASK_ERROR = vim.TaskInfo.State.error
    
    def __init__(self, vcenter_conn=None, nsx_manager_conn=None):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)        
        
        # vcenter connection service instance
        self.vsphere_id = None
        self.si = None
        self.vcenter_session = None
        self.os_list = get_class_props(vim.vm.GuestOsDescriptor.GuestOsIdentifier)
        self.vcenter_conn = vcenter_conn
        
        # nsx manager connection
        self.nsx_id = None
        self.nsx = None
        self.nsx_user = None
        self.nsx_pwd = None        
        self.nsx_manager_conn= nsx_manager_conn
        
        if vcenter_conn is not None:
            self.vsphere_id = "%s:%s" % (vcenter_conn['host'], 
                                         vcenter_conn['port'])
            self._get_vcenter_connection(vcenter_conn['host'], 
                                         vcenter_conn['port'], 
                                         vcenter_conn['user'], 
                                         vcenter_conn['pwd'], 
                                         verified=vcenter_conn['verified'])
        if nsx_manager_conn is not None:
            self.nsx_id = "%s:%s" % (nsx_manager_conn['host'], 
                                     nsx_manager_conn['port'])            
            self._get_nsx_manager_connection(nsx_manager_conn['host'],
                                             nsx_manager_conn['user'], 
                                             nsx_manager_conn['pwd'], 
                                             port=nsx_manager_conn['port'],
                                             verified=nsx_manager_conn['verified'], 
                                             timeout=nsx_manager_conn['timeout'])
        
        # vsphere proxy objects
        self.system = VsphereSystem(self)
        self.datacenter = VsphereDatacenter(self)
        self.folder = VsphereFolder(self)
        self.server = VsphereServer(self)
        self.vapp = VsphereVApp(self)
        self.datastore = VsphereDatastore(self)
        self.network = VsphereNetwork(self)
        self.cluster = VsphereCluster(self)
        
        self.server_props = [u'name', u'parent', u'overallStatus',
                             u'config.hardware.numCPU', 
                             u'config.hardware.memoryMB', 
                             u'guest.guestState', u'guest.hostName', 
                             u'guest.ipAddress',
                             u'config.guestFullName', u'config.guestId',
                             u'config.template',
                             u'runtime.powerState']
    
    @watch
    def _get_vcenter_connection(self, host, port, user, pwd, verified=False):
        """"""
        try:
            ctx = None
            if verified is False:
                '''if hasattr(ssl, '_create_unverified_context'):
                   ctx = ssl._create_unverified_context()
                else:
                   sslContext = None
                try:
                    ssl._https_verify_certificates(enable=False)
                except:
                    ctx = create_urllib3_context(cert_reqs=ssl.CERT_NONE)'''
                '''# python >= 2.7.9
                if version_info.major==2 and version_info.minor==7 and \
                   version_info.micro>8:                
                    ctx = ssl._create_unverified_context()
                # python < 2.7.8
                elif version_info.major==2 and version_info.minor==7 and \
                   version_info.micro<9:
                    #ctx = create_urllib3_context(cert_reqs=ssl.CERT_NONE)
                    ctx = ssl._create_unverified_context()
                    ctx.verify_mode = ssl.CERT_NONE
                    ctx.check_hostname = False
                else:
                    ctx = None'''

            try:
                try:
                    ssl._https_verify_certificates(enable=False)
                except:
                    ctx = create_urllib3_context(cert_reqs=ssl.CERT_NONE)
                self.si = connect.SmartConnect(host=host, user=user, pwd=pwd,
                                               port=int(port), sslContext=ctx)
            except:               
                self.si = connect.SmartConnectNoSSL(host=host, user=user,
                                                    pwd=pwd, port=int(port))
            
            self.vcenter_session = self.si.content.sessionManager.currentSession
            self.logger.info("Connect vcenter %s. Current session id: %s" % (
                                host, self.vcenter_session.key))
        except vim.fault.NotAuthenticated as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg, code=0)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg, code=0)
        except Exception as error:
            self.logger.error(error, exc_info=True)
            raise VsphereError(error, code=0)
    
    @watch
    def _get_nsx_manager_connection(self, host, user, pwd, port=443, 
                                    verified=False, timeout=30):
        """Configure nsx https client
        
        :param host: Request host. Ex. 10.102.90.30
        :param port: Request port. [default=80]
        :param timeout: Request timeout. [default=30s]
        :raise VsphereError:
        """
        self.logger.debug('Configure http client for https://%s:%s' % (host, port))

        try:
            if verified is False:
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                    #ctx = ssl._create_unverified_context()
                except: pass
            
            #self.nsx = httplib.HTTPSConnection(host, port, timeout=timeout)
            self.nsx = {'host':host, 'port':port, 'timeout':timeout, 
                        'user':user, 'pwd':pwd, 'etag':None}
        except httplib.HTTPException as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error, code=0)

    @watch
    def disconnect(self):
        """Disconnect vcenter and reset nsx connection"""
        try:
            connect.Disconnect(self.si)
            self.si = None
            self.nsx = None
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg, code=0)
        except Exception as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error, code=0)
        return None

    @watch
    def get_vcenter_session(self):
        """Get current vcenter session
        """
        self.vcenter_session = None
        try:
            self.vcenter_session = self.si.content.sessionManager.currentSession
            self.logger.info("Current session id: %s" % (self.vcenter_session.key))
        except vim.fault.NotAuthenticated as error:
            self.logger.warn(traceback.format_exc())
        except vmodl.MethodFault as error:
            self.logger.warn(traceback.format_exc())
            #raise VsphereError(error.msg, code=0)
        except Exception as error:
            self.logger.warn(traceback.format_exc())
            #raise VsphereError(error, code=0)
        return self.vcenter_session

    @watch
    def nsx_call(self, path, method, data, headers={}, parse=True, timeout=None):
        """Run nsx https request
        
        :param path: Request path. Ex. /api/
        :param method: Request method. Ex. GET, POST, PUT, DELETE
        :param headers: Request headers. [default={}]. Ex. 
                        {"Content-type": "application/x-www-form-urlencoded",
                         "Accept": "text/plain"}
        :param data: Request data. [default={}]. Ex. 
                       {'@number': 12524, '@type': 'issue', '@action': 'show'}
        :param timeout: [defualt=None] optional request timeout
        :raise VsphereError:
        """
        try:
            if timeout is None:
                timeout = self.nsx[u'timeout']
            
            conn = httplib.HTTPSConnection(self.nsx[u'host'], self.nsx[u'port'], 
                                           timeout=timeout)
            
            # set simple authentication
            auth = base64.encodestring(u'%s:%s' % (self.nsx[u'user'], 
                                                   self.nsx[u'pwd'])).replace(u'\n', u'')
            headers[u'Authorization'] = u'Basic %s' % auth

            self.logger.info(u'Send %s request to %s' % (method, path))
            if data.lower().find(u'password') < 0:
                self.logger.debug(u'Send [headers=%s] [data=%s]' % 
                                  (headers, data))
            else:
                self.logger.debug(u'Send [headers=%s] [data=%s]' % 
                                  (headers, u'xxxxxxx')) 
            
            data = str(data)
            conn.request(method, path, data, headers)
            response = conn.getresponse()
            content_type = response.getheader(u'content-type')
            self.logger.info(u'Response status: %s %s' % 
                              (response.status, response.reason))            
        except Exception as error:
            self.logger.error(error, exc_info=True)
            raise VsphereError(error, code=400)            
        except httplib.HTTPException as error:
            self.logger.error(error, exc_info=True)
            raise VsphereError(error, code=400)
        
        # evaluate response status
        # BAD_REQUEST     400     HTTP/1.1, RFC 2616, Section 10.4.1
        if response.status == 400:
            res = response.read()
            self.logger.debug(u'Response [content-type=%s] [data=%s]' % 
                              (content_type, res))
            if parse is True and content_type.find(u'text/xml') >= 0 or \
                 content_type.find(u'application/xml') >= 0:
                res = xml2dict(res)
                msg = res[u'details']
            else:
                msg = u''
                
            self.logger.error(u'BAD_REQUEST - ' + msg, exc_info=True)
            raise VsphereError(u'BAD_REQUEST - ' + msg, code=400)
  
        # UNAUTHORIZED           401     HTTP/1.1, RFC 2616, Section 10.4.2
        elif response.status == 401:
            self.logger.error(u'UNAUTHORIZED', exc_info=True)
            raise VsphereError(u'UNAUTHORIZED', code=401)
        
        # PAYMENT_REQUIRED       402     HTTP/1.1, RFC 2616, Section 10.4.3
        
        # FORBIDDEN              403     HTTP/1.1, RFC 2616, Section 10.4.4
        elif response.status == 403:
            self.logger.error(u'FORBIDDEN', exc_info=True)
            raise VsphereError(u'FORBIDDEN', code=403)
        
        # NOT_FOUND              404     HTTP/1.1, RFC 2616, Section 10.4.5
        elif response.status == 404:
            self.logger.error(u'NOT_FOUND', exc_info=True)
            raise VsphereNotFound()
        
        # METHOD_NOT_ALLOWED     405     HTTP/1.1, RFC 2616, Section 10.4.6
        elif response.status == 405:
            self.logger.error(u'METHOD_NOT_ALLOWED', exc_info=True)
            raise VsphereError(u'METHOD_NOT_ALLOWED', code=405)
        # NOT_ACCEPTABLE         406     HTTP/1.1, RFC 2616, Section 10.4.7
        
        # PROXY_AUTHENTICATION_REQUIRED     407     HTTP/1.1, RFC 2616, Section 10.4.8
        
        # REQUEST_TIMEOUT        408
        elif response.status == 408:
            self.logger.error(u'REQUEST_TIMEOUT', exc_info=True)
            raise VsphereError(u'REQUEST_TIMEOUT', code=408)
        
        # INTERNAL SERVER ERROR  500
        elif response.status == 500:
            self.logger.error(u'CLOUDAPI_SERVER_ERROR', exc_info=True)
            raise VsphereError(u'CLOUDAPI_SERVER_ERROR', code=500)        
        
        # OK                     200    HTTP/1.1, RFC 2616, Section 10.2.1
        # CREATED                201    HTTP/1.1, RFC 2616, Section 10.2.2
        # ACCEPTED               202    HTTP/1.1, RFC 2616, Section 10.2.3
        # NON_AUTHORITATIVE_INFORMATION    203    HTTP/1.1, RFC 2616, Section 10.2.4
        # NO_CONTENT             204    HTTP/1.1, RFC 2616, Section 10.2.5
        # RESET_CONTENT          205    HTTP/1.1, RFC 2616, Section 10.2.6
        # PARTIAL_CONTENT        206    HTTP/1.1, RFC 2616, Section 10.2.7
        # MULTI_STATUS           207    WEBDAV RFC 2518, Section 10.2
        elif re.match(u'20[0-9]+', str(response.status)):
            try:
                #token = response.getheader('x-subject-token', None)
                #if token is not None:
                #    self.token = token
                    
                res = response.read()
                res_headers = response.getheaders()
                
                # get etag
                self.nsx[u'etag'] = response.getheader(u'etag', 0)
                
                self.logger.debug(u'Response [content-type=%s] [headers=%s] '\
                                  u'[data=%s]' % (content_type, 
                                  truncate(res_headers), truncate(res)))             
                
                if content_type is not None:
                    # json reqeust
                    if parse is True and content_type.find(u'application/json') >= 0:
                        res = json.loads(res)
                    elif parse is True and content_type.find(u'text/xml') >= 0 or \
                         parse is True and content_type.find(u'application/xml') >= 0:
                        res = xmltodict(res, dict_constructor=dict)
                    conn.close()
                else:
                    conn.close()
                return res
            except Exception as error:
                self.logger.error(error, exc_info=True)
                raise VsphereError(error, code=0)
        return None        
    
    # Shamelessly borrowed from:
    # https://github.com/dnaeon/py-vconnector/blob/master/src/vconnector/core.py
    @watch
    def collect_properties(self, view_ref, obj_type, path_set=None,
                           include_mors=False):
        """
        Collect properties for managed objects from a view ref
    
        Check the vSphere API documentation for example on retrieving
        object properties:
    
            - http://goo.gl/erbFDz
    
        Args:
            view_ref (pyVmomi.vim.view.*): Starting point of inventory navigation
            obj_type      (pyVmomi.vim.*): Type of managed object
            path_set               (list): List of properties to retrieve
            include_mors           (bool): If True include the managed objects
                                           refs in the result
    
        Returns:
            A list of properties for the managed objects
    
        """
        collector = self.si.content.propertyCollector
    
        # Create object specification to define the starting point of
        # inventory navigation
        obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True
    
        # Create a traversal specification to identify the path for collection
        traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__
        obj_spec.selectSet = [traversal_spec]
    
        # Identify the properties to the retrieved
        property_spec = vmodl.query.PropertyCollector.PropertySpec()
        property_spec.type = obj_type
    
        if not path_set:
            property_spec.all = True
    
        property_spec.pathSet = path_set
    
        # Add the object and property specification to the
        # property filter specification
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]
        filter_spec.propSet = [property_spec]
    
        # Retrieve properties
        props = collector.RetrieveContents([filter_spec])
        
        view_ref.Destroy()
    
        data = []
        for obj in props:
            properties = {}
            for prop in obj.propSet:
                properties[prop.name] = prop.val
    
            if include_mors:
                properties['obj'] = obj.obj
    
            data.append(properties)
        return data
    
    @watch
    def get_container_view(self, obj_type, container=None):
        """
        Get a vSphere Container View reference to all objects of type 'obj_type'
    
        It is up to the caller to take care of destroying the View when no longer
        needed.
    
        Args:
            obj_type (list): A list of managed object types
    
        Returns:
            A container view ref to the discovered managed objects
    
        """
        if not container:
            container = self.si.content.rootFolder

        view_ref = self.si.content.viewManager.CreateContainerView(
            container=container,
            type=obj_type,
            recursive=True
        )
        return view_ref
    
    @watch
    def get_object(self, morid, obj_type, container=None):
        cont = self.get_container_view(obj_type, container=container)
    
        obj = None
        for view in cont.view:
            if view._moId == morid:
                obj = view
                break
        return obj
    
    @watch
    def get_object_by_name(self, name, obj_type, container=None):
        cont = self.get_container_view(obj_type, container=container)
    
        obj = None
        for view in cont.view:
            if view.name == name:
                obj = view
                break
        return obj    
    
    @watch
    def query_nsx_job(self, jobid):
        """Query nsx job
        
        :param jobid: job id
        """
        res = self.nsx_call('/api/2.0/services/taskservice/job/%s' % (jobid),
                            'GET', '')
        return res
    
    @staticmethod
    def wait_task(self, task):
        self.logger.debug('Monitor task: %s' % task.name)
        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            time.sleep(0.1)
        
        if task.info.state in [vim.TaskInfo.State.error]:
            print "Error: %s" % task.info.error.msg
        if task.info.state in [vim.TaskInfo.State.success]:
            print "Completed"    
    
    def query_task(self, task, wait=None):
        """Query vsphere task.
        
        :param task: vsphere task
        :param wait: wait function to execute in each step of the loop
        :return: vsphere entity instance
        :raises ApiManagerError: raise :class:`.ApiManagerError`
        """
        try:
            # loop until job has finished
            self.logger.debug("Query vsphere task %s - START" % task.info.key)
            while task.info.state not in [vim.TaskInfo.State.success,
                                          vim.TaskInfo.State.error]:
                
                # update job status
                self.logger.debug("Query vsphere task %s - RUN: %s" % (
                        task.info.key, task.info.progress))
                
                if wait is not None:
                    wait()
                
            # vsphere task error
            if task.info.state in [vim.TaskInfo.State.error]:
                self.logger.error('Query vsphere task %s - ERROR - %s' % (
                    task.info.key, task.info.error.msg))
                raise VsphereError("Vsphere task %s failed. Error %s" % (
                    task.info.key, task.info.error.msg))
                                       
            # vsphere task completed
            elif task.info.state in [vim.TaskInfo.State.success]:
                self.logger.debug("Query vsphere task  %s - STOP" % (
                                  task.info.key))
                return task.info.result
        except vmodl.MethodFault as ex:
            self.logger.error(ex.msg, exc_info=True)
            raise VsphereError(ex.msg)    
    
    @staticmethod
    def wait_for_tasks(service_instance, tasks):
        """Given the service instance si and tasks, it returns after all the
       tasks are complete
       """
        property_collector = service_instance.content.propertyCollector
        task_list = [str(task) for task in tasks]
        # Create filter
        obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                     for task in tasks]
        property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                                   pathSet=[],
                                                                   all=True)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = obj_specs
        filter_spec.propSet = [property_spec]
        pcfilter = property_collector.CreateFilter(filter_spec, True)
        try:
            version, state = None, None
            # Loop looking for updates till the state moves to a completed state.
            while len(task_list):
                print '.'
                update = property_collector.WaitForUpdates(version)
                for filter_set in update.filterSet:
                    for obj_set in filter_set.objectSet:
                        task = obj_set.obj
                        for change in obj_set.changeSet:
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
                                state = change.val
                            else:
                                continue
    
                            if not str(task) in task_list:
                                continue
    
                            if state == vim.TaskInfo.State.success:
                                # Remove task from taskList
                                task_list.remove(str(task))
                            elif state == vim.TaskInfo.State.error:
                                raise task.info.error
                # Move to next version
                version = update.version
        finally:
            if pcfilter:
                pcfilter.Destroy()
                
class VsphereObject(object):
    """
    """
    def __init__(self, manager):
        self.logger = getLogger(self.__class__.__module__+ \
                                '.'+self.__class__.__name__)         
        
        self.manager = manager
        
    def call(self, path, method, data, headers={}, parse=True, timeout=None):
        if self.manager.nsx is None:
            raise VsphereError('Nsx is not configured')
        else:
            return self.manager.nsx_call(path, method, data, headers=headers, 
                                         parse=parse, timeout=timeout)        
        
    @watch
    def get_tags(self, entity):
        """
        """
        try:
            res = [t.key for t in entity.tag]
        except Exception as error:
            self.logger.error(error, exc_info=True)
            res = []
        
        return res
    
    @watch
    def assign_tag(self, entity, tag):
        """
        """
        try:
            tag_obj = vim.Tag()
            tag_obj.key = tag
            entity.tag.append(tag_obj)
        except Exception as error:
            self.logger.error(error, exc_info=True)
    
    @watch
    def remove_tag(self):
        """
        """
        pass
    
    @watch
    def permissions(self, entity):
        """
        """
        try:
            res = [{'group':p.Group,
                    'principal':p.principal,
                    'propagate':p.propagate,
                    'role':p.roleId
                    } for p in entity.permission]
        except Exception as error:
            self.logger.error(error, exc_info=True)
            res = []
        
        return res
    
    @watch
    def scheduled_tasks(self):
        """
        """
        pass
    
    @watch
    def info(self, obj):
        """Get info

        :param server: object obtained from api request
        :return: dict like {u'id':.., u'name':..}
        """
        try:
            data = {
                u'id':str(obj.get(u'obj')).split(u':')[1].rstrip(u"'"),
                u'name':get_attrib(obj, u'name', u''),
            }  
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = {}
        
        return data

    @watch
    def detail(self, obj):
        """Get detail

        :param obj: object obtained from api request
        :return: dict like {u'id':.., u'name':..}
        """
        try:
            info = {
                u'id':str(obj).split(u':')[1].rstrip(u"'"),
                u'name':obj.name
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}
        
        return info    

class VsphereSystem(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
        
        self._nsx = VsphereSystemNsx(manager)
        
    @property
    def nsx(self):
        if self.manager.nsx is None:
            raise VsphereError('Nsx is not configured')
        else:
            return self._nsx
        
    @watch
    def ping_vsphere(self):
        """Ping vsphere.
        
        :return: True if ping ok, False otherwise
        """
        try:
            self.manager.si.content.sessionManager.currentSession
            self.logger.info("Ping vsphere %s : OK" % self.manager.vsphere_id)
        except Exception as error:
            self.logger.error("Ping vsphere %s : KO" % self.manager.vsphere_id)
            return False
        return True
    
    @watch
    def ping_nsx(self):
        """Ping nsx.
        
        :return: True if ping ok, False otherwise
        """
        try:
            self.nsx.info()
            self.logger.info("Ping nsx %s : OK" % self.manager.nsx_id)
        except Exception as error:
            self.logger.error("Ping nsx %s : KO" % self.manager.nsx_id)
            return False
        return True            

class VsphereSystemNsx(VsphereSystem):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def info(self):
        """ """
        res = self.call('/api/1.0/appliance-management/global/info', 'GET', '')
        return res

    def global_info(self):
        """ """
        res = self.call('/api/1.0/appliance-management/global/info', 'GET', '')
        return res

    def summary_info(self):
        """ """
        res = self.call('/api/1.0/appliance-management/summary/system', 
                        'GET', '')
        return res

    #
    # appliance management
    #
    def reboot_appliance(self):
        """Reboots the appliance manager."""
        res = self.call('/api/1.0/appliance-management/system/restart', 
                        'POST', '')
        return res

    def query_appliance_cpu(self):
        """Query Appliance Manager CPU"""
        res = self.call('/api/1.0/appliance-management/system/cpuinfo', 
                        'GET', '')
        return res
    
    def query_appliance_uptime(self):
        """Query Appliance Manager Uptime"""
        res = self.call('/api/1.0/appliance-management/system/uptime', 
                        'GET', '')
        return res    

    def query_appliance_memory(self):
        """Query Appliance Manager Memory"""
        res = self.call('/api/1.0/appliance-management/system/meminfo', 
                        'GET', '')
        return res

    def query_appliance_storage(self):
        """Query Appliance Manager Storage"""
        res = self.call('/api/1.0/appliance-management/system/storageinfo', 
                        'GET', '')
        return res

    # network, dns
    def query_appliance_network(self):
        """Query Network Information"""
        res = self.call('/api/1.0/appliance-management/system/network', 
                        'GET', '')
        return res

    def configure_appliance_dns(self, ipv4_address='', ipv6A_adress='', 
                                domain_list=''):
        """Configures DNS servers.
        
        :param ipv4_address: 
        :param ipv4_address: 
        :param domain_list: 
        :return:
        :raise:
        """
        data = ['<dns>',
                '<ipv4Address>%s</ipv4Address>',
                '<ipv6Address>%s</ipv6Address>',
                '<domainList>%s</domainList>',
                '</dns>']
        data = ''.join(data) % (ipv4_address, ipv6A_adress, domain_list)
        res = self.call('/api/1.0/appliance-management/system/network/dns',  
                        'PUT', data, headers={'Content-Type':'text/xml'},
                        timeout=60)
        return res
    
    def delete_appliance_dns(self):
        """Deletes DNS servers."""
        res = self.call('/api/1.0/appliance-management/system/network/dns', 
                        'DELETE', '')
        return res    

    # time settings
    def query_appliance_time_settings(self):
        """Retrieves time settings like timezone or current date and time with 
        NTP server, if configured."""
        res = self.call('/api/1.0/appliance-management/system/timesettings', 
                        'GET', '')
        return res

    def configure_appliance_time_settings(self, ntp_server='', datetime='', 
                                timezone=''):
        """You can either configure time or specify the NTP server to be used 
        for time synchronization.
        
        :param ntpServer: 
        :param datetime: 
        :param timezone: 
        :return:
        :raise:
        """
        data = ['<timeSettings>',
                '<ntpServer>',
                '<string>%s</string>',
                '</ntpServer>',
                '<datetime>%s</datetime>',
                '<timezone>%s</timezone>',
                '</timeSettings>']
        data = ''.join(data) % (ntp_server, datetime, timezone)
        res = self.call('/api/1.0/appliance-management/system/timesettings',  
                        'PUT', data, headers={'Content-Type':'text/xml'},
                        timeout=60)
        return res
    
    def delete_appliance_time_settings(self):
        """Deletes NTP server."""
        res = self.call('/api/1.0/appliance-management/system/timesettings/ntp', 
                        'DELETE', '')
        return res
    
    # locals
    def query_appliance_local(self):
        """Retrieves locale information."""
        res = self.call('/api/1.0/appliance-management/system/locale', 
                        'GET', '')
        return res

    def configure_appliance_local(self, language='en', country='US', 
                                timezone=''):
        """Configures locale.
        
        :param language: 
        :param country:
        :return:
        :raise:
        """
        data = ['<locale>',
                '<language>%s</language>',
                '<country>%s</country>',
                '</locale>']
        data = ''.join(data) % (language, country)
        res = self.call('/api/1.0/appliance-management/system/locale',  
                        'PUT', data, headers={'Content-Type':'text/xml'},
                        timeout=60)
        return res  

    # syslog
    def query_appliance_syslog(self):
        """Retrieves syslog servers."""
        res = self.call('/api/1.0/appliance-management/system/syslogserver', 
                        'GET', '')
        return res

    def configure_appliance_syslog(self, hosname, port, protocol):
        """Configures syslog servers.
        
        If you specify a syslog server, NSX Manager sends all audit logs and 
        system events from NSX Manager to the syslog server.
        
        :param hosname: 
        :param port: 
        :param protocol: 
        :return:
        :raise:
        """
        data = ['<syslogserver>',
                '<syslogServer>%s</syslogServer>',
                '<port>%s</port>',
                '<protocol>%s</protocol>',
                '</syslogserver>']
        data = ''.join(data) % (hosname, port, protocol)
        res = self.call('/api/1.0/appliance-management/system/syslogserver',  
                        'PUT', data, headers={'Content-Type':'text/xml'},
                        timeout=60)
        return res
    
    def delete_appliance_syslog(self):
        """Deletes syslog servers."""
        res = self.call('/api/1.0/appliance-management/system/syslogserver', 
                        'DELETE', '')
        return res

    #
    # appliance components Components Management
    #
    def components_summary(self):
        """Retrieves summary of all available components available and their 
        status information."""
        res = self.call('/api/1.0/appliance-management/summary/components', 
                        'GET', '')
        return res[u'componentsByGroup']
    
    def query_appliance_components(self):
        """Retrieves all Appliance Manager components."""
        res = self.call('/api/1.0/appliance-management/components', 
                        'GET', '')
        return res[u'components']
    
    def query_appliance_component(self, component):
        """Retrieves details for the specified component ID.
        
        :param component: component id
        """
        res = self.call('/api/1.0/appliance-management/components/component/%s' % component, 
                        'GET', '')
        return res
    
    def query_appliance_component_dependency(self, component):
        """Retrieves dependency details for the specified component ID.
        
        :param component: component id
        """
        res = self.call('/api/1.0/appliance-management/components/component/%s/dependencies' % component, 
                        'GET', '')
        return res 

    def query_appliance_component_status(self, component):
        """Retrieves current status for the specified component ID.
        
        :param component: component id
        """
        res = self.call('/api/1.0/appliance-management/components/component/%s/status' % component, 
                        'GET', '')
        return res
    
    def toggle_appliance_component_status(self, component):
        """Toggles component status.
        
        :param component: component id
        """
        res = self.call('/api/1.0/appliance-management/components/component/%s/toggleStatus/command' % component, 
                        'GET', '')
        return res    

    def restart_appliance_webapp(self):
        """Restarts appliance management web application."""
        res = self.call('/api/1.0/appliance-management/components/component/APPMGMT/restart', 
                        'POST', '')
        return res

    #
    # appliance backup
    # 
    '''You can back up and restore your NSX Manager data, which can include 
    system configuration, events, and audit log tables. Configuration tables are 
    included in every backup. Backups are saved to a remote location that must 
    be accessible by the NSX Manager.
    For information on backing up controller data, see Backup Controller Data
    on page 34.'''
    # Configure Backup Settings
    # Configure On-Demand Backup
    # Query Backup Settings
    # Delete Backup Configuration
    # Query Available Backups
    # Restore Data
    
    #
    # Working with Tech Support Logs
    #
    
    #
    # Querying NSX Manager Logs
    #
    def get_system_events(self, start_index=0, page_size=10, 
                         sort_order_ascending=False):
        """You can retrieve NSX Manager system events.
        
        :param start_index: start index is an optional parameter which specifies 
            the starting point for retrieving the logs. If this parameter is not 
            specified, logs are retrieved from the beginning.
        :param page_size: page size is an optional parameter that limits the 
            maximum number of entries returned by the API. The default value for 
            this parameter is 256 and the valid range is 1-1024.
        :param sort_order_ascending: if False sort item descendant by id
        """
        res = self.call('/api/2.0/systemevent?startIndex=%s&pageSize=%s&sortOrderAscending=%s' % 
                        (start_index, page_size, sort_order_ascending),  'GET', '')
        return res[u'pagedSystemEventList'][u'dataPage']
    
    def get_system_audit_logs(self, start_index=0, page_size=10, 
                              sort_order_ascending=False):
        """You can get NSX Manager audit logs.
        
        :param start_index: start index is an optional parameter which specifies 
            the starting point for retrieving the logs. If this parameter is not 
            specified, logs are retrieved from the beginning.
        :param page_size: page size is an optional parameter that limits the 
            maximum number of entries returned by the API. The default value for 
            this parameter is 256 and the valid range is 1-1024.
        :param sort_order_ascending: if False sort item descendant by id
        """
        res = self.call('/api/2.0/auditlog?startIndex=%s&pageSize=%s&sortOrderAscending=%s' % 
                        (start_index, page_size, sort_order_ascending),  'GET', '')
        return res[u'pagedAuditLogList'][u'dataPage']

    #
    # Working with Support Notifications
    #

    #
    # transport_zones
    #
    def list_transport_zones(self):
        """ """
        res = self.call('/api/2.0/vdn/scopes',  'GET', '')
        return res
    
    #
    # controller
    #    
    def list_controllers(self):
        """Retrieves details and runtime status for controller. 
        Runtime status can be one of the following:
        
        - Deploying: controller is being deployed and the procedure has not 
                     completed yet. 
        - Removing: controller is being removed and the procedure has not 
                    completed yet. 
        - Running: controller has been deployed and can respond to API 
                   invocation. 
        - Unknown: controller has been deployed but fails to respond to API 
                   invocation.
        """
        res = self.call('/api/2.0/vdn/controller',  'GET', '')
        resp = res[u'controllers']
        if isinstance(resp, list):
            return resp
        else:
            return [resp]

    def query_controller_progress(self, job_id):
        """Retrieves status of controller creation or removal. The progress 
        gives a percentage indication of current deploy / remove procedure.
        """
        res = self.call('/api/2.0/vdn/controller/progress/job_id',  'GET', '')
        return res
        #return res['virtualWires']['dataPage']['virtualWire']   

    def create_controller(self, name, desc, ):
        """Create controller
        
        TODO:
        
        :param scope_id: transport zone id
        :param name: logical switch name
        :param desc: logical switch desc
        :param tenant: tenant id [default="virtual wire tenant"]
        :param guest_allowed: [default='true']
        """
        data = ['<virtualWireCreateSpec>',
                '<name>%s</name>' % name,
                '<description>%s</description>' % desc,
                '<tenantId>%s</tenantId>' % tenant,
                '<controlPlaneMode>UNICAST_MODE</controlPlaneMode>',
                '<guestVlanAllowed>%s</guestVlanAllowed>' % guest_allowed,
                '</virtualWireCreateSpec>']
        data = ''.join(data)
        res = self.call('/api/2.0/vdn/scopes/%s/virtualwires' % scope_id,  
                        'POST', data, headers={'Content-Type':'text/xml'},
                        timeout=120)
        return res

    def delete_controller(self, controller):
        """Deletes NSX controller. When deleting the last controller from a 
        cluster, the parameter forceRemovalForLast must be set to true.
        
        :param controller: controller id
        """
        res = self.call('/api/2.0/vdn/controller/%s?forceRemoval=true' % controller,  
                        'DELETE', '')
        return res
        #return res['virtualWires']['dataPage']['virtualWire']  

class VsphereDatacenter(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
        
    @watch
    def list(self):
        """Get _datacenters with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']        
        """
        props = ['name', 'parent', 'overallStatus']
        view = self.manager.get_container_view(obj_type=[vim.Datacenter])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.Datacenter,
                                               path_set=props,
                                               include_mors=True)
        return data
    
    @watch
    def get(self, morid):
        """Get _datacenter by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        obj = self.manager.get_object(morid, [vim.Datacenter], container=None)
        return obj

    @watch
    def remove(self, dc):
        """
        :param dc: dc instance. Get with get_by_****
        """
        task = dc.Destroy_Task()
        return task

    #
    # summary
    #
    @watch
    def info(self, dc):
        """
        :param dc: dc instance. Get with get_by_****
        """
        info = {
            u'id':str(dc.get(u'obj')).split(u':')[1].rstrip(u"'"),
            u'name':get_attrib(dc, u'name', u''),
        }
        return info

class VsphereFolder(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    @watch
    def list(self):
        """Get folders with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']        
        """
        props = ['name', 'parent', 'childType', 'overallStatus']
        view = self.manager.get_container_view(obj_type=[vim.Folder])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.Folder,
                                               path_set=props,
                                               include_mors=True)
        return data
    
    @watch
    def get(self, morid):
        """Get folder by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        obj = self.manager.get_object(morid, [vim.Folder], container=None)
        return obj
    
    @watch
    def create(self, name, folder=None, datacenter=None, host=False,
               network=False, storage=False, vm=False):
        """Creates a folder.
    
        :param name: String Name for the folder
        :param folder: parent folder
        :param datacenter: parent datacenter
        :param host: if True create a host subfolder 
        :param network: if True create a network subfolder 
        :param storage: if True create a storage subfolder 
        :param vm: if True create a vm subfolder 
        """
        try:
            if folder is not None:
                folder = folder.CreateFolder(name=name)
            elif datacenter is not None:
                # vm folder
                if vm is True:
                    folder = datacenter.vmFolder.CreateFolder(name=name)
                #  Datastore folder
                elif storage is True:
                    folder = datacenter.datastoreFolder.CreateFolder(name=name)
                # host folder 
                elif host is True:
                    folder = datacenter.hostFolder.CreateFolder(name=name)
                # Network folder
                elif network is True:
                    folder = datacenter.networkFolde.CreateFolder(name=name)
                else:
                    raise vmodl.MethodFault(msg='No type of folder is been specified')      
            else:
                raise vmodl.MethodFault(msg='No parent folder is been specified')
                
            self.logger.debug('Create folder %s in %s' % (name, folder.name))
            return folder
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)

    @watch
    def remove(self, folder):
        """
        :param folder: folder instance. Get with get_by_****
        """
        task = folder.Destroy_Task()
        return task

    @watch
    def update(self, folder, name):
        """
        :param folder: folder instance. Get with get_by_****
        :param name: new folder name
        """
        task = folder.Rename_Task(name)
        return task

    #
    # summary
    #
    @watch
    def info(self, obj):
        """
        :param obj: folder instance. Get with get_by_****
        """
        try:
            info = {
                u'id':str(obj.get(u'obj')).split(u':')[1].rstrip(u"'"),
                u'name':get_attrib(obj, u'name', u''),
                u'type':u','.join(get_attrib(obj, u'childType', u'')),
                u'parent':str(obj.get(u'parent')).split(u':')[1].rstrip(u"'"),
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}        
        return info
    
    @watch
    def detail(self, obj):
        """
        :param obj: folder instance. Get with get_by_****
        """    
        try:
            info = {
                u'id':str(obj).split(u':')[1].rstrip(u"'"),
                u'name':obj.name,
                u'type':obj.childType,
                u'parent':str(obj.parent).split(u':')[1].rstrip(u"'"),
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}
        return info

    #
    # monitor
    #

    #
    # manage
    #
    
    #
    # related object
    #
    @watch
    def get_servers(self, folder):
        """Get servers with some properties
        """
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine],
                                               container=folder)
        vm_data = self.manager.collect_properties(view_ref=view,
                                                  obj_type=vim.VirtualMachine,
                                                  path_set=self.manager.server_props,
                                                  include_mors=True)
        return vm_data    

class VsphereVApp(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
        
    @watch
    def list(self):
        """Get vapp with some properties:   
        """
        properties = ["name", "parent", "overallStatus"]
        
        view = self.manager.get_container_view(obj_type=[vim.VirtualApp],
                                               container=None)
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.VirtualApp,
                                               path_set=properties,
                                               include_mors=True)
        return data
    
    @watch
    def get(self, morid):
        """Get vapp by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.VirtualApp], 
                                      container=container)
        return obj

    @watch
    def create(self):
        """"""
        pass
    
    @watch
    def update(self, vapp):
        """
        :param vapp: vapp instance. Get with get_by_****
        """
        # TODO
        #task = server.Destroy_Task()
        task = None
        return task

    @watch
    def remove(self, vapp):
        """
        :param vapp: vapp instance. Get with get_by_****
        """
        task = vapp.Destroy_Task()
        return task    

    #
    # summary
    #
    @watch
    def info(self, vapp):
        """
        :param vapp: vapp instance. Get with get_by_****
        """
        return {}

    #
    # monitor
    #

    #
    # manage
    #
    
    #
    # related object
    #

class VsphereServer(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
        
        self.monitor = VsphereServerMonitor(self)
        self.hardware = VsphereServerHardware(self)
        self.snapshot = VsphereServerSnapshot(self)
        
    @watch
    def __list(self, template=False):
        """Get servers with some properties.
        
        :param template: if True search only template server
        """
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine],
                                               container=None)
        vm_data = self.manager.collect_properties(view_ref=view,
                                                  obj_type=vim.VirtualMachine,
                                                  path_set=self.manager.server_props,
                                                  include_mors=True)
        
        if template is True:
            vm_data = [vm for vm in vm_data if vm[u'config.template'] == True]

        return vm_data
    
    @watch
    def get_by_morid(self, morid):
        """Get server by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.VirtualMachine], 
                                      container=container)
        return obj
    
    @watch
    def get_by_uuid(self, uuid):
        """Get server by uuid."""
        search_index = self.manager.si.content.searchIndex
    
        obj = search_index.FindByUuid(None, uuid, True, True)
        return obj
    
    @watch
    def get_by_dnsname(self, name):
        """Get server by dnsname."""
        search_index = self.manager.si.content.searchIndex
    
        obj = search_index.FindByDnsName(None, name, True)
        return obj
    
    @watch
    def get_by_name(self, name):
        """Get server by name."""
        container = None
        obj = self.manager.get_object_by_name(name, [vim.VirtualMachine], 
                                              container=container)
        return obj

    @watch
    def get_by_ip(self, ipaddress):
        """Get server by ipaddress."""
        search_index = self.manager.si.content.searchIndex
    
        obj = search_index.FindByIp(None, ipaddress, True)
        return obj

    @watch
    def list(self, template=False, morid=None, uuid=None, name=None, 
             ipaddress=None, dnsname=None):
        if morid is not None:
            return [self.get_by_morid(morid)]
        elif uuid is not None:
            return [self.get_by_uuid(uuid)]
        elif dnsname is not None:
            return [self.get_by_dnsname(dnsname)]
        elif name is not None:
            return [self.get_by_name(name)]        
        elif ipaddress is not None:
            return [self.get_by_ip(ipaddress)]
        else:
            return self.__list(template)
        
    @watch
    def get(self, oid):
        return self.get_by_morid(oid)

    @watch
    def create(self, name, guest_id, resource_pool, datastore, folder, 
               network, memory_mb=1024, cpu=1, core_x_socket=1, 
               disk_size_gb=5, version='vmx-10', power_on=False):
        """Creates a VirtualMachine.
    
        :param name: String Name for the VirtualMachine
        :param folder: Folder to place the VirtualMachine in
        :param resource_pool: ResourcePool to place the VirtualMachine in
        :param datastore: DataStrore to place the VirtualMachine on
        :param network: Network to attach
        :param memory_mb:
        :param cpu: 
        :param core_x_socket: 
        :param disk_size_gb:
        :param version: vmx-8 , vmx-9, vmx-10, vmx-11
        :param power_on: power_on status [defualt=False]
        """
        try:
            datastore_path = '[' + datastore + '] ' + name
        
            # bare minimum VM shell, no disks. Feel free to edit
            vmx_file = vim.vm.FileInfo(logDirectory=None,
                                       snapshotDirectory=None,
                                       suspendDirectory=None,
                                       vmPathName=datastore_path)
        
            dev_changes = []
    
            # add ide controller
            #ide_spec = vim.vm.device.VirtualDeviceSpec()
            #ide_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            #ide_spec.device = vim.vm.device.VirtualIDEController()
            #ide_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
            #ide_spec.device.key = 200
            #dev_changes.append(ide_spec)    
            
            # add ps2 controller
            #ps2_spec = vim.vm.device.VirtualDeviceSpec()
            #ps2_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            #ps2_spec.device = vim.vm.device.VirtualPS2Controller()
            #e_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
            #ps2_spec.device.key = 300
            #dev_changes.append(ps2_spec)
            
            # add pci controller
            pci_spec = vim.vm.device.VirtualDeviceSpec()
            pci_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            pci_spec.device = vim.vm.device.VirtualPCIController()
            #ide_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
            pci_spec.device.key = 100
            dev_changes.append(pci_spec)
            
            # add scsi controller
            scsi_spec = vim.vm.device.VirtualDeviceSpec()
            scsi_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            scsi_spec.device = vim.vm.device.ParaVirtualSCSIController()
            scsi_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
            scsi_spec.device.key = 5000
            dev_changes.append(scsi_spec)
            
            # add disk
            disk_type = 'thin'
            new_disk_kb = disk_size_gb * 1024 * 1024
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.fileOperation = "create"
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            disk_spec.device = vim.vm.device.VirtualDisk()
            disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            if disk_type == 'thin':
                disk_spec.device.backing.thinProvisioned = True
            disk_spec.device.backing.diskMode = 'persistent'
            disk_spec.device.unitNumber = 0
            disk_spec.device.capacityInKB = new_disk_kb
            disk_spec.device.controllerKey = scsi_spec.device.key    
            dev_changes.append(disk_spec)
            
            # add vim.vm.device.VirtualKeyboard
            #dev_spec = vim.vm.device.VirtualDeviceSpec()
            #dev_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            #dev_spec.device = vim.vm.device.VirtualKeyboard()
            #dev_spec.device.backing = None
            #dev_spec.device.controllerKey = ps2_spec.device.key
            #dev_changes.append(dev_spec)
            
            # add vim.vm.device.VirtualCdrom
            dev_spec = vim.vm.device.VirtualDeviceSpec()
            dev_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            dev_spec.device = vim.vm.device.VirtualCdrom()
            dev_spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
            #dev_spec.device.backing.exclusive = False
            #dev_spec.device.backing.deviceName = 'cdrom0'
            #dev_spec.connectable
            dev_spec.device.controllerKey = 200 #ide_spec.device.key
            dev_changes.append(dev_spec)
            
            # add network card
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()
            nic_spec.device.addressType = 'Generated'
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nic_spec.device.backing.port = vim.dvs.PortConnection()    
            nic_spec.device.backing.port.portgroupKey = network.key
            nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid     
            nic_spec.device.wakeOnLanEnabled = False
            dev_changes.append(nic_spec)
        
            config = vim.vm.ConfigSpec(name=name, 
                                       memoryMB=memory_mb,
                                       numCPUs=cpu,
                                       numCoresPerSocket=core_x_socket,
                                       deviceChange=dev_changes,
                                       files=vmx_file, 
                                       guestId=guest_id,
                                       version=version)
        
            task = folder.CreateVM_Task(config=config, pool=resource_pool)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)        
    
    @watch
    def create_from_library(self):
        """"""
        pass
    
    @watch
    def create_linked_clone(self, server, name, folder, datastore, 
                            resource_pool, power_on=False):
        """Clone a linked clone VirtualMachine from another.
        Ref: http://pubs.vmware.com/vsphere-60/index.jsp#com.vmware.wssdk.pg.doc/PG_VM_Manage.13.4.html#1115589
        https://www.vmware.com/support/ws55/doc/ws_clone_template_enabling.html
        
        :param name: String Name for the VirtualMachine
        :param folder: Folder to place the VirtualMachine in
        :param resource_pool: ResourcePool to place the VirtualMachine in
        :param server: parent VirtualMachine
        :param power_on: power_on status [defualt=False]
        """
        try:
            # set relospec
            relospec = vim.vm.RelocateSpec()
            relospec.diskMoveType = vim.vm.RelocateSpec.DiskMoveOptions.createNewChildDiskBacking
            relospec.datastore = datastore
            relospec.pool = resource_pool
        
            clonespec = vim.vm.CloneSpec()
            clonespec.location = relospec
            clonespec.powerOn = power_on
            clonespec.memory = False
            clonespec.template = False
            clonespec.snapshot = server.snapshot.currentSnapshot
        
            task = server.CloneVM_Task(folder=folder, name=name, spec=clonespec)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)     
    
    @watch
    def create_from_template(self, template, name, folder, datastore, 
                             resource_pool, power_on=False):
        """Creates a VirtualMachine from template.
    
        :param name: String Name for the VirtualMachine
        :param folder: Folder to place the VirtualMachine in
        :param resource_pool: ResourcePool to place the VirtualMachine in
        :param template: template VirtualMachine
        :param network: Network to attach
        :param version: vmx-8 , vmx-9, vmx-10, vmx-11
        :param power_on: power_on status [defualt=False]
        """
        try:
            # set relospec
            relospec = vim.vm.RelocateSpec()
            relospec.datastore = datastore
            relospec.pool = resource_pool
        
            clonespec = vim.vm.CloneSpec()
            clonespec.location = relospec
            clonespec.powerOn = power_on
        
            task = template.Clone(folder=folder, name=name, spec=clonespec)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)     
    
    @watch
    def create_from_template_library(self):
        """"""
        pass    

    @watch
    def update(self, server, name=None, notes=None):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            spec = vim.vm.ConfigSpec()
            if notes is not None:
                spec.annotation = notes
            if name is not None:
                spec.name = name
                
            task = server.ReconfigVM_Task(spec)
            self.logger.debug(u"Update server %s in vSphere" % (server))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)    

    @watch
    def remove(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.Destroy_Task()
            self.logger.debug(u"Destroying server %s from vSphere" % (server))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)

    #
    # summary
    #
    def data(self, server):
        try:
            server.config
            return self.detail(server)
        except:
            return self.info(server)
    
    def info(self, server):
        """Get server info
        
        :param server: server object obtained from api request
        :param flavor_idx: index of flavor object obtained from api request
        :param volume_idx: index of volume object obtained from api request
        :param image_idx: index of image object obtained from api request
        :return: dict like
        
            {u'cpu': 2,
              u'disk': None,
              u'hostname': 'tst-beehive-04',
              u'id': 'vim.VirtualMachine:vm-2287',
              u'ip_address': ['10.102.184.54'],
              u'memory': 2048,
              u'name': 'tst-beehive-04',
              u'os': 'CentOS 4/5/6/7 (64-bit)',
              u'state': 'poweredOn',
              u'template': False}
        """
        try:
            data = {
                u'id':str(server.get(u'obj')).split(u':')[1].rstrip(u"'"),
                u'name':get_attrib(server, u'name', u''),
                u'os':get_attrib(server, u'config.guestFullName', u''),
                u'memory':get_attrib(server, u'config.hardware.memoryMB', u''),
                u'cpu':get_attrib(server, u'config.hardware.numCPU', u''),
                u'state':get_attrib(server, u'runtime.powerState', u''),
                u'template':get_attrib(server, u'config.template', u''),
                u'hostname':get_attrib(server, u'guest.hostName', u''),
                u'ip_address':[get_attrib(server, u'guest.ipAddress', u'')],
                u'disk':None
            }  
        except Exception as error:
            self.logger.error(error, exc_info=True)
            data = {}
        
        return data
    
    def detail(self, server):
        """Get server detail
        
        :param server: server object
        :return: dict like
        
            {u'date': {u'created': None, u'launched': u'2017-03-10T17:49:39', u'terminated': None, u'updated': None},
             u'flavor': {u'cpu': 4, u'id': None, u'memory': 2048},
             u'hostname': 'prova01',
             u'id': u'vim.VirtualMachine:vm-2739',
             u'metadata': None,
             u'name': 'instance04-server',
             u'networks': [{u'dns': ['10.102.184.2', '10.102.184.3'],
                            u'fixed_ips': '10.102.184.55',
                            u'mac_addr': '00:50:56:a1:55:4e',
                            u'name': 'Network adapter 1',
                            u'net_id': 'dvportgroup-82',
                            u'port_state': True}],
             u'os': 'CentOS 4/5/6/7 (64-bit)',
             u'state': 'poweredOn',
             u'volumes': [{u'bootable': None,
                           u'format': None,
                           u'id': '[DS_EX_OPSTK_VSP_LUN_00] instance04-server/instance04-server.vmdk',
                           u'mode': 'persistent',
                           u'name': 'Hard disk 1',
                           u'size': 50.0,
                           u'storage': 'DS_EX_OPSTK_VSP_LUN_00',
                           u'type': None}],
             u'vsphere:firmware': 'bios',
             u'vsphere:linked': {u'linked': False, u'parent': None},
             u'vsphere:managed': None,
             u'vsphere:notes': '',
             u'vsphere:template': False,
             u'vsphere:tools': {u'status': 'guestToolsRunning', u'version': '10246'},
             u'vsphere:uuid': '5021ebf0-a489-6876-a94c-ac58d9d02fed',
             u'vsphere:vapp': None,
             u'vsphere:version': 'vmx-11'}     
        """
        try:
            server_volumes = []
            networks = []
            
            vm = server
            hw = server.config.hardware
            
            for device in hw.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    net = {u'name':device.deviceInfo.label,
                           u'mac_addr':device.macAddress,
                           u'fixed_ips':vm.guest.ipAddress,
                           u'dns':None,
                           u'net_id':None,
                           u'port_state':device.connectable.connected}

                    if hasattr(device.backing, u'port'):
                        port_group_ext_id = device.backing.port.portgroupKey
                        net[u'net_id'] = port_group_ext_id
                    
                    try:
                        self.check_guest_tools(vm)                    
                    
                        for conf in vm.guest.ipStack:
                            net[u'dns'] = [ip for ip in conf.dnsConfig.ipAddress if
                                           ip != u'127.0.0.1']
                    except Exception as ex:
                        pass
                                
                    networks.append(net)
                    
                #if hasattr(device.backing, 'fileName'):
                elif type(device) == vim.vm.device.VirtualDisk:
                    vol = {u'bootable':None,
                           u'format':None,
                           u'id':device.backing.fileName,
                           u'mode':device.backing.diskMode,
                           u'name':device.deviceInfo.label,
                           u'size':round(device.capacityInBytes/1073741824, 0),
                           u'storage':None,
                           u'type': None}
                    
                    datastore = device.backing.datastore
                    if datastore is not None:
                        vol[u'storage'] = datastore.name
                    server_volumes.append(vol)             
            
            try:
                launched = str2uni(vm.runtime.bootTime.strftime(
                                "%Y-%m-%dT%H:%M:%S"))
            except:
                launched = None
            
            info = {
                u'id':str(server),
                u'name':server.name,
                u'hostname':server.guest.hostName,
                u'os':vm.summary.config.guestFullName,
                u'state':vm.runtime.powerState,
                u'flavor':{
                    u'id':None,
                    u'memory':hw.memoryMB,
                    u'cpu':int(hw.numCPU)*int(hw.numCoresPerSocket),
                },
                u'networks':networks,
                u'volumes':server_volumes,
                u'date':{u'created':None,
                         u'updated':None,
                         u'launched':launched,
                         u'terminated':None},
                u'metadata':None,
                
                u'vsphere:version':vm.config.version,
                u'vsphere:firmware':vm.config.firmware,                    
                u'vsphere:template':vm.config.template,
                u'vsphere:uuid': vm.config.instanceUuid,
                u'vsphere:managed':vm.config.managedBy,
                u'vsphere:tools':{u'status':vm.guest.toolsRunningStatus,
                                  u'version':vm.guest.toolsVersion},
                u'vsphere:notes':vm.config.annotation,
                u'vsphere:vapp':None,
                u'vsphere:linked':self.is_linked_clone(server)}
            
            # vapp info
            if vm.parentVApp is not None:
                info[u'vsphere:vapp'] = {u'ext_id':vm.parentVApp._moId, u'name':vm.parentVApp.name}
        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}
        
        return info

    @watch
    def is_linked_clone(self, server):
        """Check if virtual machine is a linked clone and return parent 
        virtual machine
        
        :param server: server instance
        :return: dictionary with linked clone check and linked server name
         """
        name = server.name
        linked = False
        linked_server = None            
        for item in server.layoutEx.file:
            # checK if server contain backing file 
            if not item.name.find(name) >= 0:
                linked = True
                # get parent server name
                start = item.name.index('] ') + 2
                end = item.name.index('/', start)
                linked_server = item.name[start:end]
                
        return {u'linked':linked, u'parent':linked_server}

    @watch
    def guest_info(self, server):
        """Server guest info
        """
        try:
            vm = server.guest
            
            info = {u'hostname':vm.hostName,
                    u'ip_address':vm.ipAddress,
                    u'tools':{u'status':vm.toolsStatus,
                              u'version_status':vm.toolsVersionStatus,
                              u'version_status2':vm.toolsVersionStatus2,
                              u'running_status':vm.toolsRunningStatus,
                              u'version':vm.toolsVersion},
                    u'guest':{
                        u'id':vm.guestId,
                        u'family':vm.guestFamily,
                        u'fullname':vm.guestFullName,
                        u'state':vm.guestState,
                        u'app_heartbeat_status':vm.appHeartbeatStatus,
                        u'guest_kernel_crashed':vm.guestKernelCrashed,
                        u'app_state':vm.appState,
                        u'operations_ready':vm.guestOperationsReady,
                        u'interactive_operations_ready':vm.interactiveGuestOperationsReady,
                        u'state_change_supported':vm.guestStateChangeSupported,
                        u'generation_info':vm.generationInfo},
                    u'ip_stack':[],
                    u'nics':[],
                    u'disk':[],
                    u'screen':{u'width':vm.screen.width,
                               u'height':vm.screen.height}}
            
            for conf in vm.disk:
                info[u'disk'].append({
                    u'diskPath':conf.diskPath,
                    u'capacity':u'%sMB' % (conf.capacity/1048576),
                    u'free_space':u'%sMB' % (conf.freeSpace/1048576)})
                        
            for conf in vm.ipStack:
                info[u'ip_stack'].append({
                    u'dns_config':{
                        u'dhcp':conf.dnsConfig.dhcp,
                        u'hostname':conf.dnsConfig.hostName,
                        u'domainname':conf.dnsConfig.domainName,
                        u'ip_address':[ip for ip in conf.dnsConfig.ipAddress],
                        u'search_domain':[c for c in conf.dnsConfig.searchDomain]},
                    u'ip_route_config':[
                        {u'network':u'%s/%s' % (c.network, c.prefixLength),
                         u'gateway':c.gateway.ipAddress} for c in conf.ipRouteConfig.ipRoute],
                    u'ipStackConfig':[i for i in conf.ipStackConfig],
                    u'dhcpConfig':conf.dhcpConfig})
            
            for nic in vm.net:
                info[u'nics'].append({
                    u'network':nic.network,
                    u'mac_address':nic.macAddress,
                    u'connected':nic.connected,
                    u'device_config_id':nic.deviceConfigId,
                    u'dnsConfig':nic.dnsConfig,
                    u'ip_config':{
                        u'dhcp':nic.ipConfig.dhcp,
                        u'ip_address':[u'%s/%s' % (i.ipAddress, i.prefixLength) 
                                       for i in nic.ipConfig.ipAddress]},
                    u'netbios_config':nic.netBIOSConfig})
            
        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}
        
        return info
    
    @watch
    def network(self, server):
        """Server network
        """
        res = []
        for n in server.network:
            try: nid = self.container.get_networks(ext_id=n._moId)[0].oid
            except: nid = None
            res.append({u'id':n._moId, 
                        u'name':n.name, 
                        u'type':type(n).__name__})
        return res     
    
    @watch
    def runtime(self, server):
        """Server runtime info
        """
        try:
            vm = server.runtime
            
            res = {u'boot_time':vm.bootTime,
                   u'resource_pool':{u'id':server.resourcePool._moId, 
                                     u'name':server.resourcePool.name},                   
                   u'host':{u'id':vm.host._moId,
                            u'name':vm.host.name,
                            u'parent_id':vm.host.parent._moId,
                            u'parent_name':vm.host.parent.name}} 
        except Exception as error:
            self.logger.error(error, exc_info=True)
            res = {}
        
        return res

    @watch
    def usage(self, server):
        """Cpu, memory, storage usage
        """
        try:
            res = server.summary.quickStats
        except Exception as error:
            self.logger.error(error, exc_info=True)
            res = {}
        
        return res            

    @watch
    def security_tags(self):
        """
        """
        pass

    @watch
    def security_groups(self, sever):
        """
        :param moid: server morid
        """
        vmid = sever._moId
        res = self.call('/api/2.0/services/securitygroup/lookup/virtualmachine/%s' % vmid,
                        'GET', '')
        self.logger.debug(res)
        try:
            return res['securityGroups']['securityGroups']['securitygroup']
        except:
            return []

    @watch
    def advanced_confugration(self):
        """
        """
        pass

    @watch
    def related_objects(self):
        """Cluster, host, networks, storage
        """
        pass

    @watch
    def vapp_details(self):
        """
        """
        pass

    #
    # remote console
    @watch
    def remote_console(self, server, to_host=True, to_vcenter=False):
        """
        
        :param server: server instance
        :param to_host: if True open ticket and sessione over esxi host
        :param to_vcenter: if True open ticket and sessione over esxi host
        """
        try:
            if to_vcenter is True:
                content = self.manager.si.RetrieveContent()
                #content = self.manager.si.content
                vm_moid = server._moId                
                
                vcenter_data = content.setting
                vcenter_settings = vcenter_data.setting
                console_port = '9443'

                for item in vcenter_settings:
                    key = getattr(item, 'key')
                    if key == 'VirtualCenter.FQDN':
                        vcenter_fqdn = getattr(item, 'value')
            
                session_manager = content.sessionManager
                ticket = session_manager.AcquireCloneTicket()
                #spec = vim.SessionManager.ServiceRequestSpec()
                #ticket = session_manager.AcquireGenericServiceTicket(spec)
                #self.vcenter_session
                host = self.manager.vcenter_conn[u'host']
                port = self.manager.vcenter_conn[u'port']
                vc_cert = ssl.get_server_certificate((host, port))
                vc_pem = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM,
                                                         vc_cert)
                vc_fingerprint = vc_pem.digest('sha1')
    
                uri = ["wss://%s:%s/vsphere-client/webconsole/authd?",
                       "vmId=%s&vmName=%s&host=%s:%s&sessionTicket=%s"]
                uri = [u'https://%s:%s/vsphere-client/webconsole.html?',
                       u'vmId=%s&vmName=%s&host=%s:%s&sessionTicket=%s',
                       u'&thumbprint=%s',
                       u'&serverGuid=19de7544-3057-4069-b43e-785157ffc309&locale=en_US']
                #serverGuid
                #ticket ='cst-VCT-5242c443-9310-61a1-c7a5-5e3aae4abed5--tp-13-9D-7B-AF-52-80-7D-51-4F-13-A3-A3-16-C0-B9-3B-3F-54-3C-B9'
                #guid = '64b9af30-f59d-4e86-9e07-0cba501e1d5a'
                uri = u''.join(uri) % (host, console_port, vm_moid, server.name,
                                       host, console_port, ticket, vc_fingerprint)
                #res = "wss://%s:%s/ticket/%s"% (host, console_port, ticket)

                res = {u'ticket':ticket,
                       u'cfgFile':None,
                       u'host':server.name,
                       u'port':console_port,
                       u'sslThumbprint':vc_fingerprint,
                       u'uri':uri}
            elif to_host is True:
                #data = server.AcquireTicket('mks')
                data = server.AcquireTicket('webmks')

                res = {u'ticket':data.ticket,
                       u'cfgFile':data.cfgFile,
                       u'host':data.host,
                       u'port':data.port,
                       u'sslThumbprint':data.sslThumbprint,
                       u'uri':u'wss://%s:%s/ticket/%s' % (data.host, data.port, data.ticket)}
                
            self.logger.debug(u'Get remote console for server %s' % server.name)
            return res
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    #
    # guest access
    #    
    @watch
    def check_guest_tools(self, server):
        """
        """
        # get guest tools status
        tools_status = server.guest.toolsRunningStatus
        if (tools_status == 'guestToolsNotRunning'):
            raise vmodl.MethodFault(msg=\
                "VMwareTools is either not running or not installed. "
                "Rerun the script after verifying that VMwareTools "
                "is running")
            
    @watch
    def guest_tools_is_running(self, server):
        """
        :return: True if guest tools are running
        """
        # get guest tools status
        tools_status = server.guest.toolsRunningStatus
        if (tools_status == u'guestToolsNotRunning' or \
            tools_status == u'guestToolsExecutingScripts'):
            return False
        elif (tools_status == u'guestToolsRunning'):
            return True
    
    @watch
    def guest_execute_command(self, server, user, pwd, 
                              path_to_program=u'/bin/cat',
                              program_arguments=u'/etc/network/interfaces'):
        """"""
        self.check_guest_tools(server)
        try:
            content = self.manager.si.RetrieveContent()
            
            creds = vim.vm.guest.NamePasswordAuthentication(
                username=user, password=pwd
            )
    
            pm = content.guestOperationsManager.processManager

            ps = vim.vm.guest.ProcessManager.ProgramSpec(
                programPath=path_to_program,
                arguments=program_arguments
            )
            res = pm.StartProgramInGuest(server, creds, ps)
            self.logger.debug("Program executed, PID is %d" % res)
            return res
        except IOError as error:
            self.logger.error(error)
            raise VsphereError(error)                
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    @watch
    def guest_list_process(self, server, user, pwd, pids=None):
        """
        
        :param pids: list of process id. [optional]
        """
        self.check_guest_tools(server)
        try:
            content = self.manager.si.RetrieveContent()
            
            creds = vim.vm.guest.NamePasswordAuthentication(
                username=user, password=pwd
            )
    
            pm = content.guestOperationsManager.processManager
            procs = pm.ListProcessesInGuest(server, creds, pids=pids)
            self.logger.debug("List of server %s processes: %s" % (server, procs))
            return procs
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    @watch
    def guest_read_environment_variable(self, server, user, pwd):
        """
        
        :param pids: list of process id. [optional]
        """
        self.check_guest_tools(server)
        try:
            content = self.manager.si.RetrieveContent()
            
            creds = vim.vm.guest.NamePasswordAuthentication(
                username=user, password=pwd
            )
    
            pm = content.guestOperationsManager.processManager
            env = pm.ReadEnvironmentVariableInGuest(server, creds)
            self.logger.debug("List of server %s environment variables: %s" % 
                              (server, env))
            return env
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)

    @watch
    def guest_setup_network2(self, server, user, pwd, ip, nm, gw, hostname, 
                            device=u'eth0'):
        """
        :param ip: ip address
        :param nm: ip netmask
        :param gw: default gateway
        :param device: network devide [default=eth0]
        :param hostname: host name
        """
        # set hostname
        proc = self.guest_execute_command(server, user, pwd, 
                                          path_to_program=u'/bin/hostname', 
                                          program_arguments=hostname)
        params = u'-e "%s" > /etc/hostname' % (hostname)
        proc = self.guest_execute_command(server, user, pwd, 
                                          path_to_program=u'/bin/echo', 
                                          program_arguments=params)
        # set ip
        params = u'-e "TYPE=Ethernet\nBOOTPROTO=static\nIPV6INIT=no\nDEVICE='\
                 u'%s\nONBOOT=yes\nIPADDR=%s\nNETMASK=%s\nGATEWAY=%s" > '\
                 u'/etc/sysconfig/network-scripts/ifcfg-eth0' % (device, ip, nm, gw)
        proc = self.guest_execute_command(server, user, pwd, 
                                          path_to_program=u'/bin/echo', 
                                          program_arguments=params)
        #res = self.guest_list_process(server, user, pwd,
        #                              pids=[int(proc)])
        proc = self.guest_execute_command(server, user, pwd,
                                          path_to_program=u'/bin/systemctl', 
                                          program_arguments=u'restart network')
        #res = self.guest_list_process(server, 'root', 'Admin$01', 
        #                              pids=[int(proc)])
        
        self.logger.debug(u'Configure network for server %s: %s/%s' % 
                          (server, ip, nm))
        
    @watch
    def guest_setup_network(self, server, pwd, ipaddr, macaddr, gw, hostname, 
                            dns, dns_search, conn_name=u'net01', user=u'root'):
        """
        :param server: server mor object
        :param user: admin user
        :param pwd: admin password        
        :param ipaddr: ip address
        :param macaddr: mac address
        :param gw: default gateway
        :param device: network devide [default=eth0]
        :param hostname: host name
        :param conn_name: connection name
        :param dns: dns list. Ex. '8.8.8.8 8.8.8.4'
        :param dns_search: dns search domain. Ex. local.domain
        """
        # set hostname
        proc = self.guest_execute_command(server, user, pwd, 
                                          path_to_program=u'/bin/hostname', 
                                          program_arguments=hostname)
        params = u'-e "%s" > /etc/hostname' % (hostname)
        proc = self.guest_execute_command(server, user, pwd, 
                                          path_to_program=u'/bin/echo', 
                                          program_arguments=params)
        params = u'-e "%s %s" >> /etc/hosts' % (ipaddr, hostname)
        proc = self.guest_execute_command(server, user, pwd, 
                                          path_to_program=u'/bin/echo', 
                                          program_arguments=params)        
        
        # delete connection with the same name
        params = u'con delete %s' % conn_name
        proc = self.guest_execute_command(
                    server, user, pwd, path_to_program=u'/bin/nmcli',
                    program_arguments=params)        
        
        # create new connection
        params = u'con add type ethernet con-name %s ifname "*" mac %s ip4 %s/24 '\
                 u'gw4 %s' % (conn_name, macaddr, ipaddr, gw)
        proc = self.guest_execute_command(
                    server, user, pwd, path_to_program=u'/bin/nmcli',
                    program_arguments=params)
        
        # setup dns
        params = u'con modify %s ipv4.dns "%s" ipv4.dns-search %s' % \
                 (conn_name, dns, dns_search)
        proc = self.guest_execute_command(
                    server, user, pwd, path_to_program=u'/bin/nmcli',
                    program_arguments=params)        
        
        # restart network
        proc = self.guest_execute_command(server, user, pwd,
                                          path_to_program=u'/bin/systemctl', 
                                          program_arguments=u'restart network')
        
        self.logger.debug(u'Configure server %s device %s ip %s' % 
                          (server, macaddr, ipaddr))        

    @watch
    def guest_setup_admin_password(self, server, user, pwd, new_pwd):
        """
        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param new_pwd: new admin password
        """
        params = u'-e "%s" | passwd root --stdin > /dev/null' % (new_pwd)
        proc = self.guest_execute_command(server, user, pwd, 
                                          path_to_program=u'/bin/echo', 
                                          program_arguments=params)
        self.logger.debug(u'Setup server %s admin password' % (server))
        return proc
        
    @watch
    def guest_setup_ssh_key(self, server, user, pwd, key):
        """
        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param key: ssh public key
        """
        params = u'-e %s >> /root/.ssh/authorized_keys' % (key)
        proc = self.guest_execute_command(server, user, pwd, 
                                          path_to_program=u'/bin/echo',
                                          program_arguments=params)
        self.logger.debug(u'Setup server %s ssh key' % (server))  
        return proc      

    @watch
    def guest_copy_file(self, server, user, pwd, server_path, args):
        """TODO
        
        :param server: server mor object
        :param user: admin user
        :param pwd: admin password
        :param server_path: path inside server
        """
        self.check_guest_tools(server)
        try:
            content = self.manager.si.RetrieveContent()
            file_attribute = vim.vm.guest.FileManager.FileAttributes()
            creds = vim.vm.guest.NamePasswordAuthentication(
                username=user, password=pwd
            )     
            url = content.guestOperationsManager.fileManager. \
                InitiateFileTransferToGuest(server, creds, server_path,
                                            file_attribute,
                                            len(args), True)
            import requests
            resp = requests.put(url, data=args, verify=False)
            if not resp.status_code == 200:
                print "Error while uploading file"
            else:
                print "Successfully uploaded file"
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)            

    #
    # fault tolerance
    @watch
    def fault_tolerance(self):
        """"""
        pass

    #
    # system logs
    @watch
    def export_system_logs(self):
        """"""
        pass

    #
    # clone
    @watch
    def clone(self):
        """"""
        pass

    @watch
    def clone_to_template(self):
        """"""
        pass
    
    @watch
    def clone_to_template_library(self):
        """"""
        pass
    
    #
    # convert
    @watch
    def convert_to_template(self):
        """"""
        pass
    
    @watch
    def convert_from_template(self):
        """"""
        pass      
    
    #
    # ovf
    @watch
    def export_ovf_template(self):
        """"""
        pass    
    
    @watch
    def deploy_ovf_template(self):
        """"""
        pass     
    
    #
    # manage
    #
    @watch
    def start(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.PowerOnVM_Task()
            self.logger.debug("Attempting to power on %s" % (server))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)        
    
    @watch
    def stop(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.PowerOffVM_Task()
            self.logger.debug("Attempting to power off %s" % (server))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)    

    @watch
    def reboot(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            server.RebootGuest()
            self.logger.debug("Attempting to reboot %s" % (server))
            return None
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)        
    
    @watch
    def suspend(self, server):
        """
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            self.logger.debug("Attempting to suspend %s" % (server))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)        
    
    @watch
    def reset(self, server):
        """TODO
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)        

    @watch
    def stop_guest_os(self, server):
        """TODO
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)  

    @watch
    def restart_guest_os(self, server):
        """TODO
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)  
    
    @watch
    def migrate(self, server):
        """TODO
        :param server: server instance. Get with get_by_****
        """
        try:
            task = server.SuspendVM_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg)
            raise VsphereError(error.msg)       

class VsphereServerHardware(VsphereObject):
    """
    """
    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server
    
    def get_config_data(self, config):
        """ """
        try:
            cfg = config
            hw = v
            
            info = {u'bios_uuid': cfg.uuid,
                    u'version':cfg.version,
                    u'firmware':cfg.firmware,
                    u'swap_placement':cfg.swapPlacement,
                    u'boot':{
                        u'boot_delay':cfg.bootOptions.bootDelay,
                        u'enter_bios_setup':cfg.bootOptions.enterBIOSSetup,
                        u'retry_enabled':cfg.bootOptions.bootRetryEnabled,
                        u'retry_delay':cfg.bootOptions.bootRetryDelay,
                        u'network_protocol':cfg.bootOptions.networkBootProtocol,
                        u'order':[]}}
            for item in cfg.bootOptions.bootOrder:
                info[u'boot'][u'order'].append(item)
        
            # server files on storage
            info[u'file_layout'] = {
                u'vmPathName':cfg.files.vmPathName,
                u'snapshotDirectory':cfg.files.snapshotDirectory,
                u'suspendDirectory':cfg.files.suspendDirectory,
                u'logDirectory':cfg.files.logDirectory,
                u'files':[]}
        
            # server cpu
            reservation = u"%s MHz" % (cfg.cpuAllocation.reservation)
            shares = u"%s (%s)" % (cfg.cpuAllocation.shares.shares,
                                   cfg.cpuAllocation.shares.level)
            limit = cfg.cpuAllocation.limit
            if limit < 0:
                limit = u'unlimited'
            info[u'cpu'] = {u'num':hw.numCPU,
                            u'core':hw.numCoresPerSocket,
                            u'reservation':reservation,
                            u'limit':limit,
                            u'shares':shares,
                            u'hardware_utilization':None,
                            u'performance_counters':None
                           }
            
            # server memory
            reservation = u"%s MB" % (cfg.memoryAllocation.reservation)
            shares = u"%s (%s)" % (cfg.memoryAllocation.shares.shares,
                                   cfg.memoryAllocation.shares.level)
            limit = cfg.memoryAllocation.limit
            if limit < 0:
                limit = u'unlimited'            
            info[u'memory'] = {u'total': hw.memoryMB,
                               u'reservation':reservation,
                               u'limit':limit,
                               u'shares':shares,
                               u'vm_overhead_consumed':None}
            
            # server network adapter
            info[u'network'] = []
            
            # sever hard disk
            info[u'storage'] = []
            
            # server floppy
            info[u'floppy'] = None
            
            # sever cdrom
            info[u'cdrom'] = None
            
            # sever video card
            info[u'video'] = None
            
            # sever other
            info[u'other'] = {u'scsi_adapters':[], 
                              u'controllers':[],
                              u'input_devices':[],
                              u'pci':[],
                              u'other':[]}

            for device in hw.device:
                if device.backing is None:
                    if type(device).__name__.find('Controller') > -1:
                        dev = {u'name':device.deviceInfo.label,
                               u'type':type(device).__name__,
                               u'key':device.key}

                        info[u'other'][u'controllers'].append(dev)
                        
                    elif isinstance(device, vim.vm.device.VirtualKeyboard):
                        dev = {u'name':device.deviceInfo.label,
                               u'type':type(device).__name__,
                               u'key':device.key}

                        info[u'other'][u'input_devices'].append(dev)
                        # TODO
                            
                    elif isinstance(device, vim.vm.device.VirtualVideoCard):
                        dev = {u'name':device.deviceInfo.label,
                               u'type':type(device).__name__,
                               u'key':device.key}

                        info[u'video'] = dev
                        # TODO
                        
                    elif isinstance(device, vim.vm.device.VirtualVMCIDevice):
                        dev = {u'name':device.deviceInfo.label,
                               u'type':type(device).__name__,
                               u'key':device.key}

                        info[u'other'][u'pci'].append(dev)
                    
                    elif isinstance(device, vim.vm.device.VirtualSoundCard):
                        # TODO
                        pass
                                
                elif isinstance(device, vim.vm.device.VirtualPointingDevice):
                    dev = {u'name':device.deviceInfo.label,
                           u'type':type(device).__name__,
                           u'backing':type(device.backing).__name__,
                           u'key':device.key}

                    info[u'other'][u'input_devices'].append(dev) 
    
                elif isinstance(device, vim.vm.device.VirtualCdrom):                    
                    dev = {u'name':device.deviceInfo.label,
                           u'type':type(device).__name__,
                           u'backing':type(device.backing).__name__,
                           u'key':device.key}
                    if isinstance(device.backing, vim.vm.device.VirtualCdrom.IsoBackingInfo):
                        datastore = device.backing.datastore
                        if datastore is not None:
                            dev[u'dstastore'] = datastore._moId
                            dev[u'path'] = device.backing.fileName

                    info[u'cdrom'] = dev
                    # TODO
                
                elif isinstance(device, vim.vm.device.VirtualFloppy):
                    dev = {u'name':device.deviceInfo.label,
                           u'type':type(device).__name__,
                           u'key':device.key}

                    info[u'floppy'] = dev
                    # TODO
    
                elif isinstance(device, vim.vm.device.VirtualEthernetCard):
                    net = {u'key':device.key,
                           u'unit_number':device.unitNumber,
                           u'name':device.deviceInfo.label,
                           u'type':type(device).__name__,
                           u'backing':type(device.backing).__name__,
                           u'macaddress':device.macAddress,
                           u'direct_path_io':None,
                           u'network':None,
                           u'shares':None,
                           u'reservation':None,
                           u'limit':None,
                           u'connected':device.connectable.connected}

                    if hasattr(device.backing, u'port'):
                        port_group_ext_id = device.backing.port.portgroupKey
                        dvp = self.manager.network.get_network(port_group_ext_id)
                        cfg = dvp.config.defaultPortConfig
                        net[u'network'] = {u'id':port_group_ext_id,
                                           u'name':dvp.name,
                                           u'vlan':cfg.vlan.vlanId,
                                           u'dvs':dvp.config.distributedVirtualSwitch._moId,
                                          }
                    
                    info[u'network'].append(net)
                    
                #if hasattr(device.backing, 'fileName'):
                elif type(device) == vim.vm.device.VirtualDisk:
                    dev = {u'name':device.deviceInfo.label,
                           u'type':type(device).__name__,
                           u'backing':type(device.backing).__name__,
                           u'size':device.capacityInBytes/1024/1024,
                           u'flashcache':device.vFlashCacheConfigInfo,
                           u'datastore':None}
                    datastore = device.backing.datastore
                    if datastore is not None:
                        dev[u'datastore'] = {
                             u'file_name':device.backing.fileName,
                             u'name':datastore.name,
                             u'id':datastore._moId,
                             u'write_through':device.backing.writeThrough,
                             u'thin_provisioned':device.backing.thinProvisioned,
                             u'split':device.backing.split,
                             u'sharing':device.backing.sharing,
                             u'disk_mode':device.backing.diskMode,
                             u'digest_enabled':device.backing.digestEnabled,
                             u'delta_grain_size':device.backing.deltaGrainSize,
                             u'delta_disk_format_variant':device.backing.deltaDiskFormatVariant,
                             u'delta_disk_format':device.backing.deltaDiskFormat,
                             u'delta_grain_size':device.backing.deltaGrainSize,
                             u'parent':None}
                        if device.backing.parent is not None:
                            dev[u'datastore'][u'parent'] = {
                                 u'file_name':device.backing.parent.fileName,
                                 u'name':device.backing.parent.datastore.name,
                                 u'id':device.backing.parent.datastore._moId,
                                 u'write_through':device.backing.parent.writeThrough,
                                 u'thin_provisioned':device.backing.parent.thinProvisioned,
                                 u'split':device.backing.parent.split,
                                 u'sharing':device.backing.parent.sharing,
                                 u'disk_mode':device.backing.parent.diskMode,
                                 u'digest_enabled':device.backing.parent.digestEnabled,
                                 u'delta_grain_size':device.backing.parent.deltaGrainSize,
                                 u'delta_disk_format_variant':device.backing.parent.deltaDiskFormatVariant,
                                 u'delta_disk_format':device.backing.parent.deltaDiskFormat,
                                 u'delta_grain_size':device.backing.parent.deltaGrainSize}

                    info[u'storage'].append(dev)
                else:
                    dev = {u'name':device.deviceInfo.label,
                           u'type':type(device).__name__,
                           u'key':device.key}

                    info[u'other'][u'other'].append(dev)

        except:
            self.logger.warning(traceback.format_exc())
            info = {}
        
        return info        
    
    @watch
    def info(self, server):
        """Server hardware details: CPU, Ram, HD, Net, CD, Floppy, Video, 
        Compatibility (vm version), Other (SCSI Adapters, Controllers, Input
        devices)
        """
        info = self.get_config_data(server.config)
        
        # add file info
        for item in server.layoutEx.file:
            info[u'file_layout'][u'files'].append({
                u'key':item.key,
                u'name':item.name,
                u'type':item.type,
                u'size':item.size,
                u'uniqueSize':item.uniqueSize,
                u'accessible':item.accessible})
        
        return info 
    
    @watch
    def get_devices(self, server, dev_type=None):
        """
        
        :param dev_type: device type. Ex. vim.vm.device.VirtualVmxnet3. If None
                         get all device types.
        """
        devices = []
        try:
            for device in server.config.hardware.device:
                dtype = type(device).__name__
                if dev_type is not None and dtype != dev_type:
                    continue

                # diving into each device, we pull out a few interesting bits
                dev_details = {u'key': device.key,
                               u'unitNumber': device.unitNumber,
                               u'summary': device.deviceInfo.summary,
                               u'label':device.deviceInfo.label,
                               u'device type': dtype,
                               u'backing': {u'type':type(device.backing).__name__}}

                devices.append(dev_details)
        except:
            self.logger.warning(traceback.format_exc())
        
        return devices
    
    @watch
    def get_original_devices(self, server, dev_type=None):
        """
        
        :param dev_type: device type. Ex. vim.vm.device.VirtualVmxnet3. If None
                         get all device types.
        """
        devices = []
        try:
            for device in server.config.hardware.device:
                dtype = type(device).__name__
                if dev_type is not None and dtype != dev_type:
                    continue
                devices.append(device)
        except:
            self.logger.warning(traceback.format_exc())
        
        return devices
    
    #
    # add action
    #
    @watch
    def add_hard_disk(self, server, disk_size, disk_type='thin', existing=False):
        """
        Supported virtual disk backings:
        - Sparse disk format, version 1 and 2 : The virtual disk backing grows 
          when needed. Supported only for VMware Server.
        - Flat disk format, version 1 and 2 : The virtual disk backing is 
          preallocated. Version 1 is supported only for VMware Server.
        - Space efficient sparse disk format : The virtual disk backing grows 
          on demand and incorporates additional space optimizations.
        - Raw disk format, version 2  : The virtual disk backing uses a full 
          physical disk drive to back the virtual disk. Supported only for 
          VMware Server.
        - Partitioned raw disk format, version 2 : The virtual disk backing uses 
          one or more partitions on a physical disk drive to back a virtual 
          disk. Supported only for VMware Server.
        - Raw disk mapping, version 1 : The virtual disk backing uses a raw 
          device mapping to back the virtual disk. Supported for ESX Server 
          2.5 and 3.x.        
        
        TODO: extend backing support. Now support only FlatVer2BackingInfo
        
        :param server: server instance
        :param disk_size: disk size in MB
        :param disk_type: disk type [default=thin]
        :param existing: if True add existing hard disk
        """
        try:
            spec = vim.vm.ConfigSpec()
            # get all disks on a VM, set unit_number to the next available
            for dev in server.config.hardware.device:
                if hasattr(dev.backing, 'fileName'):
                    unit_number = int(dev.unitNumber) + 1
                    # unit_number 7 reserved for scsi controller
                    if unit_number == 7:
                        unit_number += 1
                    if unit_number >= 16:
                        raise vmodl.MethodFault(msg="we don't support this many disks")

                if isinstance(dev, vim.vm.device.VirtualSCSIController):
                    controller = dev
                    
            # add disk here
            dev_changes = []
            new_disk_kb = int(disk_size) * 1024 * 1024
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.fileOperation = "create"
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            disk_spec.device = vim.vm.device.VirtualDisk()
            disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            if disk_type == 'thin':
                disk_spec.device.backing.thinProvisioned = True
            disk_spec.device.backing.diskMode = 'persistent'
            disk_spec.device.unitNumber = unit_number
            disk_spec.device.capacityInKB = new_disk_kb
            disk_spec.device.controllerKey = controller.key
            dev_changes.append(disk_spec)
            spec.deviceChange = dev_changes
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("%sGB disk added to %s" % (disk_size, server.config.name))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return task
    
    @watch
    def add_network(self, server, network):
        """
        """
        try:
            spec = vim.vm.ConfigSpec()
            dev_changes = []
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()
            nic_spec.device.addressType = 'Generated'
            nic_spec.device.backing = \
                vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nic_spec.device.backing.port = vim.dvs.PortConnection()    
            nic_spec.device.backing.port.portgroupKey = network.key
            nic_spec.device.backing.port.switchUuid = \
                network.config.distributedVirtualSwitch.uuid     
            nic_spec.device.wakeOnLanEnabled = False
            dev_changes.append(nic_spec)
            spec.deviceChange = dev_changes
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Network %s added to %s" % 
                              (network.name, server.config.name))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return task

    @watch
    def add_cdrom(self, server):
        """
        """
        try:
            task = None
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return task
    
    @watch
    def add_floppy(self):
        """
        """
        pass    

    @watch
    def add_serial_port(self):
        """
        """
        pass

    @watch
    def add_parallel_port(self):
        """
        """
        pass

    @watch
    def add_usb_device(self):
        """
        """
        pass

    @watch
    def add_usb_controller(self):
        """
        """
        pass

    @watch
    def add_scsi_device(self):
        """
        """
        pass

    @watch
    def add_pci_device(self):
        """
        """
        pass

    @watch
    def add_shared_pci_device(self):
        """
        """
        pass

    @watch
    def add_scsi_controller(self):
        """
        """
        pass

    @watch
    def add_sata_controller(self):
        """
        """
        pass

    #
    # update action
    #
    @watch
    def update_hard_disk(self, existing=False):
        """
        :param existing: if True update existing hard disk
        """
        pass
    
    @watch
    def update_network(self, server, net_number, connect=True, network=None):
        """
        """
        try:
            spec = vim.vm.ConfigSpec()
            dev_changes = []
            
            net_prefix_label = 'Network adapter '
            net_label = net_prefix_label + str(net_number)
            virtual_net_device = None
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualEthernetCard) \
                        and dev.deviceInfo.label == net_label:
                    virtual_net_device = dev
            if not virtual_net_device:
                raise vmodl.MethodFault(msg='%s could not be found.' % 
                                        (net_label))
            
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            nic_spec.device = virtual_net_device
            nic_spec.device.wakeOnLanEnabled = False
            
            if network is not None:
                nic_spec.device.backing = \
                    vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                nic_spec.device.backing.port = vim.dvs.PortConnection()
                nic_spec.device.backing.port.portgroupKey = network.key
                nic_spec.device.backing.port.switchUuid = \
                    network.config.distributedVirtualSwitch.uuid     

            nic_spec.device.connectable = \
                vim.vm.device.VirtualDevice.ConnectInfo()
            nic_spec.device.connectable.startConnected = connect
            nic_spec.device.connectable.allowGuestControl = True

            dev_changes.append(nic_spec)
            spec.deviceChange = dev_changes
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Nic %s updated for server %s" % 
                              (net_label, server.name))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return task

    @watch
    def update_cdrom(self, server, cdrom_number, full_path_to_iso=None):
        """Updates Virtual Machine CD/DVD backend device
        
        :param server: server instance
        :param cdrom_number: CD/DVD drive unit number
        :param full_path_to_iso: Full path to iso. i.e. "[ds1] folder/Ubuntu.iso"
        :return: True or false in case of success or error
        """
        try:
            cdrom_prefix_label = 'CD/DVD drive '
            cdrom_label = cdrom_prefix_label + str(cdrom_number)
            virtual_cdrom_device = None
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualCdrom) \
                        and dev.deviceInfo.label == cdrom_label:
                    virtual_cdrom_device = dev
        
            if not virtual_cdrom_device:
                raise vmodl.MethodFault(msg='Virtual {} could not '
                                   'be found.'.format(cdrom_label))
        
            virtual_cd_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_cd_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            virtual_cd_spec.device = vim.vm.device.VirtualCdrom()
            virtual_cd_spec.device.controllerKey = virtual_cdrom_device.controllerKey
            virtual_cd_spec.device.key = virtual_cdrom_device.key
            virtual_cd_spec.device.connectable = \
                vim.vm.device.VirtualDevice.ConnectInfo()
            # if full_path_to_iso is provided it will mount the iso
            if full_path_to_iso:
                virtual_cd_spec.device.backing = \
                    vim.vm.device.VirtualCdrom.IsoBackingInfo()
                virtual_cd_spec.device.backing.fileName = full_path_to_iso
                virtual_cd_spec.device.connectable.connected = True
                virtual_cd_spec.device.connectable.startConnected = True
            else:
                virtual_cd_spec.device.backing = \
                    vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo()
            # Allowing guest control
            virtual_cd_spec.device.connectable.allowGuestControl = True
        
            dev_changes = []
            dev_changes.append(virtual_cd_spec)
            spec = vim.vm.ConfigSpec()
            spec.deviceChange = dev_changes
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug("Cdorm %s updated for server %s" % 
                              (cdrom_label, server.name))            
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return task
    
    @watch
    def update_floppy(self):
        """
        """
        pass    

    @watch
    def update_serial_port(self):
        """
        """
        pass

    @watch
    def update_parallel_port(self):
        """
        """
        pass

    @watch
    def update_usb_device(self):
        """
        """
        pass

    @watch
    def update_usb_controller(self):
        """
        """
        pass

    @watch
    def update_scsi_device(self):
        """
        """
        pass

    @watch
    def update_pci_device(self):
        """
        """
        pass

    @watch
    def update_shared_pci_device(self):
        """
        """
        pass

    @watch
    def update_scsi_controller(self):
        """
        """
        pass

    @watch
    def update_sata_controller(self):
        """
        """
        pass

    #
    # delete action
    #
    @watch
    def delete_hard_disk(self, server, disk_number):
        """
        :param server: server insatnce
        :param disk_number: Hard Disk Unit Number
        :return: task
        """
        try:
            hdd_prefix_label = 'Hard disk '
            hdd_label = hdd_prefix_label + str(disk_number)
            virtual_hdd_device = None
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualDisk) \
                        and dev.deviceInfo.label == hdd_label:
                    virtual_hdd_device = dev
            if not virtual_hdd_device:
                raise vmodl.MethodFault(msg='Virtual %s could not be found.' % 
                                        (hdd_label))
        
            virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_hdd_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.Operation.remove
            virtual_hdd_spec.device = virtual_hdd_device
        
            spec = vim.vm.ConfigSpec()
            spec.deviceChange = [virtual_hdd_spec]
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug('Remove disk %s from sever %s' % 
                              (hdd_label, server.name))
            return task  
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return task

    @watch
    def delete_network(self, server, net_number):
        """
        """
        try:
            net_prefix_label = 'Network adapter '
            net_label = net_prefix_label + str(net_number)
            virtual_net_device = None
            for dev in server.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualEthernetCard) \
                        and dev.deviceInfo.label == net_label:
                    virtual_net_device = dev
            if not virtual_net_device:
                raise vmodl.MethodFault(msg='%s could not be found.' % 
                                        (net_label))         
            
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.Operation.remove
            nic_spec.device = virtual_net_device
            
            spec = vim.vm.ConfigSpec()
            spec.deviceChange = [nic_spec]
            task = server.ReconfigVM_Task(spec=spec)
            self.logger.debug('Remove network %s from sever %s' % 
                              (net_label, server.name))
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return task

    @watch
    def delete_cdrom(self):
        """
        """
        pass
    
    @watch
    def delete_floppy(self):
        """
        """
        pass    

    @watch
    def delete_serial_port(self):
        """
        """
        pass

    @watch
    def delete_parallel_port(self):
        """
        """
        pass

    @watch
    def delete_usb_device(self):
        """
        """
        pass

    @watch
    def delete_usb_controller(self):
        """
        """
        pass

    @watch
    def delete_scsi_device(self):
        """
        """
        pass

    @watch
    def delete_pci_device(self):
        """
        """
        pass

    @watch
    def delete_shared_pci_device(self):
        """
        """
        pass

    @watch
    def delete_scsi_controller(self):
        """
        """
        pass

    @watch
    def delete_sata_controller(self):
        """
        """
        pass

class VsphereServerMonitor(VsphereObject):
    """
    """
    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server
    
    @watch
    def issues(self):
        """"""
        pass
    
    @watch
    def performances(self):
        """"""
        pass

    @watch
    def policies(self):
        """"""
        pass

    @watch
    def tasks(self):
        """"""
        pass

    @watch
    def events(self):
        """"""
        pass
    
    @watch
    def utilization(self):
        """"""
        pass
    
    @watch
    def activity(self):
        """"""
        pass    
    
    @watch
    def service_composer(self):
        """"""
        pass    
    
    @watch
    def data_security(self):
        """"""
        pass
    
    @watch
    def flow(self):
        """"""
        pass    

class VsphereServerSnapshot(VsphereObject):
    """
    """
    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server    
    
    @watch
    def list(self, server):
        """List server snapshots.
        
        :param server: server instance
        :return: list of dictionary with snapshot info
        """
        try:
            snapshots = []
            if server.snapshot is not None:
                for item in server.snapshot.rootSnapshotList:
                    snapshot = {
                        u'id':item.snapshot._moId,
                        u'name':item.name,
                        u'desc':item.description,
                        u'creation_date':item.createTime,
                        u'state':item.state,
                        u'quiesced':item.quiesced,
                        u'backup_manifest':item.backupManifest,
                        u'replaysupported':item.replaySupported,
                        u'childs':[]
                    }
                    for child in item.childSnapshotList:
                        snapshot[u'childs'].append(child._moId)
                snapshots.append(snapshot)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return snapshots
    
    def _get(self, server, snapshot_id):
        """Get server snapshot by managed object reference id.
        
        :param server: server instance
        :param snapshot_id: snapshot id
        :return: snapshot instance
                :raise vmodl.MethodFault: 
        """
        # get snapshot
        if server.snapshot is None:
            self.logger.error('Snapshot %s does not exist' % snapshot_id, 
                              exc_info=True)
            raise vmodl.MethodFault(msg='Snapshot %s does not exist' % snapshot_id)      
            
        for item in server.snapshot.rootSnapshotList:
            if item.snapshot._moId == snapshot_id:
                self.logger.debug('Snapshot %s' % item.snapshot)
                return item
        
        self.logger.error('Snapshot %s does not exist' % snapshot_id, 
                          exc_info=True)
        raise vmodl.MethodFault(msg='Snapshot %s does not exist' % snapshot_id)
    
    @watch
    def get(self, server, snapshot_id):
        """Get server snapshot by managed object reference id.
        
        :param server: server instance
        :param snapshot_id: snapshot id
        :return: dict with snaphsot info
        :raise VsphereError: 
        """
        try:
            item = self._get(server, snapshot_id)
            snapshot = {
                u'id':item.snapshot._moId,
                u'name':item.name,
                u'desc':item.description,
                u'creation_date':item.createTime,
                u'state':item.state,
                u'quiesced':item.quiesced,
                u'backup_manifest':item.backupManifest,
                u'replaysupported':item.replaySupported,
                u'childs':[]
            }
            for child in item.childSnapshotList:
                snapshot[u'childs'].append(child._moId)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return snapshot

    @watch
    def get_current(self, server):
        """Get current server snapshot.
        
        :param server: server instance
        :return: dictionary with snapshot info
        :raise VsphereError:        
        """
        try:
            item = server.rootSnapshot[0]
            hw = VsphereServerHardware(self.server)
            
            snapshot = {
                u'id':item._moId,
                u'config':hw.get_config_data(item.config),
                u'childs':[]
            }
            for child in item.childSnapshot:
                snapshot[u'childs'].append(child._moId)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
        return snapshot

    @watch
    def take(self, server, name, desc, memory=True, quiesce=False):
        """Creates a new snapshot of this virtual machine. As a side effect, 
        this updates the current snapshot.
        Snapshots are not supported for Fault Tolerance primary and secondary 
        virtual machines.

        Any % (percent) character used in this name parameter must be escaped, 
        unless it is used to start an escape sequence. Clients may also escape 
        any other characters in this name parameter.
        
        :param name: The name for this snapshot. The name need not be unique 
                     for this virtual machine. 
        :param description: A description for this snapshot. If omitted, a 
                            default description may be provided. 
        :param memory: If TRUE, a dump of the internal state of the virtual 
                       machine (basically a memory dump) is included in the 
                       snapshot. Memory snapshots consume time and resources, 
                       and thus take longer to create. When set to FALSE, the 
                       power state of the snapshot is set to powered off.
                       capabilities indicates whether or not this virtual 
                       machine supports this operation. 
        :param quiesce: If TRUE and the virtual machine is powered on when the 
                        snapshot is taken, VMware Tools is used to quiesce the 
                        file system in the virtual machine. This assures that a 
                        disk snapshot represents a consistent state of the guest 
                        file systems. If the virtual machine is powered off or 
                        VMware Tools are not available, the quiesce flag is ignored.
        :return: task
        :raise VsphereError:
        """
        try:
            task = server.CreateSnapshot_Task(name=name,
                                              description=desc,
                                              memory=memory,
                                              quiesce=quiesce)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)  
  
    @watch
    def rename(self, server, snapshot_id, name, description=None):
        """Rename server snapshot snapshot_id.
        
        :param server: server instance
        :param snapshot_id: snapshot id
        :return: True
        :raise VsphereError:
        """
        try:
            snapshot = self._get(server, snapshot_id)
            snapshot.RenameSnapshot(name=name, description=description)
            return True
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
  
    @watch
    def revert(self, server, snapshot_id, suppress_power_on=False):
        """Revert to server snapshot snapshot_id.
        
        :param server: server instance
        :param snapshot_id: snapshot id
        :param suppress_power_on: (optional) If set to true, the virtual machine 
                                  will not be powered on regardless of the power 
                                  state when the snapshot was created. 
                                  Default to false.
        :return: task
        :raise VsphereError:
        """
        try:
            snapshot = self._get(server, snapshot_id)
            task = snapshot.RevertToSnapshot_Task(suppressPowerOn=suppress_power_on)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)

    @watch
    def remove(self, server, snapshot_id):
        """Remove server snapshot snapshot_id.
        
        :param server: server instance
        :param snapshot_id: snapshot id
        :return: task
        :raise VsphereError:
        """
        try:
            snapshot = self._get(server, snapshot_id)
            task = snapshot.snapshot.RemoveSnapshot_Task(removeChildren=True,
                                                         consolidate=True)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)

class VsphereNetwork(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
        
        self._nsx = VsphereNetworkNsx(manager)
        
    @property
    def nsx(self):
        if self.manager.nsx is None:
            raise VsphereError('Nsx is not configured')
        else:
            return self._nsx
    
    #
    # DistributedVirtualSwitch
    #
    @watch
    def list_distributed_virtual_switches(self):
        """Get distributed virtual switch with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']
            
        return: list of vim.dvs.VmwareDistributedVirtualSwitch
        """
        props = ['name', 'parent', 'overallStatus']
        view = self.manager.get_container_view(obj_type=[vim.dvs.VmwareDistributedVirtualSwitch])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.dvs.VmwareDistributedVirtualSwitch,
                                               path_set=props,
                                               include_mors=True)
        return data  

    @watch
    def get_distributed_virtual_switch(self, morid):
        """Get distributed virtual switch by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        #container = self.si.content.rootFolder
        container = None
        dvs = self.manager.get_object(morid, 
                                      [vim.dvs.VmwareDistributedVirtualSwitch], 
                                      container=container)
        return dvs

    #
    # network and DistributedVirtualPortgroup
    #
    @watch
    def list_networks(self):
        """Get networks with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']
            
        return: list of vim.Network, vim.dvs.DistributedVirtualPortgroup   
        """
        props = ['name', 'parent', 'overallStatus', 'summary.ipPoolId',
                 'summary.ipPoolName']
        view = self.manager.get_container_view(obj_type=[vim.Network])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.Network,
                                               path_set=props,
                                               include_mors=True)
        return data
    
    @watch
    def get_network(self, morid):
        """Get network by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.Network],
                                      container=container)
        return obj   

    @watch
    def create_distributed_port_group(self, name, desc, vlan, dvs, numports=24):
        """Creates a distributed virtual port group.
    
        :param name: String Name
        :param desc: String desc
        :param vlan: vlan id
        :param dvs: dvs object reference
        :param numports: number of ports in the portgroup [default=24]
        """
        try:
            vlan_config = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
            vlan_config.vlanId = vlan
            port_config = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
            port_config.vlan = vlan_config

            config = vim.dvs.DistributedVirtualPortgroup.ConfigSpec(
                        name=name, description=desc, autoExpand=True,
                        defaultPortConfig=port_config, type='earlyBinding',
                        numPorts=numports)
        
            task = dvs.CreateDVPortgroup_Task(spec=config)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)
        
    @watch
    def remove_network(self, network):
        """Remove a distributed virtual port group.
    
        :param morid: 
        """
        try:
            task = network.Destroy_Task()
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)

    #
    # summary
    #
    @watch
    def info_distributed_virtual_switch(self, obj):
        """
        :param obj: instance. Get with get_by_****
        """
        try:
            info = {
                u'id':str(obj.get(u'obj')).split(u':')[1].rstrip(u"'"),
                u'name':get_attrib(obj, u'name', u''),
                u'parent':str(get_attrib(obj, u'parent', u'')).split(u':')[1].rstrip(u"'"),
                u'overallStatus':get_attrib(obj, u'overallStatus', u'')
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}        
        return info    
    
    @watch
    def detail_distributed_virtual_switch(self, dvs):
        """ TODO: add host attrib
        """
        try:
            creation_date = str2uni(dvs.config.createTime.strftime("%d-%m-%y %H:%M:%S"))
            res = {u'uuid':dvs.uuid,
                   u'configVersion':dvs.config.configVersion,
                   u'date':{u'created':creation_date},
                   u'desc':dvs.config.description,
                   u'extensionKey':dvs.config.extensionKey,
                   u'maxPorts':dvs.config.maxPorts,
                   u'networkResourceManagementEnabled':dvs.config.networkResourceManagementEnabled,
                   u'numPorts':dvs.config.numPorts,
                   u'maxPorts':dvs.config.maxPorts,
                   u'numStandalonePorts':dvs.config.numStandalonePorts,
                   u'switchIpAddress':dvs.config.switchIpAddress,
                   #u'productInfo':dvs.config.productInfo,
                   u'targetInfo':dvs.config.targetInfo}
            res[u'uplinkPortgroup'] = [u._moId for u in dvs.config.uplinkPortgroup]
            #res[u'host'] = [u._moId for u in dvs.config.host]
        except Exception as error:
            self.logger.error(error, exc_info=True)
            res = {}
        
        return res
    
    @watch
    def info_network(self, obj):
        """
        :param obj: instance. Get with get_by_****
        """
        try:
            info = {
                u'id':str(obj.get(u'obj')).split(u':')[1].rstrip(u"'"),
                u'name':get_attrib(obj, u'name', u''),
                u'parent':str(get_attrib(obj, u'parent', u'')).split(u':')[1].rstrip(u"'"),
                u'overallStatus':get_attrib(obj, u'overallStatus', u'')
            }
        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}        
        return info      
    
    @watch
    def detail_network(self, dvp):
        """
        """
        try:
            cfg = dvp.config.defaultPortConfig
            res = {u'name':dvp.name,
                   u'desc':dvp.config.description,
                   u'portKeys':[p for p in dvp.portKeys],
                   u'autoExpand':dvp.config.autoExpand,
                   u'configVersion':dvp.config.configVersion,
                   u'description':dvp.config.description,
                   u'numPorts':dvp.config.numPorts,
                   u'type':dvp.config.type,
                   #u'policy':dvp.config.policy,
                   u'dvs':dvp.config.distributedVirtualSwitch._moId,
                   u'vlan':cfg.vlan.vlanId,
                   u'lacp':{u'enable':cfg.lacpPolicy.enable.value,
                            u'mode':cfg.lacpPolicy.mode.value},
                   u'config':{u'in':{u'ShapingPolicy':cfg.inShapingPolicy.enabled.value,
                                     u'averageBandwidth':cfg.inShapingPolicy.averageBandwidth.value,
                                     u'peakBandwidth':cfg.inShapingPolicy.averageBandwidth.value,
                                     u'burstSize':cfg.inShapingPolicy.averageBandwidth.value},
                             u'out':{u'ShapingPolicy':cfg.outShapingPolicy.enabled.value,
                                     u'averageBandwidth':cfg.outShapingPolicy.averageBandwidth.value,
                                     u'peakBandwidth':cfg.outShapingPolicy.averageBandwidth.value,
                                     u'burstSize':cfg.outShapingPolicy.averageBandwidth.value}}}
        except:
            self.logger.warning(traceback.format_exc())
            res = {}
        
        return res

    #
    # monitor
    #

    #
    # manage
    #
    
    #
    # related object
    #
    @watch
    def get_network_servers(self, morid):
        """
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.dvs.DistributedVirtualPortgroup], 
                                      container=container)
        
        vm_data = []
        for o in obj.vm:
            vm_data.append({'_moId':o._moId,
                            'config.guestId':o.config.guestId,
                            'config.guestFullName':o.config.guestFullName,
                            'config.hardware.memoryMB':o.config.hardware.memoryMB,
                            'config.hardware.numCPU':o.config.hardware.numCPU,
                            'config.version':o.config.version,
                            'runtime.powerState':o.runtime.powerState,
                            'config.template':o.config.template,
                            'guest.hostName':o.guest.hostName,
                            'guest.ipAddress':o.guest.ipAddress})            
        return vm_data

class VsphereNetworkNsx(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
        
        self.dfw = VsphereNetworkDfw(self.manager)
        self.lg = VsphereNetworkLogicalSwitch(self.manager)
        self.sg = VsphereNetworkSecurityGroup(self.manager)
        self.dlr = VsphereNetworkDlr(self.manager)
        self.edge = VsphereNetworkEdge(self.manager)
        self.ipset = VsphereNetworkIpSet(self.manager)
        self.service = VsphereNetworkService(self.manager)
        self.lb = VsphereNetworkLB(self.manager)

    #
    # logical_switches
    #    
    def list_transport_zones(self):
        """ """
        res = self.call('/api/2.0/vdn/scopes',  'GET', '')
        return res['vdnScopes']['vdnScope']

    
    #
    # logical_switches
    #
    def list_logical_switches(self):
        """ """
        res = self.call('/api/2.0/vdn/virtualwires',  'GET', '')
        return res['virtualWires']['dataPage']['virtualWire']
    
    def get_logical_switch(self, oid):
        """
        :param oid: logical switch id
        """
        res = self.call('/api/2.0/vdn/virtualwires/%s' % oid,  'GET', '')
        return res['virtualWire']
    
    def create_logical_switch(self, scope_id, name, desc, 
                              tenant="virtual wire tenant", 
                              guest_allowed='true'):
        """Create logical switch
        
        :param scope_id: transport zone id
        :param name: logical switch name
        :param desc: logical switch desc
        :param tenant: tenant id [default="virtual wire tenant"]
        :param guest_allowed: [default='true']
        """
        data = ['<virtualWireCreateSpec>',
                '<name>%s</name>' % name,
                '<description>%s</description>' % desc,
                '<tenantId>%s</tenantId>' % tenant,
                '<controlPlaneMode>UNICAST_MODE</controlPlaneMode>',
                '<guestVlanAllowed>%s</guestVlanAllowed>' % guest_allowed,
                '</virtualWireCreateSpec>']
        data = ''.join(data)
        res = self.call('/api/2.0/vdn/scopes/%s/virtualwires' % scope_id,  
                        'POST', data, headers={'Content-Type':'text/xml'},
                        timeout=600)
        return res
    
    def delete_logical_switch(self, oid):
        """
        :param oid: logical switch id
        """
        res = self.call('/api/2.0/vdn/virtualwires/%s' % oid,  'DELETE', '',
                        timeout=600)
        return res
    
    def info_logical_switch(self, sw):
        """Format logical switch main info"""
        res = {
            "objectId":sw['objectId'],
            "objectTypeName":sw['objectTypeName'], 
            "vsmUuid":sw['vsmUuid'], 
            "nodeId":sw['nodeId'], 
            "revision":sw['revision'],
            "description":sw['description'],
            "clientHandle":sw['clientHandle'],
            "extendedAttributes":sw['extendedAttributes'],
            "isUniversal":sw['isUniversal'],
            "universalRevision":sw['universalRevision'],
            "tenantId":sw['tenantId'],
            "vdnScopeId":sw['vdnScopeId'],
            "switch": [],
            "vdnId": sw['vdnId'],
            "guestVlanAllowed":sw['guestVlanAllowed'],
            "controlPlaneMode":sw['controlPlaneMode'],
            "ctrlLsUuid":sw['ctrlLsUuid'],
            "macLearningEnabled":sw['macLearningEnabled'],
        }
        
        for item in sw['vdsContextWithBacking']:
            switch = item["switch"]
            data = {"switch":{"objectId":switch["objectId"],
                              "name":switch["name"]},
                    "mtu":item["mtu"],
                    "promiscuousMode":item["promiscuousMode"],
                    "portgroup":{"objectId":item["backingValue"]}}
            res['switch'].append(data)
        
        return res
    
    def print_logicalswitch(self, data):
        """Format logical switch main info"""
        res = []
        row_tmpl = "%-40s%-20s%-20s%-7s%-10s"      
        row_tmpl2 = "%-90s%-20s%-6s%-25s%-30s"  
        legend = ('name',
                  'transport',
                  'tenant',
                  'vlanid',
                  'switch')
        res.append(row_tmpl % legend)
        for item in data:

            row = (item['name'],
                   item['controlPlaneMode'],
                   item['tenantId'],
                   item['vdnId'],
                   '')
                   
            '''
            ]'''
            res.append(row_tmpl % row)
            for switch in item['vdsContextWithBacking']:
                try: backingvalue = switch['backingValue']
                except: backingvalue = None
                try: mtu = switch['mtu']
                except: mtu = None
                try: name = switch['switch']['name']
                except: name = None
                try: scope = switch['switch']['scope']['name']
                except: scope = None
                row = ('',
                       backingvalue,
                       mtu,
                       name,
                       scope)
                res.append(row_tmpl2 % row)
        return res

class VsphereNetworkLogicalSwitch(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
        
    def list(self):
        """ """
        res = self.call('/api/2.0/vdn/virtualwires',  'GET', '')
        return res['virtualWires']['dataPage']['virtualWire']
    
    def get(self, oid):
        """
        :param oid: logical switch id
        """
        res = self.call('/api/2.0/vdn/virtualwires/%s' % oid,  'GET', '')
        return res['virtualWire']
    
    def create(self, scope_id, name, desc, 
                              tenant="virtual wire tenant", 
                              guest_allowed='true'):
        """Create logical switch
        
        :param scope_id: transport zone id
        :param name: logical switch name
        :param desc: logical switch desc
        :param tenant: tenant id [default="virtual wire tenant"]
        :param guest_allowed: [default='true']
        """
        data = ['<virtualWireCreateSpec>',
                '<name>%s</name>' % name,
                '<description>%s</description>' % desc,
                '<tenantId>%s</tenantId>' % tenant,
                '<controlPlaneMode>UNICAST_MODE</controlPlaneMode>',
                '<guestVlanAllowed>%s</guestVlanAllowed>' % guest_allowed,
                '</virtualWireCreateSpec>']
        data = ''.join(data)
        res = self.call('/api/2.0/vdn/scopes/%s/virtualwires' % scope_id,  
                        'POST', data, headers={'Content-Type':'text/xml'},
                        timeout=600)
        return res
    
    def delete(self, oid):
        """
        :param oid: logical switch id
        """
        res = self.call('/api/2.0/vdn/virtualwires/%s' % oid,  'DELETE', '',
                        timeout=600)
        return res
    
    def info(self, sw):
        """Format logical switch main info"""
        res = {
            "objectId":sw['objectId'],
            "objectTypeName":sw['objectTypeName'], 
            "vsmUuid":sw['vsmUuid'], 
            "nodeId":sw['nodeId'], 
            "revision":sw['revision'],
            "description":sw['description'],
            "clientHandle":sw['clientHandle'],
            "extendedAttributes":sw['extendedAttributes'],
            "isUniversal":sw['isUniversal'],
            "universalRevision":sw['universalRevision'],
            "tenantId":sw['tenantId'],
            "vdnScopeId":sw['vdnScopeId'],
            "switch": [],
            "vdnId": sw['vdnId'],
            "guestVlanAllowed":sw['guestVlanAllowed'],
            "controlPlaneMode":sw['controlPlaneMode'],
            "ctrlLsUuid":sw['ctrlLsUuid'],
            "macLearningEnabled":sw['macLearningEnabled'],
        }
        
        data = sw['vdsContextWithBacking']
        if not isinstance(data, list):
            data = [data]
        
        for item in data:
            switch = item["switch"]
            data = {"switch":{"objectId":switch["objectId"],
                              "name":switch["name"]},
                    "mtu":item["mtu"],
                    "promiscuousMode":item["promiscuousMode"],
                    "portgroup":{"objectId":item["backingValue"]}}
            res['switch'].append(data)
        
        return res
    
    def detail(self, sw):
        """Format logical switch main info"""
        res = self.info(sw)
        
        return res    
    
    def info_print(self, data):
        """Format logical switch main info"""
        res = []
        row_tmpl = "%-40s%-20s%-20s%-7s%-10s"      
        row_tmpl2 = "%-90s%-20s%-6s%-25s%-30s"  
        legend = ('name',
                  'transport',
                  'tenant',
                  'vlanid',
                  'switch')
        res.append(row_tmpl % legend)
        for item in data:

            row = (item['name'],
                   item['controlPlaneMode'],
                   item['tenantId'],
                   item['vdnId'],
                   '')
                   
            '''
            ]'''
            res.append(row_tmpl % row)
            for switch in item['vdsContextWithBacking']:
                try: backingvalue = switch['backingValue']
                except: backingvalue = None
                try: mtu = switch['mtu']
                except: mtu = None
                try: name = switch['switch']['name']
                except: name = None
                try: scope = switch['switch']['scope']['name']
                except: scope = None
                row = ('',
                       backingvalue,
                       mtu,
                       name,
                       scope)
                res.append(row_tmpl2 % row)
        return res        
        
class VsphereNetworkSecurityGroup(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """ """
        res = self.call('/api/2.0/services/securitygroup/scope/globalroot-0',
                        'GET', '')['list']['securitygroup']
        if isinstance(res, dict):
            res = [res]        
        return res
    
    def list_by_server(self, vmid):
        """
        :param moid: server morid
        """
        res = self.call('/api/2.0/services/securitygroup/lookup/virtualmachine/%s' % vmid,
                        'GET', '')
        return res
    
    def get(self, oid):
        """
        :param oid: securitygroup id
        :return: None if security group does not exist
        """
        res = self.call('/api/2.0/services/securitygroup/%s' % oid,  'GET', '')
        return res['securitygroup']
    
    def info(self, sg):
        """
        """
        res = sg
        return sg
    
    def detail(self, sg):
        """
        """
        res = sg
        return sg    
    
    def create(self, name):
        """
        TODO
        <member>
        <objectId></objectId>
        <objectTypeName></objectTypeName>
        <vsmUuid></vsmUuid>
        <revision></revision>
        <type>
        <typeName></typeName>
        </type>
        <name></name>
        <scope>
        <id></id>
        <objectTypeName></objectTypeName>
        <name></name>
        </scope>
        <clientHandle></clientHandle>
        <extendedAttributes></extendedAttributes>
        </member>
        
        <excludeMember>
        <objectId></objectId>
        <objectTypeName></objectTypeName>
        <vsmUuid></vsmUuid>
        <revision></revision>
        <type>
        <typeName></typeName>
        </type>
        <name></name>
        <scope>
        <id></id>
        <objectTypeName></objectTypeName>
        <name></name>
        </scope>
        <clientHandle></clientHandle>
        <extendedAttributes></extendedAttributes>
        </excludeMember>
        
        <dynamicMemberDefinition>
        <dynamicSet>
        <operator></operator>
        <dynamicCriteria>
        <operator></operator>
        <key></key>
        <criteria></criteria>
        <value></value>
        </dynamicCriteria>
        <dynamicCriteria>
        </dynamicCriteria>
        </dynamicSet>
        </dynamicMemberDefinition>
        
        :param name: logical switch name
        :return: mor id
        """
        data = ['<securitygroup>',
                '<name>%s</name>' % name,
                '<scope>',
                '<id>globalroot-0</id>',
                '<objectTypeName>GlobalRoot</objectTypeName>',
                '<name>Global</name>',
                '</scope>',             
                '</securitygroup>']
        data = ''.join(data)
        res = self.call('/api/2.0/services/securitygroup/bulk/globalroot-0',
                        'POST', data, headers={'Content-Type':'text/xml'},
                        timeout=600)
        return res
    
    def update(self, oid):
        """
        
        TODO:
        
        :param oid: securitygroup id
        """
        data = self.call('/api/2.0/services/securitygroup/%s' % oid,  'GET', 
                         '', parse=False)
        # TODO modify data content to update cofiguration
        res = self.call('/api/2.0/services/securitygroup/%s' % oid,  'PUT', 
                        data, parse=False)
        
        return res    
    
    def delete(self, oid):
        """
        :param oid: securitygroup id
        """
        res = self.call('/api/2.0/services/securitygroup/%s' % oid,  'DELETE', 
                        '', timeout=600)
        return True
    
    def get_allowed_member_type(self, oid):
        """Retrieve a list of valid elements that can be added to a security group.
        
        :param oid: security group id
        """
        res = self.call('/api/2.0/services/securitygroup/scope/globalroot-0/memberTypes',
                        'GET', '')
        return res    
    
    def add_member(self, oid, moid):
        """
        :param oid: security group id
        :param moid: member morid
        """
        res = self.call('/api/2.0/services/securitygroup/%s/members/%s' % 
                        (oid, moid),  'PUT', '', timeout=600)
        return res
    
    def delete_member(self, oid, moid):
        """
        :param oid: security group id
        :param moid: member morid
        """
        res = self.call('/api/2.0/services/securitygroup/%s/members/%s' % 
                        (oid, moid),  'DELETE', '', timeout=600)
        return res    

class VsphereNetworkIpSet(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """ """
        res = self.call('/api/2.0/services/ipset/scope/globalroot-0',
                        'GET', '')['list']['ipset']
        if isinstance(res, dict):
            res = [res]             
        return res
    
    def get(self, oid):
        """
        :param oid: securitygroup id
        :return: None if security group does not exist
        """
        res = self.call('/api/2.0/services/ipset/%s' % oid,  'GET', '')
        return res['ipset']
    
    def info(self, sg):
        """
        """
        res = sg
        return sg
    
    def detail(self, sg):
        """
        """
        res = sg
        return sg    
    
    def create(self, name, desc, ipset):
        """
        
        :param name: ip set name
        :param desc: ip set description
        :param ipset: list of ip. Ex. 10.112.201.8-10.112.201.14
        :return: mor id
        """       
       
        data = ['<ipset>',
                '<objectId/>',
                '<type>',
                '<typeName/>',
                '</type>',
                '<description>%s</description>',
                '<name>%s</name>',
                '<revision>0</revision>',
                '<objectTypeName/>',
                '<value>%s</value>',
                '</ipset>']
        data = ''.join(data) % (desc, name, ipset)
        res = self.call('/api/2.0/services/ipset/globalroot-0',
                        'POST', data, headers={'Content-Type':'text/xml'},
                        timeout=600)
        return res
    
    def update(self, oid, name=None, description=None, value=None):
        """
        Modify/Edit ipset properties
        Modified by Miko ( TO DO by Sergio )
        
       
        
        :param oid: securitygroup id ( morefid )
        :param name: new name of the ipset to modify
        :param description: new description to modify
        :param value: new ipset to modify 
        """        
        
        data = self.call('/api/2.0/services/ipset/%s' % oid,  'GET', 
                         '', parse=False)
        # TODO modify data content to update configuration
        
        #self.logger.debug("MIKO_IP_SET :%s" %data)
        
        res = xmltodict(data, dict_constructor=dict)
        
        noName=False
        noDescription=False
        noValue=False
        
        if name == None :
            name=res['ipset']['name']
            noName=True
        elif name == res['ipset']['name']:
            noName=True
            #self.logger.debug("MIKO_IP_SET: sono in name ")
                
        if description == None:
            description= res['ipset']['description']
            noDescription=True
        elif description==res['ipset']['description']:
            noDescription=True
            #self.logger.debug("MIKO_IP_SET: sono in description ")

        if value==None:
            value=res['ipset']['value']
            noValue=True
        elif value==res['ipset']['value']:
            noValue=True
            #self.logger.debug("MIKO_IP_SET: sono in value ")
        
        '''        
        Request:
            PUT https://NSX-Manager-IP-Address/api/2.0/services/ipset/objectId

        Request Body:
            <ipset>
                <objectId>ipset-ae40752f-3b9b-4885-b63c-551fbaa459ab</objectId>
                <type>
                    <typeName>IPSet</typeName>
                </type>
                <description>Updated Description</description>
                <name>TestIPSet1updated</name>
                <revision>2</revision>
                <objectTypeName />
                <value>10.112.200.1,10.112.200.4-10.112.200.10</value>
            </ipset>
        '''        
        if (noName) and  (noDescription) and (noValue):
            # no update to do
            res=data
            self.logger.debug("MIKO_IP_SET: NO DATA TO MODIFY ")
        else :
            revision= int (res['ipset']['revision']) +1
                        
            newData= ['<ipset>',
                       '<objectId>%s</objectId>',
                       '<type>',
                       '<typeName>IPSet</typeName>',
                       '</type>',
                       '<description>%s</description>',
                       '<name>%s</name>',
                       '<revision>%s</revision>',
                       '<objectTypeName />',
                       '<value>%s</value>',
                       '</ipset>']
            
            newData = ''.join(newData) % (oid,description, name,revision, value)
            
            res = self.call('/api/2.0/services/ipset/%s' % oid,  'PUT', 
                        newData, headers={'Content-Type':'text/xml'}, parse=False)
        
        return res    
    
    def delete(self, oid):
        """
        :param oid: securitygroup id
        """
        res = self.call('/api/2.0/services/ipset/%s' % oid,  'DELETE', 
                        '', timeout=600)
        return True

class VsphereNetworkService(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self):
        """List Services on a Scope
        """
        objs = self.call('/api/2.0/services/application/scope/globalroot-0',
                         'GET', '')
        items = objs['list']['application']
        if isinstance(items, dict):
            items = [items]           
        res = []
        for item in items:
            if u'element' in item.keys():
                res.append({u'id':item[u'objectId'], 
                            u'proto':item[u'element'][u'applicationProtocol'],
                            u'ports':item[u'element'][u'value'],
                            u'revision':item[u'revision'],
                            u'name':item[u'name']})
        return res
    
    def get(self, proto, ports):
        """Get service id
        
        :param proto: service protocol. Ex. TCP, UDP, ICMP, ..
        :param ports: service ports. Ex. 80, 8080, 7200,7210,7269,7270,7575,  9000-9100
        :return: None if query empty
        """
        objs = self.call('/api/2.0/services/application/scope/globalroot-0',
                         'GET', '')
        items = objs['list']['application']
        datas = {}
        for item in items:
            if u'element' in item.keys():
                val = item[u'element'][u'value']
                objectid = item[u'objectId']
                data = {u'id':objectid, 
                        u'proto':item[u'element'][u'applicationProtocol'],
                        u'ports':item[u'element'][u'value'],
                        u'revision':item[u'revision'],
                        u'name':item[u'name']}
                try:
                    datas[item[u'element'][u'applicationProtocol']][val] = data
                except:
                    datas[item[u'element'][u'applicationProtocol']] = {val:data}
                      
        try:
            return datas[proto][ports]
        except:
            raise VsphereError(u'No port found')
    
    def info(self, sg):
        """
        """
        res = sg
        return sg
    
    def create(self, protocol, ports, name, desc):
        """Create a new service on the specified scope.
        
        :param name: ip set name
        :param desc: ip set description
        :param ipset: list of ip. Ex. 10.112.201.8-10.112.201.14
        :return: mor id
        """
        data = ['<application>',
                '<objectId></objectId>',
                '<type>',
                '<typeName/>',
                '</type>',
                '<description>%s</description>',
                '<name>%s</name>',
                '<revision>0</revision>',
                '<objectTypeName></objectTypeName>',
                '<element>',
                '<applicationProtocol>%s</applicationProtocol>',
                '<value>%s</value>',
                '</element>',
                '</application>']
        data = ''.join(data) % (desc, name, protocol, ports)
        res = self.call('/api/2.0/services/application/globalroot-0',
                        'POST', data, headers={'Content-Type':'text/xml'},
                        timeout=600)
        return res
    
    def delete(self, oid):
        """Delete a service by specifying its <applicationgroup-id>. 
        The force=flag indicates if the delete should be forced or unforced. 
        For forced deletes, the object is deleted irrespective of its use in 
        other places such as firewall rules, which invalidates other 
        configurations referring to the deleted object. For unforced deletes, 
        the object is deleted only if it is not being used by any other 
        configuration. The default is unforced (false).

        :param oid: securitygroup id
        """
        res = self.call('/api/2.0/services/application/%s' % oid,  'DELETE', 
                        '', timeout=600)
        return True

class VsphereNetworkDlr(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self, datacenter=None, portgroup=None):
        """
        :param datacenter: Retrieve Edges by datacenter
        :param portgroup: Retrieve Edges with one interface on specified port group
        """
        params = {}
        if datacenter is not None:
            params['datacenter'] = datacenter
        if portgroup is not None:
            params['portgroup'] = portgroup            
        params = urlencode(params)
        items = self.call('/api/4.0/edges?%s' % params, 'GET', '')\
                ['pagedEdgeList']['edgePage']['edgeSummary']
        if isinstance(items, dict):
            items = [items]                
        res = [i for i in items if i["edgeType"] == "distributedRouter"]
        return res
    
    def get(self, oid):
        """
        :param oid: dlr id
        """
        res = self.call('/api/4.0/edges/%s' % oid,  'GET', '')
        return res['edge']
    
    def info(self, dlr):
        """TODO
        :param dlr: dlr instance
        """
        dlr.pop('id')
        res = dlr
        return res  
 
    def create(self,dictNewDlr):
        """
        Create a Distribuited Logical Router
        
        ( in working ) Author: Miko
        
           TO DO:   1) multiply address for each  interface
                    2) HA edge
                    3) async task 

        
        :param dictNewDlr: a dictionary containing the value to create a new DLR 
        
            Dictionary format example:            
            
            dict = {'datacenterMoid':'datacenter-38',
                    'name':'NSX_Miko-APIDICT',
                    'staticRouting':{'enabled':'true',
                                     'vnic':'2',
                                     'mtu':'1500',
                                     'description':'Miko Gateway',
                                     'gatewayAddress':'10.102.184.1'},
                    'appliances':{'deployAppliances':'true',
                                  'resourcePoolId':'domain-c54',
                                  'datastoreId':'datastore-93'},
                    'cliSettings':{'remoteAccess':'true',
                                   'userName':'admin',
                                   'password':'Applenumber@143'},
                    'mgmtInterface':{'connectedToId':'dvportgroup-82'},
                    'interfaces':{'interface':[
                                    {'name':'Uplink_miko_by_API',
                                    'mtu':'1500','type':'uplink',
                                    'connectedToId':'dvportgroup-82',
                                    'primaryAddress':'10.102.184.40',
                                    'subnetMask':'255.255.255.0',
                                    'subnetPrefixLength':'24',
                                    'isConnected':'true'},
                                    {'name':'internal_miko_by_API',
                                    'mtu':'1500',
                                    'type':'internal',
                                    'connectedToId':'virtualwire-7',
                                    'primaryAddress':'192.168.100.1',
                                    'subnetMask':'255.255.255.0',
                                    'subnetPrefixLength':'24',
                                    'isConnected':'true'}
                                    ]}
                    }
        """
        
        if dictNewDlr['appliances']['deployAppliances']=='false':
            #
            # NO Appliance to deploy: i have to create DLR WITHOUT static routing adminDistance
            #    
            edge=['<edge>',
                '<datacenterMoid>%s</datacenterMoid>',
                '<type>distributedRouter</type>',
                '<name>%s</name>',
                '<features>',       
                    '<routing>',
                    '<enabled>%s</enabled>',
                    '<staticRouting>',
                        '<defaultRoute>',
                            '<vnic>%s</vnic>',
                            '<mtu>%s</mtu>',
                            '<description>%s</description>',
                            '<gatewayAddress>%s</gatewayAddress>',
                        '</defaultRoute>',
                    '<staticRoutes/>',
                    '</staticRouting>',
                    '</routing>',
                '</features>',        
                '<appliances>',
                    '<deployAppliances>%s</deployAppliances>',
                '</appliances>',
                '<cliSettings>',
                    '<remoteAccess>%s</remoteAccess>',
                    '<userName>%s</userName>',
                    '<password>%s</password>',
                '</cliSettings>',
                '<mgmtInterface>',
                    '<connectedToId>%s</connectedToId>',
                '</mgmtInterface>',
                '<interfaces>']

            edge=''.join(edge) % (dictNewDlr['datacenterMoid'],dictNewDlr['name'],
                                  dictNewDlr['staticRouting']['enabled'], dictNewDlr['staticRouting']['vnic'], dictNewDlr['staticRouting']['mtu'],
                                  dictNewDlr['staticRouting']['description'], dictNewDlr['staticRouting']['gatewayAddress'],
                                  dictNewDlr['appliances']['deployAppliances'],
                                  dictNewDlr['cliSettings']['remoteAccess'],dictNewDlr['cliSettings']['userName'],dictNewDlr['cliSettings']['password'],
                                  dictNewDlr['mgmtInterface']['connectedToId'])

        else:
            
            
            edge=['<edge>',
                '<datacenterMoid>%s</datacenterMoid>',
                '<type>distributedRouter</type>',
                '<name>%s</name>',
                '<features>',       
                    '<routing>',
                    '<enabled>%s</enabled>',
                    '<staticRouting>',
                        '<defaultRoute>',
                            '<vnic>%s</vnic>',
                            '<mtu>%s</mtu>',
                            '<description>%s</description>',
                            '<gatewayAddress>%s</gatewayAddress>',
                            '<adminDistance>1</adminDistance>',
                        '</defaultRoute>',
                    '<staticRoutes/>',
                    '</staticRouting>',
                    '</routing>',
                '</features>',        
                '<appliances>',
                '<deployAppliances>%s</deployAppliances>',
                    '<appliance>',
                    '<resourcePoolId>%s</resourcePoolId>',
                    '<datastoreId>%s</datastoreId>',
                    '</appliance>',
                    '</appliances>',
                '<cliSettings>',
                    '<remoteAccess>%s</remoteAccess>',
                    '<userName>%s</userName>',
                    '<password>%s</password>',
                '</cliSettings>',
                '<mgmtInterface>',
                    '<connectedToId>%s</connectedToId>',
                '</mgmtInterface>',
                '<interfaces>']
            edge=''.join(edge) % (dictNewDlr['datacenterMoid'],dictNewDlr['name'],
                                  dictNewDlr['staticRouting']['enabled'], dictNewDlr['staticRouting']['vnic'], dictNewDlr['staticRouting']['mtu'],
                                  dictNewDlr['staticRouting']['description'], dictNewDlr['staticRouting']['gatewayAddress'],
                                  dictNewDlr['appliances']['deployAppliances'],
                                  dictNewDlr['appliances']['resourcePoolId'],
                                  dictNewDlr['appliances']['datastoreId'],
                                  dictNewDlr['cliSettings']['remoteAccess'],dictNewDlr['cliSettings']['userName'],dictNewDlr['cliSettings']['password'],
                                  dictNewDlr['mgmtInterface']['connectedToId'])

        # Costruisco parte del file XML per la sezione interfaces 
        interfaces=""
        for element in dictNewDlr['interfaces']['interface']:
            interface =[ '<interface>',
                        '<name>%s</name>',
                        '<addressGroups>',
                            '<addressGroup>',
                            '<primaryAddress>%s</primaryAddress>',
                            '<subnetMask>%s</subnetMask>',
                            '<subnetPrefixLength>%s</subnetPrefixLength>',
                            '</addressGroup>',
                        '</addressGroups>',
                        '<mtu>%s</mtu>',
                        '<type>%s</type>',
                        '<isConnected>%s</isConnected>',
                        '<isSharedNetwork>false</isSharedNetwork>',
                        '<connectedToId>%s</connectedToId>',
                        '</interface>'
                        ]
            interface=''.join(interface)%(
                element['name'],
                element['primaryAddress'],
                element['subnetMask'],
                element['subnetPrefixLength'],
                element['mtu'],
                element['type'],
                element['isConnected'],
                element['connectedToId'])
            interfaces=interfaces + interface
        
        XML=edge+interfaces + "</interfaces></edge>"
        
        res = self.call('/api/4.0/edges',  'POST', 
                        XML, headers={'Content-Type':'text/xml'}, parse=False) 
                            
        return res


    
    def delete(self, oid):       
        """
        
        Modified by Miko ( TO DO by Sergio )
    
        
        :param oid: edge id
        """
        
        res = self.call('/api/4.0/edges/%s' % oid,  'DELETE', 
                        '', timeout=600)
        return True

        
class VsphereNetworkEdge(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def list(self, datacenter=None, portgroup=None):
        """
        :param datacenter: Retrieve Edges by datacenter
        :param portgroup: Retrieve Edges with one interface on specified port group
        """
        params = {}
        if datacenter is not None:
            params['datacenter'] = datacenter
        if portgroup is not None:
            params['portgroup'] = portgroup            
        params = urlencode(params)
        items = self.call('/api/4.0/edges?%s' % params, 'GET', '')\
                ['pagedEdgeList']['edgePage']['edgeSummary']
        if isinstance(items, dict):
            items = [items]
        res = [i for i in items if i["edgeType"] == "gatewayServices"]
        return res
    
    def get(self, oid):
        """
        :param oid: edge id
        """
        res = self.call('/api/4.0/edges/%s' % oid,  'GET', '')
        return res['edge']
    
    def info(self, edge):
        """TODO
        :param dlr: edge instance
        """
        edge.pop('id')
        res = edge
        return res  

    def create(self,dictNewEsg):
        

        """
        Create a NSX EDGE Service Gateway
        
        ( in working ) Author: Miko
        
           TO DO:   1) multiply address for each  interface
                    2) HA edge
                    3) async task 

        
        :param dictNewEsg: a dictionary containing the value to create a new NSX Edge Service Gateway 
        
            Dictionary format example:            
            
            dictNewEsg= {'datacenterMoid':'datacenter-38',
                        'name':'NSX_Miko-API DLR',
                        'tenant':'Default',
                        'vseLogLevel':'emergency',
                        'staticRouting':{'enabled':'true','vnic':'0','mtu':'1500','description':'Miko Gateway','gatewayAddress':'10.102.184.1'},  
                        'appliances':{'applianceSize':'compact','resourcePoolId':'domain-c54','datastoreId':'datastore-93'},
                        'cliSettings':{'remoteAccess':'true','userName':'admin','password':'Applenumber!143'},
                        'vnics':{'vnic':[{'name':'Uplink_miko_by_API','mtu':'1500','type':'uplink',
                                                     'portgroupId':'dvportgroup-82',
                                                     'primaryAddress':'10.102.184.40','subnetPrefixLength':'24',
                                                     'enableProxyArp':'false',
                                                     'enableSendRedirects':'true',
                                                     'isConnected':'true'},
                                                   {'name':'internal_miko_by_API','mtu':'1500','type':'internal',
                                                     'portgroupId':'virtualwire-7',
                                                     'primaryAddress':'192.168.100.1','subnetPrefixLength':'24',
                                                     'enableProxyArp':'false',
                                                     'enableSendRedirects':'true',                                                
                                                     'isConnected':'true'},
                                                    {'name':'internal_miko_by_API2','mtu':'1500','type':'internal',
                                                     'portgroupId':'virtualwire-1',
                                                     'primaryAddress':'192.168.10.1','subnetPrefixLength':'24',
                                                     'enableProxyArp':'false',
                                                     'enableSendRedirects':'true',                                                
                                                     'isConnected':'true'}
                                                    ]}       
                        }
        """

        edge=['<edge>',
            '<datacenterMoid>%s</datacenterMoid>',
            '<name>%s</name>',
            '<tenant>%s</tenant>',
            '<vseLogLevel>%s</vseLogLevel>',
            '<appliances>',
                '<applianceSize>%s</applianceSize>',
                '<appliance>',
                '<resourcePoolId>%s</resourcePoolId>',
                '<datastoreId>%s</datastoreId>',
                '</appliance>',
            '</appliances>',
            '<features>',       
                '<routing>',
                    '<enabled>%s</enabled>',                    
                    '<routingGlobalConfig>',
                        '<ecmp>false</ecmp>',
                        '<logging>',
                            '<enable>false</enable>',
                            '<logLevel>info</logLevel>',
                        '</logging>',
                    '</routingGlobalConfig>',
                    '<staticRouting>',
                        '<defaultRoute>',
                            '<vnic>%s</vnic>',
                            '<mtu>%s</mtu>',
                            '<description>%s</description>',
                            '<gatewayAddress>%s</gatewayAddress>',
                            '<adminDistance>1</adminDistance>',
                        '</defaultRoute>',
                    '<staticRoutes/>',
                    '</staticRouting>',
                '</routing>',
            '</features>',        
            '<cliSettings>',
                '<remoteAccess>%s</remoteAccess>',
                '<userName>%s</userName>',
                '<password>%s</password>',
            '</cliSettings>',
            '<vnics>']
        
        edge=''.join(edge) % (dictNewEsg['datacenterMoid'],dictNewEsg['name'],dictNewEsg['tenant'],dictNewEsg['vseLogLevel'],
                              dictNewEsg['appliances']['applianceSize'],
                              dictNewEsg['appliances']['resourcePoolId'],
                              dictNewEsg['appliances']['datastoreId'],                              
                              dictNewEsg['staticRouting']['enabled'], dictNewEsg['staticRouting']['vnic'], dictNewEsg['staticRouting']['mtu'],
                              dictNewEsg['staticRouting']['description'], dictNewEsg['staticRouting']['gatewayAddress'],
                              dictNewEsg['cliSettings']['remoteAccess'],dictNewEsg['cliSettings']['userName'],dictNewEsg['cliSettings']['password'])
        
        interfaces=""
        i=0
        for element in dictNewEsg['vnics']['vnic']:
            interface =[ '<vnic>',
                        '<index>%s</index>',
                        '<name>%s</name>',
                        '<addressGroups>',
                            '<addressGroup>',
                            '<primaryAddress>%s</primaryAddress>',                            
                            '<subnetPrefixLength>%s</subnetPrefixLength>',
                            '</addressGroup>',
                        '</addressGroups>',
                        '<mtu>%s</mtu>',
                        '<type>%s</type>',
                        '<isConnected>%s</isConnected>',                        
                        '<enableProxyArp>%s</enableProxyArp>',
                        '<enableSendRedirects>%s</enableSendRedirects>',
                        '<portgroupId>%s</portgroupId>',
                        '</vnic>'
                        ]
            interface=''.join(interface)%(i,
                element['name'],
                element['primaryAddress'],
                element['subnetPrefixLength'],
                element['mtu'],
                element['type'],
                element['isConnected'],
                element['enableProxyArp'],
                element['enableSendRedirects'],
                
                element['portgroupId'])
            interfaces=interfaces + interface
            i=i+1
        
        XML=edge+interfaces + "</vnics></edge>"
        
        res = self.call('/api/4.0/edges',  'POST', 
                        XML, headers={'Content-Type':'text/xml'}, parse=False) 
                            
        return res
    
            
    def delete(self, oid):       
        """
        Modify/Edit ipset properties
        Modified by Miko ( TO DO by Sergio )

        
        :param oid: edge id
        """
        
        res = self.call('/api/4.0/edges/%s' % oid,  'DELETE', 
                        '', timeout=600)
        return True

class VsphereNetworkLB(VsphereObject):
    """
    Class implementing the NSX Edge load balancer functionality. 
    
    The NSX Edge load balancer enables high-availability service and distributes the network traffic 
    load among multiple servers. 
    It distributes incoming service requests evenly among multiple servers in such a way that
    the load distribution is transparent to users.
    
    Author : Miko
    Date: Marzo 2017    
    
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
    
    def get_config(self,edgeId):
        """ """
                
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config' % edgeId, u'GET', u'')
        
        
        return res[u'loadBalancer']

    
    def update_global_config (self,edgeId,enabled='True',edgeLogging='false',edgeLogLevel='warning',
                              accelerationEnabled='False'):
        """ Enable (or Disable)load balancer configuration and logging configuration.   
        
        :param edgeId: ID of the edge to enable or to disable
        :param enable: if false the edge will be disabled ( Default = true )
        :param edgeLogging : enable or disable edge log
        :param edgeLogLevel: Valid log levels are: EMERGENCY|ALERT|CRITICAL|ERROR|WARNING|NOTICE|INFO|DEBUG
                            Default = INFO
                            
                            
        TO DO: service insertion section
        """
        # since during the API call of enable or disable the object, the LB will delete the original global configuration for the edge
        # i had to read the actual configuration and save the result in a XML format (parse=False )
        xmlres = self.call(u'/api/4.0/edges/%s/loadbalancer/config' % edgeId,u'GET', u'', parse=False )        
        #self.logger.debug("Lettura XML :%s" %xmlres)
        
        root = ElementTree.fromstring(xmlres)
        
        # change the enable Load Balancer parameter
        root_enabled = root.find('enabled')
        root_enabled.text = enabled
        
        # change the accelerationEnabled parameter
        root_accelerationEnabled = root.find('accelerationEnabled')
        root_accelerationEnabled.text = accelerationEnabled
        
        # change in the logging sections the logLevel and enable  parameters
        root_logging = root.find('logging')
        edgeLogLevelXML = root_logging.find('logLevel')
        edgeLogLevelXML.text = edgeLogLevel
        edgeLoggingEnable = root_logging.find('enable')
        edgeLoggingEnable.text=edgeLogging
        
        # TO DO:  service insertion section parameter with third party appliances
                
        root = ''.join(tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config' % edgeId,  u'PUT', 
                        root, headers={'Content-Type':'text/xml'}, parse=False)
        
        return (res)

    def list_app_profile (self,edgeId):
        """ 
        An application profile are use to define the behavior of a particular type of 
            network traffic.    
            
        list all application profiles for the edge identified by edgeId
        
        :param egdeId
        
        """

        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % edgeId, u'GET', u'')
        
        return res[u'loadBalancer'][u'applicationProfile']
        

    def get_app_profile (self,edgeId,applicationProfileId):
        """ 
        An application profile are use to define the behavior of a particular type of 
            network traffic.  
        
        list the details of a single application profile identified by 'applicationProfileId'
            
        :param edgeId :ID of the edge acting as load balancer
        :param applicationProfileId: ID of the application profiles to list
        
        TO DO: implementing  https profiles without SSL passthrough
        
        """
            
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/applicationprofiles/%s' % (edgeId,applicationProfileId), u'GET', u'')

        #self.logger.info ("Nuova versione :%s" % versione)
        return (res)

    def add_app_profile_old (self,edgeId,prof_type,name,persistence='None',expire='None',httpRedirect_url='',
                         insertXForwardedFor='false',sslPassthrough='false',serverSslEnabled='false',
                         cookiename='None',cookiemode ='insert'):
        """ An application profile are use to define the behavior of a particular type of network traffic.    """
                
        if prof_type == 'TCP'or prof_type=='UDP':
            if persistence == 'None':                
                XMLReq= [
                            '<applicationProfile>',
                                '<name>%s</name>',
                                '<insertXForwardedFor>false</insertXForwardedFor>',
                                '<sslPassthrough>false</sslPassthrough>',
                                '<template>%s</template>',
                                '<serverSslEnabled>false</serverSslEnabled>',
                            '</applicationProfile>']
                XMLReq = ''.join(XMLReq) % (name,prof_type)
            else:
                if expire == 'None':                    
                    XMLReq= [
                                '<applicationProfile>',
                                    '<persistence>',
                                    '<method>%s</method>',
                                    '</persistence>',
                                    '<name>%s</name>',
                                    '<insertXForwardedFor>false</insertXForwardedFor>',
                                    '<sslPassthrough>false</sslPassthrough>',
                                    '<template>%s</template>',
                                    '<serverSslEnabled>false</serverSslEnabled>',
                                '</applicationProfile>']
                    XMLReq = ''.join(XMLReq) % (persistence,name,prof_type)
                else:                        
                    XMLReq= [
                                '<applicationProfile>',
                                    '<persistence>',
                                    '<method>%s</method>',
                                    '<expire>%s</expire>',
                                    '</persistence>',
                                    '<name>%s</name>',
                                    '<insertXForwardedFor>false</insertXForwardedFor>',
                                    '<sslPassthrough>false</sslPassthrough>',
                                    '<template>%s</template>',
                                    '<serverSslEnabled>false</serverSslEnabled>',
                                '</applicationProfile>']
                    XMLReq = ''.join(XMLReq) % (persistence,expire,name,prof_type)
  
            self.logger.info ("XMLReq :%s" % XMLReq)
            res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % edgeId,  
                            'POST',XMLReq, headers={'Content-Type':'text/xml'}, parse=False)
        
        #if prof_type == 'HTTP'or prof_type=='HTTPS':
        if prof_type == 'HTTP':
            if persistence == 'None':                
                XMLReq= [
                        '<applicationProfile>',
                            '<httpRedirect>',
                                '<to>%s</to>'
                            '</httpRedirect>',
                            '<name>%s</name>',
                            '<insertXForwardedFor>%s</insertXForwardedFor>',
                            '<sslPassthrough>%s</sslPassthrough>',
                            '<template>%s</template>',
                            '<serverSslEnabled>%s</serverSslEnabled>',
                        '</applicationProfile>']
                XMLReq = ''.join(XMLReq) % (httpRedirect_url,name,insertXForwardedFor,sslPassthrough,prof_type,serverSslEnabled)
 
            elif persistence =='cookie' and cookiemode =='insert':                

                XMLReq= [
                        '<applicationProfile>',
                            '<httpRedirect>',
                                '<to>%s</to>'
                            '</httpRedirect>',
                            '<persistence>',
                                '<method>%s</method>',
                                '<cookieName>%s</cookieName>',
                                '<cookieMode>%s</cookieMode>',
                            '</persistence>',
                            '<name>%s</name>',
                            '<insertXForwardedFor>%s</insertXForwardedFor>',
                            '<sslPassthrough>%s</sslPassthrough>',
                            '<template>%s</template>',
                            '<serverSslEnabled>%s</serverSslEnabled>',
                        '</applicationProfile>']               
                XMLReq = ''.join(XMLReq) % (httpRedirect_url,persistence,cookiename,cookiemode,name,insertXForwardedFor,
                                            sslPassthrough,prof_type,serverSslEnabled)
                
            elif persistence =='cookie' and cookiemode !='insert':

                XMLReq= [
                        '<applicationProfile>',
                            '<httpRedirect>',
                                '<to>%s</to>'
                            '</httpRedirect>',
                            '<persistence>',
                                '<method>%s</method>',
                                '<cookieName>%s</cookieName>',
                                '<cookieMode>%s</cookieMode>',
                                '<expire>%s</expire>',                            
                            '</persistence>',
                            '<name>%s</name>',
                            '<insertXForwardedFor>%s</insertXForwardedFor>',
                            '<sslPassthrough>%s</sslPassthrough>',
                            '<template>%s</template>',
                            '<serverSslEnabled>%s</serverSslEnabled>',
                        '</applicationProfile>']               
                XMLReq = ''.join(XMLReq) % (httpRedirect_url,persistence,cookiename,cookiemode,expire,
                                            name,insertXForwardedFor,sslPassthrough,prof_type,serverSslEnabled)

            elif persistence == 'sourceip':

                XMLReq= [
                        '<applicationProfile>',
                            '<httpRedirect>',
                                '<to>%s</to>'
                            '</httpRedirect>',
                            '<persistence>',
                                '<method>%s</method>',
                                '<expire>%s</expire>',                            
                            '</persistence>',
                            '<name>%s</name>',
                            '<insertXForwardedFor>%s</insertXForwardedFor>',
                            '<sslPassthrough>%s</sslPassthrough>',
                            '<template>%s</template>',
                            '<serverSslEnabled>%s</serverSslEnabled>',
                        '</applicationProfile>']               
                
                XMLReq = ''.join(XMLReq) % (httpRedirect_url,persistence,expire,
                                            name,insertXForwardedFor,sslPassthrough,prof_type,serverSslEnabled)
                if expire == 'None':
                    XMLReq= [
                            '<applicationProfile>',
                                '<httpRedirect>',
                                    '<to>%s</to>'
                                '</httpRedirect>',
                                '<persistence>',
                                    '<method>%s</method>',                                                                
                                '</persistence>',
                                '<name>%s</name>',
                                '<insertXForwardedFor>%s</insertXForwardedFor>',
                                '<sslPassthrough>%s</sslPassthrough>',
                                '<template>%s</template>',
                                '<serverSslEnabled>%s</serverSslEnabled>',
                            '</applicationProfile>']               
                    
                    XMLReq = ''.join(XMLReq) % (httpRedirect_url,persistence,
                                                name,insertXForwardedFor,sslPassthrough,prof_type,serverSslEnabled)
  
                
            
            self.logger.info ("XMLReq :%s" % XMLReq)
            res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % edgeId,  
                            'POST',XMLReq, headers={'Content-Type':'text/xml'}, parse=False)
     
        if prof_type == 'HTTPS' and sslPassthrough == 'true':

            if persistence == 'None':                
                XMLReq= [
                        '<applicationProfile>',
                            '<name>%s</name>',
                            '<insertXForwardedFor>%s</insertXForwardedFor>',
                            '<sslPassthrough>%s</sslPassthrough>',
                            '<template>%s</template>',
                            '<serverSslEnabled>%s</serverSslEnabled>',
                        '</applicationProfile>']
                XMLReq = ''.join(XMLReq) % (name,insertXForwardedFor,sslPassthrough,prof_type,serverSslEnabled)

            else :                
                if expire == 'None':
                    XMLReq= [
                            '<applicationProfile>',
                                '<persistence>',
                                    '<method>%s</method>',
                                '</persistence>',
                                '<name>%s</name>',
                                '<insertXForwardedFor>%s</insertXForwardedFor>',
                                '<sslPassthrough>%s</sslPassthrough>',
                                '<template>%s</template>',
                                '<serverSslEnabled>%s</serverSslEnabled>',
                            '</applicationProfile>']               
                    XMLReq = ''.join(XMLReq) % (persistence,name,insertXForwardedFor,
                                                sslPassthrough,prof_type,serverSslEnabled)
                
                else:
                    XMLReq= [
                            '<applicationProfile>',
                                '<persistence>',
                                    '<method>%s</method>',
                                    '<expire>%s</expire>',                            
                                '</persistence>',
                                '<name>%s</name>',
                                '<insertXForwardedFor>%s</insertXForwardedFor>',
                                '<sslPassthrough>%s</sslPassthrough>',
                                '<template>%s</template>',
                                '<serverSslEnabled>%s</serverSslEnabled>',
                            '</applicationProfile>']               
                    XMLReq = ''.join(XMLReq) % (persistence,expire,name,insertXForwardedFor,
                                                sslPassthrough,prof_type,serverSslEnabled)

            res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % edgeId,  
                            'POST',XMLReq, headers={'Content-Type':'text/xml'}, parse=False)

        
        
        if prof_type == 'HTTPS' and sslPassthrough == 'false':
            """
            TO DO:  
            """
            error = "add_app_profile: function not implemented yet"
            self.logger.error (error)           
            raise VsphereError(error, code=500)
               

        return (res)

    def add_app_profile (self,edgeId,template,name,persistence='None',expire='None',httpRedirect_url='',
                         insertXForwardedFor='false',sslPassthrough='false',serverSslEnabled='false',
                         cookiename='None',cookiemode ='insert'):
        """ Application profile are use to define the behavior of a particular type of network traffic.    
        
        ADD a new application profile to LB configuration of the edge identified by edgeID
        
        :param edgeId : morefid of the edge acting as load balancer
        :param template : Profile type; permitted  value [TCP | UDP | HTTP | HTTPS ]
        :param name : name of the new profile
        :param persistence : permitted value [None |sourceip | msrdp | cookie ] default value: None
        :param expire : [optional] persistence time in seconds
        :param httpRedirect_url : [optional] HTTP redirect URL
        :param insertXForwardedFor : insert X-Forwarded-for HTTP Header
        :param sslPassthrough : Enable SSL Passthrough
        :param serverSslEnabled : Enable Pool side SSL
        :param cookiename : name of the cookie
        :param cookiemode : permitted value [insert | prefix | appsession ]
        
        
        
        :raise VsphereError(error, code=500)
        
        
        TO DO : case of template = HTTPS andsslPassthrough == 'false'
        
        """
                
        XMLReq= [
                '<applicationProfile>',
                    '<httpRedirect>',
                        '<to>%s</to>',
                    '</httpRedirect>',
                    '<persistence>',
                        '<method>%s</method>',
                        '<cookieName>%s</cookieName>',
                        '<cookieMode>%s</cookieMode>',
                        '<expire>%s</expire>',                            
                    '</persistence>',
                    '<name>%s</name>',
                    '<insertXForwardedFor>%s</insertXForwardedFor>',
                    '<sslPassthrough>%s</sslPassthrough>',
                    '<template>%s</template>',
                    '<serverSslEnabled>%s</serverSslEnabled>',
                '</applicationProfile>']          
        
        if persistence =='None':            
            XMLReq[4]=''
            XMLReq[5]=''
            XMLReq[6]=''
            XMLReq[7]=''
            XMLReq[8]=''
            XMLReq[9]=''
        
        if expire == 'None' and persistence !='None':
            XMLReq[8]=''
            
        if persistence == 'sourceip':
            XMLReq[6]=''
            XMLReq[7]=''

        self.logger.debug ("XMLReq :%s" % XMLReq )
        
        if template == 'HTTPS' and sslPassthrough == 'false':
            """
            TO DO:  
            """
            error = "add_app_profile: function not implemented yet"
            self.logger.error (error)           
            raise VsphereError(error, code=500)

        if persistence =='None':
            XMLReq = ''.join(XMLReq) % (httpRedirect_url,name,insertXForwardedFor,sslPassthrough,template,serverSslEnabled)
        
        if expire == 'None' and persistence !='None'and persistence !='sourceip':
            XMLReq = ''.join(XMLReq) % (httpRedirect_url,persistence,cookiename,cookiemode,
                                            name,insertXForwardedFor,sslPassthrough,template,serverSslEnabled)

        if expire != 'None' and persistence !='None' and persistence !='sourceip':
            XMLReq = ''.join(XMLReq) % (httpRedirect_url,persistence,cookiename,cookiemode,expire,
                                            name,insertXForwardedFor,sslPassthrough,template,serverSslEnabled)

        if persistence == 'sourceip' and expire == 'None' :
            XMLReq = ''.join(XMLReq) % (httpRedirect_url,persistence,
                                            name,insertXForwardedFor,sslPassthrough,template,serverSslEnabled)

        if persistence == 'sourceip' and expire != 'None':
            XMLReq = ''.join(XMLReq) % (httpRedirect_url,persistence,expire,
                                            name,insertXForwardedFor,sslPassthrough,template,serverSslEnabled)

        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % edgeId,  
                          'POST',XMLReq, headers={'Content-Type':'text/xml'}, parse=False)
        return (res)




    def update_app_profile (self,edgeId,applicationProfileId,
                            template='None',name='None',persistence='None',expire='None',
                            httpRedirect_url='None',insertXForwardedFor='None',sslPassthrough='None',
                            serverSslEnabled='None',cookiename='None',cookiemode ='None'):
        """ An application profile are use to define the behavior of a particular type of network traffic.    
        
        
        
        """
                

        xmlres = self.call(u'/api/4.0/edges/%s/loadbalancer/config/applicationprofiles/%s' % (edgeId,applicationProfileId),
                            u'GET', u'',parse=False)


        self.logger.debug (xmlres)
        root = ElementTree.fromstring(xmlres)
        root_template = root.find('template')
        root_name=root.find('name')
        root_persistence=root.find('persistence')
        expire_persistence=root_persistence.find('expire')
        method_persistence=root_persistence.find('method')
        #if expire_persistence:
        print(expire_persistence.text)

        if name!='None':
            root_name.text=name
        if expire != 'None':
            if not expire_persistence.text:
                # to do: aggiungere nuova sezione xml
                 pass
            else:
                expire_persistence.text=expire
        if persistence != 'None':
            method_persistence.text=persistence    
        


        '''

        root = ElementTree.fromstring(xmlres)
        
        # change the enable Load Balancer parameter
        root_enabled = root.find('enabled')
        root_enabled.text = enabled
        
        # change the accelerationEnabled parameter
        root_accelerationEnabled = root.find('accelerationEnabled')
        root_accelerationEnabled.text = accelerationEnabled
        
        # change in the logging sections the logLevel and enable  parameters
        root_logging = root.find('logging')
        edgeLogLevelXML = root_logging.find('logLevel')
        edgeLogLevelXML.text = edgeLogLevel
        edgeLoggingEnable =edgeId root_logging.find('enable')
        edgeLoggingEnable.text=edgeLogging
        
        # TO DO:  service insertion section parameter with third party appliances
                
        root = ''.join(tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config' % edgeId,  u'PUT', 
                        root, headers={'Content-Type':'text/xml'}, parse=False)



        '''
        root = ''.join(tostring(root))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/applicationprofiles/%s' % (edgeId,applicationProfileId),  u'PUT', 
                        root, headers={'Content-Type':'text/xml'}, parse=False)





        
        return (res)

    def del_app_profile (self,edgeId,applicationProfileId):
        """ 
        An application profile are use to define the behavior of a particular type of 
            network traffic.  
        
        DELETE a single application profile identified by 'applicationProfileId'
            
        :param edgeId :ID of the edge acting as load balancer
        :param applicationProfileId: ID of the application profiles to DELETE
        """
        
        
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/applicationprofiles/%s' % (edgeId,applicationProfileId),  
                        'DELETE', '', timeout=600)
        return True
        
    def del_all_app_profiles (self,edgeId):
        """ 
        An application profile are use to define the behavior of a particular type of 
            network traffic.  
        
        DELETE ALL application profiles identified by edgeId
            
        :param edgeId :ID of the edge acting as load balancer
        :param applicationProfileId: ID of the application profiles to DELETE
        """
        
        
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/applicationprofiles' % (edgeId),  
                        'DELETE', '', timeout=600)
        return True
        

    def list_pools (self,edgeId):
        """ 
        You can add a server pool to manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
   
            
        list all the pools for the edge identified by edgeId
        
        :param egdeId
        
        """

        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/pools' % edgeId, u'GET', u'')
        
        return res[u'loadBalancer'][u'pool']
 

    def get_pool (self,edgeId,poolId):
        """ 
        You can add a server pool to manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
        
        list the details of a single pool identified by 'poolId'
            
        :param edgeId :ID of the edge acting as load balancer
        :param poolId: ID of the pool to list
        
        
        
        """
            
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edgeId,poolId), u'GET', u'')

        #self.logger.info ("Nuova versione :%s" % versione)
        return (res)

    def add_pool (self,edgeId,name,algorithm,algorithmParameters='',
                  description='', transparent='false',monitorId=''):
        """ 
        With a server pool we can manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
   
            
        CREATE a new pool for the edge identified by edgeId
        
        :param egdeId : morefid of the edge acting as load balancer
        :param name : name of the new pool 
        :param algorithm : Valid algorithms are: IP-HASH|ROUND-ROBIN|URI|LEASTCONN|URL|HTTP-HEADER.
        :param algorithmParameters : 
                        if algorithm = URL
                            valid algorithmParameters are :urlParam=<url> where 1<=len(url)<=256 
                        
                        if algorithm = URI
                            valid algorithmParameters are : uriLength=<lenght> uriDepth=<depth>
                                where 1<= <lenght> <= 256 AND 1<= <depth> <=10
                        
                        if algorith = HTTP-HEADER
                            valid algorithmParameters are headerName=<name> where 1<=len(name)<=256 
                            
        :param description  [optional]
        :param transparent [default = false]
        :param monitorId : [optional]
        
        """
        XMLReq = [         
                '<pool>',
                    '<name>%s</name>',
                    '<algorithm>%s</algorithm>',
                    '<algorithmParameters>%s</algorithmParameters>',
                    '<description>%s</description>',
                    '<transparent>%s</transparent>',
                    '<monitorId>%s</monitorId>',
                '</pool>'
                ]
        
        if algorithm.lower() == 'ip-hash' or algorithm.lower() == 'roud-robin' or algorithm.lower() == 'leastconnhash' : 
            XMLReq[3] =''                
            XMLReq = ''.join(XMLReq) % (name,algorithm,
                                    description,transparent,monitorId)
        else :
            XMLReq = ''.join(XMLReq) % (name,algorithm,algorithmParameters,
                                    description,transparent,monitorId)
            
        
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/pools' % edgeId, u'POST',  
                                    XMLReq,headers={'Content-Type':'text/xml'}, parse=False)
        return (res)
 

    def update_pool_todo (self,edgeId,poolId,name,algorithm,algorithmParameters='',
                  description='', transparent='false',monitorId=''):
        """ 
        With a server pool we can manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
   
        
        TO DO:
            
        UPDATE the pool identified by identified by 'poolId' into the edge 'edgeId'
        
        :param egdeId : morefid of the edge acting as load balancer
        :param name : name of the new pool 
        :param algorithm : Valid algorithms are: IP-HASH|ROUND-ROBIN|URI|LEASTCONN|URL|HTTP-HEADER.
        :param algorithmParameters : 
                        if algorithm = URL
                            valid algorithmParameters are :urlParam=<url> where 1<=len(url)<=256 
                        
                        if algorithm = URI
                            valid algorithmParameters are : uriLength=<lenght> uriDepth=<depth>
                                where 1<= <lenght> <= 256 AND 1<= <depth> <=10
                        
                        if algorith = HTTP-HEADER
                            valid algorithmParameters are headerName=<name> where 1<=len(name)<=256 
                            
        :param description  [optional]
        :param transparent [default = false]
        :param monitorId : [optional]
        
        """
        XMLReq = [         
                '<pool>',
                    '<name>%s</name>',
                    '<algorithm>%s</algorithm>',
                    '<algorithmParameters>%s</algorithmParameters>',
                    '<description>%s</description>',
                    '<transparent>%s</transparent>',
                    '<monitorId>%s</monitorId>',
                '</pool>'
                ]
        """
        
        TO DO :
         
         
        """
        
        
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edgeId,poolId), u'PUT',  
                                    XMLReq,headers={'Content-Type':'text/xml'}, parse=False)
        return (res)

    def add_pool_member (self,edgeId,poolId,
                         ipAddress='none',
                         groupingObjectId='none',groupingObjectName='none',
                         weight='1',monitorPort='0',port='none',maxConn='0',minConn='0',
                         condition='enabled',name='none'):
        """ 
        Add a new member to the pool  identified by identified by 'poolId' into the edge 'edgeId'
        
        With a server pool we can  manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
        
        add a new member to the pool  identified by identified by 'poolId' into the edge 'edgeId'
            
        :param edgeId :ID of the edge acting as load balancer
        :param poolId: ID of the pool to list
        :param ipAddress : IP address of the member to add
        :param groupingObjectId : morefId of the vmware object
        :param groupingObjectName : name of the vmware object
        :param weight : (optional)
        :param monitorPort : 
        :param port : (optional)
        :param maxConn : (optional)
        :param minConn : (optional)
        :param condition :
        :param name :
        
        For pools we have to update the full information to add a backend member 
            or for that matter remove a member. 

        NOTE:
        
        if the new member is an IP ADDRESS, the XML must be in this format:
         
        <member>
            <memberId>member-12</memberId>
            <ipAddress>10.102.189.17</ipAddress>
            <weight>1</weight>
            <monitorPort>80</monitorPort>
            <maxConn>0</maxConn>
            <minConn>0</minConn>
            <condition>enabled</condition>
            <name>server_by_ip</name>
        </member>
   
        if the member is an VC CONTAINER. the XML must be :
        
        <member>
            <memberId>member-13</memberId>
            <groupingObjectId>domain-c54</groupingObjectId>
            <groupingObjectName>LEGACYCompute</groupingObjectName>
            <weight>1</weight>
            <monitorPort>80</monitorPort>
            <maxConn>0</maxConn>
            <minConn>0</minConn>
            <condition>enabled</condition>
            <name>cluster</name>
        </member>
                
        """
        
        # i had to read the actual configuration and save the result in a XML format (parse=False )
        xmlres = self.call(u'/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edgeId,poolId),u'GET', u'', parse=False )        
        self.logger.debug("Lettura XML :%s" %xmlres)
        
        pool = ElementTree.fromstring(xmlres)
        member = ElementTree.SubElement(pool, 'member')
        
        
        if port != 'none':
            portET = ElementTree.SubElement(member,'port')
            portET.text = port
                    
        if ipAddress!='none':
            ipAddressET = ElementTree.SubElement(member,'ipAddress')
            ipAddressET.text = ipAddress
        else:
            groupingObjectIdET = ElementTree.SubElement(member,'groupingObjectId')
            groupingObjectIdET.text = groupingObjectId
            groupingObjectNameET = ElementTree.SubElement(member,'groupingObjectName')
            groupingObjectNameET.text = groupingObjectName
            
        weightET = ElementTree.SubElement(member,'weight')
        weightET.text = weight
        
        monitorPortET = ElementTree.SubElement(member,'monitorPort')
        monitorPortET.text = monitorPort
        
        maxConnET = ElementTree.SubElement(member,'maxConn')
        maxConnET.text = maxConn
        
        minConnET = ElementTree.SubElement(member,'minConn')
        minConnET.text = minConn
        
        conditionET = ElementTree.SubElement(member,'condition')
        conditionET.text = condition
        
        nameET = ElementTree.SubElement(member,'name')
        nameET.text = name

        pool = ''.join(tostring(pool))
        res = self.call('/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edgeId,poolId),  u'PUT', 
                        pool, headers={'Content-Type':'text/xml'}, parse=False)
        
        return (res)        
  
    def del_pool (self,edgeId,poolId):
        """ 
        With a server pool we can manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
   
        
        DELETE the pool identified by 'poolId' into the edge 'edgeId'
        
        :param egdeId : morefid of the edge acting as load balancer
        :param poolId : name of the new pool 
        
        """
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/pools/%s' % (edgeId,poolId),  
                        'DELETE', '', timeout=600)
        return (res)
 
    def del_all_pools (self,edgeId):
        """ 
        With a server pool we can manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
   
        
        DELETE ALL the pools into the edge 'edgeId'
        
        :param egdeId : morefid of the edge acting as load balancer
        :param poolId : name of the new pool 
        
        """
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/pools' % edgeId,  
                        'DELETE', '', timeout=600)
        return (res)
 
    def list_virt_servers (self,edgeId):
        """ 
        You can add a server pool to manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
   
            
        list all the virtual servers for the edge identified by edgeId
        
        :param egdeId
        
        """

        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/virtualservers' % edgeId, u'GET', u'')
        
        return res[u'loadBalancer'][u'virtualServer']

    def get_virt_server (self,edgeId,virtualServerId):
        """ 
        You can add a server pool to manage and share backend servers flexibly and efficiently. 
        A pool manages load balancer distribution methods 
            and has a service monitor attached to it for health check parameters.
   
            
        list the details of a single virtual server identified by 'virtualServerId' into the edge 'edgeId'
        
        :param egdeId
        :param virtualServerId
        
        """

        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config/virtualservers/%s' % (edgeId,virtualServerId), u'GET', u'')
        
        return res[u'loadBalancer'][u'virtualServer']
 

   
    def delete (self,edgeId):
        """ Delete the whole Load Balancer section"""
        res = self.call(u'/api/4.0/edges/%s/loadbalancer/config' % edgeId,  u'DELETE', 
                        u'', timeout=600)
        return True

        
    
    
    
     
class VsphereNetworkDfw(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)

    def get_config(self):
        """ """
        res = self.call(u'/api/4.0/firewall/globalroot-0/config',
                        u'GET', u'')
        return res[u'firewallConfiguration']
    
    def get_sections(self, rule_type=u'LAYER2'):
        """Get list of section with rules.
        
        :param rule_type: rule type. Can be LAYER3, L3REDIRECT. If
                          not specify return all the sections [optional]
        :return:
        """
        res = self.call(u'/api/4.0/firewall/globalroot-0/config'\
                        u'?ruleType=%s' % rule_type,
                        u'GET', u'')
        res = res[u'filteredfirewallConfiguration']

        return res
    
    def get_layer3_section(self, sectionid=None, name=None):
        """
        :param sectionid: section id
        :param name: section name
        :return: json string
        
        Return example:
        
            .. code-block:: python
        
                {
                    "@name": "Default Section Layer3", 
                    "@timestamp": "1472659441651",
                    "@generationNumber": "1472659441651", 
                    "@id": "1031", 
                    "@type": "LAYER3"                    
                    "rule": [
                        {
                            "direction": "inout", 
                            "name": "Default Rule", 
                            "precedence": "default", 
                            "sectionId": "1031", 
                            "@logged": "true", 
                            "@disabled": "false", 
                            "action": "deny", 
                            "appliedToList": {
                                "appliedTo": {
                                    "isValid": "true", 
                                    "type": "DISTRIBUTED_FIREWALL", 
                                    "name": "DISTRIBUTED_FIREWALL", 
                                    "value": "DISTRIBUTED_FIREWALL"
                                }
                            }, 
                            "packetType": "any", 
                            "@id": "133087"
                        },..
                    ]
                }        
        """
        if sectionid is not None:
            res = self.call(u'/api/4.0/firewall/globalroot-0/config/'\
                            u'layer3sections/%s' % sectionid,
                            u'GET', u'')
            return res[u'section']
        elif name is not None:
            res = self.call(u'/api/4.0/firewall/globalroot-0/config/'\
                            u'layer3sections?name=%s' % name,
                            u'GET', u'')            
            return res[u'sections'][u'section']
    
    def get_rule(self, sectionid, ruleid):
        """
        :param sectionid: section id
        :param ruleid: rule id
        :return: json string
        
        Return example:
        
            .. code-block:: python        
        
                {
                    "direction": "inout", 
                    "name": "Default Rule", 
                    "precedence": "default", 
                    "@logged": "true", 
                    "@disabled": "false", 
                    "action": "deny", 
                    "appliedToList": {
                        "appliedTo": {
                            "isValid": "true", 
                            "type": "DISTRIBUTED_FIREWALL", 
                            "name": "DISTRIBUTED_FIREWALL", 
                            "value": "DISTRIBUTED_FIREWALL"
                        }
                    }, 
                    "packetType": "any", 
                    "@id": "133087"
                }
        """
        res = self.call(u'/api/4.0/firewall/globalroot-0/config/layer3sections'\
                        u'/%s/rules/%s' % (sectionid, ruleid),
                        u'GET', '')
        return res[u'rule']
    
    def print_sections(self, sections, print_rules=True, table=True):
        """Print frendly all the firewall rules and section
        
        :param print_rules: if True print rules detail
        """
        l3sections = sections["layer3Sections"]['section']
        if type(l3sections) is not list: l3sections = [l3sections]
        for l3section in l3sections:
            if print_rules is True:
                self.print_section(l3section, table)
            else:
                self.logger.info("%-10s%-70s%15s" % (l3section['@id'], 
                                                     l3section['@name'], 
                                                     l3section['@timestamp']))
        l2sections = sections["layer2Sections"]['section']
        if type(l2sections) is not list: l2sections = [l2sections]
        for l2section in l2sections:
            if print_rules is True:
                self.print_section(l2section, table)
            else:
                self.logger.info("%-10s%-70s%15s" % (l3section['@id'], 
                                                     l3section['@name'], 
                                                     l3section['@timestamp']))                
        
    def print_section(self, l3section, table=True):
        """Print frendly all the firewall rules and section
        """
        self.logger.info(''.join(['#' for i in xrange(120)]))
        self.logger.info("%-10s%-70s%15s" % 
                         (l3section['@id'], l3section['@name'], l3section['@timestamp']))
        self.logger.info(''.join(['#' for i in xrange(120)]))        
        
        if table is True:
            tmpl = "%-8s%-20s%-9s%-9s%-10s%-8s%20s%20s%20s%20s"
            title = ('id', 'name', 'logged', 'disabled', 'direction', 'action',
                     'sources', 'destinations', 'services', 'appliedto')
            self.logger.info(tmpl % title)
            self.logger.info(''.join(['-' for i in xrange(150)]))
        
        rules = l3section["rule"]
        if type(rules) is not list: rules = [rules]
        
        for rule in rules:
            if table is True:
                # sources
                sources = []
                try:
                    source = rule['sources']
                    infos = source['source']
                    if type(infos) is not list: infos = [infos]
                    for info in infos:
                        try: name = info['name']
                        except: name = ''
                        sources.append(name)
                except:
                    sources.append('* any')
                
                # destinations
                destinations = []
                try:
                    source = rule['destinations']
                    infos = source['destination']
                    if type(infos) is not list: infos = [infos]
                    for info in infos:
                        try: name = info['name']
                        except: name = ''
                        destinations.append(name)
                except:
                    destinations.append('* any')
                
                # services
                services = []
                try:
                    source = rule['services']
                    infos = source['service']
                    if type(infos) is not list: infos = [infos]
                    for info in infos:
                        try: name = truncate(info['name'], 5)
                        except: name = ''
                        services.append(name)
                except:
                    services.append('* any')
                
                # appliedToList
                appliedto = []
                try:
                    source = rule['appliedToList']
                    infos = source['appliedTo']
                    if type(infos) is not list: infos = [infos]
                    for info in infos:
                        try: name = truncate(info['name'], 9)
                        except: name = ''
                        appliedto.append(name)
                except:
                    appliedto.append('* any')             
                
                row = (rule['@id'], rule['name'], rule['@logged'], 
                       rule['@disabled'], rule['direction'], rule['action'],
                       ','.join(sources), ','.join(destinations), ','.join(services), 
                       ','.join(appliedto))
                self.logger.info(tmpl % row)
            else:
                self.print_rule(rule)
                self.logger.info('  '+''.join(['-' for i in xrange(100)]))
            
    def print_rule(self, rule):
        """Print frendly all the firewall rules and section
        """
        tmpl = "   %-15s:%20s"
        self.logger.info(tmpl % ('id', rule['@id']))
        self.logger.info(tmpl % ('name', rule['name']))
        self.logger.info(tmpl % ('logged', rule['@logged']))
        self.logger.info(tmpl % ('disabled', rule['@disabled']))
        self.logger.info(tmpl % ('direction', rule['direction']))
        #self.logger.info(tmpl % ('packetType', rule['packetType']))
        self.logger.info(tmpl % ('action', rule['action']))
        
        # sources
        self.logger.info(tmpl % ('sources:', ''))
        try:
            source = rule['sources']
            infos = source['source']
            if type(infos) is not list: infos = [infos]
            for info in infos:
                try: name = info['name']
                except: name = ''
                self.logger.info('%20s %s : %s : %s' % ('', name, info['value'], 
                                                        info['type']))
        except:
            self.logger.info('%20s %s %s' % ('', '*', 'any'))
        
        # destinations
        self.logger.info(tmpl % ('destinations:', ''))
        try:
            source = rule['destinations']
            infos = source['destination']
            if type(infos) is not list: infos = [infos]
            for info in infos:
                try: name = info['name']
                except: name = ''
                self.logger.info('%20s %s : %s : %s' % ('', name, info['value'], 
                                                        info['type']))
        except:
            self.logger.info('%20s %s %s' % ('', '*', 'any'))
        
        # services
        self.logger.info(tmpl % ('services:', ''))
        try:
            source = rule['services']
            infos = source['service']
            if type(infos) is not list: infos = [infos]
            for info in infos:
                try: name = info['name']
                except: name = ''
                self.logger.info('%20s %s : %s : %s' % ('', name, info['value'], 
                                                        info['type']))
        except:
            self.logger.info('%20s %s %s' % ('', '*', 'any'))
        
        # appliedToList
        self.logger.info(tmpl % ('applied to:', ''))
        try:
            source = rule['appliedToList']
            infos = source['appliedTo']
            if type(infos) is not list: infos = [infos]
            for info in infos:
                try: name = info['name']
                except: name = ''
                self.logger.info('%20s %s : %s : %s' % ('', name, info['value'], 
                                                        info['type']))
        except:
            self.logger.info('%20s %s %s' % ('', '*', 'any')) 
    
    def _append_rule_attribute(self, tag, value, rtype, name=None):
        """Append rule internal tag like source, destination and 
        appliedToList
        
        :param tag: tag can be source, destination, appliedTo and service
        :param name: rule name
        :param value: for certain rule contains morId
        :param rtype: type
        :return: list with rule structure
        """
        data = ['<%s>' % tag]
            
        if name is not None:
            data.append('<name>%s</name>' % name)
                    
        data.extend(['<value>%s</value>' % value,
                     '<type>%s</type>' % rtype,
                     '<isValid>true</isValid>',
                     '</%s>' % tag])
        return data
    
    def _append_rule_service_attribute(self, value):
        """Append rule internal tag service.
        
        :param value: contains service morId
        :param rtype: type
        :return: list with rule structure
        """
        data = ['<service><value>%s</value></service>' % value]
        return data    
    
    def _append_rule_definition(self, tags, tag, data):
        res = []
        if data is not None:
            if tags in ['sources', 'destinations']:
                res.append('<%s excluded="false">' % tags)
            else:
                res.append('<%s>' % tags)
            for s in data:
                res.extend(self._append_rule_attribute(tag, s['value'], 
                                                       s['type'], 
                                                       name=s['name']))
            res.append('</%s>' % tags)
        return res
    
    def _append_rule_service(self, data):
        """Append service configuration to rule
        
            Ex. [{u'port':u'*', u'protocol':u'*'}] -> *:*
                [{u'port':u'*', u'protocol':6}] -> tcp:*
                [{u'port':80, u'protocol':6}] -> tcp:80
                [{u'port':80, u'protocol':17}] -> udp:80
                [{u'protocol':1, u'subprotocol':8}] -> icmp:echo request        
        """
        res = [u'<services>']
        if data is not None:
            for s in data:
                if u'value' in s:
                    res.extend(u'<service><value>%s</value></service>' % s[u'value'])
                elif not (s[u'protocol'] == u'*' and s[u'port'] == u'*'):
                #else:
                    if u'subprotocol' not in s:
                        s[u'subprotocol'] = s[u'protocol']
                    res.extend(u'<service>')
                    if u'port' not in s or s[u'port'] == u'*':
                        port = u''
                    else:
                        port = s[u'port']
                    
                    res.extend(u'<destinationPort>%s</destinationPort>' % port)
                    res.extend(u'<protocol>%s</protocol>' % s[u'protocol'])
                    res.extend(u'<subProtocol>%s</subProtocol>' % s[u'subprotocol'])
                    res.extend(u'</service>')                   
        res.append(u'</services>')
        return res
    
    def create_section(self, name, action='allow', logged='false'):
        """Create new section
        
        :param name: section name
        :param action: new action value. Ie: allow, deny, reject [default=allow]
        :param logged: if True rule is logged [default=false]
        """
        """
                '<rule disabled="false" logged="false">',
                '<name>%s-rule-01</name>' % name,
                '<action>%s</action>' % action,
                '<appliedToList>',
                '<appliedTo>',
                '<name>DISTRIBUTED_FIREWALL</name>',
                '<value>DISTRIBUTED_FIREWALL</value>',
                '<type>DISTRIBUTED_FIREWALL</type>',
                '<isValid>true</isValid>',
                '</appliedTo>',
                '</appliedToList>',
                '<precedence>default</precedence>',
                '<direction>out</direction>',
                '<packetType>any</packetType>',
                '</rule>',        
        """
        
        data = ['<section name="%s">' % name,
                '</section>']
        data = ''.join(data)
        res = self.call('/api/4.0/firewall/globalroot-0/config/layer3sections',
                        'POST', data, headers={'Content-Type':'application/xml',
                                              'If-Match':self.manager.nsx['etag']})
        return res[u'section']
    
    def create_rule(self, sectionid, name, action, direction='inout', 
                    logged='false', sources=None, destinations=None, 
                    services=None, appliedto=None, precedence='default'):
        """
        
        :param sectionid: section id
        :param name: rule name
        :param action: new action value. Ie: allow, deny, reject [optional]
        :param logged: if 'true' rule is logged
        :param direction: rule direction: in, out, inout
        :param sources: List like [{'name':, 'value':, 'type':, }] [optional]
            Ex: [{'name':'db-vm-01', 'value':'vm-84', 'type':'VirtualMachine'}]
            Ex: [{'name':None, 'value':'10.1.1.0/24', 'type':'Ipv4Address'}]
            Ex: [{'name':'WEB-LS', 'value':'virtualwire-9', 
                  'type':'VirtualWire'}]
            Ex: [{'name':'APP-LS', 'value':'virtualwire-10', 
                  'type':'VirtualWire'}]
            Ex: [{'name':'SG-WEB2', 'value':'securitygroup-22', 
                  'type':'SecurityGroup'}]
            Ex: [{'name':'PAN-app-vm2-01 - Network adapter 1', 
                  'value':'50031300-ad53-cc80-f9cb-a97254336c01.000', 
                  'type':'vnic'}]                
        :param destinations: List like [{'name':, 'value':, 'type':, }] [optional]
            Ex: [{'name':'WEB-LS', 'value':'virtualwire-9', 
                  'type':'VirtualWire'}]
            Ex: [{'name':'APP-LS', 'value':'virtualwire-10', 
                  'type':'VirtualWire'}]
            Ex: [{'name':'SG-WEB-1', 'value':'securitygroup-21', 
                  'type':'SecurityGroup'}]                                    
        :param services: List like [{'name':, 'value':, 'type':, }] [optional]
            Ex: [{'name':'ICMP Echo Reply', 'value':'application-337', 
                  'type':'Application'}]
            Ex: [{'name':'ICMP Echo', 'value':'application-70', 
                  'type':'Application'}]
            Ex: [{'name':'SSH', 'value':'application-223', 
                  'type':'Application'}]
            Ex: [{'name':'DHCP-Client', 'value':'application-223', 
                  'type':'Application'},
                 {'name':'DHCP-Server', 'value':'application-223', 
                  'type':'Application'}]
            Ex: [{'name':'HTTP', 'value':'application-278', 
                  'type':'Application'},
                 {'name':'HTTPS', 'value':'application-335', 
                  'type':'Application'}]
            Ex. [{u'port':u'*', u'protocol':u'*'}] -> *:*
                [{u'port':u'*', u'protocol':6}] -> tcp:*
                [{u'port':80, u'protocol':6}] -> tcp:80
                [{u'port':80, u'protocol':17}] -> udp:80
                [{u'protocol':1, u'subprotocol':8}] -> icmp:echo request
                 
            Get id from https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
            For icmp Summary of Message Types:
                0  Echo Reply
                3  Destination Unreachable
                4  Source Quench
                5  Redirect
                8  Echo
               11  Time Exceeded
               12  Parameter Problem
               13  Timestamp
               14  Timestamp Reply
               15  Information Request
               16  Information Reply
        :param appliedto: List like [{'name':, 'value':, 'type':, }] [optional]
            Ex: [{'name':'DISTRIBUTED_FIREWALL', 
                  'value':'DISTRIBUTED_FIREWALL', 
                  'type':'DISTRIBUTED_FIREWALL'}]
            Ex: [{'name':'ALL_PROFILE_BINDINGS', 
                  'value':'ALL_PROFILE_BINDINGS', 
                  'type':'ALL_PROFILE_BINDINGS'}]
            Ex: [{'name':'db-vm-01', 'value':'vm-84', 'type':'VirtualMachine'}]
            Ex: [{'name':'SG-WEB-1', 'value':'securitygroup-21', 
                  'type':'SecurityGroup'},
                 {'name':'SG-WEB2', 'value':'securitygroup-22', 
                  'type':'SecurityGroup'}]                             
        """
        # get section to capture etag
        res = self.call('/api/4.0/firewall/globalroot-0/config/layer3sections/%s' % sectionid,
                        'GET', '')     
        
        data = ['<rule id="0" disabled="false" logged="%s">' % logged,
                '<name>%s</name>' % name,
                '<action>%s</action>' % action,
                '<precedence>%s</precedence>' % precedence,
                '<direction>%s</direction>' % direction,
                '<sectionId>%s</sectionId>' % sectionid,
                '<notes></notes>',
                '<packetType>any</packetType>']
        
        data.extend(self._append_rule_definition('sources', 'source', sources))
        data.extend(self._append_rule_definition('destinations', 'destination', destinations))
        data.extend(self._append_rule_service(services))
        data.extend(self._append_rule_definition('appliedToList', 'appliedTo', appliedto))

        data.append('</rule>')
        
        data = ''.join(data)
        res = self.call('/api/4.0/firewall/globalroot-0/config/layer3sections'\
                        '/%s/rules' % sectionid,
                        'POST', data, headers={'Content-Type':'application/xml',
                                              'If-Match':self.manager.nsx['etag']})
        self.logger.debug('Create dfw rule: %s' % res)
        return res[u'rule']
    
    def update_rule(self, sectionid, ruleid, new_action=None, new_disable=None,
                    new_name=None):
        """
        :param sectionid: section id
        :param ruleid: rule id
        :param new_name: new rule name
        :param new_action: new action value. Ie: allow, deny, reject [optional]
        :param new_disable: 'true' if rule is disabled [optional]
        """
        data = self.call('/api/4.0/firewall/globalroot-0/config/'\
                         'layer3sections/%s/rules/%s' % (sectionid, ruleid),  
                         'GET', '', parse=False)
        
        import xml.etree.ElementTree as etree
        root = etree.fromstring(data)
        
        if new_action is not None:
            action = root.find('action')
            action.text = new_action
        
        if new_disable is not None:
            root.set('disabled', new_disable)
            
        if new_name is not None:
            name = root.find('name')
            name.text = new_name      
        
        data = etree.tostring(root)
        res = self.call('/api/4.0/firewall/globalroot-0/config/'\
                        'layer3sections/%s/rules/%s' % (sectionid, ruleid),  
                        'PUT', data, headers={'Content-Type':'application/xml',
                                              'If-Match':self.manager.nsx['etag']})
        
        return res[u'rule']
    
    def move_rule(self, sectionid, ruleid, ruleafter=None):
        """
        :param sectionid: section id
        :param ruleid: rule id
        :param ruleafter: rule id, put rule after this.  
        """
        data = self.call('/api/4.0/firewall/globalroot-0/config/'\
                         'layer3sections/%s' % (sectionid),  
                         'GET', '', parse=False)
        
        import xml.etree.ElementTree as etree
        root = etree.fromstring(data)
        rule = root.findall("./rule[@id='%s']" % ruleid)
        if len(rule) <= 0:
            raise VsphereError('Rule %s not found' % ruleid)
        
        rule = rule[0]
        root.remove(rule)
        # insert rule on the top
        if ruleafter is None:
            root.insert(0, rule)
            
        # insert rule in the given postion
        rules = root.findall("./rule")
        pos = 0
        for r in rules:
            oid = r.get('id')
            pos += 1
            if oid == ruleafter:
                break
        root.insert(pos, rule)
        
        data = etree.tostring(root)
        res = self.call('/api/4.0/firewall/globalroot-0/config/'\
                        'layer3sections/%s' % (sectionid),  
                        'PUT', data, headers={'Content-Type':'application/xml',
                                              'If-Match':self.manager.nsx['etag']})
        
        return res
    
    def delete_section(self, sectionid):
        """
        :param sectionid: section id
        """
        res = self.call('/api/4.0/firewall/globalroot-0/config/layer3sections'\
                        '/%s' % sectionid,  'DELETE', '', 
                        headers={'Content-Type':'application/xml',
                                 'If-Match':self.manager.nsx['etag']})
        return res
    
    def delete_rule(self, sectionid, ruleid):
        """
        :param sectionid: section id
        :param ruleid: rule id
        """
        data = self.call('/api/4.0/firewall/globalroot-0/config/'\
                         'layer3sections/%s/rules/%s' % (sectionid, ruleid),  
                         'GET', '', parse=False)        
        res = self.call('/api/4.0/firewall/globalroot-0/config/layer3sections'\
                        '/%s/rules/%s' % (sectionid, ruleid),  'DELETE', '', 
                        headers={'Content-Type':'application/xml',
                                 'If-Match':self.manager.nsx['etag']})
        return True    

    #
    # exclusion_list
    #
    def get_exclusion_list(self):
        res = self.call('/api/2.1/app/excludelist',  'GET', '')
        return res['VshieldAppConfiguration']['excludeListConfiguration']
    
    def add_item_to_exclusion_list(self):
        """ TODO: """
        pass
    
    def remove_item_from_exclusion_list(self):
        """ TODO: """
        pass      
        

class VsphereCluster(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
        
        self.host = VsphereHost(self.manager)
        self.resource_pool = VsphereResourcePool(self.manager)
    
    @watch
    def list(self):
        """Get clusters with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']
            
        return: list of vim.Cluster  
        """
        props = ['name', 'parent', 'overallStatus', 'resourcePool', 
                 'host']
        view = self.manager.get_container_view(obj_type=[vim.ClusterComputeResource])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.ClusterComputeResource,
                                               path_set=props,
                                               include_mors=True)
        return data
    
    @watch
    def get(self, morid):
        """Get cluster by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.ClusterComputeResource], 
                                      container=container)
        return obj
    
    #
    # summary
    #

    @watch
    def usage(self):
        """Cpu, memory, storage usage
        """
        pass

    @watch
    def ha_status(self):
        """
        """
        pass

    @watch
    def drs_status(self):
        """
        """
        pass

    @watch
    def related_objects(self):
        """datcenter
        """
        pass

    @watch
    def consumers(self):
        """Resource pools, vApps, Virual machines
        """
        pass

    #
    # monitor
    #

    #
    # manage
    #
    
    #
    # related object
    #
    @watch
    def get_servers(self, morid):
        """
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.ClusterComputeResource], 
                                      container=container)
        
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine],
                                               container=obj)
        vm_data = self.manager.collect_properties(view_ref=view,
                                                  obj_type=vim.VirtualMachine,
                                                  path_set=self.manager.server_props,
                                                  include_mors=True)
        return vm_data    

class VsphereHost(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
    
    @watch
    def list(self, cluster=None):
        """Get hosts with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']
            
        return: list of vim.Cluster  
        """
        props = ['name', 'parent', 'overallStatus']
        view = self.manager.get_container_view(obj_type=[vim.HostSystem])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.HostSystem,
                                               path_set=props,
                                               include_mors=True)
        return data
    
    @watch
    def get(self, morid):
        """Get cluster by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.HostSystem], 
                                      container=container)
        return obj
    
    @watch
    def add(self, network):
        """
        """
        pass
    
    @watch
    def update(self, network):
        """
        """
        pass
    
    @watch
    def remove(self, network):
        """
        """
        pass    
    
    #
    # summary
    #
    @watch
    def detail(self, host):
        """
        """
        data = {'rebootRequired':host.summary.rebootRequired,
                'currentEVCModeKey':host.summary.currentEVCModeKey,
                'maxEVCModeKey':host.summary.maxEVCModeKey,
                'network':{'atBootIpV6Enabled':host.config.network.atBootIpV6Enabled,
                           'ipV6Enabled':host.config.network.ipV6Enabled},
               }
        return data

    @watch
    def hardware(self, host):
        """Manifacturer, model, CPU, Memory, Virtual Flash, Network, Storage
        """
        return host.hardware

    @watch
    def runtime(self, host):
        """
        """
        return {'boot_time':host.runtime.bootTime,
                'maintenance':host.runtime.inMaintenanceMode,
                'power_state':host.runtime.powerState}

    @watch
    def configuration(self, host):
        """Esxi version, ha state, Fault tolerance, EVC mode
        """
        return {}

    @watch
    def usage(self, host):
        """Cpu, memory, storage usage
        """
        return host.summary.quickStats

    @watch
    def related_objects(self, host):
        """
        """
        pass
    
    @watch
    def services(self, host):
        """
        """
        return host.config.service

    #
    # monitor
    #
    @watch
    def issues(self):
        """
        """
        pass

    @watch
    def performance(self):
        """
        """
        pass

    @watch
    def log_browser(self):
        """
        """
        pass
    
    @watch
    def tasks(self):
        """
        """
        pass      
    
    @watch
    def events(self):
        """
        """
        pass      
    
    @watch
    def hardware_status(self):
        """
        """
        pass      
    
    #
    # manage
    #
    @watch
    def connect(self):
        """
        """
        pass

    @watch
    def disconnect(self):
        """
        """
        pass

    @watch
    def enter_maintenance(self):
        """
        """
        pass

    @watch
    def exit_maintenance(self):
        """
        """
        pass

    @watch
    def power_on(self):
        """
        """
        pass

    @watch
    def power_off(self):
        """
        """
        pass

    @watch
    def standby(self):
        """
        """
        pass

    @watch
    def reboot(self):
        """
        """
        pass

    #
    # related object
    #
    @watch
    def get_servers(self, morid):
        """
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.HostSystem], 
                                      container=container)
        
        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine],
                                               container=obj)
        vm_data = self.manager.collect_properties(view_ref=view,
                                                  obj_type=vim.VirtualMachine,
                                                  path_set=self.manager.server_props,
                                                  include_mors=True)
        return vm_data

class VsphereResourcePool(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
    
    @watch
    def list(self, cluster=None):
        """Get resource_polls with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']
            
        return: list of vim.Cluster  
        """
        props = ['name', 'parent', 'overallStatus']
        view = self.manager.get_container_view(obj_type=[vim.ResourcePool])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.ResourcePool,
                                               path_set=props,
                                               include_mors=True)
        return data
    
    @watch
    def get(self, morid):
        """Get resource_poll by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.ResourcePool],
                                      container=container)
        return obj  
    
    @watch
    def create(self, cluster, name, cpu, memory, shares='normal'):
        """Creates a resource pool.
    
        :parma cluster: cluster instance
        :param name: String Name
        :param cpu: cpu limit in MHz
        :param memory: memory limit in MB
        :param shares: high    
                         For CPU: Shares = 2000 * nmumber of virtual CPUs
                         For Memory: Shares = 20 * virtual machine memory size in megabytes
                         For Disk: Shares = 2000
                         For Network: Shares = networkResourcePoolHighShareValue 
                       low    
                         For CPU: Shares = 500 * number of virtual CPUs
                         For Memory: Shares = 5 * virtual machine memory size in megabytes
                         For Disk: Shares = 500
                         For Network: Shares = 0.25 * networkResourcePoolHighShareValue 
                       normal    
                         For CPU: Shares = 1000 * number of virtual CPUs
                         For Memory: Shares = 10 * virtual machine memory size in megabytes
                         For Disk: Shares = 1000
                         For Network: Shares = 0.5 * networkResourcePoolHighShareValue    
                      [default=normal]     
        :raise VsphereError:
        """
        try:
            config = vim.ResourceConfigSpec()
            config.cpuAllocation = vim.ResourceAllocationInfo()
            config.cpuAllocation.expandableReservation = False
            config.cpuAllocation.limit = cpu
            config.cpuAllocation.reservation = cpu
            config.cpuAllocation.shares = vim.SharesInfo()
            config.cpuAllocation.shares.level = shares            
            config.memoryAllocation = vim.ResourceAllocationInfo()
            config.memoryAllocation.expandableReservation = False
            config.memoryAllocation.limit = memory
            config.memoryAllocation.reservation = memory
            config.memoryAllocation.shares = vim.SharesInfo()
            config.memoryAllocation.shares.level = shares
            
            res = cluster.resourcePool.CreateResourcePool(name, config)
            self.logger.debug("Create resource pool %s" % name)
            return res
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)    
    
    @watch
    def update(self, respool, name, cpu, memory, shares='normal'):
        """Creates a resource pool.
    
        :parma cluster: cluster instance
        :param name: String Name
        :param cpu: cpu limit in MHz
        :param memory: memory limit in MB
        :param shares: high    
                         For CPU: Shares = 2000 * nmumber of virtual CPUs
                         For Memory: Shares = 20 * virtual machine memory size in megabytes
                         For Disk: Shares = 2000
                         For Network: Shares = networkResourcePoolHighShareValue 
                       low    
                         For CPU: Shares = 500 * number of virtual CPUs
                         For Memory: Shares = 5 * virtual machine memory size in megabytes
                         For Disk: Shares = 500
                         For Network: Shares = 0.25 * networkResourcePoolHighShareValue 
                       normal    
                         For CPU: Shares = 1000 * number of virtual CPUs
                         For Memory: Shares = 10 * virtual machine memory size in megabytes
                         For Disk: Shares = 1000
                         For Network: Shares = 0.5 * networkResourcePoolHighShareValue    
                      [default=normal]     
        :raise VsphereError:
        """
        try:
            config = vim.ResourceConfigSpec()
            config.cpuAllocation = vim.ResourceAllocationInfo()
            config.cpuAllocation.expandableReservation = False
            config.cpuAllocation.limit = cpu
            config.cpuAllocation.reservation = cpu
            config.cpuAllocation.shares = vim.SharesInfo()
            config.cpuAllocation.shares.level = shares            
            config.memoryAllocation = vim.ResourceAllocationInfo()
            config.memoryAllocation.expandableReservation = False
            config.memoryAllocation.limit = memory
            config.memoryAllocation.reservation = memory
            config.memoryAllocation.shares = vim.SharesInfo()
            config.memoryAllocation.shares.level = shares
            
            res = respool.UpdateConfig(name, config)
            self.logger.debug("Update resource pool %s" % name)
            return res
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg)    
    
    @watch
    def remove(self, respool):
        """Remove a resource pool.
    
        :param morid: 
        """
        task = respool.Destroy_Task()
        return task   
    
    #
    # summary
    #
    @watch
    def detail(self, respool):
        """Get resource pool infos.
        
        shares mean:
        
        high    
          For CPU: Shares = 2000 * nmumber of virtual CPUs
          For Memory: Shares = 20 * virtual machine memory size in megabytes
          For Disk: Shares = 2000
          For Network: Shares = networkResourcePoolHighShareValue 
        low    
          For CPU: Shares = 500 * number of virtual CPUs
          For Memory: Shares = 5 * virtual machine memory size in megabytes
          For Disk: Shares = 500
          For Network: Shares = 0.25 * networkResourcePoolHighShareValue 
        normal    
          For CPU: Shares = 1000 * number of virtual CPUs
          For Memory: Shares = 10 * virtual machine memory size in megabytes
          For Disk: Shares = 1000
          For Network: Shares = 0.5 * networkResourcePoolHighShareValue
          
        :param respool: resource pool instance
        """
        cpu = respool.config.cpuAllocation
        mem = respool.config.memoryAllocation
        data = {'config':{'version':respool.config.changeVersion,
                          'cpu_allocation':{
                            'reservation':cpu.reservation,
                            'expandableReservation':cpu.expandableReservation,
                            'limit':cpu.limit,
                            'shares':{'level':cpu.shares.level,
                                      'shares':cpu.shares.shares}},
                          'memory_allocation':{
                            'reservation':mem.reservation,
                            'expandableReservation':mem.expandableReservation,
                            'limit':mem.limit,
                            'shares':{'level':mem.shares.level,
                                      'shares':mem.shares.shares}}
                         },
                'date':{'modified':respool.config.lastModified}}
        return data

    @watch
    def runtime(self, respool):
        """
        """
        return respool.runtime

    @watch
    def usage(self, respool):
        """Cpu, memory, storage usage
        """
        return respool.summary.quickStats

    #
    # monitor
    #

    #
    # manage
    #
    
    #
    # related object
    #
    
    
    @watch
    def get_servers(self, morid):
        """
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.ResourcePool], 
                                      container=container)

        view = self.manager.get_container_view(obj_type=[vim.VirtualMachine],
                                               container=obj)
        vm_data = self.manager.collect_properties(view_ref=view,
                                                  obj_type=vim.VirtualMachine,
                                                  path_set=self.manager.server_props,
                                                  include_mors=True)
        return vm_data

class VsphereDatastore(VsphereObject):
    """
    """
    def __init__(self, manager):
        VsphereObject.__init__(self, manager)
    
    @watch
    def list(self):
        """Get datastore with some properties:
            ['obj']._moId, ['parent']._moId, ['name'], ['overallStatus']
            
        return: list of vim.Cluster  
        """
        props = ['name', 'parent', 'overallStatus']
        view = self.manager.get_container_view(obj_type=[vim.Datastore])
        data = self.manager.collect_properties(view_ref=view,
                                               obj_type=vim.Datastore,
                                               path_set=props,
                                               include_mors=True)
        return data
    
    @watch
    def get(self, morid):
        """Get datastore by managed object reference id.
        Some important properties: name, parent._moId, _moId
        """
        #container = self.si.content.rootFolder
        container = None
        obj = self.manager.get_object(morid, [vim.Datastore], 
                                      container=container)
        return obj
    
    #
    # summary
    #
    @watch
    def detail(self, datastore):
        """datastore main info
        """
        try:
            ds = datastore
            info = {'name':ds.name,
                    'accessible':ds.summary.accessible,
                    'size':ds.summary.capacity,
                    'url':ds.summary.url,
                    'freespace':ds.summary.freeSpace,
                    'max_file_size':ds.info.maxFileSize,
                    'maintenanceMode':ds.summary.maintenanceMode,
                    'multipleHostAccess':ds.summary.multipleHostAccess,
                    'type':ds.summary.type,
                    'uncommitted':ds.summary.uncommitted}

        except Exception as error:
            self.logger.error(error, exc_info=True)
            info = {}
        
        return info

    @watch
    def usage(self):
        """storage usage
        """
        pass

    #
    # monitor
    #
    @watch
    def issues(self, datastore):
        """
        """
        pass    

    @watch
    def perfomance(self, datastore):
        """
        """
        pass

    @watch
    def tasks(self, datastore):
        """
        """
        pass

    @watch
    def events(self, datastore):
        """
        """
        pass

    #
    # manage
    #
    @watch
    def browse_files(self, datastore, path='/'):
        """
        """
        try:
            res = []
            browser = datastore.browser
            #print browser.supportedType
            
            task = browser.SearchDatastore_Task(datastorePath='[%s] %s' % 
                                                (datastore.name, path))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg, code=0)
        return task
    
    @watch
    def parse_files(self, result):
        """ """
        try:
            res = []
            files = result.file
            for item in files:
                res.append({'type':type(item).__name__,
                            'dynamicType':item.dynamicType,
                            'path':item.path,
                            'fileSize':item.fileSize,
                            'modification':item.modification,
                            'owner':item.owner})
        except Exception as error:
            self.logger.error(error, exc_info=True)
            raise VsphereError(error, code=0)
        return res        
    
    
    @watch
    def mount(self, datastore):
        """
        """
        pass    

    @watch
    def unmount(self, datastore):
        """
        """
        pass

    @watch
    def enter_maintenance(self, datastore):
        """
        """
        pass    

    @watch
    def exit_maintenance(self, datastore):
        """
        """
        pass

    #
    # related object
    #
    @watch
    def get_servers(self, datastore):
        """
        """
        try:
            servers = datastore.vm
            res = []
            for server in servers:
                res.append({'name':server.name,
                            'id':server._moId,
                            'template':server.config.template})
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg, code=0)
        return res
    
    @watch
    def get_hosts(self, datastore):
        """
        """
        try:
            hosts = datastore.host
            res = []
            for host in hosts:
                host = host.key
                res.append({'name':host.name,
                            'id':host._moId})
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=True)
            raise VsphereError(error.msg, code=0)
        return res