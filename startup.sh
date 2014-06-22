#! /bin/bash
set -x
sudo service apache2 stop
redis-cli flushall
sudo rm /var/log/apache2/error.log
sudo cp emile_master.py /var/www/emile_master
sudo cp emile_master.wsgi /var/www/emile_master
sudo chown www-data /var/www/emile_master/emile_master.py
sudo chown www-data /var/www/emile_master/emile_master.wsgi
sudo service redis-server restart
sudo chmod 777 /var/run/redis/redis.sock
sudo service apache2 start
