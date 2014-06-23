import httplib
import subprocess
import os
import tempfile
import sys
from time import sleep

if (len(sys.argv) < 4):
  print "Usage: python emile_worker.py POOL_SIZE server_addr remy_binary"
  exit(1)

POOL_SIZE = int( sys.argv[1] )
server_addr = sys.argv[2]
remy_binary = sys.argv[3]

http_get = httplib.HTTPConnection( server_addr );
http_post = httplib.HTTPConnection( server_addr );
POOL_SIZE = int(sys.argv[1])

def reap_process( proc, http_post ):
  assert( proc['process'].poll() is not None )
  returncode  = proc['process'].returncode
  proc['answer'].flush();
  http_post.request( 'POST', '/answer',
                     body = proc['answer'].read(),
                     headers = { 'problemid' : proc['id'],
                                 'returncode': returncode,
                                 'Host'       : 'www.emile.com' } )
  post_status = http_post.getresponse()
  assert( post_status.status == 200 );
  assert( post_status.read() == "OK" );
  # Close tmp files and reap dead processes
  proc['problem'].close();
  proc['answer'].close();

process_handles = []
while (True):
  if (len(process_handles) == 0):
    sleep( 1 )
  else:
    sleep( 0.01 )

  # if you have space, fetch jobs
  if (len(process_handles) < POOL_SIZE):
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
       # Can either be 404 or 200, nothing else
       assert( reply.status == 404 )

  # check all handles
  remove_handles = []
  for i in range( 0, len( process_handles ) ):
    if (process_handles[i]['process'].poll() is not None):
      reap_process( process_handles[ i ], http_post );
      remove_handles.append( process_handles[ i ] )

  # reap the ones that are done
  for handle in remove_handles:
    process_handles.remove( handle )
