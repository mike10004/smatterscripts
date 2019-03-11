#!/usr/bin/python3
#
# Convert spreadsheet to CSV file.
#
# Based on:
#   PyODConverter (Python OpenDocument Converter) v1.0.0 - 2008-05-05
#   Copyright (C) 2008 Mirko Nasato <mirko@artofsolving.com>
#   Licensed under the GNU LGPL v2.1 - or any later version.
#   http://www.gnu.org/licenses/lgpl-2.1.html
#

import os
import re
from . import ooutils
import sys
import uno
try:
    from com.sun.star.task import ErrorCodeIOException
except ImportError:
    print("ooutils: python3-uno must be installed", file=sys.stderr)
    raise


class SSConverter:
    """
    Spreadsheet converter class.
    Converts spreadsheets to CSV files.
    """

    def __init__(self, oorunner=None):
        self.desktop  = None
        self.oorunner = oorunner


    def convert(self, inputFile, outputFile, verbose=False):
        """
        Convert the input file (a spreadsheet) to a CSV file.

        The input file name can contain a sheet specification to specify a particular sheet.
        The sheet specification is either a number or a sheet name.
        The sheet specification is appended to the file name separated by a colon
        or an at sign: ":" or "@".

        If the output file name contains a %d or %s format specifier, then all the sheets
        in the input file are converted, otherwise only the first sheet is converted.

        If the output file name contains a %d format specifier then the sheet number
        is used when formatting the output file name.
        The format can contain a width specifier (eg %02d).

        If the output file name contains a %s specifier then the sheet name is used
        when formatting the output file name.
        """

        # Start openoffice if needed.
        if not self.desktop:
            if not self.oorunner:
                self.oorunner = ooutils.OORunner()

            self.desktop = self.oorunner.connect()

        # Check for sheet specification in input file name.
        match = re.search(r'^(.*)[@:](.*)$', inputFile)
        if os.path.exists(inputFile) or not match:
            inputUrl   = uno.systemPathToFileUrl(os.path.abspath(inputFile))
            inputSheet = '1'   # Convert first sheet.
        else:
            inputUrl   = uno.systemPathToFileUrl(os.path.abspath(match.group(1)))
            inputSheet = match.group(2)


        # NOTE:
        #   Sheet activation does not work properly when Hidden is specified.
        #   Although the sheet does become the active sheet, it's not the sheet that
        #   gets saved if the spreadsheet is loaded with Hidden=True.
        #
        #   Removing Hidden=True doesn't seem to change anything: nothing appears
        #   on the screen regardless of the Hidden value.
        #
        # document  = self.desktop.loadComponentFromURL(inputUrl, "_blank", 0, ooutils.oo_properties(Hidden=True))
        document  = self.desktop.loadComponentFromURL(inputUrl, "_blank", 0, ooutils.oo_properties())

        try:
            props = ooutils.oo_properties(FilterName="Text - txt - csv (StarCalc)")
            #
            # Another useful property option:
            #   FilterOptions="59,34,0,1"
            #     59 - Field separator (semicolon), this is the ascii value.
            #     34 - Text delimiter (double quote), this is the ascii value.
            #      0 - Character set (system).
            #      1 - First line number to export.
            #
            # For more information see:
            #   http://wiki.services.openoffice.org/wiki/Documentation/DevGuide/Spreadsheets/Filter_Options

            # To convert a particular sheet, the sheet needs to be active.
            # To activate a sheet we need the spreadsheet-view, to get the spreadsheet-view
            # we need the spreadsheet-controller, to get the spreadsheet-controller
            # we need the spreadsheet-model.
            #
            # The spreadsheet-model interface is available from the document object.
            # The spreadsheet-view interface is available from the controller.
            #
            controller = document.getCurrentController()
            sheets     = document.getSheets()

            # If the output file name contains a %d or %s format specifier, convert all sheets.
            # Use the sheet number if the format is %d, otherwise the sheet name.
            dfmt = re.search(r'%[0-9]*d', outputFile)
            sfmt = re.search(r'%s', outputFile)

            if dfmt  or  sfmt:
                i = 0
                while i < sheets.getCount():
                    # Activate the sheet.
                    sheet = sheets.getByIndex(i)
                    controller.setActiveSheet(sheet)

                    # Create output file name.
                    if dfmt:
                        ofile = outputFile % (i+1)
                    else:
                        ofile = outputFile % sheet.getName().replace(' ', '_')

                    if verbose:
                        print("    %s" % ofile)

                    # Save the sheet to the output file.
                    outputUrl = uno.systemPathToFileUrl(os.path.abspath(ofile))
                    document.storeToURL(outputUrl, props)
                    i += 1

            else:
                # Activate the sheet to be converted.
                if re.search(r'^\d+$', inputSheet):
                    sheet = sheets.getByIndex(int(inputSheet)-1)
                else:
                    sheet = sheets.getByName(inputSheet)

                controller.setActiveSheet(sheet)
                outputUrl = uno.systemPathToFileUrl(os.path.abspath(outputFile))
                document.storeToURL(outputUrl, props)
        finally:
            if document: document.close(True)

_ERR_PROCESSING = 2

def main():
    from sys import argv
    from argparse import ArgumentParser
    if len(argv) == 2  and  argv[1] == '--shutdown':
        ooutils.oo_shutdown_if_running()
    else:
        p = ArgumentParser(description="Export spreadsheet worksheets to CSV files.", epilog="Use --shutdown to shut down running instance.")
        p.add_argument("input", metavar="INPUT[:SHEET]", help="input file, optionally with single sheet specification")
        p.add_argument("output", metavar="OUTPUT[%s|%d].csv", help="output file")
        p.add_argument("-v", "--verbose", action="store_true", help="print messages about processing")
        p.add_argument("--shutdown", action="store_true", help="shut down running instance")
        args = p.parse_args()
        if args.shutdown: p.error("--shutdown must be only option, with no positional arguments")
        converter = SSConverter()
        try:
            converter.convert(args.input, args.output, args.verbose)
        except ErrorCodeIOException as exception:
            print("ERROR! ErrorCodeIOException %d" % exception.ErrCode, file=sys.stderr)
            return _ERR_PROCESSING
    return 0


if __name__ == "__main__":
    exit(main())