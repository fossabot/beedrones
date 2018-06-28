"""  test camunda
"""
import sys
import os
import pytest
sys.path.append(
    os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)),
        "src"))

from beedrones.camunda import WorkFlowEngine
from beecell.simple import id_gen

import logging

logging.basicConfig(level=logging.DEBUG)

conn = {
    'host': '10.102.160.12',
    'port': 9090,
    'path': '/engine-rest',
    'proto': 'http'
}

USER = 'admin'
PASSWD = 'adminadmin'
WFTEST = None


def intialize():
    global WFTEST
    if WFTEST is None:
        WFTEST = WorkFlowEngine(conn, user=USER, passwd=PASSWD)


def test_wf_initialize(capsys):
    # test = WorkFlowEngine(conn, user=USER, passwd=PASSWD)
    intialize()
    assert isinstance(WFTEST, WorkFlowEngine)


def test_wf_process(capsys):
    intialize()
    res = WFTEST.process_definition_list()
    assert isinstance(res, list)
    key = res[0]['key']
    assert isinstance(key, basestring)


def test_wf_proces(capsys):
    intialize()
    # test = WorkFlowEngine(conn, user=USER, passwd=PASSWD)
    key = 'invoiceppp'
    res = WFTEST.process_definition_get(key)
    with capsys.disabled():
        print res
    assert res['id']


def test_wf_xmlget(capsys):
    '''
        get an xml frp proces definition and redeloy it
        fail
    '''
    intialize()
    key = 'invoice'

    res = WFTEST.process_definition_xml_get(key)
    assert res['bpmn20Xml']
    # print res
    xml = res['bpmn20Xml']
    # TODO FIXME
    # res = WFTEST.process_deploy(xml, 'prova')
    # print res
    # assert res


def test_wf_startproc(capsys):
    intialize()
    res = WFTEST.process_definition_xml_get('invoice')
    import random
    amount = 1000.0 * random.random()
    # parameters= {
    #     "variables": {
    #         "amount": {
    #             "value": amount,
    #             "type": "double"
    #         },
    #         "invoiceCategory": {
    #             "value": "pippo--" + str(amount),
    #             "type": "string"
    #         }
    #     }
    # }
    parameters = {
        "amount": amount,
        "invoiceCategory": "pippo--" + str(amount)
    }
    bky = id_gen()
    res = WFTEST.process_instance_start_processDefinitionId('invoice', businessKey=bky,
                              variables=parameters)
    assert res
    with capsys.disabled():
        print (res)


def test_wf_tasksbyasignee(capsys):
    intialize()
    fi = {'assignee': 'demo'}
    res = WFTEST.tasks_list(fi)
    print res
    assert res


def test_wf_taskswithoutasignee(capsys):
    intialize()
    fi = {'assignee': None}
    res = WFTEST.tasks_list(fi)
    print res
    assert res


def test_wf_hol(capsys):
    '''  ppp
    '''
    intialize()
    # test = WorkFlowEngine(conn, user=USER, passwd=PASSWD)
    procinst = WFTEST.process_instance_start_processDefinitionId('holiday', variables={'prova': 'pluto'})
    procinst_id = procinst['id']
    filt = {'processInstanceId': procinst_id}
    task_list = WFTEST.tasks_list(filt)
    with capsys.disabled():
        for task in task_list:
            task_id = task['id']
            pvars = WFTEST.task_variables_get(task_id)
            print pvars
            pvars = WFTEST.process_instance_variables_list_ex(procinst_id)
            print pvars
            com = WFTEST.task_complete(task_id, {'settvar': True})
            print com

    amount = 1000.0 * 0.987654321
    parameters = {
        "amount": amount,
        "invoiceCategory": "pippo--" + str(amount)
    }
    bkid = id_gen()
    procid = WFTEST.process_instance_start_processDefinitionId(
        'invoice',
        variables=parameters,
        businessKey=bkid)
    assert not (procid is None)

    with capsys.disabled():
        print procid
    instl = WFTEST.process_instances_list(process_definition_get='invoice', businessKey=bkid)
    assert instl
    with capsys.disabled():
        print instl
