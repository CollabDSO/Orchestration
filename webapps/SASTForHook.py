import os
import uuid
import getopt
import traceback
import time
import stat
from subprocess import call
from MasterConfig import *
from SASTHTMLReporter import *
from lib.commons import get_report_path
from lib.commons import get_debugger
from lib.logger import Logger
from Email import *

#dir = str(uuid.uuid4().hex)

orchPath = str(os.path.dirname(os.path.realpath(sys.argv[0])))
scanPath = "//home//ubuntu//Tools//ClientScans"
reportPath = get_report_path(REPORT_PATH, "SAST_Reports")
odcCSVPath = reportPath + "//dependency-check-report.csv"
OWASPBinPath = '//home//ubuntu//Tools//dependency-check//bin'
flag = False

log = Logger(get_debugger(reportPath))
#time = datetime.now()
log.record('debug', "SAST Scan Started at: " + str(time))
log.record('debug', "Value of report path is: " + reportPath)
log_path = os.path.join(reportPath, "Debug")
log.record('debug', "Value of log_path is: " + log_path)

def copycssForReport():
    try:
        if CSSFilePath:
            copytree(CSSFilePath, reportPath+'//css')
            log.record('debug', "Successfully copied CSS to target location")
        else:
            log.record('debug', "Issue copying CSS file to target location")
    except Exception as e:
        log.record('debug', str(e))

def startSAST(key, projectname, version, gitURL, rEmail):
    try:
         repoName = gitURL.split('.git')[0].split('/')[-1]
         if(len(os.listdir(scanPath)) != 0):
             cleanDir()
             #os.system("rm -rf " + scanPath + "//{*,.*}")
         os.chdir(scanPath)
         os.system("git clone " + gitURL)
         log.record('debug', 'Initiating SAST Scan')
         #START - OWASP Dependency Check
         log.record('debug', 'Starting OWASP Dependency Scan')
         os.chdir(OWASPBinPath)
         os.system(
             'sudo ./dependency-check.sh --enableExperimental --scan ' + scanPath + ' --out ' + reportPath + ' --format CSV')
         log.record('debug', 'OWASP Dependency Scan Complete')
         #END - OWASP Dependency Check


         # START - SonarQube
         log.record('debug', 'Starting SonarQube Scan')
         os.chdir(scanPath)
         f = open("sonar-project.properties", "w")
         f.write("sonar.projectKey=" + key + "\n")
         f.write("sonar.projectName=" + projectname + "\n")
         f.write("sonar.projectVersion=" + version + "\n")
         modScanPath = scanPath.replace('/', '//')
         f.write("sonar.projectBaseDir=" + repoName + "\n")
         f.write("sonar.sources=.\n")
         f.close()
         #configs = Properties()
        # with open("sonar-project.properties", 'rb') as config_file:
         #    configs.load(config_file)
         #projectBaseDir = configs.get('sonar.projectBaseDir')
         #os.chdir(str(projectBaseDir.data))
         os.chdir(modScanPath)
         os.system('sonar-scanner')
         log.record('debug', 'SonarQube Complete')
         # END - SonarQube
         log.record('debug', 'SAST Scan Ended')

         if os.path.exists(odcCSVPath):
             copycssForReport()
             flag = generateSASTReport(odcCSVPath, reportPath)
             sendEmail(reportPath + "/Dummy", "SAST", rEmail)
         else:
             log.record('debug', 'SAST Scan might not have run properly! Please check.')
         print("FLAG IS====>>>>>>>" + flag)
         return flag

    except Exception as e:
        log.record('debug', str(e))

def cleanDir():
    for root, dirs, files in os.walk(scanPath):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
        