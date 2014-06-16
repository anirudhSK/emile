import flask
from flask import Flask
from flask import request
from flask import make_response
from flask import render_template
import redis
import md5
import time
# What happens when the worker node fails while executing?
# Ans: Garbage collect it every now and then.

# Setup Redis
redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_conn.flushall()

# Check that redis is actually running
try:
    redis_conn.ping()
except redis.ConnectionError:
    print "Redis isn't running. try `sudo service redis-server restart`"
    exit(0)

# Setup Flask
app = Flask(__name__)

@app.before_request
def connect_to_redis():
      flask.g.redis = redis.StrictRedis(host='localhost', port=6379, db=0)

# URL to POST problems from optimizer and GET answers
@app.route("/problem", methods = ['POST', 'GET'])
def problem():
    if ( request.method == 'POST' ):
      # problem data from optimizer
      protobuf = request.data

      # find the unique problem ID
      problem_id = md5.new( protobuf ).hexdigest()

      # Queue up job if this problem_id doesn't exist in KV
      if ( not flask.g.redis.exists( problem_id ) ):
        # Insert into redis, mark as unscheduled
        flask.g.redis.rpush( problem_id, protobuf )
        flask.g.redis.rpush( problem_id, 'unscheduled' )
        flask.g.redis.rpush( problem_id, '-1' )
        flask.g.redis.rpush( "queue", problem_id )
        print "Queue length", flask.g.redis.llen("queue")

      # return problem id to optimizer
      return problem_id

    if ( request.method == 'GET' ):
      # optimizer sends problem_id
      problem_id = request.headers[ 'problem_id' ]

      # make sure it exists
      assert( flask.g.redis.exists( problem_id ) )

      # determine current status of problem
      status = flask.g.redis.lindex( problem_id, 1 )

      # if it's still unscheduled or executing, wait
      if ( status == 'unscheduled' or status[0:9] =='executing' ) :
        p = flask.g.redis.pubsub( ignore_subscribe_messages=True )
        p.subscribe( problem_id );
        print "Still waiting ..."
        for message in p.listen():
          print "Got notification"
          p.close() # Close pubsub connection
          return make_response( flask.g.redis.lindex( problem_id, 1 ),
                                200,
                                { 'return_code' : flask.g.redis.lindex( problem_id, 2 ) } )

      # else return answer immediately.
      else :
        print "Answering immediately\n";
        return make_response( flask.g.redis.lindex( problem_id, 1 ),
                              200,
                              { 'return_code' : flask.g.redis.lindex( problem_id, 2 ) } )


# URL to GET questions that have been posted
@app.route("/question", methods = ['GET'])
def question():
    # worker is requesting work
    assert ( request.method == 'GET' )

    # No jobs in queue
    if ( flask.g.redis.llen( "queue" ) == 0 ):
      response = make_response( "No jobs!", 404 )

    # Dequeue one problem alone
    else :
      # Pop from queue, mark as executing, and send problem
      problem_id = flask.g.redis.lpop( "queue" )
      print "Scheduled job, qsize is", flask.g.redis.llen( "queue" )
      assert( flask.g.redis.exists( problem_id ) )
      flask.g.redis.lset( problem_id, 1, "executing" + str( time.time() ) )
      response = make_response( flask.g.redis.lindex( problem_id, 0 ),
                                200,
                                { 'problem_id' : problem_id } )
    return response

# URL to POST answers from worker
@app.route("/answer", methods = ['POST'])
def answer():
    # worker is POSTing answer
    if ( request.method == 'POST' ):
      id_of_answer = request.headers[ 'problem_id' ];
      assert( flask.g.redis.exists( id_of_answer ) )
      flask.g.redis.lset( id_of_answer, 1, request.data )
      flask.g.redis.lset( id_of_answer, 2, request.headers[ 'return_code' ] )
      flask.g.redis.publish( id_of_answer, "done" )
      return "OK"

if __name__ == "__main__":
    app.debug = True
    app.run( threaded = True, host = '0.0.0.0', port = 5000 )
