from pathlib import Path
import io,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import ftp_cleanup as cleanup
from zv1_ftp import persist_settings
class CleanupTests(unittest.TestCase):
 def setUp(self):
  self.catalog=json.loads((ROOT/'resources/catalog.json').read_text())
  rows=json.loads((ROOT/'resources/ftp_reset_defaults.json').read_text())['properties']
  self.old={int(k,16):b'X'*row['bytes'] for k,row in rows.items()}
  self.old[0x1070316]=b'model';self.old[0x19e000d]=b'wifi-private'
  self.new=cleanup.reset_plan(self.catalog,self.old)
 def test_scope_and_nine_empty_profiles(self):
  self.assertEqual(len(self.new),133)
  self.assertNotIn(0x1071cd7,self.new);self.assertNotIn(0x1070316,self.new);self.assertNotIn(0x19e000d,self.new)
  for row in self.catalog['slots']:
   for field in ['host','username','password','directory']:self.assertEqual(self.new[int(row[field],16)],bytes(256))
   self.assertEqual(self.new[int(row['port'],16)],b'\x15\x00')
  self.assertEqual(self.new[0x1071c4d],b'\x00')
  self.assertEqual(sum(bool(x) for x in self.new[0x1071cd6]),1)
 def test_length_mismatch_refuses(self):
  changed=self.old.copy();changed[0x1071cd6]=b'bad'
  with self.assertRaises(ValueError):cleanup.reset_plan(self.catalog,changed)
 def test_transaction_and_every_failure_rolls_back(self):
  initial=self.old.copy()
  class Camera:
   def __init__(self,fail=None):self.data=initial.copy();self.calls=0;self.fail=fail;self.failed=False
   def readBackup(self,k):return self.data[k]
   def writeBackup(self,k,b):
    self.calls+=1
    if self.calls==self.fail and not self.failed:self.failed=True;raise RuntimeError('simulated failure')
    self.data[k]=b
   def saveBackup(self,unused):pass
  c=Camera();written=persist_settings(c,self.new,self.old,{0x1070316,0x19e000d})
  self.assertEqual(len(written),133)
  self.assertEqual(c.data[0x19e000d],b'wifi-private')
  self.assertEqual(persist_settings(c,self.new,c.data.copy(),{0x1070316,0x19e000d}),[])
  for failure in range(1,len(written)+1):
   c=Camera(failure)
   with self.assertRaises(RuntimeError):persist_settings(c,self.new,self.old,{0x1070316,0x19e000d})
   self.assertEqual(c.data,initial)
 def test_only_verified_reboot_device_loss_is_normalized(self):
  USBError=type('USBError',(Exception,),{})
  e=USBError(None,'连到系统上的设备没有发挥作用。'.encode('gbk'))
  good={'status':'PASS_RESTORE_FILES_REBOOT_REQUIRED','reboot_command_attempted':True}
  self.assertTrue(cleanup.expected_reboot_disconnect(good,e))
  self.assertFalse(cleanup.expected_reboot_disconnect({'status':'STARTED','reboot_command_attempted':True},e))
  self.assertFalse(cleanup.expected_reboot_disconnect({'status':'PASS_RESTORE_FILES_REBOOT_REQUIRED'},e))
  self.assertFalse(cleanup.expected_reboot_disconnect(good,RuntimeError('hash mismatch')))
  self.assertFalse(cleanup.expected_reboot_disconnect(good,USBError('unrelated USB protocol error')))
 def test_wrapped_usb_error_prevents_unsafe_rollback(self):
  USBError=type('USBError',(Exception,),{})
  e=RuntimeError('wrapped failure');e.__cause__=USBError('lost device')
  self.assertTrue(cleanup.transport_failure(e));self.assertFalse(cleanup.transport_failure(RuntimeError('format error')))
if __name__=='__main__':unittest.main()
