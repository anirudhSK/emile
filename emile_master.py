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

      # problemid cannot be in KV, else something is wrong
      assert ( not flask.g.redis.exists( problemid ) )

      # Insert into redis, mark as unscheduled
      flask.g.redis.hmset( problemid, {'pb': protobuf, 'status' : 'unscheduled', 'retcode' : '-1' } );
      flask.g.redis.rpush( "queue", problemid )
      print "Pushed ",problemid, "into queue"

      # return problem id to optimizer
      return problemid

    if ( request.method == 'GET' ):
      # optimizer sends problemid
      problemid = request.headers[ 'problemid' ]

      # make sure it exists
      assert( flask.g.redis.exists( problemid ) )

      # determine current status of problem
      problem_dict = flask.g.redis.hgetall( problemid )

      # if it's still unscheduled or executing, return Processing to client
      if ( problem_dict['status'] == 'unscheduled' or problem_dict['status'][0:9] =='executing' ) :
        return make_response( problem_dict['status'],
                              202,
                              { 'returncode' : -1 } )

      # else return answer immediately.
      else :
        print "Answering immediately\n";
        return make_response( problem_dict['status'],
                              200,
                              { 'returncode' : problem_dict['retcode'] } )


# URL to GET questions that have been posted
@app.route("/question", methods = ['GET'])
def question():
    # worker is requesting work
    assert ( request.method == 'GET' )

    # Dequeue upto one problem
    problemid = flask.g.redis.lpop( "queue" )
    if ( problemid is None ):
      # No jobs in queue
      response = make_response( "No jobs!", 404 )

    else :
      # Pop from queue, mark as executing, and send problem
      print "Scheduled job with problemid", problemid
      assert( flask.g.redis.exists( problemid ) )
      flask.g.redis.hset( problemid, 'status', "executing" + str( time.time() ) )
      response = make_response( flask.g.redis.hget( problemid, 'pb' ),
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
      flask.g.redis.hset( id_of_answer, 'status', request.data )
      flask.g.redis.hset( id_of_answer, 'retcode', request.headers[ 'returncode' ] )
      return "OK"

if __name__ == "__main__":
    app.run( threaded = True, host = '0.0.0.0', port = 80 )
