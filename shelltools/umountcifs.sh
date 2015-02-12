#! /bin/sh
### BEGIN INIT INFO
# Provides:          umountcifs
# Required-Start:
# Required-Stop:     umountcifs
# Should-Stop:
# Default-Start:
# Default-Stop:      0 6
# Short-Description: Unmount all cifs filesystems and terminate all processes using them
# Description:       
### END INIT INFO

# http://www.jejik.com/articles/2007/07/automatically_mounting_and_unmounting_samba_windows_shares_with_cifs/
# LICENSE: http://creativecommons.org/licenses/by-sa/3.0/

PATH=/sbin:/usr/sbin:/bin:/usr/bin
KERNEL="$(uname -s)"
RELEASE="$(uname -r)"
. /lib/init/vars.sh

. /lib/lsb/init-functions

case "${KERNEL}:${RELEASE}" in
  Linux:[01].*|Linux:2.[01].*)
        FLAGS=""
        ;;
  Linux:2.[23].*|Linux:2.4.?|Linux:2.4.?-*|Linux:2.4.10|Linux:2.4.10-*)
        FLAGS="-f"
        ;;
  *)
        FLAGS="-f -l"
        ;;
esac

do_stop () {
        #
        # Make list of points to unmount in reverse order of their creation
        #

        exec 9<&0 </etc/mtab

        DIRS=""
        while read DEV MTPT FSTYPE OPTS REST
        do
                case "$MTPT" in
                  /|/proc|/dev|/dev/pts|/dev/shm|/proc/*|/sys|/lib/init/rw)
                        continue
                        ;;
                  /var/run)
                        if [ yes = "$RAMRUN" ] ; then
                                continue
                        fi
                        ;;
                  /var/lock)
                        if [ yes = "$RAMLOCK" ] ; then
                                continue
                        fi
                        ;;
                esac
                case "$FSTYPE" in
                  cifs)
                        DIRS="$MTPT $DIRS"
                        ;;
                esac
        done

        exec 0<&9 9<&-

        if [ "$DIRS" ]
        then
		# Kill all processes using the cifs volumes
		PROCESSES=""
		for DIR in $DIRS; do
			PROCESS=`fuser -m $DIR`
			if [ "$PROCESS" ]; then
				PROCESSES="$PROCESS $PROCESSES"
			fi
		done

		if [ "$PROCESSES" ]
		then
			log_action_begin_msg "Asking all processes using cifs filesystems to terminate"
			echo "kill -15 $PROCESSES"
			log_action_end_msg 0

			for seq in 1 2 3 4 5 ; do
	                	# use SIGCONT/signal 18 to check if there are
	                	# processes left.  No need to check the exit code
	                	# value, because either killall5 work and it make
	                	# sense to wait for processes to die, or it fail and
	                	# there is nothing to wait for.
	                	echo "kill -18 $PROCESSES > /dev/null 2>&1" || break

	                	sleep 1
	        	done
		        log_action_begin_msg "Killing all remaining processes using cifs filesystems"
		        echo "kill -9 $PROCESSES > /dev/null 2>&1" # SIGKILL
		        log_action_end_msg 0
		fi
		# Unmount all cifs filesystems
	        [ "$VERBOSE" = no ] || log_action_begin_msg "Unmounting remote and non-toplevel cifs filesystems"
	        umount $FLAGS $DIRS
	        ES=$?
	        [ "$VERBOSE" = no ] || log_action_end_msg $ES
        fi
}

case "$1" in
  start)
        # No-op
        ;;
  restart|reload|force-reload)
        echo "Error: argument '$1' not supported" >&2
        exit 3
        ;;
  stop|"")
        do_stop
        ;;
  *)
        echo "Usage: umountcifs [start|stop]" >&2
        exit 3
        ;;
esac

:
