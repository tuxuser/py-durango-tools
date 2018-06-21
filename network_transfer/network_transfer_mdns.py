import logging
import socket
from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange, ServiceInfo

logger = logging.getLogger(__name__)


class NetworkTransferConsole(object):
    def __init__(self, server_name, name, liveid, address):
        self.server_name = server_name
        self.name = name
        self.liveid = liveid
        self.address = address

    def __str__(self):
        return '%s, Name: %s, LiveID: %s, Address: %s' % (self.server_name,
                                                          self.name,
                                                          self.liveid,
                                                          self.address)


class NetworkTransferMDNS(object):
    SERVICE_TYPE = "_xboxcol._tcp.local."
    DESC_NAME = b'N'
    DESC_LIVEID = b'U'

    def __init__(self):
        self._zc = Zeroconf()
        self._consoles = list()
        self._service_info = None

    @property
    def consoles(self):
        return self._consoles

    @property
    def service_info(self):
        return self._service_info

    def _discover_cb(self, zeroconf, service_type, name, state_change):
        logger.debug("Service %s of type %s state changed: %s" % (name, service_type, state_change))
        info = zeroconf.get_service_info(service_type, name)

        if not info:
            logger.warning("Service %s discovered but no info available" % name)
            return

        if state_change is ServiceStateChange.Added:
            address = "%s:%d" % (socket.inet_ntoa(info.address), info.port)
            name = info.properties[b'N'].decode('utf8')
            liveid = info.properties[b'U'].decode('utf8')
            console_entry = NetworkTransferConsole(info.server, name, liveid,
                                                   address)
            logger.info("Found Console %s" % console_entry)
            self._consoles.append(console_entry)

        elif state_change is ServiceStateChange.Removed:
            # Remove console info to dict
            self._consoles.pop(info.server)

    def discover(self):
        ServiceBrowser(self._zc, NetworkTransferMDNS.SERVICE_TYPE,
                       handlers=[self._discover_cb])

    def _prepare_serviceinfo(self, name, liveid, address, port):
        mdns_name = '%s.%s' % (liveid, NetworkTransferMDNS.SERVICE_TYPE)
        server_name = '%s.local.' % name
        ipaddr = socket.inet_aton(address)
        properties = {
            NetworkTransferMDNS.DESC_NAME: name.upper().encode('utf-8'),
            NetworkTransferMDNS.DESC_LIVEID: liveid.encode('utf-8')
        }

        self._service_info = ServiceInfo(type_=NetworkTransferMDNS.SERVICE_TYPE,
                                         name=mdns_name,
                                         address=ipaddr,
                                         port=port,
                                         weight=0,
                                         priority=0,
                                         properties=properties,
                                         server=server_name)

    def register_service(self, name, liveid, address, port):
        self._prepare_serviceinfo(name, liveid, address, port)
        self._zc.register_service(self._service_info)

    def unregister_service(self):
        if self._service_info:
            self._zc.unregister_service(self._service_info)