#!/bin/sh

found_exe() {
    hash "$1" 2>/dev/null
}

install_deps() {
    if found_exe apt-get; then
        sudo apt-get install -y gcc make pkg-config automake libtool libasound2-dev libicu-dev
    elif found_exe dnf; then
        sudo dnf install -y gcc make pkgconfig automake libtool alsa-lib-devel
    elif found_exe pacman; then
        sudo pacman --noconfirm -S --needed install gcc make pkg-config automake libtool alsa-lib
    else
        if found_exe tput; then
            green="$(tput setaf 2)"
            blue="$(tput setaf 4)"
            reset="$(tput sgr0)"
        fi
        echo
        echo "${green}Could not find package manager"
        echo "${green}Make sure to manually install: ${blue}gcc make pkg-config automake libtool alsa-lib"
        echo $reset
    fi
}

if [ $# -ge 1 ] && [ "$1" == "clean" ]; then
    clean=true
else
    clean=false
fi

if $clean || [ ! -d "autom4te.cache" ]; then
    install_deps
    ./autogen.sh
fi
if $clean || [ ! -f 'Makefile' ]; then
    ./configure --with-audio=alsa --enable-shared --prefix=$(pwd)
fi
if $clean || [ ! -f 'mimic' ]; then
    if $clean; then
        make clean
    fi
    if  [ "$(free|awk '/^Mem:/{print $2}')" -lt "1572864" ] ; then
        cores=1
    else 
        cores=$(nproc)
    fi
    make -j$cores
fi

