"""
Created on May 10, 2013

@author: darkbk
"""
import ujson as json
import hashlib
import logging
from beedrones.cloudstack.api_client import ApiError, ClskError
from .event import Event
from .alert import Alert
from .region import Region
from .zone import Zone
from .pod import Pod
from .cluster import Cluster
from .host import Host
from .storagepool import StoragePool
from .system_virtual_machine import SystemVirtualMachine
from .virtual_router import VirtualRouter
from .virtual_machine import VirtualMachine
from .volume import Volume
from .network import Network
from .template import Template
from .iso import Iso
from .account import Account
from .domain import Domain
from .service_offering import ServiceOffering
from .network_offering import NetworkOffering
from .disk_offering import DiskOffering
from beecell.perf import watch
from beedrones.virt import VirtManager
from pygments.lexers.other import SnobolLexer
import time
from datetime import date

class ClskOrchestrator(object):
    """Cloudstack orchestrator.
    
    :param api_client: ApiClient instance
    :type api_client: :class:`ApiClient`
    :param data: set data for current object. [optional]
    :type data: dict or None
    :param oid: set oid for current object. [optional]
    :type data: str or None
    """    
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, api_client, extend=True, db_manager=None, name='', oid='', active=False):
        """ """
        self._obj_type = 'orchestrator'
        self.active = active
        self.orchestrator_type = 'cloudstack'
        
        self._api_client = api_client
        self._name = name
        self.id = oid
        self._extended = False
        self._hypervisors = None
        self._hypervisor_types = []        
        
        if extend is not None:
            self._extend(db_manager)

    def __str__(self):
        return "<%s id=%s, name=%s active=%s>" % (self._obj_type, 
                                                  self.id, 
                                                  self._name,
                                                  self.active)
        
    def __repr__(self):
        return "<%s id=%s, name=%s active=%s>" % (self._obj_type, 
                                                  self.id, 
                                                  self._name,
                                                  self.active)

    def is_extended(self):
        return self._extended

    def hypervisor(self, hid):
        if self._extended is False:
            raise NotImplementedError()
        
        return self._hypervisors[hid]
    
    @property
    def async(self):
        return self._api_client._gevent_async    
    
    @property
    def hypervisor_types(self):
        return self._hypervisor_types

    def open_db_session(self):
        db_session = self._db_manager()
        return db_session

    def _extend(self, db_manager):
        """Extended function perform advanced operation using cloudstack db and 
        direct connection to hypervisor.
        
        :param db_server: 
        :type db_server: :class:`beecell.db.manager.MysqlManager`
        :param hypervisors: List of dictionary with hypervisor connection params
        :type hypervisors: list
        """
        try:
            self._extended = True
            self._db_manager = db_manager
            self._get_hypervisors()
            
            self.logger.debug("Enable orchestrator extension with db manager %s" % 
                              (db_manager))
        except:
            self.logger.warning("Orchestrator extension can not be enabled.")

    def send_request(self, params):
        """Send api client if orchestrator is active.
        
        :param dict params: Request params
        :return: Api response
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        if self.active:
            response = self._api_client.send_api_request(params)
            return response
        else:
            err = 'Orchestrator %s is not active' % self.id
            self.logger.error(err)
            raise ClskError(err)

    def query_async_job(self, clsk_job_id):
        """Query cloudstack async job.
        
        :param clsk_job_id: Cloudstack job id
        :return: Api job response
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`         
        """
        try:
            return self._api_client.query_async_job(clsk_job_id)
        except ApiError as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def ping(self):
        """Ping orchestrator.
        
        :return: True if ping ok
        :rtype: bool    
        """
        try:
            self._api_client.send_api_request({'command':'listCapabilities'})
            self.logger.debug('Ping cloudstack instance %s: OK' % (self.id))
            return True
        except:
            self.logger.error('Ping cloudstack instance %s: KO' % (self.id))
            return False

    @watch
    def info(self):
        """Get system capabilities.
        
        :return: Dictionary with system capabilities.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listCapabilities'}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listcapabilitiesresponse']['capability']
            res['name'] = self._name
            res['id'] = self.id
            res['extended'] = self._extended
            self.logger.debug('Get cloudstack %s capabilities: %s' % (self.id, res))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return res

    @watch
    def _get_hypervisors(self):
        """Get orchestrator hypervisors.
        
        :return: Dictionary with system capabilities.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        self._hypervisors = {}
        params = {'command':'listHosts',
                  'listAll':'true',
                  'resourcestate':'Enabled',
                  'type': 'Routing'}                     

        try:
            response = self.send_request(params)
            res = json.loads(response)['listhostsresponse']['host']
            for item in res:
                htype = item['hypervisor']
                if htype not in self._hypervisor_types:
                    self._hypervisor_types.append(htype)                
                # kvm
                if htype == 'KVM':
                    hid = item['name']
                    host = item['ipaddress']
                    port = '16509'
                    user = ''
                    pwd = ''
                    self._hypervisors[hid] = VirtManager(hid, host, port, 
                                                         user=user, pwd=pwd, 
                                                         async=self.async)
                    self.logger.debug('Get %s hypervisor: %s, %s, %s' % (
                                      htype, hid, host, port))
                # XenServer,VMware,Hyperv,BareMetal,Simulator

        except KeyError as ex:
            self.logger.error(ex)
            raise ClskError('Error parsing json data: %s' % ex)
        except (ApiError, Exception) as ex:
            self.logger.error(ex)
            raise ClskError(ex)

    @watch
    def list_deployment_planners(self):
        """Lists all DeploymentPlanners available.
        
        Example: FirstFitPlanner, UserDispersingPlanner, UserConcentratedPodPlanner,
                 ImplicitDedicationPlanner, BareMetalPlanner, SkipHeuresticsPlanner
        
        :return: Dictionary with DeploymentPlanners available.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listDeploymentPlanners'}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listdeploymentplannersresponse']['deploymentPlanner']
            self.logger.debug('Get cloudstack %s capabilities: %s...' % (self.id, str(res)[0:200]))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return res

    @watch
    def list_configurations(self, accountid=None, category=None, clusterid=None, 
                                  name=None, page=None, pagesize=None, 
                                  storageid=None, zoneid=None):
        """Lists configurations.
        
        :param accountid: the ID of the Account to update the parameter value for corresponding account
        :param category: lists configurations by category. Value like:
                         Advanced, Alert, Console Proxy, ...
        :param clusterid: the ID of the Cluster to update the parameter value for corresponding cluster
        :param name: lists configuration by name
        :param page: 
        :param pagesize: 
        :param storageid: the ID of the Storage pool to update the parameter value for corresponding storage pool
        :param zoneid: the ID of the Zone to update the parameter value for corresponding zone
        
        :return: Dictionary with following key:
                id: the value of the configuration,
                category: the category of the configuration
                description: the description of the configuration
                name: the name of the configuration
                scope: scope(zone/cluster/pool/account) of the parameter that needs to be updated
                value: the value of the configuration        
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listConfigurations'}
        
        if accountid is not None:
            params['accountid'] = accountid
        if category is not None:
            params['category'] = category
        if clusterid is not None:
            params['clusterid'] = clusterid
        if name is not None:
            params['name'] = name
        if page is not None:
            params['page'] = page
        if pagesize is not None:
            params['pagesize'] = pagesize
        if storageid is not None:
            params['storageid'] = storageid
        if zoneid is not None:
            params['zoneid'] = zoneid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listconfigurationsresponse']['configuration']
            self.logger.debug('Get cloudstack %s configurations: %s...' % (self.id, str(res)[0:200]))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return res

    @watch
    def update_configuration(self, name, value):
        """Update system configuration.
        
        :param name: the name of the configuration
        :param value: the value of the configuration
        :return: Dictionary with following key:
                id: the value of the configuration,
                category: the category of the configuration
                descriptVirtualMachineion: the description of the configuration
                name: the name of the configuration
                scope: scope(zone/cluster/pool/account) of the parameter that needs to be updated
                value: the value of the configuration        
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'updateConfiguration',
                  'name':name,
                  'value':value}

        try:
            response = self.send_request(params)
            res = json.loads(response)['updateconfigurationresponse']['configuration']
            data = res
            self.logger.debug('Set cloudstack %s configurations: %s' % (self.id, data))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data

    @watch
    def list_ldap_configurations(self):
        """Lists all LDAP configurations.
        
        :return: Dictionary with LDAP configurations.
        :rtype: dict        
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listLdapConfigurations'}

        try:
            response = self.send_request(params)
            res = json.loads(response)['ldapconfigurationresponse']
            if len(res) > 0:
                data = res['ldapconfiguration']
            else:
                data = []
            data = res
            self.logger.debug('Get cloudstack %s LDAP configurations: %s...' % (self.id, str(data)[0:200]))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data
    
    # tags
    @watch    
    def list_tags(self, account=None, customer=None, domainid=None, 
                        isrecursive=None, key=None, keyword=None, 
                        page=None, pagesize=None, resourceid=None,
                        resourcetype=None, value=None):
        """List resource tag(s)
        
        :param account: list resources by account. Must be used with the 
                        domainId parameter.
        :param customer: list by customer name
        :param domainid: list only resources belonging to the domain specified
        :param isrecursive: defaults to false, but if true, lists all resources 
                            from the parent specified by the domainId till leaves.
        :param key: list by key
        :param keyword: List by keyword
        :param page: 
        :param pagesize: 
        :param resourceid: list by resource id
        :param resourcetype: list by resource type
        :param value: list by value
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
                  'listall':True}
        
        if account is not None:
            params['account'] = account
        if customer is not None:
            params['customer'] = customer
        if domainid is not None:
            params['domainid'] = domainid
        if isrecursive is not None:
            params['isrecursive'] = isrecursive
        if key is not None:
            params['key'] = key
        if keyword is not None:
            params['keyword'] = keyword
        if page is not None:
            params['page'] = page
        if pagesize is not None:
            params['pagesize'] = pagesize
        if resourceid is not None:
            params['resourceid'] = resourceid
        if resourcetype is not None:
            params['resourcetype'] = resourcetype
        if value is not None:
            params['value'] = value

        try:
            response = self.send_request(params)
            res = json.loads(response)['listtagsresponse']
            if len(res) > 0:
                data = res['tag']
                self.logger.debug('Get cloudstack %s configurations: %s...' % (self.id, str(data)[0:200]))
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data
    
    # events
    @watch    
    def list_event_types(self):
        """List Event Types"""
        params = {'command':'listEventTypes'}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listeventtypesresponse']['eventtype']
            data = res
            self.logger.debug('List cloudstack %s event types: %s...' % (self.id, str(data)[0:200]))
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data

    @watch
    def list_events(self, domainid=None, account=None, duration=None,
                    enddate=None, startdate=None, entrytime=None, level=None,
                    page=None, pagesize=None, etype=None, oid=None):
        """List events.
        
        :param domainid: [optional] id of the domain
        :param account: [optional] name of the account. Require domainid
        :param duration: [optional] the duration of the event
        :param enddate: [optional] the end date range of the list you want to 
                        retrieve (use format "yyyy-MM-dd" or the new format 
                        "yyyy-MM-dd HH:mm:ss")
        :param startdate: [optional] the start date range of the list you want 
                          to retrieve (use format "yyyy-MM-dd" or the new format 
                          "yyyy-MM-dd HH:mm:ss")
        :param entrytime: [optional] the time the event was entered
        :param level: [optional] the event level (INFO, WARN, ERROR)
        :param page: [optional]
        :param pagesize: [optional]
        :param etype: [optional] the event type (see event types)
        :param oid: event id

        :return: list of :class:`Event`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`    
        """
        params = {'command':'listEvents',
                  'listall':'true'}

        if domainid is not None:
            params['domainid'] = domainid
        if account is not None:
            params['account'] = account
        if duration is not None:
            params['duration'] = duration
        if enddate is not None:
            params['enddate'] = enddate
        if startdate is not None:
            params['startdate'] = startdate
        if entrytime is not None:
            params['entrytime'] = entrytime
        if level is not None:
            params['level'] = level
        if page is not None:
            params['page'] = page
        if pagesize is not None:
            params['pagesize'] = pagesize
        if etype is not None:
            params['type'] = etype
        if oid is not None:
            params['id'] = oid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listeventsresponse']
            if len(res) > 0:
                data = res['event']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        events = []
        for item in data:
            # create Network instance
            event = Event(self, item)
            events.append(event)
        
        self.logger.debug('List cloudstack %s events: %s...' % (
                  self.id, str(events)[0:200])) 
        
        return events     

    @watch
    def archive_events(self, ids=None, etype=None, enddate=None, startdate=None):
        """Archive events.
        
        :param enddate: [optional] the end date range of the list you want to 
                        retrieve (use format "yyyy-MM-dd" or the new format 
                        "yyyy-MM-dd HH:mm:ss")
        :param startdate: [optional] the start date range of the list you want 
                          to retrieve (use format "yyyy-MM-dd" or the new format 
                          "yyyy-MM-dd HH:mm:ss")
        :param ids: [optional] the IDs of the events
        :param etype: [optional] the event type (see event types)

        :return: archive response
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError` 
        """
        params = {'command':'archiveEvents'}

        if enddate is not None:
            params['enddate'] = enddate
        if startdate is not None:
            params['startdate'] = startdate
        if ids is not None:
            params['ids'] = ids
        if etype is not None:
            params['type'] = etype

        try:
            response = self.send_request(params)
            res = json.loads(response)['archiveeventsresponse']['success']
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        if res:
            self.logger.debug('Archive cloudstack %s events' % (self.id)) 
            return res
        else:
            self.logger.debug('Archive cloudstack %s events error: %s' % (self.id)) 
            raise ClskError('Archive cloudstack %s events error: %s' % (self.id))

    @watch
    def delete_events(self, ids=None, etype=None, enddate=None, startdate=None):
        """Delete events.
        
        :param enddate: [optional] the end date range of the list you want to 
                        retrieve (use format "yyyy-MM-dd" or the new format 
                        "yyyy-MM-dd HH:mm:ss")
        :param startdate: [optional] the start date range of the list you want 
                          to retrieve (use format "yyyy-MM-dd" or the new format 
                          "yyyy-MM-dd HH:mm:ss")
        :param ids: [optional] the IDs of the events
        :param etype: [optional] the event type (see event types)
        :return: delete response
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError`   
        """
        params = {'command':'deleteEvents'}

        if enddate is not None:
            params['enddate'] = enddate
        if startdate is not None:
            params['startdate'] = startdate
        if ids is not None:
            params['ids'] = ids
        if etype is not None:
            params['type'] = etype

        try:
            response = self.send_request(params)
            res = json.loads(response)['deleteeventsresponse']['success']
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        if res:
            self.logger.debug('Delete cloudstack %s events' % (self.id)) 
            return res
        else:
            self.logger.debug('Delete cloudstack %s events error: %s' % (self.id)) 
            raise ClskError('Delete cloudstack %s events error: %s' % (self.id))

    @watch
    def list_alerts(self, name=None, page=None, pagesize=None, atype=None, oid=None):
        """List alerts.
        
        :param name: [optional] alert name. If type is not custom use:
        
                     type    name
                     -------------------------------------------
                     5       ALERT.NETWORK.PRIVATEIP
                     9       ALERT.SERVICE.DOMAINROUTER
        :param page: [optional]
        :param pagesize: [optional]
        :param atype: [optional] Custom type or one of the following alert types: 
                      MEMORY = 0, 
                      CPU = 1, 
                      STORAGE = 2, 
                      STORAGE_ALLOCATED = 3, 
                      PUBLIC_IP = 4, 
                      PRIVATE_IP = 5, 
                      HOST = 6, 
                      USERVM = 7, 
                      DOMAIN_ROUTER = 8, 
                      CONSOLE_PROXY = 9, 
                      ROUTING = 10: lost connection to default route (to the gateway), 
                      STORAGE_MISC = 11: lost connection to default route (to the gateway), 
                      USAGE_SERVER = 12: lost connection to default route (to the gateway), 
                      MANAGMENT_NODE = 13: lost connection to default route (to the gateway), 
                      DOMAIN_ROUTER_MIGRATE = 14, 
                      CONSOLE_PROXY_MIGRATE = 15, 
                      USERVM_MIGRATE = 16, 
                      VLAN = 17, 
                      SSVM = 18, 
                      USAGE_SERVER_RESULT = 19
        :param oid: alert id
        :return: list of :class:`Alert`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`    
        """
        params = {'command':'listAlerts'}

        if name is not None:
            params['name'] = name
        if page is not None:
            params['page'] = page
        if pagesize is not None:
            params['pagesize'] = pagesize
        if atype is not None:
            params['type'] = atype
        if oid is not None:
            params['id'] = oid            

        try:
            response = self.send_request(params)
            res = json.loads(response)['listalertsresponse']
            if len(res) > 0:
                data = res['alert']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        alerts = []
        for item in data:
            # create Network instance
            alert = Alert(self, item)
            alerts.append(alert)
        
        self.logger.debug('List cloudstack %s alerts: %s...' % (
                  self.id, str(alerts)[0:200])) 
        
        return alerts

    @watch
    def archive_alerts(self, ids=None, atype=None, enddate=None, startdate=None):
        """Archive events.
        
        :param enddate: [optional] the end date range of the list you want to 
                        retrieve (use format "yyyy-MM-dd" or the new format 
                        "yyyy-MM-dd HH:mm:ss")
        :param startdate: [optional] the start date range of the list you want 
                          to retrieve (use format "yyyy-MM-dd" or the new format 
                          "yyyy-MM-dd HH:mm:ss")
        :param ids: [optional] the IDs of the events
        :param atype: [optional] Custom type or one of the following alert types: 
                      MEMORY = 0, 
                      CPU = 1, 
                      STORAGE = 2, 
                      STORAGE_ALLOCATED = 3, 
                      PUBLIC_IP = 4, 
                      PRIVATE_IP = 5, 
                      HOST = 6, 
                      USERVM = 7, 
                      DOMAIN_ROUTER = 8, 
                      CONSOLE_PROXY = 9, 
                      ROUTING = 10: lost connection to default route (to the gateway), 
                      STORAGE_MISC = 11: lost connection to default route (to the gateway), 
                      USAGE_SERVER = 12: lost connection to default route (to the gateway), 
                      MANAGMENT_NODE = 13: lost connection to default route (to the gateway), 
                      DOMAIN_ROUTER_MIGRATE = 14, 
                      CONSOLE_PROXY_MIGRATE = 15, 
                      USERVM_MIGRATE = 16, 
                      VLAN = 17, 
                      SSVM = 18, 
                      USAGE_SERVER_RESULT = 19

        :return: archive response
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError` 
        """
        params = {'command':'archiveAlerts'}

        if enddate is not None:
            params['enddate'] = enddate
        if startdate is not None:
            params['startdate'] = startdate
        if ids is not None:
            params['ids'] = ids
        if atype is not None:
            params['type'] = atype

        try:
            response = self.send_request(params)
            res = json.loads(response)['archivealertsresponse']['success']
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        if res:
            self.logger.debug('Archive cloudstack %s alerts' % (self.id)) 
            return res
        else:
            self.logger.debug('Archive cloudstack %s alerts error: %s' % (self.id)) 
            raise ClskError('Archive cloudstack %s alerts error: %s' % (self.id))

    @watch
    def delete_alerts(self, ids=None, atype=None, enddate=None, startdate=None):
        """Delete alerts.
        
        :param enddate: [optional] the end date range of the list you want to 
                        retrieve (use format "yyyy-MM-dd" or the new format 
                        "yyyy-MM-dd HH:mm:ss")
        :param startdate: [optional] the start date range of the list you want 
                          to retrieve (use format "yyyy-MM-dd" or the new format 
                          "yyyy-MM-dd HH:mm:ss")
        :param ids: [optional] the IDs of the events
        :param atype: [optional] Custom type or one of the following alert types: 
                      MEMORY = 0, 
                      CPU = 1, 
                      STORAGE = 2, 
                      STORAGE_ALLOCATED = 3, 
                      PUBLIC_IP = 4, 
                      PRIVATE_IP = 5, 
                      HOST = 6, 
                      USERVM = 7, 
                      DOMAIN_ROUTER = 8, 
                      CONSOLE_PROXY = 9, 
                      ROUTING = 10: lost connection to default route (to the gateway), 
                      STORAGE_MISC = 11: lost connection to default route (to the gateway), 
                      USAGE_SERVER = 12: lost connection to default route (to the gateway), 
                      MANAGMENT_NODE = 13: lost connection to default route (to the gateway), 
                      DOMAIN_ROUTER_MIGRATE = 14, 
                      CONSOLE_PROXY_MIGRATE = 15, 
                      USERVM_MIGRATE = 16, 
                      VLAN = 17, 
                      SSVM = 18, 
                      USAGE_SERVER_RESULT = 19

        :return: delete response
        :rtype: bool
        :raises ClskError: raise :class:`.base.ClskError` 
        """
        params = {'command':'deleteAlerts'}

        if enddate is not None:
            params['enddate'] = enddate
        if startdate is not None:
            params['startdate'] = startdate
        if ids is not None:
            params['ids'] = ids
        if atype is not None:
            params['type'] = atype

        try:
            response = self.send_request(params)
            res = json.loads(response)['deletealertsresponse']['success']
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        if res:
            self.logger.debug('Delete cloudstack %s alerts' % (self.id)) 
            return res
        else:
            self.logger.debug('Delete cloudstack %s alerts error: %s' % (self.id)) 
            raise ClskError('Delete cloudstack %s alerts error: %s' % (self.id))

    @watch
    def generate_alert(self, description, name, atype, zoneid=None, podid=None):
        """Generate an alert.
        
        *Async command*

        :param description: Alert description
        :param name: Name of the alert
        :param atype: Type of the alert
        :param podid: Pod id for which alert is generated
        :param zoneid: Zone id for which alert is generated
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`                         
        """        
        params = {'command':'generateAlert',
                  'name':name,
                  'description':description,
                  'type':atype}
        
        if podid is not None:
            params['podid'] = podid
        if zoneid is not None:
            params['zoneid'] = zoneid
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['generatealertresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.id, 
                              'generateAlert', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def get_cloud_identifier(self, userid):
        """Get cloud identifier"""
        params = {'command':'getCloudIdentifier',
                  'userid':userid}

        try:
            response = self.send_request(params)
            res = json.loads(response)['getcloudidentifierresponse']['cloudidentifier']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data

    @watch
    def login(self, username, password, domainId=None):
        """Logs a user into the CloudStack. A successful login attempt will 
        generate a JSESSIONID cookie value that can be passed in subsequent 
        Query command calls until the "logout" command has been issued or the 
        session has expired.
        
        :param username: Username
        :param password: Hashed password (Default is MD5). If you wish to use 
                         any other hashing algorithm, you would need to write 
                         a custom authentication adapter See Docs section.
        :param domainId: id of the domain that the user belongs to. If both 
                         domain and domainId are passed in, "domainId" parameter 
                         takes precendence [optional]
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        """
        md5_password = hashlib.md5(password).hexdigest()
        md5_password = password

        params = {'command':'login',
                  'username':username,
                  'password':md5_password}
        
        if domainId is not None:
            params['domainId'] = domainId

        try:
            response = self.send_request(params)
            res = json.loads(response)['loginresponse']
            self.logger.debug('Login user %s: %s' % (username, res))
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data

    @watch
    def logout(self):
        """Logs out the user.
        
        :param username: Username
        :param password: Hashed password (Default is MD5). If you wish to use 
                         any other hashing algorithm, you would need to write 
                         a custom authentication adapter See Docs section.
        :param domainId: id of the domain that the user belongs to. If both 
                         domain and domainId are passed in, "domainId" parameter 
                         takes precendence [optional]
        :return: Dictionary with all network configuration attributes.
        :rtype: dict
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'logout'}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['logoutresponse']
            self.logger.debug('Logout user')
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        return data

    @watch
    def list_regions(self):
        """List all cloudstack regions.
        """
        params = {'command':'listRegions',
                  'listAll':'true'}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listregionsresponse']['region']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        regions = []
        for item in data:
            # create Account instance
            region = Region(self, item)
            regions.append(region)   
        return regions

    @watch
    def list_zones(self, oid=None, name=None):
        """List all cloudstack zones.
        
        :param oid: zone id [optional]
        :param name: zone name [optional]
        """
        params = {'command':'listZones',
                  'listAll':'true'}
        
        if oid is not None:
            params['id'] = oid
        if name is not None:
            params['name'] = name            

        try:
            response = self.send_request(params)
            res = json.loads(response)['listzonesresponse']['zone']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        zones = []
        for item in data:
            # create Account instance
            zone = Zone(self, item)
            zones.append(zone)
            
        self.logger.debug('List cloudstack %s zones: %s...' % (self.id, str(zones)[0:200]))
        return zones      

    @watch
    def list_pods(self):
        """List all cloudstack pods.
        """
        params = {'command':'listPods',
                  'listAll':'true'}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listpodsresponse']['pod']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        pods = []
        for item in data:
            # create Account instance
            pod = Pod(self, item)
            pods.append(pod)
            
        self.logger.debug('List cloudstack %s pods: %s...' % (self.id, str(pods)[0:200]))
        return pods  

    @watch
    def list_clusters(self):
        """List all cloudstack clusters.
        """
        params = {'command':'listClusters',
                  'listAll':'true'}
        
        response = self.send_request(params)

        try:
            response = self.send_request(params)
            res = json.loads(response)['listclustersresponse']['cluster']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        clusters = []
        for item in data:
            # create Account instance
            cluster = Cluster(self, item)
            clusters.append(cluster)
        return clusters       

    @watch
    def list_hosts(self, oid=None, name=None, zoneid=None, podid=None, 
                         clusterid=None, resourcestate='Enabled',
                         virtualmachineid=None, htype=None):
        """List all hosts
        
        :param oid: id of the host
        :param name: name of the host
        :param zoneid: zone id of the host
        :param podid: pod id of the host
        :param clusterid: cluster id of the host
        :param resourcestate: list hosts by resource state. Resource state 
                              represents current state determined by admin of 
                              host, valule can be one of [Enabled, Disabled, 
                              Unmanaged, PrepareForMaintenance, ErrorInMaintenance, 
                              Maintenance, Error]
        :param virtualmachineid: lists hosts in the same cluster as this instance and 
                                 flag hosts with enough CPU/RAm to host this instance
        :param htype: tpe of host
        """
        params = {'command':'listHosts',
                  'listAll':'true'}

        if oid is not None:
            params['id'] = oid
        if name is not None:
            params['name'] = name
        if zoneid is not None:
            params['zoneid'] = zoneid
        if podid is not None:
            params['podid'] = podid
        if clusterid is not None:
            params['clusterid'] = clusterid            
        if resourcestate is not None:
            params['resourcestate'] = resourcestate
        if virtualmachineid is not None:
            params['virtualmachineid'] = virtualmachineid
        if htype is not None:
            params['type'] = htype                        

        try:
            response = self.send_request(params)
            res = json.loads(response)['listhostsresponse']['host']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        hosts = []
        for item in data:
            # create Account instance
            host = Host(self._api_client, data=item)
            hosts.append(host)
        return hosts 

    @watch
    def list_storagepools(self, zoneid=None, name=None):
        """List all cloudstack storage pools.
        """
        params = {'command':'listStoragePools'}
        
        if zoneid is not None:
            params['zoneid'] = zoneid
        if name is not None:
            params['name'] = name            
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['liststoragepoolsresponse']['storagepool']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        storagepools = []
        for item in data:
            # create StoragePool instance
            storagepool = StoragePool(self, item)
            storagepools.append(storagepool)
        return storagepools

    @watch
    def list_imagestores(self):
        """List all image stores"""
        params = {'command':'listImageStores',
                  'listAll':'true'}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listimagestoresresponse']['imagestore']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        return data
        
        """
        hosts = []
        for item in data:
            # create Account instance
            host = Host(self._api_client, item)
            hosts.append(host)
        return hosts
        """
      
    @watch
    def list_system_instances(self, oid=None):
        """List all system instances"""
        params = {'command':'listSystemVms',
                  'listAll':'true'}

        if oid is not None:
            params['id'] = oid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listsystemvmsresponse']['systemvm']
            data = res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        instances = []
        for item in data:
            # create Account instance
            instance = SystemVirtualMachine(self, item)
            instances.append(instance)
            
        self.logger.debug('List system instance: %s...' % str(instances)[0:200])
        return instances

    @watch
    def list_routers(self, oid=None):
        """List all routers"""
        params = {'command':'listRouters',
                  'listAll':'true'}

        if oid is not None:
            params['id'] = oid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listroutersresponse']
            if len(res) > 0:
                data = res['router']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        instances = []
        for item in data:
            # create Account instance
            instance = VirtualRouter(self, item)
            instances.append(instance)
            
        self.logger.debug('List virtual router: %s...' % str(instances)[0:200])
        return instances

    @watch
    def list_virtual_machines(self, zone_id=None, domain=None, domain_id=None,
                                    account=None, instance_id=None, name=None):
        """List virtual machines.
        
        :param zone_id: [optional] id of the zone
        :param domain_id: [optional] id of the domain
        :param domain: [optional] name of the domain
        :param account: [optional] name of the account
        :param vole_id: [optional] id of the virtual machine
        :param name: [optional] virtual machine name        
        """
        params = {'command':'listVirtualMachines',
                  'listall':'true',
                  'isrecursive':'true'}

        if zone_id is not None:
            params['zoneid'] = zone_id  
        if domain is not None:
            params['domainid'] = self.get_domain_id(domain)
        if domain_id is not None:
            params['domainid'] = domain_id
        if account is not None:
            params['account'] = account
        if instance_id is not None:
            params['id'] = instance_id
        if name is not None:
            params['name'] = name
        
        try:
            response = self.send_request(params)
            
            res = json.loads(response)['listvirtualmachinesresponse']
            if len(res) > 0:
                data = res['virtualmachine']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        instances = []
        for item in data:
            # create Account instance
            instance = VirtualMachine(self, item)
            instances.append(instance)
            
        self.logger.debug('List virtual machine: %s...' % str(instances)[0:200])
        return instances

    @watch
    def list_volumes(self, zone_id=None, domain=None, domain_id=None,
                           account=None, vol_id=None, name=None):
        """List volumes.

        :param zone_id: [optional] id of the zone
        :param domain_id: [optional] id of the domain
        :param domain: [optional] name of the domain
        :param account: [optional] name of the account
        :param vole_id: [optional] id of the volume
        :param name: [optional] volume name
        """
        params = {'command':'listVolumes',
                  'listall':'true'}

        if zone_id is not None:
            params['zoneid'] = zone_id  
        if domain is not None:
            params['domainid'] = self.get_domain_id(domain)
        if domain_id is not None:
            params['domainid'] = domain_id
        if account is not None:
            params['account'] = account
        if vol_id is not None:
            params['id'] = vol_id
        if name is not None:
            params['name'] = name            

        try:
            response = self.send_request(params)
            res = json.loads(response)['listvolumesresponse']
            if len(res) > 0:
                data = res['volume']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

        volumes = []
        for item in data:
            # create Volume instance
            volume = Volume(self, item)
            volumes.append(volume)
        
        self.logger.debug('List cloudstack %s volumes: %s...' % (self.id, str(volumes)[0:200])) 
        
        return volumes 

    @watch
    def list_networks(self, zone_id=None, domain=None, domain_id=None, 
                        account=None, net_id=None, name=None):
        """List software defined network.
        
        :param zone_id: [optional] id of the zone
        :param domain_id: [optional] id of the domain
        :param domain: [optional] name of the domain
        :param account: [optional] name of the account
        :param net_id: [optional] id of the network
        :param name: [optional] network name   

        :return: list of :class:`Network`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`    
        """
        params = {'command':'listNetworks',
                  'listall':'true'}

        if zone_id is not None:
            params['zoneid'] = zone_id  
        if domain is not None:
            params['domainid'] = self.get_domain_id(domain)
        if domain_id is not None:
            params['domainid'] = domain_id
        if account is not None:
            params['account'] = account
        if net_id is not None:
            params['id'] = net_id
        if name is not None:
            params['name'] = name            

        try:
            response = self.send_request(params)
            res = json.loads(response)['listnetworksresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        networks = []
        for item in data:
            # create Network instance
            network = Network(self, item)
            networks.append(network)
        
        self.logger.debug('List cloudstack %s networks: %s...' % (self.id, str(networks)[0:200])) 
        
        return networks 

    @watch
    def list_physical_networks(self, pnid=None, name=None, zone_id=None, ):
        """List physical networks.
        
        :param pnid: [optional] physical network id
        :param name: [optional] physical network name
        :param zone_id: [optional] id of the zone
        
        Return:
        
        [{u'name': u'cloudbr0', 
          u'broadcastdomainrange': u'ZONE', 
          u'state': u'Enabled', 
          u'zoneid': u'2af97976-9679-427b-8dbd-6b11f9dfa169', 
          u'isolationmethods': u'VLAN', 
          u'id': u'5b72e792-bb66-4fad-9e16-8f4f7c290a07'}, 
         {u'name': u'cloudbr1', 
          u'broadcastdomainrange': u'ZONE', 
          u'vlan': u'1200-1204', 
          u'isolationmethods': u'VLAN', 
          u'zoneid': u'2af97976-9679-427b-8dbd-6b11f9dfa169', 
          u'state': u'Enabled', 
          u'id': u'c0bdc2a5-a222-49cf-a11a-98ff886ee210'}]        
        """
        params = {'command':'listPhysicalNetworks',
                  'listall':'true'}

        if pnid is not None:
            params['id'] = pnid  
        if name is not None:
            params['name'] = name  
        if zone_id is not None:
            params['zoneid'] = zone_id

        try:
            response = self.send_request(params)
            res = json.loads(response)['listphysicalnetworksresponse']
            if len(res) > 0:
                data = res['physicalnetwork']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        return data

    @watch
    def list_remote_access_vpns(self, networkid=None, publicipid=None,
                                       domainid=None, account=None):
        """List remote access vpn.
        
        :param networkid: [optional] list remote access VPNs for ceratin network
        :param publicipid: [optional] public ip address id of the vpn server
        :param domainid: [optional] list only resources belonging to the domain specified
        :param account: [optional]list resources by account. Must be used with the domainId parameter.
        
        :return:    [{u'presharedkey': u'9O89veQ8s9mHpna6ZjrmzcYn', 
                      u'account': u'admin', 
                      u'domainid': u'ae3fad3c-d518-11e3-8225-0050560203f1', 
                      u'publicipid': u'fc9fc2ce-98df-48d5-99c8-7d960a843f07', 
                      u'id': u'2761b5a3-9949-4714-8610-656f5e978510', 
                      u'publicip': u'10.102.43.124', 
                      u'state': u'Running', 
                      u'domain': u'ROOT', 
                      u'iprange': u'10.1.2.2-10.1.2.8'}]
        """
        params = {'command':'listRemoteAccessVpns',
                  'listall':'true'}

        if domainid is not None:
            params['domainid'] = domainid
        if account is not None:
            params['account'] = account
        if networkid is not None:
            params['networkid'] = networkid
        if publicipid is not None:
            params['publicipid'] = publicipid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listremoteaccessvpnsresponse']
            if len(res) > 0:
                data = res['remoteaccessvpn']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        return data

    @watch
    def list_public_ip_addresses(self, ipaddressid=None, ipaddress=None, zone_id=None, 
                                       domainid=None, account=None):
        """List public Ip Addresses.
        
        :param ipaddressid: [optional] Ip Address id
        :param ipaddress: [optional] lists the specified IP address
        :param zone_id: [optional] id of the zone
        :param domainid: [optional] list only resources belonging to the domain specified
        :param account: [optional]list resources by account. Must be used with the domainId parameter.
        
        :return:[{u'networkid': u'48e77c5a-c8d6-4c8a-a5e4-675b0f555507', 
                  u'physicalnetworkid': u'c0bdc2a5-a222-49cf-a11a-98ff886ee210', 
                  u'account': u'oasis', 
                  u'domainid': u'92e75598-4604-43d3-a8ad-b3a96bfabcb1', 
                  u'isportable': False, u'issourcenat': True, 
                  u'associatednetworkname': u'oasis-network01', 
                  u'tags': [], 
                  u'isstaticnat': False, 
                  u'domain': u'PRG-EUROPEI', 
                  u'vlanid': u'1ed1b9e8-bfac-4cf2-be93-052fe0b182ea', 
                  u'zoneid': u'2af97976-9679-427b-8dbd-6b11f9dfa169', 
                  u'vlanname': u'vlan://28', 
                  u'state': u'Allocated', 
                  u'associatednetworkid': u'48a74a6f-c839-4ffc-9fa6-d5f9d453cd56', 
                  u'forvirtualnetwork': True, 
                  u'allocated': u'2014-05-07T11:16:25+0200', 
                  u'issystem': False, 
                  u'ipaddress': u'10.102.43.125', 
                  u'id': u'c08a5410-1bf3-4250-b1ed-41a0354c9821', 
                  u'zonename': u'zona_kvm_01'}, ...]
        """
        params = {'command':'listPublicIpAddresses',
                  'listall':'true',
                  'allocatedonly':'true'}

        if zone_id is not None:
            params['zoneid'] = zone_id
        if domainid is not None:
            params['domainid'] = domainid
        if account is not None:
            params['account'] = account
        if ipaddressid is not None:
            params['ipid'] = ipaddressid
        if ipaddress is not None:
            params['ipaddress'] = ipaddress

        try:
            response = self.send_request(params)
            res = json.loads(response)['listpublicipaddressesresponse']
            if len(res) > 0:
                data = res['publicipaddress']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        return data

    @watch
    def list_os_categories(self):
        """Lists all supported OS categories for this cloud.
        
        :return: list of os categories
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listOsCategories'}

        try:
            response = self.send_request(params)
            res = json.loads(response)['listoscategoriesresponse']
            if len(res) > 0:
                data = res['oscategory']
            else:
                data = []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        self.logger.debug('List cloudstack %s os categories: %s...' % (self.id, str(data)[0:200]))          
        
        return data

    @watch
    def list_os_types(self, oscategoryid=None):
        """Lists all supported OS types for this cloud.
        
        :param oscategoryid: list by Os Category id [optional]
        :return: list of os type
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listOsTypes'}
        
        if oscategoryid is not None:
            params['oscategoryid'] = oscategoryid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listostypesresponse']
            if len(res) > 0:
                data = res['ostype']
            else:
                data = []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        self.logger.debug('List cloudstack %s os types' % (self.id))
        
        return data

    @watch
    def list_templates(self, zoneid=None, hypervisor=None, oid=None, name=None):
        """List system templates.
        
        :param str oid: id [optional]
        :param str name: domain name [optional]        
        :param str zoneid: zone id [optional]
        :param str hypervisor: hypervisor. Es. KVM [optional]
        :return: list of :class:`Template`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listTemplates',
                  'listall':'true',
                  'templatefilter':'all'}
        
        if zoneid is not None:
            params['zoneid'] = zoneid
        if hypervisor is not None:
            params['hypervisor'] = hypervisor
        if oid is not None:
            params['id'] = oid
        if name is not None:
            params['name'] = name            

        try:
            response = self.send_request(params)
            res = json.loads(response)['listtemplatesresponse']
            if len(res) > 0:
                data = res['template']
            else:
                data = []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        templates = []
        for item in data:
            # create Template instance
            template = Template(self, item)
            templates.append(template)
        
        self.logger.debug('List cloudstack %s templates: %s...' % (self.id, str(templates)[0:200]))          
        
        return templates

    @watch
    def list_isos(self, zoneid=None, hypervisor=None, oid=None, name=None):
        """List system isos.
        
        :param str oid: id [optional]
        :param str name: domain name [optional]        
        :param str zoneid: zone id [optional]
        :param str hypervisor: hypervisor. Es. KVM [optional]
        :return: list of :class:`Iso`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`
        """
        params = {'command':'listIsos',
                  'listall':'true',
                  'isofilter':'all'}
        
        if zoneid is not None:
            params['zoneid'] = zoneid
        if hypervisor is not None:
            params['hypervisor'] = hypervisor
        if oid is not None:
            params['id'] = oid
        if name is not None:
            params['name'] = name            

        try:
            response = self.send_request(params)
            res = json.loads(response)['listisosresponse']
            if len(res) > 0:
                data = res['iso']
            else:
                data = []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        isos = []
        for item in data:
            # create Iso instance
            iso = Iso(self, item)
            isos.append(iso)
        
        self.logger.debug('List cloudstack %s isos: %s...' % (self.id, str(isos)[0:200]))            
        
        return isos

    @watch
    def list_domains(self, domain_id=None, name=None, level=None):
        """List domains.
        
        :param str domain_id: domain id [optional]
        :param str name: domain name [optional]
        :param int level: List domains by domain level [optional]
        :return: list of :class:`Domain`
        :rtype: list
        :raises ClskError: raise :class:`.base.ClskError`        
        """

        params = {'command':'listDomains',
                  'listall':'true',}
        
        if domain_id is not None:
            params['id'] = domain_id
        if name is not None:
            params['name'] = name
        if level is not None:
            params['level'] = level            
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listdomainsresponse']
            if len(res) > 0:
                data = res['domain']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        domains = []
        for item in data:
            # create Account instance
            domain = Domain(self, item)
            domains.append(domain)
        self.logger.debug("List cloudstack %s domains: %s..." % (self.id, str(domains)[0:200]))
        
        return domains

    @watch
    def list_accounts(self, domain=None, domain_id=None, account=None, oid=None):
        """List all accounts

        :param domain: full domain path like ROOT/CSI/dc
        :param domain_id: id of the domain the account belongs. This param and
                          domain are mutually exclusive
        :param account: account name
        :param oid: account id
        """
        params = {'command':'listAccounts',
                  'listall':'true'}
        
        if domain is not None:
            try:
                params['domainid'] = self.get_domain_id(domain)
            except ApiError as ex:
                raise ClskError(ex)
        if domain_id is not None:
            params['domainid'] = domain_id
        if account is not None:
            params['name'] = account
        if oid is not None:
            params['id'] = oid
            
        self.logger.debug("Get account list: %s" % params)

        try:
            response = self.send_request(params)
            res = json.loads(response)['listaccountsresponse']
            if len(res) > 0:
                data = res['account']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        accounts = []
        for item in data:
            # create Account instance
            account = Account(self, item)
            accounts.append(account)
        self.logger.debug("List cloudstack %s account: %s..." % (self.id, str(accounts)[0:200]))
        
        return accounts        

    @watch
    def list_service_offerings(self, name=None, oid=None):
        """List service offerings.
        
        :param name: name of the offering
        :param oid: id of the offering
        :return: Dictionary with all the offerings
        :rtype: dict       
        :raises ClskError: raise :class:`.base.ClskError`           
        """
        params = {'command':'listServiceOfferings'}

        if name is not None:
            params['name'] = name
        if oid is not None:
            params['id'] = oid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listserviceofferingsresponse']
            if len(res) > 0:
                data = res['serviceoffering']
            else:
                data = []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        serviceofferings = []
        for item in data:
            serviceoffering = ServiceOffering(self, item)
            serviceofferings.append(serviceoffering)
        
        self.logger.debug("Get service offerings: %s..." % str(serviceofferings)[0:200])
        return serviceofferings
    
    @watch
    def create_service_offering(self, name, displaytext, cpunumber, cpuspeed,
                                       memory, customizediops=None, 
                                       deploymentplanner=None,
                                       issystem=False, isvolatile=False, 
                                       offerha=False, limitcpuuse=None, 
                                       hosttags=None, storagetype='shared', 
                                       bytesreadrate=None, byteswriterate=None,
                                       iopsreadrate=None, iopswriterate=None, 
                                       networkrate=None, systemvmtype=None,
                                       maxiops=None, miniops=None, 
                                       serviceofferingdetails=None, tags=None):
        """Creates a service offering.

        :param displaytext: the display text of the service offering
        :param name: the name of the service offering
        :param bytesreadrate: bytes read rate of the disk offering [otpional]
        :param byteswriterate: bytes write rate of the disk offering [otpional]
        :param cpunumber: the CPU number of the service offering
        :param cpuspeed: the CPU speed of the service offering in MHz.
        :param customizediops: whether compute offering iops is custom or 
                               not [otpional]
        :param deploymentplanner: The deployment planner heuristics used to 
                                  deploy a instance of this offering. If null, value 
                                  of global config vm.deployment.planner is 
                                  used [otpional]
        :param limitcpuuse: restrict the CPU usage to committed service 
                            offering [otpional]
        :param hosttags: the host tag for this service offering. [otpional]
        :param iopsreadrate: io requests read rate of the disk 
                             offering [otpional]
        :param iopswriterate: io requests write rate of the disk offering [otpional]
        :param maxiops: max iops of the compute offering [otpional]
        :param miniops: min iops of the compute offering [otpional]
        :param serviceofferingdetails: details for planner, used to store 
                                       specific parameters [otpional]
        :param issystem: is this a system instance offering [default=false]
        :param isvolatile: true if the virtual machine needs to be volatile so 
                           that on every reboot of instance, original root disk is 
                           dettached then destroyed and a fresh root disk is 
                           created and attached to instance [default=false]
        :param memory: the total memory of the service offering in MB
        :param networkrate: data transfer rate in megabits per second allowed. 
                            Supported only for non-System offering and system 
                            offerings having "domainrouter" systemvmtype [otpional]
        :param offerha: the HA for the service offering [default=false]
        :param storagetype: the storage type of the service offering. Values are 
                            local and shared. [default=shared]
        :param systemvmtype: the system instance type. Possible types are 
                             "domainrouter", "consoleproxy" and 
                             "secondarystoragevm". [otpional]
        :param tags: the tags for this service offering.
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """  
        params = {'command':'createServiceOffering',
                  'name':name,
                  'displaytext':displaytext,
                  'cpunumber':cpunumber,
                  'cpuspeed':cpuspeed,
                  'memory':memory,
                  'issystem':issystem,
                  'isvolatile':isvolatile,
                  'offerha':offerha,
                  'storagetype':storagetype}
        
        if limitcpuuse is not None:
            params['limitcpuuse'] = limitcpuuse
        if hosttags is not None:
            params['hosttags'] = hosttags
        if bytesreadrate is not None:
            params['bytesreadrate'] = bytesreadrate
        if byteswriterate is not None:
            params['byteswriterate'] = byteswriterate
        if iopsreadrate is not None:
            params['iopsreadrate'] = iopsreadrate
        if iopswriterate is not None:
            params['iopswriterate'] = iopswriterate
        if networkrate is not None:
            params['networkrate'] = networkrate
        if systemvmtype is not None:
            params['systemvmtype'] = systemvmtype
        if customizediops is not None:
            params['customizediops'] = customizediops
        if deploymentplanner is not None:
            params['deploymentplanner'] = deploymentplanner
        if maxiops is not None:
            params['maxiops'] = maxiops
        if miniops is not None:
            params['miniops'] = miniops
        if serviceofferingdetails is not None:
            params['serviceofferingdetails'] = serviceofferingdetails
        if tags is not None:
            params['tags'] = tags
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            data = res['createserviceofferingresponse']['serviceoffering']
            self.logger.debug("Create service offering: %s" % data)
            serviceoffering = ServiceOffering(self, data)
            return serviceoffering
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)     
    
    @watch
    def list_network_offerings(self, name=None, oid=None):
        """List all accounts.
        
        :param name: name of the offering
        :param oid: id of the offering        
        :return: Dictionary with all the offerings
        :rtype: dict       
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        params = {'command':'listNetworkOfferings'}

        if name is not None:
            params['name'] = name
        if oid is not None:
            params['id'] = oid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listnetworkofferingsresponse']
            if len(res) > 0:
                data = res['networkoffering']
            else:
                data = []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        networkofferings = []
        for item in data:
            networkoffering = NetworkOffering(self, item)
            networkofferings.append(networkoffering)
        
        self.logger.debug("Get network offerings: %s..." % str(networkofferings)[0:200])
        return networkofferings    

    @watch
    def create_network_offering(self, name, displaytext):
        """Creates a network offering.

        :param displaytext: tthe display text of the network offering
        :param name: the name of the network offering
        :param guestiptype: guest type of the network offering: Shared or Isolated
        :param supportedservices: services supported by the network offering
        :param traffictype: the traffic type for the network offering. Supported type in current release is GUEST only
        :param availability: the availability of network offering. Default value is Optional
        :param conservemode: true if the network offering is IP conserve mode enabled
        :param details: Network offering details in key/value pairs. Supported keys are internallbprovider/publiclbprovider with service provider as a value
        :param egressdefaultpolicytrue if default guest network egress policy is allow; false if default egress policy is deny
        :param ispersistenttrue if network offering supports persistent networks; defaulted to false if not specified
        :param keepaliveenabledif true keepalive will be turned on in the loadbalancer. At the time of writing this has only an effect on haproxy; the mode http and httpclose options are unset in the haproxy conf file.
        :param maxconnectionsmaximum number of concurrent connections supported by the network offering
        :param networkratedata transfer rate in megabits per second allowed
        :param servicecapabilitylistdesired service capabilities as part of network offering
        :param serviceofferingidthe service offering ID used by virtual router provider
        :param serviceproviderlistprovider to service mapping. If not specified, the provider for the service will be mapped to the default provider on the physical network
        :param specifyipranges: true if network offering supports specifying ip ranges; defaulted to false if not specified
        :param specifyvlan: true if network offering supports vlans

        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """  
        params = {'command':'createServiceOffering',
                  'name':name}

        try:
            response = self.send_request(params)
            res = json.loads(response)
            data = res['createserviceofferingresponse']['serviceoffering']
            self.logger.debug("Create service offering: %s" % data)
            return data
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def list_disk_offerings(self, name=None, oid=None):
        """List all accounts.
        
        :param name: name of the offering
        :param oid: id of the offering        
        :return: Dictionary with all the offerings
        :rtype: dict       
        :raises ClskError: raise :class:`.base.ClskError`           
        """
        params = {'command':'listDiskOfferings'}

        if name is not None:
            params['name'] = name
        if oid is not None:
            params['id'] = oid

        try:
            response = self.send_request(params)
            res = json.loads(response)['listdiskofferingsresponse']
            if len(res) > 0:
                data = res['diskoffering']
            else:
                return []
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        diskofferings = []
        for item in data:
            diskoffering = DiskOffering(self, item)
            diskofferings.append(diskoffering)
        
        self.logger.debug("Get disk offerings: %s..." % str(diskofferings)[0:200])
        return diskofferings

    @watch
    def create_disk_offering(self, name, displaytext):
        """Creates a disk offering.
        """
        pass

    #---------------------------------------------------------------------------
    # create object
    @watch    
    def create_domain(self, name, parent_domain_id=None):
        """Create domain 
        
        :param name: full domain path like ROOT/CSI/dc
        :param parent_domain_id: id of the parent domain [optional]
        :return: :class:`Domain` instance
        :rtype: :class:`Domain`
        :raises ClskError: raise :class:`.base.ClskError`   
        """
        params = {'command':'createDomain',
                  'name':name}
        
        if parent_domain_id is not None:
            params['parentdomainid'] = parent_domain_id
        
        try:
            response = self.send_request(params)
            data = json.loads(response)['createdomainresponse']['domain']
            
            # create Account instance
            domain = Domain(self, data) 
            self.logger.debug('Create cloudstack %s domain: %s' % (self.id, name))
            return domain
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def create_instance(self, name, displayname, serviceofferingid, templateid,
                        zoneid, domainid, account, hypervisor, networkids,
                        hostid=None, diskofferingid=None, size=None, 
                        keyboard='it', startvm=True, spice=True,
                        spice_multi=False, videoqxl=True, usbredir=True,
                        audio='ich6'):
        """Create virtual machine.
        
        *Async command*

        :param name: host name for the virtual machine
        :param displayname: an optional user generated name for the 
                            virtual machine
        :param serviceofferingid: the ID of the service offering for the 
                                  virtual machine
        :param templateid: the: ID of the template for the virtual machine
        :param zoneid: availability zone for the virtual machine
        :param domainid: an optional domain for the virtual machine. If the 
                       account parameter is used, domain must also be used.        
        :param account: an optional account for the virtual machine. 
                        Must be used with domainId.
        :param projectid: Deploy instance for the project        
        :param diskofferingid: the ID of the disk offering for the virtual 
                               machine. If the template is of ISO format, the 
                               diskOfferingId is for the root disk volume. 
                               Otherwise this parameter is used to indicate the 
                               offering for the data disk volume. If the 
                               templateId parameter passed is from a Template 
                               object, the diskOfferingId refers to a DATA Disk 
                               Volume created. If the templateId parameter 
                               passed is from an ISO object, the diskOfferingId 
                               refers to a ROOT Disk Volume created.
        :param hostid: destination Host ID to deploy the instance to - parameter 
                       available for root admin only
        :param hypervisor: the hypervisor on which to deploy the virtual machine
        :param networkids: list of network ids used by virtual machine. 
                           Can't be specified with ipToNetworkList parameter        
        :param keyboard: an optional keyboard device type for the virtual 
                         machine. valid value can be one of de,de-ch,es,fi,fr,
                         fr-be,fr-ch,is,it,jp,nl-be,no,pt,uk,us
        :param keypair: name of the ssh key pair used to login to the 
                        virtual machine
        :param size: the arbitrary size for the DATADISK volume. Mutually 
                     exclusive with diskOfferingId
        :param startvm: true if network offering supports specifying ip ranges; 
                        defaulted to true if not specified
        :param spice: True enable spice connection [default=True]
        :param spice_multi: True enable spice multi session [default=False]
        :param videoqxl: True enable qxl video [default=True]
        :param usbredir: True enable usb redirection [default=True]
        :param audio: Audio type. USe one of this: ac97, es1370, sb16, ich6
                     [default=ich6]
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`                         
        """        
        params = {'command':'deployVirtualMachine',
                  'name':name,
                  'displayname':displayname,
                  'serviceofferingid':serviceofferingid,
                  'templateid':templateid,
                  'zoneid':zoneid,
                  'domainid':domainid,
                  'account':account,
                  'hypervisor':hypervisor,
                  'networkids':networkids,
                  'keyboard':keyboard,
                  'startvm':startvm}
        
        if diskofferingid is not None:
            params['diskofferingid'] = diskofferingid
        if size is not None:
            params['size'] = size            
        if diskofferingid is not None:
            params['hostid'] = hostid
        if spice is True:
            params['details[3].spice'] = 'on'
        if spice_multi is True:
            params['details[4].spice_multi'] = 'true'            
        if videoqxl is True:
            params['details[0].videoqxl'] = 'on'
        if usbredir is True:
            params['details[2].usbredir'] = 'on'
        if audio is not None:
            params['details[1].audio'] = audio
            
        try:
            response = self.send_request(params)
            res = json.loads(response)
            clsk_job_id = res['deployvirtualmachineresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.id, 
                              'deployVirtualMachine', res))            
            return clsk_job_id
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def create_isolated_network(self, name, displaytext, 
                                  networkoffering_id, zone_id,
                                  domain_id=None, domain=None, account=None,
                                  networkdomain=None, 
                                  physicalnetworkid=None,
                                  gateway=None, netmask=None, 
                                  startip=None, endip=None, vlan=None):
        """Create isolated network.
        
        :param str name: network name
        :param str displaytext: network displaytext
        :param str networkoffering_id: network offering id
        :param str zone_id: id of the zone
        :param str domain_id: id of the domain
        :param str domain: domain name. Use in place of domain_id
        :param str account: account name        
        :param str networkdomain: network domain [optional]
        :param str physicalnetworkid: physical network id [optional]
        :param gateway: 172.16.1.1 [optional]
        :param netmask: 255.255.255.0 [optional]
        :param startip: 172.16.1.2 [optional]
        :param endip: 172.16.1.254 [optional]
        :param vlan: vlan id. Ex. 239 [optional]
        :return: 
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`
        """       
        params = {'command':'createNetwork',
                  'name':name,
                  'displaytext':displaytext,
                  'networkofferingid':networkoffering_id,
                  'zoneid':zone_id,
                  'acltype':'Account'}
        
        if domain is not None:
            params['domainid'] = self.get_domain_id(domain)
        elif domain_id is not None:
            params['domainid'] = domain_id
        if account is not None:
            params['account'] = account
        if physicalnetworkid is not None:
            params['physicalnetworkid'] = physicalnetworkid
        if networkdomain is not None:
            params['networkdomain'] = networkdomain
        if networkdomain is not None:
            params['gateway'] = gateway
        if networkdomain is not None:
            params['netmask'] = netmask            
        if networkdomain is not None:
            params['startip'] = startip
        if networkdomain is not None:
            params['endip'] = endip
        if vlan is not None:
            params['vlan'] = vlan
                    
        try:
            response = self.send_request(params)
            res = json.loads(response)['createnetworkresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return None
            
            # create network
            net = Network(self, data)
            self.logger.debug('Create isolated cloudstack %s network: %s' % (self.id, name))
            return net   
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
    @watch
    def create_guest_network(self, name, displaytext, 
                               networkoffering_id, zone_id,
                               gateway, netmask, startip, endip, vlan, 
                               domain_id=None, domain=None, account=None,
                               networkdomain=None,
                               physicalnetworkid=None):
        """Create guest cloudstack network
        
        :param str name: network name
        :param str displaytext: network displaytext
        :param str networkoffering_id: network offering id
        :param str zone_id: id of the zone
        :param str domain_id: id of the domain
        :param str domain: domain name. Use in place of domain_id
        :param str account: account name [default=None]
        :param bool shared: True set network shared for all account in the domain.
                            False set network isolated to account. [optional]
        :param str networkdomain: network domain [optional]
        :param str physicalnetworkid: physical network id [optional]
        :param gateway: 10.102.221.129
        :param netmask: 255.255.255.240
        :param startip: 10.102.221.130
        :param endip: 10.102.221.142
        :param vlan: vlan id. Ex. 239
        :return: 
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        params = {'command':'createNetwork',
                  'name':name,
                  'displaytext':displaytext,
                  'networkofferingid':networkoffering_id,
                  'zoneid':zone_id,
                  'gateway':gateway,
                  'netmask':netmask,
                  'startip':startip,
                  'endip':endip,
                  'vlan':str(vlan)}
        
        # set shared status of the network
        if account is not None:
            params['acltype'] = 'Account'
            params['account'] = account
        else:
            params['acltype'] = 'Domain'
            
        if domain is not None:
            params['domainid'] = self.get_domain_id(domain)
        elif domain_id is not None:
            params['domainid'] = domain_id
        if physicalnetworkid is not None:
            params['physicalnetworkid'] = physicalnetworkid
        if networkdomain is not None:
            params['networkdomain'] = networkdomain

        try:
            response = self.send_request(params)
            res = json.loads(response)['createnetworkresponse']
            if len(res) > 0:
                data = res['network']
            else:
                return None
            
            # create network
            net = Network(self, data)
            self.logger.debug('Create guest cloudstack %s network: %s' % (self.id, name))
            return net            
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def create_data_volume(self, name, zone_id,
                                 domain_id=None, domain=None, account=None,
                                 diskofferingid=None, 
                                 snapshotid=None,
                                 size=None,
                                 virtualmachineid=None,
                                 maxiops=None, miniops=None):
        """Create a disk volume from a disk offering. This disk volume must 
        still be attached to a virtual machine to make use of it.
        
        *Async command*
        
        :param name: the name of the disk volume
        :param zoneid: the ID of the availability zone
        :param domainid: the domain ID associated with the disk offering. If 
                         used with the account parameter returns the disk volume
                         associated with the account for the specified domain.
        :param account: the account associated with the disk volume. Must be 
                        used with the domainId parameter.
        :param diskofferingid: the ID of the disk offering. Either 
                               diskOfferingId or snapshotId must be passed in.
        :param snapshotid: the snapshot ID for the disk volume. Either 
                           diskOfferingId or snapshotId must be passed in.
        :param int size: Arbitrary volume size
        :param virtualmachineid: the ID of the virtual machine; to be used with 
                                 snapshot Id, instance to which the volume gets 
                                 attached after creation
        :param maxiops: max iops
        :param miniops: min iops
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`    
        """
        self.logger.debug('Create data volume: %s' % name)
        
        params = {'command':'createVolume',
                  'name':name,
                  'zoneid':zone_id}
        
        if domain is not None:
            params['domainid'] = self.get_domain_id(domain)
        elif domain_id is not None:
            params['domainid'] = domain_id
        if account is not None:
            params['account'] = account
        if diskofferingid is not None:
            params['diskofferingid'] = diskofferingid
        if snapshotid is not None:
            params['snapshotid'] = snapshotid            
        if size is not None:
            params['size'] = size 
        if virtualmachineid is not None:
            params['virtualmachineid'] = virtualmachineid 
        if maxiops is not None:
            params['maxiops'] = maxiops 
        if miniops is not None:
            params['miniops'] = miniops            
        
        try:
            response = self.send_request(params)
            res = json.loads(response)            
            clsk_job_id = res['createvolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.id, 
                              'createVolume', res))             
            return clsk_job_id            
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def upload_data_volume(self, name, zoneid, format, url,
                                 domain_id=None, domain=None, account=None,
                                 checksum=None, 
                                 imagestoreuuid=None):
        """Uploads a data disk.
        
        *Async command*
        
        :param name: the name of the volume
        :param format: the format for the volume. Possible values include QCOW2,
                       OVA, and VHD.        
        :param url: the URL of where the volume is hosted. Possible URL include http:// and https://
        :param zoneid: the ID of the zone the volume is to be hosted on
        :param account: an optional accountName. Must be used with domainId.
        :param domainid: an optional domainId. If the account parameter is used, 
                         domainId must also be used.
        :param domain:
        :param checksum: the MD5 checksum value of this volume
        :param imagestoreuuid: Image store uuid
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`        
        """
        self.logger.debug('Create data volume: %s' % name)
        
        params = {'command':'uploadVolume',
                  'name':name,
                  'zoneid':zoneid}
        
        if domain is not None:
            params['domainid'] = self.get_domain_id(domain)
        elif domain_id is not None:
            params['domainid'] = domain_id
        if account is not None:
            params['account'] = account
        if checksum is not None:
            params['checksum'] = checksum
        if imagestoreuuid is not None:
            params['imagestoreuuid'] = imagestoreuuid          
        
        try:
            response = self.send_request(params)
            res = json.loads(response)            
            clsk_job_id = res['createvolumeresponse']['jobid']
            self.logger.debug('Start job over %s.%s - %s: %s' % (
                              self._obj_type, self.id, 
                              'uploadVolume', res))               
            return clsk_job_id            
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def register_template(self, name, displaytext, format, hypervisor, ostypeid,
                                url, zoneid, domainid=None, account=None,
                                checksum=None, bits=64,
                                isdynamicallyscalable=False, isextractable=True,
                                isfeatured=False, ispublic=True, isrouting=False,
                                passwordenabled=False):
        """Registers an existing template into the CloudStack cloud.
        
        :param name: the name of the volume
        :param displaytext: the display text of the template. This is usually 
                            used for display purposes.
        :param format: the format for the volume. Possible values include QCOW2,
                       OVA, and VHD.
        :param hypervisor: the target hypervisor for the template
        :param ostypeid: the ID of the OS Type that best represents the OS of 
                         this template.
        :param url: the URL of where the volume is hosted. Possible URL include http:// and https://
        
        :param zoneid: the ID of the zone the volume is to be hosted on
        :param account: an optional accountName. Must be used with domainId [optional]
        :param domainid: an optional domainId. If the account parameter is used, 
                         domainId must also be used [optional]
        :param checksum: the MD5 checksum value of this volume.
        :param bits: 32 or 64 bits support. 64 by default
        :param isdynamicallyscalable: true if template contains XS/VMWare tools 
                                      inorder to support dynamic scaling of instance 
                                      cpu/memory
        :param isextractable: true if the template or its derivatives are 
                              extractable; default is false
        :param isfeatured: true if this template is a featured template, false 
                           otherwise
        :param ispublic: true if the template is available to all accounts; 
                         default is true
        :param isrouting: true if the template type is routing i.e., if template 
                          is used to deploy router
        :param passwordenabled: true if the template supports the password reset 
                                feature; default is false
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`  
        """
        self.logger.debug('Create data volume: %s' % name)
        
        params = {'command':'registerTemplate',
                  'name':name,
                  'displaytext':displaytext,
                  'format':format,
                  'hypervisor':hypervisor,
                  'ostypeid':ostypeid,
                  'url':url,
                  'zoneid':zoneid,
                  'bits':bits,
                  'isdynamicallyscalable':isdynamicallyscalable,
                  'isextractable':isextractable,
                  'isfeatured':isfeatured,
                  'ispublic':ispublic,
                  'isrouting':isrouting,
                  'passwordenabled':passwordenabled}
        
        if domainid is not None:
            params['domainid'] = domainid
        if account is not None:
            params['account'] = account
        if checksum is not None:
            params['checksum'] = checksum     
        
        try:
            response = self.send_request(params)
            res = json.loads(response) 
            data = res['registertemplateresponse']['template'][0]
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        # create Template instance
        template = Template(self._api_client, data=data)
        self.logger.debug('Register cloudstack %s template: %s' % (self.id, name))
        return template

    @watch
    def register_iso(self, name, displaytext, hypervisor, ostypeid,
                                url, zoneid, domain_id=None, account=None,
                                checksum=None, bits=64,
                                isdynamicallyscalable=False, isextractable=True,
                                isfeatured=False, ispublic=True):
        """Registers an existing ISO into the CloudStack Cloud.
        
        :param name: the name of the volume
        :param displaytext: the display text of the template. This is usually 
                            used for display purposes.
        :param hypervisor: the target hypervisor for the template
        :param ostypeid: the ID of the OS Type that best represents the OS of 
                         this template.
        :param url: the URL of where the volume is hosted. Possible URL include http:// and https://
        
        :param zoneid: the ID of the zone the volume is to be hosted on
        :param account: an optional accountName. Must be used with domainId [optional]
        :param domainid: an optional domainId. If the account parameter is used, 
                         domainId must also be used [optional]
        :param checksum: the MD5 checksum value of this volume.
        :param bits: 32 or 64 bits support. 64 by default
        :param isdynamicallyscalable: true if template contains XS/VMWare tools 
                                      inorder to support dynamic scaling of instance 
                                      cpu/memory
        :param isextractable: true if the template or its derivatives are 
                              extractable; default is false
        :param isfeatured: true if this template is a featured template, false 
                           otherwise
        :param ispublic: true if the template is available to all accounts; 
                         default is true
        :return: Cloudstack asynchronous job id
        :rtype: str
        :raises ClskError: raise :class:`.base.ClskError`  
        """
        self.logger.debug('Create data volume: %s' % name)
        
        params = {'command':'registerIso',
                  'name':name,
                  'displaytext':displaytext,
                  'hypervisor':hypervisor,
                  'ostypeid':ostypeid,
                  'url':url,
                  'zoneid':zoneid,
                  'bits':bits,
                  'isdynamicallyscalable':isdynamicallyscalable,
                  'isextractable':isextractable,
                  'isfeatured':isfeatured,
                  'ispublic':ispublic}
        
        if domain_id is not None:
            params['domainid'] = domain_id
        if account is not None:
            params['account'] = account
        if checksum is not None:
            params['checksum'] = checksum     
        
        try:
            response = self.send_request(params)
            res = json.loads(response) 
            data = res['registerisoresponse']['iso'][0]
        except KeyError as ex :
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
        # create Template instance
        template = Iso(self._api_client, data=data)
        self.logger.debug('Register cloudstack %s iso: %s' % (self.id, name))
        return template

    # tree object
    @watch
    def tree_physical(self):
        """Return physical tree."""
        system = {'name':self._name, 
                  'id':self.id, 
                  'type':self._obj_type, 
                  'childs':[]}
        for zone in self.list_zones():
            system['childs'].append(zone.tree())
        return system

    @watch
    def tree_logical(self):
        """Return logical tree."""
        system = {'name':self._name, 
                  'id':self.id, 
                  'type':self._obj_type, 
                  'childs':[]}
        for domain in self.list_domains():
            system['childs'].append(domain.tree())
        return system

    @watch
    def tree_network(self):
        """Return network tree."""
        system = {'name':self._name, 
                  'id':self.id, 
                  'type':self._obj_type, 
                  'childs':[]}
        for network in self.list_networks():
            system['childs'].append(network.tree())
        return system

    # get resource by id
    @watch    
    def get_domain_id(self, path):
        """Get id for the domain specified.
        
        :param path: full domain path like ROOT/CSI/dc
        """
        name = path.split('/')[-1]
        params = {'command':'listDomains',
                  'name':name,
                 }
        
        try:
            response = self.send_request(params)
            data = json.loads(response)['listdomainsresponse']['domain']
            domain_id = [d['id'] for d in data if str(d['path']) == path][0]
            
            self.logger.debug("Id of domain '%s': %s" % (path, domain_id))
            return domain_id
        except (KeyError, Exception):
            self.logger.error('Domain %s does not exist' % path)
            raise ClskError('Domain %s does not exist' % path)
        except ApiError as ex:
            self.logger.error('Domain %s does not exist' % path)
            raise ClskError(ex)

    @watch
    def get_account_id(self, domainid, name):
        """Get id for the account specified.
        
        :param name: name of the account
        """
        params = {'command':'listAccounts',
                  'domainid':domainid,
                  'name':name,
                 }
        
        try:
            response = self.send_request(params)
            data = json.loads(response)['listaccountsresponse']['account'][0]
            accountid = data['id']
            self.logger.debug("Id of account '%s/%s': %s" % (domainid, name, accountid))
            return accountid
        except (KeyError, TypeError):
            raise ClskError('Account %s.%s does not exist' % (domainid, name))
        except ApiError as ex:
            raise ClskError(ex)

    @watch
    def get_domain_path(self, domain_id):
        """Get virtual machine domain path """
        params = {'command':'listDomains',
                  'id':domain_id}
        
        try:
            response = self.send_request(params)
            res = json.loads(response)['listdomainsresponse']['domain'][0]
            dompath = res['path']
            self.logger.debug("Path of domain '%s': %s" % (domain_id, dompath))
            return dompath
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
    #
    # usage
    #
    def get_usage_type(self):
        """Get usage types """
        params = {'command':'listUsageTypes'}
        
        try:
            res = []
            response = self.send_request(params)
            data = json.loads(response)['listusagetypesresponse']['usagetype']
            print data
            for item in data:
                num = int(item['usagetypeid'])-1
                res.insert(num, str(item['description']))
            self.logger.debug("Get usage types: %s..." % str(res)[0:200])
            return res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)
        
    def get_usage_data(self, domainid=None, oid=None, accountid=None, 
                             startdate=None, enddate=None, usage_type=None):
        """Get usage data
        
        :param domaind: id of the domain [optional]
        :param accountid: id of the account [optional]
        :param enddate: End date range for usage record query. Use yyyy-MM-dd 
                        as the date format, e.g. startDate=2009-06-03 [optional]
        :param startdate: Start date range for usage record query. Use 
                          yyyy-MM-dd as the date format, e.g. startDate=2009-06-01.
                           [optional]
        :param usage_type: 1:'Running Vm Usage', 2:'Allocated Vm Usage', 
                           3:'IP Address Usage', 4:'Network Usage (Bytes Sent)', 
                           5:'Network Usage (Bytes Received)', 6:'Volume Usage', 
                           7:'Template Usage', 8:'ISO Usage', 9:'Snapshot Usage', 
                           10:'Security Group Usage', 11:'Load Balancer Usage', 
                           12:'Port Forwarding Usage', 13:'Network Offering Usage', 
                           14:'VPN users usage', 15:'VM Disk usage(I/O Read)', 
                           16:'VM Disk usage(I/O Write)', 17:'VM Disk usage(Bytes Read)', 
                           18:'VM Disk usage(Bytes Write)', 19:'VM Snapshot storage usage'
                            [optional]
        """
        params = {'command':'listUsageRecords'}
        
        now = time.time()
        today = date.fromtimestamp(now-86400*1)
        yesterday = date.fromtimestamp(now-86400*2)

        if oid is not None:
            params['usageid'] = oid
        if domainid is not None:
            params['domainid'] = domainid
        if accountid is not None:
            params['accountid'] = accountid
        if startdate is not None:
            params['startdate'] = startdate
        else:
            params['startdate'] = "%s-%s-%s" % (yesterday.year, 
                                                yesterday.month, 
                                                yesterday.day)
        if enddate is not None:
            params['enddate'] = enddate
        else:
            params['enddate'] = "%s-%s-%s" % (today.year, 
                                              today.month, 
                                              today.day)            
        if usage_type is not None:
            params['type'] = usage_type    
        
        try:
            res = []
            response = self.send_request(params)
            data = json.loads(response)['listusagerecordsresponse']
            if 'usagerecord' in data:
                res = data['usagerecord']
            else:
                res = []
            self.logger.debug("Get usage data: %s..." % str(res)[0:200])
            return res
        except KeyError as ex:
            raise ClskError('Error parsing json data: %s' % ex)
        except ApiError as ex:
            raise ClskError(ex)