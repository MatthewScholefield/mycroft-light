#!/usr/bin/env bash

apt_packages=""

show_usage() {
    echo "Usage: $1 [-f]"
    echo "Sets up and updates both python and native dependencies"
    exit 0
}

found_exe() {
    hash "$1" 2>/dev/null
}

found_lib() {
    found=1
    paths="$(ld --verbose | grep SEARCH_DIR | tr -s '; ' '\n' | grep -o '/[^"]*')"
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
    prev_d="$(pwd)"
    cd /tmp/fann-2.2.0
    cmake .
    sudo make install
    cd "$prev_d"
}

find_virtualenv_root() {
    if [ -z "$WORKON_HOME" ]; then
        VIRTUALENV_ROOT=${VIRTUALENV_ROOT:-"${HOME}/.virtualenvs/mycroft-light"}
    else
        VIRTUALENV_ROOT="$WORKON_HOME/mycroft-light"
    fi
}

activate_virtualenv() {
    source "$VIRTUALENV_ROOT/bin/activate"
}

create_virtualenv() {
    if [ ! -d "$VIRTUALENV_ROOT" ]; then
        mkdir -p $(dirname "$VIRTUALENV_ROOT")
        python3 -m venv "$VIRTUALENV_ROOT" --without-pip
        activate_virtualenv
        curl https://bootstrap.pypa.io/get-pip.py | python3
    fi
}

install_deps() {
    echo "Installing packages..."

    if found_exe sudo; then
        SUDO=sudo
    fi

    while read line; do
        exe=${line%%:*}
        packages="$(echo ${line##*:} | tr -s ' ')"
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

install_mycroft() {
    "$VIRTUALENV_ROOT/bin/python3" -m pip install -e . --upgrade
}

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

find_virtualenv_root
create_virtualenv
activate_virtualenv

if file_has_changed "requirements.txt"; then
    install_mycroft
fi

hash_dependencies
