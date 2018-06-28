'''
Created on Jan 31, 2014

@author: darkbk
'''
import logging
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .decorator import transaction, query
from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

try:
    from beecell.uwsgi_sys.perf import watch
except:
    from beecell.perf import watch
    
class VmInstance(Base):
    __tablename__ = 'vm_instance'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    uuid = Column(String(40), nullable=False)
    instance_name = Column(String(255), nullable=False)
    state = Column(String(32), nullable=False)
    vm_template_id = Column(Integer, nullable=False)
    guest_os_id = Column(Integer, nullable=False)
    private_mac_address = Column(String(50), nullable=False)
    private_ip_address = Column(String(50), nullable=False)
    pod_id = Column(Integer, nullable=False)
    data_center_id = Column(Integer, nullable=False)
    host_id = Column(Integer, nullable=False)
    last_host_id = Column(Integer, nullable=False)
    proxy_id = Column(Integer, nullable=False)
    proxy_assign_time = Column(String(50), nullable=False)
    vnc_password = Column(String(50), nullable=False)
    ha_enabled = Column(String(50), nullable=False)
    limit_cpu_use = Column(String(50), nullable=False)
    update_count = Column(String(50), nullable=False)
    update_time = Column(String(50), nullable=False)
    created = Column(String(50), nullable=False)
    removed = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    vm_type = Column(String(50), nullable=False)
    account_id = Column(Integer, nullable=False)
    domain_id = Column(Integer, nullable=False)
    service_offering_id = Column(Integer, nullable=False)
    reservation_id = Column(Integer, nullable=False)
    hypervisor_type = Column(String(50), nullable=False)
    disk_offering_id = Column(Integer, nullable=False)
    owner = Column(String(255), nullable=False)
    host_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    desired_state = Column(String(32), nullable=False)
    dynamically_scalable = Column(Integer, nullable=False)
    display_vm = Column(Integer, nullable=False)
    power_state = Column(String(74), nullable=False)
    power_state_update_time = Column(DateTime, nullable=False)
    power_state_update_count = Column(Integer, nullable=False)
    power_host = Column(Integer, nullable=False)

    def __init__(self, clsk_id, devices):
        self.clsk_id = clsk_id
        self.device = devices

    def __repr__(self):
        return "<VirtDomain(%s, %s, %s)>" % (self.id, self.clsk_id, self.device)

class VirtDomainDeviceType(Base):
    __tablename__ = 'vm_virt_domain_device_type'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    device = Column(String(30), nullable=False)
    
    def __init__(self, device):
        self.device = device

    def __repr__(self):
        return "<VirtDomainDeviceType(%s, %s)>" % (self.id, self.device)

class VirtDomainDevice(Base):
    __tablename__ = 'vm_virt_domain_device'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    vm_id = Column(Integer, ForeignKey('vm_virt_domain.id'))
    type_id = Column(Integer, ForeignKey('vm_virt_domain_device_type.id'))
    type = relationship('VirtDomainDeviceType')
    config = Column(String(100), nullable=True, default='')
    
    def __init__(self, type, config):
        self.config = config
        self.type = type

    def __repr__(self):
        return "<VirtDomainDevice(%s, %s, %s, %s)>" % (self.id, self.vm_id, 
                                                       self.type, self.config)

class VirtDomain(Base):
    __tablename__ = 'vm_virt_domain'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    clsk_id = Column(String(50), nullable=False, unique=True)
    device = relationship('VirtDomainDevice')
    
    def __init__(self, clsk_id, devices):
        self.clsk_id = clsk_id
        self.device = devices

    def __repr__(self):
        return "<VirtDomain(%s, %s, %s)>" % (self.id, self.clsk_id, self.device)

class VmManagerError(Exception): pass
class VmManager(object):
    """
    """
    logger = logging.getLogger('gibbon.cloud.db')
    
    def __init__(self, session):
        """ """
        self._session = session
    
    @staticmethod
    def create_table(db_uri):
        """Create all tables in the engine. This is equivalent to "Create Table"
        statements in raw SQL."""
        try:
            engine = create_engine(db_uri)
            Base.metadata.create_all(engine)
            del engine
        except exc.DBAPIError, e:
            raise VmManagerError(e)
    
    @staticmethod
    def remove_table(db_uri):
        """ Remove all tables in the engine. This is equivalent to "Drop Table"
        statements in raw SQL."""
        try:
            engine = create_engine(db_uri)
            Base.metadata.drop_all(engine)
            del engine
        except exc.DBAPIError, e:
            raise VmManagerError(e)

    @watch
    def set_initial_data(self):
        """Set initial data.
        """
        @transaction(self._session)
        def set_initial_data_inner(session):
            data = [VirtDomainDeviceType(device='spice_graphics'),
                    VirtDomainDeviceType(device='vnc_graphics'),
                    VirtDomainDeviceType(device='rdp_graphics'),
                    VirtDomainDeviceType(device='video_cirrus'),
                    VirtDomainDeviceType(device='video_qxl'),
                    VirtDomainDeviceType(device='virtio_serial'),
                    VirtDomainDeviceType(device='usb_redirect'),
                    VirtDomainDeviceType(device='sound_card_ac97'),
                    VirtDomainDeviceType(device='sound_card_es1370'),
                    VirtDomainDeviceType(device='sound_card_sb16'),
                    VirtDomainDeviceType(device='sound_card_ich6'),]
            
            session.add_all(data)
        return set_initial_data_inner()
    
    def get_device_type(self, name):
        @query(self._session)
        def get_device_type_inner(session):
            device = session.query(VirtDomainDeviceType)\
                            .filter_by(device=name).first()
            return device
        return get_device_type_inner()
    
    def get_virt_domain(self, clsk_id):
        """Get Virtual Machine reference.
        
        :param clsk_id: Cloudstack Virtual Machine id
        :type clsk_id: str
        :return: Virtual machine running status.
        :rtype: str
        :raises ClskObjectError: raise :class:`.base.ClskObjectError`        
        """
        @query(self._session)
        def get_virt_domain_inner(session):
            vm = session.query(VirtDomain).filter_by(clsk_id=clsk_id)
            if vm.count() > 0:
                devs = {}
                for device in vm.first().device:
                    devs[device.type.device] = device.config
                data = {'id':clsk_id, 'devices':devs}
            else:
                data = None
            
            self.logger.debug('Get virt domain: %s' % data)
            return data
        return get_virt_domain_inner()

    def add_virt_domain(self, clsk_id, devices):
        """Add Virtual Machine reference
        
        :param clsk_id: Cloudstack Virtual Machine id
        :type clsk_id: str
        :param devices: dict of libvirt devices to set. Es. {'spice':'password:testlab,'}
        """
        @transaction(self._session)
        def add_virt_domain_inner(session):
            virt_devices = []
            for device, config in devices.iteritems():
                vir_type = session.query(VirtDomainDeviceType)\
                                  .filter_by(device=device).first()
                virt_devices.append(VirtDomainDevice(vir_type, config))
            data = VirtDomain(clsk_id, virt_devices)
            session.add(data)
            
            self.logger.debug('Add virt domain %s with devices %s' % (clsk_id, devices))
        return add_virt_domain_inner()

    def delete_virt_domain(self, clsk_id):
        """Delete Virtual Machine reference
        
        :param clsk_id: Cloudstack Virtual Machine id
        :type clsk_id: str
        """
        @transaction(self._session)
        def delete_virt_domain_inner(session):
            vm = session.query(VirtDomain).filter_by(clsk_id=clsk_id)
            if vm.count() > 0:
                for device in vm.first().device:
                    session.delete(device)            
                session.delete(vm.first())
                
            self.logger.debug('Delete virt domain: %s' % clsk_id)
        return delete_virt_domain_inner()

    def append_virt_domain_devices(self, clsk_id, devices):
        """Append devices to Virtual Machine
        
        :param clsk_id: Cloudstack Virtual Machine id
        :type clsk_id: str
        :param devices: dict of libvirt devices to set. Es. {'spice':'password:testlab,'}
        """
        @transaction(self._session)
        def append_virt_domain_devices_inner(session):
            virt_devices = []
            for device, config in devices.iteritems():
                vir_type = session.query(VirtDomainDeviceType)\
                                  .filter_by(device=device).first()
                virt_devices.append(VirtDomainDevice(vir_type, config))
            vm = session.query(VirtDomain).filter_by(clsk_id=clsk_id)
            vm.first().device = virt_devices
            #data = VirtDomain(clsk_id, virt_devices)
            #session.add(data)
            
            self.logger.debug('Append devices %s to virt domain %s' % (devices, clsk_id))
        return append_virt_domain_devices_inner()

    def delete_virt_domain_devices(self, clsk_id):
        """Delete Virtual Machine devices
        
        :param clsk_id: Cloudstack Virtual Machine id
        :type clsk_id: str
        """
        @transaction(self._session)
        def delete_virt_domain_devices_inner(session):
            vm = session.query(VirtDomain).filter_by(clsk_id=clsk_id)
            if vm.count() > 0:
                for device in vm.first().device:
                    session.delete(device)
                
            self.logger.debug('Delete virt domain devices: %s' % clsk_id)
        return delete_virt_domain_devices_inner()

    def update_graphic_password(self, clsk_id, password):
        """Update Virtual Machine grachic password
        
        :param clsk_id: Cloudstack Virtual Machine id
        :type clsk_id: str
        :param password: Virtual Machine grachic password
        :type password: str                
        """
        @transaction(self._session)
        def update_graphic_password_inner(session):
            #vm = session.query(VirtDomain).filter_by(vm_id=vm_id)
            dev = session.query(VirtDomain, VirtDomainDevice, VirtDomainDeviceType).\
                filter(VirtDomain.id==VirtDomainDevice.vm_id).\
                filter(VirtDomainDeviceType.id==VirtDomainDevice.type_id).\
                filter(VirtDomainDeviceType.device.like('%_graphics')).\
                filter(VirtDomain.clsk_id==clsk_id)
            if dev.count() > 0:
                dev = dev.first()
                dev[1].config = 'password:%s' % password
                return True
            else:
                return False
            
            self.logger.debug('Update virt domain graphic password: %s' % clsk_id)
        return update_graphic_password_inner()