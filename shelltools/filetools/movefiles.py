#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import sys
import os
import stat
import logging
import shutil

LOG_FILENAME = '/tmp/py-movefiles.log'

MOVEMODE_MOVE = 0
MOVEMODE_RENAME = 1
MOVEMODE_COPYRM = 2
MOVEMODE_COPY_ONLY = 3
MOVEMODES = {'move': MOVEMODE_MOVE, 
            'rename': MOVEMODE_RENAME, 
            'copyrm': MOVEMODE_COPYRM, 
            'copy_only': MOVEMODE_COPY_ONLY}
#[MOVEMODE_MOVE, MOVEMODE_RENAME, MOVEMODE_COPYRM, MOVEMODE_COPY_ONLY]

ERR_MSG_DIRNAME_IS_EXISTING_FILE = 'invalid destination directory -- ' + \
                                'pathname exists and is file: '
ERR_MSG_INVALID_MOVE_MODE = "invalid move mode"

def action_log_msg(dry_run, mode, src, dst):
    if dry_run:
        action = 'simulating'
    else:
        action = 'performing' 
    #return '{0} {1} {2} to {3}'.format(action, mode, src, dst)
    return '%s %s %s to %s' % (action, mode, src, dst)

def validate_dirname(new_dirname, verbose=False, dry_run=False):
    logging.debug("validating dirname %s (verbose=%s, dry_run=%s)",
                    new_dirname, verbose, dry_run)
    if os.path.exists(new_dirname):
        if os.path.isdir(new_dirname):
            pass
        else:
            logging.info(ERR_MSG_DIRNAME_IS_EXISTING_FILE + new_dirname)
            print >> failuresfile, old_pathname
            if quiet == False:
                print >> sys.stderr, ERR_MSG_DIRNAME_IS_EXISTING_FILE
    else:
        logging.debug("%s does not exist; creating", new_dirname)
        if verbose:
            print 'mkdir -p %s' % new_dirname
        if dry_run == False:
            os.makedirs(new_dirname)

def get_action_items(dupepathnames, newroot, movemode, 
                verbose=False, quiet=False, failuresfile=sys.stderr, 
                dry_run=False):
    logging.debug("getting action items; args:\n\tnum dupepathnames=%d\n\tnewroot=%s"+
                    "movemode=%s\n\tverbose=%s\n\tquiet=%s"+
                    "\n\tfailuresfile=%s\n\tdry_run=%s", 
                    len(dupepathnames), newroot, movemode, 
                    verbose, quiet, failuresfile, dry_run)
    action_items = []
    for old_pathname in dupepathnames:
        new_pathname = os.path.normpath(newroot + os.sep + old_pathname)
        new_dirname = os.path.dirname(new_pathname)
        validate_dirname(new_dirname, verbose, dry_run)
        assert os.path.isdir(new_dirname) or dry_run

        # stat to get devices -- rename can only work on same filesystem
        old_dev = os.stat(old_pathname)[stat.ST_DEV]
        # must stat dirname b/c file does not exist yet
        new_dev = os.stat(new_dirname)[stat.ST_DEV]
        logging.debug("[dev=%s] %s, [dev=%s] %s", 
                    old_dev, old_pathname, new_dev, new_pathname)
        same_device = old_dev == new_dev
        itemmode = movemode
        """ batch 'move' mode determines whether rename is possible 
            (when both pathnames are on same device) or 
            copy-and-remove is necessary (pathnames are cross-device)
            
            in batch 'rename' mode, same determination is made but
            action is skipped if it would be a cross-device rename
        """
        if itemmode == MOVEMODES['move']:
            if same_device:
                itemmode = MOVEMODES['rename']
            else:
                itemmode = MOVEMODES['copyrm']
        action_item = (old_pathname, new_pathname, itemmode)
        
        # can't act if mode='rename' but files not on same device
        if ( (itemmode == MOVEMODES['rename'] 
                and same_device == False) == False): 
            # src first, dst second, mode third
            action_items.append( action_item )
        else:
            # note that new directory may have been created
            logging.info("action item rejected b/c cross-device: %s",
                        action_item)
    return action_items

def move_files(dupepathnames, newroot=os.getcwd(), movemode=MOVEMODES['move'], 
                verbose=False, quiet=False, failuresfile=sys.stderr, 
                dry_run=False):
    logging.debug('request: %s dupes to %s in mode %s' % \
            (len(dupepathnames), newroot, str(movemode)))
    assert (movemode in MOVEMODES.values()), ERR_MSG_INVALID_MOVE_MODE 
    assert (dupepathnames is not None), "dupepathnames must be a list"
    action_items = get_action_items(dupepathnames, newroot, movemode,
                                    verbose, quiet, failuresfile, dry_run)
    
    logging.debug('got %d action items from list of %d dupes', 
                    len(action_items), len(dupepathnames))
    
    for item in action_items:
        src, dst, mode = item
        logging.debug(action_log_msg(dry_run, mode, src, dst))
        if mode == MOVEMODES['rename']:
            if verbose:
                print 'mv %s %s' % (src, dst)
            if dry_run == False:
                os.rename(src, dst)
                logging.debug('rename successful')
        elif mode == MOVEMODES['copyrm'] or mode == MOVEMODES['copy_only']:
            if verbose:
                print 'cp -p %s %s' % (src, dst)
            if dry_run == False:
                shutil.copy2(src, dst)
                logging.debug('copy successful')
            if mode == 'copyrm':
                if verbose:
                    print 'rm %s' % src
                if dry_run == False:
                    # will remove file, but not directory even if it's empty
                    os.remove(src)
                    logging.debug('removal successful')
        else:
            assert False, "bug: item mode %s must be in %s" % \
                            (mode, MOVEMODES.values())


def parse_args():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", 
                        dest="dupesfile_pathname", metavar="PATHNAME")
    parser.add_option("-v", "--verbose", 
                        dest="verbose", action="store_true")
    parser.add_option("-d", "--dest", 
                        dest="dest_dirname", metavar="DIRNAME")
    parser.add_option("-e", "--errors", 
                        dest="errors_file_pathname", metavar="PATHNAME")
    parser.add_option("-q", "--quiet", 
                        dest="quiet", action="store_true")
    parser.add_option("-s", "--dry-run", 
                        dest="dry_run", action="store_true")
    parser.add_option("-c", "--copyrm", action="store_const",
                        dest="movemode", const=MOVEMODES['copyrm'])
    parser.add_option("-C", "--copy-only", action="store_const",
                        dest="movemode", const=MOVEMODES['copy_only'])
    parser.add_option("-n", "--rename", action="store_const",
                        dest="movemode", const=MOVEMODES['rename'])
    
    parser.set_defaults(movemode=MOVEMODES['move'], dry_run=False,
                        quiet=False, verbose=False, dest_dirname=os.getcwd())
    (options, args) = parser.parse_args()
    if len(args) > 1:
        parser.error("only one argument max (destination DIRNAME)")
    # override option with positional argument
    if len(args) == 1:
        options.dest_dirname = args[0]

    return options, args

if __name__ == '__main__':
    logging.basicConfig(filename=LOG_FILENAME,
                        filemode='w',
                        level=logging.DEBUG,)
    
    options, args = parse_args()
    logging.debug("parsed options: %s\n\targs: %s", options, args)
    if options.dupesfile_pathname is not None:
        dupesfile = open(options.dupesfile_pathname, 'r')
    else:
        dupesfile = sys.stdin
    
    dupepathnames = []
    for line in dupesfile:
		dupepathnames.append(os.path.normpath(line.strip()))
    if dupesfile != sys.stdin:
        dupesfile.close()

    # directing failures to file not implemented yet
    move_files(dupepathnames, options.dest_dirname, movemode=options.movemode,
                verbose=options.verbose, 
                dry_run=options.dry_run, 
                quiet=options.quiet)
