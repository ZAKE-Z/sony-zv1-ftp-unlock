"""Set only the reported version record to 2.00; does not downgrade firmware."""
from ui_language import print,tr,announce
from pathlib import Path
import argparse,datetime,json,sys
ROOT=Path(__file__).resolve().parents[1]
TARGET='/setting/updater/dat4'
def decode_version(raw):
 if len(raw)!=2:raise ValueError('Unexpected version record length')
 return '%x.%02x'%(raw[1],raw[0])
def encode_version(text):
 if text not in ('2.00','2.01'):raise ValueError('Only 2.00 and 2.01 are recognized')
 major,minor=text.split('.');return bytes([int(minor,16),int(major,16)])
def main():
 p=argparse.ArgumentParser(description=tr('Set ZV-1 reported version to 2.00 for a later official updater reinstall; this script does not reinstall firmware'))
 p.add_argument('--version',choices=['2.00'],default='2.00');p.add_argument('--check',action='store_true');a=p.parse_args()
 from setup_environment import ensure_environment
 ensure_environment()
 import diagnose as d
 from senser_readonly import file_read_receiver
 folder=ROOT/'logs'/datetime.datetime.now().strftime('set-version-%Y%m%d-%H%M%S-%f');folder.mkdir(parents=True)
 announce('camera')
 report={'target':TARGET,'requested':a.version,'status':'STARTED'}
 def save():(folder/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 save()
 try:
  with d.service_camera() as(cam,senser):
   with file_read_receiver(cam,{},65536):version=cam.readFile('/version.txt')
   expected=json.loads((ROOT/'resources/catalog.json').read_text(encoding='utf-8'))['firmware']
   if version.decode('ascii').strip()!=expected:raise RuntimeError('Unsupported camera/firmware; no write')
   with file_read_receiver(cam,{},4096):old=cam.readFile(TARGET)
   report['original_hex']=old.hex();report['original_version']=decode_version(old);save()
   if report['original_version'] not in ('2.00','2.01'):raise RuntimeError('Unexpected version record; no write')
   (folder/'dat4.original.bin').write_bytes(old)
   if a.check:report['status']='PASS_VERSION_PREFLIGHT_NO_WRITES';save();return
   new=encode_version(a.version)
   if old!=new:
    announce('version');cam.writeFile(TARGET,new)
   with file_read_receiver(cam,{},4096):actual=cam.readFile(TARGET)
   if actual!=new:raise RuntimeError('Version readback mismatch; inspect saved original record')
   report.update(status='PASS_READBACK',actual_version=decode_version(actual),changed=old!=new);save()
 except Exception as e:report.update(status='FAILED',error=type(e).__name__+': '+str(e));save();raise
 finally:print(report['status']);print('Report:',folder/'report.json')
if __name__=='__main__':
    from operation_launcher import run
    sys.exit(run('version', __import__('os').environ.get('ZV1_FTP_LANG','en')))
