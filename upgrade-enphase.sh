#!/bin/bash
#
# upgrade-enphase.sh
# v0.6.0
# Interactive Setup to update enphase-dashboard installation

# Stop on Errors
set -e

# Set Globals

# Checkfirst for updated upgrade script. Then restart script outside of install directory
CWD=$(pwd)
if [ ! "$0" = "./tmp.sh" ]; then
    # Grab latest upgrade script from GitHub and run it
    curl -sL --output tmp.sh https://raw.githubusercontent.com/scotthibbard/enphase-dashboard/main/upgrade.sh
    OUTPUT=$(cat tmp.sh)
    if [[ ${OUTPUT} = "404: Not Found" ]]; then  
    	echo "No upgrade online, using this one"
    	cp "$0" tmp.sh
    else
    	echo "upgrade online"
    fi
    mv tmp.sh ..
    cd ..
    exec bash ./tmp.sh $CWD
fi

cat << EOF

Enphase Microinverter extensions update script.
-----------------------------------------------------------------------------
This script looks online for updates to the enphase-dashboard
installation.  If one is found, it will offer to update.
EOF

if [ ! -f "${1}/VERSION" ]; then
    echo ""
    echo "ERROR: Can't find enphase-dashboard installed version."
    echo ""
    exit 1
else
    INSTALLED_V=`cat ${1}/VERSION`
fi

ONLINE_V=$(curl -sL https://raw.githubusercontent.com/schibbard/enphase-dashboard/main/VERSION)
if [ ${INSTALLED_V} = ${ONLINE_V} ]; then
	echo "${INSTALLED_V} installed, ${ONLINE_V} available online. System is up-to-date."
	rm tmp.sh
	exit 1
fi

read -r -p "${INSTALLED_V} is currently installed, ${ONLINE_V} is available online. Would you like to upgrade? [y/N] " response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    exit 1
fi

mv ./enphase-dashboard ./enphase-dashboard-old
git clone https://github.com/SCHibbard/enphase-dashboard.git
cp -n ./enphase-dashboard-old/*.save enphase-dashboard
cp -n ./enphase-dashboard-old/*.json enphase-dashboard
cp -n ./enphase-dashboard-old/*.env enphase-dashboard

echo
echo "Successfully updated to ${ONLINE_V}, and copied environment variables, arrays and jsons to new install."
read -r -p "Previous version is in enphase-dashboard-old directory. Delete that? [y/N] " response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
	rm tmp.sh
    exit 1
fi

rm -r -f ./enphase-dashboard-old
rm tmp.sh

