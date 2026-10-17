"""Restore stock firmware spans; clear FTP settings and preserve Wi-Fi/USB settings."""
from ui_language import print,tr,announce
from pathlib import Path
import argparse,datetime,hashlib,json,re,secrets,sys
ROOT=Path(__file__).resolve().parents[1]
def stock_variants(catalog):
 writers={'/usr/lib/libObj.so':'auto_obj_native.elf','/usr/lib/viewUnified2.so':'auto_view_native.elf','/usr/lib/CautionConfig.so':'menu_native.elf','/usr/lib/viewUnified4.so':'bounded_input_dns.elf'}
 result=[]
 for target,writer in writers.items():
  rows=[v for v in catalog['variants'] if v['target']==target and v['writer']==writer]
  if len(rows)!=1:raise ValueError('No unique stock restore variant: '+target)
  result.append(rows[0])
 return result
def restore_plan(catalog,actual):
 result=[]
 targets=sorted({v['target'] for v in catalog['variants']})
 for path in targets:
  candidates=[v for v in stock_variants(catalog) if v['target']==path]
  if len(candidates)!=1:raise ValueError('No unique stock restore variant: '+path)
  row=candidates[0]
  if actual[path]==row['original_md5']:continue
  choices=[v for v in [row,*catalog.get('legacy_restore_variants',[])]
           if v['target']==path and v['original_md5']==row['original_md5'] and v['candidate_md5']==actual[path]]
  if len(choices)!=1:raise ValueError('Unknown firmware state; refusing to restore '+path)
  result.append(choices[0])
 return result
def main():
 p=argparse.ArgumentParser(description=tr('Restore stock ZV-1 firmware files; clear FTP profiles; preserve Wi-Fi/USB settings'))
 p.add_argument('--check',action='store_true',help=tr('Read-only restore preflight'));args=p.parse_args()
 from setup_environment import ensure_environment
 ensure_environment()
 import diagnose as d,mwf_session as m
 from ram_probe import Terminal,owned_guard,cleanup_command
 from senser_readonly import file_read_receiver
 catalog=json.loads((ROOT/'resources/catalog.json').read_text(encoding='utf-8'))
 folder=ROOT/'logs'/datetime.datetime.now().strftime('restore-%Y%m%d-%H%M%S-%f');folder.mkdir(parents=True)
 announce('camera')
 from ftp_cleanup import reset_keys,reset_plan,transport_failure,expected_reboot_disconnect
 from zv1_ftp import persist_settings
 report={'status':'STARTED','settings_written':False,'restored':[],'removed_libraries':[]}
 def save():(folder/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 def digest(t,path):
  _,s=t.run('/bin/busybox md5sum '+path,timeout=60);hit=re.search(r'\b([0-9a-f]{32})\s+'+re.escape(path),s)
  if not hit:raise RuntimeError('Missing checksum: '+path)
  return hit[1]
 def readonly(t):
  _,s=t.run('/bin/busybox cat /proc/mounts');rows=[x.split() for x in s.splitlines() if len(x.split())>3 and x.split()[1]=='/usr']
  if len(rows)!=1:raise RuntimeError('Unexpected /usr mount state')
  return 'ro' in rows[0][3].split(',')
 save()
 try:
  with (folder/'session.private.log').open('w',encoding='utf-8') as log:
   stdout,stderr=sys.stdout,sys.stderr;sys.stdout=sys.stderr=log
   try:
    with d.service_camera() as(cam,senser),d.terminal(cam):
     d.direct_read(senser,seconds=1)
     with m.bounded_reads(senser.driver):
      t=Terminal(senser);_,version=t.run('/bin/busybox cat /version.txt')
      if version.strip()!=catalog['firmware'] or not readonly(t):raise RuntimeError('Wrong firmware or writable /usr; no restore')
      if digest(t,'/usr/lib/libSysDef.so')!=catalog['native_sysdef_md5']:raise RuntimeError('Unknown inhibit table; no restore')
      actual={target:digest(t,target) for target in sorted({v['target'] for v in catalog['variants']})};plan=restore_plan(catalog,actual)
      libs=[]
      for name,row in catalog['libraries'].items():
       path='/usr/lib/'+name;_,s=t.run('if [ -e '+path+' ]; then echo PRESENT; else echo ABSENT; fi')
       if 'PRESENT' in s:
        if digest(t,path)!=row['md5']:raise RuntimeError('Unknown added dependency; no restore: '+name)
        libs.append(name)
       elif 'ABSENT' not in s:raise RuntimeError('No existence response')
      protected_ids={0x1070316,0x19e000d}
      old_settings={k:cam.readBackup(k) for k in sorted(set(reset_keys(catalog))|protected_ids)}
      defaults=reset_plan(catalog,old_settings)
      settings_changes=[k for k,b in defaults.items() if old_settings[k]!=b]
      report.update(source_hashes=actual,planned=[v['name'] for v in plan],planned_library_removals=libs,planned_ftp_reset_properties=[hex(k) for k in settings_changes]);save()
      if args.check:report['status']='PASS_RESTORE_PREFLIGHT_NO_WRITES';save();return
      settings={k:old_settings[k] for k in protected_ids}
      private=folder/'before.private';private.mkdir()
      for k,b in old_settings.items():(private/(hex(k)+'.bin')).write_bytes(b)
      reset_attempted=False
      source='zv1restore_'+secrets.token_hex(6);stage='/tmp/.'+source
      t.run('zp_parent() { [ -d /tmp ] && [ ! -L /tmp ]; }');t.run('zp_parent');t.run(owned_guard(stage,source))
      t.run('zp_parent && (umask 077; mkdir '+stage+')');t.run('zp_parent && mount -n -t tmpfs -o size=1024k,mode=0700,nosuid,nodev '+source+' '+stage);t.run('zp_parent && zp_owned')
      remotes=[];removed=[];applied=[]
      try:
       for v in plan:
        with file_read_receiver(cam,{},64*1024*1024):b=cam.readFile(v['target'])
        if hashlib.sha256(b).hexdigest()!=v['candidate_sha256']:raise RuntimeError('Full-file hash mismatch')
        (folder/(Path(v['target']).name+'.before.so')).write_bytes(b)
        helper=(ROOT/'assets'/v['writer']).read_bytes()
        if hashlib.sha256(helper).hexdigest()!=v['writer_sha256']:raise RuntimeError('Writer resource mismatch')
        remote=stage+'/'+v['writer'];cam.writeFile(remote,helper)
        with file_read_receiver(cam,{},len(helper)+1024):assert cam.readFile(remote)==helper
        t.run('zp_parent && zp_owned && chmod 700 '+remote);remotes.append((remote,v))
       for name in libs:
        with file_read_receiver(cam,{},1024*1024):b=cam.readFile('/usr/lib/'+name)
        if hashlib.sha256(b).hexdigest()!=catalog['libraries'][name]['sha256']:raise RuntimeError('Dependency full-file hash mismatch')
        (folder/(name+'.before.so')).write_bytes(b);cam.writeFile(stage+'/'+name,b)
        with file_read_receiver(cam,{},len(b)+1024):assert cam.readFile(stage+'/'+name)==b
       if plan or libs or settings_changes:
        if any(cam.readBackup(k)!=b for k,b in old_settings.items()):raise RuntimeError('Camera settings changed during preparation; refusing restore')
        announce('restore')
        t.run('/bin/busybox mount -o remount,rw /usr')
        if readonly(t):raise RuntimeError('Remount failed')
        try:
         for remote,v in remotes:
          applied.append((remote,v));_,s=t.run(remote+' '+v['target']+' restore')
          if 'LIFE_RESTORED' not in s or digest(t,v['target'])!=v['original_md5']:raise RuntimeError('Restore verification failed')
          report['restored'].append(v['name']);save()
         if settings_changes:
          announce('reset_config');reset_attempted=True
          report['configuration_write_attempted']=True;save()
          reset_changed=persist_settings(cam,defaults,old_settings,protected_ids)
          report.update(settings_written=bool(reset_changed),ftp_configuration_cleared=True,reset_properties=[hex(k) for k in reset_changed]);save()
         for name in libs:
          removed.append(name);t.run('/bin/busybox rm /usr/lib/'+name);report['removed_libraries'].append(name);save()
         if any(cam.readBackup(k)!=b for k,b in settings.items()):raise RuntimeError('Protected settings changed')
        except Exception as e:
         if transport_failure(e):report['status']='INTERRUPTED_REQUIRES_INSPECTION';save();raise
         for name in reversed(removed):
          path='/usr/lib/'+name;t.run('/bin/busybox cp '+stage+'/'+name+' '+path);t.run('/bin/busybox chmod 555 '+path)
          if digest(t,path)!=catalog['libraries'][name]['md5']:raise RuntimeError('Rollback library mismatch')
         for remote,v in reversed(applied):
          _,s=t.run(remote+' '+v['target']+' apply')
          if 'LIFE_APPLIED' not in s or digest(t,v['target'])!=v['candidate_md5']:raise RuntimeError('Rollback patch mismatch')
         if reset_attempted:
          current={k:cam.readBackup(k) for k in old_settings}
          persist_settings(cam,{k:old_settings[k] for k in defaults},current,protected_ids)
          report['settings_written']=False
         report['status']='FAILED_ROLLED_BACK';save();raise
        finally:t.run('/bin/busybox sync',check=False);t.run('/bin/busybox mount -o remount,ro /usr',check=False)
       for target in actual:
        row=next(v for v in stock_variants(catalog) if v['target']==target)
        if digest(t,target)!=row['original_md5']:raise RuntimeError('Final stock file mismatch')
       for name in libs:
        _,s=t.run('if [ -e /usr/lib/'+name+' ]; then echo PRESENT; else echo ABSENT; fi')
        if 'ABSENT' not in s:raise RuntimeError('Added library still exists')
       if not readonly(t):raise RuntimeError('/usr not read-only')
       if any(cam.readBackup(k)!=b for k,b in defaults.items()):raise RuntimeError('FTP reset verification failed')
       report['ftp_configuration_cleared']=True
       report['status']='PASS_RESTORE_FILES_REBOOT_REQUIRED' if plan or libs or settings_changes else 'PASS_ALREADY_STOCK';save()
      finally:t.run(cleanup_command(stage),check=False)
      if plan or libs or settings_changes:
       report['reboot_command_attempted']=True;report['reboot_completion_verified']=False;save()
       announce('reboot');t.run('/bin/busybox reboot',check=False)
   finally:sys.stdout,sys.stderr=stdout,stderr
 except Exception as e:
  if expected_reboot_disconnect(report,e):
   report['reboot_usb_disconnect']=type(e).__name__+': '+str(e);save()
   print('Restore verified before reboot; USB disconnected during the reboot request. Wait for the camera to restart and confirm the result.')
  else:
   report['error']=type(e).__name__+': '+str(e);save();raise
 finally:print(report['status']);print('Report:',folder/'report.json')
if __name__=='__main__':
    from operation_launcher import run
    sys.exit(run('restore', __import__('os').environ.get('ZV1_FTP_LANG','en')))
