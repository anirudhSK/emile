#! /bin/bash
sudo puppet module install puppetlabs-stdlib
sudo puppet apply --debug --templatedir ~/emile emile.pp
