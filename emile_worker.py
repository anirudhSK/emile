import requests
import subprocess
from time import sleep
from random import random
process_handles = []
while (True):
  if (len(process_handles) == 0):
    sleep( 1 )
  else:
    sleep( 0.01 )

  # if you have space, fetch jobs
  if (len(process_handles) < 30):
    reply = requests.get( 'http://localhost:5000/question' )
    if ( reply.status_code == 200 ):
       print "Running the problem we found\n";
       print "Sleep time ",str(random() * 5.0)
       args = [ '/bin/sleep', str( random() * 5.0 ) ]
       # TODO: args = [ '/remy/', 'if=...', 'of=...', ]
       process_handles.append( ( subprocess.Popen( args ), reply.text, reply.headers[ 'problem_id' ] ) )

  # check all handles
  remove_handles = []
  for i in range( 0, len( process_handles ) ):
    if (process_handles[i][0].poll() is not None):
      return_code  = process_handles[i][0].returncode
      remove_handles.append( process_handles[ i ] )
      post_status = requests.post( 'http://localhost:5000/answer',
                                    data = { 'problem_id' : process_handles[i][2],
                                             'answer' : process_handles[i][1],
                                             'return_code' : return_code } )

  # reap the ones that are done
  for handle in remove_handles:
    print "Removing handle", handle
    process_handles.remove( handle )

@atexit.register
def kill_subprocesses():
  for proc in process_handles:
    proc[0].kill()
