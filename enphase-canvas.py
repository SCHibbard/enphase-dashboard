#!/usr/bin/env python
# enphase-canvas.py
# -*- coding: utf-8 -*-

"""
Python script to interactively create a Grafana dashboard with canvas panels
graphically depicting a Solar array with Enphase micro-inverters.

Needed to run:  no additional python packages should be required beyond the standard package.
"""

import copy
import json
import os
import shutil
import signal
import sys

# Constants
BUILD = "0.5.0"
DEBUG = False
MAX_WIDTH = 30
MAX_HEIGHT = 30
MAX_INVERTERS = 99
MIN_GRAFANA = "10.4.1"
MIN_PYTHON = (3, 5)
BORDER_COLORS = ["#8AB8FF", "#FF780A", "#F2495C", "#5794F2", "#B877D9", "#705DA0", "#37872D", "#FADE2A",
                 "#447EBC", "#C15C17", "#890F02", "#0A437C", "#6D1F62", "#584477", "#B7DBAB", "#F4D598",
                 "#70DBED", "#F9BA8F", "#F29191", "#82B5D8", "#E5A8E2", "#AEA2E0", "#629E51", "#E5AC0E",
                 "#64B0C8", "#E0752D", "#BF1B00", "#634836", "#D8FF8A", "#53261F", "#A1FF8A", "#CAC5A2",
                 "#386371", "#74124E", "#707ED5", "#79FAC4", "#5771F2", "#7C6E13", "#629E51", "#F21191",
                 "#788AFA", "#2F6750", "#9D8B1B", "#354B57", "#81405B", "#FAFF8A", "#5B435A", "#FA78AE",
                 "#651C25", "#FF0000"]
TEMPERATURE_COLORS = ["#323232", "#3C3C3C", "#464646", "#505050", "#5A5A5A", "#0000FF", "#0019FF", "#0032FF",
                      "#004BFF", "#0064FF", "#007DFF", "#0096FF", "#00AFFF", "#00C8FF", "#00E1FF", "#00F0FF",
                      "#00FFE1", "#00FFC8", "#00FFAF", "#00FF96", "#00FF7D", "#00FF64", "#00FF4B", "#00FF32",
                      "#00FF19", "#00FF00", "#19FF00", "#32FF00", "#4BFF00", "#64FF00", "#7dFF00", "#96FF00",
                      "#AFFF00", "#C8FF00", "#E1FF00", "#F0FF00", "#FFFF00", "#FFF000", "#FFE100", "#FFC800",
                      "#FFAF00", "#FF9600", "#FF7D00", "#FF6400", "#FF4B00", "#FF3200", "#FF1900", "#FF0000"]

refIdList = ['', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
             'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
UID_CurOut = "x0x0SolarPanelCurOutputTemplate"
UID_TtlProd = "YoYoTotalProdPeriod"
UID_Time_Series = "ZoZoTimeSeries"

# Global variables
p_array = []        # main deta for array creation
                    # element [0]] = basics (array dims, custom panel # choice):
                        # {'R': x, 'C': y, 'Custom': <True/False>}
                    # elements [1] - [x] are each serial number, with array coordinates:
                        # {"SN": "<serial#>)", "R": x, "C": y, "Panel": <panel#>, "Color": "<color code>>"}


# ############################################################################
# get_panel_data() prompts for the serial number for a given panel in array,
# and optionally custom panel number.  p_array is updated. Arguments:
#  loc: an r-c dictionary of panel location (coordinates)
#  p_no:  next panel to use (ignored if customer numbering)
#  editing: true if editing a panel (preserves standard panel number)
# updated default panel number is returned
# Notes:
#   If editing & using default panel numbering, panels renumbered in RC order
# ############################################################################
def get_panel_data(loc: dict, p_no: int, editing: bool) -> int:
    global p_array

    # Save off existing if editing
    old_sn = 0
    old_pn = 0
    for i in range(1, len(p_array)):
        if p_array[i]['R'] == loc['R'] and p_array[i]['C'] == loc['C']:
            old_sn = p_array[i]['SN']
            old_pn = p_array[i]['Panel']
            p_array[i].update({'R': 0, 'C': 0, 'Panel': 0})
            break

    while True:
        if editing:
            sn = input(f"Serial number for location R{loc['R']:02d}C{loc['C']:02d} (0 for blank, ENTER to use {old_sn}): ")
            if sn == "":
                sn = str(old_sn)
        else:
            sn = input(f"Serial number for location R{loc['R']:02d}C{loc['C']:02d} (0 for blank): ")
        if not sn.isnumeric():
            print("only positive integer values allowed.")
            continue
        sn = int(float(sn))
        if sn == 0:  # blank panel?
            if editing:         # If editing, erase exiting info
                for i in range(1, len(p_array)):
                    if p_array[i]['R'] == loc['R'] and p_array[i]['C'] == loc['C']:
                        p_array[i].update({'R': 0, 'C': 0, 'Panel': 0, 'Color': 0})
            break

        # Check that Serial number exists, and has not been used already
        err_msg = 'Serial number not found in array.'
        for i in range(1, len(p_array)):
            if p_array[i]['SN'] == str(sn):
                if p_array[i]['R'] != 0 or p_array[i]['C'] != 0:
                    err_msg = 'That serial number is already in use.'
                    sn = 0
                    break
                else:  # Found SN, and it's not in use yet
                    err_msg = ''
                    if editing:
                        p_no = p_array[i]['Panel']
                    break
        if err_msg != '':
            print(err_msg)
            continue
        else:           # Found serial number & it is not yet used
            break

    # Have good SN, handle custom panel number if selected
    if sn != 0 and p_array[0]['Custom'] is True:
        while True:
            if editing:
                p_no = input(
                    f"\tCustom panel number for location R{loc['R']:02d}C{loc['C']:02d} (ENTER to use {old_pn}): ")
                if p_no == "":
                    p_no = str(old_pn)
            else:
                p_no = input(f"\tCustom panel number for location R{loc['R']:02d}C{loc['C']:02d}: ")

            if not p_no.isnumeric():
                print("\tOnly integer values allowed.")
                continue
            p_no = int(float(p_no))
            if p_no <= 0 or p_no > len(p_array) - 1:
                print(f"\tCustom Panel number must be between 1 and {len(p_array) - 1}.")
                continue
            # Check that custom panel number is not already used
            dup = False
            for i in range(1, len(p_array)):
                if p_array[i]['Panel'] == p_no:
                    print('\tThat custom panel number is already in use.')
                    dup = True
            if dup:
                continue
            else:
                break              # Custom panel number is in range & unique

    # Have valid serial number & panel number, update
    if sn != 0:
        found = False
        for i in range(1, len(p_array)):
            if p_array[i]['SN'] == str(sn):
                p_array[i].update({'R': loc['R'], 'C': loc['C'], 'Panel': p_no, 'Color': 0})
                p_no += 1  # in case using default, ignored if custom
                found = True
                break
        if not found:
            sys.exit("Fatal error re-searching for serial #")

    if editing and not p_array[0]['Custom']:                  # Editing w/ default panel #s, renumber all
        return renumber_panels()
    else:
        return p_no


# ############################################################################
# get_rc() prompts for a row/column pair, dictionary returned.
# prompt is a string to use in user input prompt, together with vert & horiz
# limits is a dict pair of max values {'c(width)': x, 'r(height)': y}
# ############################################################################
def get_rc(prompt: str, vert: str, horiz: str, limit: dict) -> dict:
    rc_ok = False
    rc = {}
    while not rc_ok:
        rc = {'R': 0, 'C': 0, 'Custom': False}
        while rc['R'] <= 0:
            tmp = input(f"Enter {vert} {prompt} (1-{limit['R']}): ")
            if not tmp.isnumeric():
                print("Only positive integer values allowed.")
                continue
            tmp = int(float(tmp))
            if tmp > limit['R'] or tmp <= 0:
                print(f"Range is 0 to {limit['R']}")
            else:
                rc['R'] = tmp
                rc_ok = True

        while rc['C'] <= 0:
            tmp = input(f"Enter {horiz} {prompt} (1-{limit['C']}): ")
            if not tmp.isnumeric():
                print("Only positive integer values allowed.")
                continue
            tmp = int(float(tmp))
            if tmp > limit['C'] or tmp <= 0:
                print(f"Range is 0 to {limit['C']}")
            else:
                rc['C'] = tmp
    return rc


# ############################################################################
# get_ref_id() returns a one or two letter designation for a refID used in
# queries, etc.
# item is the item number (e.g., panel number)
# offset is the number of queries before this starts
# A string is returned
# ############################################################################
def get_ref_id(item: int, offset: int) -> str:
    id = f"{refIdList[int((item - 1 + offset) / 26)]}"
    id += f"{refIdList[(item + offset) - int((item - 1 + offset) / 26) * 26]}"
    return id


# ############################################################################
# initialize_array()
# 1) Clears p_array of RC values, panel numbers, and colors
# 2) Gets array dimensions & custom panel number selection
# 3) Loads p_array with RC
# ############################################################################
def initialize_array():
    for i in range(1, len(p_array)):
        p_array[i].update({'R': 0, 'C': 0, 'Panel': 0, 'Color': 0})

    while True:
        p_array[0] = get_rc("of array in panels, including gaps", "HEIGHT (R)", "WIDTH (C)", {'C':MAX_WIDTH, 'R': MAX_HEIGHT})
        show_array(p_array, False, screen_width)
        if input("Look OK? (Y/N): ").upper() == "Y":
            break

    print("\nDefault setup is to number panels consecutively, left to right, top to bottom (as above).")
    if input("Would you like to customize each panel number instead? (Y or N): ").upper() == "Y":
        p_array[0]['Custom'] = True
        print("Customizing panel numbers.\n")
    else:
        p_array[0]['Custom'] = False
        print("Using default panel numbering.\n")

    print("For each position above, enter the serial number of the inverter, or '0' if blank.")
    if p_array[0]['Custom']:
        print(
            f"After each serial number, you'll be prompted to enter the number the panel will be identified by (1-{len(p_array) - 1}).")
    panel_no = 1  # In case default panel numbering
    for r in range(1, p_array[0]['R'] + 1):
        for c in range(1, p_array[0]['C'] + 1):
            panel_no = get_panel_data({'C': c, 'R': r}, panel_no, False)
    return


# ############################################################################
# renumber_panels is used after edits to array, call if using default numbers.
# ############################################################################
def renumber_panels() -> int:
    p_no = 1
    for r in range(1, p_array[0]['R'] + 1):
        for c in range(1, p_array[0]['C'] + 1):
            for i in range(1, len(p_array)):
                if p_array[i]['R'] == r and p_array[i]['C'] == c:
                    p_array[i].update({'Panel': p_no})
                    p_no += 1
    return p_no - 1


def save_session(array, default_name: str):
    if input("Save this session for use at next run? (Y/N): ").upper() == "Y":
        while True:
            save_file = input(f"Enter filename to save to (hit ENTER for '{default_name}'): ")
            if not len(save_file):
                save_file = default_name
            if save_file.find('/') >= 0:
                print("Subdirectories not supported.")
                continue
            save_file += ".save"
            if os.path.isfile(save_file) and input(f"\t{save_file} exists.  Overwrite it? (Y or N): ").upper() != "Y":
                continue
            break
        file = open(save_file, 'w')
        json.dump(array, file)
        file.close()
        print(f"Array data saved to {save_file}.")
    return


# ############################################################################
# show_array paints the array on the screen. serials numbers shown if show_sn
# array_to_show = p_array
# ############################################################################
def show_array(array_to_show: list, show_sn: bool, screen_width: int):
    default_panel_no = 1
    box_width = min(13, int(screen_width / p_array[0]['C']))  # width of box w/o pipes
    panel_text = 'Panel'
    if box_width >= 13:
        sn_width = 12
    elif box_width < 6:
        box_width = 6
        sn_width = 4
    else:
        sn_width = box_width - 2

    if box_width < 8:
        panel_text = "Pnl"

    PadSNl = '.' * (box_width - sn_width - 1)
    PadSNr = ' ' * (box_width - sn_width - len(PadSNl))
    PadR = int((box_width - len(panel_text) - 3) / 2)
    PadL = box_width - len(panel_text) - 3 - PadR
    PadRCR = int((box_width - 6) / 2)
    PadRCL = box_width - 6 - PadRCR

    for r in range(1, p_array[0]['R'] + 1):
        line1 = '-'
        line2 = "|"
        line3 = "|"
        for c in range(1, p_array[0]['C'] + 1):
            line1 += f"{'-' * PadRCL}R{r:02d}C{c:02d}{'-' * PadRCR}-"
            if show_sn:
                found = False
                for i in range(1, len(array_to_show)):
                    if array_to_show[i]['R'] == r and array_to_show[i]['C'] == c:
                        found = True
                        line2 += f"{PadSNl}{array_to_show[i]['SN'][-sn_width:]}{PadSNr}|"
                        line3 += f"{' ' * PadL}{panel_text}{array_to_show[i]['Panel']:03d}{' ' * PadR}|"
                        break
                if not found:
                    line2 += f"{' ' * box_width}|"
                    line3 += f"{' ' * box_width}|"
            else:
                line2 += f"{' ' * PadL}{panel_text}{default_panel_no:03d}{' ' * PadR}|"
                line3 += f"{' ' * box_width}|"
                default_panel_no += 1
        print(line1)
        print(line2)
        print(line3)
    print('-' * (((box_width + 1) * p_array[0]['C']) + 1))


# ############################################################################
# signal_handler exits if SIGTERM or SIGINT are received.
# ############################################################################
def signal_handler(sig, frame):
    sys.exit("\n\nInterrupt received.")


# ############################################################################
# Main Program
# ############################################################################
if __name__ == "__main__":
    p_array = [{'R': 0, 'C': 0, 'Custom': False}]      # initialize p_array with basic array info dictionary

    if sys.version_info < MIN_PYTHON:
        sys.exit(f"Using Python {sys.version}, Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.\n")

    signal.signal(signal.SIGINT, signal_handler)  # To catch Ctrl-C
    signal.signal(signal.SIGTERM, signal_handler)  # To catch Term (e.g., Docker)

    screen_width = int(shutil.get_terminal_size()[0])

    try:
        file = open('enphase.env', 'r')
    except:
        sys.exit(
            "'enphase.env' file not found. Run 'setup-enphase.sh' & make sure this program is in the same directory.)")

    IQ_GATEWAY_IP = ''
    IQ_GATEWAY_TOKEN = ''
    tmp = file.read()
    lines = tmp.splitlines()
    for i in range(len(tmp.splitlines())):
        if lines[i].find('IQ_GATEWAY_IP=') >= 0:
            IQ_GATEWAY_IP = lines[i][14:]
        elif lines[i].find('IQ_GATEWAY_TOKEN=') >= 0:
            IQ_GATEWAY_TOKEN = lines[i][17:]
    file.close()
    if IQ_GATEWAY_IP == '' or IQ_GATEWAY_TOKEN == '':
        sys.exit('IQ_GATEWAY_IP or IQ_GATEWAY_TOKEN missing from enphase.env.  Cannot continue')

    cmd = (f"curl -f -k --silent -H'Accept: application/json' -H 'Authorization: Bearer {IQ_GATEWAY_TOKEN}' "
           f"-X GET 'https://{IQ_GATEWAY_IP}/api/v1/production/inverters'")
    r = os.popen(cmd)
    tmp = r.read()
    if r.close():
        sys.exit("Error fetching inverter serial numbers. Check login credentials.")

    sn_java = tmp.splitlines()  # curl returns lines, split into a list

    # Build panel array with all serial numbers found
    for i in range(len(tmp.splitlines())):
        if sn_java[i].find("serialNumber") > 0:
            p_array.append({'SN': sn_java[i][21:33], 'R': 0, 'C': 0, 'Panel': 0, 'Color': 0})
    if len(p_array) - 1 > MAX_INVERTERS:
        sys.exit(
            f"Sorry, up to {MAX_INVERTERS} inverters is supported, {len(p_array) - 1} were found in your network.")

    print(
        f"\n\n**************** enphase-canvas.py Build {BUILD} ****************\n"
        f"This program will create a Grafana Dashboard with Canvas Panels that will display the output of your\n"
        f"Enphase inverters graphically to resemble your installation. "
        f"{len(p_array) - 1} inverters were found on your network.\n"
        f"First, indicate the width and height of your array in panels.  If you want gaps to appear in the graphic\n"
        f"count them as panels.  Example, if your array has 5 across, then a gap of one, then 3 more, the width is 9.")

    # Are there saved arrays?
    saved_arrays = []
    default_array_name = ""
    for file in os.listdir('.'):
        if file.endswith(".save"):
            saved_arrays.append(os.path.basename(file))
    if len(saved_arrays):
        print("\nThe following saved arrays are available:")
        for i in range(len(saved_arrays)):
            print(f"{i+1}. {saved_arrays[i]}")
        while True:
            i = input(f"Enter array number to load (1 to {len(saved_arrays) - 1}), or ENTER to start a new one: ")
            if i == "":
                print("Starting a new array.")
                default_array_name = "enphase"
                initialize_array()
                break
            if not str.isnumeric(i) or int(i) <= 0 or int(i) > len(saved_arrays):
                continue
            default_array_name = os.path.splitext(saved_arrays[int(i)-1])[0]
            print(f"Loading array '{default_array_name}.save'")
            file = open(default_array_name + '.save', 'r')
            p_array_temp = json.load(file)
            file.close()
            p_array[0] = p_array_temp[0]                 # Load basic info
            # Now each panel, checking that it's serial number exits in current configuration
            for i in range(1, len(p_array_temp)):
                err_msg =\
                    f"SN {p_array_temp[i]['SN']} in saved data is not in current array.  Cannot use saved data."
                for j in range(1, len(p_array)):
                    if p_array_temp[i]['SN'] == p_array[j]['SN']:
                        p_array[j] = p_array_temp[i]
                        err_msg = ""
                        break
                if err_msg != "":
                    sys.exit(err_msg)
            print("Loaded saved data.")
            break
    else:
        print("No saved arrays found")
        initialize_array()

    response = ''
    while response != 'A':
        first = 0
        second = 0
        show_array(p_array, True, screen_width)
        response = input(
            "'A' to approve, 'E' to edit a panel, 'S' to swap panels, 'C' to clear & restart, 'Q' to quit: ").upper()
        if response == 'E':
            edit_panel1_loc = get_rc("of panel to edit", "Row (R)", "Column (C)", p_array[0])
            panel_no = get_panel_data(edit_panel1_loc, 1, True)
        elif response == 'S':
            edit_panel1_loc = get_rc("of 1st panel to swap", "Row (R)", "Column (C)", p_array[0])
            edit_panel2_loc = get_rc("of 2nd panel to swap", "Row (R)", "Column (C)", p_array[0])
            for i in range(1, len(p_array)):
                if p_array[i]['R'] == edit_panel1_loc['R'] and p_array[i]['C'] == edit_panel1_loc['C']:
                    first = i
                elif p_array[i]['R'] == edit_panel2_loc['R'] and p_array[i]['C'] == edit_panel2_loc['C']:
                    second = i
            p_array[first]['R'], p_array[second]['R'] = p_array[second]['R'], p_array[first]['R']
            p_array[first]['C'], p_array[second]['C'] = p_array[second]['C'], p_array[first]['C']
            if not p_array[0]['Custom']:
                renumber_panels()
        elif response == 'C':
            initialize_array()
        elif response == 'Q':
            save_session(p_array, default_array_name)
            sys.exit(0)
        elif response == 'A':
            # Check for unused serial number, warn if any found
            missing = ""
            for i in range(1, len(p_array)):
                if p_array[i]['R'] == 0 and p_array[i]['C'] == 0:
                    missing += p_array[i]['SN'] + ','
            if len(missing):
                print(f"The following inverter serial numbers have not been used: {missing[:-1]}.")
                if input("Do you want to continue anyway? (y/N)").upper() != "Y":
                    response = ''
        else:
            print("Invalid option.")
            response = ''

    # Fill in color numbers in panel-naming order
    color_index = 0
    for i in range(1, len(p_array)):
        for c in range(1, len(p_array)):
            if p_array[c]['Panel'] == i:
                p_array[c]['Color'] = BORDER_COLORS[color_index]
                color_index += 1
                if color_index >= len(BORDER_COLORS):
                    color_index = 0  # Start reusing border colors

    # JSON creation
    while True:
        if DEBUG:
            out_file_name = 'debug.json'
            break
        out_file_name = input(f"Enter name for dashboard json file (hit ENTER for '{default_array_name}'): ")
        if out_file_name == '':
            out_file_name = default_array_name + '.json'
        else:
            default_array_name = out_file_name
            out_file_name = out_file_name + '.json'
        try:
            FinalFile = open(out_file_name, 'r')
            if input(f"\t{out_file_name} exists.  Overwrite it? (Y or N): ").upper() == "Y":
                break                   # will be deleted when opened for write
        except:              # no file - we're good
            break
        continue
    FinalFile = open(out_file_name, 'w')

    if input("Save dashboard panels to Grafana's library for use in other dashboards (Y or N): ").upper() == "Y":
        library = True
        print("    Panels will be added to Grafana Library when you import dashboard.")
        Influx = "DS_INFLUXDB-FOR-LIBRARY-PANEL"
        SunAndMoon = "DS_SUN_AND_MOON-FOR-LIBRARY-PANEL"
    else:
        library = False
        print("    Panels will NOT be added to Grafana Library when you import dashboard.")
        Influx = "DS_INFLUXDB"
        SunAndMoon = "DS_SUN_AND_MOON"

    UID_Influx = '${' + Influx + '}'
    UID_SunAndMoon = '${' + SunAndMoon + '}'

    # Build jsons
    # Building Block JSONS:
    elements_common = []        # Common part of canvas options section List - header & element definitions
    cur_query = []              # Queries for Current Output panel List
    prod_query = []             # Queries for Production panel List
    transforms = []             # Transformations List (same for both Canvas panels)
    time_series_overrides = []  # Overrides List, including custom colors, for Time Series Panel
    time_series_targets = []    # Includes shortened names for Time Series Legend
    CurOut_gridPos = {}         # Current Output Panel Position, etc. Dictionary
    TtlProd_gridPos = {}        # Total Production Panel Position, etc. Dictionary
    TimeSeries_gridPos = {}     # Time Series Panel Position, etc. Dictionary
    Input_influx = {}
    Input_SunAndMoon = {}

    # Panel definition dictionaries
    CurOut_panel = {}
    TtlProd_panel = {}
    TimeSeries_panel = {}

    final_json = {}         # Final JSON file dictionary

    # Make common part for canvas element's definitions, both panels' queries and transformations JSONs,
    # as well as base for time series panel

    # First, pre-pend time-series overides with fixed stuff
    time_series_overrides.append({"matcher": {"id": "byName", "options": "Clouds"},
                                  "properties": [{"id": "color", "value": {"fixedColor": "#ffffff", "mode": "fixed"}},
                                                 {"id": "custom.fillOpacity", "value": 0},
                                                 {"id": "unit", "value": "percent"},
                                                 {"id": "custom.lineStyle", "value": {"dash": [5, 6], "fill": "dash"}},
                                                 {"id": "custom.pointSize", "value": 1},
                                                 {"id": "custom.lineWidth", "value": 1},
                                                 {"id": "custom.spanNulls", "value": True},
                                                 {"id": "custom.axisPlacement", "value": "left"},
                                                 {"id": "custom.axisLabel", "value": ""},
                                                 {"id": "custom.hideFrom",
                                                  "value": {"legend": False, "tooltip": False, "viz": False}}]})

    time_series_overrides.append({"matcher": {"id": "byName", "options": "Sun altitude"},
                                  "properties": [{"id": "custom.fillOpacity", "value": 10},
                                                 {"id": "custom.axisPlacement", "value": "hidden"},
                                                 {"id": "unit", "value": "percent"},
                                                 {"id": "decimals", "value": 0},
                                                 {"id": "color", "value": {"fixedColor": "#c0c0c0", "mode": "fixed"}},
                                                 {"id": "custom.lineStyle", "value": {"dash": [1, 5], "fill": "dash"}},
                                                 {"id": "min", "value": -101},
                                                 {"id": "max", "value": 101},
                                                 {"id": "unit", "value": "degree"},
                                                 {"id": "displayName", "value": "Sun Altitude"},
                                                 {"id": "custom.hideFrom", "value":
                                                     {"legend": True, "tooltip": False, "viz": False}}]})

    # Prepend time series targets with fixed stuff
    time_series_targets.append({"datasource": {"type": "fetzerch-sunandmoon-datasource", "uid": UID_SunAndMoon},
                                "hide": False, "refId": "A",
                                "target": ["sun_altitude"]})
    time_series_targets.append({"alias": "Clouds",
                                "datasource": {"type": "influxdb", "uid": UID_Influx},
                                "groupBy": [{"params": ["$__interval"], "type": "time"},
                                            {"params": ["null"], "type": "fill"}],
                                "hide": False,
                                "measurement": "weather", "orderByTime": "ASC", "policy": "autogen", "refId": "B",
                                "resultFormat": "time_series",
                                "select": [[{"params": ["clouds"], "type": "field"},
                                            {"params": [], "type": "mean"}]],
                                "tags": []})

    # Now loop through all panels and add appropriate data to JSONs
    for i in range(1, len(p_array) + 1):
        found = False
        for j in range(1, len(p_array)):
            if p_array[j]['Panel'] == i:
                r = p_array[j]['R']
                c = p_array[j]['C']
                found = True
                break
        if not found:  # Non-existent panel
            continue
        else:  # Do all json here
            panel_text = f"{p_array[j]['Panel']:02d}"
            elements_common.append({"background": {
                                        "color": {"field": panel_text, "fixed": "#D9D9D9"}, "image": {"fixed": ""}},
                                    "border": {"color": {"fixed": f"{p_array[j]['Color']}"}, "width": 5},
                                    "config": {"align": "right",
                                               "color": {"field": f"{panel_text}Color", "fixed": "#000000"},
                                               "text": {"fixed": panel_text},
                                               "valign": "bottom"},
                                    "constraint": {"horizontal": "left", "vertical": "top"},
                                    "name": f"Panel{panel_text}",
                                    "placement":
                                        {"height": 45, "left": 5 + (79 * (c - 1)),
                                         "top": 32 + (48 * (r - 1)), "width": 76},
                                    "type": "rectangle"})
            elements_common.append({"background": {"color": {"fixed": "transparent"}},
                                    "border": {"color": {"fixed": "dark-green"}},
                                    "config": {
                                        "align": "left", "color": {"field": f"{panel_text}Color", "fixed": "#000000"},
                                        "text": {"field": panel_text, "mode": "field"},
                                        "valign": "middle"},
                                    "constraint": {"horizontal": "left", "vertical": "top"},
                                    "name": f"Panel{panel_text}Watts",
                                    "placement":
                                        {"height": 20, "left": 11 + (79 * (c - 1)),
                                         "top": 34 + (48 * (r - 1)), "width": 68},
                                    "type": "rectangle"})
            cur_query.append({"alias": panel_text,
                              "datasource": {"type": "influxdb", "uid": UID_Influx},
                              "hide": False,
                              "query":
                                  f"SELECT last(\"lastReportWatts\") FROM \"local\".\"LocalData_Enphase\" WHERE (\"serialNumber\" = '{p_array[j]['SN']}')",
                              "rawQuery": True,
                              "refId": f"{get_ref_id(p_array[j]['Panel'], 0)}",
                              "resultFormat": "time_series"})
            transforms.append({"id": "calculateField",
                               "options": {"alias": f"{panel_text}Color", "mode": "reduceRow",
                                           "reduce": {"include": [panel_text], "reducer": "lastNotNull"}}})

            prod_query.append({"alias": panel_text, "datasource": {
                "type": "influxdb", "uid": UID_Influx}, "hide": False,
                               "query": f"SELECT integral(\"lastReportWatts\")  / 3600 FROM \"local\".\"LocalData_Enphase\" WHERE (\"serialNumber\" = '{p_array[j]['SN']}') AND $timeFilter",
                               "rawQuery": True,
                               "refId": f"{get_ref_id(p_array[j]['Panel'], 0)}",
                               "resultFormat": "time_series"})
            time_series_overrides.append({"matcher": {"id": "byName", "options": panel_text},
                                          "properties": [{"id": "color",
                                                          "value":
                                                              {"fixedColor": f"{p_array[j]['Color']}",
                                                               "mode": "fixed"}}]})
            time_series_targets.append({"alias": panel_text,
                                        "datasource": {"type": "influxdb", "uid": UID_Influx},
                                        "groupBy": [{"params": ["$__interval"], "type": "time"},
                                                    {"params": ["serialNumber"], "type": "tag"}],
                                        "hide": False,
                                        "measurement": "LocalData_Enphase",
                                        "orderByTime": "ASC",
                                        "policy": "local",
                                        "refId": f"{get_ref_id(p_array[j]['Panel'], 2)}",
                                        "resultFormat": "time_series",
                                        "select": [[{"params": ["lastReportWatts"], "type": "field"},
                                                    {"params": [], "type": "distinct"}]],
                                        "tags": [{"key": "serialNumber", "operator": "=", "value": p_array[j]['SN']}]})

    # Final 1-time items
    cur_query.append({"alias": "Total",
                      "datasource": {"type": "influxdb", "uid": UID_Influx},
                      "hide": False,
                      "query":
                          "SELECT sum(last) from (SELECT last(\"lastReportWatts\") FROM \"local\".\"LocalData_Enphase\" GROUP BY \"serialNumber\")",
                      "rawQuery": True,
                      "refId": f"{get_ref_id(len(p_array), 0)}",
                      "resultFormat": "time_series"})
    prod_query.append({"alias": "Total",
                       "datasource": {"type": "influxdb", "uid": UID_Influx},
                       "hide": False,
                       "query":
                           "SELECT sum(integral) from (SELECT integral(\"lastReportWatts\")  / 3600 FROM \"local\".\"LocalData_Enphase\" WHERE $timeFilter GROUP BY \"serialNumber\")",
                       "rawQuery": True,
                       "refId": f"{get_ref_id(len(p_array), 0)}",
                       "resultFormat": "time_series"})

    # Build dictionary with Panel Options common to both canvas panels
    panel_options_common = {}
    panel_options_common.update({"inlineEditing": False, "panZoom": True, "infinitePan": True,
                                 "root": {"background": {"color": {"fixed": "transparent"},
                                                         "image": {"field": "", "fixed": "", "mode": "fixed"}},
                                          "border": {"color": {"fixed": "dark-green"}},
                                          "constraint": {"horizontal": "left", "vertical": "top"}}})

    # Build Current Output Panel
    CurOut_gridPos.update({"gridPos": {"h": int(round(2.7 + p_array[0]['R']*1.32, 0)), "w": 24, "x": 0, "y": 1}})
    cur_elements = copy.deepcopy(elements_common)  # Clone elements to suffix Current Output Panel specific stuff
    cur_elements.append({"background": {"color": {"fixed": "transparent"}},
                         "border": {"color": {"fixed": "dark-green"}},
                         "config": {"align": "center", "color": {"fixed": "text"}, "size": 22,
                                    "text": {"fixed": "Total Current Output:"}, "valign": "middle"},
                         "constraint": {"horizontal": "left", "vertical": "top"},
                         "name": "TotalOutputTitle",
                         "placement": {"height": 30, "left": 5 + int(max(0, p_array[0]['C']-4)*39.5),
                                       "top": 32+p_array[0]['R']*48, "width": 230},
                         "type": "text"},)

    cur_elements.append({"background": {"color": {"fixed": "transparent"}},
                         "border": {"color": {"fixed": "dark-green"}},
                         "config": {"align": "left", "color": {"fixed": "text"}, "size": 22,
                                    "text": {"field": "Total", "fixed": "XXX", "mode": "field"},
                                    "valign": "middle"},
                         "constraint": {"horizontal": "left", "vertical": "top"},
                         "name": "TotalOutput",
                         "placement": {"height": 30, "left": 235 + int(max(0, p_array[0]['C']-4)*39.5),
                                       "top": 32+p_array[0]['R']*48, "width": 100},
                         "type": "rectangle"})

    # Build Threshold colors for CurOut_panel
    Threshold_steps = [{"color": "transparent", "value": None}]
    i = 0
    for step in [0, 2, 5, 7, 9, 10, 15, 20, 25, 30, 35]:
        Threshold_steps.append({"color": TEMPERATURE_COLORS[i], "value": step})
        i += 1
    for step in range(40, 401, 10):
        Threshold_steps.append({"color": TEMPERATURE_COLORS[i], "value": step})
        i += 1

    CurOut_panel.update({"datasource": {"type": "datasource", "uid": "-- Mixed --"},
                         "description": "", "fieldConfig": {
                            "defaults": {"color": {"mode": "thresholds"}, "fieldMinMax": True, "mappings": [],
                                         "noValue": "0", "thresholds": {"mode": "absolute", "steps": Threshold_steps},
                                         "unit": "watt"},
                         "overrides": [{"matcher": {"id": "byRegexp", "options": "/[0-9][0-9]Color/"},
                                        "properties": [{"id": "thresholds",
                                                        "value": {"mode": "absolute", "steps": [
                                                            {"color": "#ffffff", "value": None},
                                                            {"color": "#000000", "value": 30}]}}]}]}})
    if library:
        CurOut_panel.update({"libraryPanel": {"uid": UID_CurOut}})
    else:                       # If not saving panel to library, gridPos & ID go here
        CurOut_panel.update(CurOut_gridPos)
        CurOut_panel.update({"id": 150})

    CurOut_panel["options"] = copy.deepcopy(panel_options_common)
    CurOut_panel["options"]["root"]["elements"] = copy.deepcopy(cur_elements)
    CurOut_panel["options"]["root"]["name"] = "Element 1703022472170"
    CurOut_panel["options"]["root"]["placement"] = {"height": 100, "left": 0, "top": 0, "width": 100}
    CurOut_panel["options"]["root"]["type"] = "frame"
    CurOut_panel["options"]["showAdvancedTypes"] = True
    CurOut_panel.update({"pluginVersion": MIN_GRAFANA})
    CurOut_panel["targets"] = copy.deepcopy(cur_query)
    CurOut_panel.update({"title": "Solar Panels - Current Output Template"})
    CurOut_panel["transformations"] = transforms
    CurOut_panel["type"] = "canvas"

    # Build Total Production Panel
    TtlProd_gridPos.update({"gridPos": {"h": int(round(2.7 + p_array[0]['R']*1.32, 0)), "w": 24, "x": 0,
                                        "y": 1+int(round(2.7 + p_array[0]['R']*1.32, 0))}})
    tp_elements = copy.deepcopy(elements_common)  # Clone elements to suffix Total Production Panel specific stuff
    tp_elements.append({"background": {"color": {"fixed": "transparent"}},
                        "border": {"color": {"fixed": "dark-green"}},
                        "config": {"align": "right", "color": {"fixed": "text"}, "size": 22,
                                   "text": {"fixed": "Total Production:"}, "valign": "middle"},
                        "constraint": {"horizontal": "left", "vertical": "top"},
                        "name": "TotalProdTitle",
                        "placement": {"height": 30, "left": 5 + int(max(0, p_array[0]['C']-4)*39.5),
                                      "top": 32+p_array[0]['R']*48, "width": 180},
                        "type": "text"}, )

    tp_elements.append({"background": {"color": {"fixed": "transparent"}},
                        "border": {"color": {"fixed": "dark-green"}},
                        "config": {"align": "left", "color": {"fixed": "text"}, "size": 22,
                                   "text": {"field": "Total", "fixed": "XXX", "mode": "field"},
                                   "valign": "middle"},
                        "constraint": {"horizontal": "left", "vertical": "top"},
                        "name": "TotalProd",
                        "placement": {"height": 30, "left": 190 + int(max(0, p_array[0]['C']-4)*39.5),
                                      "top": 32+p_array[0]['R']*48, "width": 140},
                        "type": "rectangle"})

    # Build Threshold colors for TtlProd_Panel
    Threshold_steps = []
    Threshold_steps.clear()
    Threshold_steps.append({"color": "transparent", "value": None},)
    i = 0
    for step in range(0, 1975, 42):
        Threshold_steps.append({"color": TEMPERATURE_COLORS[i], "value": step})
        i += 1

    TtlProd_panel.update({"datasource": {
            "type": "datasource", "uid": "-- Mixed --"}, "description": "", "fieldConfig": {
                "defaults": {"color": {"mode": "thresholds"}, "fieldMinMax": True, "mappings": [],
                             "noValue": "0", "thresholds": {"mode": "absolute", "steps": Threshold_steps},
                             "unit": "watth"},
                "overrides": [{"matcher": {"id": "byRegexp", "options": "/[0-9][0-9]Color/"},
                               "properties": [{"id": "thresholds",
                                               "value": {"mode": "absolute", "steps": [
                                                   {"color": "#ffffff", "value": None},
                                                   {"color": "#000000", "value": 400}]}}]}]}})
    if library:
        TtlProd_panel.update({"libraryPanel": {"uid": UID_TtlProd}})
    else:                           # If not saving panel to library, gridPos & ID go here
        TtlProd_panel.update(TtlProd_gridPos)
        TtlProd_panel.update({"id": 152})

    TtlProd_panel["options"] = copy.deepcopy(panel_options_common)
    TtlProd_panel["options"]["root"]["elements"] = {}
    TtlProd_panel["options"]["root"]["elements"] = copy.deepcopy(tp_elements)
    TtlProd_panel["options"]["root"]["name"] = "Element 1703022472170"
    TtlProd_panel["options"]["root"]["placement"] = {"height": 100, "left": 0, "top": 0, "width": 100}
    TtlProd_panel["options"]["root"]["type"] = "frame"
    TtlProd_panel["options"]["showAdvancedTypes"] = True
    TtlProd_panel.update({"pluginVersion": MIN_GRAFANA})
    TtlProd_panel["targets"] = copy.deepcopy(prod_query)
    TtlProd_panel.update({
        "title": "Solar Panel Production Template Between ${__from:date:YYYY-MMM-DD HH:mm} and ${__to:date:YYYY-MMM-DD HH:mm}"})
    TtlProd_panel["transformations"] = transforms
    TtlProd_panel["type"] = "canvas"

    # Build Inverter Output Time Series Panel
    TimeSeries_gridPos.update(
        {"gridPos": {"h": 9, "w": 24, "x": 0, "y": 1+int(round(2.7 + p_array[0]['R']*1.32, 0))*2}})
    TimeSeries_panel.update({"datasource": {"type": "datasource", "uid": "-- Mixed --"},
                             "description": "",
                             "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"},
                                                          "custom": {
                                                              "axisBorderShow": False,
                                                              "axisCenteredZero": False, "axisColorMode": "text",
                                                              "axisLabel": "Watts", "axisPlacement": "right",
                                                              "barAlignment": 0, "drawStyle": "line",
                                                              "fillOpacity": 0, "gradientMode": "none",
                                                              "hideFrom":
                                                                  {"legend": False, "tooltip": False, "viz": False},
                                                              "insertNulls": False,
                                                              "lineInterpolation": "linear", "lineWidth": 1,
                                                              "pointSize": 5,
                                                              "scaleDistribution": {"type": "linear"},
                                                              "showPoints": "auto", "spanNulls": False,
                                                              "stacking": {"group": "A", "mode": "none"},
                                                              "thresholdsStyle": {"mode": "off"}},
                                                          "mappings": [],
                                                          "thresholds": {"mode": "absolute",
                                                                         "steps": [{"color": "green", "value": None},
                                                                                   {"color": "red", "value": 80}]}}}})
    TimeSeries_panel["fieldConfig"]["overrides"] = time_series_overrides
    if library:
        TimeSeries_panel.update({"libraryPanel": {"uid": UID_Time_Series}})
    else:                                   # If not saving panel to library, gridPos & ID go here
        TimeSeries_panel.update(TimeSeries_gridPos)
        TimeSeries_panel.update({"id": 146})

    TimeSeries_panel.update({"options": {
        "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
        "tooltip": {"maxHeight": 600, "mode": "single", "sort": "none"}}})
    TimeSeries_panel["targets"] = time_series_targets
    TimeSeries_panel["title"] = "Enphase Inverter Output Template"
    TimeSeries_panel["type"] = "timeseries"

    # Build Final JSON Sections
    __inputs = []
    Input_influx.update({"name": Influx, "label": "influxDB", "description": "",
                         "type": "datasource", "pluginId": "influxdb", "pluginName": "InfluxDB"})
    Input_SunAndMoon.update({"name": SunAndMoon, "label": "Sun and Moon", "description": "",
                             "type": "datasource",
                             "pluginId": "fetzerch-sunandmoon-datasource", "pluginName": "Sun and Moon"})
    if library:             # Add in library panel usage
        Input_influx.update({"usage": {"libraryPanels": [
                             {"name": "Solar Panels - Current Output Template", "uid": UID_CurOut},
                             {"name": "Solar Panels - Production Over Period Template", "uid": UID_TtlProd},
                             {"name": "Enphase Inverter Output Template", "uid": UID_Time_Series}]}})
        Input_SunAndMoon.update({"usage": {"libraryPanels": [
                             {"name": "Enphase Inverter Output Template", "uid": UID_Time_Series}]}})
    __inputs.append(Input_influx)
    __inputs.append(Input_SunAndMoon)
    __inputs.append({"name": "VAR_TZ", "type": "constant", "label": "Timezone",
                     "value": "America/Chicago", "description": ""})

    __elements = {}
    if library:
        __elements.update(
            {UID_CurOut: {
                "name": "Solar Panels - Current Output Template",
                "uid": UID_CurOut, "kind": 1, "model": CurOut_panel},
             UID_TtlProd: {
                 "name": "Solar Panels - Production Over Period Template",
                 "uid": UID_TtlProd, "kind": 1, "model": TtlProd_panel},
             UID_Time_Series: {"name": "Enphase Inverter Output Template",
                               "uid": UID_Time_Series, "kind": 1, "model": TimeSeries_panel}})

    __requires = [{"type": "grafana", "id": "grafana", "name": "Grafana", "version": MIN_GRAFANA}]
    if not library:
        __requires.append({"type": "panel", "id": "canvas", "name": "Canvas", "version": ""})
        __requires.append({"type": "datasource", "id": "fetzerch-sunandmoon-datasource",
                           "name": "Sun and Moon", "version": "0.3.2"})
        __requires.append({"type": "datasource", "id": "influxdb", "name": "InfluxDB", "version": "1.0.0"})
        __requires.append({"type": "panel", "id": "timeseries", "name": "Time series", "version": ""})

    panels = [{"collapsed": False, "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
               "id": 98, "panels": [], "title": "Enphase", "type": "row"}]
    if library:             # Add in library definitions to gridPos, add to panels
        CurOut_gridPos.update({"id": 150})
        CurOut_gridPos.update({"libraryPanel": {"uid": UID_CurOut,
                                                "name": "Solar Panels - Current Output Template"}})
        panels.append(CurOut_gridPos)

        TtlProd_gridPos.update({"id": 152})
        TtlProd_gridPos.update({"libraryPanel": {"uid": UID_TtlProd,
                                                 "name": "Solar Panels - Production Over Period Template"}})
        panels.append(TtlProd_gridPos)

        TimeSeries_gridPos.update({"id": 146})
        TimeSeries_gridPos.update({"libraryPanel": {"uid": UID_Time_Series,
                                                    "name": "Enphase Inverter Output Template"}})
        panels.append(TimeSeries_gridPos)
    else:
        panels.append(CurOut_panel)
        panels.append(TtlProd_panel)
        panels.append(TimeSeries_panel)

    # Build full json
    final_json["__inputs"] = __inputs
    final_json["__elements"] = __elements
    final_json["__requires"] = __requires
    final_json.update({"annotations": {"list": [
                        {"builtIn": 1, "datasource": {"type": "datasource", "uid": "grafana"},
                         "enable": True, "hide": True, "iconColor": "rgba(0, 211, 255, 1)",
                         "name": "Annotations & Alerts",
                         "target": {"limit": 100, "matchAny": False, "tags": [], "type": "dashboard"},
                         "type": "dashboard"}]}})
    final_json.update({"description": ""})
    final_json.update({"editable": False})
    final_json.update({"fiscalYearStartMonth": 0})
    final_json.update({"graphTooltip": 0})
    final_json.update({"id": None})
    final_json.update({"links": []})
    final_json.update({"liveNow": False})
    final_json["panels"] = panels
    final_json.update({"refresh": "5s"})
    final_json.update({"schemaVersion": 39})
    final_json.update({"tags": []})
    final_json.update({"templating": {"list": [
        {"description": "Timezone", "hide": 2, "label": "Timezone", "name": "tz",
         "query": "${VAR_TZ}", "skipUrlSync": False, "type": "constant",
         "current": {"value": "${VAR_TZ}", "text": "${VAR_TZ}", "selected": False},
         "options": [{"value": "${VAR_TZ}", "text": "${VAR_TZ}", "selected": False}]}]}})
    final_json.update({"time": {"from": "now-24h", "to": "now"}})
    final_json.update({"timeRangeUpdatedDuringEditOrView": False, "timepicker": {
        "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]}})
    final_json.update({"timezone": "America/Chicago"})
    final_json.update({"title": "Enphase Panels Template"})
    final_json.update({"uid": "bdquc1pkin2tcb"})
    final_json.update({"version": 1})
    final_json.update({"weekStart": ""})
    json.dump(final_json, FinalFile, indent=2)
    FinalFile.close()

    print(f"\nDashboard JSON file '{out_file_name}' created. Go to Grafana, Dashboards, New, Import & open this file.\n"
          f"If you have not run Powerwall-Dashboard's ./setup.sh since running setup-enphase.sh, be sure to, followed by reboot!\n")
    if not DEBUG:
        save_session(p_array, default_array_name)
sys.exit(0)
