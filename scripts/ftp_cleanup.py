"""Restore validated unused FTP defaults without replacing Backup.bin."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
GLOBALS={0x1071c48,0x1071c49,0x1071c4a,0x1071c4d,0x1071cd6}
def reset_plan(catalog,old):
 path=ROOT/'resources/ftp_reset_defaults.json';blob=path.read_bytes()
 if hashlib.sha256(blob).hexdigest()!=catalog['ftp_reset']['sha256']:raise ValueError('FTP reset rules checksum mismatch')
 rules=json.loads(blob)['properties'];new={}
 for name,row in rules.items():
  k=int(name,16)
  if k>>16!=0x1ac and k not in GLOBALS:raise ValueError('Reset rule outside FTP scope')
  size=row['bytes']
  if k not in old or len(old[k])!=size:raise ValueError('FTP reset record length mismatch: '+name)
  data=bytearray(size);seen=set()
  for index,value in row['nonzero']:
   if not 0<=index<size or not 1<=value<=255 or index in seen:raise ValueError('Invalid FTP default rule')
   seen.add(index);data[index]=value
  new[k]=bytes(data)
 expected={int(v,16) for row in catalog['slots'] for key,v in row.items() if key!='slot'}
 if not expected.issubset(new):raise ValueError('Reset rules do not cover all nine FTP profiles')
 return new
def reset_keys(catalog):
 blob=(ROOT/'resources/ftp_reset_defaults.json').read_bytes()
 if hashlib.sha256(blob).hexdigest()!=catalog['ftp_reset']['sha256']:raise ValueError('FTP reset rules checksum mismatch')
 return sorted(int(k,16) for k in json.loads(blob)['properties'])
def transport_failure(error):
 seen=set()
 while error is not None and id(error) not in seen:
  seen.add(id(error))
  if 'USB' in type(error).__name__ or isinstance(error,TimeoutError):return True
  error=error.__cause__ or error.__context__
 return False
def expected_reboot_disconnect(report,error):
 if report.get('status')!='PASS_RESTORE_FILES_REBOOT_REQUIRED' or not report.get('reboot_command_attempted'):return False
 if type(error).__name__!='USBError':return False
 if getattr(error,'errno',None)==19 or getattr(error,'backend_error_code',None)==-4:return True
 message=' '.join(v.decode('gbk',errors='replace') if isinstance(v,bytes) else str(v) for v in error.args).lower()
 return any(s in message for s in ['指定不存在的设备','连到系统上的设备没有发挥作用','no such device','device not connected','device is not connected','device attached to the system is not functioning'])
