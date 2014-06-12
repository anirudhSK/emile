import requests
import multiprocessing
from time import sleep
from random import random
import logging

def myfunction(problem_id, problem):
##  try:
    sleep_time = random() * 5.0
    logging.info("Sleep time computed\n");
    sleep( sleep_time )
    print "Hello"
    # TODO: In general, you would do much more than just echo
    return (problem_id, problem)
##  except:
##    logging.critical("Errored out here\n");

def post_answers(problem_tuple):
  reply = requests.post( 'http://localhost:5000/answer', data = { 'problem_id' : problem_tuple[0], 'answer' : problem_tuple[1] } )
  logging.info("OK");
  print reply.text 

pool = multiprocessing.Pool(processes = 40)
while (True):
  reply = requests.get( 'http://localhost:5000/question' )
  print "Current pool cache size is", len(pool._cache)
  if (reply.status_code == 404):
    print "No problems, sleeping 1 second before trying again"
    sleep(1)
    continue
  else:
    print "applying async to the problem we found\n";
    pool.apply_async(myfunction, (reply.headers['problem_id'], reply.text), callback = post_answers );
  # Figure out how to limit the number of tasks
