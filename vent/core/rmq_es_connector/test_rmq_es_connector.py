import pytest
import sys

import rmq_es_connector


class Method():
    """ create mock method object """
    routing_key = None

    def __init__(self, routing_key="foo.bar"):
        self.routing_key = routing_key


def test_rmq_es_connector_connections():
    """ tests the connections function """
    rmq_es = rmq_es_connector.RmqEs()
    rmq_es.connections(False)
    rmq_es = rmq_es_connector.RmqEs(es_host="localhost", rmq_host="localhost")
    rmq_es.connections(True)


def test_rmq_es_connector_callback():
    """ tests the callback function """
    rmq_es = rmq_es_connector.RmqEs()
    method = Method()
    rmq_es.callback(None, method, None, "[]")
    rmq_es.callback(None, method, None, "[]")
    method = Method(routing_key="syslog.foo")
    rmq_es.callback(None, method, None, "[]")
    method = Method(routing_key="dshell_netflow.foo")
    rmq_es.callback(None, method, None, "[]")
    method = Method(routing_key="hex_flow.foo")
    rmq_es.callback(None, method, None, "[]")
    rmq_es = rmq_es_connector.RmqEs(es_host="localhost", rmq_host="localhost")
    rmq_es.connections(True)
    rmq_es.callback(None, method, None, "[]")
    rmq_es.callback(None, method, None, "asdf * '[]'")


def test_rmq_es_connector_start():
    """ tests the start function """
    rmq_es = rmq_es_connector.RmqEs(es_host="localhost", rmq_host="localhost")
    rmq_es.start()
    argv = sys.argv
    sys.argv = ["foo"]
    with pytest.raises(SystemExit):
        rmq_es.start()
    sys.argv = argv
