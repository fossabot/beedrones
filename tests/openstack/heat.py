'''
Created on Mar 17, 2016

@author: pas
'''
import tests.test_util
import gevent
from pyVim import connect
from beedrones.openstack.client import OpenstackManager
from tests.test_util import run_test, CloudapiTestCase
import ujson as json
import unittest
import random
import time
from beecell.simple import transaction_id_generator

#uri = "http://172.25.5.60:5000/v3"
uri = "http://172.25.3.51:5000/v3"
test_files_url="http://172.25.5.22/testfiles"

domain = 'default'    
user = 'admin'
project = 'admin'
#project = 'demo'
pwd = 'Opstkcs1'
region = 'RegionOne'

client = OpenstackManager(uri=uri, default_region=region)

sid = 'ce1c69c5-b360-4761-9758-5245c758663a'
vid = '4aaef387-96e8-4f98-91e4-bee36c0787fc'
user_id = None
project_id = None

class OpenstackHeatTestCase(CloudapiTestCase):
    """To execute this test you need a openstack instance.
    """
    def setUp(self):
        CloudapiTestCase.setUp(self)
        
        self.service = 'heat'

    def tearDown(self):
        CloudapiTestCase.tearDown(self)
    
    def test_ping(self):
        res = client.ping()
        
    def test_api(self):
        res = client.heat.api()
        self.logger.debug('Get openstack heat api: %s' % res)
        

#--------------Test stack list---------------------
    def test_stack_list(self):
        res = client.heat.stacks_list(global_tenant=True,show_deleted=False)
        self.logger.debug(self.pp.pformat(res))
         
    def test_stack_list_count(self):
        res = client.heat.stacks_list(with_count=True)

    def test_stack_list_id(self):
        res0 = client.heat.stacks_list()
        self.logger.debug(res0)
        for item in res0:
            res1=client.heat.stacks_list(ext_id=item['id'])   
            self.logger.debug('Stack id %s value: %s' % (item['id'],json.dumps(res1)))

    def test_stack_list_id_single(self):
        res1=client.heat.stacks_list(ext_id='TEIDXp9qoFSW2a')   
        self.logger.debug('Stack id %s value: %s' % ('TEIDXp9qoFSW2a',json.dumps(res1)))

    def test_stack_list_status(self):
        res = client.heat.stacks_list(status='CREATE_COMPLETE')
        self.logger.debug('Stack status %s value: %s' % ('CREATE_COMPLETE',json.dumps(res)))
        

    def test_stack_list_name(self):
        res0 = client.heat.stacks_list()
        for item in res0:
            res1=client.heat.stacks_list(name=item['stack_name'])   
            self.logger.debug('Stack name %s value: %s' % (item['stack_name'],json.dumps(res1)))

    def test_stack_list_tenant(self):
        res = client.heat.stacks_list(global_tenant=True,tenant='ad576ba1da5344a992463639ca4abf61')   
        self.logger.debug('Stack tenant %s value: %s' % ('ad576ba1da5344a992463639ca4abf61',json.dumps(res)))
        res = client.heat.stacks_list(global_tenant=True)   
        self.logger.debug('Stack global_tenant value: %s' % json.dumps(res))        

    def test_stack_list_username(self):
        res = client.heat.stacks_list(username='demo')
        self.logger.debug('Stack username %s value: %s' % ('demo',json.dumps(res)))
    
    def test_stack_list_owner_id(self):
        res = client.heat.stacks_list(owner_id='ad576ba1da5344a992463639ca4abf61')
        self.logger.debug('Stack owner %s value: %s' % ('ad576ba1da5344a992463639ca4abf61',json.dumps(res)))              

    def test_stack_list_limit(self):
        res = client.heat.stacks_list(limit=1)
        for item in res:
            mark = item['id']
        self.logger.debug('Stack limit %s until marker %s value: %s' % (2,mark,
                                                                        json.dumps(res))) 
        res = client.heat.stacks_list(limit=2,marker=mark)
        self.logger.debug('Stack limit %s starting by marker %s (not included) value: %s' % (2,mark,json.dumps(res)))                     
    
    def test_stack_list_show_deleted(self):
        res = client.heat.stacks_list(show_deleted=True)       
        self.logger.debug('Stack list with deleted %s' % json.dumps(res))

    def test_stack_list_show_nested(self):
        res = client.heat.stacks_list(show_nested=True)       
        self.logger.debug('Stack list with nested %s' % json.dumps(res))   
        
    def test_stack_list_show_sort_keys(self):
        res = client.heat.stacks_list(show_deleted=True,sort_keys='stack_name',
                               limit=2)       
        self.logger.debug('Stack list with deleted and sorted by name %s' % json.dumps(res))
        res = client.heat.stacks_list(show_deleted=True,sort_keys='stack_status',
                               limit=2)       
        self.logger.debug('Stack list with deleted and sorted by status %s' % json.dumps(res))        
        res = client.heat.stacks_list(show_deleted=True,sort_keys='creation_time',
                               limit=2)       
        self.logger.debug('Stack list with deleted and sorted by creation_time %s' % json.dumps(res))  
        res = client.heat.stacks_list(show_deleted=True,sort_keys='updated_time',
                               limit=2)       
        self.logger.debug('Stack list with deleted and sorted by updated_time %s' % json.dumps(res))
        #-------
        res = client.heat.stacks_list(show_deleted=True,sort_keys='stack_name', sort_dir='desc',
                               limit=2)       
        self.logger.debug('Stack list with deleted and sorted by name desc %s' % json.dumps(res))
        res = client.heat.stacks_list(show_deleted=True,sort_keys='stack_status',sort_dir='desc',
                               limit=2)       
        self.logger.debug('Stack list with deleted and sorted by status desc %s' % json.dumps(res))        
        res = client.heat.stacks_list(show_deleted=True,sort_keys='creation_time',sort_dir='desc',
                               limit=2)       
        self.logger.debug('Stack list with deleted and sorted by creation_time desc %s' % json.dumps(res))  
        res = client.heat.stacks_list(show_deleted=True,sort_keys='updated_time',sort_dir='desc',
                               limit=2)       
        self.logger.debug('Stack list with deleted and sorted by updated_time desc %s' % json.dumps(res))  
        
    def test_stack_list_tags(self):
        res = client.heat.stacks_list(tags='tag1,tag2')       
        self.logger.debug('Stack list with tags %s res %s' % ('tag1,tag2',json.dumps(res)))
        res = client.heat.stacks_list(tags_any='tag1,tag2')       
        self.logger.debug('Stack list with tags_any %s res %s' % ('tag1,tag2',json.dumps(res)))
        res = client.heat.stacks_list(not_tags='tag1,tag2')       
        self.logger.debug('Stack list with not_tags %s res %s' % ('tag1,tag2',json.dumps(res)))
        res = client.heat.stacks_list(not_tags_any='tag1,tag2')       
        self.logger.debug('Stack list with not_tags_any %s res %s' % ('tag1,tag2',json.dumps(res)))


#---------------Test Create stack----------------

    def test_stack_create(self):
        stack_n= "test_%s"%transaction_id_generator(length=10)
        res = client.heat.stacks_create(stack_name=stack_n,
        use_all_urls=True, 
        template_url="%s/test_templ.yaml"%test_files_url,
        environment="%s/test_env.yaml"%test_files_url,
        parameters="%s/test_param.json"%test_files_url,
        tags="test_api,tag_test_api",
        files="%s/test_files.json"%test_files_url
        )
        self.logger.debug('Create stack result %s' % res)     

    def test_stack_create_type_env(self):
        stack_n= "test_%s"%transaction_id_generator(length=10)
        res = client.heat.stacks_create(stack_name=stack_n,
        use_all_urls=True, 
        template_url="%s/autoscaling_simple_volumes.yaml"%test_files_url,
        environment="%s/environment_ServerWithVolume.json"%test_files_url,
        #         parameters="%s/test_param.json"%test_files_url,
        #         tags="test_api,tag_test_api",
        #         files="%s/test_files.json"%test_files_url
        )
        self.logger.debug('Create stack result %s' % res) 
        
    def test_stack_create_params(self):
        stack_n= "test_%s"%transaction_id_generator(length=10)
        res = client.heat.stacks_create(stack_name=stack_n,
        use_all_urls=False, 
        template="heat_template_version: 2015-04-30\n\ndescription: Template di prova per istanza singola\nparameters:\n  key_name:\n    type: string\n  image_id:\n    type: string\n  instance_type:\n    type: string\n  net_id:\n    type: string\nresources:\n  my_instance:\n    type: OS::Nova::Server\n    properties:\n      key_name: { get_param: key_name }\n      image: { get_param: image_id }\n      flavor: { get_param: instance_type }\n      networks:\n        - network: { get_param: net_id }\n      user_data: { get_file : myfile }        \n\noutputs:\n  instance_ip:\n    description: The IP address of the deployed instance\n    value: { get_attr: [my_instance, first_address] }\n ",
        environment="{\n    \"parameter_defaults\":{\n        \"image_id\":\"centos7-heat\",\n        \"instance_type\":\"m1.medium\",\n        \"net_id\":\"admin-private-net\"\n    }\n}",
        parameters="{\n    \"key_name\":\"opstkcsi\"\n}",
        tags="test_api,tag_test_api",
        files="{\n    \"myfile\": \"#!\/bin\/bash\necho \"Hello world\" > \/root\/testfile.txt\"\n}"
        #         template="heat_template_version: 2015-04-30\n\ndescription: Template di prova per istanza singola\nparameters:\n  key_name:\n    type: string\n  image_id:\n    type: string\n  instance_type:\n    type: string\n  net_id:\n    type: string\nresources:\n  my_instance:\n    type: OS::Nova::Server\n    properties:\n      key_name: { get_param: key_name }\n      image: { get_param: image_id }\n      flavor: { get_param: instance_type }\n      networks:\n        - network: { get_param: net_id }\n      user_data: { get_file : myfile }        \n\noutputs:\n  instance_ip:\n    description: The IP address of the deployed instance\n    value: { get_attr: [my_instance, first_address] }\n ",
        #         environment={"parameter_defaults":{
        #                         "image_id":"centos7-heat",
        #                         "instance_type":"m1.medium",
        #                         "net_id":"admin-private-net"}},
        #         parameters={"key_name":"opstkcsi"},
        #         tags="test_api,tag_test_api",
        #         files={"myfile":"#!\/bin\/bash\necho \"Hello world\" > \/root\/testfile.txt"}        
        )
        self.logger.debug('Create stack result %s' % res)                   

    def test_stack_create_simple(self):        
        stack_n= "test_%s"%transaction_id_generator(length=10)
        res = client.heat.stacks_create(stack_name=stack_n, 
        tags="test_api,tag_test_api",
        template_url="%s/test_template_full.yaml"%test_files_url)                     
        self.logger.debug('Create stack % result %s' % (stack_n,json.dumps(res)))
        
    def test_stack_create_from_string(self):        
        stack_n= "test_%s"%transaction_id_generator(length=10)
        res = client.heat.stacks_create(stack_name=stack_n, 
        tags="test_api,tag_test_api",
        template=u'heat_template_version: 2015-04-30\n\ndescription: Template Test API\n\n\nparameters:\n\n  key_name:\n    type: string\n    label: Key Name\n    description: Name of key-pair to be used for compute instance\n    default: "opstkcsi"\n \n  image_id:\n    type: string\n    label: Image ID\n    description: Image to be used for compute instance\n    default: "centos7-heat"\n\n  instance_type:\n    type: string\n    label: Instance Type\n    description: Type of instance (flavor) to be used\n    default: "m1.medium"\n\n  net_id:\n    type: string\n    label: Network ID\n    description: Network ID for the server\n    default: "admin-private-net"    \n\n\nresources:\n  my_instance:\n    type: OS::Nova::Server\n    properties:\n      key_name: { get_param: key_name }\n      image: { get_param: image_id }\n      flavor: { get_param: instance_type }\n      networks:\n        - network: { get_param: net_id }\n \n\noutputs:\n  instance_ip:\n    description: The IP address of the deployed instance\n    value: { get_attr: [my_instance, first_address] }\n                  ')                     
        self.logger.debug('Create stack % result %s' % (stack_n,json.dumps(res)))        
        
        
        
        
    def test_stack_create_failed(self):        
        stack_n= "test_%s"%transaction_id_generator(length=10)
        res = client.heat.stacks_create(stack_name=stack_n, 
        template_url="%s/test_template_cinder.yaml"%test_files_url,
        disable_rollback=False,
        tags="test_api,tag_test_api",
        timeout_mins="1"
        )                     
        self.logger.debug('Create stack % result %s' % (stack_n,json.dumps(res)))        
        

#---------------Test Create stack preview------------

    def test_stack_create_simple_preview(self):        
        stack_n= "test_%s"%transaction_id_generator(length=10)
        res = client.heat.stacks_preview(stack_name=stack_n, 
        tags="test_api,tag_test_api",
        template_url="%s/test_template_full.yaml"%test_files_url)                     
        self.logger.debug('Preview stack %s result %s' % (stack_n,json.dumps(res)))        

    def test_stack_create_preview(self):
        stack_n= "test_%s"%transaction_id_generator(length=10)
        res = client.heat.stacks_preview(stack_name=stack_n,
        use_all_urls=True, 
        template_url="%s/test_templ.yaml"%test_files_url,
        #environment="%s/test_env.yaml"%test_files_url,
        #parameters="%s/test_param.json"%test_files_url,
        tags="test_api,tag_test_api",
        #files="%s/test_files.json"%test_files_url
        )        
        self.logger.debug('Preview stack %s result %s' % (stack_n,json.dumps(res)))        
        
#---------------Test Create stack update------------

    def test_stack_create_simple_update(self):        
        stack_n='coreos_prova'
        stack_i='213f6a23-c56b-40cb-ba76-85d08d20efdb'
        res = client.heat.stacks_update(stack_name=stack_n,ext_id=stack_i, 
        tags="test_api2,tag_test_api2",
        template_url="%s/test_template_full.yaml"%test_files_url)                     
        self.logger.debug('Preview stack % result %s' % (stack_n,json.dumps(res)))        

    def test_stack_create_simple_update_preview(self):        
        stack_n='coreos_prova'
        stack_i='213f6a23-c56b-40cb-ba76-85d08d20efdb'
        res = client.heat.stacks_update_preview(stack_name=stack_n,ext_id=stack_i, 
        tags="test_api2,tag_test_api2",
        template_url="%s/test_template_full.yaml"%test_files_url)                     
        self.logger.debug('Preview stack %s result %s' % (stack_n,json.dumps(res)))   

#---------------Test stack find------------
    
    def test_stack_find(self):
        res = client.heat.stacks_find(stack_name='coreos_prova')
        self.logger.debug('Stack find %s href value: %s' % ('coreos_prova',res))

#---------------Test stack details------------
    
    def test_stack_details(self):
        res = client.heat.stacks_details(stack_name='hook_test',
                            ext_id="548c42eb-f8fb-4335-aeae-0c2d3c8e293b")
        self.logger.debug('Get openstack heat Details: %s' % json.dumps(res))
        
#---------------Test stack delete-------------
    
    def test_stack_delete(self):
        res = client.heat.stacks_delete(stack_name='lampue',
                            ext_id="9515f051-f477-46ec-a3b4-27556f6a9e92")
        self.logger.debug('Get openstack heat Details: %s' % json.dumps(res))        

#---------------Test snapshot ------------
    
    def test_snapshots_list(self):
        res = client.heat.snapshots_list(stack_name='coreos_prova',
                            ext_id="213f6a23-c56b-40cb-ba76-85d08d20efdb")
        self.logger.debug('Openstack heat snapshots list: %s' % json.dumps(res))

    def test_snapshots_create(self):
        res = client.heat.snapshots_create(stack_name='coreos_prova',
                            ext_id="213f6a23-c56b-40cb-ba76-85d08d20efdb",
                            name="snapshot1")
        self.logger.debug('Openstack heat snapshots %s create: %s' % ('snapshot1',
                            json.dumps(res)))
    
    def test_snapshots_show(self):
        res = client.heat.snapshots_show(stack_name='coreos_prova',
                            ext_id="213f6a23-c56b-40cb-ba76-85d08d20efdb",
                            snapshot_id="340a24ad-286c-43e8-9a03-5e3df3831376")
        self.logger.debug('Openstack heat snapshots show: %s' % json.dumps(res))
        
    def test_snapshots_restore(self):
        res = client.heat.snapshots_restore(stack_name='coreos_prova',
                            ext_id="213f6a23-c56b-40cb-ba76-85d08d20efdb",
                            snapshot_id="340a24ad-286c-43e8-9a03-5e3df3831376")
        self.logger.debug('Openstack heat snapshots restore: %s' % json.dumps(res))
  
    def test_snapshots_delete(self):
        res = client.heat.snapshots_delete(stack_name='coreos_prova',
                            ext_id="213f6a23-c56b-40cb-ba76-85d08d20efdb",
                            snapshot_id="340a24ad-286c-43e8-9a03-5e3df3831376")
        self.logger.debug('Openstack heat snapshots delete: %s' % json.dumps(res))      


#---------------Test Outputs --------------

    def test_outputs_find(self):
        res = client.heat.outputs_find(stack_name='DB_stack_test_view-9174',
                            ext_id="c4d870bc-812f-4bea-bbdd-6cd2aa82f3bd")
        self.logger.debug('Get openstack heat list outputs: %s' % json.dumps(res))

    def test_outputs_find_key(self):
        res = client.heat.outputs_find(stack_name='DB_stack_test_view-9174',
                            ext_id="c4d870bc-812f-4bea-bbdd-6cd2aa82f3bd",
                            output_key="server_list")
        self.logger.debug('Get openstack heat list outputs: %s' % json.dumps(res))

#---------------Test Resources in a stack------------

    def test_resources_find(self):
        res = client.heat.resources_find(stack_name='DB_stack_test-87995',
                            ext_id="5da73ee9-35e5-4803-88d9-6c73d63ec908")
        self.logger.debug('Get openstack heat list resources: %s' % json.dumps(res))

    def test_resources_find_name(self):
        res = client.heat.resources_find(stack_name='DB_stack_test-34045',
                            ext_id="4428713c-d41f-4731-8d9b-2cd5957c2a56",
                            resource_name="DB-t-87995-asg-zsy24ml3tgq6-khwdd7mvrhsf-awx6bitsl4kj")
        self.logger.debug('Get openstack heat list resources: %s' % json.dumps(res))

    def test_resources_find_metadata(self):
        res = client.heat.resources_find_metadata(stack_name='DB_stack_test-34045',
                            ext_id="4428713c-d41f-4731-8d9b-2cd5957c2a56",
                            resource_name="asg")
        self.logger.debug('Get openstack heat list resources: %s' % json.dumps(res))

    def test_resources_send_signal(self):
        res = client.heat.resources_send_signal(stack_name='coreos_prova',
                            ext_id="213f6a23-c56b-40cb-ba76-85d08d20efdb",
                            resource_name="my_instance",signal_data={'test':'value'})
        self.logger.debug('Send a signal to resources: %s' % json.dumps(res))
        
    def test_resources_send_signal_id(self):
        res = client.heat.resources_send_signal(stack_name='hook_test',
                            ext_id="55fde993-3bd8-4ae8-abe8-2210c08c9ee6",resource_name='wait_handle',
                            signal_data={"status": "SUCCESS"})
        self.logger.debug('Send a signal to resources: %s' % json.dumps(res))        



    def test_resource_types_list(self):
        res = client.heat.resource_types_list()
        self.logger.debug('Get openstack resources types list: %s' % json.dumps(res))
 
    def test_resource_types_show(self):
        res = client.heat.resource_types_show(resource_type="OS::Nova::Server")
        self.logger.debug('Get openstack resources types show: %s' % json.dumps(res))

    def test_resource_types_template(self):
        res = client.heat.resource_types_template(resource_type="OS::Nova::Server", 
                                         template_type='hot')
        self.logger.debug('Get openstack resources types template: %s' % json.dumps(res))                  
                         

#---------------Test stack Events------------
    
    def test_events_list(self):
        res = client.heat.events_list(stack_name='DB_stack_test-34045',
                            ext_id="4428713c-d41f-4731-8d9b-2cd5957c2a56")
        self.logger.debug('Get openstack event list: %s' % json.dumps(res))
        
    def test_events_list_resource_action(self):
        res = client.heat.events_list(stack_name='coreos_prova',
                            ext_id="213f6a23-c56b-40cb-ba76-85d08d20efdb",
                            resource_action='CREATE')
        self.logger.debug('Get openstack event list resource action %s: %s' 
                          % ('CREATE',json.dumps(res)))
    
    def test_events_list_resource_status(self):
        res = client.heat.events_list(stack_name='coreos_prova',
                            ext_id="213f6a23-c56b-40cb-ba76-85d08d20efdb",
                            resource_status='COMPLETE')
        self.logger.debug('Get openstack event list resource statu %s: %s' 
                          % (' COMPLETE',json.dumps(res)))        

#---------------Templates--------------------
    def test_template_versions(self):
        res = client.heat.template_versions()
        self.logger.debug('Get heat template versions: %s' % json.dumps(res))

    def test_template_simple_validate(self):        
        res = client.heat.template_validate(
            template_url="%s/test_template_full.yaml"%test_files_url)                     
        self.logger.debug('Template simple validate result %s'%(json.dumps(res)))        

    def test_template_validate(self):
        res = client.heat.template_validate(
        use_all_urls=True, 
        template_url="%s/test_templ.yaml"%test_files_url,
        environment="%s/test_env.yaml"%test_files_url,
        )        
        self.logger.debug('Template simple validate result %s'%(json.dumps(res)))        
                

    #--------------Build Info--------------------
    def test_build_info(self):
        res = client.heat.build_info()
        self.logger.debug('Get heat build info: %s' % json.dumps(res))

    #--------------Software--------------------

    def test_generate_temp_url(self):
        timeout='30000'
        container='signaling'
        c_object='swconfig_03'
        method='PUT'
        key='containerkey'
        client.swift.object_put(container=container,c_object=c_object)
        res = client.swift.generate_temp_url(container=container,c_object=c_object,
                    timeout=timeout,method=method, key=key)
        self.logger.debug(u'Generate openstack swift temp urls: %s' % res)

    def test_object_get_temp_url(self):
        container='signaling'
        c_object='swconfig_03'
        res = client.swift.object_get(container=container,c_object=c_object)
        self.logger.debug(u'Get openstack swift object details: %s' % res)     
    
    def test_software_configs_list(self):
        res = client.heat.software_configs_list()
        self.logger.debug('Get heat List configs: %s' % json.dumps(res))

    def test_software_configs_details(self):
        res = client.heat.software_configs_details(config_id='d9395163-4238-4e94-902f-1e8abdbfa2bb')
        self.logger.debug('Get heat shows software config: %s' % json.dumps(res))

    def test_software_configs_create(self):
        #conf_name= "test_config_%s"%transaction_id_generator(length=10)
        conf_name = "swconfig_05"
        res = client.heat.software_configs_create(
        name=conf_name,
        group='script',
        use_all_urls=False,
        config="""#!/bin/bash
touch /tmp/test 
hostname > /tmp/test  
hostname > ${host_name}
""",
        inputs=
[
    {
        "type":"String",
        "name":"deploy_signal_transport",
        "value":"TEMP_URL_SIGNAL",
        "description":"How the server should signal to heat with the deployment output values."
     },
    {
        "type": "String",
        "name": "deploy_signal_id",
        "value": "http://ctrl-liberty.nuvolacsi.it:8080/v1/AUTH_b570fe9ea2c94cb8ba72fe07fa034b62/signaling/swconfig_03?temp_url_sig=72c75c3b29f97d36a48d9664e035207d1587ff8b&temp_url_expires=1484593629",
        "description": "ID of signal to use for signaling output values"
    },
    {
        "description": "HTTP verb to use for signaling "
        "output values",
        "name": "deploy_signal_verb",
        "type": "String",
        "value": "PUT"
    }         
],
        outputs=
[
    {
        "type": "String",
        "name": "host_name",
        "error_output": 'true',
        "description": 'null'
    }
],
        options=
[
    {
        "test":"Value"
    }
])

        ''',
        config="""|
        #!/bin/bash
        su - ${user_name} << EOF > ${heat_outputs_path}.id_rsa_pub
        test -f .ssh/id_rsa.pub || ssh-keygen -q -t rsa -N "" -f .ssh/id_rsa
        cat .ssh/id_rsa.pub
        EOF
        """
         config="""#!/bin/bash
touch /tmp/test 
hostname > /tmp/test  
"""
        '''

        #!/bin/sh -x\necho \"Writing to /tmp/$bar\"\necho $foo > /tmp/$bar\necho -n \"The file /tmp/$bar contains `cat /tmp/$bar` for server $deploy_server_id during $deploy_action\" > $heat_outputs_path.result\necho \"Written to /tmp/$bar\"\necho \"Output to stderr\" 1>&2"
        
        self.logger.debug('Create software config: %s' % json.dumps(res))        

    def test_software_configs_delete(self):
        res = client.heat.software_configs_delete(config_id='1f087375-25a1-4107-aefc-f2ccc7e00f49')
        self.logger.debug('Get heat delete software config: %s' % json.dumps(res))
            
    def test_software_deployments_list(self):
        res = client.heat.software_deployments_list()
        self.logger.debug('Get heat List deployments: %s' % json.dumps(res))

    def test_software_deployments_details(self):
        res = client.heat.software_deployments_details(deployment_id='e792343e-177c-4db9-bb67-dd0bd3b5b65c')
        self.logger.debug('Get heat show deployment details: %s' % json.dumps(res))

    def test_software_deployments_show_metadata(self):
        res = client.heat.software_deployments_show_metadata(server_id='469dd1eb-273f-4515-8a79-791f42a903cc')
        self.logger.debug('Get heat server metadata: %s' % json.dumps(res))

    def test_software_deployments_create(self):
        res = client.heat.software_deployments_create(
        config_id="4f64e47f-d450-4e6c-a018-6828efd00f64",
        server_id="469dd1eb-273f-4515-8a79-791f42a903cc",
        action='CREATE',
        status_reason="Deploy data available",
        status="IN_PROGRESS",
        )
        self.logger.debug('Create software config: %s' % json.dumps(res))    

    def test_software_deployments_delete(self):
        res = client.heat.software_deployments_delete(
        deployment_id='cde79347-0280-4199-a6ff-4a360f5e8568'
        )
        self.logger.debug('delete software deployment: %s' % json.dumps(res))

    def test_software_deployments_update(self):
        res = client.heat.software_deployments_update(
        use_all_urls=True, 
        deployment_id='cde79347-0280-4199-a6ff-4a360f5e8568',
        config_id='1e92e4dc-d414-4877-a490-1bc1efdbe5bb',
        output_values="%s/test_sw_depl_update_outputs.json"%test_files_url,
        action='CREATE',
        status_reason="Outputs received",
        status="COMPLETE"        
        )
        self.logger.debug('Update software config: %s' % json.dumps(res)) 

    def test_services_status(self):
        res = client.heat.services_status()
        self.logger.debug('Get heat services status: %s' % json.dumps(res))

#---------------Other Tests------------------
    
    def test_authorize(self):
        #authorize keystone api v3
        res = client.authorize(user, pwd, project=project, domain=domain)
        #authorize keystone api v2
        #res = client.authorize(user, pwd, project=project, version='v2')
        
    def test_release_token(self):
        client.identity.release_token()        



        
def test_suite():
    tests = [
            'test_authorize',
            
            #'test_ping',
            
            #'test_api',
            
            #-----------list-------------- 
            #'test_stack_list',
            #'test_stack_list_count',
            #'test_stack_list_status',
            #'test_stack_list_id',
            #'test_stack_list_id_single',            
            #'test_stack_list_name',
            #'test_stack_list_tenant',
            #'test_stack_list_username',             
            #'test_stack_list_owner_id',
            #'test_stack_list_limit',
            #'test_stack_list_show_deleted',
            #'test_stack_list_show_nested',
            #'test_stack_list_show_sort_keys',
            #'test_stack_list_tags',
            
            #-----------create------------ 
            #'test_stack_create_simple',
            #'test_stack_create',
            #'test_stack_create_params',
            #'test_stack_create_failed',
            #'test_stack_create_from_string',
            #'test_stack_create_type_env',
            
            #-----------preview-------------- 
            #'test_stack_create_simple_preview',
            #'test_stack_create_preview',             
            
            #-----------update--------------- 
            #'test_stack_create_simple_update',
            #'test_stack_create_simple_update_preview',
            
            #-----------find------------------ 
            #'test_stack_find',
            
            #-----------details--------------- 
            #'test_stack_details',
            
            #-----------delete-------------- 
            #'test_stack_delete',             
            
            #-----------snapshots-------------             
            #'test_snapshots_create',
            #'test_snapshots_restore',
            #'test_snapshots_list',
            #'test_snapshots_show',
            
            #-----------outputs---------------             
            #'test_outputs_find',
            #'test_outputs_find_key',
            
            #--------resources in a stack-----             
            #'test_resources_find',
            #'test_resources_find_name',
            #'test_resources_find_metadata',
            #'test_resources_send_signal',
            #'test_resources_send_signal_id',
            
            #'test_resource_types_list',
            #'test_resource_types_show', 
            #'test_resource_types_template',           
            
            #-----------events----------------
            #'test_events_list',
            #'test_events_list_resource_action',
            #'test_events_list_resource_status',
            
            #-----------template--------------
            #'test_template_versions',
            #'test_template_simple_validate',
            #'test_template_validate',
            
            #-----------build----------------
            #'test_build_info',
            
            #-----------Software-------------
            #'test_generate_temp_url',
            
            #'test_software_configs_delete',
            #'test_software_configs_list',
            #'test_software_configs_details',
            #'test_software_configs_create',            

            #'test_software_deployments_create',
            #'test_software_deployments_details',
            #'test_software_deployments_update',
            #'test_software_deployments_list',
            #'test_software_deployments_show_metadata',                        
            #'test_software_deployments_delete',

            'test_object_get_temp_url',
            
            #'test_services_status',
            #'test_release_token',
            
            ]
    return unittest.TestSuite(map(OpenstackHeatTestCase, tests))

if __name__ == '__main__':
    run_test([test_suite()])          