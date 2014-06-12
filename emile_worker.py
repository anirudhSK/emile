import requests

# Get problems
reply = requests.get( 'http://localhost:5000/question' )
print reply.text

# Return answers
#reply = requests.post( 'http://localhost:5000/answer', data = { 'problem_id' :   
