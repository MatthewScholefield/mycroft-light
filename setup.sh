#!/usr/bin/env bash

apt_packages=""

show_usage() {
    echo "Usage: $1 [-f] [-h]"
    echo "Sets up and updates both python and native dependencies"
    exit 0
}

found_exe() {
    hash "$1" 2>/dev/null
}

found_lib() {
    local found=1
    local paths="$(ld --verbose | grep SEARCH_DIR | tr -s '; ' '\n' | grep -o '/[^"]*')"
    for p in $paths; do
        if [ -e "$p/$1" ]; then
            found=0
        fi
    done
    return $found
}

check_no_root() {
    if [ $(id -u) -eq 0 ]; then
      echo "This script should not be run as root or with sudo."
      exit 1
    fi
}

install_fann() {
    echo "Compiling FANN..."
    if ! found_exe cmake || ! found_exe curl; then
        echo "Please install cmake and curl first."
        exit 1
    fi
    rm -rf /tmp/fann-2.2.0
    curl -L https://github.com/libfann/fann/archive/2.2.0.tar.gz | tar xvz -C /tmp
    local prev_d="$(pwd)"
    cd /tmp/fann-2.2.0
    cmake .
    sudo make install
    cd "$prev_d"
}

create_virtualenv() {
    if [ ! -d ".venv/" ]; then
        python3 -m venv .venv/ --without-pip
        curl https://bootstrap.pypa.io/get-pip.py | .venv/bin/python
    fi
}

install_deps() {
    echo "Installing packages..."

    if found_exe sudo; then
        local SUDO=sudo
    fi

    while read line; do
        local exe=${line%%:*}
        local packages="$(echo ${line##*:} | tr -s ' ')"
        if found_exe $exe; then
            $SUDO $exe $packages
            break
        elif [ "$exe" = "other" ]; then
            if found_exe tput; then
                green="$(tput setaf 2)"
                blue="$(tput setaf 4)"
                reset="$(tput sgr0)"
            fi
            echo
            echo "${green}Could not find package manager"
            echo "${green}Make sure to manually install:${blue} $packages"
            echo $reset
        fi
    done < packages.txt

    if ! found_lib libfann.so; then
        install_fann
    fi
}

install_piwheels() {
    echo "Installing piwheels..."
    echo "
[global]
extra-index-url=https://www.piwheels.org/simple
" | sudo tee -a /etc/pip.conf
}

has_piwheels() { cat /etc/pip.conf 2>/dev/null | grep -qF 'piwheels'; }

hash_dependencies() {
    md5sum requirements.txt packages.txt > .installed
}

file_has_changed() {
    [ "$force_update" ] || [ ! -f .installed ] || ! < .installed grep "$1" | md5sum -c >/dev/null
}

[ "$1" = "-h" ] && show_usage "$0"
[ "$1" = "-f" ] && force_update="true"
check_no_root

set -e

if file_has_changed "packages.txt"; then
    install_deps
fi

create_virtualenv

if file_has_changed "requirements.txt"; then
    .venv/bin/pip install -r requirements.txt
    .venv/bin/pip install -e .
    .venv/bin/pip install -e mycroft_core
fi

arch="$(python -c 'import platform; print(platform.machine())')"
if [ "$arch" = "armv7l" ] && ! has_piwheels; then
    install_piwheels
fi

hash_dependencies

./start.sh setup
