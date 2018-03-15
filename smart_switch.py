import email.utils
from logging import getLogger
from upnp_device import upnp_device

import const

logger = getLogger('devel')

# This subclass does the bulk of the work
# to mimic a WeMo switch on the network.

SETUP_XML = """<?xml version="1.0"?>
<root>
  <device>
    <deviceType>urn:Xevious:device:controllee:1</deviceType>
    <friendlyName>%(device_name)s</friendlyName>
    <manufacturer>Belkin International Inc.</manufacturer>
    <modelName>Emulated Socket</modelName>
    <modelNumber>3.1415</modelNumber>
    <UDN>uuid:Socket-1_0-%(device_serial)s</UDN>
    <serialNumber>221517K0101769</serialNumber>
    <binaryState>0</binaryState>
            <serviceList>
              <service>
                  <serviceType>urn:Belkin:service:basicevent:1</serviceType>
                  <serviceId>urn:Belkin:serviceId:basicevent1</serviceId>
                  <controlURL>/upnp/control/basicevent1</controlURL>
                  <eventSubURL>/upnp/event/basicevent1</eventSubURL>
                  <SCPDURL>/eventservice.xml</SCPDURL>
              </service>
          </serviceList>
  </device>
</root>
"""

eventservice_xml = """<?scpd xmlns="urn:Belkin:service-1-0"?>
        <actionList>
          <action>
            <name>SetBinaryState</name>
            <argumentList>
              <argument>
                <retval/>
                <name>BinaryState</name>
                <relatedStateVariable>BinaryState</relatedStateVariable>
                <direction>in</direction>
              </argument>
            </argumentList>
             <serviceStateTable>
              <stateVariable sendEvents="yes">
                <name>BinaryState</name>
                <dataType>Boolean</dataType>
                <defaultValue>0</defaultValue>
              </stateVariable>
              <stateVariable sendEvents="yes">
                <name>level</name>
                <dataType>string</dataType>
                <defaultValue>0</defaultValue>
              </stateVariable>
            </serviceStateTable>
          </action>
        </scpd>
"""

GetBinaryState_soap = """<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:GetBinaryStateResponse xmlns:u="urn:Belkin:service:basicevent:1">
      <BinaryState>%(state_realy)s</BinaryState>
    </u:GetBinaryStateResponse>
  </s:Body>
</s:Envelope>
"""

REQ_GET_BINARY_STATE = "urn:Belkin:service:basicevent:1#GetBinaryState"
SOAP_SET_BINARY_STATE = \
        'SOAPACTION: "urn:Belkin:service:basicevent:1#SetBinaryState"'


class smart_switch(upnp_device):
    relayState = 0

    @staticmethod
    def make_uuid(name):
        return ''.join(["%x" % sum([ord(c) for c in name])] +
                       ["%x" % ord(c) for c in "%sfauxmo!" % name])[:14]

    def __init__(self, name, listener, poller, ip_address, port,
                 action_handler=None):
        self.serial = self.make_uuid(name)
        logger.debug(self.state)

        self._name = name
        self.ip_address = ip_address
        persistent_uuid = "Socket-1_0-" + self.serial
        other_headers = ['X-User-Agent: solvalou']
        upnp_device.__init__(self, listener, poller, port, const.URL_SETUP_XML,
                             "Unspecified, UPnP/1.0, Unspecified",
                             persistent_uuid, other_headers=other_headers,
                             ip_address=ip_address)
        if action_handler:
            self.action_handler = action_handler
        else:
            self.action_handler = self
        logger.debug("Virtual Switch/Socket device '%s' ready on %s:%s" %
                     (self._name, self.ip_address, self.port))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def handle_request(self, data, sender, socket):
        logger.debug(data)
        if data.find(const.POST_UPNP) == 0 and \
                data.find(REQ_GET_BINARY_STATE) != -1:
            # logger.debug(state)
            soap = GetBinaryState_soap % {'state_realy': self.state}
            date_str = email.utils.formatdate(
                timeval=None, localtime=False, usegmt=True)
            message = ("HTTP/1.1 200 OK\r\n"
                       "CONTENT-LENGTH: %d\r\n"
                       "CONTENT-TYPE: text/xml charset=\"utf-8\"\r\n"
                       "DATE: %s\r\n"
                       "EXT:\r\n"
                       "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
                       "X-User-Agent: solvalou\r\n"
                       "CONNECTION: close\r\n"
                       "\r\n"
                       "%s" % (len(soap), date_str, soap))
            logger.debug(message)
            socket.send(message)
        elif data.find(const.GET_EVENT_SRV_XML) == 0:
            logger.debug(
                "Responding to eventservice.xml for %s" % self._name)
            date_str = email.utils.formatdate(
                timeval=None, localtime=False, usegmt=True)
            messageEvent = ("HTTP/1.1 200 OK\r\n"
                            "CONTENT-LENGTH: %d\r\n"
                            "CONTENT-TYPE: text/xml\r\n"
                            "DATE: %s\r\n"
                            "LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT\r\n"
                            "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
                            "X-User-Agent: solvalou\r\n"
                            "CONNECTION: close\r\n"
                            "\r\n"
                            "%s" %
                            (len(eventservice_xml), date_str,
                                eventservice_xml))
            logger.debug(messageEvent)
            socket.send(messageEvent)
        elif data.find(const.GET_SETUP_XML) == 0:
            logger.debug("Responding to setup.xml for %s" % self._name)
            xml = SETUP_XML % {'device_name': self._name,
                               'device_serial': self.serial}
            date_str = email.utils.formatdate(
                timeval=None, localtime=False, usegmt=True)
            message = ("HTTP/1.1 200 OK\r\n"
                       "CONTENT-LENGTH: %d\r\n"
                       "CONTENT-TYPE: text/xml\r\n"
                       "DATE: %s\r\n"
                       "LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT\r\n"
                       "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
                       "X-User-Agent: solvalou\r\n"
                       "CONNECTION: close\r\n"
                       "\r\n"
                       "%s" % (len(xml), date_str, xml))
            logger.debug(message)
            socket.send(message)
        elif data.find(SOAP_SET_BINARY_STATE) != -1:
            success = False
            if data.find('<BinaryState>1</BinaryState>') != -1:
                # on
                logger.debug("Responding to ON for %s" % self._name)
                success = True
                self.relayState = 1
                #  success = self.action_handler.on()
            elif data.find('<BinaryState>0</BinaryState>') != -1:
                # off
                logger.debug("Responding to OFF for %s" % self._name)
                success = True
                self.relayState = 0
                # success = self.action_handler.off()
            else:
                logger.debug("Unknown Binary State request:")
                logger.debug(data)
            if success:
                # The echo is happy with the 200 status code and doesn't
                # appear to care about the SOAP response body
                soap = ""
                date_str = email.utils.formatdate(
                    timeval=None, localtime=False, usegmt=True)
                message = ("HTTP/1.1 200 OK\r\n"
                           "CONTENT-LENGTH: %d\r\n"
                           "CONTENT-TYPE: text/xml charset=\"utf-8\"\r\n"
                           "DATE: %s\r\n"
                           "EXT:\r\n"
                           "SERVER: Unspecified, UPnP/1.0, Unspecified\r\n"
                           "X-User-Agent: solvalou\r\n"
                           "CONNECTION: close\r\n"
                           "\r\n"
                           "%s" % (len(soap), date_str, soap))
                logger.debug(message)
                socket.send(message)
        else:
            logger.debug(data)

    def on(self):
        return False

    def off(self):
        return True

    @property
    def state(self):
        return self.relayState


# This is an example handler class. The fauxmo class expects handlers to be
# instances of objects that have on() and off() methods that return True
# on success and False otherwise.
#
# This example class takes two full URLs that should be requested when an on
# and off command are invoked respectively. It ignores any return data.

class rest_api_handler(object):
    def __init__(self, on_cmd, off_cmd):
        self.on_cmd = on_cmd
        self.off_cmd = off_cmd

    def on(self):
        r = requests.get(self.on_cmd)
        return r.status_code == 200

    def off(self):
        r = requests.get(self.off_cmd)
        return r.status_code == 200


DEFINITION = [
    # ['office lights', 'cmd=on&a=office', 'cmd=off&a=office'],
    # ['kitchen lights', 'cmd=on&a=kitchen', 'cmd=off&a=kitchen'],
    # ['bedroom lights', 'cmd=on&a=bedroom', 'cmd=off&a=bedroom'],
    # ['dining room lights', 'cmd=on&a=dining', 'cmd=off&a=dining'],
    # ['home room lights', 'cmd=on&a=homeroom', 'cmd=off&a=homeroom'],
    # ['my room lights', 'cmd=on&a=myroom', 'cmd=off&a=myroom'],
    ['something', 'cmd=on&a=mylight', 'cmd=off&a=mylight'],
]


SWITCHES = []


def load(listener, poller):
    http = 'http://{0}/ha-api?'.format(upnp_device.local_ip_address())
    for name, on, off in DEFINITION:
        device = [name, rest_api_handler(http+on, http+off)]
        SWITCHES.append(device)

    for one in SWITCHES:
        if len(one) == 2:
            # a fixed port wasn't specified, use a dynamic one
            one.append(0)
        switch = smart_switch(one[0], listener, poller, None,
                              one[2], action_handler=one[1])
