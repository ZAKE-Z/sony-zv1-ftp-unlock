from pathlib import Path
import contextlib,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'scripts/support'))
import zv1_ftp as installer
import senser_readonly as receiver
class CaptureLimitTests(unittest.TestCase):
 def read(self,payload,expected):
  limits=[]
  class Camera:
   def readFile(self,path):
    if len(payload)>limits[-1]:raise RuntimeError('Senser response exceeds the file capture limit.')
    return payload
  @contextlib.contextmanager
  def fake_receiver(cam,record,limit):
   limits.append(limit);yield
  with patch.object(receiver,'file_read_receiver',fake_receiver):result=installer.read_config_file(Camera(),'/tmp/helper',expected)
  return result,limits
 def test_full_actual_cipher_helper_can_be_read(self):
  payload=(ROOT/'assets/config_cipher.elf').read_bytes()
  self.assertGreater(len(payload),4000)
  self.assertLess(len(payload),10000)
  data,limits=self.read(payload,len(payload));self.assertEqual(data,payload);self.assertEqual(limits,[len(payload)+1024])
 def test_cipher_records_keep_a_small_bound(self):
  data,limits=self.read(bytes(1024),1024);self.assertEqual(len(data),1024);self.assertEqual(limits,[2048])
  with self.assertRaises(RuntimeError):self.read(bytes(2049),1024)
 def test_oversized_or_negative_expected_size_is_refused(self):
  with self.assertRaises(ValueError):installer.read_config_file(None,'/tmp/unused',-1)
  with self.assertRaises(ValueError):installer.read_config_file(None,'/tmp/unused',1024*1024+1)
if __name__=='__main__':unittest.main()
