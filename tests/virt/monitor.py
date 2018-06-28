'''
Created on Feb 14, 2015

@author: darkbk
'''
import os
import time
import datetime
import psutil
import gevent
import gevent.monkey
# apply monkey patch
gevent.monkey.patch_all()
from memory_profiler import profile

from gibboncloud.virt.monitor import VirtDomainMonitor, VirtDomainMonitorError 

def monitor(virt_domain, delta):
    while True:
        virt_domain.tick()
        m = virt_domain.get_metrics()
        d = datetime.datetime.fromtimestamp(m[0])
        g = id(gevent.getcurrent())
        print g, virt_domain.name, d.strftime("%d-%m-%y %H:%M:%S"), m
        time.sleep(delta)    

def main():
    from gibboncloud.virt.manager import VirtServer
    
    """
    <memballoon model='virtio'>
      <alias name='balloon0'/>
      <stats period='10'/>
    </memballoon>    
    """
    host = 'clsk-kvm02.csi.it:16509'
    host = '172.16.0.19:16509'
    vm_names = ['i-3-59-VM', 'i-3-62-VM', 'i-3-68-VM', 'i-3-47-VM', 'i-3-60-VM']
    delta = 2
    
    pid = os.getpid()
    print pid
    p = psutil.Process(pid)
    print p.name(), p.status()
    
    #currentMemory
    server = VirtServer(id, "qemu+tcp://%s/system" % host)
    import random
    g = []
    for vm_name in vm_names:
        try:
            virt_domain = VirtDomainMonitor(server, name=vm_name)
            g.append(gevent.spawn(monitor, virt_domain, random.randint(2, 5)))
        except:
            print('Monitor for vm %s can not be started' % vm_name)
    
    gevent.joinall(g)
    
    server.disconnect()

if __name__ == "__main__":
    import sys
    sys.path.append('/usr/share/virt-manager')
    
    try:
        # Make sure we have a default '_' implementation, in case something
        # fails before gettext is set up
        __builtins__._ = lambda msg: msg
    except:
        pass
    
    main()