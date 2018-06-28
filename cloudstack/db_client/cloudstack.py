'''
Created on Jan 31, 2014

@author: darkbk
'''
import logging
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from .base import Base

class Asym_encrypt(Base):
    __tablename__ = 'asym_encrypt'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    seckey = Column(String(30), nullable=False)
    pubkey = Column(String(30), nullable=False)
    
class Simple_auth(Base):
    __tablename__ = 'simple_auth'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    username = Column(String(30), nullable=False)
    password = Column(String(30), nullable=False)

class Host_type(Base):
    """vSphere vCenter, esxi, qemu-kvm, xen, hyperv """
    __tablename__ = 'host_type'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    type = Column(String(10), nullable=False)

class Host(Base):
    __tablename__ = 'host'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    id = Column(Integer, primary_key=True)
    alias = Column(String(30), nullable=False)
    ip = Column(String(30), nullable=False)
    type_id = Column(Integer, ForeignKey('host_type.id'))
    type = relationship('Host_type')
    description = Column(String(100), nullable=True)
    auth_id = Column(Integer, ForeignKey('simple_auth.id'))
    auth = relationship('Simple_auth')
    encryption_id = Column(Integer, ForeignKey('asym_encrypt.id'))
    encryption = relationship('Asym_encrypt')
    
    def __init__(self, alias, ip, type, description, auth=None, encryption=None):
        self.alias = alias
        self.ip = ip
        self.type = type
        self.description = description
        if auth: self.auth = auth
        if encryption: self.encryption = encryption

    def __repr__(self):
        return "Host(%s, %s, %s)" % (self.id, self.alias, self.ip, self.type)