import requests
import answer_pb2
import sys
NUM_TASKS = 10
problemid = [''] * NUM_TASKS
problem_file = sys.argv[ 1 ]

for i in range(0, NUM_TASKS):
  reply = requests.post( url  = 'http://localhost:80/problem',
                         headers = { 'Host' : 'www.emile.com' },
                         data = open( problem_file, "rb" ).read() )
  problemid[i] = reply.content
  print problemid[i]

for i in range(0, NUM_TASKS):
  reply = requests.get( url = 'http://localhost:80/problem',
                        headers = { 'problemid' : problemid[i], 'Host' : 'www.emile.com' } )
  print reply.status_code
  if ( reply.status_code  == 200 ) :
    answer_proto = answer_pb2.Outcome()
    print reply.content
    answer_proto.ParseFromString( reply.content )
    print reply.headers['returncode']
