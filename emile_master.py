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

# Setup Redis, TODO: Automatically check that UNIX sockets are enabled
redis_conn = redis.StrictRedis(unix_socket_path='/var/run/redis/redis.sock', db=0)

# Check that redis is actually running
try:
    redis_conn.ping()
except redis.ConnectionError:
    print "Redis isn't running. try `sudo service redis-server restart`"
    exit(0)

# Setup Flask
app = Flask(__name__)
app.debug = True

@app.before_request
def connect_to_redis():
      flask.g.redis = redis.StrictRedis(unix_socket_path='/var/run/redis/redis.sock', db=0)

# URL to POST problems from optimizer and GET answers
@app.route("/problem", methods = ['POST', 'GET'])
def problem():
    if ( request.method == 'POST' ):
      # problem data from optimizer
      protobuf = request.data

      # find the unique problem ID
      problemid = md5.new( protobuf ).hexdigest()

      # Queue up job if this problemid doesn't exist in KV
      if ( not flask.g.redis.exists( problemid ) ):
        # Insert into redis, mark as unscheduled
        flask.g.redis.rpush( problemid, protobuf )
        flask.g.redis.rpush( problemid, 'unscheduled' )
        flask.g.redis.rpush( problemid, '-1' )
        flask.g.redis.rpush( "queue", problemid )
        print "Queue length", flask.g.redis.llen("queue")

      # return problem id to optimizer
      return problemid

    if ( request.method == 'GET' ):
      # optimizer sends problemid
      problemid = request.headers[ 'problemid' ]

      # make sure it exists
      assert( flask.g.redis.exists( problemid ) )

      # determine current status of problem
      status = flask.g.redis.lindex( problemid, 1 )

      # if it's still unscheduled or executing, return Processing to client
      if ( status == 'unscheduled' or status[0:9] =='executing' ) :
        return make_response( status,
                              202,
                              { 'returncode' : -1 } )

      # else return answer immediately.
      else :
        print "Answering immediately\n";
        return make_response( flask.g.redis.lindex( problemid, 1 ),
                              200,
                              { 'returncode' : flask.g.redis.lindex( problemid, 2 ) } )


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
      problemid = flask.g.redis.lpop( "queue" )
      print "Scheduled job, qsize is", flask.g.redis.llen( "queue" )
      assert( flask.g.redis.exists( problemid ) )
      flask.g.redis.lset( problemid, 1, "executing" + str( time.time() ) )
      response = make_response( flask.g.redis.lindex( problemid, 0 ),
                                200,
                                { 'problemid' : problemid } )
    return response

# URL to POST answers from worker
@app.route("/answer", methods = ['POST'])
def answer():
    # worker is POSTing answer
    if ( request.method == 'POST' ):
      id_of_answer = request.headers[ 'problemid' ];
      assert( flask.g.redis.exists( id_of_answer ) )
      flask.g.redis.lset( id_of_answer, 1, request.data )
      flask.g.redis.lset( id_of_answer, 2, request.headers[ 'returncode' ] )
      return "OK"

if __name__ == "__main__":
    app.run( threaded = True, host = '0.0.0.0', port = 80 )
