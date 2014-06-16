from flask import Flask
from flask import request
from flask import make_response
from flask import render_template
import redis
import md5
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

      # find the unique problem ID
      problem_id = md5.new( protobuf ).hexdigest()

      # Queue up job if this problem_id doesn't exist in KV
      if ( not r.exists( problem_id ) ):
        # Insert into redis, mark as unscheduled
        r.rpush( problem_id, protobuf )
        r.rpush( problem_id, 'unscheduled' )
        r.rpush( problem_id, '-1' )
        r.rpush( "queue", problem_id )
        print "Queue length", r.llen("queue")

      # return problem id to optimizer
      return problem_id

    if ( request.method == 'GET' ):
      # optimizer sends problem_id
      problem_id = request.headers[ 'problem_id' ]

      # make sure it exists
      assert( r.exists( problem_id ) )

      # determine current status of problem
      status = r.lindex( problem_id, 1 )

      # if it's still unscheduled or executing, wait
      if ( status == 'unscheduled' or status[0:9] =='executing' ) :
        p = r.pubsub( ignore_subscribe_messages=True )
        p.subscribe( problem_id );
        for message in p.listen():
          p.close() # Close pubsub connection
          return make_response( r.lindex( problem_id, 1 ),
                                200,
                                { 'return_code' : r.lindex( problem_id, 2 ) } )

      # else return answer immediately.
      else :
        print "Answering immediately\n";
        return make_response( r.lindex( problem_id, 1 ),
                              200,
                              { 'return_code' : r.lindex( problem_id, 2 ) } )


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
      assert( r.exists( problem_id ) )
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
