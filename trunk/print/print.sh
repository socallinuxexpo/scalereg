#!/bin/bash

. settings.sh
SCRIPTDIR=$(dirname "$(readlink -f "$0")")

for PNGFILE in $SCRIPTDIR/out_png/*.png; do
  PDFFILE=$(basename "$PNGFILE")
  PDFFILE=$(echo $PDFFILE | sed 's/png$/pdf/')
  if [ ! -e "$SCRIPTDIR/out_print/$PDFFILE" ]; then
    echo printing $PDFFILE to $PRINTER
    convert -density 72 -units PixelsPerInch "$PNGFILE" \
      "$SCRIPTDIR/out_print/$PDFFILE"
    # Remove the echo to actually print
    #/usr/bin/lp -d "$PRINTER" "$SCRIPTDIR/out_print/$PDFFILE"
  fi
done
