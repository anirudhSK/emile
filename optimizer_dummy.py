import requests
import random
import answer_pb2
# TODO: Replicate this using libcurl
NUM_TASKS = 50
problem_id = [''] * NUM_TASKS

for i in range(0, NUM_TASKS):
  reply = requests.post( 'http://localhost:5000/problem', data = 'deadbeef' + str(random.random()) )
  problem_id[i] = reply.text

for i in range(0, NUM_TASKS):
  reply = requests.get( 'http://localhost:5000/problem', data = problem_id[i] )
  answer_proto = answer_pb2.Outcome()
  open("/tmp/interim", "wb").write( reply.content );
  answer_proto.ParseFromString( reply.content )
  print str( answer_proto )
