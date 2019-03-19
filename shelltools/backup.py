#!/usr/bin/env python3

# -*- coding: utf-8 -*-
#
#       backup.py
#       
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import with_statement
import csv
import shutil
import sys
import os.path
import tempfile
import time
import logging
from optparse import OptionParser
import traceback
import platform

_log = logging.getLogger('backup')

ERR_FILE_ALREADY_EXISTS = 200
ERR_TEMP_PATHNAME_USED = 201
ERR_UNDEFINED = 202
_BACKUP_CONF_FILENAME = ".backup.conf"
_SITE_BACKUP_CONF_FILENAME = "backup.conf"
_USER_BACKUP_CONF_FILENAME = "backup.conf"
_OPTS_NOT_IMPLEMENTED = tuple("keep_extension")
_SITE_CONFIG_DIR = "/etc"
_USER_HOME_DIR = os.getenv('USERPROFILE') or os.getenv('HOME')
_PLATFORM_UNAME = platform.uname()
_PLATFORM_OS = _PLATFORM_UNAME[0]
_STAGE_SITE = 1
_STAGE_USER = 2
_STAGE_DIRECTORY = 3
_STAGE_COMMAND = 4
_CONFIG_STAGES = (_STAGE_SITE, _STAGE_USER, _STAGE_DIRECTORY, _STAGE_COMMAND)
_ALL_OPTS = ("strict", "stacktraces", "destdir", "log_level", "logfile", 
        "overwrite", "config_file", "stamp", "tag", "temp")
_LOG_LEVEL_CHOICES=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),

if _PLATFORM_OS == 'Windows':
    raise NotImplementedError("Windows support is not yet implemented")
_USER_CONFIG_DIR = os.path.join(_USER_HOME_DIR, '.config', _BACKUP_CONF_FILENAME)

def _get_progname(parser=None):
    progname = os.path.basename(sys.argv[0]) or 'backup'
    if parser is not None:
        progname = parser.prog or progname
    return progname

def _check_src_pathname(src_pathname, parser):
    if not os.path.isfile(src_pathname):
        #parser.error("source pathname must exist and be a file")
        raise IOError("%s: source pathname must exist and be a file: %s" % (_get_progname(parser), src_pathname))

def _create_filename(options, srcname, stampfmt="%Y%m%d-%H%M"):
    tag, stamp = None, None
    if options.tag is not None:
        tag = options.tag
    if options.stamp is not None and options.stamp:
        stamp = time.strftime(stampfmt)
    if tag is None and (stamp is None or not stamp):
        raise ValueError("stamp or tag is required, but neither is specified")
    if tag is None and stamp:
        filename = "%s-%s" % (srcname, stamp)
    elif tag is not None and not stamp:
        filename = "%s-%s" % (srcname, tag)
    elif tag is not None and stamp:
        filename = "%s-%s-%s" % (srcname, tag, stamp)
    assert filename is not None
    return filename

def _override(defValues, newValues):
    oplist = _ALL_OPTS
    for k in newValues.__dict__.keys():
        v = newValues.__dict__[k]
        if k in oplist and v is not None:
            defValues.__dict__[k] = v
    return defValues

def _eval_level(option, opt_str, value, parser):
    parser.values.log_level = eval('logging.' + value)

def _config_logging(options):
    """Configures logging based on an options object. The options object
    must be one that was created from a parser passed to the
    add_log_level_option function.
    """
    if options.log_level is None:
        options.log_level = logging.INFO
    logging.basicConfig(logfile=options.logfile, level=options.log_level)
    

def _add_logging_options(parser):
    """Add log destination and log level options to a parser. The log 
    level option sets the log_level attribute of the options object
    returned by parser.parse_args() to a logging.LEVEL value (not a 
    string), and has default value logging.INFO.
    """
    parser.add_option("-L", "--logfile", dest="logfile",
                        metavar="PATHNAME",
                        action="store",
                        help="print log messages to specified file instead" + 
                        " of standard error")
    parser.add_option("-l", "--log-level", dest="log_level",
                        metavar="LEVEL",
                        nargs=1,
                        action="callback",
                        type="str",
                        callback=_eval_level,
                        help="set log level to one of " + 
                            str(_LOG_LEVEL_CHOICES))

def _check_options(parser, options):
    # stamp must be set to False explicitly 
    if options.stamp is None: options.stamp = True
    if not options.stamp and options.tag is None:
        parser.error("backup must be stamped or tagged, but neither is specified")
    if (options.strict and options.overwrite):
        parser.error("overwrite and strict options cannot be used together")
    allopts = set(_ALL_OPTS)
    flagged = set()
    for k in options.__dict__.keys():
        if k in allopts and options.__dict__[k] is not None and k in _OPTS_NOT_IMPLEMENTED:
            raise NotImplementedError("options not yet implemented: " + str(_OPTS_NOT_IMPLEMENTED))

def _configure(argv):
    """Create a parser and parse command line arguments.
    """
    parser = OptionParser(version="%prog 0.3", usage="""
    %prog [OPTIONS] PATHNAME
Makes a copy of a file. The filename of the copy contains the current 
timestamp by default. This is the 'ideal' destination filename. 

The program first creates a temporary file with a guaranteed unique name. It 
then copies from the source to the temporary file and tries to rename the temp 
file to the ideal destination name. 
 - In default mode, if a file or directory already exists at the ideal 
   destination name, the temporary file is left in the destination directory, 
   so the backup exists even though it's not at the expected filename, and the 
   program exists with a nonzero code. 
 - In strict mode, the temporary file is removed and the program exists with a 
   nonzero code.
 - In overwrite mode, the existing file is overwritten with the copied file.
Overwrite mode conflicts with strict mode, so the two options cannot be used
simultaneously.""")
    _add_logging_options(parser)
    parser.add_option("-s", "--strict", action="store_true", 
            help="fail if file already exists at target pathname")
    parser.add_option("-d", "--dir", action="store", dest="destdir",
            help="set destination directory to DIRNAME", metavar="DIRNAME")
    parser.add_option("-w", "--overwrite", action="store_true",
            help="if file already exists at target pathname, overwrite it")
    parser.add_option("-f", "--config-file", metavar="PATHNAME", 
            help="use options defined in file at PATHNAME")
    parser.add_option("-S", "--no-stamp", action="store_false", dest="stamp",
            help="do not use a timestamp (requires -t)")
    parser.add_option("-t", "--tag", metavar="TAG", action="store",
            help="use TAG before timestamp (or in place of: see -S)")
    parser.add_option("-m", "--temp", action="store_true", 
            help="write backup file to temp directory")
    parser.add_option("-E", "--stacktraces", action="store_true", 
            dest="stacktraces", help="print stacktrace on exception")
    parser.add_option("-k", "--keep-extension", action="store_true",
            help="keep filename extension (insert suffix as infix)")
    # First pass parses command line, because some options may direct our 
    # search for other configuration files.
    cmdline_options, args = parser.parse_args(argv)
    if len(args) != 1: parser.error("source file argument required")
    # Now go through the real configuration stages
    stage_options = cmdline_options
    for stage in _CONFIG_STAGES:
        old_options = stage_options
        stage_options, args = _parse_config(stage, argv, parser, old_options, 
                cmdline_options, args)
        options = _override(old_options, stage_options)
    #print >> sys.stderr, "STDERR:backup: final options:", str(options)
    #~ print >> sys.stderr, "post-override options:", str(options)
    #~ _log.debug(" options: %s" % str(options))
    return parser, options, args

def _find_backup_conf(stage, parser, cmdline_options, src_pathname):
    """Get the pathname of the configuration file to use. Return None if 
    no configuration file is specified or present.
    
    The options argument must be the command line options, because those
    may direct how the configuration file is found. For example, if it's the
    directory stage, the command line options may specify what the name of
    the configuration file is. The options are not used for any other stage.
    """
    if stage == _STAGE_DIRECTORY:
        if cmdline_options.config_file is None:
            backup_conf_pathname = os.path.join(os.path.dirname(src_pathname), _BACKUP_CONF_FILENAME)
            if not os.path.isfile(backup_conf_pathname):
                backup_conf_pathname = None
        elif os.path.isdir(cmdline_options.config_file):
            backup_conf_pathname = os.path.join(cmdline_options.config_file, _BACKUP_CONF_FILENAME)
        elif os.path.isfile(cmdline_options.config_file):
            backup_conf_pathname = cmdline_options.config_file
        if cmdline_options.config_file is not None and backup_conf_pathname is None:
            parser.error("backup: configuration file specified but not present: %s" % backup_conf_pathname)
    elif stage == _STAGE_SITE:
        backup_conf_pathname = os.path.join(_SITE_CONFIG_DIR, _SITE_BACKUP_CONF_FILENAME)
    elif stage == _STAGE_USER:
        backup_conf_pathname = os.path.join(_USER_CONFIG_DIR, _USER_BACKUP_CONF_FILENAME)
    if backup_conf_pathname is not None and not os.path.isfile(backup_conf_pathname):
        backup_conf_pathname = None
    return backup_conf_pathname

def _parse_config_file(stage, parser, options, args, cfgfile_pathname):
    """Parse a configuration file. If a file exists at the specified pathname,
    then a new options object is returned. Otherwise, the same options object
    is returned.
    """
    if cfgfile_pathname is None:
        return options, args
    #print >> sys.stderr, ("STDERR:backup: parsing config file: %s" % cfgfile_pathname)
    if os.path.getsize(cfgfile_pathname) == 0: # empty file
        return options, args
    if stage == _STAGE_DIRECTORY:
        allargs = list()
        with open(cfgfile_pathname, 'r') as cfile:
            reader = csv.reader(cfile, delimiter=' ')
            for row in reader:
                allargs += row
        allargs += args
        options, args = parser.parse_args(allargs)
    else:
        raise NotImplementedError("parsing of site/user config files not yet implemented")
    # For all configuration files, the directory argument, if non-absolute, 
    # is relative to the source file's directory, not the current directory
    if options.dest_dir is not None and not os.path.isabs(options.dest_dir):
        options.dest_dir = os.path.join(os.path.dirname(args[0]), options.dest_dir)
    return options, args

def _parse_config(stage, argv, parser, options_base, cmdline_options, args):
    """Get the (options, args) tuple for a configuration stage. Either parse
        configuration file options or command line options. Assume the
        argument options object is the defaults that should be 
        overridden with new option values defined by this latest stage.
    """
    if stage not in _CONFIG_STAGES: 
        raise ValueError("invalid config stage: " + stage)
    src_pathname = args[0]
    # No need to re-parse the command line options here
    if stage == _STAGE_COMMAND:
        # cmdline_options, args = parser.parse_args(argv)
        return cmdline_options, args
    else:
        cfgfile_pathname = _find_backup_conf(stage, parser, cmdline_options, src_pathname)
        return _parse_config_file(stage, parser, options_base, args, cfgfile_pathname)

def _do_copy(src_pathname, dest_pathname, options):
    _log.debug(" ideal destination: " + dest_pathname)
    if options.strict and os.path.exists(dest_pathname):
        _log.error(" backup NOT created because file already exists: " + dest_pathname)
        sys.exit(ERR_FILE_ALREADY_EXISTS)
    #~ print >> sys.stderr, "destdir:", options.destdir
    #~ print >> sys.stderr, "dest_pathname:", dest_pathname
    dest_basename = os.path.basename(dest_pathname)
    fd, temp_pathname = tempfile.mkstemp(prefix=dest_basename, dir=options.destdir)
    _log.debug(" created temp file: " + temp_pathname)
    with os.fdopen(fd, 'wb') as ofile:
        with open(src_pathname, 'rb') as ifile:
            shutil.copyfileobj(ifile, ofile)
    shutil.copymode(src_pathname, temp_pathname)
    _log.debug(" source copied to temp file")
    if os.path.exists(dest_pathname):
        _log.debug(" file already exists at ideal target pathname")
        if options.strict:
            os.remove(temp_pathname)
            _log.error("backup NOT created because file already exists: " + dest_pathname)
            return ERR_FILE_ALREADY_EXISTS
        elif not options.overwrite:
            _log.info(" temp filename used for backup instead: " + temp_pathname)
            return ERR_TEMP_PATHNAME_USED
    os.rename(temp_pathname, dest_pathname)
    _log.debug(" renamed temp file: " + dest_pathname)
    return 0

def main():
    parser, options, args = _configure(sys.argv[1:])
    ret = ERR_UNDEFINED
    try:
        _config_logging(options)
        _check_options(parser, options)
        src_pathname = args[0]
        _check_src_pathname(src_pathname, parser)
        src_dirname, src_filename = os.path.split(src_pathname)
        dest_filename = _create_filename(options, src_filename)
        if options.destdir is None and not options.temp:
            options.destdir = src_dirname
        elif options.temp:
            options.destdir = tempfile.gettempdir()
        _log.debug(" using backup directory: %s" % options.destdir)
        dest_pathname = os.path.join(options.destdir, dest_filename)
        ret = _do_copy(src_pathname, dest_pathname, options)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if options.stacktraces:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        else:
            print(traceback.format_exc().splitlines()[-1], file=sys.stderr)
    return ret

