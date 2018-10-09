#!/bin/bash

while [ "$#" -gt 0 ]; do
    key="$1"
    case $key in
        --quick)
        QUICK="y"
        shift
        ;;
        --full)
        FULL="y"
        shift
        ;;
        *)
        echo "Unknown argument ${key}"
        exit 1
    esac
done


if [ "$QUICK" = y ]; then
    if [ "$FULL" = y ]; then
        echo "Cannot specify both --quick and --full"
        exit 1
    else
        echo "Since --quick is specified we skip tests of optional noise."
        exit 1
    fi
fi

if [ -f "${NETSIM}/config/settings.ini" ]; then
    echo "Temporarily moving settings.ini to use noisy settings..."
    mv "${NETSIM}/config/settings.ini" "${NETSIM}/config/_settings.ini"
fi

echo "Setting noisy settings.ini..."
cp "${NETSIM}/tests/auto/resources/noise_settings/settings.ini" "${NETSIM}/config/settings.ini"

echo "Starting SimulaQron sever (noisy setting)"
sh "${NETSIM}/run/startAll.sh"
sleep 1s
echo "Started SimulaQron sever (noise setting)"
python "${NETSIM}/tests/auto/optional_noise/test_optional_noise.py"

# Clean up
rm "${NETSIM}/config/settings.ini"
if [ -f "${NETSIM}/config/_settings.ini" ]; then
    echo "Moving back the old settings file"
    mv "${NETSIM}/config/_settings.ini" "${NETSIM}/config/settings.ini"
fi