"""ZV-1 host/USB terminal diagnostics; no flash, backup writes, or driver install."""
from pathlib import Path
import argparse,contextlib,datetime,os,select,socket,sys,time,traceback
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor'))
STAGE='startup'

def stage(name):
 global STAGE
 STAGE=name
 print('\n[STAGE] '+name,flush=True)

def failure():
 print('\n[FAILED STAGE] '+STAGE,flush=True)
 traceback.print_exc()

class Tee:
 def __init__(self,console,log):self.console,self.log=console,log
 def write(self,s):
  self.console.write(s);self.console.flush();self.log.write(s);self.log.flush();return len(s)
 def flush(self):self.console.flush();self.log.flush()
 def isatty(self):return False

@contextlib.contextmanager
def loopback_pair():
 with contextlib.ExitStack() as stack:
  stage('socket.create.listener')
  listener=stack.enter_context(socket.socket(socket.AF_INET,socket.SOCK_STREAM));listener.settimeout(3)
  listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
  stage('socket.bind.127.0.0.1:5005');listener.bind(('127.0.0.1',5005))
  stage('socket.listen');listener.listen(1)
  client=stack.enter_context(socket.socket(socket.AF_INET,socket.SOCK_STREAM));client.settimeout(3)
  stage('socket.client.connect');client.connect(('127.0.0.1',5005))
  stage('socket.accept');conn,_=listener.accept();stack.enter_context(conn);conn.settimeout(3)
  stage('socket.select');select.select([conn],[conn],[],0)
  stage('socket.roundtrip');client.sendall(b'PMCA-DIAG');assert conn.recv(9)==b'PMCA-DIAG';conn.sendall(b'OK');assert client.recv(2)==b'OK'
  print('[PASS] Local TCP/select/send/receive test')
  yield conn,client


def choose_backend():
 import usb.backend.libusb0,usb.backend.libusb1
 stage('usb.load.backend')
 back=usb.backend.libusb0.get_backend()
 if back is not None:print('Backend: system libusb0');return back
 import libusb_package
 back=usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
 if back is None:raise RuntimeError('No libusb backend. Existing Zadig driver is not changed by this tool.')
 print('Backend: bundled libusb1');return back


def find_camera(backend):
 import usb.core
 from pmca.usb.sony import SONY_ID_PRODUCT_SENSER
 devices=[]
 for d in usb.core.find(find_all=True,idVendor=0x054c,backend=backend):
  interfaces=[i for c in d for i in c]
  if not interfaces:continue
  i=interfaces[0]
  print('Sony USB VID=%04x PID=%04x class=%02x'%(d.idVendor,d.idProduct,i.bInterfaceClass))
  if d.idProduct in SONY_ID_PRODUCT_SENSER or i.bInterfaceClass==8:devices.append(d)
 if len(devices)!=1:raise RuntimeError('Expected exactly ONE Sony camera; found %d. Close other PMCA processes; connect only the ZV-1 in mass-storage/service mode.'%len(devices))
 return devices[0]


def make_driver(device):
 from pmca.usb.driver.generic import GenericUsbDriver,MscBbbDriver,MscCbiDriver
 from pmca.usb.driver.generic.libusb import UsbBackend
 interface=next(i for c in device for i in c)
 backend=UsbBackend(device)
 if interface.bInterfaceClass==8:
  if interface.bInterfaceProtocol==0x50:return MscBbbDriver(backend)
  if interface.bInterfaceProtocol in (0,1):return MscCbiDriver(backend)
  raise RuntimeError('Unsupported mass-storage protocol')
 return GenericUsbDriver(backend)


@contextlib.contextmanager
def service_camera():
 import usb.util
 from pmca.usb import MscDevice
 from pmca.usb.sony import SonySenserAuthDevice,SonySenserDevice,SonySenserCamera,SONY_ID_PRODUCT_SENSER,isSonyMscCamera
 backend=choose_backend();stage('usb.enumerate');device=find_camera(backend);driver=make_driver(device)
 if device.idProduct not in SONY_ID_PRODUCT_SENSER:
  stage('usb.confirm.sony.mass-storage')
  info=MscDevice(driver).getDeviceInfo()
  if not isSonyMscCamera(info):raise RuntimeError('Device not identified as a supported Sony camera')
  stage('usb.request.service-mode')
  switch=SonySenserAuthDevice(driver);switch.start();switch.authenticate();usb.util.dispose_resources(device)
  for attempt in range(20):
   time.sleep(.5)
   try:
    candidate=find_camera(backend)
    if candidate.idProduct in SONY_ID_PRODUCT_SENSER:device=candidate;break
   except Exception:
    if attempt==19:raise
  else:raise RuntimeError('Camera did not re-enumerate in service mode. Existing service-mode driver may need attention; no driver was changed.')
  driver=make_driver(device)
 stage('usb.authenticate')
 senser=SonySenserDevice(driver);auth=SonySenserAuthDevice(driver)
 try:
  auth.start();auth.authenticate();cam=SonySenserCamera(senser)
  stage('usb.readHasp');cam.readHasp();print('[PASS] Service authentication')
  yield cam,senser
 finally:
  try:auth.stop()
  except Exception:print('[CLEANUP ERROR] auth.stop');traceback.print_exc()
  usb.util.dispose_resources(device)


@contextlib.contextmanager
def terminal(cam):
 try:
  stage('camera.terminal.disable.before-test');cam.setTerminalEnable(False)
  stage('camera.terminal.enable');cam.setTerminalEnable(True)
  print('Terminal activation requests returned. A usable Linux shell is NOT yet proven.')
  yield
 finally:
  try:
   cam.setTerminalEnable(False);print('[CLEANUP] Terminal disable requested')
  except Exception:print('[CLEANUP ERROR] terminal.disable');traceback.print_exc()


def read_usb(senser):
 # Unlike upstream readTerminal(), do not silently hide non-timeout USB errors.
 import usb.core
 driver=senser.driver
 if len(driver.epIn)<2:raise RuntimeError('Terminal USB IN endpoint index 1 is missing')
 try:return driver.backend.dev.read(driver.epIn[1],0x40,timeout=100).tobytes()
 except usb.core.USBError as e:
  if isinstance(e,usb.core.USBTimeoutError) or getattr(e,'errno',None) in (60,110) or getattr(e,'backend_error_code',None) in (-7,-116):return b''
  raise


def direct_read(senser,seconds=4):
 stage('usb.terminal.read');count=0;deadline=time.monotonic()+seconds
 while time.monotonic()<deadline:
  data=read_usb(senser)
  if data:count+=len(data);print(data.decode('utf-8','replace'),end='',flush=True)
 print('\n[RX BYTES] '+str(count));return count


def probe_bridge(pair,senser):
 conn,client=pair;deadline=time.monotonic()+5;total=0
 while time.monotonic()<deadline:
  stage_name='bridge.select'
  global STAGE
  STAGE=stage_name;ready=select.select([conn],[conn],[],0)
  if ready[1]:
   STAGE='usb.terminal.read';data=read_usb(senser)
   if data:
    STAGE='bridge.send';conn.sendall(data)
    STAGE='bridge.client.recv';received=client.recv(len(data));total+=len(received);print(received.decode('utf-8','replace'),end='',flush=True)
  if ready[0]:
   STAGE='bridge.recv';data=conn.recv(64)
   if not data:break
   raise RuntimeError('Unexpected host input during passive bridge diagnostic')
 print('\n[PASS] Passive bridge loop completed; RX bytes=%d. Zero bytes does not prove a working shell.'%total)


ALLOWED={'id','uname -a','cat /proc/mounts','ls -l /usr/lib/libIMDB.so','ls -l /usr/lib/libInfraFtpClient.so','echo PMCA_DIAG_OK'}
def direct_console(senser):
 direct_read(senser)
 print('\nAllowed read-only test commands:')
 for cmd in sorted(ALLOWED):print('  '+cmd)
 print('Type exit to finish. Commands go directly over USB; no localhost sockets.')
 while True:
  cmd=input('TEST> ').strip()
  if cmd=='exit':return
  if cmd not in ALLOWED:print('Not in the diagnostic allowlist.');continue
  print('[TX] '+cmd);stage('usb.terminal.write');senser.writeTerminal((cmd+'\n').encode('ascii'));direct_read(senser)


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--direct',action='store_true');parser.add_argument('--socket-only',action='store_true');args=parser.parse_args()
 logs=ROOT/'logs';logs.mkdir(exist_ok=True);fn=logs/('diagnostic-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.txt')
 stdout,stderr=sys.stdout,sys.stderr
 with fn.open('w',encoding='utf-8') as log:
  sys.stdout=Tee(stdout,log);sys.stderr=Tee(stderr,log)
  try:
   print('ZV-1 Diagnostic v1 | '+datetime.datetime.now().isoformat());print('Python: '+sys.version);print('PMCA commit: '+(ROOT/'PMCA_COMMIT.txt').read_text().strip());print('Mode: '+('direct-usb' if args.direct else 'socket-bridge'));print('No driver installation, firmware flashing, or backup-setting writes are performed.')
   if args.direct:
    with service_camera() as (cam,senser):
     with terminal(cam):direct_console(senser)
   else:
    with loopback_pair() as pair:
     if not args.socket_only:
      with service_camera() as (cam,senser):
       with terminal(cam):probe_bridge(pair,senser)
  except KeyboardInterrupt:print('\nInterrupted; cleanup requested.')
  except Exception:failure();return 1
  finally:
   print('\nLOG FILE: '+str(fn));sys.stdout,sys.stderr=stdout,stderr
 return 0
if __name__=='__main__':sys.exit(main())
