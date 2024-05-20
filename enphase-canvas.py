#!/usr/bin/env python
# enphase-canvas.py - Tesla Fleet API access
# -*- coding: utf-8 -*-

"""
Python scrypt to interactively create a Grafana dashboard with canvas panels
graphically depicting a Solar array with Enphase micro-inverters.

Rev History:
0.1.0: Initial

Needed to run:  no additional python packages should be required beyond the standard package.
"""

import json
import os
import signal
import sys
import shutil  # for screen resolution command invocation

# Constants
BUILD = "0.1.0"
MAX_WIDTH = 15
MAX_HEIGHT = 15
MIN_PYTHON = (3, 5)
BORDER_COLORS = ["#8ab8ff", "#ff780a", "#f2495c", "#5794f2", "#b877d9", "#705da0", "#37872d", "#fade2a",
                 "#447ebc", "#c15c17", "#890f02", "#0a437c", "#6d1f62", "#584477", "#b7dbab", "#f4d598",
                 "#70dbed", "#f9ba8f", "#f29191", "#82b5d8", "#e5a8e2", "#aea2e0", "#629e51", "#e5ac0e",
                 "#64b0c8", "#e0752d", "#bf1b00"]
refIdList = ['', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
             'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

# Global variables
p_array = []        # main deta for array creation
                    # element [0]] = basics (array dims, custom panel # choice):
                        # {'R': x, 'C': y, 'Custom': <True/False>}
                    # elements [1] - [x] are each serial number, with array coordinates:
                        # {"SN": "<serial#>)", "R": x, "C": y, "Panel": <panel#>, "Color": "<color code>>"}

# ############################################################################
# add_json() appends 'element' to file 'file_handle' in json format. 'offset'
# is # of spaces to prepend lines with.  'add_comma' will suffix a comma.
# ############################################################################
def add_json(file_handle, element: dict, offset: int, add_comma: bool):
    output = json.dumps(element, indent=2)
    output = output[output.find('\n'):output.rfind('\n')]   # Lob off opening/closing brackets
    output = output[1:]                                     # Lob off next blank line & leading spaces
    output = ' ' * (offset+2) + (' ' * offset).join((output.lstrip()).splitlines(True))
    if add_comma:
        output += ','
    file_handle.write(output)

def add_template(template_name: str, FinalFileHandle):
    try:
        TemplateFile = open('./templates/' + template_name, 'r')
    except:
        sys.exit(f"Fatal error: template '{template_name}' not found under {os.getcwd()}.")
    FinalFileHandle.write(TemplateFile.read())
    TemplateFile.close()
    return


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
    print('')
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
        p_array[0] = get_rc("of array in panels, including gaps", "HEIGHT (R)", "WIDTH (C)", {'C': 15, 'R': 15})
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


def save_session(array):
    if input("Save this session for use at next run? (Y/N): ").upper() == "Y":
        try:
            file = open('array.save', 'r')
            file.close()
            if input(f"\tSaved array data exists.  Overwrite it? (Y or N): ").upper() != "Y":
                sys.exit(0)
        except:              # no file - we're good
            pass

        file = open('array.save', 'w')
        json.dump(array, file)
        file.close()
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
            line1 += f"{'-' * PadRCL}R{r:02d}C{c:02d}{'-' * (PadRCR)}-"
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
                line3 += f"{' ' * (box_width)}|"
                default_panel_no += 1
        print(line1)
        print(line2)
        print(line3)
    print('-' * (((box_width + 1) * p_array[0]['C']) + 1))


# ############################################################################
# Signal_Handler exits if SIGTERM or SIGINT are received.
# ############################################################################
def Signal_Handler(sig, frame):
    global StopNow
    sys.exit("\n\nInterrupt received.")


# ############################################################################
# Main Program
# ############################################################################
if __name__ == "__main__":
    p_array = [{'R':0, 'C':0, 'Custom':False}]      # initialize p_array with basic array info dictionary

    if sys.version_info < MIN_PYTHON:
        sys.exit(f"Using Python {sys.version}, Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.\n")

    signal.signal(signal.SIGINT, Signal_Handler)  # To catch Ctrl-C
    signal.signal(signal.SIGTERM, Signal_Handler)  # To catch Term (e.g., Docker)

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

    print(
        f"\n\n**************** enphase-canvas.py Build {BUILD} ****************\n"
        f"This program will create a Grafana Dashboard with Canvas Panels that will display the output of your\n"
        f"Enphase inverters graphically to resemble your installation. "
        f"{len(p_array) - 1} inverters were found on your network.\n"
        f"First, indicate the width and height of your array in panels.  If you want gaps to appear in the grafic\n"
        f"count them as panels.  Example, if your array has 5 across, then a gap of one, then 3 more, the width is 9.")

    # is there a saved array from an earlier run?
    try:
        file = open('array.save', 'r')
        saved_session = True
    except:
        saved_session = False
    if saved_session:
        if input("\nSaved session found, restore? (y/N) ").upper() != 'Y':
            saved_session = False
        else:
            p_array_temp = json.load(file)
            file.close()
            p_array[0] = p_array_temp[0]                 # Load basic info
            # Now each panel, checking that it's serisl number exits in current configuration
            for i in range(1, len(p_array_temp)):
                err_msg =\
                    f"SN {p_array_temp[i]['SN']} in saved data is not in current array.  Cannot use saved data."
                for j in range(1, len(p_array)):
                    if p_array_temp[i]['SN'] == p_array[j]['SN']:
                        p_array[j] = p_array_temp[i]
                        err_msg = ""
                        break
                if(err_msg != ""):
                    sys.exit(err_msg)
            print("Loaded saved data.")
            saved_session = True
    if not saved_session:
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
            save_session(p_array)
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
        out_file_name = input("Enter name for dashboard json file (hit ENTER for 'enphase'): ")
        if out_file_name == '':
            out_file_name = 'enphase.json'
        else:
            out_file_name = out_file_name + '.json'
        try:
            FinalFile = open(out_file_name, 'r')
            if input(f"\t{out_file_name} exists.  Overwrite it? (Y or N): ").upper() == "Y":
                break                   # will be deleted when opened for write
        except:              # no file - we're good
            break
        continue
    FinalFile = open(out_file_name, 'w')

    # Build jsons
    element_json = []  # All Canvas element definitions - both Canvas Panels (Identical)
    current_query_json = []  # Current Output queries
    production_query_json = []  # Production queries
    xf_json = []  # Transformations (same for both Canvas panels)
    time_series_json = []  # Custom color overrides for time series panel
    time_series_aliases_json = []  # Shortened names for Time Series Legend

    # Since overrides for time series are one list, add in top part now, append others in loop
    time_series_json.append(
        {
            "matcher": {
                "id": "byName",
                "options": "Clouds"
            },
            "properties": [
                {
                    "id": "color",
                    "value": {
                        "fixedColor": "#ffffff",
                        "mode": "fixed"
                    }
                },
                {
                    "id": "custom.fillOpacity",
                    "value": 0
                },
                {
                    "id": "unit",
                    "value": "percent"
                },
                {
                    "id": "custom.lineStyle",
                    "value": {
                        "dash": [
                            5,
                            6
                        ],
                        "fill": "dash"
                    }
                },
                {
                    "id": "custom.pointSize",
                    "value": 1
                },
                {
                    "id": "custom.lineWidth",
                    "value": 1
                },
                {
                    "id": "custom.spanNulls",
                    "value": True
                },
                {
                    "id": "custom.axisPlacement",
                    "value": "left"
                },
                {
                    "id": "custom.axisLabel",
                    "value": ""
                },
                {
                    "id": "custom.hideFrom",
                    "value": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False
                    }
                }
            ]
        })
    time_series_json.append(
        {
            "matcher": {
                "id": "byName",
                "options": "Sun altitude"
            },
            "properties": [
                {
                    "id": "custom.fillOpacity",
                    "value": 10
                },
                {
                    "id": "custom.axisPlacement",
                    "value": "hidden"
                },
                {
                    "id": "unit",
                    "value": "percent"
                },
                {
                    "id": "decimals",
                    "value": 0
                },
                {
                    "id": "color",
                    "value": {
                        "fixedColor": "#c0c0c0",
                        "mode": "fixed"
                    }
                },
                {
                    "id": "custom.lineStyle",
                    "value": {
                        "dash": [
                            1,
                            5
                        ],
                        "fill": "dash"
                    }
                },
                {
                    "id": "min",
                    "value": -101
                },
                {
                    "id": "max",
                    "value": 101
                },
                {
                    "id": "unit",
                    "value": "degree"
                },
                {
                    "id": "displayName",
                    "value": "Sun Altitude"
                },
                {
                    "id": "custom.hideFrom",
                    "value": {
                        "legend": True,
                        "tooltip": False,
                        "viz": False
                    }
                }
            ]
        })

    for i in range(1, len(p_array) + 1):
        found = False
        for j in range(1, len(p_array)):
            if p_array[j]['Panel'] == i:
                r = p_array[j]['R']
                c = p_array[j]['C']
                found = True
                break
        if not found:  # Non-existant panel
            continue
        else:  # Do all json here
            panel_text = f"{p_array[j]['Panel']:02d}"
            element_json.append({
                "background": {
                    "color": {
                        "field": panel_text,
                        "fixed": "#D9D9D9"
                    },
                    "image": {
                        "fixed": ""
                    }
                },
                "border": {
                    "color": {
                        "fixed": f"{p_array[j]['Color']}",
                    },
                    "width": 5
                },
                "config": {
                    "align": "right",
                    "color": {
                        "field": f"{panel_text}Color",
                        "fixed": "#000000"
                    },
                    "text": {
                        "fixed": panel_text
                    },
                    "valign": "bottom"
                },
                "constraint": {
                    "horizontal": "left",
                    "vertical": "top"
                },
                "name": f"Panel{panel_text}",
                "placement": {
                    "height": 45,
                    "left": 5 + (79 * (c - 1)),
                    "top": 32 + (48 * (r - 1)),
                    "width": 76
                },
                "type": "rectangle"
            })
            element_json.append({
                "background": {
                    "color": {
                        "fixed": "transparent"
                    }
                },
                "border": {
                    "color": {
                        "fixed": "dark-green"
                    }
                },
                "config": {
                    "align": "left",
                    "color": {
                        "field": f"{panel_text}Color",
                        "fixed": "#000000"
                    },
                    "text": {
                        "field": panel_text,
                        "mode": "field"
                    },
                    "valign": "middle"
                },
                "constraint": {
                    "horizontal": "left",
                    "vertical": "top"
                },
                "name": f"Panel{panel_text}Watts",
                "placement": {
                    "height": 20,
                    "left": 11 + (79 * (c - 1)),
                    "top": 34 + (48 * (r - 1)),
                    "width": 68
                },
                "type": "rectangle"
            })
            current_query_json.append({
                "alias": panel_text,
                "datasource": {
                    "type": "influxdb",
                    "uid": "${DS_INFLUXDB-FOR-LIBRARY-PANEL}"
                },
                "hide": False,
                "query": f"SELECT last(\"lastReportWatts\") FROM \"local\".\"LocalData_Enphase\" WHERE (\"serialNumber\" = '{p_array[j]['SN']}')",
                "rawQuery": True,
                "refId": f"{get_ref_id(p_array[j]['Panel'], 0)}",
                "resultFormat": "time_series"
            })
            xf_json.append({
                "id": "calculateField",
                "options": {
                    "alias": f"{panel_text}Color",
                    "mode": "reduceRow",
                    "reduce": {
                        "include": [
                            panel_text
                        ],
                        "reducer": "lastNotNull"
                    }
                }
            })

            production_query_json.append({
                "alias": panel_text,
                "datasource": {
                    "type": "influxdb",
                    "uid": "${DS_INFLUXDB-FOR-LIBRARY-PANEL}"
                },
                "hide": False,
                "query": f"SELECT integral(\"lastReportWatts\")  / 3600 FROM \"local\".\"LocalData_Enphase\" WHERE (\"serialNumber\" = '{p_array[j]['SN']}') AND $timeFilter",
                "rawQuery": True,
                "refId": f"{get_ref_id(p_array[j]['Panel'], 0)}",
                "resultFormat": "time_series"
            })
            time_series_json.append({
                "matcher": {
                    "id": "byName",
                    "options": panel_text
                },
                "properties": [
                    {
                        "id": "color",
                        "value": {
                            "fixedColor": f"{p_array[j]['Color']}",
                            "mode": "fixed"
                        }
                    }
                ]
            })
            time_series_aliases_json.append({
                "alias": panel_text,
                "datasource": {
                    "type": "influxdb",
                    "uid": "${DS_INFLUXDB-FOR-LIBRARY-PANEL}"
                },
                "groupBy": [
                    {
                        "params": [
                            "$__interval"
                        ],
                        "type": "time"
                    },
                    {
                        "params": [
                            "serialNumber"
                        ],
                        "type": "tag"
                    }
                ],
                "hide": False,
                "measurement": "LocalData_Enphase",
                "orderByTime": "ASC",
                "policy": "local",
                "refId": f"{get_ref_id(p_array[j]['Panel'], 2)}",
                "resultFormat": "time_series",
                "select": [
                    [
                        {
                            "params": [
                                "lastReportWatts"
                            ],
                            "type": "field"
                        },
                        {
                            "params": [],
                            "type": "distinct"
                        }
                    ]
                ],
                "tags": [
                    {
                        "key": "serialNumber",
                        "operator": "=",
                        "value": p_array[j]['SN']
                    }
                ]
            })

    current_query_json.append({
        "alias": "Total",
        "datasource": {
            "type": "influxdb",
            "uid": "${DS_INFLUXDB-FOR-LIBRARY-PANEL}"
        },
        "hide": False,
        "query": "SELECT sum(last) from (SELECT last(\"lastReportWatts\") FROM \"local\".\"LocalData_Enphase\" GROUP BY \"serialNumber\")",
        "rawQuery": True,

        "refId": f"{get_ref_id(len(p_array), 0)}",
        "resultFormat": "time_series"
    })
    production_query_json.append({
        "alias": "Total",
        "datasource": {
            "type": "influxdb",
            "uid": "${DS_INFLUXDB-FOR-LIBRARY-PANEL}"
        },
        "hide": False,
        "query": "SELECT sum(integral) from (SELECT integral(\"lastReportWatts\")  / 3600 FROM \"local\".\"LocalData_Enphase\" WHERE $timeFilter GROUP BY \"serialNumber\")",
        "rawQuery": True,
        "refId": f"{get_ref_id(len(p_array), 0)}",
        "resultFormat": "time_series"

    })

    # Make FinalFile:
    add_template('Header1.template', FinalFile)
    add_json(FinalFile, element_json, 12, True)
    add_template('OutputTtlPanels.template', FinalFile)
    add_json(FinalFile, current_query_json, 8, False)
    FinalFile.write(
        "\n        ],\n        \"title\": \"Solar Panels - Current Output Templete\",\n        \"transformations\": [\n")
    add_json(FinalFile, xf_json, 8, False)  # Add in transformations for Current Output Canvas
    add_template('Header2.template', FinalFile)# Add Header for Total Production Canvas
    add_json(FinalFile, element_json, 12, True) # Add Production Canvas Element Elements (same as Current Output)
    add_template('ProductionTtlPanels.template', FinalFile)
    add_json(FinalFile, production_query_json, 8, False)
    FinalFile.write(
        "\n        ],\n        \"title\": \"Solar Panel Production Template Between ${__from:date:YYYY-MMM-DD HH:MM} and ${__to:date:YYYY-MMM-DD HH:MM}\",\n        \"transformations\": [\n")
    add_json(FinalFile, xf_json, 8, False)  # Add Production Canvas transformations (same as Current Output)
    add_template('TimeSeriesHeader.template', FinalFile)
    add_json(FinalFile, time_series_json, 10, False)    # Add in color overrides for time series panel
    add_template('TimeSeriesTrailer.template', FinalFile)
    add_json(FinalFile, time_series_aliases_json, 8, False)     # Add in aliases for time series panel
    add_template('Trailer.template', FinalFile)
    FinalFile.close()

    print(f"\nDashboard JSON file '{out_file_name}' created. Go to Grafana, Dashboards, New, Import & open this file.\n"
          f"If you have not run Powerwall-Dashboard's ./setup.sh since running setup-enphase.sh, be sure to, followed by reboot!\n")
    save_session(p_array)
sys.exit(0)
