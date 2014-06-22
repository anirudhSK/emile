#! /bin/bash
sudo puppet module install puppetlabs-stdlib
sudo puppet apply --templatedir ~/emile emile.pp
