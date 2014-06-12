import requests
import random
# TODO: Replicate this using libcurl

problem_id = [''] * 100

for i in range(0, 100):
  reply = requests.post( 'http://localhost:5000/problem', data = 'deadbeef' + str(random.random()) )
  problem_id[i] = reply.text

for i in range(0, 100):
  reply = requests.get( 'http://localhost:5000/problem', data = problem_id[i] )
  print reply.text
