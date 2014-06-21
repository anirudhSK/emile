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

# Start redis only after changing file
service { "redis-server",
      ensure => "stopped"
}

# Copy over redis conf
file { '/etc/redis/redis.conf':
      content => template('redis.templ'),
      notify  => Service["redis-server"]
}

# Start redis only if we have the files setup
service { "redis-server",
      ensure => "running",
      enable => "true", 
      require => Package["redis-server"]
}

# Ensure apache is running
service { "apache",
      ensure => "running",
      enable => "true",
      require => Package["apache2"]
}

# Apache keep-alive messages
file { '/etc/apache2/apache2.conf',
      content => template('apache2.templ'),
      notify  => Service["apache"]
}

# sites-enabled for virtual host
file { '/etc/apache2/sites-enabled/emile_master.conf',
      notify => Service["apache"]
      content => template('emile_master.conf')
      require => [ File["/var/www/emile_master/emile_master.py"],
                   File["/var/www/emile_master/emile_master.py"] ]
}

# check out emile to a normal folder and change DocumentRoot appropriately.
file { '/var/www/emile_master',
      ensure => "directory",
      owner  => "www-data",
      group  => "root",
      require => Package["apache2"]
}

file { '/var/www/emile_master/emile_master.py',
      content => template('emile_master.py'),
      owner  => "www-data",
      group  => "root",
      require => File["/var/www/emile_master"]
}

file { '/var/www/emile_master/emile_master.wsgi',
      content => template('emile_master.wsgi'),
      owner  => "www-data",
      group  => "root",
      require => File["/var/www/emile_master"]
}

# SIGUSR1 errors
