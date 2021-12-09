#******************************************************************************
# @file    U5_QuickConnect.py
# @version 1.0.0
# @author  MCD Application Team
# @brief   Communicates with the U5 Board over UART to store connection parameters
# ******************************************************************************
# * @attention
#   COPYRIGHT 2015 STMicroelectronics</center>
#  Licensed under MCD-ST Liberty SW License Agreement V2, (the "License");
# You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#       http://www.st.com/software_license_agreement_liberty_v2
#  Unless required by applicable law or agreed to in writing, software 
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ******************************************************************************


import serial                     #Communicate with board via UART
import serial.tools.list_ports    #List COM ports
import sys                        #Take Parameters
import time                       #Delay
import shutil, os                 #Copy and paste
import platform                   #Identify OS
import string                     #string library
import atexit


# List of possible board labels
boards = ["NOD_U585AI"]

def getcwd(config_name):

  # determine if application is a script file or frozen exe
  if getattr(sys, 'frozen', False):
      application_path = os.path.dirname(sys.executable)
  elif __file__:
      application_path = os.path.dirname(__file__)

  return os.path.join(application_path, config_name)

# Determines USB path for the board provisioning process
def findPath():
  op_sys = platform.system()

  USBPATH = ''
  if op_sys == "Windows":
    # Find drive letter
    for l in string.ascii_uppercase:
      if os.path.exists('%s:\\MBED.HTM' % l):
        USBPATH = '%s:\\' % l
        break
      
  elif op_sys == "Linux":
    user = os.getlogin()
    for board in boards:
      temp_path = '/media/%s/%s' % (user, board)
      if os.path.exists(temp_path):
        USBPATH = temp_path
        break
  
  elif op_sys == "Darwin": # Mac
    for board in boards:
      temp_path = '/Volumes/%s' % board
      if os.path.exists(temp_path):
        USBPATH = temp_path
        break
  else:
    sys.exit()
  
  return USBPATH


#Flash a file to STM32 using Drag and Drop
def flash(file, USBPATH, com):

  print("Flashing " + file + " to " + USBPATH)
  shutil.copy(file, USBPATH)

  port = serial.Serial(com, 115200)

  while True:
    if(port.in_waiting > 0):
      port.close()
      return
    time.sleep(0.01)


#Find Serial port for STM32 device
def findPort():
  ports = serial.tools.list_ports.comports()
    
  for p in ports:
    if "stlink" in p.description.lower():
      return p.device
      

  print("ERR: BOARD NOT FOUND")
  sys.exit()


#Pull Wifi credentials from Config.txt
def getCredentials():

  config_path = getcwd('Config.txt')
  
  with open(config_path, 'r') as input:
    for line in input:
      if line.lower().startswith('ssid'):
        ssid = line.split()[-1].strip("\r\n\t")
      if line.lower().startswith('pass'): 
        pswd = line.split()[-1].strip("\r\n\t")
      if line.lower().startswith('id'): 
        idscope = line.split()[-1].strip("\r\n\t")
      if line.lower().startswith('dev'): 
        deviceid = line.split()[-1].strip("\r\n\t")
      if line.lower().startswith('prim'): 
        primaryKey = line.split()[-1].strip("\r\n\t")

  return ssid, pswd, idscope, deviceid, primaryKey


# Waits until serial port has full message in_waiting.
def wait(ser):
    start = ser.in_waiting
    time.sleep(0.5)
    while ser.in_waiting > start:
        time.sleep(0.5)
        start = ser.in_waiting

#Interfaces with EEPPROM firmware to store required credentials
def storeCredentials(port, endpt, ssid, pswd, idscope, deviceID, primaryKey):
  # Setting Baud Rate
  ser = serial.Serial(port, 115200)

  # Send the Endpoint
  ser.write(b'1')
  wait(ser)
  print("Storing Endpoint " + repr(endpt))
  ser.write(bytes(endpt, 'utf-8'))
  ser.write(bytes("\r\n", 'utf-8'))
  wait(ser)

  # Send the SSID
  ser.write(b'2')
  wait(ser)
  print("Storing SSID " + repr(ssid))
  ser.write(bytes(ssid, 'utf-8'))
  ser.write(bytes("\r\n", 'utf-8'))
  wait(ser)

  # Send the PASSWD
  pswdSec = '*' * len(pswd)
  ser.write(b'3')
  wait(ser)
  print("Storing Password " + repr(pswdSec))
  ser.write(bytes(pswd, 'utf-8'))
  ser.write(bytes("\r\n", 'utf-8'))
  wait(ser)

  # Send the IDScope
  ser.write(b'5')
  wait(ser)
  print("Storing Scope ID " + repr(idscope))
  ser.write(bytes(idscope, 'utf-8'))
  ser.write(bytes("\r\n", 'utf-8'))
  wait(ser)

  # Send the Registration
  ser.write(b'6')
  wait(ser)
  print("Storing Thing Name " + repr(deviceID))
  ser.write(bytes(deviceID, 'utf-8'))
  ser.write(bytes("\r\n", 'utf-8'))
  wait(ser)

  # Send the Registration
  ser.write(b'7')
  wait(ser)
  print("Storing Primary Key " + repr(primaryKey))
  ser.write(bytes(primaryKey, 'utf-8'))
  ser.write(bytes("\r\n", 'utf-8'))
  wait(ser)

  # Writing all credentials to EEPROM 
  ser.write(b'8')
  wait(ser)

  # Closing Serial Port
  ser.close()

# Indefinitely Reading Serial communication
def readSerial(port):
  
  ser = serial.Serial(port, 115200) 

  while (True):
    if (ser.inWaiting()>0): 
        data_str = ser.read(ser.inWaiting()).decode('ascii', errors='ignore') 
        print(data_str, end='')
    time.sleep(0.01)


  #closing port on script exit
  atexit.register(ser.close())





def main():
  #Find serial port
  com = findPort()
  print("STM32 COM Port Found: " + com + '\n')

  #Find board path 
  path = findPath()
  print("STM32 File Path Found: " + path + '\n')

  #Collect SSID and PSWD
  ssid, pswd, idscope, deviceID, primaryKey = getCredentials()
  print("Collected Parameters From Config.txt" + '\n')

  #Flash EEPROM project
  flash(getcwd('Binaries/STM32U585_DK_EEPROM.bin'), path, com)
  print('\n')

  #Communicate credentials to board over serial
  endpt = 'global.azure-devices-provisioning.net'
  storeCredentials(com, endpt, ssid, pswd, idscope, deviceID, primaryKey)
  print('\n')

  #Flash main application
  flash(getcwd('Binaries/B-U585I-IOT02A_SampleApp.bin'), path, com)
  print('\n')

  #Print out serial
  readSerial(com)
  


if __name__ == "__main__":
  main()
