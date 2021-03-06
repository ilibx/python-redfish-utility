###
# Copyright 2017 Hewlett Packard Enterprise, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

# -*- coding: utf-8 -*-
""" Factory Defaults Command for rdmc """
import sys
import time

from optparse import OptionParser, SUPPRESS_HELP
from collections import OrderedDict

import colorama
from six.moves import input

from rdmc_base_classes import RdmcCommandBase
from rdmc_helper import ReturnCodes, InvalidCommandLineError, InvalidCommandLineErrorOPTS,\
                    NoContentsFoundForOperationError, IncompatibleiLOVersionError, Encryption

CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'

class OneButtonEraseCommand(RdmcCommandBase):
    """ Backup and restore server using iLO's .bak file """
    def __init__(self, rdmcObj):
        RdmcCommandBase.__init__(self,\
            name='onebuttonerase',\
            usage='onebuttonerase [OPTIONS]\n\n\t'\
                'Erase all iLO settings, Bios settings, User Data, and iLO Repository data.'\
                '\n\texample: onebuttonerase\n\n\tSkip the confirmation before'\
                ' erasing system data.\n\texample: onebuttonerase --confirm\n\nWARNING: This '\
                'command will erase user data! Use with extreme caution! Complete erase can take'\
                ' up to 24 hours to complete.',\
            summary='Performs One Button Erase on a system .',\
            aliases=None,\
            optparser=OptionParser())
        self.definearguments(self.parser)
        self._rdmc = rdmcObj
        self.typepath = rdmcObj.app.typepath
        self.lobobj = rdmcObj.commands_dict["LoginCommand"](rdmcObj)
        self.logoutobj = rdmcObj.commands_dict["LogoutCommand"](rdmcObj)
        self.rebootobj = rdmcObj.commands_dict["RebootCommand"](rdmcObj)

    def run(self, line):
        """ Main onebuttonerase function

        :param line: string of arguments passed in
        :type line: str.
        """
        try:
            (options, args) = self._parse_arglist(line)
        except:
            if ("-h" in line) or ("--help" in line):
                return ReturnCodes.SUCCESS
            else:
                raise InvalidCommandLineErrorOPTS("")

        if args:
            raise InvalidCommandLineError("onebuttonerase command takes no arguments.")

        self.onebuttonerasevalidation(options)

        select = "ComputerSystem."
        results = self._rdmc.app.select(selector=select)

        if self._rdmc.app.getiloversion() < 5.140:
            raise IncompatibleiLOVersionError('One Button Erase is only available on iLO 5 1.40 '\
                                                                                    'and greater.')
        try:
            results = results[0].dict
        except:
            raise NoContentsFoundForOperationError("Unable to find %s" % select)

        if results['Oem']['Hpe']['SystemROMAndiLOEraseStatus'] == 'Idle' and \
                            results['Oem']['Hpe']['UserDataEraseStatus'] == 'Idle':

            post_path = None
            body_dict = {"SystemROMAndiLOErase": True, "UserDataErase": True}
            for item in results['Oem']['Hpe']['Actions']:
                if 'SecureSystemErase' in item:
                    post_path = results['Oem']['Hpe']['Actions'][item]['target']
                    break

            if options.confirm:
                userresp = 'erase'
            else:
                userresp = input('Please type "erase" to begin erase process. Any other input will'\
                  ' cancel the operation. If you wish to skip this prompt add the --confirm flag: ')

            if userresp == 'erase':
                if post_path and body_dict:
                    self._rdmc.app.post_handler(post_path, body_dict)
                    self._rdmc.app.post_handler(results['Actions']['#ComputerSystem.Reset']\
                                                ['target'], {"Action": "ComputerSystem.Reset", \
                                                                    "ResetType": "ForceRestart"})
                    self.monitor_erase(results['@odata.id'])
                    return ReturnCodes.SUCCESS
                else:
                    NoContentsFoundForOperationError("Unable to start One Button Erase.")
            else:
                sys.stdout.write("Canceling One Button Erase.\n")
                return ReturnCodes.SUCCESS
        else:
            sys.stdout.write("System is already undergoing a One Button Erase process...\n")
        if not options.nomonitor:
            self.monitor_erase(results['@odata.id'])

        return ReturnCodes.SUCCESS

    def monitor_erase(self, path):
        """ Monitor the One Button Erase progress

        :param path: Path to the one button monitor path
        :type path: str.
        """
        print_dict = {'BIOSSettingsEraseStatus': 'Bios Settings Erase:', 'iLOSettingsEraseStatus': \
         'iLO Settings Erase:', 'ElapsedEraseTimeInMinutes': 'Elapsed Time in Minutes:', \
         'EstimatedEraseTimeInMinutes': 'Estimated Remaining Time in Minutes:', \
         'NVDIMMEraseStatus': 'NVDIMM Erase:', 'NVMeDrivesEraseStatus': 'NVMe Drive Erase:',\
         'SATADrivesEraseStatus': 'SATA Drive Erase:', 'TPMEraseStatus': 'TPM Erase:',\
         'SmartStorageEraseStatus': 'Smart Storage Erase:', 'SystemROMAndiLOEraseStatus': \
         'Bios and iLO Erase:', 'UserDataEraseStatus': 'User Data Erase:'}
        colorama.init()

        sys.stdout.write('\tOne Button Erase Status\n')
        sys.stdout.write('==========================================================\n')
        results = self._rdmc.app.get_handler(path, service=True, silent=True)
        counter = 0
        eraselines = 0
        while True:
            if not (counter + 1) % 8:
                results = self._rdmc.app.get_handler(path, service=True, silent=True)
            print_data = self.gather_data(results.dict['Oem']['Hpe'])

            self.reset_output(eraselines)

            for key in print_data.keys():
                self.print_line(print_dict[key], print_data[key], counter)
            if counter == 7:
                counter = 0
            else:
                counter += 1
            if all([print_data[key].lower() in ['completedwithsuccess', 'completedwitherrors', \
                'failed'] for key in print_data.keys() if not key.lower() in \
                                    ['elapsederasetimeinminutes', 'estimatederasetimeinminutes']]):
                break
            eraselines = len(print_data.keys())
            time.sleep(.5)
        colorama.deinit()
        self.logoutobj.run("")

    def gather_data(self, resdict):
        """ Gather information on current progress from response

        :param resdict: response dictionary to parse
        :type resdict: dict.
        """
        retdata = OrderedDict()
        data = [('ElapsedEraseTimeInMinutes', None), ('EstimatedEraseTimeInMinutes', None),\
         ('SystemROMAndiLOEraseComponentStatus', ['BIOSSettingsEraseStatus', \
         'iLOSettingsEraseStatus']), ('UserDataEraseComponentStatus', ['NVDIMMEraseStatus',\
         'NVMeDrivesEraseStatus', 'SATADrivesEraseStatus', 'SmartStorageEraseStatus', \
         'TPMEraseStatus'])]
        for key, val in data:
            if val:
                if key == 'SystemROMAndiLOEraseComponentStatus':
                    try:
                        resdict[key]
                    except KeyError:
                        retdata['SystemROMAndiLOEraseStatus'] = resdict\
                                                                ['SystemROMAndiLOEraseStatus']
                elif key == 'UserDataEraseComponentStatus':
                    try:
                        if not resdict[key]:
                            raise KeyError()
                    except KeyError:
                        retdata['UserDataEraseStatus'] = resdict['UserDataEraseStatus']
                for item in val:
                    try:
                        retdata[item] = resdict[key][item]
                    except KeyError:
                        pass
            else:
                try:
                    retdata[key] = resdict[key]
                except KeyError:
                    pass

        return retdata

    def reset_output(self, numlines=0):
        """ reset the output for the next print"""
        for _ in range(numlines):
            sys.stdout.write(CURSOR_UP_ONE)
            sys.stdout.write(ERASE_LINE)

    def print_line(self, pstring, value, ctr):
        """print the line from system monitoring"""
        pline = '%s %s' % (pstring, value)

        spinner = ['|', '/', '-', '\\']
        if str(value).lower() in ['initiated', 'inprogress']:
            pline += '\t%s' %spinner[ctr%4]
        pline += '\n'

        sys.stdout.write(pline)

    def onebuttonerasevalidation(self, options):
        """ one button erase validation function

        :param options: command line options
        :type options: list.
        """
        client = None
        inputline = list()

        if options.encode and options.user and options.password:
            options.user = Encryption.decode_credentials(options.user)
            options.password = Encryption.decode_credentials(options.password)

        try:
            client = self._rdmc.app.get_current_client()
            if options.user and options.password:
                if not client.get_username():
                    client.set_username(options.user)
                if not client.get_password():
                    client.set_password(options.password)
        except:
            if options.user or options.password or options.url:
                if options.url:
                    inputline.extend([options.url])
                if options.user:
                    inputline.extend(["-u", options.user])
                if options.password:
                    inputline.extend(["-p", options.password])
            else:
                if self._rdmc.app.config.get_url():
                    inputline.extend([self._rdmc.app.config.get_url()])
                if self._rdmc.app.config.get_username():
                    inputline.extend(["-u", \
                                  self._rdmc.app.config.get_username()])
                if self._rdmc.app.config.get_password():
                    inputline.extend(["-p", \
                                  self._rdmc.app.config.get_password()])

        if inputline:
            self.lobobj.loginfunction(inputline)
        elif not client:
            raise InvalidCommandLineError("Please login or pass credentials" \
                                          " to complete the operation.")

    def definearguments(self, customparser):
        """ Wrapper function for new command main function

        :param customparser: command line input
        :type customparser: parser.
        """
        if not customparser:
            return
        customparser.add_option(
            '--url',
            dest='url',
            help="Use the provided iLO URL to login.",
            default=None,
        )
        customparser.add_option(
            '-u',
            '--user',
            dest='user',
            help="If you are not logged in yet, including this flag along"\
            " with the password and URL flags can be used to log into a"\
            " server in the same command.""",
            default=None,
        )
        customparser.add_option(
            '-p',
            '--password',
            dest='password',
            help="""Use the provided iLO password to log in.""",
            default=None,
        )
        customparser.add_option(
            '--nomonitor',
            dest='nomonitor',
            help="Optionally include this flag to skip monitoring of the one button erase process "\
            "and simply trigger the operation.",
            action="store_true",
            default=False,
        )
        customparser.add_option(
            '--confirm',
            dest='confirm',
            help="Optionally include this flag to skip the confirmation prompt before starting One"\
            " Button Erase and begin the operation.",
            action="store_true",
            default=False,
        )
        customparser.add_option(
            '-e',
            '--enc',
            dest='encode',
            action='store_true',
            help=SUPPRESS_HELP,
            default=False,
        )
