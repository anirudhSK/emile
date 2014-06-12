import requests
# TODO: Replicate this using libcurl
reply = requests.post( 'http://localhost:5000/problem', data = 'deadbeef' )
problem_id = reply.text
reply = requests.get( 'http://localhost:5000/problem', data = problem_id )
print reply.text
