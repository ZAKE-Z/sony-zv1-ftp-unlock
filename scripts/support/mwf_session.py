"""Pull ZV-1 libMWF.so + read live inhibit-engine state from im.elf memory."""
from pathlib import Path
import contextlib
import datetime
import hashlib
import json
import re
import secrets
import sys
import diagnose as d
from ram_probe import Terminal, PARENT_GUARD, owned_guard, cleanup_command, TOOL_CHECK
from senser_readonly import file_read_receiver

ROOT = Path(__file__).resolve().parent
HELPER = 'menu_probe.elf'
META = json.loads((ROOT / 'native' / 'menu_manifest.json').read_text(encoding='utf-8'))['helper']

# libMWF a7C dynsym offsets (vaddr==fileoff for these .bss/.data symbols; bss is beyond
# file so use runtime map math). We read via maps of /usr/lib/libMWF.so.
GLOBAL_SYMS = {  # name: vaddr (from a7C dynsym; ZV-1 may differ slightly, printed for info)
    'mp_inhMgrInsList': 0x442c8,
    'mp_inhTbl': 0x442d0,
    'mp_featChgTbl': 0x442dc,
    'InhMcmd::m_cmdSubTableInh': 0x4402c,
}


@contextlib.contextmanager
def bounded_reads(driver):
    original = driver.read
    def read(length, ep=0, timeout=None):
        return original(length, ep=ep, timeout=60000 if timeout is None else timeout)
    driver.read = read
    try:
        yield
    finally:
        driver.read = original


def stage_helper(cam, term):
    token = secrets.token_hex(6)
    path = '/tmp_bt/.zv1_mwf_' + token
    source = 'zv1mwf_' + token
    term.run(owned_guard(path, source))
    term.run('zp_parent && (umask 077; mkdir ' + path + ')')
    term.run('zp_parent && mount -n -t tmpfs -o size=1024k,mode=0700,nosuid,nodev ' + source + ' ' + path)
    helper = (ROOT / 'native' / HELPER).read_bytes()
    assert len(helper) == META['bytes'] and hashlib.sha256(helper).hexdigest() == META['sha256']
    remote = path + '/' + HELPER
    cam.writeFile(remote, helper)
    term.run('zp_parent && zp_owned && chmod 700 ' + remote)
    return path, remote


def read_mem(term, helper_path, pid, addr, length):
    code, out = term.run('zp_parent && (ulimit -c 0; ' + helper_path + ' %d %x %x)' %
                         (pid, addr, length), check=False, timeout=120)
    for line in out.splitlines():
        m = re.fullmatch(r'MEMHEX ([0-9a-f]+) ([0-9a-f]+)', line)
        if m:
            return bytes.fromhex(m.group(2))
    raise RuntimeError('no MEMHEX (out: %r)' % out[:300])


def main():
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    folder = ROOT / 'snapshots' / ('zv1-mwf-' + stamp)
    folder.mkdir(parents=True, exist_ok=False)
    out, err = sys.stdout, sys.stderr
    result = 0
    with (folder / 'session.txt').open('w', encoding='utf-8') as log:
        sys.stdout, sys.stderr = d.Tee(out, log), d.Tee(err, log)
        try:
            with d.service_camera() as (cam, senser), d.terminal(cam):
                d.direct_read(senser, seconds=1)
                with bounded_reads(senser.driver):
                    term = Terminal(senser)
                    term.run('PATH=/bin:/sbin:/usr/bin:/usr/sbin:$PATH; export PATH')
                    term.run(TOOL_CHECK)
                    term.run(PARENT_GUARD)
                    term.run('zp_parent')

                    # 1) pull libMWF.so
                    record = {}
                    with file_read_receiver(cam, record, 2 * 1024 * 1024):
                        data = cam.readFile('/usr/lib/libMWF.so')
                    (folder / 'libMWF.so').write_bytes(data)
                    print('[PULLED] libMWF.so %d bytes' % len(data))

                    # 2) live engine state in im.elf
                    code, mp = term.run('for zm_p in /proc/[0-9]*; do if [ -r "$zm_p/comm" ]; then '
                                        'read zm_name < "$zm_p/comm"; '
                                        'if [ "$zm_name" = im.elf ]; then printf "MAIN %s\\n" "$zm_p"; fi; fi; done',
                                        check=False, timeout=30)
                    pid = int(re.findall(r'MAIN /proc/([0-9]+)', mp, re.M)[0])
                    code, maps = term.run('/bin/busybox grep libMWF /proc/%d/maps' % pid, check=False, timeout=20)
                    print(maps)
                    (folder / 'maps-mwf.txt').write_text(maps, encoding='utf-8')
                    lines = [l.split() for l in maps.splitlines() if len(l.split()) >= 6]
                    base = None
                    for p in lines:
                        if p[2] == '00000000' and p[1].startswith('r'):
                            base = int(p[0].split('-')[0], 16)
                    print('libMWF base: %s' % hex(base) if base else 'libMWF base: None')
                    if base is None:
                        raise RuntimeError('libMWF not mapped in im.elf')

                    path, remote = stage_helper(cam, term)
                    try:
                        import struct
                        # read the globals block 0x44000..0x44400 (contains all syms)
                        blob = read_mem(term, remote, pid, base + 0x44000, 0x400)
                        (folder / 'mwf_globals.bin').write_bytes(blob)
                        for name, off in GLOBAL_SYMS.items():
                            v = struct.unpack_from('<I', blob, off - 0x44000)[0]
                            print('live %-24s = %#010x' % (name, v))
                        ptbl = struct.unpack_from('<I', blob, 0x442d0 - 0x44000)[0]
                        if 0x1000 < ptbl < 0xffffffff:
                            obj = read_mem(term, remote, pid, ptbl, 0x40)
                            (folder / 'inhtbl_obj.bin').write_bytes(obj)
                            print('InhTbl object @%#x words: %s' % (ptbl, [hex(v) for v in struct.unpack('<16I', obj)]))
                        pmgr = struct.unpack_from('<I', blob, 0x442c8 - 0x44000)[0]
                        if 0x1000 < pmgr < 0xffffffff:
                            obj = read_mem(term, remote, pid, pmgr, 0x80)
                            (folder / 'inhmgr_obj.bin').write_bytes(obj)
                            print('InhMgr object @%#x words: %s' % (pmgr, [hex(v) for v in struct.unpack('<32I', obj)]))
                    finally:
                        term.run(cleanup_command(path), check=False)
        except Exception:
            import traceback
            traceback.print_exc()
            d.failure()
            result = 1
        finally:
            sys.stdout, sys.stderr = out, err
    print('folder: %s' % folder)
    return result


if __name__ == '__main__':
    sys.exit(main())
