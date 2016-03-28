#!/bin/bash

if [ $# -ne 3 ]; then
  echo $0 /path/to/save_dir/save_file.png barcode_data [type]
  echo -e "\nArguements: "
  echo -e "[type]\t dummy,qr"
  exit 1
fi

# This is a dummy program
SCRIPTDIR=$(dirname "$(readlink -f "$0")")
SAVEFILE="$1"
BARCODE_DATA="$2"
BARCODE_TYPE=$3

case "$BARCODE_TYPE" in
    "dummy" )
      BARCODE="$SCRIPTDIR/dummy_barcode/dummy.png"
      cp "$BARCODE" "$SAVEFILE"
      ;;
    "qr" )
      qrencode -l H -s 5 -o $SAVEFILE  "$BARCODE_DATA"
      ;;
    *) 
      echo "Type $BARCODE_TYPE not supported."
      exit 1  
      ;;
esac
