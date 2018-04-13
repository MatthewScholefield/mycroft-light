#!/bin/sh

found_exe() {
    hash "$1" 2>/dev/null
}

check_no_root() {
    if [ $(id -u) -eq 0 ]; then
      echo "This script should not be run as root or with sudo."
      exit 1
    fi
}

check_dependencies() {
    if [ ! -f .installed ] || ! md5sum -c .installed > /dev/null
    then
        echo "Please update dependencies with ./setup.sh"
        if found_exe notify-send; then
            notify-send "Please update dependencies" "Run ./setup.sh"
        fi
    fi
}

set -eE  # Fail on errors
cd "$(dirname $(readlink -f "$0"))"
check_no_root
check_dependencies
.venv/bin/mycroft $@
