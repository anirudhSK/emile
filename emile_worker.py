import httplib
import subprocess
import os
import tempfile
from time import sleep

http_get = httplib.HTTPConnection( 'localhost:80' );
http_post = httplib.HTTPConnection( 'localhost:80' );

process_handles = []
remy_binary  = '/usr/local/google/home/anirudhsk/remy/src/rat-runner'
while (True):
  if (len(process_handles) == 0):
    sleep( 1 )
  else:
    sleep( 0.01 )

  # if you have space, fetch jobs
  if (len(process_handles) < 30):
    http_get.request( 'GET', '/question', '', { 'Host' : 'www.emile.com' } );
    reply = http_get.getresponse()
    if ( reply.status == 200 ):
       problem_fd = tempfile.NamedTemporaryFile()
       answer_fd  = tempfile.NamedTemporaryFile()
       problem_fd.write( reply.read() )
       problem_fd.flush()
       args = [ remy_binary, 'problem=' + problem_fd.name, 'answer=' + answer_fd.name ]
       print "Running the problem with problemid is", reply.getheader( 'problemid' ), "\n";
       fnull = open( os.devnull, 'w' )
       process_handles.append( { 'process' : subprocess.Popen( args,
                                                               stdout = fnull,
                                                               stderr = subprocess.STDOUT  ),
                                 'id'      : reply.getheader( 'problemid' ),
                                 'problem' : problem_fd,
                                 'answer'  : answer_fd
                               },
                             )
    else :
       reply.read()

  # check all handles
  remove_handles = []
  for i in range( 0, len( process_handles ) ):
    if (process_handles[i]['process'].poll() is not None):
      returncode  = process_handles[i]['process'].returncode
      process_handles[i]['answer'].flush();
      http_post.request( 'POST', '/answer',
                         body = process_handles[i]['answer'].read(),
                         headers = { 'problemid' : process_handles[i]['id'],
                                     'returncode': returncode,
                                     'Host'       : 'www.emile.com' } )
      post_status = http_post.getresponse()
      assert( post_status.status == 200 );
      assert( post_status.read() == "OK" );
      # Close tmp files and reap dead processes
      process_handles[i]['problem'].close();
      process_handles[i]['answer'].close();
      remove_handles.append( process_handles[ i ] )

  # reap the ones that are done
  for handle in remove_handles:
    process_handles.remove( handle )

@atexit.register
def kill_subprocesses():
  for proc in process_handles:
    proc[0].kill()
  http_get.close()
  http_post.close()
