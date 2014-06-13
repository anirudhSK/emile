import requests
import answer_pb2
# TODO: Replicate this using libcurl
NUM_TASKS = 10
problem_id = [''] * NUM_TASKS
problem_file = '/usr/local/google/home/anirudhsk/remy/test.problem'

for i in range(0, NUM_TASKS):
  reply = requests.post( url  = 'http://localhost:5000/problem',
                         data = open( problem_file, "rb" ).read() )
  problem_id[i] = reply.content

for i in range(0, NUM_TASKS):
  reply = requests.get( url = 'http://localhost:5000/problem',\
                        headers = { 'problem_id' : problem_id[i] } )
  answer_proto = answer_pb2.Outcome()
  answer_proto.ParseFromString( reply.content )
  print reply.headers['return_code']
