'''
Created on Jul 26, 2013

@author: darkbk

Integer    an integer
String (size)    a string with a maximum length
Text    some longer unicode text
DateTime    date and time expressed as Python datetime object.
Float    stores floating point values
Boolean    stores a boolean value
PickleType    stores a pickled Python object
LargeBinary    stores large arbitrary binary data
'''
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text

Base = declarative_base()

class VmInstances(Base):
    __tablename__ = 'vm_instance'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    uuid = Column(String(40))
    instance_name = Column(String(255))
    state = Column(String(32))
    vm_template_id = Column(Integer)
    guest_os_id = Column(Integer)
    private_mac_address = Column(String(17))
    private_ip_address = Column(String(40))
    pod_id = Column(Integer)
    data_center_id = Column(Integer)
    host_id = Column(Integer)
    last_host_id = Column(Integer)
    proxy_id = Column(Integer)
    proxy_assign_time = Column(DateTime)
    vnc_password = Column(String(255))
    ha_enabled = Column(Integer)
    limit_cpu_use = Column(Integer)
    update_count = Column(Integer)
    update_time = Column(DateTime)
    created = Column(DateTime)
    removed = Column(DateTime)
    type = Column(String(32))
    vm_type = Column(String(32))
    account_id = Column(Integer)
    domain_id = Column(Integer)
    service_offering_id = Column(Integer)
    reservation_id = Column(String(40))
    hypervisor_type = Column(String(32))
    disk_offering_id = Column(Integer)
    cpu = Column(Integer)
    ram = Column(Integer)
    owner = Column(String(255))
    speed = Column(Integer)
    host_name = Column(String(255))
    display_name = Column(String(255))
    desired_state = Column(String(32))

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<Volume ('%s','%s')>" % (self.id, self.name)

class Volumes(Base):
    __tablename__ = 'volumes'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer)
    domain_id = Column(Integer)
    pool_id = Column(Integer)
    last_pool_id = Column(Integer)
    instance_id = Column(Integer)
    device_id = Column(Integer)
    name = Column(String(255))
    uuid = Column(String(40))
    size = Column(Integer)
    folder = Column(String(255))
    path = Column(String(255))
    pod_id = Column(Integer)
    data_center_id = Column(Integer)
    iscsi_name = Column(String(255))
    host_ip = Column(String(40))
    volume_type = Column(String(64))
    pool_type = Column(String(64))
    disk_offering_id = Column(Integer)
    template_id = Column(Integer)
    first_snapshot_backup_uuid = Column(String(255))
    recreatable = Column(Integer)
    created = Column(DateTime)
    attached = Column(DateTime)
    updated = Column(DateTime)
    removed = Column(DateTime)
    state = Column(String(32))
    chain_info = Column(Text)
    update_count = Column(Integer)
    disk_type = Column(String(255))

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<Volume ('%s','%s', '%s')>" % (self.id, self.name, self.path)
    




