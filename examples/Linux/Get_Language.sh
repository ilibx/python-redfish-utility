#!/bin/bash

#    RESTful Interface Tool Sample Script for HPE iLO Products    #
#  Copyright 2014, 2019 Hewlett Packard Enterprise Development LP #

# Description:  This is a sample bash script to read the default  #
#               language on iLO                                   #

# NOTE:  You will need to replace the USER_LOGIN and PASSWORD     #
#        values that are appropriate for your environment.        #

#        Firmware support information for this script:            #
#            iLO 5 - All versions                                 #
#            iLO 4 - All versions.                                #

runLocal(){
  ilorest select ServiceRoot. -u USER_LOGIN -p PASSWORD
  # The line below is for iLO 5 and up.                             #
  ilorest list Oem/Hpe/Manager/DefaultLanguage
  # Uncomment the line below is you are using iLO 4.                #
  #ilorest list Oem/Hp/Manager/DefaultLanguage
  ilorest logout
}

runRemote(){
  ilorest select ServiceRoot. --url=$1 --user $2 --password $3
  # The line below is for iLO 5 and up.                             #
  ilorest list Oem/Hpe/Manager/DefaultLanguage
  # Uncomment the line below is you are using iLO 4.                #
  #ilorest list Oem/Hp/Manager/DefaultLanguage
  ilorest logout
}

error(){
  echo "Usage:"
  echo        "remote: Get_Language.sh ^<iLO url^> ^<iLO username^>  ^<iLO password^>"
  echo        "local:  Get_Language.sh"
}

if [ "$#" -eq "3" ]
then 
  runRemote "$1" "$2" "$3"
elif [ "$#" -eq "0" ]
then
  runLocal
else
  error
fi