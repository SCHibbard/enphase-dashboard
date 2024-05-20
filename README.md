# enphase-dashboard #
Powerwall-Dashboard add-on for Enphase microinverter support

This project will supplement The Powerwall-Dashboard project by @jasoncox with support to gather production data from Enphase microinverters. With it, graphic details of a solar installation show individual output from each solar panel.

![Screenshot from 2024-05-20 11-40-29](https://github.com/SCHibbard/enphase-dashboard/assets/40345296/48342833-77af-4bcb-94aa-757c7dcfc878)

## Requirements ##

- Host system running Linux. This has only been tested on Ubuntu.  Feedback welcome on experiences with other systems.
- Powerwall-Dashboard (github.com/jasonacox/Powerwall-Dashboard) installed and running on the host system.
- An account created for your Enphase system at enlighten.enphaseenergy.com.
- The IP address on your local network
- The serial number of your Enphase Gateway (can be obtained from https://enlighten.enphaseenergy.com > System > Devices).
- A diagram of your arrays that maps the serial numbers of each panel to its physical location in your installation if you plan to create Canvas panels as shown above. Unfortunately, Enphase does not provide this in their customer-access portal.  You will need to contact your installer to get that information.

## Installation ##
- Clone this repo on the host running the dashboard:
```
git clone https://github.com/SCHibbard/enphase-dashboard.git
```

- Move the cloned repo under the main folder for your Powerwall-Dashboard installation, so that the installation script can find necessary environment files.
e.g.:
```
mv ~/enphase-dashboard ~/Powerwall-Dashboard
```


## Setup ##
Two programs are included, a setup script 'setup-enphase.sh' and a Python program 'enphase-canvas.py' The shell script will call the Python program, so you should only have to execute the shell script.
- execute the setup script under the installation folder.  Example:
```
cd ~/Powerwall-Dashboard/enphase-dashboard
./setup-enphase.sh
```
This will add support for gathering Enphase inverter data and storing it in the same InfluxDB database that Powerwall-Dashboard uses.  This includes:
- Adding a new InfluxDB retention policy 'local', where the Enphase data will be stored.
- Adding lines to telegraf.local for Enphase support
- Optionally executing enphase-canvas.py to create custom canvas panels of your solar array. This requires Grafana 10, see below.
- After the Enphase setup is complete, run Powerwall-Dashboard's setup.sh script to activate the added support.

If you create canvas panels, the dashboard generated will include a time-series panel of all inverters' production in addition to the two canvas panels (as image above).  If you do NOT create canvas panels, 'current-state-canvas-panel.json' is included in the repo. It can be installed as a dashboard in Grafana to display a time-series panel of microinverter production.

## Grafana 10 ##
Powerwall-dashboard currently uses Grafana version 9.  With version 10, Grafana introduced a new 'Canvas' panel, which can be used to display a graphic of your solar array.  The shell script will offer to upgrade to version 10 if you are not running.  Caveats:
- Grafana 10 may cause problems with other panels you have setup.  I have only experienced one annoyance.  The panel 'Current State' that is included with Powerwall-Dashboard default dashboards uses the Boom Table visualization type, which is depreciated in version 10.  As of 10.4.1 the panel still works but has an annoying deprecation warning.  An updated 'Current State' panel is included in the repo 'current-state-canvas-panel.json'.  If you load this into Grafana as a dashboard (Grafana > Dashboards > New > Import) it will create a single panel dashboard and add the panel to the 'Library Panels'. You can then delete the Boom Table version in your dashboard(s) and add this one from the library.
- Grafana 10 changes the titles of panels from being centered to Left-justified.  This has proven annoying to some.

During the shell-script setup, if you are not running version 10, you be asked if you want to update.  If you are running it already or update it, you will have the opportunity later to create Canvas panels for your solar array.

## Creating Canvas Panels with enphase-canvas.py ##
enphase-canvas.py is a terminal-based program that will generate a Grafana dashboard of your array containing 3 panels as shown above:
- A Canvas panel showing the current output (in Watts) of each microinverter.
- A Canvas panel showing the total production (in Watthours) of each panel over the selected time range
- A time-series panel showing production of each panel

The program is entirely text driven, showing crude representations of the solar array you build.  It is suggested to run it in terminal full-screen mode, especially for larger solar arrays.  The below instructions are based on the following panel array.  This assumes 2 panel arrays, one on a house & one on a garage.  The house array is 5 panels across and 3 panels down, the garage array is 1 across & 3 down.  The house array (columns 1-5) has two areas where no solar panels are mounted, the top two areas in column 4 (R01C04 and R02C04).  Column 7 is the garage array. Column 6 is used to display a gap between the house and the garage.

<pre>
----R01C01------R01C02------R01C03------R01C04------R01C05------R01C06------R01C07---
|  Panel001 |  Panel002 |  Panel003 |           |  Panel004 |           |  Panel005 |
|           |           |           |           |           |           |           |
----R02C01------R02C02------R02C03------R02C04------R02C05------R02C06------R02C07---
|  Panel006 |  Panel007 |  Panel008 |           |  Panel009 |           |  Panel010 |
|           |           |           |           |           |           |           |
----R03C01------R03C02------R03C03------R03C04------R03C05------R03C06------R03C07---
|  Panel011 |  Panel012 |  Panel013 |  Panel014 |  Panel015 |           |  Panel016 |
|           |           |           |           |           |           |           |
-------------------------------------------------------------------------------------
</pre>

1. When the program starts, it will query your Enphase gateway to get an inventory of all solar panels and their serial numbers.
2. Enter the height (number of rows, 3 in above example), and width (number of columns, 7 in example, to get the gap between house & garage). 
3. a graphical depiction of your choice will be displayed to confirm.
4. Each panel is numbered. These numbers will be displayed on all dashboard panels (see images).  Default behavior in Grafana would display the serial numbers, but a) they are not intuitive, and b) they are 12 digits long. Therefore, this program aliases each inverter with a reference number, as well as a color code. Default is to number them from left to right, top to bottom.  If you would rather have for example the house & garage grouped, you can select custom panel numbering.
5. The program will then request the serial number of each microinverter in their appropriate position on the array.  This is where you need the microinverter mapping information mentioned in the requirements.  If a location is not used, enter 0.  If you have also selected custom panel numbering, this will also be entered at this time.
6. After all serial numbers are entered, the above depiction will be re-drawn, but with the serial numbers and panel numbers selected filled in.  If the array is too large to show the complete serial numbers, they will be shortened to show only the last few digits.
7. You can choose now to edit the diagram if mistakes were made, save the array for future work, or approve it and generate a dashboard JSON.  Note when editing panels, the program will not allow a serial number to be used in two places, so either swap, or edit to a blank location first.
8. Once the JSON is created you can import it into Grafana.

Notes:
1. In the unlikely event you choose to not show all of your inverters in the canvas panels, the time-series panel will still show all connected inverters.
2. Canvas visualization support in Grafana is evolving.  Currently it does a poor job of scaling.  I notice this on mobile devices. A few revs into Grafana 10 support for "pan and Zoom" for Canvas was added, which is activated by the install script, however it still needs work at Grafana!
3. I added titles to my Canvas Panels for 'House' & Garage', as well as a separator between them.  Such customization is not included in the auto-generation yet.
3. When the generated JSON is loaded, it created Grafana library panels for each of the three panels generated.  The good news is 5his enables easily loading them into other dashboards you have.  The bad news is if you make changes in the panel configuration and generate a new JSON, you will have to delete the old panels in Grafana's library, or the changes will not be taken.  You can only delete a library panel if it is not used in any dashboard, so you must delete them from the dashboards first.  This can be improved by generating unique UUIDs for the library panels, that's on the to-do list.
4. Note when the script installs Grafana 10, it does not delete Grafana 9 from Docker.  The image will be there, just not running.  Doesn't hurt anything, but you can delete it via the Docker CLI if you wish.


## Final Notes ##
I am a newbie with Python.  I programmed in assembler, C, Pascal, and other ancient languages between the late '70s and mid '80s before a hiatus of about 35 years.  I know the Python is very far from Pythonic!  While I plan to improve that, constructive criticism or edits are welcome!
