#!/bin/bash
#
# Interactive Setup to add Enphase Data to Powerwall InfluxDB Database

# Stop on Errors
set -e

# Set Globals
VERSION="0.1.1"
ENPHASE_ENV_FILE="./enphase.env"
TELEGRAF_LOCAL="../telegraf.local"
GRAFANA_ENV_FILE='../grafana.env'
GRAFANA_REQ="10.4.1-ubuntu"
GRAFANA_CUR=""
POWERWALL_YML_FILE='../powerwall.yml'
RUN_ONCE_FILE="../influxdb/run-once-local.sql"
ENPHASE_USER=""
ENPHASE_PW=""
IQ_GATEWAY_SN=""
IQ_GATEWAY_IP=""
IQ_GATEWAY_TOKEN=""
TOKEN_RENEW_DATE=''
DASHBOARD_ENPHASE="'enphase-basic-panel.json'"
POLICY_LINE="CREATE RETENTION POLICY local ON powerwall duration 0s replication 1"

if [ ! -f ../VERSION ]; then
    echo ""
    echo "ERROR: Can't find Powerwall-Dashboard installation. This script should be in a sub-directory of it."
    echo ""
    exit 1
fi

# Check for telegraf local file
if [ ! -f ${TELEGRAF_LOCAL} ]; then
    echo ""
    echo "Can't find '${TELEGRAF_LOCAL}' file.  It should have been created when installing Powerwall-Dashboard. Aborting."
    exit 1
fi

# Check for powerwall.yml
if [ ! -f ${POWERWALL_YML_FILE} ]; then
    echo ""
    echo "Can't find '${POWERWALL_YML_FILE}' file.  It should have been created when installing Powerwall-Dashboard. Aborting."
    exit 1
fi

# Check for grafana.env
if [ ! -f ${GRAFANA_ENV_FILE} ]; then
    echo ""
    echo "Can't find '${GRAFANA_ENV_FILE}' file.  It should have been created when installing Powerwall-Dashboard. Aborting."
    exit 1
fi

# Check Influx is up
if ! docker ps | grep -q "influxdb" > /dev/null 2>&1 ; then
    echo "InfluxDB Docker container not running. Check that Powerwall-Dashboard is installed correctly. Aborting."
    exit 1
fi

# Check powerwall database exists
if ! curl -s -G http://localhost:8086/query?pretty=true --data-urlencode  "q=SHOW databases" | grep -q "\"powerwall\"" 2>&1 ; then
    echo "powerwall database not found in influxDB.  Check that Powerwall-Dashboard is installed correctly."
    exit 1
fi

cat << EOF

Enphase Microinverter extensions to Powerwall-Dashboard (v${VERSION}) - SETUP
-----------------------------------------------------------------------------
This script will configure Powerwall-Dashboard to support data from Enphase
microinverters.  Prerequisites to running this script are:
1) Powerwall-Dashboard (github.com/jasonacox/Powerwall-Dashboard) has been installed and is running.
2) A directory containing this script and the supporting files has been placed under the Powerwall-Dashboard directory.
3) An account has been created for your system at enlighten.enphaseenergy.com.
4) The IP address on your local network for your Enphase Gateway is known.
5) The serial number of your Enphase Gateway is known (can be obtained from https://enlighten.enphaseenergy.com > System > Devices).
For more information, refer to the README.md file.
EOF

read -r -p "Continue? [y/N] " response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    exit 1
fi

# Check local retention policy exists.  If not, set up to be made
if ! curl -s -G http://localhost:8086/query --data-urlencode  "q=SHOW retention policies on powerwall" | grep -q "\"local\"," 2>&1 ; then
    echo "Retention Policy 'local' does not exist in InfluxDB dabatabase."
    if [ -f ${RUN_ONCE_FILE} ]; then
        if grep -qE "^${POLICY_LINE}$" "${RUN_ONCE_FILE}"; then
            echo "${RUN_ONCE_FILE} already has Retention Policy 'local' in it."
        else
            echo "Adding Retention Policy 'local' to existing ${RUN_ONCE_FILE}."
            echo ${POLICY_LINE} >> ${RUN_ONCE_FILE}
        fi
    else
        echo "Creating ${RUN_ONCE_FILE} with Retention Policy 'local' line in it ..."
        echo ${POLICY_LINE} > ${RUN_ONCE_FILE}
    fi
    rm -f ${RUN_ONCE_FILE}.done
else
    echo "Retention Policy 'local' already exists in InfluxDB powerwall database."
fi

# Load Enphase Credentials
if [ -f ${ENPHASE_ENV_FILE} ]; then
    export $(grep "ENPHASE_USER=" ${ENPHASE_ENV_FILE})
    export $(grep "ENPHASE_PW=" ${ENPHASE_ENV_FILE})
    export $(grep "IQ_GATEWAY_IP=" ${ENPHASE_ENV_FILE})
    export $(grep "IQ_GATEWAY_SN=" ${ENPHASE_ENV_FILE})
    export $(grep "IQ_GATEWAY_TOKEN=" ${ENPHASE_ENV_FILE})
    export $(grep "TOKEN_RENEW_DATE=" ${ENPHASE_ENV_FILE})
    echo "Current Enphase Credentials:"
    echo "ENPHASE_USER=" ${ENPHASE_USER}
    echo "ENPHASE_PW=" ${ENPHASE_PW}
    echo "IQ_GATEWAY_IP=${IQ_GATEWAY_IP}"
    echo "IQ_GATEWAY_SN=" ${IQ_GATEWAY_SN}
    echo "IQ_GATEWAY_TOKEN=${IQ_GATEWAY_TOKEN}"
    echo "TOKEN_RENEW_DATE=$(date --date=${TOKEN_RENEW_DATE} '+%Y-%b-%d')"
    echo ""
    read -r -p "Update these credentials? [y/N] " response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        rm -fv ${ENPHASE_ENV_FILE}
    else
        echo "Using existing ${ENPHASE_ENV_FILE}."
    fi
fi

# Create Enphase Settings
if [ ! -f ${ENPHASE_ENV_FILE} ]; then
    if [ ! -z "$ENPHASE_USER" ]; then
        TEMP=""
    	read -p "Enphase account user name (e.g., your Email address) (leave blank for ${ENPHASE_USER}): " TEMP
    	if [ ! -z "$TEMP" ]; then
    	    ENPHASE_USER=$TEMP
    	fi
    fi
    while [ -z "$ENPHASE_USER" ]; do
        read -p 'Enphase account user name (e.g., your Email address): ' ENPHASE_USER
    done
        
    if [ ! -z "$ENPHASE_PW" ]; then
        TEMP=""
    	read -p "Enphase account password (leave blank for ${ENPHASE_PW}): " TEMP
    	if [ ! -z "$TEMP" ]; then
    	    ENPHASE_PW=$TEMP
    	fi
    fi
    while [ -z "$ENPHASE_PW" ]; do
        read -p 'Enphase account password: ' ENPHASE_PW
    done

    if [ ! -z "$IQ_GATEWAY_IP" ]; then
        TEMP=""
    	read -p "Enphase IQ Gateway IP Address (leave blank for ${IQ_GATEWAY_IP}): " TEMP
    	if [ ! -z "$TEMP" ]; then
    	    IQ_GATEWAY_IP=$TEMP
    	fi
    fi
    while [ -z "$IQ_GATEWAY_IP" ]; do
        read -p 'Enphase IQ Gateway IP Address: ' IQ_GATEWAY_IP
    done
    
    if [ ! -z "$IQ_GATEWAY_SN" ]; then
        TEMP=""
    	read -p "Enphase IQ Gateway Serial Number (leave blank for ${IQ_GATEWAY_SN}): " TEMP
    	if [ ! -z "$TEMP" ]; then
    	    IQ_GATEWAY_SN=$TEMP
    	fi
    fi
    while [ -z "$IQ_GATEWAY_SN" ]; do
        read -p 'Enphase IQ Gateway Serial Number: ' IQ_GATEWAY_SN
    done
    
    if [ ! -z "$IQ_GATEWAY_TOKEN" ]; then
        read -r -p "Your Enphase Token will expire $(date --date=${TOKEN_RENEW_DATE} '+%Y-%b-%d') - renew it? [y/N] " response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            IQ_GATEWAY_TOKEN=""
        fi
    fi
    if [ -z "$IQ_GATEWAY_TOKEN" ]; then
        echo "fetching token ..."
        IQ_GATEWAY_TOKEN=$(python3 get-token.py "{\"email\":\"${ENPHASE_USER}\", \"pw\":\"${ENPHASE_PW}\", \"sn\":\"${IQ_GATEWAY_SN}\"}" 2>&1)
        echo "IQ_GATEWAY_TOKEN=${IQ_GATEWAY_TOKEN}"
        TOKEN_RENEW_DATE='@'$(expr $(date +%s) + 31536000)
    fi


    echo ENPHASE_USER=${ENPHASE_USER} >> ${ENPHASE_ENV_FILE}
    echo ENPHASE_PW=${ENPHASE_PW} >> ${ENPHASE_ENV_FILE}
    echo IQ_GATEWAY_IP=${IQ_GATEWAY_IP} >> ${ENPHASE_ENV_FILE}
    echo IQ_GATEWAY_SN=${IQ_GATEWAY_SN} >> ${ENPHASE_ENV_FILE}
    echo IQ_GATEWAY_TOKEN=${IQ_GATEWAY_TOKEN} >> ${ENPHASE_ENV_FILE}
    echo TOKEN_RENEW_DATE=${TOKEN_RENEW_DATE} >> ${ENPHASE_ENV_FILE}
fi

# Do telegraf.local
if ! grep -qE "api/v1/production/inverters" "${TELEGRAF_LOCAL}"; then
    echo "Adding Enphase lines to '${TELEGRAF_LOCAL}'."
    cat ./telegraf.enphase >> ${TELEGRAF_LOCAL}
else
    echo "'${TELEGRAF_LOCAL}' already has Enphase lines in it."
fi

# Update Gateway IP address & Token in telegraf.local
sed -i "s/\"https\:.*\/api\/v1\/production\/inverters\"/\"https\:\/\/"${IQ_GATEWAY_IP}"\/api\/v1\/production\/inverters\"/" "${TELEGRAF_LOCAL}"
# WARNING:  The below could change another Authorization in telegraf.local besides Enphase!
sed -i "s/headers = {\"Authorization\" = \"Bearer.*\"}/headers = {\"Authorization\" = \"Bearer "${IQ_GATEWAY_TOKEN}"\"}/" "${TELEGRAF_LOCAL}"

# Check Grafana version - offer to update to 10 if older.
GRAFANA_CUR=$(grep -E "image: grafana/grafana:" "${POWERWALL_YML_FILE}" | sed -n -e 's/^.*grafana://p')
if [ ${GRAFANA_CUR} != ${GRAFANA_REQ} ]; then
    
    read -r -p "Grafana version is currently ${GRAFANA_CUR}. ${GRAFANA_REQ} required to use Canvas panels.  Do you want to update? [y/N] " response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "Updating Grafana version to ${GRAFANA_REQ} in '${POWERWALL_YML_FILE}'."
            sed -i "s/grafana\/grafana:.\+-ubuntu$/grafana\/grafana:${GRAFANA_REQ}/" "${POWERWALL_YML_FILE}"
            echo "Refer to READ.ME for compatibility tips with Grafana ${GRAFANA_REQ}."
            GRAFANA_CUR=${GRAFANA_REQ}
        fi
else
    echo "Grafana version is currently ${GRAFANA_CUR}, Canvas panels supported."
fi

cat << EOF


------------------[ Final Setup Instructions ]-----------------

1) Run ./setup.sh in Dashboard home folder
2) Open Grafana at http://localhost:9000/ ... use admin/admin for login or Grafana credentials you created.
3) From 'Dashboard\Browse', select 'New/Import', browse to ${PWD}/enphase-dashboards and upload ${DASHBOARD_ENPHASE}.

EOF


if [ ${GRAFANA_CUR} = ${GRAFANA_REQ} ]; then
    read -r -p "Would you like to create graphic Canvas dashboards of your array? [y/N] " response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        # Add Pan & Zoom support if not there
        if ! grep -qE "GF_FEATURE_TOGGLES_ENABLE=canvasPanelPanZoom" "${GRAFANA_ENV_FILE}"; then
            echo "Adding Pan & Zoom support in '${GRAFANA_ENV_FILE}'."
            echo "" >> ${GRAFANA_ENV_FILE}
            echo "GF_FEATURE_TOGGLES_ENABLE=canvasPanelPanZoom" >> ${GRAFANA_ENV_FILE}
        else
            echo "'${GRAFANA_ENV_FILE}' already has Pan & Zoom support line in it."
        fi
        python3 ./enphase-canvas.py
    fi
fi

