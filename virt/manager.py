'''
Created on Jul 29, 2013

@author: darkbk
'''
import libvirt
import types
import logging
from time import gmtime
from time import strftime
from beecell.xml_parser import xml2dict
from beecell.perf import watch
from beecell.remote import RemoteClient, RemoteException
from beedrones.dto import Interface
from beedrones.dto import Bridge
from beedrones.dto import BondInterface
from beedrones.dto import Network
from beedrones.dto import VirtualMachine
from beedrones.dto import Storage
from beedrones.dto import Datastore
from beedrones.dto import DatastoreItem

try:
    import gevent
    import gevent.monkey
    # apply monkey patch
    gevent.monkey.patch_all()    
except:
    pass

"""
0    VIR_DOMAIN_NOSTATE    no state
1    VIR_DOMAIN_RUNNING    the domain is running
2    VIR_DOMAIN_BLOCKED    the domain is blocked on resource
3    VIR_DOMAIN_PAUSED     the domain is paused by user
4    VIR_DOMAIN_SHUTDOWN   the domain is being shut down
5    VIR_DOMAIN_SHUTOFF    the domain is shut off
6    VIR_DOMAIN_CRASHED    the domain is crashed
7    VIR_DOMAIN_PMSUSPENDED    the domain is suspended by guest 
                               power management
8    VIR_DOMAIN_LAST        NB: this enum value will increase 
                            over time as new events are added 
                            to the libvirt API. It reflects the 
                            last state supported by this version 
                            of the libvirt API.
"""
vm_state = ['NOSTATE',
            'RUNNING',
            'BLOCKED',
            'PAUSED',
            'SHUTDOWN',
            'SHUTOFF',
            'CRASHED',
            'PMSUSPENDED',
            'LAST',
            ]

'''
class VirtServerError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)
'''
class VirtManagerError(Exception): pass
class VirtManager(object):
    logger = logging.getLogger('gibbon.cloud.virt')
    
    def __init__(self, hid, host, port, user=None, pwd=None, key=None, async=False):
        """
        :param api_params: dict with {uri, api_key, sec_key}
        """
        self.id = hid
        # mysql db connection params
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.key = key
        self.async = async

    def __str__(self):
        return "<VirtManager id=%s, host=%s, port=%s>" % \
                (self.id, self.host, self.port)
        
    def __repr__(self):
        return "<VirtManager id=%s, host=%s, port=%s>" % \
                (self.id, self.host, self.port)

    def get_conn(self):
        try:
            conn_string = "qemu+tcp://%s:%s/system" % (self.host, self.port)
            conn = VirtServer(id, conn_string, async=self.async)
            conn.connect()
            self.logger.debug('Get libvirt-qemu server %s:%s connection: %s' % (
                self.host, self.port, conn))
            return conn
        except VirtServerError as e:
            raise VirtManagerError(e)
    
    def release_conn(self, conn):
        conn.disconnect()
        self.logger.debug('Release libvirt-qemu connection: %s' % (conn))
        
    def run_ssh_command(self, cmd):
        try:
            remote = RemoteClient(self.host)
            return remote.run_ssh_command(cmd, self.user, self.pwd, 22)
        except RemoteException as e:
            raise VirtManagerError(e)

class VirtServerError(Exception): pass
class VirtServer(object):
    logger = logging.getLogger('gibbon.cloud.virt')
    
    """ """
    def __init__(self, id, uri, async=False):
        """
        :param uri : Example "qemu+tcp://10.102.90.3/system" 
        """
        self.id = id
        self.uri = uri
        self.conn = None
        self.hostname = None
        self.async = async
        
        self.datacenter = {'id':'dc1', 'name':'dc1'}
        self.cluster = {'id':'cls1', 'name':'cls1'}
    
    def switch(self):
        try:
            if self.async is True:
                gevent.sleep(0.01)
        except:
            pass
    
    # hypervisor
    @watch
    def connect(self):
        
        """ """
        if self.conn == None:
            try:
                self.switch()
                self.conn = libvirt.open(self.uri)
                self.switch()
                self.hostname = self.conn.getHostname()
                self.switch()
            except libvirt.libvirtError as ex:
                raise VirtServerError(ex)
            
        return self.conn

    @watch
    def disconnect(self):
        """ """
        if self.conn != None:
            self.conn.close()
            self.conn = None
 
    @watch
    def is_alive(self):
        """Return status of the hypervisor: alive, dead, error"""
        state = {1:'alive', 0:'dead', -1:'error'}
        res = None
        if self.conn != None:
            res = self.conn.isAlive()
            return state[res]
        else:
            raise VirtServerError('No connection to libvirt host found')
 
    @watch
    def ping(self):
        """Ping hypervisor """
        if self.conn != None and self.conn.isAlive() == 1:
            return True
        else:
            return False
 
    @watch
    def info(self):
        """Return basic hypervisor info: hostname, hypervisor, info, 
        libver, maxvcpux, uri.
        """
        if self.conn != None:
            libver = self.conn.getLibVersion()
            self.switch()
            conntype = self.conn.getType()
            self.switch()
            ver = self.conn.getVersion()
            self.switch()
            info = self.conn.getInfo()
            self.switch()
            uri = self.conn.getURI()
            self.switch()
            
            data = {'hostname':self.hostname,
                    'libver':libver,
                    'hypervisor':{'type':conntype, 
                                  'version':ver},
                    'info':info,
                    'uri':uri,
                    'type':None
                    #'filters':self.conn.listNWFilters(),
                   }
            return data
        else:
            raise VirtServerError('No connection to libvirt host found')

    @watch
    def tree(self):
        """Return hypervisor tree."""
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)
        
        tree = []
        
        dc_tree = {'id':self.datacenter['id'],
                   'name':self.datacenter['name'],
                   'clusters':[],
                   'datastores':[],
                   'networks':[],
                   'resource_pools':[],
                   'vms':[]}
        tree.append(dc_tree)
        
        # get clusters
        # kvm-libvirt hypervisor correspond to kvm host
        # To use the same structure as vShpere vCenter suppose that 
        # kvm-libvirt hypervisor has a cluster with one only host 
        # corresponding to itself
        cluster_info = {'id':self.cluster['id'],
                        'name':self.cluster['name'],
                        'hosts':self.nodes_list()}
        dc_tree['clusters'].append(cluster_info)
        
        # get datastores
        datastores = self.node_datastore_list(None)
        for datastore in datastores:
            datastore_info = {'id':datastore.id,
                              'name':datastore.name}
            dc_tree['datastores'].append(datastore_info)
        
        # get resource pools

        # get networks
        dc_tree['networks'] = [{'name':item} 
                               for item in self.networks_list().keys()]

        # get virtual machines
        dc_tree['vms'] = [{'name':dom.name(), 
                           'id':dom.ID(),
                           'state':vm_state[dom.info()[0]]
                          } for dom in self.conn.listAllDomains(1)]
        return dc_tree

    @watch
    def stats(self):
        """ TO-DO """
        pass

    @watch
    def nw_filters_list(self):
        """ """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)
        data = [] 
        for item in self.conn.listAllNWFilters(0):
            data.append(xml2dict(item.XMLDesc(0)))

    # node
    @watch
    def nodes_list(self):
        """ """
        return [{'id':self.id, 'name':self.hostname}]
    
    @watch
    def node_info(self, node_id):
        """Return kvm node info
        :param node_id: id ofnode
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)        
        
        info = xml2dict(self.conn.getCapabilities())

        # main info
        data = {'id':node_id,
                'name':self.hostname}
        
        # hardware
        data['hardware'] = info['host']                   

        # runtime
        data['runtime'] = None
        
        # cofiguration
        data['config'] = None
        
        # firmware
        data['firmware'] = info['guest']
        
        return data

    def __get_interface(self, desc, active):
        """ """
        mac = getattr(getattr(desc, 'mac', None), 'address', None)
        interface = Interface(desc['name'], active, mac)
        if 'protocol' in desc and desc['protocol'] is not None:
            # protocol is a list
            try:
                for p in desc['protocol']:
                    interface.add_ip_protocol(p['family'], 
                                              p['ip']['address'],
                                              p['ip']['prefix'])
            # protocolo is a single element
            except:
                p = desc['protocol']
                interface.add_ip_protocol(p['family'], 
                                          p['ip']['address'],
                                          p['ip']['prefix'])
                
        return interface

    def __get_bridge(self, desc, active):
        """ """
        interface = Bridge(desc['name'], active)
        # add ip configuration
        if 'protocol' in desc and desc['protocol'] is not None:
            # protocol is a list
            try:
                for p in desc['protocol']:
                    interface.add_ip_protocol(p['family'], 
                                              p['ip']['address'],
                                              p['ip']['prefix'])
            # protocolo is a single element
            except:
                p = desc['protocol']
                interface.add_ip_protocol(p['family'], 
                                          p['ip']['address'],
                                          p['ip']['prefix'])
        
        # add port
        try:
            for port in desc['bridge']['interface']:
                # add interface
                if port['type'] == 'ethernet':
                    mac = getattr(getattr(port, 'mac', None), 'address', None)
                    interface.add_port(Interface(desc['name'], active, mac))
                elif port['type'] == 'bond':
                    bond = BondInterface(desc['name'], active)
                    # add interfaces to bond
                    for i in port['interface']:
                        mac = getattr(getattr(i, 'mac', None), 'address', None)
                        bond.add_port(Interface(i['name'], active, mac))
                    interface.add_port(bond)
        except: pass
        
        return interface  

    @watch
    def node_network_list(self, node_id):
        """ List node networks. 
        :param node_id: id of the node.
        """
        if self.conn is None:
            raise VirtServerError('No connection to vCenter %s host found' %
                               self.id)

        try:
            network_list = {}
            
            # get node
            #node = self.__get_node_object(node_id)
            # get bridge form node network conf    
            conf = self.node_network_conf(node_id)
    
            # network              
            for k,v in conf.iteritems():
                if v.type == 'bridge':
                    # create new network
                    bridge = k
                    active = v.active
                    network = Network(bridge, active)
                    network_list[bridge] = network
                    
                    # get vlan id
                    info = k.split('-')
                    if len(info)>1:
                        network.set_param('vlan', info[1])
                    
                    # add vm to network
                    for port in v.ports:
                        if 'vm' in port.params:
                            network.add_vm(port.params['vm'])
            
            #for k in network_list.keys():
            #    network_list[k] = network_list[k].get_dict()        
        
            return network_list
        except libvirt.libvirtError, ex:
            raise VirtServerError(ex)
    
    @watch
    def node_network_conf(self, node_id):
        """ Describe node network configuration. 
        :param node_id: id of the node.
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)
            
        try:      
            data = {}
            
            # get physical interface
            # inactive interface
            for item in self.conn.listAllInterfaces(1):
                desc = xml2dict(item.XMLDesc(0))
                interface = self.__get_interface(desc, False)
                data[interface.name] = interface
                
            # active interface
            for item in self.conn.listAllInterfaces(2):
                desc = xml2dict(item.XMLDesc(0))
                if (desc['type'] == 'ethernet'):
                    interface = self.__get_interface(desc, True)
                else:
                    interface = self.__get_bridge(desc, True)
                data[interface.name] = interface
            
            # add bridge from libvirt list      
            for net in self.conn.listAllNetworks(0):
                desc = xml2dict(net.XMLDesc(0))

                active = net.isActive()
                bridge = Bridge(desc['bridge']['name'], active)
                
                mac = getattr(getattr(desc, 'mac', None), 'address', None)
                port = Interface(desc['bridge']['name'], active, mac)
                port.add_ip_protocol('ipv4', 
                                     desc['ip']['address'],
                                     desc['ip']['netmask'])
                bridge.add_port(port)
                
                bridge.set_param('delay', desc['bridge']['delay'])
                bridge.set_param('stp', desc['bridge']['stp'])
                bridge.set_param('forward', desc['forward'])
                bridge.set_policy('dhcp', desc['ip']['dhcp'])
                
                data[bridge.name] = bridge
            
            # get sub-bridge
            #   get all running vms
            vm_status = 16
            vm_list = self.vms_list(host=None, status=vm_status)
            
            #   iter vm list and find bridge used from vnic
            for item in vm_list:
                nets = self.vm_network(name=item.name)
                for net in nets:
                    bridge = net.params['bridge']
                    if bridge not in data:
                        data[bridge] = Bridge(bridge, True)
                    
                    # create interface
                    interface = Interface(net.name, True, net.mac)
                    # add info of virtual machine parent of interface
                    interface.set_param('vm', item.name)
                    
                    data[bridge].add_port(interface)

            # get dict
            for k,v in data.iteritems():
                data[k] = v #.get_dict()
                
            return data
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)        

    @watch
    def node_datastore_list(self, node_id):
        """Return kvm node storage
        
        Exception: VirtServerError 
        
        :param node_id: id of the node     
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)
        
        '''
        virStoragePoolState
        VIR_STORAGE_POOL_INACTIVE = 0
        VIR_STORAGE_POOL_BUILDING = 1
        VIR_STORAGE_POOL_RUNNING = 2
        VIR_STORAGE_POOL_DEGRADED = 3
        VIR_STORAGE_POOL_INACCESSIBLE = 4

        virConnectListAllStoragePoolsFlags
        VIR_CONNECT_LIST_STORAGE_POOLS_INACTIVE = 1
        VIR_CONNECT_LIST_STORAGE_POOLS_ACTIVE = 2
        VIR_CONNECT_LIST_STORAGE_POOLS_PERSISTENT = 4
        VIR_CONNECT_LIST_STORAGE_POOLS_TRANSIENT = 8
        VIR_CONNECT_LIST_STORAGE_POOLS_AUTOSTART = 16
        VIR_CONNECT_LIST_STORAGE_POOLS_NO_AUTOSTART = 32
        VIR_CONNECT_LIST_STORAGE_POOLS_DIR = 64
        VIR_CONNECT_LIST_STORAGE_POOLS_FS = 128
        VIR_CONNECT_LIST_STORAGE_POOLS_NETFS = 256
        VIR_CONNECT_LIST_STORAGE_POOLS_LOGICAL = 512
        VIR_CONNECT_LIST_STORAGE_POOLS_DISK = 1024
        VIR_CONNECT_LIST_STORAGE_POOLS_ISCSI = 2048
        VIR_CONNECT_LIST_STORAGE_POOLS_SCSI = 4096
        VIR_CONNECT_LIST_STORAGE_POOLS_MPATH = 8192
        VIR_CONNECT_LIST_STORAGE_POOLS_RBD = 16384
        VIR_CONNECT_LIST_STORAGE_POOLS_SHEEPDOG = 32768           
        '''
        dss = self.conn.listAllStoragePools(2)
        datastores = []
        active = [False, True]
        
        for ds in dss:
            item = Datastore(ds.name(),
                             ds.UUIDString(),
                             None,
                             active[int(ds.isActive())])
            #item.set_url(ds.info.url)
            #item.set_timestamp(ds.info.timestamp)
            # set sizes
            item.set_size('capacity', str(ds.info()[1]))
            #item.set_size('freeSpace', ds.summary.freeSpace)
            #item.set_size('uncommitted', getattr(ds.summary, 'uncommitted', None))
            #item.set_size('maxFileSize', ds.info.maxFileSize)
            # add vm
            #for vm in ds.vm:
            #    item.add_vm(vm.name)

            datastores.append(item)
        return datastores

    @watch
    def node_vm_list(self, node_id):
        """TO-DO Return virtual machine running on node
        
        Exception: VirtServerError.
        
        :param node_id: id of the node
        """
        vm_status = 1
        vms = self.vms_list(host=node_id, status=vm_status)
        return vms

    @watch
    def node_device_list(self, node_id):
        """ TO-DO create a device tree. Now structure is flat.
        
        Exception: VirtServerError
        
        :param node_id: id of the node
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)        
                  
        data = []
        try:
            for item in self.conn.listAllDevices(0):
                data.append({'name':item.name(),
                             'parent':item.parent(),
                             'listCaps':item.listCaps()[0],
                             'host':self.hostname,
                             })
        except libvirt.libvirtError, ex:
            raise VirtServerError(ex)
        return data

    # datastore
    @watch
    def datastores_list(self):
        """ Return running storage pool.
        """
        return self.node_datastore_list(None)

    def datastore_info(self, name=None, id=None):
        """TO-DO
        
        Exception: VirtServerError.
        
        :param name:
        :param id:
        :return
            {'allocation': {'data': '9344090112', 'unit': 'bytes'},
             'available': {'data': '527526821888', 'unit': 'bytes'},
             'capacity': {'data': '536870912000', 'unit': 'bytes'},
             'name': '62350862-632f-3598-97cd-6195ae92c874',
             'source': {'dir': {'path': '/mnt/zvol01/clsk_kvm/primary'},
                        'format': {'type': 'auto'},
                        'host': {'name': 'freenas.clskdom.lab'}},
             'target': {'path': '/mnt/62350862-632f-3598-97cd-6195ae92c874',
                        'permissions': {'group': '-1', 'mode': '0755', 'owner': '-1'}},
             'type': 'netfs',
             'uuid': '62350862-632f-3598-97cd-6195ae92c874'}        
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)        
        
        try:
            if name != None:
                dom = self.conn.storagePoolLookupByName(name)
            elif id != None:
                dom = self.conn.storagePoolLookupByUUIDString(id)
            data = xml2dict(dom.XMLDesc(1))
            return data
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)

    def datastore_tree(self, name=None, id=None, path = '/'):
        """ 
        Exception: VirtServerError.
        
        :param name:
        :param uuid:
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)
        
        data = []
        try:
            if name != None:
                dom = self.conn.storagePoolLookupByName(name)
            elif id != None:
                dom = self.conn.storagePoolLookupByUUIDString(id)
            storage_path = xml2dict(dom.XMLDesc(1))['target']['path']
            vols = dom.listVolumes()
            
            for vol in vols:
                try:
                    vol_path = "%s/%s" % (storage_path, vol)
                    volobj = self.__volume_info(path=vol_path)

                    itime = {}
                    # atime: time of last access (ls -lu)
                    #t = ctime(float(volobj['target']['timestamps']['atime']))
                    t = gmtime(float(volobj['target']['timestamps']['atime']))
                    itime['atime'] = strftime("%d-%m-%Y %H:%M:%S", t)
                    # mtime: time of last modification (ls -l)
                    t = gmtime(float(volobj['target']['timestamps']['mtime']))
                    itime['mtime'] = strftime("%d-%m-%Y %H:%M:%S", t)
                    # ctime: time of last status change (ls -lc)
                    t = gmtime(float(volobj['target']['timestamps']['ctime']))
                    itime['ctime'] = strftime("%d-%m-%Y %H:%M:%S", t)

                    size = {'capacity':int(volobj['capacity']['data']),
                            'used':int(volobj['allocation']['data'])}

                    # add new row to tree                    
                    raw = DatastoreItem(volobj['name'], 
                                        volobj['target']['path'],
                                        size, 
                                        volobj['target']['format']['type'], 
                                        volobj['target']['permissions'],
                                        itime)
                except Exception, e:
                    print e
                    # add new empty row to tree                    
                    raw = DatastoreItem(vol, 
                                        None, 
                                        None, 
                                        None, 
                                        None, 
                                        None)
                data.append(raw)
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)
        return data

    def __volume_info(self, name=None, path=None):
        """
        Exception: VirtServerError.
        
        :param extended: True show more description fields
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)
        
        data = None
        try:
            if name != None:
                vol = self.conn.storageVolLookupByName(name)
            elif path != None:
                vol = self.conn.storageVolLookupByPath(path)
            data = xml2dict(vol.XMLDesc(0))
            data['storage'] = vol.storagePoolLookupByVolume().name()
        except libvirt.libvirtError as ex:
            raise VirtServerError(ex)
        return data

    # network
    def networks_list(self):
        """List network list. Some used network may not appear. 
        
        Exception: VirtServerError.
        
        TO-DO : define active statuse
        """
        try:
            # list all running vms
            vm_status = 16
            vm_list = self.vms_list(host=None, status=vm_status)
            
            network_list = {}
            
            for item in vm_list:
                nets = self.vm_network(name=item.name)
                for net in nets:
                    # create new network
                    bridge = net.params['bridge']
                    if bridge not in network_list:
                        active = True
                        network = Network(bridge, active)
                        network.add_vm(item.name)
                        network_list[bridge] = network
                    # network already exist in network list
                    else:
                        network_list[bridge].add_vm(item.name)
            
            #for k in network_list.keys():
            #    network_list[k] = network_list[k].get_dict()
                        
            return network_list
        except libvirt.libvirtError, ex:
            VirtServerError(ex)

    # virtual machine
    def vms_list(self, datacenter=None, cluster=None, host=None,
                       resource_pool=None, status=None):
        """List vm for current host. Use vm status to filter the search.
        
        Exception: libvirtError, VirtServerError.
    
        :option node_id: id of node
        :option status:  
        1     ACTIVE
        2     INACTIVE
        4     PERSISTENT
        8     TRANSIENT
        16    RUNNING
        32    PAUSED
        64    SHUTOFF
        128   OTHER
        256   MANAGEDSAVE
        512   NO_MANAGEDSAVE
        1024  AUTOSTART
        2048  NO_AUTOSTART
        4096  HAS_SNAPSHOT
        8192  NO_SNAPSHOT  
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)

        data = []
        for dom in self.conn.listAllDomains(status):
            data.append(self.__get_vm_info(dom))
        return data

    def vm_info(self, name=None, id=None):
        """
        
        Exception: libvirtError, VirtServerError.
        
        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        desc = self.__get_vm_description(name, id)
        return desc

    def vm_storage(self, name=None, id=None):
        """ 
        TO-DO: get datastore name
        
        Exception: VirtServerError.
        
        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)          
        
        # get datastore list
        dss = self.datastores_list()
        #dss_info = {ds.name:self.datastore_tree(name=ds.name) for ds in dss}
        dss_info = {}
        for ds in dss:
            dss_info[ds.name] = self.datastore_tree(name=ds.name)
        #print dss_info
        
        # get vm description
        desc = self.__get_vm_description(name, id)

        try:
            storages = []
            for item in desc['devices']['disk']:
                keys = item.keys()
                path = item['source']['file']
                # find path in datastore
                size = None
                datastore = None
                for k,vv in dss_info.items():
                    for v in vv:
                        if v.path == path:
                            size = v.size
                            datastore = k
                            break
                
                if (('driver' in keys) and ('source' in keys)):
                    storage = Storage(item['alias']['name'],
                                      None,
                                      device=item['device'],
                                      driver=item['driver'],
                                      target=item['target'],
                                      size=size)
                    storage.set_source(path, 
                                       None,
                                       None,
                                       datastore)
                    storages.append(storage)
        except KeyError as ex:
            raise VirtServerError(ex)
        return storages
    
    def vm_files(self, name=None, id=None):
        """Get files related to virtual machine.
        
        Exception: VirtServerError.
        
        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)  

        desc = self.__get_vm_description(name, id)
        
        try:
            files = []
            for item in desc['devices']['disk']:
                # get only disk type
                if item['device'] == 'disk':
                    files.append({'key': None,
                                  'name': item['source']['file'],
                                  'size': None,
                                  'type': None})
        except KeyError as ex:
            raise VirtServerError(ex)
        return files

    def vm_network(self, name=None, id=None):
        """ 
        TO-DO: get active
        
        Exception: VirtServerError.
        
        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)        
        
        desc = self.__get_vm_description(name, id)
        
        try:
            # if net_list is not a list create one
            net_list = desc['devices']['interface']
            if type(net_list) is not types.ListType:
                net_list = [net_list]

            interfaces = []
            for item in net_list:
                name = item['target']['dev']
                active = True
                mac = item['mac']['address']
                # create interface
                interface = Interface(name, active, mac)
                interface.set_param('alias', item['alias']['name'])
                interface.set_param('bridge', item['source']['bridge'])
                interface.set_param('driver', item['model']['type'])
                # add interface to list
                interfaces.append(interface)
                
            return interfaces
        except KeyError, ex:
            raise VirtServerError(ex)

    def vm_device(self, name=None, id=None):
        """
        Exception: VirtServerError.
        
        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        if self.conn is None:
            raise VirtServerError('No connection to libvirt %s host found' %
                                 self.id)          
        
        desc = self.__get_vm_description(name, id)
        return desc['devices']
    
    def vm_stats(self, name=None, id=None):
        """ 
        Exception: VirtServerError.
        
        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        pass    
    
    def __get_vm_description(self, name=None, id=None):
        """ Get virtual machine description. Specify at least name or id.
        
        Exception: VirtServerError.
        
        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        try:
            if name != None:
                dom = self.conn.lookupByName(name)
            elif id != None:
                dom = self.conn.lookupByName(id)
            data = xml2dict(dom.XMLDesc(8))
            return data
        except libvirt.libvirtError, ex:
            raise VirtServerError(ex)
    
    def __get_vm_info(self, dom):
        """ 
        info : {state, maxMem, memory, nrVirtCpu, cpouTime}
        
        XMLDesc flags:
        1 VIR_DOMAIN_XML_SECURE     dump security sensitive information too
        2 VIR_DOMAIN_XML_INACTIVE   dump inactive domain information
        4 VIR_DOMAIN_XML_UPDATE_CPU update guest CPU requirements according to host CPU
        8 VIR_DOMAIN_XML_MIGRATABLE dump XML suitable for migration       
        
        TO_DO get machine type: vm or template 
        TO-DO get cpu socket num and frequency
        TO-DO set status
        """
        infos = dom.info()
        ext_infos = xml2dict(dom.XMLDesc(8))
        # example: x86_64
        os_arch = ext_infos['os']['type']['arch']
        # example: rhel6.4.0
        os_machine = ext_infos['os']['type']['machine']
        # example: 5902
        vnc_port = ext_infos['devices']['graphics']['port']
        
        # create vm
        vm = VirtualMachine(dom.name(), 
                            dom.UUIDString(), 
                            os_machine+'-'+os_arch, 
                            None)
        #vm.set_status(vm_state[vm.get_status()])
        vm.set_port('vnc', vnc_port)
        vm.resource.set_cpu(infos[3], 0, 0)
        vm.resource.set_memory_max(infos[2])
            
        return vm