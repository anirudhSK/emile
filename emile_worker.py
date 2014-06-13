import requests
import httplib
import subprocess
import os
from time import sleep
process_handles = []
remy_binary  = '/home/anirudh/remy/src/rat-runner'
answer_file =  '/home/anirudh/remy/src/test.answer'
while (True):
  if (len(process_handles) == 0):
    sleep( 1 )
  else:
    sleep( 0.01 )

  # if you have space, fetch jobs
  if (len(process_handles) < 30):
    http_get = httplib.HTTPConnection( 'localhost:5000' );
    http_get.request( 'GET', '/question' );
    reply = http_get.getresponse()
    if ( reply.status == 200 ):
       print "Running the problem we found\n";
       open( "/tmp/problem", "wb").write( reply.read() )
       args = [ remy_binary, 'problem=/tmp/problem', 'answer=' + str(answer_file) ]
       fnull = open( os.devnull, 'w' )
       process_handles.append( ( subprocess.Popen( args,
                                                   stdout = fnull,
                                                   stderr = subprocess.STDOUT  ),
                                 reply.getheader( 'problem_id' )
                               ),
                             )

  # check all handles
  remove_handles = []
  for i in range( 0, len( process_handles ) ):
    if (process_handles[i][0].poll() is not None):
      return_code  = process_handles[i][0].returncode
      remove_handles.append( process_handles[ i ] )
      http_post = httplib.HTTPConnection( 'localhost:5000' )
      http_post.request( 'POST', '/answer',
                         body = open( answer_file, 'rb' ).read(),
                         headers = { 'problem_id' : process_handles[i][1],
                                     'return_code': return_code } )
      post_status = http_post.getresponse()
      assert( post_status.status == 200 );
      assert( post_status.read() == "OK" );

  # reap the ones that are done
  for handle in remove_handles:
    print "Removing handle", handle
    process_handles.remove( handle )

@atexit.register
def kill_subprocesses():
  for proc in process_handles:
    proc[0].kill()
