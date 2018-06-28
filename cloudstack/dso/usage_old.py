'''
Created on May 10, 2013

@author: io

http://10.102.90.5:8080/client/api?
account=isola1
&api_key=CLkbHQuSroEzAiFfFgiQRbNH7Eakh9zHO53gl2fe6RWreVe9xwn_G1DstQTA7mIGUJDgXsIjtDc6gi4ZT_M2jA
&command=createNetwork
&displaytext=CSK-I2-DATA-BL-336
&domainid=2602ce61-59b5-4068-bf9b-a85101fae4be
&endip=10.102.221.238
&gateway=10.102.221.225
&name=CSK-I2-DATA-BL
&netmask=255.255.255.240
&networkofferingid=8f7f831a-87ec-4022-b0fa-35b6c9eb1944
&physicalnetworkid=331a4517-01bc-4d00-9162-d494dcdb9a02
&startip=10.102.221.226&vlan=336
&zoneid=255f521c-4f6c-46db-8965-b94ee83be30c
&response=json
&signature=FYxAC73%2BtsDvDXQF6c0pgDN%2B%2B9c%3D

Secret Key = IDTLYfNR30TAr-ZvwI7r_ICaPfeDcLZgGS08aAOOaZ_gb7DZBCG06MxuBze8fqpfMpDRm8WuroXRqRVee5YkXg


Signature: This is the hashed signature of the Base URL that is generated using a combination of the user's Secret Key and the HMAC SHA-1 hashing algorithm.

Every API request has the format Base URL+API Path+Command String+Signature.

To generate the signature.
- For each field-value pair (as separated by a '&') in the Command String, URL encode each value so that it can be safely sent via HTTP GET. (Make sure all spaces are encoded as "%20" rather than "+".)
- Lower case the entire Command String and sort it alphabetically via the field for each field-value pair. The result of this step would look like the following.
api_key=mivr6x7u6bn_sdahobpjnejpgest35exq-jb8cg20yi3yaxxcgpyuairmfi_ejtvwz0nukkjbpmy3y2bcikwfq&command=deployvirtualmachine&diskofferingid=1&serviceofferingid=1&templateid=2&zoneid=4
- Take the sorted Command String and run it through the HMAC SHA-1 hashing algorithm (most programming languages offer a utility method to do this) with the user's Secret Key. Base64 encode the resulting byte array in UTF-8 so that it can be safely transmitted via HTTP. The final string produced after Base64 encoding should be "Lxx1DM40AjcXU%2FcaiK8RAP0O1hU%3D".
By reconstructing the final URL in the format Base URL+API Path+Command String+Signature, the final URL should look like:
http://localhost:8080/client/api?command=deployVirtualMachine&serviceOfferingId=1&diskOfferingId=1&templateId=2&zoneId=4&api_key=miVr6X7u6bN_sdahOBpjNejPgEsT35eXq-jB8CG20YI3yaxXcgpyuaIRmFI_EJTVwZ0nUkkJbPmY3y2bciKwFQ&signature=Lxx1DM40AjcXU%2FcaiK8RAP0O1hU%3D


account=isola1&api_key=CLkbHQuSroEzAiFfFgiQRbNH7Eakh9zHO53gl2fe6RWreVe9xwn_G1DstQTA7mIGUJDgXsIjtDc6gi4ZT_M2jA&command=listVirtualMachines&domainid=2602ce61-59b5-4068-bf9b-a85101fae4be&response=json&signature=w4Hel8%2BtbJPUd7BGorLOXETmR5w%3D
account=isola3&api_key=CLkbHQuSroEzAiFfFgiQRbNH7Eakh9zHO53gl2fe6RWreVe9xwn_G1DstQTA7mIGUJDgXsIjtDc6gi4ZT_M2jA&command=listUsageRecords&domainid=2602ce61-59b5-4068-bf9b-a85101fae4be&enddate=2013-05-02&response=json&startdate=2013-05-01&signature=tKEBbig%2BGolx2eyVPz9ngF%2BJywM%3D

tKEBbig%2BGolx2eyVPz9ngF%2BJywM%3D

u'account': u'isola3',
u'accountid': u'52621b7f-c685-4b71-8db6-ed9f2d98ff3b',
u'description': u'isola3-client running time (ServiceOffering: 12) (Template: 208)',
u'domainid': u'2602ce61-59b5-4068-bf9b-a85101fae4be',
u'enddate': u"2013-05-01'T'23:59:59+00:00",
u'name': u'isola3-client',
u'offeringid': u'9cb5c025-00fd-4302-99e9-65b43196c25a',
u'rawusage': u'24',
u'startdate': u"2013-05-01'T'00:00:00+00:00",
u'templateid': u'a5b73249-e996-46bf-a010-d80729d588a4',
u'type': u'KVM',
u'usage': u'24 Hrs',
u'usageid': u'8c300460-3b84-4bf6-9d6b-c7fd4d204054',
u'usagetype': 1,
u'virtualmachineid': u'8c300460-3b84-4bf6-9d6b-c7fd4d204054',
u'zoneid': u'255f521c-4f6c-46db-8965-b94ee83be30c'
'''

import urllib
import json
import pprint
from hashlib import sha1
import hmac
import binascii
import collections
from datetime import date

from gibbon_cloud.cloudstack.dso.base import ApiClient
from gibbon_cloud.cloudstack.dso.virtual_machine import VirtualMachine
from gibbon_cloud.cloudstack.dso.template import Template
from gibbon_cloud.cloudstack.dso.volume import Volume
from gibbon_cloud.cloudstack.dso.base import ApiClient
from gibbon_cloud.cloudstack.dso.base import ApiClient

from gibbon_cloud.util.billing import Billing

class Usage(ApiClient):
    ''' '''
    def __init__(self, base_url, api_key, secKey, billing):
        ''' '''
        super(Usage, self).__init__(base_url, api_key, secKey)
        
        self.usageTypes = self.get_usage_type()
        self.vmObj = VirtualMachine(base_url, api_key, secKey)
        self.tmplObj = Template(base_url, api_key, secKey)
        self.volObj = Volume(base_url, api_key, secKey)
        self.billing = billing

    def set_billing(self, billing):
        self.billing = billing

    def get_usage_type(self):
        ''' '''
        params = {'command':'listUsageTypes',
                  'response':'json',}
        response = self.send_api_request(params)
        try:
            res = []
            data = json.loads(response)['listusagetypesresponse']['usagetype']
            for item in data:
                num = int(item['usagetypeid'])-1
                res.insert(num, str(item['description']))
            return res
        except KeyError:
            res = []

    def get_data(self, account, domainId, startDate, endDate):
        ''' 
        return [{'usageList': [], 'usageType': 'Template Usage'},
                {'usageList': [], 'usageType': 'VPN users usage'},]
        '''
        start = startDate.split('-')
        end = endDate.split('-')
        startDateObj = date(int(start[2]), int(start[1]), int(start[0]))
        endDateObj = date(int(end[2]), int(end[1]), int(end[0]))
        params = {'account':account,
                  'command':'listUsageRecords',
                  'domainid':domainId,
                  'response':'json',
                  'enddate':endDateObj.strftime("%Y-%m-%d"),
                  'startdate':startDateObj.strftime("%Y-%m-%d"),}
        
        response = self.send_api_request(params)
        #print(params)
        #params = ''
     
        #f = urllib.urlopen("http://10.102.90.5:8080/client/api", params, proxies={})
        #print f
        #response = f.read()
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(json.loads(response))
        
        try:
            res = {'price_tot':0, 'usage':[]}
            data = json.loads(response)['listusagerecordsresponse']['usagerecord']

            for type in self.usageTypes:
                res['usage'].append({'usageType':type, 'usageList':[]})
            
            for item in data:               
                # usage tyep index
                usageTypeIndex = int(item.pop('usagetype')) - 1
                
                # create useg item
                usageItem = {'description':item['description'],
                             'rawusage':item['rawusage'],
                             'usage':item['usage'],
                             'startdate':item['startdate'],
                             'enddate':item['enddate']}
                
                # calculate running virtual machine price
                if res['usage'][usageTypeIndex]['usageType'] == 'Running Vm Usage':
                    vmId = item['virtualmachineid']
                    timeUsage = float(item['rawusage'])/24
                    # fields: templateid cpunumber cpuused networkkbswrite  
                    # networkkbsread memory hypervisor cpuspeed serviceofferingid
                    vmInfo = self.vmObj.info(vmId)
                    
                    # if virtual machine was been deleted vmInfo = []
                    if len(vmInfo)>0:
                        cpu_num = vmInfo['cpunumber']
                        ram = float(vmInfo['memory'])/1024
                        #print vmInfo
                        
                        # fields: so, size
                        volumes = self.volObj.info(vmInfo['id'])
                        #templateInfo = self.tmplObj.info(vmInfo['templateid'])
                        #print volumes
                        disk = 0
                        for volume in volumes:
                            disk += float(volume['size'])/1073741824
                        #print templateInfo
                        
                        price = self.billing.virtual_machine('windows', cpu_num, ram, disk, timeUsage)
                        #print price
                        usageItem['price'] = price
                        res['price_tot'] += price
    
                        #print '%s %s %s %s %s %s %s' % (item['name'], item['startdate'], item['enddate'], cpu_num, ram, disk, price)
                
                res['usage'][usageTypeIndex]['usageList'].append(usageItem)

                # organize usage by usagetype
                '''if usageTypeIndex in res.keys():
                    res[usageTypeIndex].append(item)
                else:
                    res[usageTypeIndex] = [item]
                #print res'''
            return res
        except KeyError as ex:
            return None
        #print pp.pprint(data)

if __name__ == "__main__":
    CLOUDSTACK_api_key = 'Ql9PouD8sxoVcFIJlnbbyD3LUg-_haUdYCjwO7fC1KehpA0on54y9h9uGJZ0RyQuWPDjPzQJFlrWjs5CwD69TQ'
    CLOUDSTACK_SECKEY = '7jNDIMfsrCCoj2LgGCMrCq4itTyzeGEeKFbQNE-eaq9CbqLH9GSyG5lWoC-UfEaz5nEtYY2ul6LwIP9siWu23w'
    account = 'admin'
    domainId = '5bc2595e-29df-11e3-b7de-005056020061'
    startDate = '05-10-2013'
    endDate = '05-10-2013'
    billing = Billing('day')
    usage = Usage('http://10.102.47.205:8001/client/api',
                  CLOUDSTACK_api_key,
                  CLOUDSTACK_sec_key,
                  billing)
    #res = account.get_domains()
    res = usage.get_usage_type()
    res = usage.get_data(account, domainId, startDate, endDate)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(res)