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
"""This is the helper module for RDMC"""

#---------Imports---------

import os
import glob
import shlex

from optparse import OptionParser, OptionGroup

import six

import cliutils
import versioning

#---------End of imports---------

#Using hard coded list until better solution is found
HARDCODEDLIST = ["name", "modified", "type", "description",
                 "attributeregistry", "links", "settingsresult",
                 "actions", "availableactions", "id", "extref"]

class CommandBase(object):
    """Abstract base class for all Command objects.

    This class is used to build complex command line programs
    """
    def __init__(self, name, usage, summary, aliases=None, optparser=None):
        self.name = name
        self.summary = summary
        self.aliases = aliases
        self.config_required = True # does the command access config data

        if optparser is None:
            self.parser = cliutils.CustomOptionParser()
        else:
            self.parser = optparser

        self.parser.usage = usage
        self._cli = cliutils.CLI()

    def run(self, line):
        """Called to actually perform the work.

        Override this method in your derived class.  This is where your program
        actually does work.
        """
        pass

    def ismatch(self, cmdname):
        """Compare cmdname against possible aliases.

        Commands can have aliases for syntactic sugar.  This method searches
        aliases for a match.

        :param cmdname: name or alias to search for
        :type cmdname: str.
        :returns: boolean -- True if it matches, otherwise False
        """
        if not cmdname:
            return False

        cmdname_lower = cmdname.lower()
        if self.name.lower() == cmdname_lower:
            return True

        if self.aliases:
            for alias in self.aliases:
                if alias.lower() == cmdname_lower:
                    return True

        return False

    def print_help(self):
        """Automated help printer.
        """
        self.parser.print_help()

    def print_summary(self):
        """Automated summary printer.
        """
        maxsum = 45
        smry = self.summary

        if not smry:
            smry = ''

        sumwords = smry.split(' ')
        lines = []
        line = []
        linelength = 0

        for sword in sumwords:
            if linelength + len(sword) > maxsum:
                lines.append(' '.join(line))
                line = []
                linelength = 0

            line.append(sword)
            linelength += len(sword) + 1

        lines.append(' '.join(line))

        sep = '\n' + (' ' * 34)
        print("  %-28s - %s" % (self.name, sep.join(lines)))

    def _parse_arglist(self, line=None):
        """parses line into an options and args taking
        special consideration of quote characters into account

        :param line: string of arguments passed in
        :type line: str.
        :returns: args list
        """
        if line is None:
            return self.parser.parse_args(line)

        arglist = []
        if isinstance(line, six.string_types):
            arglist = shlex.split(line, posix=False)

            for ind, val in enumerate(arglist):
                arglist[ind] = val.strip('"\'')
        elif isinstance(line, list):
            arglist = line

        exarglist = []
        if os.name == 'nt':
            # need to glob for windows
            for arg in arglist:
                gob = glob.glob(arg)

                if gob and len(gob) > 0:
                    exarglist.extend(gob)
                else:
                    exarglist.append(arg)

        else:
            for arg in arglist:
                exarglist.append(arg)

        return self.parser.parse_args(exarglist)

class RdmcCommandBase(CommandBase):
    """Base class for rdmc commands which includes some common helper
       methods.
    """

    def __init__(self, name, usage, summary, aliases, optparser=None):
        """ Constructor """
        CommandBase.__init__(self,\
            name=name,\
            usage=usage,\
            summary=summary,\
            aliases=aliases,\
            optparser=optparser)
        self.json = False
        self.cache = False
        self.nologo = False

    def is_enabled(self):
        """ If reachable return true for command """
        return True

    def enablement_hint(self):
        """
        Override to define a error message displayed to the user
        when command is not enabled.
        """
        return ""

class RdmcOptionParser(OptionParser):
    """ Constructor """
    def __init__(self):
        OptionParser.__init__(self,\
            usage="Usage: %s [GLOBAL OPTIONS] [COMMAND] [ARGUMENTS]"\
            " [COMMAND OPTIONS]" % versioning.__shortname__)

        globalgroup = OptionGroup(self, "GLOBAL OPTIONS")

        #to correct the capitalization on help text:
        self.option_list[0].help = 'Show this help message and exit.'

        self.add_option(
            '-c',
            '--config',
            dest='config',
            help="Use the provided configuration file instead of the default"\
            " one.",
            metavar='FILE'
        )

        config_dir_default = os.path.join(cliutils.get_user_config_dir(),\
                                            '.%s' % versioning.__shortname__)
        self.add_option(
            '--cache-dir',
            dest='config_dir',
            default=config_dir_default,
            help="Use the provided directory as the location to cache data"\
            " (default location: %s)" % config_dir_default,
            metavar='PATH'
        )
        globalgroup.add_option(
            '-v',
            '--verbose',
            dest='verbose',
            action="store_true",
            help="""Display verbose information.""",
            default=False
        )
        globalgroup.add_option(
            '-d',
            '--debug',
            dest='debug',
            action="store_true",
            help="""Display debug information.""",
            default=False
        )
        globalgroup.add_option(
            '--logdir',
            dest='logdir',
            default=None,
            help="""Use the provided directory as the location for log file.""",
            metavar='PATH'
        )
        globalgroup.add_option(
            '--nocache',
            dest='nocache',
            action="store_true",
            help="During execution the application will temporarily store"\
            " data only in memory.",
            default=False
        )
        globalgroup.add_option(
            '--nologo',
            dest='nologo',
            action="store_true",
            help="""Include to block copyright and logo.""",
            default=False
        )
        globalgroup.add_option(
            '--redfish',
            dest='is_redfish',
            action='store_true',
            help="Use this flag if you wish to to enable "\
                "Redfish only compliance. It is enabled by default "\
                "in systems with iLO5 and above.",
            default=False
        )
        globalgroup.add_option(
            '--latestschema',
            dest='latestschema',
            action='store_true',
            help="Optionally use the latest schema instead of the one "\
            "requested by the file. Note: May cause errors in some data "\
            "retreval due to difference in schema versions.",
            default=False
        )
        globalgroup.add_option(
            '--proxy',
            dest='proxy',
            default=None,
            help="""Use the provided proxy for communication.""",
            metavar='URL'
        )
        self.add_option_group(globalgroup)
