import requests
import multiprocessing
from time import sleep

def myfunction(problem_id, problem):
  sleep(5)
  # TODO: In general, you would do much more than just echo
  return (problem_id, problem)

def post_answers(problem_tuple):
  reply = requests.post( 'http://localhost:5000/answer', data = { 'problem_id' : problem_tuple[0], 'answer' : problem_tuple[1] } )
  print reply.text 

pool = multiprocessing.Pool(processes = 30)
while (True):
  reply = requests.get( 'http://localhost:5000/question' )
  if (reply.status_code == 404):
    print "No problems, sleeping 1 second before trying again"
    sleep(1)
    continue
  else:
    print "applying async to the problem we found\n";
    pool.apply_async(myfunction, (reply.headers['problem_id'], reply.text), callback = post_answers );
  # Figure out how to limit the number of tasks
