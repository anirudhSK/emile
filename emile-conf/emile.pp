$sys_path = ['/usr/local/bin', '/opt/local/bin', '/usr/bin', '/usr/sbin', '/bin', '/sbin']

exec { "apt-get update":
      path => $sys_path,
}

$basic_packages = ['apache2', 'python-pip', 'libcurl4-openssl-dev', 'libboost-all-dev', 'libprotobuf-dev', 'protobuf-compiler', 'git', 'libapache2-mod-wsgi', 'redis-server', 'autoconf', 'build-essential', 'libtool', 'pkg-config', 'htop' ]

package { $basic_packages:
      ensure  => present,
      require => Exec["apt-get update"],
}

exec {"pip install flask":
      path    => $sys_path,
      require => Package[$basic_packages],
}

exec {"pip install redis":
      path    => $sys_path,
      require => Package[$basic_packages],
}

exec {"pip install protobuf":
      path    => $sys_path,
      require => Package[$basic_packages],
}

# Start redis
file { '/etc/redis/redis.conf':
      content => template('redis.templ')
}

# Start redis only if we have correct permissions.
service { "redis-server",
      ensure => "started",
      require => File['/etc/redis/redis.conf']
}      

# emile_master
file { '/var/www/emile_master/':
      content => template('redis.templ')
}

# emile_master_wsgi

# sites-enabled
file { '/etc/apache2/sites-enabled/emile_master.conf',
       content => template('emile_master.conf')
}

# Fix keep-alive

# Actually check out to a more sane directory and remove dependency on port 80
# check out emile to a normal folder and change DocumentRoot appropriately.
# Restart apache
# SIGUSR1 errors
