#!/usr/bin/env python
__author__ = 'Justin Bollinger'

import syslog_client
import glob
import csv
import sys
import re
import getopt
import os
import time
import zipfile
from ciscoconfparse import CiscoConfParse
import emailreport
import ConfigParser



def writecsv(orgdir,report):
    os.chdir(orgdir)
    with open(outputfile, 'wb') as csvfile:
        outfile = csv.writer(csvfile, delimiter=',', quotechar="'", quoting=csv.QUOTE_MINIMAL)
        # Write the header to the CSV file
        outfile.writerow(csvheader)
        # If input file was a zip then change directory to the temp location
        for index, rlist in report.iteritems():
            outfile.writerow(rlist)

def parse_configs(cfgdir, verbose_mode):
    global int_index
    report = {}
    switchname = ''
    os.chdir(cfgdir)
    for f1 in configfiles:
        #strip the .txt off of the file name if it exists
        configfile = re.search('(\S+)\.txt', str(f1))
        switchname = configfile.group(1)
        site = switchname[0:3].upper()
        region = "unknown"
        if site in APAC_sites:
            region = "APAC"
        elif site in EMEA_sites:
            region = "EMEA"
        elif site in AMER_sites:
            region = "AMER"
        phase = "unknown"
        if site in phase_2:
            phase = "2"
        elif site in phase_3:
            phase = "3"
        elif site in phase_4:
            phase = "4"
        elif site in phase_5:
            phase = "5"
        if switchname.upper() not in excluded_switches:
            if verbose_mode:
                print 'Working on', switchname
            parse = CiscoConfParse(f1)
            all_intfs = parse.find_objects(r"^interface\s(Gi|Fa)")
            for obj in all_intfs:
                interfacename = obj.geneology_text[0].lstrip('interface ')
                if obj.re_search_children(r"access-group ACL-ALLOW.*in$") and \
                   obj.re_search_children(r'dot1x pae authenticator'):
                    try:
                        vlan_obj = obj.re_search_children(r'switchport access vlan (\S+)')
                        vlan_match = re.search(r'switchport access vlan (\S+)',vlan_obj[0].text)
                        if vlan_match:
                            vlan = vlan_match.group(1)
                    except:
                        print >> sys.stderr, switchname + " " + interfacename + " is configured for VLAN 1 and is"\
                                              " in monitor mode"
                        vlan = '1'
                    report[int_index] = [switchname,interfacename, 'Monitor Mode', vlan, site, region,phase]
                    int_index += 1
                elif obj.re_search_children(r"access-group ACL-PREAUTH.*in$") and \
                     obj.re_search_children(r'dot1x pae authenticator'):
                    try:
                        vlan_obj = obj.re_search_children(r'switchport access vlan (\S+)')
                        vlan_match = re.search(r'switchport access vlan (\S+)',vlan_obj[0].text)
                        if vlan_match:
                            vlan = vlan_match.group(1)
                    except:
                        print >> sys.stderr, switchname + " " + interfacename + " is configured for VLAN 1 and is"\
                                              " in authentication mode"
                        vlan = '1'
                    report[int_index] = [switchname,interfacename, 'Authentication Mode',vlan,site, region, phase]
                    int_index += 1
                else:
                    for vlan in included_vlans:
                        if (obj.re_search_children(r'switchport access vlan ' + vlan) and \
                            obj.re_search_children(r'switchport mode access')) \
                            or \
                           (obj.re_search_children(r'switchport access vlan ' + vlan) and not \
                            obj.re_search_children(r'switchport mode trunk')):
                            report[int_index] = [switchname,interfacename, 'ISE Disabled',vlan,site, region,phase]
                            int_index += 1
    return report

def difTodayYesterday(output):
    import difflib
    from datetime import date, timedelta
    import time
    import shutil
    yesterday = date.today() - timedelta(1)
    file1 = time.strftime('%Y_%m_%d' + '.csv')
    file2 = yesterday.strftime('%Y_%m_%d' + '.csv')
    lines1 = []
    lines2 = []
    with open(file1, 'rb') as f:
        for line in f:
            lines1.append(line)
    try:
        with open(file2, 'rb') as f:
            for line in f:
                lines2.append(line)
        diff = difflib.unified_diff(lines2, lines1, fromfile='file2', tofile='file1', lineterm='')
        lines = list(diff)[2:]
        added = [line[1:] for line in lines if line[0] == '+']
        removed = [line[1:] for line in lines if line[0] == '-']

        print 'Lines added or changed, ignoring position\r\n    '

        for line in added:
            if line not in removed:
                output.append(line.strip("\r\n"))
                print line
    except:
        file2 = ''
    print 'File1 is', file1
    if file2 is not '':
        print 'File2 is', file2
    else:
        print 'File2 is does not exist skiped comparison'

    return output, file1, file2

def print_help():
    print 'ISEAudit.py -d [config directory] -v (optional)'
# init of variables
configfiles = []
origionaldir = os.getcwd()
outputfile = str(origionaldir) + str('\\') + time.strftime('%Y_%m_%d.csv')
configdirectory = origionaldir
config = ConfigParser.ConfigParser()
config.read('config.ini')
sysloghost = config.get("Syslog", "host")
email_enabled = config.get("Email", "enabled").upper()
syslog_enabled = config.get('Syslog','enabled').upper()
syslog_source = config.get('Syslog','syslog_source')
syslogheader = time.strftime("%b %d %Y %H:%M:%S") + " " + syslog_source + " "
leefheader = "LEEF:1.0|ISE|ISE Audit|1.0|1|"
included_sites = config.get('Scope','sites').upper().split(' ')
included_vlans = config.get('Scope','vlans').split(' ')
excluded_switches = config.get('Scope', 'excluded_switches').upper().split(' ')
excluded_sites = config.get('Scope', 'excluded_sites').upper().split(' ')
APAC_sites = config.get('Regions','APAC').upper().split(' ')
AMER_sites = config.get('Regions','AMER').upper().split(' ')
EMEA_sites = config.get('Regions','EMEA').upper().split(' ')
phase_2 = config.get('ProjectPhase','two').upper().split(' ')
phase_3 = config.get('ProjectPhase','three').upper().split(' ')
phase_4 = config.get('ProjectPhase','four').upper().split(' ')
phase_5 = config.get('ProjectPhase','five').upper().split(' ')
verbose_mode = False
int_index = 0
csvheader = ['Switch', 'Interface', 'Mode', 'vlan','site code','Region','Phase Number','Notes/description']

#System arguments for input and output files
try:
    opts, args = getopt.getopt(sys.argv[1:],"hd:v",["directory=","verbose"])
except getopt.GetoptError:
    print_help()
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print_help()
        sys.exit()
    elif opt in ("-d", "--directory"):
        configdirectory = arg
    elif opt in ("-v", "--verbose"):
        verbose_mode = True

os.chdir(configdirectory)
all_configfiles = glob.glob('*.txt')
for file in all_configfiles:
    if 'ALL' in included_sites:
        if not file[0:3].upper() in excluded_sites:
            configfiles.append(file)
    else:
        if not file[0:3].upper() in included_sites:
            configfiles.append(file)
print "Starting Config Parsing..."
report = parse_configs(configdirectory,verbose_mode)
os.chdir(origionaldir)
writecsv(origionaldir,report)
msg = []
print "Checking differences between today and yesterday"
differences = difTodayYesterday(msg)
files = []
files.append(str(differences[1]))
if differences[2] is not '':
    files.append(str(differences[2]))
#
# Zip file to report.zip to attach to email
#

with zipfile.ZipFile('report.zip', 'w', zipfile.ZIP_DEFLATED) as myzip:
    for file in files:
        myzip.write(file)
zfile = 'report.zip'
if email_enabled == 'YES':
    emailreport.EmailHTML(msg,zfile)

#
# Syslog Message to QRadar
#
if syslog_enabled == "YES":
    if msg:
        for line in msg:
            print line
            tl = line.split(',')
            logmsg = syslogheader + leefheader + "cat=detected    swhostname=" + str(tl[0]) + "\tinterface=" + str(tl[1]) + "\tAuthZMode=" + str(tl[2])
            syslog_client.syslog(logmsg,sysloghost)

