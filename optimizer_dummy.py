import requests
import answer_pb2
NUM_TASKS = 10
problemid = [''] * NUM_TASKS
problem_file = '/usr/local/google/home/anirudhsk/remy/test.problem'

for i in range(0, NUM_TASKS):
  reply = requests.post( url  = 'http://localhost:80/problem',
                         headers = { 'Host' : 'www.emile.com' },
                         data = open( problem_file, "rb" ).read() )
  problemid[i] = reply.content
  print problemid[i]

for i in range(0, NUM_TASKS):
  reply = requests.get( url = 'http://localhost:80/problem',
                        headers = { 'problemid' : problemid[i], 'Host' : 'www.emile.com' } )
  answer_proto = answer_pb2.Outcome()
  print reply.content
  answer_proto.ParseFromString( reply.content )
  print reply.headers['returncode']
