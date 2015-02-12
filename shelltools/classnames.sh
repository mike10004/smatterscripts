#!/bin/sh

ROOT="."

if [ -d "src" ]; then
    ROOT="src"
fi

DIRS="${ROOT} $@"

for DIR in ${DIRS}; do
    MORE_CLASSES=$(find ${DIR} -type f -name "*.java" -print | \
                    xargs -n1 basename | \
                    sed 's/\.java//g')
    SIMPLE_CLASSNAMES="${SIMPLE_CLASSNAMES} ${MORE_CLASSES}"
done

echo ${SIMPLE_CLASSNAMES}


    
