from pathlib import Path
import json,unittest,tempfile,importlib.util,copy,hashlib,contextlib,io
ROOT=Path(__file__).resolve().parents[1]
import sys
from unittest.mock import patch
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('installer',ROOT/'scripts/zv1_ftp.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec2=importlib.util.spec_from_file_location('setver',ROOT/'scripts/set_reported_version.py');sv=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(sv)
class ProjectTests(unittest.TestCase):
 def test_default_slots(self):
  c=m.load_configuration(ROOT/'ftp_config.example.json');self.assertEqual(len(c['servers']),9)
  for s in c['servers']:self.assertEqual(s,{'slot':s['slot'],'host':'127.0.0.1','port':21})
 def test_reject_invalid_configuration(self):
  for field,value in [('port',0),('port',65536),('port',True),('host','ftp://localhost'),('host','999.20.10.123'),('slot',2)]:
   c=json.loads((ROOT/'ftp_config.example.json').read_text());c['servers'][0][field]=value
   with tempfile.TemporaryDirectory() as d:
    f=Path(d)/'config.json';f.write_text(json.dumps(c))
    with self.assertRaises(ValueError):m.load_configuration(f)
 def test_known_firmware_selection(self):
  c=json.loads((ROOT/'resources/catalog.json').read_text());final={v['target']:v['candidate_md5'] for v in c['variants']}
  self.assertEqual(m.select(c,final),[])
  for v in c['variants']:
   actual={**final,v['target']:v['original_md5']};self.assertEqual(m.select(c,actual),[v])
  with self.assertRaises(RuntimeError):m.select(c,{**final,'/usr/lib/CautionConfig.so':'0'*32})
 def test_custom_tools_hash(self):
  c=json.loads((ROOT/'resources/catalog.json').read_text())
  for v in c['variants']:self.assertEqual(hashlib.sha256((ROOT/'assets'/v['writer']).read_bytes()).hexdigest(),v['writer_sha256'])
  self.assertEqual(hashlib.sha256((ROOT/'assets/config_cipher.elf').read_bytes()).hexdigest(),c['config_cipher']['sha256'])
 def test_unlock_does_not_write_server_configuration(self):
  import extract_firmware,setup_environment
  with patch.object(sys,'argv',['unlock','--verify']), \
       patch.object(m,'validate'), \
       patch.object(extract_firmware,'prepare'), \
       patch.object(setup_environment,'ensure_environment'), \
       patch.object(m,'run',return_value=False) as inspect_firmware, \
       patch.object(m,'configure_camera',side_effect=AssertionError('unexpected config write')), \
       contextlib.redirect_stdout(io.StringIO()):
   m.main()
  inspect_firmware.assert_called_once()

 def test_config_validation_does_not_open_camera(self):
  import write_ftp_config
  with patch.object(sys,'argv',['write_config','--validate','--config',str(ROOT/'ftp_config.example.json')]), \
       patch.object(m,'run',side_effect=AssertionError('unexpected camera access')), \
       patch.object(m,'configure_camera',side_effect=AssertionError('unexpected camera access')), \
       contextlib.redirect_stdout(io.StringIO()):
   write_ftp_config.main()

 def test_config_apply_does_not_open_a_second_preflight_session(self):
  import write_ftp_config,setup_environment
  with patch.object(sys,'argv',['write_config','--config',str(ROOT/'ftp_config.example.json')]), \
       patch.object(setup_environment,'ensure_environment'), \
       patch.object(write_ftp_config.core,'run',side_effect=AssertionError('second USB session')), \
       patch.object(write_ftp_config.core,'configure_camera') as configure, \
       contextlib.redirect_stdout(io.StringIO()):
   write_ftp_config.main()
  configure.assert_called_once()

 def test_version_record_roundtrip(self):
  self.assertEqual(sv.decode_version(b'\x01\x02'),'2.01');self.assertEqual(sv.decode_version(b'\x00\x02'),'2.00')
  self.assertEqual(sv.encode_version('2.00'),b'\x00\x02');self.assertEqual(sv.encode_version('2.01'),b'\x01\x02')
 def test_version_record_rejects(self):
  with self.assertRaises(ValueError):sv.encode_version('2.02')
  with self.assertRaises(ValueError):sv.encode_version('3.00')
  with self.assertRaises(ValueError):sv.decode_version(b'\x01')
if __name__=='__main__':unittest.main()
