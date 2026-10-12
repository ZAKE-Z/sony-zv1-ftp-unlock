"""Extract only hash-verified donor libraries from user-supplied official EXEs."""
from ui_language import print,tr,announce
from pathlib import Path
import argparse,hashlib,io,json,os,shutil,stat,struct,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
MAGIC=b'\x89UFU\r\n\x1a\n'
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def apply_patches(data,plan):
 if hashlib.sha256(data).hexdigest()!=plan['original_sha256']:raise ValueError('Wrong original FTP client')
 out=bytearray(data)
 for row in plan['patches']:
  offset=int(row['offset'],16);old=bytes.fromhex(row['old']);new=bytes.fromhex(row['new'])
  if len(old)!=len(new) or out[offset:offset+len(old)]!=old:raise ValueError('FTP patch precondition mismatch')
  out[offset:offset+len(new)]=new
 if hashlib.sha256(out).hexdigest()!=plan['candidate_sha256']:raise ValueError('Final FTP client hash mismatch')
 return bytes(out)
def find_packages(directory,manifest):
 directory=Path(directory)
 if not directory.is_dir():raise ValueError('Create the firmware directory and place the two official Windows firmware EXEs there.')
 expected={r['exe_sha256']:key for key,r in manifest['firmware'].items()};found={}
 for f in sorted(directory.iterdir()):
  if f.is_file() and f.suffix.lower()=='.exe':
   key=expected.get(digest(f))
   if key:found.setdefault(key,f)
 missing=[manifest['firmware'][k]['filename'] for k in manifest['firmware'] if k not in found]
 if missing:raise ValueError('Missing exact firmware package(s): '+', '.join(missing)+'. Renaming does not change an incompatible version.')
 return found
def extract_dat(exe_path,output):
 from fwtool import pe,zip,lzh
 from fwtool.io import FilePart
 from fwtool.sony import dat
 # a7 III 4.01 contains a raw UFU payload; a7C uses a packed installer.
 with Path(exe_path).open('rb') as source:
  content=source.read();start=content.find(MAGIC)
  if start>=0:
   pos=start+8
   while True:
    if pos+8>len(content):raise ValueError('Truncated UFU chunk')
    size,kind=struct.unpack_from('>I4s',content,pos)
    if size>len(content)-pos-8:raise ValueError('Invalid UFU chunk length')
    pos+=8+size
    if kind==b'DEND':break
   output.write(content[start:pos]);return
  source.seek(0);sectors=pe.readExe(source)
  if '_winzip_' in sectors:
   members={f.path:f for f in zip.readZip(sectors['_winzip_'])}
   payload=members[dat.findDat(members.keys())].contents
  else:
   last=next(reversed(sectors.values()));packed=FilePart(source,last.offset+last.size)
   if not lzh.isLzh(packed):raise ValueError('Unsupported installer shell')
   payload=lzh.readLzh(packed).contents
  shutil.copyfileobj(payload,output)
def extract_libraries(exe_path,spec,wanted):
 from fwtool import archive
 from fwtool.sony import dat,fdat
 result={}
 with tempfile.TemporaryFile() as dat_file,tempfile.TemporaryFile() as decrypted:
  extract_dat(exe_path,dat_file);dat_file.seek(0)
  container=dat.readDat(dat_file);_,stream=fdat.decryptFdat(container.firmwareData)
  shutil.copyfileobj(stream,decrypted);decrypted.seek(0)
  meta=fdat.readFdat(decrypted)
  if meta.model!=int(spec['model_id'],16) or meta.version!=spec['version']:raise ValueError('Internal camera model/firmware version mismatch')
  print('Verified firmware:',spec['camera'],meta.version,flush=True)
  for member in archive.readArchive(meta.firmware):
   if not stat.S_ISREG(member.mode) or not member.path.endswith('/dev/nflasha15'):continue
   for entry in archive.readArchive(member.contents):
    if not stat.S_ISREG(entry.mode):continue
    name=Path(entry.path).name
    for target,row in wanted.items():
     if name not in row['source_names']:continue
     data=entry.contents.read()
     if hashlib.sha256(data).hexdigest()!=row['source_sha256']:raise ValueError('Wrong library hash: '+name)
     result[target]=data
   break
 if set(result)!=set(wanted):raise ValueError('Required donor files missing: '+str(set(wanted)-set(result)))
 return result
def prepare(directory=None,output=None,check_only=False):
 manifest=json.loads((ROOT/'resources/firmware_sources.json').read_text(encoding='utf-8'))
 packages=find_packages(directory or ROOT/'firmware',manifest)
 if check_only:
  print('PASS_EXACT_FIRMWARE_PACKAGES; camera not accessed');return
 from setup_environment import ensure_environment
 ensure_environment('crypto')
 generated={};evidence={}
 for key,spec in manifest['firmware'].items():
  wanted={name:row for name,row in manifest['libraries'].items() if row['firmware']==key}
  extracted=extract_libraries(packages[key],spec,wanted)
  for name,data in extracted.items():
   row=wanted[name]
   if 'patch_plan' in row:
    plan=json.loads((ROOT/row['patch_plan']).read_text(encoding='utf-8'));data=apply_patches(data,plan)
   if hashlib.sha256(data).hexdigest()!=row['final_sha256']:raise ValueError('Generated library mismatch: '+name)
   generated[name]=data;evidence[name]={'camera':spec['camera'],'firmware':spec['version'],'package_sha256':spec['exe_sha256'],'sha256':row['final_sha256']}
 target=Path(output or ROOT/'assets');target.mkdir(parents=True,exist_ok=True)
 for name,data in generated.items():
  dest=target/name
  if dest.is_symlink():raise ValueError('Refusing output symlink: '+str(dest))
  if dest.exists() and dest.read_bytes()!=data:raise ValueError('Existing library differs; preserved: '+str(dest))
 # All sources and patches are validated before any library output is replaced.
 for name,data in generated.items():
  fd,tmp=tempfile.mkstemp(prefix='.extract-',dir=target)
  try:
   with os.fdopen(fd,'wb') as f:f.write(data)
   os.replace(tmp,target/name)
  finally:
   if Path(tmp).exists():Path(tmp).unlink()
 (target/'extraction.private.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
 print('PASS_DONOR_LIBRARIES_PREPARED; camera not accessed')
def main():
 p=argparse.ArgumentParser(description=tr('Extract a7 III 4.01 and a7C 2.00 dependencies from locally downloaded official Windows EXEs'))
 p.add_argument('--firmware-dir',type=Path,default=ROOT/'firmware');p.add_argument('--output',type=Path,default=ROOT/'assets');p.add_argument('--check',action='store_true')
 a=p.parse_args();prepare(a.firmware_dir,a.output,a.check)
if __name__=='__main__':
    from operation_launcher import run
    sys.exit(run('extract', __import__('os').environ.get('ZV1_FTP_LANG','en')))
