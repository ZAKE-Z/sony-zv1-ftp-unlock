"""ZV-1: bounded tmpfs mount and independent ARM execution, direct USB."""
from pathlib import Path
import datetime
import hashlib
import re
import secrets
import sys
import time
import diagnose as d
from build_arm_probe import build, MESSAGE

ROOT = Path(__file__).resolve().parent
VERSION = '1.1'

# Sony's ash build omits the `command` builtin. Search executable files directly.
TOOL_CHECK = ('(zp_missing=0; for zp_tool in mount umount mkdir rmdir chmod cat; do '
              'zp_found=0; for zp_dir in /bin /sbin /usr/bin /usr/sbin; do '
              'if [ -f "$zp_dir/$zp_tool" ] && [ -x "$zp_dir/$zp_tool" ]; then '
              'printf "TOOL %s=%s/%s\\n" "$zp_tool" "$zp_dir" "$zp_tool"; '
              'zp_found=1; break; fi; done; '
              'case "$zp_found" in 0) printf "MISSING %s\\n" "$zp_tool"; zp_missing=1;; esac; '
              'done; exit "$zp_missing")')


class Terminal:
    def __init__(self, senser):
        self.senser = senser
        self.serial = 0

    def run(self, command, *, check=True, timeout=15):
        self.serial += 1
        tag = '__ZVR_%03d_%s__' % (self.serial, secrets.token_hex(3))
        wire = "printf '\\n" + tag + "_BEGIN\\n'; " + command
        wire += "; zp_rc=$?; printf '\\n" + tag + "_END:%s\\n' \"$zp_rc\"\n"
        print('\n[TX] ' + command, flush=True)
        d.stage('ram.usb.write')
        self.senser.writeTerminal(wire.encode('ascii'))
        d.stage('ram.usb.read')
        data = bytearray()
        start = ('\n' + tag + '_BEGIN\n').encode()
        end = re.compile(rb'\n' + tag.encode() + rb'_END:([0-9]+)\n')
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = d.read_usb(self.senser)
            if not chunk:
                continue
            data.extend(chunk)
            print(chunk.decode('utf-8', 'replace'), end='', flush=True)
            if len(data) > 262144:
                raise RuntimeError('Output limit; batch stopped.')
            clean = bytes(data).replace(b'\r', b'')
            begin = clean.find(start)
            if begin < 0:
                continue
            match = end.search(clean, begin + len(start))
            if match:
                status = int(match.group(1))
                output = clean[begin + len(start):match.start()].decode('utf-8', 'replace')
                print('\n[COMMAND EXIT] %d' % status)
                if check and status:
                    raise RuntimeError('Command returned %d; see output above.' % status)
                return status, output
        raise TimeoutError('USB command completion missing; no further test writes will be sent.')


PARENT_GUARD = "zp_parent() { [ -d /tmp_bt ] && [ ! -L /tmp_bt ] || return 1; while read -r zs zm zf zo zz; do if [ \"$zm\" = /tmp_bt ]; then [ \"$zf\" = tmpfs ] || return 1; case \",$zo,\" in *,rw,*) return 0;; *) return 1;; esac; fi; done < /proc/mounts; return 1; }"


def owned_guard(path, source):
    return ('zp_owned() { [ -d ' + path + ' ] && [ ! -L ' + path + ' ] || return 1; '
            'while read -r zs zm zf zo zz; do if [ "$zm" = ' + path + ' ]; then '
            '[ "$zs" = ' + source + ' ] && [ "$zf" = tmpfs ]; return $?; '
            'fi; done < /proc/mounts; return 1; }')


def cleanup_command(path):
    # No forced/lazy unmount; rmdir cannot remove nonempty directories.
    return ('if zp_parent; then if zp_owned; then umount -n ' + path + '; zp_u=$?; '
            'else zp_u=0; fi; if [ "$zp_u" = 0 ]; then rmdir ' + path + '; '
            'else false; fi; else false; fi')


def exercise(cam, senser):
    terminal = Terminal(senser)
    terminal.run('cat /proc/self/status')
    terminal.run('cat /proc/mounts')
    terminal.run('PATH=/bin:/sbin:/usr/bin:/usr/sbin:$PATH; export PATH')
    status, _ = terminal.run(TOOL_CHECK, check=False)
    if status:
        terminal.run('ls -l /bin /sbin /usr/bin /usr/sbin', check=False)
        raise RuntimeError('Required executable missing or file tests unavailable; directory inventory recorded. No RAM objects created.')
    # Check other required shell features before the first camera-side write.
    terminal.run('(umask 077 && ulimit -c 0 && read -r zp_s zp_m zp_f zp_o zp_z < /proc/mounts && [ -n "$zp_f" ])')
    terminal.run(PARENT_GUARD)
    terminal.run('zp_parent')
    # Refuse symlinks/non-RAM parents, use a never-reused private child directory.
    token = secrets.token_hex(6)
    path = '/tmp_bt/.zv1_ram_' + token
    source = 'zv1probe_' + token
    remote = path + '/probe.elf'
    terminal.run(owned_guard(path, source))
    made = False
    try:
        terminal.run('zp_parent && (umask 077; mkdir ' + path + ')')
        made = True
        terminal.run('zp_parent && mount -n -t tmpfs -o size=512k,mode=0700,nosuid,nodev ' + source + ' ' + path)
        terminal.run('zp_parent && zp_owned && cat /proc/mounts')
        payload = build()
        octal = ''.join('\\%03o' % b for b in payload)
        # Guard and write are in the same shell command. No writes to /tmp or /etc.
        terminal.run("zp_parent && zp_owned && printf '" + octal + "' > " + remote)
        terminal.run('zp_parent && zp_owned')
        d.stage('ram.verify.readback')
        actual = cam.readFile(remote)
        if actual != payload:
            raise RuntimeError('RAM payload readback mismatch; execution refused.')
        print('[PASS] RAM payload readback SHA256=' + hashlib.sha256(actual).hexdigest())
        terminal.run('zp_parent && zp_owned && chmod 700 ' + remote)
        status, output = terminal.run('zp_parent && zp_owned && (ulimit -c 0 && ' + remote + ')')
        if MESSAGE.decode().strip() not in output.splitlines():
            raise RuntimeError('ARM program returned without the expected output.')
        print('[PASS] Independent ARM ELF executed from the private RAM mount.')
        print('[INFO] This does not establish Sony FTP ABI or dynamic-library compatibility.')
        terminal.run('(ulimit -c 0 && /lib/ld-linux.so.3 --list /bin/cat)', check=False)
    finally:
        if made:
            print('\n[CLEANUP] Removing only this run\'s private RAM mount and directory.')
            try:
                terminal.run(cleanup_command(path))
                terminal.run('zp_parent && [ ! -e ' + path + ' ]')
                print('[PASS] Private RAM mount unmounted and directory removed.')
            except BaseException:
                print('[CLEANUP INCOMPLETE] Stop the test and restart the camera normally.')
                print('Private RAM test path: ' + path)
                raise


def main():
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    filename = logs / ('ramtest-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.txt')
    stdout, stderr = sys.stdout, sys.stderr
    result = 0
    with filename.open('w', encoding='utf-8') as log:
        sys.stdout, sys.stderr = d.Tee(stdout, log), d.Tee(stderr, log)
        try:
            print('ZV-1 RAM Execution Probe ' + VERSION + ' | ' + datetime.datetime.now().isoformat())
            print('Creates a private tmpfs (512 KiB limit) under verified /tmp_bt tmpfs.')
            print('Uploads a tiny ARM program which only writes a stdout marker and exits.')
            print('No FTP/Sony modules loaded; no firmware, menu or backup-setting edits.')
            with d.service_camera() as (cam, senser):
                with d.terminal(cam):
                    d.direct_read(senser, seconds=1)
                    exercise(cam, senser)
            print('\n[DONE] RAM execution and cleanup completed.')
        except KeyboardInterrupt:
            print('\nInterrupted; see cleanup status above.')
            result = 130
        except Exception:
            d.failure()
            result = 1
        finally:
            print('\nLOG FILE: ' + str(filename))
            sys.stdout, sys.stderr = stdout, stderr
    return result


if __name__ == '__main__':
    sys.exit(main())
