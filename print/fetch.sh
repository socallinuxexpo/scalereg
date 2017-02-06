#!/bin/bash

SCRIPTDIR=$(dirname "$(readlink -f "$0")")

if [ $# -lt 1 ]; then
    echo Fetch the list of checked in attendees:
    echo $0 https://hostname
    echo Get/Save the password too:
    echo $0 https://hostname savepass
    exit 1
fi

if [ $# -gt 1 ]; then
    read -p "Username: " -s
    USER="$REPLY"
    echo
    read -p "Password: " -s
    PASS="$REPLY"
    echo
    wget -q --keep-session-cookies --save-cookies "$SCRIPTDIR/cookies.txt" --no-check-certificate -O /dev/null "$1/accounts/login/"
    TMPFILE=$(mktemp)
    wget -q --load-cookies "$SCRIPTDIR/cookies.txt" --save-cookies "$TMPFILE" --keep-session-cookies --post-data "username=$USER&password=$PASS&this_is_the_login_form=1&post_data=" --no-check-certificate -O /dev/null "$1/accounts/login/"
    mv "$TMPFILE" "$SCRIPTDIR/cookies.txt"
fi

wget -q --load-cookies "$SCRIPTDIR/cookies.txt" --no-check-certificate -O "$SCRIPTDIR/attendees.txt" "$1/reg6/checked_in/"
