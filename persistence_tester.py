import httplib
from time import sleep

http_get = httplib.HTTPConnection( 'localhost:80' )
while (True):
  sleep( 1 )
  # if you have space, fetch jobs
  http_get.request( 'GET', '/loremepsum' );
  reply = http_get.getresponse()
  reply.read()
