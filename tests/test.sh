#!/bin/bash
set -ex

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

cd "$SCRIPTDIR/assets/pembroke_werke_1766/data"
ocrd-typegroups-classifier \
    -l DEBUG \
    -g PHYS_0011 \
    -m mets.xml \
    -I DEFAULT \
    -O OCR-D-FONTIDENT \
    -P stride 143

outfile="OCR-D-FONTIDENT/FILE_0010_OCR-D-FONTIDENT.xml"
expected_fontfamily='fraktur'
if egrep -q "<pc:TextStyle fontFamily=\"$expected_fontfamily.*" "$outfile"; then
    echo 'Good classification result:'
    grep '<pc:TextStyle fontFamily=' "$outfile"
else
    echo 'Bad classification result:'
    grep '<pc:TextStyle fontFamily=' "$outfile"
    exit 1
fi
