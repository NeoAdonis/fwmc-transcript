#!/usr/bin/env sh
# Clear GNU_STACK executable flag of libctranslate2>=4.4<4.6 library files.
# See https://github.com/OpenNMT/CTranslate2/issues/1849
find $VIRTUAL_ENV/lib -name "libctranslate2*.so.4.4.*" -o -name "libctranslate2*.so.4.5.*" | while read -r lib; do
    echo "Clear GNU_STACK executable flag of $lib"
    patchelf --clear-execstack "$lib"
done
