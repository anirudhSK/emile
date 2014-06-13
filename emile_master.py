from flask import Flask
from flask import request
from flask import make_response
from flask import render_template
import redis
import uuid
import time
# What happens when the worker node fails while executing?
# Ans: Garbage collect it every now and then.

# Start redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Check that redis is actually running
try:
    r.ping()
except redis.ConnectionError:
    print "Redis isn't running. try `sudo service redis-server restart`"
    exit(0)

r.flushall()
# Setup Flask
app = Flask(__name__)

# URL to POST problems from optimizer and GET answers
@app.route("/problem", methods = ['POST', 'GET'])
def problem():
    if ( request.method == 'POST' ):
      # problem data from optimizer
      protobuf = request.data

      # pick a unique problem ID
      problem_id = str( uuid.uuid4() )

      # Insert into redis, mark as unscheduled
      r.rpush( problem_id, protobuf )
      r.rpush( problem_id, 'unscheduled' )
      r.rpush( problem_id, '-1' )

      # Queue up job
      r.rpush( "queue", problem_id )
      print "Queue length", r.llen("queue")

      # return problem id to optimizer
      return problem_id

    if ( request.method == 'GET' ):
      # optimizer sends problem_id
      problem_id = request.data
      #print problem_id

      # determine current status of problem
      status = r.lindex( problem_id, 1 )
      #print status

      # if it's still unscheduled or executing, wait
      if ( status == 'unscheduled' or status[0:9] =='executing' ) :
        p = r.pubsub( ignore_subscribe_messages=True )
        p.subscribe( problem_id );
        for message in p.listen():
          return r.lindex( problem_id, 1 )

      # else return answer immediately.
      else :
        return r.lindex( problem_id, 1 )

# URL to GET questions that have been posted
@app.route("/question", methods = ['GET'])
def question():
    # worker is requesting work
    assert ( request.method == 'GET' )

    # No jobs in queue
    if ( r.llen( "queue" ) == 0 ):
      response = make_response( "No jobs!", 404 )

    # Dequeue one problem alone
    else :
      # Pop from queue, mark as executing, and send problem
      problem_id = r.lpop( "queue" )
      print "Scheduled job, qsize is", r.llen( "queue" )
      #print problem_id
      assert( r.exists( problem_id ) )
      #print r.lindex( problem_id, 1 )
      r.lset( problem_id, 1, "executing" + str( time.time() ) )
      response = make_response( r.lindex( problem_id, 0 ),
                                200,
                                { 'problem_id' : problem_id } )
    return response

# URL to POST answers from worker
@app.route("/answer", methods = ['POST'])
def answer():
    # worker is POSTing answer
    if ( request.method == 'POST' ):
      id_of_answer = request.headers[ 'problem_id' ];
      assert( r.exists( id_of_answer ) )
      r.lset( id_of_answer, 1, request.data )
      r.lset( id_of_answer, 2, request.headers[ 'return_code' ] )
      r.publish( id_of_answer, "done" )
      return "OK"

if __name__ == "__main__":
    app.debug = True
    app.run( threaded = True )
