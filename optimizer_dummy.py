import requests
import answer_pb2
# TODO: Replicate this using libcurl
NUM_TASKS = 50
problem_id = [''] * NUM_TASKS
problem_file = '/home/anirudh/remy/test.problem'

for i in range(0, NUM_TASKS):
  reply = requests.post( url  = 'http://localhost:5000/problem',
                         data = open( problem_file, "rb" ).read() )
  problem_id[i] = reply.content

for i in range(0, NUM_TASKS):
  reply = requests.get( 'http://localhost:5000/problem', data = problem_id[i] )
  answer_proto = answer_pb2.Outcome()
  answer_proto.ParseFromString( reply.content )
  print str( answer_proto )
