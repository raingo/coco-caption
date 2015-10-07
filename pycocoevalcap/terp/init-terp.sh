#!/bin/bash
# vim ft=sh

cache=$1
if [ -z "$cache" ]
then
  echo $0 localdisk-fast-large-cache-for-ppdb
  exit
fi

git clone git@github.com:snover/terp.git terp-src
curl http://wordnetcode.princeton.edu/3.0/WordNet-3.0.tar.gz | tar xfz -

java_path=`which java`
java_dir=`dirname $java_path`/../
wn3_dir=`pwd`/WordNet-3.0
terp_dir=`pwd`/terp-src

cd terp-src
# -Dbuild.compiler=javac1.7 is necessary for javac1.8
ant -Dbuild.compiler=javac1.7
bin/setup_bin.sh $terp_dir $java_dir $wn3_dir

mkdir -p $cache
mv data $cache
ln -s $cache/data
wget https://github.com/snover/terp/releases/download/v2/unfiltered_phrasetable.txt.gz -P data/ -nc
rm data/phrases.db -R
gunzip -f data/unfiltered_phrasetable.txt.gz
bin/create_phrasedb data/unfiltered_phrasetable.txt data/phrases.db

./bin/terpa -h test/sample.hyp.sgm -r test/sample.ref.sgm -P data/phrases.db
