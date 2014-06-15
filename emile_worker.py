import httplib
import subprocess
import os
import tempfile
from time import sleep

process_handles = []
remy_binary  = '/usr/local/google/home/anirudhsk/remy/src/rat-runner'
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
       problem_fd = tempfile.NamedTemporaryFile()
       answer_fd  = tempfile.NamedTemporaryFile()
       problem_fd.write( reply.read() )
       problem_fd.flush()
       args = [ remy_binary, 'problem=' + problem_fd.name, 'answer=' + answer_fd.name ]
       print "Running the problem we found with", args, "\n";
       fnull = open( os.devnull, 'w' )
       process_handles.append( { 'process' : subprocess.Popen( args,
                                                               stdout = fnull,
                                                               stderr = subprocess.STDOUT  ),
                                 'id'      : reply.getheader( 'problem_id' ),
                                 'problem' : problem_fd,
                                 'answer'  : answer_fd
                               },
                             )

  # check all handles
  remove_handles = []
  for i in range( 0, len( process_handles ) ):
    if (process_handles[i]['process'].poll() is not None):
      return_code  = process_handles[i]['process'].returncode
      http_post = httplib.HTTPConnection( 'localhost:5000' )
      process_handles[i]['answer'].flush();
      http_post.request( 'POST', '/answer',
                         body = process_handles[i]['answer'].read(),
                         headers = { 'problem_id' : process_handles[i]['id'],
                                     'return_code': return_code } )
      post_status = http_post.getresponse()
      assert( post_status.status == 200 );
      assert( post_status.read() == "OK" );
      # Close tmp files and reap dead processes
      process_handles[i]['problem'].close();
      process_handles[i]['answer'].close();
      remove_handles.append( process_handles[ i ] )

  # reap the ones that are done
  for handle in remove_handles:
    print "Removing handle", handle
    process_handles.remove( handle )

@atexit.register
def kill_subprocesses():
  for proc in process_handles:
    proc[0].kill()
