'''
Created on Sep 2, 2013

@author: darkbk
'''
import unittest
import time
import ujson as json
from gibbonutil.perf import watch_test
from tests.test_util import run_test, CloudTestCase
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from gibboncloud.virt.manager import VirtServer, VirtServerError
from gibboncloud.virt.domain import VirtDomain, VirtDomainError
from gibboncloud.virt import VirtManager

class VirtDomainTestCase(CloudTestCase):
    def setUp(self):
        CloudTestCase.setUp(self)
        #self.setup_cloudstack()
        
        #host = '172.16.0.19:16509'
        host = '10.102.90.3:16509'
        host = '10.102.86.23:16509'
        #host = 'clsk-kvm02.csi.it:16509'
        #host = '172.25.4.46:16509'
        host = '172.16.0.19:21509'
        host = '172.16.0.19:23509'
        host = '172.16.0.19:22509'
        host = 'clsk-kvm06.csi.it'
        #host = '10.102.86.24'
        #host = '10.102.86.23' 
        vm_name = 'i-14-92-VM'
        #vm_name = 'i-3-6-VM'
        #vm_name = 'i-3-11-VM'
        
        server = VirtServer(id, "qemu+tcp://%s/system" % host)
        self.virt_domain = VirtDomain(server, name=vm_name)
        
    def tearDown(self):
        CloudTestCase.tearDown(self)
        #self.session.close()
        # remove tables
        #ConfigManager.remove_table(self.db_uri)

    def test_info(self):
        self.pp.pprint(self.virt_domain.info())

    def test_monitor(self):
        #print self.virt_domain.monitor()
        #print self.virt_domain.domain.vcpus()
        
        #print self.virt_domain.domain.memoryStats()
        #print self.virt_domain.domain.maxMemory()
        #print self.virt_domain.domain.maxVcpus() 
        #print self.virt_domain.conn.getCPUStats(0)
        #print self.virt_domain.conn.getFreeMemory()
        #print self.virt_domain.conn.getMaxVcpus()
        #print self.virt_domain.conn.listNetworks()
        
        import libvirt_qemu
        #libvirt_qemu.qemuAgentCommand(domain, cmd, timeout, flags)
        
        #res = libvirt_qemu.qemuMonitorCommand(self.virt_domain.domain, '{ "execute": "query-commands" }', 
        #                                      libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT)
        #data = json.loads(res)
        #self.pp.pprint(data)

        print libvirt_qemu.qemuMonitorCommand(self.virt_domain.domain, '{ "execute": "query-vnc" }', 
                                              libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT)        
        #print libvirt_qemu.qemuMonitorCommand(self.virt_domain.domain, '{ "execute": "query-cpus" }', 
        #                                      libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT)


    def test_append_device(self):
        domain = self.virt_domain.domain
        #self.logger.debug(self.virt_domain.print_xml_description())
        '''
        spice_graphics, vlc_graphics, 
        video_cirrus, video_qxl, video_vmware
        virtio_serial, usb_redirect,
        sound_card,             
        '''
        devices = ['spice_graphics']
        domain2 = self.virt_domain.append_device(devices)
        #self.logger.debug(domain2)
        print self.virt_domain.print_xml_description()

    def test_change_graphics_password(self):
        self.virt_domain.change_graphics_password('test')
        
    def test_reboot(self):
        self.virt_domain.reboot()
        
    def test_spice_connection_status(self):
        self.virt_domain.spice_connection_status()

    def test_vnc_connection_status(self):
        self.virt_domain.vnc_connection_status()
            
def test_suite():
    tests = ['test_info',
             #'test_monitor',
             #'test_append_device',
             #'test_change_graphics_password',
             #'test_reboot',
             #'test_spice_connection_status',
             #'test_vnc_connection_status'
            ]
    return unittest.TestSuite(map(VirtDomainTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])           