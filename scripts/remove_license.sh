#!/bin/bash

set -e

source bash-colors.sh

# check cmd line args
if [[ "$#" -gt 2 ]] || [[ "$#" -eq 0 ]]; then
  echo "usage: $0 <target-dir> extension"
  echo "for example: $0 <target-dir> hpp"
  exit 1
fi

# store
targetdir=$1
if [ "$#" -gt 1 ];
then
  ext=$2
  pattern="*.${ext}"
else
  pattern='*.py'
fi

echo ""
echo "${fgyellow}Running on targetdir=$targetdir, extension=$pattern ${fgrst}"

allfiles=$(find $targetdir -name $pattern -o -name $pattern)
#echo ${allfiles[@]}
for file in $allfiles
do
  filename=$(basename $file)
  filedir=$(dirname $file)

  if ! grep -q 'BSD-3' "$file"; then
      if ! grep -q 'Ennio' "$file"; then
	 echo "found file $file without a license. Skipping."
	 #exit 11
      fi
  else
      filetmp=$(mktemp)
      tail -n +35 $file > $filetmp
      mv $filetmp $file
  fi
done
