'''
Created on Dec 9, 2013

@author: darkbk
'''
import libvirt
import libvirt_qemu
import logging
import ujson as json
from xml.dom.minidom import parseString
from beecell.xml_parser import xml2dict
from beecell.simple import random_password
from beecell.perf import watch

try:
    import gevent
    import gevent.monkey
    # apply monkey patch
    gevent.monkey.patch_all()    
except:
    pass

class VirtDomainError(Exception): pass
class VirtDomain(object):
    """ """
    logger = logging.getLogger('gibbon.cloud.virt')
    
    def __init__(self, server, name=None, domain_id=None):
        """
        :param server: instance of KvmServer
        """
        # open connection to libvirt server if it isn't already open
        self._server = server
        if server.ping():
            self.conn = server.conn
        else:
            self.conn = server.connect()
        
        self._name = name
        self._domain = self._get_domain(name=name, domain_id=domain_id)
        
    @property
    def domain(self):
        """Get domain."""
        return self._domain    

    def switch(self):
        try:
            if self._server.async is True:
                gevent.sleep(0.01)  #10E-9
        except Exception as ex:
            print 'gevent switch error: %s' % ex
            pass

    def _get_domain(self, name=None, domain_id=None):
        """ Get virtual machine domain object. Specify at least name or did.
        
        Exception: VirtDomainError.
        
        :param name: [optional] name of virtual machine
        :param did: [optional] id of virtual machine
        """
        try:
            if name != None:
                domain = self.conn.lookupByName(name)
            elif domain_id != None:
                domain = self.conn.lookupByNamtoprettyxmle(domain_id)
            self.switch()
            
            self.logger.debug('Get libvirt domain: %s' % name)
            return domain
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    @watch
    def info(self):
        """ Get virtual machine description. Specify at least name or id.
        
        Exception: VirtDomainError.
        
        :param name: [optional] name of virtual machine
        :param id: [optional] id of virtual machine
        """
        #try:
        if True:
            data = xml2dict(self._domain.XMLDesc(8))
            self.switch()
            #data = xml2dict(self._domain.XMLDesc())
            self.logger.debug('Get libvirt domain info: %s' % self._name)
            #st = None
            #st = libvirt.virStream(self.conn)
            #print st.connect()
            #st = self.conn.newStream(flags=libvirt.VIR_STREAM_NONBLOCK)
            #st.connect()
            #print st
            #print self._domain
            #'org.qemu.guest_agent.0'
            #print self._domain.openChannel('charchannel1', st, flags=libvirt.VIR_DOMAIN_CHANNEL_FORCE)
            #st.finish()
            #self._domain.reboot(libvirt.VIR_DOMAIN_SHUTDOWN_GUEST_AGENT)
            #self._domain.shutdownFlags(libvirt.VIR_DOMAIN_SHUTDOWN_GUEST_AGENT)
            return data
        #except libvirt.libvirtError, ex:
        #    self.logger.error(ex)
        #    raise VirtDomainError(ex)

    def monitor(self):
        print self._domain.numaParameters()
        print self._domain.memoryStats()
        print self._domain.maxMemory()
        print self._domain.maxVcpus()

    def _get_xml_description(self):
        """ Get virtual machine description.
        
        Exception: VirtDomainError.
        
        :param domain: libvirt domain
        """
        try:
            data = self._domain.XMLDesc(8)
            self.switch()
            return parseString(data)
        except Exception, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    @watch
    def print_xml_description(self):
        """ Get virtual machine description.
        
        Exception: VirtDomainError.
        
        :param domain: libvirt domain
        """
        try:
            data = self._domain.XMLDesc(8)
            self.switch()
            return data
        except Exception, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _append_device_spice_graphics(self, xml_desc):
        """Append configuration for spice display
            TODO : tlsPort='-1'  unsupported configuration: spice secure channels set in XML configuration, but TLS is disabled in qemu.conf
            "<channel name='main' mode='secure'/>",
        """
        try:
            password = random_password()
            # TODO to add tlsPort='-1' you must configure tls in /etc/libvirt/qemu.conf
            data = ["<graphics type='spice' port='-1' autoport='yes' passwd='%s'>" % password,
                    #"<channel name='main' mode='secure'/>", to use configure tls
                    "<image compression='auto_glz'/>",
                    "<streaming mode='filter'/>",
                    "<clipboard copypaste='yes'/>",
                    "<mouse mode='client'/>",
                    "<filetransfer enable='yes'/>",
                    "<listen type='address' address='0.0.0.0'/>",
                    "</graphics>"]         
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            graphic_device = devices_tag.getElementsByTagName("graphics")[0]
            #print devices_tag.toxml
            devices_tag.removeChild(graphic_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)          
    
    def _append_device_vnc_graphics(self, xml_desc):
        """Append configuration for spice display
        """
        try:
            data = ["<graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0' password='mypass'>",
                    "<listen type='address' address='0.0.0.0'/>",
                    "</graphics>"]
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            graphic_device = devices_tag.getElementsByTagName("graphics")[0]
            #print devices_tag.toxml()
            devices_tag.removeChild(graphic_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
    
    def _append_device_video_cirrus(self, xml_desc):
        """Append configuration for spice display
              
        """
        try:
            data = ["<video>",
                    "<model type='cirrus' vram='8192' heads='1'/>",
                    "<acceleration accel3d='yes' accel2d='yes'/>",
                    #"<alias name='video0'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>",
                    "</video>"]
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            video_device = devices_tag.getElementsByTagName("video")[0]
            devices_tag.removeChild(video_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)      

    def _append_device_video_qxl(self, xml_desc):
        """Append configuration for spice display
        """
        try:
            data = ["<video>",
                    "<model type='qxl' vram='131072' heads='1'/>",
                    #"<alias name='video0'/>",
                    "<acceleration accel3d='yes' accel2d='yes'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>",
                    "</video>"]
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            video_device = devices_tag.getElementsByTagName("video")[0]
            devices_tag.removeChild(video_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)      

    def _append_device_video_vmware(self, xml_desc):
        """Append configuration for spice display
        """
        try:
            data = ["<video>",
                    "<model type='vmware'/>",
                    "</video>"]
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            video_device = devices_tag.getElementsByTagName("video")[0]
            devices_tag.removeChild(video_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex) 

    def _append_device_channel_unix(self, xml_desc):
        """Append configuration for spice display
        """
        #try:
        if True:
            agent_name = xml_desc.getElementsByTagName("name")[0].firstChild.data

            #"<address type='virtio-serial' controller='0' bus='0' port='1'/>",
            data = ["<channel type='unix'>",
                    "<source mode='bind' path='/var/lib/libvirt/qemu/%s.agent'/>" % agent_name,
                    "<target type='virtio' name='org.qemu.guest_agent.0'/>",
                    "<alias name='channel0'/>",
                    "</channel>"]
            serial_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("Errorimage")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            #graphic_device = devices_tag.getElementsByTagName("graphics")[0]
            #print devices_tag.toxml()
            #devices_tag.removeChild(graphic_device)
            devices_tag.appendChild(serial_device)
            
            return xml_desc
        #except Exception as ex:
        #    self.logger.error(ex)
        #    raise VirtDomainError(ex)      

    def _append_device_channel_spicevmc(self, xml_desc):
        """Append configuration for spice display
        
        """
        try:
            agent_name = xml_desc.getElementsByTagName("name")[0]
            
            data = ["<channel type='spicevmc'>",
                    "<target type='virtio' name='com.redhat.spice.0'/>",
                    "</channel>"]
            device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            devices_tag.appendChild(device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)  

    def _append_device_usb_redirect(self, xml_desc):
        """Append configuration for spice display
        
        :param alias: value like redir0, redir1. Be careful to use different 
                      alias for every device.
        """
        device_num = 3
        try:
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            usbr_device = devices_tag.getElementsByTagName("redirdev")

            dev_num = len(usbr_device)
            # there are existing usbredir devices
            data = []
            if dev_num > 0:
                # TODO delete all redirdev
                pass
            
            # create new devices
            for i in range(0, device_num):
                alias = 'redir%s' % str(i)
                data = ["<redirdev bus='usb' type='spicevmc'>",
                        "<alias name='%s'/>" % alias,
                        "</redirdev>"]
            
                usbr_device = parseString(''.join(data)).documentElement
                #print new_device.getElementsByTagName("image")
                #devices_tag.removeChild(graphic_device)
                devices_tag.appendChild(usbr_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)      

    def _append_device_usb2_controller(self, xml_desc):
        """Append configuration for spice display
        
        :param alias: value like redir0, redir1. Be careful to use different 
                      alias for every device.
        """
        try:
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            cotroller_usb_nodes = devices_tag.getElementsByTagName("controller")
            
            # remove existing controllor with type = 'usb'
            for item in cotroller_usb_nodes:
                controlle_type = item.getAttribute('type')
                if controlle_type == 'usb':
                    devices_tag.removeChild(item)
            
            # first usb controller
            data = ["<controller type='usb' index='0' model='ich9-ehci1'>",
                    "<alias name='usb0'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x7'/>",
                    "</controller>"]
            usb_controller = parseString(''.join(data)).documentElement
            devices_tag.appendChild(usb_controller)
                         
            # second usb controller
            data = ["<controller type='usb' index='0' model='ich9-uhci1'>",
                    "<alias name='usb0'/>",
                    "<master startport='0'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0' multifunction='on'/>",
                    "</controller>"]
            usb_controller = parseString(''.join(data)).documentElement
            devices_tag.appendChild(usb_controller)                      

            # third usb controller
            data = ["<controller type='usb' index='0' model='ich9-uhci2'>",
                    "<alias name='usb0'/>",
                    "<master startport='2'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x1'/>",
                    "</controller>"]
            usb_controller = parseString(''.join(data)).documentElement
            devices_tag.appendChild(usb_controller) 

            # fourth usb controller
            data = ["<controller type='usb' index='0' model='ich9-uhci3'>",
                    "<alias name='usb0'/>",
                    "<master startport='4'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x2'/>",
                    "</controller>"]
            usb_controller = parseString(''.join(data)).documentElement
            devices_tag.appendChild(usb_controller) 

            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _append_device_sound_card_ac97(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            data = ["<sound model='ac97'>",
                    "<alias name='sound0'/>",
                    #"<address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>",
                    "</sound>"]
            new_device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            sound_device = devices_tag.getElementsByTagName("sound")
            if len(sound_device) > 0:
                devices_tag.removeChild(sound_device[0])
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _append_device_sound_card_es1370(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            data = ["<sound model='es1370'>",
                    "<alias name='sound0'/>",
                    #"<address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>",
                    "</sound>"]
            new_device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            sound_device = devices_tag.getElementsByTagName("sound")
            if len(sound_device) > 0:
                devices_tag.removeChild(sound_device[0])
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
        
    def _append_device_sound_card_sb16(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            data = ["<sound model='sb16'>",
                    "<alias name='sound0'/>",
                    #"<address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>",
                    "</sound>"]
            new_device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            sound_device = devices_tag.getElementsByTagName("sound")
            if len(sound_device) > 0:
                devices_tag.removeChild(sound_device[0])
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _append_device_sound_card_ich6(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            data = ["<sound model='ich6'>",
                    "<alias name='sound0'/>",
                    #"<address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>",
                    "</sound>"]
            new_device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            sound_device = devices_tag.getElementsByTagName("sound")
            if len(sound_device) > 0:
                devices_tag.removeChild(sound_device[0])
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
    
    def _change_interface_model(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            interface_devices = devices_tag.getElementsByTagName("interface")
            if len(interface_devices) > 0:
                for dev in interface_devices:
                    # get only interface of type bridge
                    if dev.getAttribute('type') == 'bridge':
                        model = dev.getElementsByTagName('model')[0]
                        model.setAttribute('type', 'virtio')
                    
                        # remove bandwidth tag
                        bandwidth = dev.getElementsByTagName('bandwidth')
                        if bandwidth:
                            dev.removeChild(bandwidth[0])
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _change_disk_bus(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            disk_devices = devices_tag.getElementsByTagName("disk")
            if len(disk_devices) > 0:
                for dev in disk_devices:
                    # get only disk device. Exclude other disk type like cdrom
                    if dev.getAttribute('device') == 'disk':
                        # create new disk target
                        new_target = parseString("<target dev='vda' bus='virtio'/>").documentElement
                        old_target = dev.getElementsByTagName("target")[0]
                        dev.replaceChild(new_target, old_target)
                        
                        # create new disk alias
                        #new_alias = parseString("<alias name='virtio-disk0'/>").documentElement
                        #old_alias = dev.getElementsByTagName("alias")[0]
                        #dev.replaceChild(new_alias, old_alias)
                    
                        # remove disk address
                        address = dev.getElementsByTagName('address')
                        if address:
                            dev.removeChild(address[0])
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    @watch    
    def change_graphics_password(self, password):
        """Append configuration for spice display
              
        """
        try:
            # get graphics device type
            xml_desc = self._get_xml_description()
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            graphic_device = devices_tag.getElementsByTagName("graphics")[0]
            graphic_type = graphic_device.attributes['type'].value
            
            if graphic_type == 'spice':
                # TODO to add tlsPort='-1' you must configure tls in /etc/libvirt/qemu.conf
                data = ["<graphics type='spice' port='-1' autoport='yes' passwd='%s'>" % password,
                        #"<channel name='main' mode='secure'/>", to use configure tls
                        "<image compression='auto_glz'/>",
                        "<streaming mode='filter'/>",
                        "<clipboard copypaste='yes'/>",
                        "<mouse mode='client'/>",
                        "<filetransfer enable='yes'/>",
                        "<listen type='address' address='0.0.0.0'/>",
                        "</graphics>"]
                #new_device = parseString(''.join(data)).documentElement
                xml = ''.join(data)              
                self._domain.updateDeviceFlags(xml, flags=0)
            self.switch()
            self.logger.debug('Change password of graphics devices %s for libvirt domain: %s' % (
                                graphic_type, self._name))                
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)  

    @watch    
    def destroy(self):
        """Destroy domain.
        
        :param domain: libvirt domain
        """
        try:
            data = self._domain.destroy()
            self.switch()
            self.logger.debug('Destroy libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    @watch
    def start(self):
        """Start domain.
        """
        try:
            data = self._domain.create()
            self.switch()
            self.logger.debug('Start libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    @watch
    def reboot(self):
        """Reboot domain.  
        """
        try:
            data = self._domain.reboot(libvirt.VIR_DOMAIN_SHUTDOWN_GUEST_AGENT)
            self.switch()
            self.logger.debug('Reboot libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    @watch        
    def shutdown(self):
        """Shutdown domain.   
        """
        try:
            data = self._domain.shutdownFlags(libvirt.VIR_DOMAIN_SHUTDOWN_GUEST_AGENT)
            self.switch()
            self.logger.debug('Shutdown libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    @watch
    def define(self, xml_desc):
        """Define domain form xml descriptor.
        
        :param xml_desc: domain xml descriptor
        """
        try:
            dom = self.conn.defineXML(xml_desc)
            self.switch()
            self.logger.debug('Define libvrit domain: %s' % self._domain)
            return dom
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)            

    @watch
    def undefine(self, domain):
        """Undefine domain.

        :param domain: libvirt domain        
        """        
        try:
            data = self._domain.undefine()
            self.switch()
            self.logger.debug('Undefine libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    @watch
    def append_device(self, devices):
        """
        
        :param device: device like : spice_graphics, vnc_graphics, rdp_graphics
                                     video_cirrus, video_qxl,
                                     virtio_serial, usb_redirect,
                                     sound_card, 
        """
        # get xml description of domain
        xml_desc = self._get_xml_description()        
        
        # default device to always append
        xml_desc2 = self._append_device_channel_spicevmc(xml_desc)
        xml_desc2 = self._append_device_usb2_controller(xml_desc)
        
        # change default device model (desk, network) to virtio
        xml_desc2 = self._change_interface_model(xml_desc)
        #xml_desc2 = self._change_disk_bus(xml_desc)
        
        if devices and len(devices) > 0:
            # append devices configuration
            for device in devices:
                if device == 'spice_graphics':
                    xml_desc2 = self._append_device_spice_graphics(xml_desc)
                elif device == 'vnc_graphics':
                    xml_desc2 = self._append_device_vnc_graphics(xml_desc)
                elif device == 'video_cirrus':
                    xml_desc2 = self._append_device_video_cirrus(xml_desc)
                elif device == 'video_qxl':
                    xml_desc2 = self._append_device_video_qxl(xml_desc)
                elif device == 'video_vmware':
                    xml_desc2 = self._append_device_video_vmware(xml_desc)                    
                elif device == 'virtio_serial':
                    xml_desc2 = self._append_device_channel_unix(xml_desc)
                elif device == 'usb_redirect':
                    xml_desc2 = self._append_device_usb_redirect(xml_desc)
                elif device == 'sound_card_ac97':
                    xml_desc2 = self._append_device_sound_card_ac97(xml_desc)
                elif device == 'sound_card_es1370':
                    xml_desc2 = self._append_device_sound_card_es1370(xml_desc)
                elif device == 'sound_card_sb16':
                    xml_desc2 = self._append_device_sound_card_sb16(xml_desc)
                elif device == 'sound_card_ich6':
                    xml_desc2 = self._append_device_sound_card_ich6(xml_desc)
            
            self.logger.debug('Append devices %s to libvirt domain: %s' % (
                                devices, self._domain))
            
        # destroy domain
        self.destroy()
        # define domain with new xml descriptor
        domain2 = self.define(xml_desc2.toxml())
        # start new domain
        res = self.start()
        
        self._domain = domain2

        return self._domain
    
    @watch
    def spice_connection_status(self):
        """Return spice connection channels
        
        :return: list of spice connection channels
        """
        try:
            stat = libvirt_qemu.qemuMonitorCommand(self._domain, 
                            '{ "execute": "query-spice" }', 
                            libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT)
            self.switch()
            data = json.loads(stat)['return']['channels']
            self.logger.debug('Get spice connection status: %s' % data)
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
            
        return data
    
    @watch
    def vnc_connection_status(self):
        """Return vnc connection channels
        
        :return: list of spice connection channels
        """
        try:
            stat = libvirt_qemu.qemuMonitorCommand(self._domain, 
                            '{ "execute": "query-vnc" }', 
                            libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT)
            self.switch()
            data = json.loads(stat)['return']['clients']
            self.logger.debug('Get spice connection status: %s' % data)
        except libvirt.libvirtError, ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
            
        return data    