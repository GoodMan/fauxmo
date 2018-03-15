# This XML is the minimum needed to define one of our virtual switches
# to the Amazon Echo
# working with Alexa Amazon Echo (2nd generation)
URL_SETUP_XML = "http://%(ip_address)s:%(port)s/setup.xml"

POST_UPNP = 'POST /upnp/control/basicevent1 HTTP/1.1'
GET_EVENT_SRV_XML = 'GET /eventservice.xml HTTP/1.1'
GET_SETUP_XML = 'GET /setup.xml HTTP/1.1'

ALEXA = {}

