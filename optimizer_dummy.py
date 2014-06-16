import requests
import answer_pb2
NUM_TASKS = 10
problem_id = [''] * NUM_TASKS
problem_file = '/usr/local/google/home/anirudhsk/remy/test.problem'

for i in range(0, NUM_TASKS):
  reply = requests.post( url  = 'http://localhost:80/problem',
                         headers = { 'Host' : 'www.emile.com' },
                         data = open( problem_file, "rb" ).read() )
  problem_id[i] = reply.content
  print problem_id[i]

for i in range(0, NUM_TASKS):
  reply = requests.get( url = 'http://localhost:80/problem',
                        headers = { 'problem_id' : problem_id[i], 'Host' : 'www.emile.com' } )
  answer_proto = answer_pb2.Outcome()
  answer_proto.ParseFromString( reply.content )
  print reply.headers['return_code']
