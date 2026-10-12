"""ZV-1 FTP firmware patcher and shared nine-slot configuration primitives."""
from ui_language import print,tr,announce
from pathlib import Path
import argparse, datetime, hashlib, json, re, sys, time, secrets
ROOT = Path(__file__).resolve().parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()

def select(catalog, actual):
    selected = []
    for target in sorted({v['target'] for v in catalog['variants']}):
        variants = [v for v in catalog['variants'] if v['target'] == target]
        if actual[target] == variants[0]['candidate_md5']:
            continue
        choices = [v for v in variants if actual[target] == v['original_md5']]
        if len(choices) != 1:
            raise RuntimeError('Unknown camera file: ' + target + '; no write allowed')
        selected.append(choices[0])
    return selected

def validate(catalog):
    assert catalog['firmware_stage_configuration_writes'] is False
    assert catalog['server_credentials_included'] is False
    for v in catalog['variants']:
        b = (ROOT/'assets'/v['writer']).read_bytes()
        assert sha(b) == v['writer_sha256']
    for name, info in catalog['libraries'].items():
        b = (ROOT/'assets'/name).read_bytes()
        assert len(b) == info['bytes'] and sha(b) == info['sha256']

def run(args):
    catalog = json.loads((ROOT/'resources/catalog.json').read_text(encoding='utf-8'))
    if not getattr(args, 'skip_local_assets', False):
        validate(catalog)
    sys.path.insert(0, args.runtime_root)
    import diagnose as d
    import mwf_session as m
    from ram_probe import Terminal, PARENT_GUARD, cleanup_command, owned_guard
    from senser_readonly import file_read_receiver
    folder = ROOT/'logs'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    folder.mkdir(parents=True)
    announce('camera')
    report = {'status':'STARTED', 'settings_written':False, 'new_libraries':[], 'patched':[]}
    def save():
        (folder/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    def digest(t, path):
        for _ in range(3):
            _, out = t.run('/bin/busybox md5sum '+path, timeout=60)
            hit = re.search(r'\b([0-9a-f]{32})\s+'+re.escape(path), out)
            if hit: return hit[1]
        raise RuntimeError('Missing checksum: '+path)
    def readonly(t):
        for _ in range(3):
            _, out = t.run('/bin/busybox cat /proc/mounts')
            rows = [x.split() for x in out.splitlines() if len(x.split())>3 and x.split()[1]=='/usr']
            if len(rows)==1: return 'ro' in rows[0][3].split(',')
        raise RuntimeError('Missing mount state')
    changed = False
    save()
    try:
        with (folder/'session.private.log').open('w',encoding='utf-8') as log:
            original_out, original_err = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = log
            try:
                with d.service_camera() as (cam, senser), d.terminal(cam):
                    d.direct_read(senser, seconds=1)
                    with m.bounded_reads(senser.driver):
                        t = Terminal(senser)
                        _, version = t.run('/bin/busybox cat /version.txt')
                        assert version.strip() == catalog['firmware'], 'Firmware mismatch'
                        assert readonly(t), '/usr must initially be read-only'
                        assert digest(t,'/usr/lib/libSysDef.so') == catalog['native_sysdef_md5'], 'Unexpected inhibit table'
                        actual = {target:digest(t,target) for target in sorted({v['target'] for v in catalog['variants']})}
                        selected = select(catalog,actual)
                        missing = []
                        for name, info in catalog['libraries'].items():
                            path = '/usr/lib/'+name
                            _, out = t.run('if [ -e '+path+' ]; then echo PRESENT; else echo ABSENT; fi')
                            if 'PRESENT' in out:
                                assert digest(t,path)==info['md5'], 'Unknown dependency: '+name
                            elif 'ABSENT' in out: missing.append(name)
                            else: raise RuntimeError('Missing existence response')
                        report.update(source_hashes=actual, selected=[v['name'] for v in selected], missing_libraries=missing)
                        save()
                        if args.verify:
                            assert not selected and not missing, 'Installation incomplete'
                        if args.check:
                            report['status']='PASS_PREFLIGHT_NO_WRITES'; save(); return False
                        # Read selected properties only; never serialize credentials.
                        keys=(0x1070316,0x19e000d,0x1071923,0x1071cd6,0x1ac0094,0x1ac0095,0x1ac0096,0x1ac0098)
                        protected={k:cam.readBackup(k) for k in keys}
                        # Fresh official firmware need not mount the former /tmp_bt.
                        # Only an owned, verified tmpfs holds uploaded assets.
                        t.run('zp_parent() { [ -d /tmp ] && [ ! -L /tmp ]; }')
                        t.run('zp_parent')
                        token=secrets.token_hex(6);stage='/tmp/.zv1ftp_'+token;source='zv1ftp_'+token
                        t.run(owned_guard(stage,source))
                        t.run('zp_parent && (umask 077; mkdir '+stage+')')
                        t.run('zp_parent && mount -n -t tmpfs -o size=1024k,mode=0700,nosuid,nodev '+source+' '+stage)
                        t.run('zp_parent && zp_owned')
                        helper=stage+'/menu_probe.elf';probe=(Path(args.runtime_root)/'native/menu_probe.elf').read_bytes()
                        assert len(probe)==m.META['bytes'] and sha(probe)==m.META['sha256']
                        cam.writeFile(helper,probe)
                        with file_read_receiver(cam,{},len(probe)+1024):assert cam.readFile(helper)==probe
                        t.run('zp_parent && zp_owned && chmod 700 '+helper)
                        try:
                            remotes=[]
                            for v in selected:
                                path=v['target']; name=Path(path).name
                                with file_read_receiver(cam,{},64*1024*1024): data=cam.readFile(path)
                                assert sha(data)==v['original_sha256'], 'Full source checksum mismatch'
                                (folder/(name+'.before.so')).write_bytes(data)
                                remote=stage+'/'+v['writer']; data=(ROOT/'assets'/v['writer']).read_bytes()
                                cam.writeFile(remote,data)
                                with file_read_receiver(cam,{},len(data)+1024): assert cam.readFile(remote)==data
                                t.run('zp_parent && zp_owned && chmod 700 '+remote)
                                _, out=t.run(remote+' '+path+' check'); assert 'LIFE_CHECK_OK' in out
                                remotes.append((remote,v))
                            for name in missing:
                                data=(ROOT/'assets'/name).read_bytes(); remote=stage+'/'+name
                                cam.writeFile(remote,data)
                                with file_read_receiver(cam,{},len(data)+1024): assert cam.readFile(remote)==data
                            applied=[]; added=[]
                            if selected or missing:
                                t.run('/bin/busybox mount -o remount,rw /usr'); assert not readonly(t)
                                announce('write')
                                report['status']='WRITING';save()
                                try:
                                    for name in missing:
                                        path='/usr/lib/'+name; temp='/usr/lib/.zv1ftp_'+Path(stage).name+'_'+name
                                        t.run('[ ! -e '+path+' ] && /bin/busybox cp '+stage+'/'+name+' '+temp)
                                        assert digest(t,temp)==catalog['libraries'][name]['md5']
                                        t.run('/bin/busybox chmod 555 '+temp)
                                        t.run('/bin/busybox ln '+temp+' '+path)
                                        added.append(name);report['new_libraries']=added[:];save()
                                        t.run('/bin/busybox rm '+temp)
                                    for remote,v in remotes:
                                        applied.append((remote,v))
                                        _,out=t.run(remote+' '+v['target']+' apply');assert 'LIFE_APPLIED' in out
                                        assert digest(t,v['target'])==v['candidate_md5']
                                        report['patched'].append(v['name']);save()
                                    assert all(cam.readBackup(k)==b for k,b in protected.items()), 'Settings changed'
                                    changed=True
                                except Exception as error:
                                    # A lost USB channel cannot safely execute rollback commands.
                                    if 'USB' in type(error).__name__ or 'Timeout' in type(error).__name__:
                                        report['status']='INTERRUPTED_REQUIRES_INSPECTION';save();raise
                                    for remote,v in reversed(applied):
                                        _,out=t.run(remote+' '+v['target']+' restore');assert 'LIFE_RESTORED' in out
                                        assert digest(t,v['target'])==v['original_md5']
                                    for name in added:t.run('/bin/busybox rm /usr/lib/'+name)
                                    report['status']='FAILED_ROLLED_BACK';save();raise
                                finally:
                                    t.run('/bin/busybox sync',check=False)
                                    t.run('/bin/busybox mount -o remount,ro /usr',check=False)
                            assert readonly(t)
                            for v in catalog['variants']:assert digest(t,v['target'])==v['candidate_md5']
                            for name,info in catalog['libraries'].items():assert digest(t,'/usr/lib/'+name)==info['md5']
                            if args.verify or not changed:
                                _,out=t.run('for p in /proc/[0-9]*; do if [ -r "$p/comm" ]; then read n < "$p/comm"; if [ "$n" = im.elf ]; then echo MAIN=$p; fi; fi; done')
                                pid=int(re.search(r'MAIN=/proc/(\d+)',out)[1])
                                _,maps=t.run('/bin/busybox cat /proc/%d/maps'%pid)
                                for v in {x['target']:x for x in catalog['variants'] if x['name'].endswith('_native')}.values():
                                    matches=[x for x in maps.splitlines() if x.split()[-1]==v['target'] and x.split()[2]=='00000000']
                                    if not matches:
                                        if v['target']!='/usr/lib/viewUnified4.so':raise RuntimeError('Expected module missing: '+v['target'])
                                        report.setdefault('unloaded_modules',[]).append(v['target'])
                                        continue
                                    base=int(matches[0].split()[0].split('-')[0],16)
                                    for patch in v['patches']:
                                        expected=bytes.fromhex(patch['new'])
                                        assert m.read_mem(t,helper,pid,base+int(patch['offset'],16),len(expected))==expected
                                report['status']='PASS_FILES_PENDING_MODULE_LOAD' if report.get('unloaded_modules') else 'PASS_FILES_AND_RUNNING_PATCHES'
                            else:report['status']='PASS_FILES_REBOOT_REQUIRED'
                            report['usr_readonly']=True;save()
                        finally:
                            t.run(cleanup_command(stage),check=False)
                        if changed:
                            report['reboot_requested']=True;save()
                            try:t.run('/bin/busybox reboot',check=False)
                            except Exception:pass # expected USB disconnection
            finally:sys.stdout,sys.stderr=original_out,original_err
    except Exception as error:
        report['error']=type(error).__name__+': '+str(error);save()
        print('Stopped. See report:',folder);raise
    print(report['status']);print('Report:',folder)
    return changed


"""Appended to the single delivered entry script by the bundle builder."""
import struct,ipaddress
def load_configuration(path):
    raw=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(raw,dict) or raw.get('version')!=1:raise ValueError('配置 version 必须为 1')
    servers=raw.get('servers')
    if not isinstance(servers,list) or len(servers)!=9:raise ValueError('必须填写 FTP1 至 FTP9 共九个槽位')
    seen=set();normalized=[]
    for entry in servers:
        if not isinstance(entry,dict) or set(entry)-{'slot','host','port','username','password'}:raise ValueError('槽位字段只支持 slot、host、port、username、password')
        slot=entry.get('slot');host=entry.get('host');port=entry.get('port')
        if type(slot)!=int or slot not in range(1,10) or slot in seen:raise ValueError('槽位编号必须为 1–9 且不能重复')
        if not isinstance(host,str) or not host or host!=host.strip() or len(host.encode('utf-8'))>255 or any(ord(c)<33 or ord(c)>126 for c in host) or any(c in host for c in '/\\:@'):raise ValueError('host 只能填写服务器 IPv4 地址或域名，不带协议或端口')
        if all(c in '0123456789.' for c in host):
            try:ipaddress.IPv4Address(host)
            except ValueError:raise ValueError('IPv4 地址不合法：FTP'+str(slot))
        if type(port)!=int or not 1<=port<=65535:raise ValueError('port 必须是 1–65535 的整数')
        item={'slot':slot,'host':host,'port':port}
        for key in ('username','password'):
            if key in entry:
                val=entry[key]
                if not isinstance(val,str) or len(val.encode('utf-8'))>64 or any(ord(c)<32 or ord(c)>126 for c in val):raise ValueError(key+' 最多 64 个可打印 ASCII 字符')
                item[key]=val
        seen.add(slot);normalized.append(item)
    selected=raw.get('selected_slot')
    if selected is not None and (type(selected)!=int or not 1<=selected<=9):raise ValueError('selected_slot 应为 null 或 1–9')
    return {'servers':sorted(normalized,key=lambda x:x['slot']),'selected_slot':selected}

def configuration_plan(config,schema,old,encrypted):
    cache_id=0x1071cd6;selection_id=0x1071c4d
    if len(old[cache_id])!=8000 or len(old[selection_id])!=1:raise ValueError('机内缓存结构不匹配，拒绝写入')
    cache=bytearray(old[cache_id]);new={}
    for item,row in zip(config['servers'],schema):
        slot=item['slot'];assert slot==row['slot'];base=36+(slot-1)*544
        host_id=int(row['host'],16);port_id=int(row['port'],16)
        if len(old[host_id])!=256 or len(old[port_id])!=2:raise ValueError('FTP'+str(slot)+' 的后台记录长度不匹配')
        new[host_id]=encrypted[(slot,'host')];new[port_id]=struct.pack('<H',item['port'])
        struct.pack_into('<I',cache,base,slot)
        cache[base+12:base+268]=item['host'].encode('ascii').ljust(256,b'\0')
        cache[base+268:base+274]=str(item['port']).encode('ascii').ljust(6,b'\0')
        for key,relative in (('username',412),('password',477)):
            if key in item:
                k=int(row[key],16)
                if len(old[k])!=256:raise ValueError('凭据记录长度不匹配')
                new[k]=encrypted[(slot,key)];cache[base+relative:base+relative+65]=item[key].encode('ascii').ljust(65,b'\0')
    current=int.from_bytes(old[selection_id],'little');selected=config['selected_slot']
    if selected is None:selected=current if 1<=current<=9 else 1
    new[selection_id]=bytes([selected]);struct.pack_into('<I',cache,24,selected)
    new[cache_id]=bytes(cache)
    return new

def persist_settings(cam,new,old,protected):
    changed=[]
    try:
        for k,b in new.items():
            if old[k]==b:continue
            changed.append(k);cam.writeBackup(k,b)
            if cam.readBackup(k)!=b:raise RuntimeError('写入回读不一致：'+hex(k))
        if changed:cam.saveBackup(0)
        if any(cam.readBackup(k)!=b for k,b in new.items()):raise RuntimeError('保存后核验失败')
        if any(cam.readBackup(k)!=old[k] for k in protected):raise RuntimeError('其他设置发生变化')
        return changed
    except Exception as ex:
        if 'USB' in type(ex).__name__ or isinstance(ex,TimeoutError):
            raise RuntimeError('连接中断，无法确认配置回滚；请保留本轮 before.private 备份，先恢复连接并核对状态') from ex
        # Only restore properties from this transaction. Never replace Backup.bin.
        for k in reversed(changed):cam.writeBackup(k,old[k])
        if changed:cam.saveBackup(0)
        if any(cam.readBackup(k)!=old[k] for k in changed):raise RuntimeError('配置回滚核验失败，请查看日志中的备份')
        raise

def read_config_file(cam,path,expected_bytes):
    # Bound each read by the catalog-verified helper or ciphertext size.
    if type(expected_bytes) is not int or not 0<=expected_bytes<=1024*1024:
        raise ValueError('Invalid configuration file read size')
    from senser_readonly import file_read_receiver
    with file_read_receiver(cam,{},expected_bytes+1024):
        return cam.readFile(path)

def configure_camera(args,config,verify=False):
    import struct
    import diagnose as d,mwf_session as m
    from ram_probe import Terminal
    from senser_readonly import file_read_receiver
    catalog=json.loads((ROOT/'resources/catalog.json').read_text(encoding='utf-8'));schema=catalog['slots']
    folder=ROOT/'logs'/datetime.datetime.now().strftime('config-%Y%m%d-%H%M%S-%f');folder.mkdir(parents=True)
    report={'status':'STARTED','firmware_writes':False,'configuration_writes':False,'operation':'verify' if verify else 'apply','slots':9,'credentials_logged':False}
    def save():(folder/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    save();stdout,stderr=sys.stdout,sys.stderr
    try:
        with (folder/'session.private.log').open('w',encoding='utf-8') as log:
            sys.stdout=sys.stderr=log
            with d.service_camera() as(cam,senser),d.terminal(cam):
                ids={0x1071cd6,0x1071c4d,0x1071c48,0x1071c49,0x1071c4a,0x1070316,0x19e000d}
                for row in schema:ids.update(int(v,16) for k,v in row.items() if k!='slot')
                old={k:cam.readBackup(k) for k in sorted(ids)}
                private=folder/'before.private';private.mkdir()
                for k,b in old.items():(private/(hex(k)+'.bin')).write_bytes(b)
                d.direct_read(senser,seconds=1)
                with m.bounded_reads(senser.driver):
                    t=Terminal(senser);_,version=t.run('/bin/busybox cat /version.txt');assert version.strip()==catalog['firmware']
                    def digest(path):
                        _,s=t.run('/bin/busybox md5sum '+path,timeout=30);hit=re.search(r'\b([0-9a-f]{32})\s+'+re.escape(path),s)
                        if not hit:raise RuntimeError('缺少文件校验响应')
                        return hit[1]
                    assert digest('/usr/lib/libBackupManager.so')==catalog['config_cipher']['backup_manager_md5']
                    assert digest('/usr/lib/libbackup.so')==catalog['config_cipher']['backup_library_md5']
                    # Verify the installed FTP patch and all donor libraries in
                    # this same service session. Opening a second USB session
                    # immediately afterward can find zero cameras.
                    assert digest('/usr/lib/libSysDef.so')==catalog['native_sysdef_md5'], 'Unexpected inhibit table'
                    targets={v['target']:v['candidate_md5'] for v in catalog['variants']}
                    for path, expected in targets.items():
                        if digest(path)!=expected:raise RuntimeError('FTP firmware installation incomplete: '+path)
                    for name, info in catalog['libraries'].items():
                        if digest('/usr/lib/'+name)!=info['md5']:
                            raise RuntimeError('FTP dependency mismatch: '+name)
                    report['firmware_verified']=True;save()
                    t.run('zp_parent() { [ -d /tmp ] && [ ! -L /tmp ]; }')
                    prefix='/tmp/zvftp_config_'+secrets.token_hex(6);helper=prefix+'.elf';temporary=[]
                    blob=(ROOT/'assets/config_cipher.elf').read_bytes();assert len(blob)==catalog['config_cipher']['bytes'] and sha(blob)==catalog['config_cipher']['sha256']
                    def read(path,expected_bytes):
                        return read_config_file(cam,path,expected_bytes)
                    def put(path,data):
                        t.run('zp_parent && [ ! -e '+path+' ]');temporary.append(path);cam.writeFile(path,data)
                        if read(path,len(data))!=data:raise RuntimeError('临时文件回读不一致')
                    def crypt(records,mode):
                        results={}
                        for start in range(0,len(records),4):
                            batch=records[start:start+4];input_path=prefix+'_'+mode+str(start)+'.in';output_path=prefix+'_'+mode+str(start)+'.out'
                            put(input_path,b''.join(b for _,b in batch).ljust(1024,b'\0'))
                            t.run('zp_parent && [ ! -e '+output_path+' ]');temporary.append(output_path)
                            _,s=t.run(helper+' '+input_path+' '+output_path+' '+mode,timeout=30)
                            if 'CIPHER_ROUNDTRIP_VERIFIED' not in s:raise RuntimeError('机内加密服务往返核验失败；未写配置')
                            encoded=read(output_path,1024)
                            if len(encoded)!=1024:raise RuntimeError('密文长度不匹配')
                            for i,(label,_) in enumerate(batch):results[label]=encoded[256*i:256*(i+1)]
                        return results
                    try:
                        report['phase']='cipher_helper_upload_and_readback';save()
                        put(helper,blob);t.run('zp_parent && /bin/busybox chmod 700 '+helper)
                        fields=[((item['slot'],key),item[key].encode('ascii').ljust(256,b'\0')) for item in config['servers'] for key in ('host','username','password') if key in item]
                        report['phase']='encrypt_and_validate_configuration';save()
                        encrypted=crypt(fields,'encrypt')
                        new=configuration_plan(config,schema,old,encrypted)
                        # Preserve existing ciphertext when its decrypted value is
                        # already correct; avoid unnecessary writes across reruns.
                        nonempty=[((item['slot'],key),old[int(schema[item['slot']-1][key],16)]) for item in config['servers'] for key in ('host','username','password') if key in item and any(old[int(schema[item['slot']-1][key],16)])]
                        decoded=crypt(nonempty,'decrypt') if nonempty else {}
                        for label,wanted in fields:
                            row=schema[label[0]-1];k=int(row[label[1]],16)
                            if decoded.get(label,bytes(256))==wanted:new[k]=old[k]
                        protected=ids-set(new)
                        if any(cam.readBackup(k)!=b for k,b in old.items()):raise RuntimeError('准备过程中相机设置变化，请停止本轮操作')
                        if verify:
                            if any(old[k]!=b for k,b in new.items()):raise RuntimeError('机内配置与配置文件不一致')
                            report['status']='PASS_CONFIG_VERIFIED'
                        else:
                            expected=folder/'expected.private';expected.mkdir()
                            for k,b in new.items():(expected/(hex(k)+'.bin')).write_bytes(b)
                            report['phase']='persist_configuration'
                            report['configuration_write_attempted']=any(old[k]!=b for k,b in new.items());save()
                            changed=persist_settings(cam,new,old,protected)
                            report.update(status='PASS_CONFIG_SAVED',configuration_writes=bool(changed),changed_properties=[hex(k) for k in changed],protected_properties_unchanged=True)
                        save()
                    finally:
                        for path in reversed(temporary):t.run('zp_parent && /bin/busybox rm -f '+path,check=False)
    except Exception as ex:
        report['error']=type(ex).__name__+': '+str(ex);save();raise
    finally:sys.stdout,sys.stderr=stdout,stderr
    print(report['status']);print('配置记录：',folder/'report.json')

def main():
    p = argparse.ArgumentParser(description=tr('ZV-1 FTP 固件安装；服务器配置由第 3 步单独写入'))
    p.add_argument('--validate', action='store_true', help=tr('仅检查本地固件资源，不访问相机'))
    p.add_argument('--check', action='store_true', help=tr('只读检查相机固件，不写入'))
    p.add_argument('--verify', action='store_true', help=tr('只读核验 FTP 固件已安装，不写入'))
    args = p.parse_args()
    if sum((args.validate, args.check, args.verify)) > 1:
        p.error(tr('检查模式一次只能选择一个'))
    catalog = json.loads((ROOT/'resources/catalog.json').read_text(encoding='utf-8'))
    if any(not (ROOT/'assets'/name).is_file() for name in catalog['libraries']):
        from extract_firmware import prepare
        prepare()
    validate(catalog)
    if args.validate:
        print('PASS_LOCAL_VALIDATION：固件资源完整，未连接相机。')
        return
    from setup_environment import ensure_environment
    ensure_environment()
    args.runtime_root = str(ROOT/'scripts/support')
    check_only = args.check or args.verify
    args.check = check_only
    changed = run(args)
    if check_only:
        return
    if changed:
        print('固件已写入，相机正在重启。')
        from operation_launcher import continue_after_usb
        continue_after_usb('reboot')
        args.verify = True
        args.check = True
        for attempt in range(3):
            try:
                run(args)
                break
            except Exception:
                if attempt == 2:
                    raise RuntimeError('固件已写入，USB 重启核验未完成；重连后用第 2 步 --verify 核验。')
                time.sleep(5)
    print('FTP 固件修改已完成。要写入 FTP1–FTP9 地址，请另运行第 3 步。')


if __name__ == '__main__':
    from operation_launcher import run
    sys.exit(run('unlock', __import__('os').environ.get('ZV1_FTP_LANG','en')))
