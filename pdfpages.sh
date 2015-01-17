#!/bin/sh
pdfinfo $1 | grep Pages | sed 's/[^0-9]*//'
