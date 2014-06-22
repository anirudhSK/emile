$sys_path = ['/usr/local/bin', '/opt/local/bin', '/usr/bin', '/usr/sbin', '/bin', '/sbin']

exec { "apt-get update":
      path => $sys_path,
}

$basic_packages = ['apache2', 'python-pip', 'zip', 'libcurl4-openssl-dev',
                   'libboost1.48-all-dev', 'libprotobuf-dev', 'protobuf-compiler',
                   'git', 'libapache2-mod-wsgi', 'redis-server', automake,
                   'autoconf', 'build-essential', 'libtool', 'pkg-config', 'htop' ]

package { $basic_packages:
      ensure  => present,
      require => Exec["apt-get update"],
}

exec {"pip install flask requests redis protobuf":
      path    => $sys_path,
      require => Package[$basic_packages],
}

# REDIS
# Ensure redis is running
service { "redis-server":
      ensure => "running",
      require => Package["redis-server"],
}

# Enable UNIX sockets
file_line { 'unixsocket':
      path    => "/etc/redis/redis.conf",
      match   => "^.*unixsocket./var/run/redis/redis.sock$",
      line => "unixsocket /var/run/redis/redis.sock",
      notify  => Service["redis-server"],
      require => Package["redis-server"]
}

file { '/var/run/redis/redis.sock':
      mode => 777,
      require => Package["redis-server"],
      notify  => Service["redis-server"]
}

# APACHE
# Ensure apache is running
service { "apache2":
      ensure => "running",
      require => Package["apache2"],
}

# Increase timeout for Apache keep-alive messages to 1000 seconds
file_line { 'keepalive_line':
      path => "/etc/apache2/apache2.conf",
      match => "^KeepAliveTimeout.*$",
      line => "KeepAliveTimeout 1000",
      require => Package["apache2"]
}

# copy emile scripts to /var/www
file { '/var/www/emile_master':
      ensure => "directory",
      owner  => "www-data",
      group  => "root",
      require => Package["apache2"],
}

file { '/var/www/emile_master/emile_master.py':
      content => template('emile_master.py'),
      owner  => "www-data",
      group  => "root",
      require => File["/var/www/emile_master"],
}

file { '/var/www/emile_master/emile_master.wsgi':
      content => template('emile_master.wsgi'),
      owner  => "www-data",
      group  => "root",
      require => File["/var/www/emile_master"],
}

# sites-enabled for virtual host
file { '/etc/apache2/sites-enabled/emile_master.conf':
      notify => Service["apache2"],
      content => template('emile_master.conf'),
      require => [ File["/var/www/emile_master/emile_master.py"],
                   File["/var/www/emile_master/emile_master.wsgi"],
                   File_line["keepalive_line"] ],
}

# TODO: SIGUSR1 errors
