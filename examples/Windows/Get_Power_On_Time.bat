::    RESTful Interface Tool Sample Script for HPE iLO Products    ::
::  Copyright 2014, 2019 Hewlett Packard Enterprise Development LP ::

:: Description:  This is a sample batch script to get the server   ::
::               power on time.                                    ::

:: NOTE:  You will need to replace the USER_LOGIN and PASSWORD     ::
::        and other values inside the quotation marks with values  ::
::        that are appropriate for your environment.               ::

::        Firmware support information for this script:            ::
::            iLO 5 - All versions                                 ::

@echo off
set argC=0
for %%x in (%*) do Set /A argC+=1
if %argC% EQU 3 goto :remote
if %argC% EQU 0 goto :local
goto :error

:local
ilorest list Oem/Hpe/PowerOnMinutes --selector=ComputerSystem. -u USER_LOGIN -p PASSWORD
ilorest logout
goto :exit
:remote
ilorest list Oem/Hpe/PowerOnMinutes --selector=ComputerSystem. --url %1 --user %2 --password %3
ilorest logout
goto :exit

:error
echo Usage:
echo        remote: Get_Power_On_Time.bat ^<iLO url^> ^<iLO username^>  ^<iLO password^>
echo        local:  Get_Power_On_Time.bat

:exit