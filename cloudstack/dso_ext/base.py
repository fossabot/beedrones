'''
Created on Dec 24, 2013

@author: darkbk
'''
import logging
from sqlalchemy import create_engine, exc, event
from sqlalchemy.pool import Pool
from sqlalchemy.orm import sessionmaker
from gibboncloud.cloudstack.dso.base import ApiClient
from gibboncloud.virt.manager import VirtServer, VirtServerError

class ApiManagerError(Exception): pass

class MysqlConnectionManager(object):
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, mid, host, port, name, user, pwd):
        """
        :param api_params: dict with {uri, api_key, sec_key}
        """
        self.id = mid
        # mysql db connection params
        self.db_host = host
        self.db_port = port
        self.db_name = name
        self.db_user = user
        self.db_pwd = pwd
        
        # create engine
        self.engine = None
        self.db_session = None
        
        try:
            conn_string = 'mysql+mysqldb://%s:%s@%s:%s/%s' % (
                          user, pwd, host, port, name)
            self.engine = create_engine(conn_string,
                                        pool_size=10, 
                                        max_overflow=10,
                                        pool_recycle=3600)
            self.logger.debug('Created new connection pool engine : %s' % self.engine)
            
            self.db_session = sessionmaker(bind=self.engine, 
                                           autocommit=False, 
                                           autoflush=False,)
            self.logger.debug('Created new db session over engine : %s' % self.db_session)
        except exc.DBAPIError:
            ApiManagerError('Connection error to mysql+mysqldb://%s:%s@%s:%s/%s' % (
                            user, "xxxx", host, port, name))
            
        """Setup simple query for every connection checkout to verify that db answer 
        correctly"""
        @event.listens_for(Pool, "checkout")
        def ping_connection(dbapi_connection, connection_record, connection_proxy):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("SELECT 1")
            except:
                # optional - dispose the whole pool
                # instead of invalidating one at a time
                # connection_proxy._pool.dispose()
        
                # raise DisconnectionError - pool will try
                # connecting again up to three times before raising.
                raise exc.DisconnectionError()
            cursor.close()
    
    def get_engine(self):
        return self.engine
    
    def get_conn(self):
        try:
            if self.engine:
                conn = self.engine.connect()
                #self.logger.debug("Get connection %s from poll %s." % (conn, self.engine))
                return conn
            ApiManagerError("There isn't active engine to use. Connection can \
                             not be opened.")            
        except exc.DBAPIError, e:
            # an exception is raised, Connection is invalidated. Connection 
            # pool will be refresh
            if e.connection_invalidated:
                self.logger.debug("Connection was invalidated!")
                raise ApiManagerError("Connection was invalidated! Try to reconnect")
    
    def release_conn(self, conn):
        conn.close()
        #self.logger.debug("Release connection %s to poll %s." % (conn, self.engine))
        
    def get_session(self):
        """
        Correct use of session object:
        
        def run_my_program():
            session = Session()
            try:
                ThingOne().go(session)
                ThingTwo().go(session)
        
                session.commit()
            except:
                session.rollback()
                raise
            finally:
                session.close()
        """
        try:
            #conn = self.get_conn()
            if self.db_session:
                session = self.db_session()#bind=conn)
                # workaround when use sqlalchemy and flask-sqlalchemy
                session._model_changes = {}
                self.logger.debug("Open session: %s" % (session))
                return session
            ApiManagerError("There isn't active db session to use. Session can \
                             not be opened.")            
        except exc.DBAPIError, e:
            # an exception is raised, Connection is invalidated. Connection 
            # pool will be refresh
            if e.connection_invalidated:
                self.logger.debug("Connection was invalidated!")
                return self.engine.connect()
            
    def release_session(self, session):
        #conn = session.connection()
        session.close()
        self.logger.debug("Release session %s." % (session))
        #self.logger.debug("Release connection %s to poll %s." % (conn, self.engine))

class QemuConnectionManager(object):
    logger = logging.getLogger('gibboncloud')
    
    def __init__(self, hid, host, port):
        """
        :param api_params: dict with {uri, api_key, sec_key}
        """
        self.id = hid
        # mysql db connection params
        self.host = host
        self.port = port

    def get_conn(self):
        try:
            conn_string = "qemu+tcp://%s:%s/system" % (self.host, self.port)
            conn = VirtServer(id, conn_string)
            conn.connect()
            self.logger.debug('Get libvirt-qemu server %s:%s connection: %s' % (
                self.host, self.port, conn))
            return conn
        except VirtServerError as e:
            raise ApiManagerError(e)
    
    def release_conn(self, conn):
        conn.disconnect()
        self.logger.debug('Release libvirt-qemu connection: %s' % (conn))

class ClskConnectionManager(object):
    logger = logging.getLogger('gibboncloud')
    
    def __init__(self, name, id, api_params, db_manager):
        """
        :param api_params: dict with {uri, api_key, sec_key}
        """
        self.name = name
        self.id = id
        # http api connection params
        self.uri = api_params['uri']
        self.api_key = api_params['api_key']
        self.sec_key = api_params['sec_key']
        # mysql db connection
        self.db_manager = db_manager
        # hypervisor list and connection params
        self.hypervisor = {'qemu':[],
                           'vsphere':[],
                           'xen':[],
                           'lxc':[]}
        
    def add_hypervisor(self, htype, h_manager):
        """
        :param htype: hypervisor type : qemu, vsphere, xen, lxc
        :param hid: id associated to hypervisor
        :param conn_params: connection params. 
                            Ex. qemu : qemu+tcp://10.102.47.205:15908/system
                                vsphere: vcenter_host, user, password
        """
        self.hypervisor[htype].append(h_manager)
        
    def remove_hypervisor(self, htype, hid):
        """
        :param htype: hypervisor type : qemu, vsphere, xen, lxc            
        :param hid: id associated to hypervisor
        """
        try:            
            hypervisor_list = self.hypervisor[htype]
            hypervisor = [item for item in hypervisor_list if item.id == hid][0]
            hypervisor_list.remove(hypervisor)
            return hypervisor
        except KeyError:
            raise ApiManagerError('Hypervisor %s of type %s not found' % (hid, htype))        

    def get_hypervisor(self, htype, hid):
        """
        :param htype: hypervisor type : qemu, vsphere, xen, lxc            
        :param hid: id associated to hypervisor
        """
        try:
            hypervisor_list = self.hypervisor[htype]
            hypervisor = [item for item in hypervisor_list if item.id == hid][0]
            return hypervisor
        except (KeyError, IndexError):
            raise ApiManagerError('Hypervisor %s of type %s not found' % (hid, htype))

    # api connection function
    def get_api_client(self):
        """ """
        api_client = ApiClient(self.uri, self.api_key, self.sec_key)
        self.logger.debug('Get cloudstack %s api client instance : %s' % (
            self.name, api_client))        
        return api_client

    # db connection function
    def get_db_conn(self):
        """ """
        return self.db_manager.get_conn()

    def release_db_conn(self, conn):
        """ """
        return self.db_manager.release_conn(conn)
    
    def get_db_session(self):
        """ """
        return self.db_manager.get_session()                     

    def release_db_session(self, session):
        """ """
        return self.db_manager.release_session(session)  

    # hypervisor connection function
    def get_hypervisor_conn(self, htype, hid):
        """
        :param htype: hypervisor type : qemu, vsphere, xen, lxc            
        :param hid: id associated to hypervisor
        """
        h_manager = self.get_hypervisor(htype, hid)
        return h_manager.get_conn()
    
    def release_hypervisor_conn(self, htype, hid, conn):
        """
        :param htype: hypervisor type : qemu, vsphere, xen, lxc            
        :param hid: id associated to hypervisor
        """
        h_manager = self.get_hypervisor(htype, hid)
        return h_manager.release_conn(conn)

class ApiManager(object):
    """
    TO-DO gestire le connessioni con un connection pool
    """
    logger = logging.getLogger('gibboncloud')
    
    def __init__(self):
        """
        """
        self.instances = {'clsk':[]}
        
        self.conn_pools = None

    def add_clsk_instance(self, clsk_manager):
        self.instances['clsk'].append(clsk_manager)
        self.logger.debug('Add cloudstack instance : %s, %s' % (
                clsk_manager.name, clsk_manager.uri))

    def get_clsk_instance(self, cid):
        """
        :param cid: id of cloudstack instance
        """
        try:
            instance = [item for item in self.instances['clsk'] if item.id == cid][0]
            return instance
        except KeyError:
            raise ApiManagerError('Cloudstack instance %s not found' % (cid))
        
    def get_all_clsk_instances(self):
        """ """
        return self.instances['clsk']