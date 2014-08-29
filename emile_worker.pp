$sys_path = ['/usr/local/bin', '/opt/local/bin', '/usr/bin', '/usr/sbin', '/bin', '/sbin']

exec { "apt-get update":
      path => $sys_path,
}

$basic_packages = ['python-pip', 'libcurl4-openssl-dev',
                   'libboost1.48-all-dev', 'libprotobuf-dev', 'protobuf-compiler',
                   'git', 'automake, 'autoconf', 'build-essential', 'libtool',
                   'pkg-config', 'htop' ]

package { $basic_packages:
      ensure  => present,
      require => Exec["apt-get update"],
}

exec {"pip install requests":
      path    => $sys_path,
      require => Package[$basic_packages],
}

# TODO: SIGUSR1 errors
