'''
Created on Jan 31, 2014

@author: darkbk
'''
import logging
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .decorator import transaction, query

Base = declarative_base()

class VirtDomainDeviceType(Base):
    __tablename__ = 'vm_virt_domain_device_type'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    device = Column(String(30), nullable=False)
    
    def __init__(self, device):
        self.device = device

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

class VirtDomain(Base):
    __tablename__ = 'vm_virt_domain'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    clsk_id = Column(String(50), nullable=False)
    device = relationship('VirtDomainDevice')
    
    def __init__(self, clsk_id, devices):
        self.clsk_id = clsk_id
        self.device = devices

class VmModelManagerError(Exception): pass

class VmModelManager(object):
    """
    """
    logger = logging.getLogger('gibbon.cloud')
    
    def __init__(self, conn_manager):
        """ """
        self._conn_manager = conn_manager
    
    """Schema method """
    def create_table(self):
        # Create all tables in the engine. This is equivalent to "Create Table"
        # statements in raw SQL.
        engine = self._conn_manager.get_engine()
        Base.metadata.create_all(engine)

    def remove_table(self):

        # Remove all tables in the engine. This is equivalent to "Drop Table"
        # statements in raw SQL.
        engine = self._conn_manager.get_engine()
        Base.metadata.drop_all(engine)
    
    def populate_table(self):
        @transaction(self._conn_manager)
        def func(session):
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
            session.commit()
        return func()
    
    """Query method """
    def get_device_type(self, name):
        @query(self._conn_manager)
        def func(session):
            device = session.query(VirtDomainDeviceType).filter_by(name=name).first()
            return device
        return func()
    
    def get_vm(self, vm_id):
        @query(self._conn_manager)
        def func(session):
            vm = session.query(VirtDomain).filter_by(clsk_id=vm_id)
            if vm.count() > 0:
                devs = {}
                for device in vm.first().device:
                    devs[device.type.device] = device.config
                data = {'id':vm_id, 'devices':devs}
            else:
                data = None
            
            self.logger.debug('Get virt domain info from db: %s' % vm_id)
            return data
        return func()

    """Add method """
    def add_vm(self, vm_id, devices):
        """
        :param vm_id: cloudstack id of the virtual machine
        :param devices: dict of libvirt devices to set. Es. {'spice':'password:testlab,'}
        """
        @transaction(self._conn_manager)
        def func(session):
            virt_devices = []
            for device, config in devices.iteritems():
                type = session.query(VirtDomainDeviceType).filter_by(device=device).first()
                virt_devices.append(VirtDomainDevice(type, config))
            data = VirtDomain(vm_id, virt_devices)
            session.add(data)
            
            self.logger.debug('Add virt domain to db: %s' % vm_id)
        return func()

    """Update method """
    def update_graphic_password(self, vm_id, password):
        @transaction(self._conn_manager)
        def func(session):
            #vm = session.query(VirtDomain).filter_by(vm_id=vm_id)
            dev = session.query(VirtDomain, VirtDomainDevice, VirtDomainDeviceType).\
                filter(VirtDomain.id==VirtDomainDevice.vm_id).\
                filter(VirtDomainDeviceType.id==VirtDomainDevice.type_id).\
                filter(VirtDomainDeviceType.device.like('%_graphics'))
            
            if dev.count() > 0:
                dev = dev.first()
                dev[1].config = 'password:%s' % password
                return True
            else:
                return False
            
            self.logger.debug('Update virt domain graphic password to db: %s' % vm_id)
        return func()        

    """Delete method """
    def delete_vm(self, vm_id):
        """
        :param items: list of action like 'add', '*'
        """
        @transaction(self._conn_manager)
        def func(session):
            vm = session.query(VirtDomain).filter_by(clsk_id=vm_id)
            if vm.count() > 0:
                for device in vm.first().device:
                    session.delete(device)            
                session.delete(vm.first())
                
            self.logger.debug('Delte virt domain from db: %s' % vm_id)
        return func()