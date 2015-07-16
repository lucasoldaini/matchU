#!/bin/bash

espath="$1"

if [ -z "$espath" ]; then
    >&2 echo "No elasticsearch path provided"
    exit 1
fi

 for f in $espath/lib/*.jar; do
    bf=`basename $f`
    if [[ "$bf" == "elasticsearch"* ]]; then
        eslib=$f;
    fi
done

if [ -z "$eslib" ]; then
    >&2 echo "No elasticsearch lib found in \"$espath\""
    exit 1
fi

mkdir -p bin
mkdir -p target

javac -cp $eslib -d bin/ src/umls/*.java
cd bin
jar cf ../target/umls.jar umls/*.class
cd ..

mkdir -p $espath/plugins/umls/
mv target/umls.jar $espath/plugins/umls/

plugin_str="script.native.umls.type: umls.UmlsScoringScriptFactory"
has_str=`cat $espath/config/elasticsearch.yml | grep "$plugin_str"`
if [ -z "$has_str" ]; then
    echo -e "\n$plugin_str" >> $espath/config/elasticsearch.yml
fi
