#!/usr/bin/env python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import os.path
import shutil
import logging
from time import strftime
_APT_CFG_DIRNAME = '/etc/apt'
_SLIST_FILENAME = 'sources.list'
_TIMESTAMP_FMT = "-%Y-%m-%d-%H%M%S"

_log = logging.getLogger("aptswitch")

#_ALLOWED_MODES = ('lenny', 'squeeze')

class AptSwitchError(Exception):
    pass

def _parse_args():
    from optparse import OptionParser
    usage="""
    %prog [options] [MODE]
Swaps the sources.list configuration file with sources.list-MODE after backing
up the current version. Options -r and -a revert to Lenny or advance to 
Squeeze, using the files sources.list-lenny and sources.list-squeeze which
must be created before using the script. An arbitrary mode file may be used by
specifying the MODE argument. For example, to switch to sources.list-special,
run 'aptswitch special'."""
    parser = OptionParser(usage=usage)
    parser.add_option("-u", "--update", 
            help="Post-swap, update the cached package lists to reflect the " + 
            " new configuration",
            action="store_true",
            dest="update")
    parser.add_option("-r", "--revert",
            help="Revert to Lenny (sets mode='lenny')",
            action="store_const",
            const="lenny",
            dest="mode")
    parser.add_option("-a", "--advance",
            help="Advance to Squeeze (sets mode='squeeze')",
            action="store_const",
            const="squeeze",
            dest="mode")
    parser.add_option("-L", "--level",
            help="set log level to one of DEBUG, INFO, WARNING, or ERROR",
            dest="log_level",
            action="store")
    parser.add_option("-d", "--dry-run",
            help="perform a dry run and don't move or copy anything",
            dest="dry_run",
            action="store_true")
    parser.set_defaults(update=False, log_level='INFO',
            dry_run=False)
    options, args = parser.parse_args()
##    options.mode = options.mode.lower()
##    if options.mode not in _ALLOWED_MODES:
##        raise AptSwitchError("mode '%s' must be one of %s" % (options.mode, 
##                str(_ALLOWED_MODES)))
    if options.mode is None:
        try:
##            print >> sys.stderr, "num args = ", len(args)
##            print >> sys.stderr, "args = ", str(args)
            options.mode = args[0].lower()
        except IndexError:
            parser.error('no mode option flagged or argument ' + 
                    ' specified; must use -r, -a, or a mode argument')
    return options, args

def get_sources_list_basename(version, slistname=_SLIST_FILENAME):
    return "%s-%s" % (slistname, version)

def backup_current(pathname=os.path.join(_APT_CFG_DIRNAME, _SLIST_FILENAME),
                    backupdir=None, stampfmt=_TIMESTAMP_FMT, dryrun=False):
    dir = backupdir or os.path.dirname(pathname)
    _log.debug(" backup directory: %s", dir)
    base = os.path.basename(pathname)
    newpath = os.path.join(dir, "%s%s" % (base, strftime(stampfmt)))
    if os.path.exists(newpath):
        _log.warn(" overwriting file %s" % newpath)
    _log.debug(" backing up by writing " + newpath)
    if dryrun:
        _log.debug(" would move %s to %s here", pathname, newpath)
    else:
        shutil.move(pathname, newpath)

def check_for_required_files(modes, aptcfgdir=_APT_CFG_DIRNAME, 
                            slistname=_SLIST_FILENAME,
                            haltonerror=True):
    _log.debug(" checking for required files corresponding to modes %s",
            str(modes))
    existing = [False] * len(modes)
    for i in xrange(len(modes)):
        mode = modes[i]
        base = get_sources_list_basename(mode, slistname)
        p = os.path.join(aptcfgdir, base)
        existing[i] = os.path.isfile(p)
        _log.debug(" --> %s exists? %s", p, existing[i])
    for i in xrange(len(existing)):
        ex = existing[i]
        if not ex:
            _log.warning(" sources.list for %s does not exist", modes[i])
            if haltonerror:
                raise AptSwitchError("sources.list for %s does not exist", modes[i])

def perform_swap(mode, aptcfgdir=_APT_CFG_DIRNAME, slistname=_SLIST_FILENAME,
                dryrun=False):
    backup_current(pathname=os.path.join(aptcfgdir, slistname), dryrun=dryrun)
    newslistbase = get_sources_list_basename(mode, slistname)
    newslistpath = os.path.join(aptcfgdir, newslistbase)
    slistpath = os.path.join(aptcfgdir, slistname)
    _log.debug(" copying %s to %s", newslistpath, slistpath)
    if dryrun:
        _log.debug(" would copy %s to %s here", newslistpath, slistpath)
    else:
        shutil.copy(newslistpath, slistpath)
    _log.debug(" swap operation complete")

def apt_update(dryrun=False):
    from subprocess import check_call
    _log.debug(" updating package lists...")
    if dryrun:
        _log.debug(" would execute apt-get update here")
    else: check_call(["apt-get", "update"])
    _log.debug(" package list update complete")

if __name__ == '__main__':
    options, args = _parse_args()
    log_level = eval('logging.' + options.log_level)
    logging.basicConfig(level=log_level)
    _log.debug(" options: %s", str(options))
    # sort of deprecated usage here...the check function checks for files
    # corresponding to a sequence of modes, but there's only one to check
    # for ever
    check_for_required_files(modes=(options.mode,))
    perform_swap(options.mode, dryrun=options.dry_run)
    if options.update: apt_update(dryrun=options.dry_run)
