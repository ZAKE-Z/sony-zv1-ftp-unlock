from pathlib import Path
import hashlib,importlib.util,json,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
extract=module('extract_firmware');restore=module('restore')
class RevisionTests(unittest.TestCase):
 def test_patch_preconditions_and_final_hash(self):
  old=b'0123456789';new=b'012AB56789'
  plan={'original_sha256':hashlib.sha256(old).hexdigest(),'candidate_sha256':hashlib.sha256(new).hexdigest(),'patches':[{'offset':'0x3','old':'3334','new':'4142'}]}
  self.assertEqual(extract.apply_patches(old,plan),new)
  with self.assertRaises(ValueError):extract.apply_patches(b'other',plan)
  plan['patches'][0]['old']='3335'
  with self.assertRaises(ValueError):extract.apply_patches(old,plan)
 def test_package_identified_by_content_not_filename(self):
  blob=b'known firmware';manifest={'firmware':{'donor':{'filename':'official.exe','exe_sha256':hashlib.sha256(blob).hexdigest()}}}
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'renamed.exe';f.write_bytes(blob)
   self.assertEqual(extract.find_packages(d,manifest)['donor'],f)
   f.write_bytes(b'wrong version')
   with self.assertRaises(ValueError):extract.find_packages(d,manifest)
 def test_restore_stock_and_final_only(self):
  c=json.loads((ROOT/'resources/catalog.json').read_text());native=restore.stock_variants(c)
  self.assertEqual(len(native),4)
  original={v['target']:v['original_md5'] for v in native};final={v['target']:v['candidate_md5'] for v in native}
  self.assertEqual(restore.restore_plan(c,original),[])
  self.assertEqual(len(restore.restore_plan(c,final)),4)
  final[native[0]['target']]='0'*32
  with self.assertRaises(ValueError):restore.restore_plan(c,final)
 def test_exact_donor_versions_and_catalog_consistency(self):
  s=json.loads((ROOT/'resources/firmware_sources.json').read_text());c=json.loads((ROOT/'resources/catalog.json').read_text())
  self.assertEqual(s['firmware']['a7iii_401']['version'],'4.01');self.assertEqual(s['firmware']['a7c_200']['version'],'2.00')
  for name,row in s['libraries'].items():self.assertEqual(row['final_sha256'],c['libraries'][name]['sha256'])
  plan=json.loads((ROOT/'resources/patches/ftp_client.json').read_text())
  self.assertEqual(plan['original_sha256'],s['libraries']['libInfraFtpClient.so']['source_sha256'])
  self.assertEqual(plan['candidate_sha256'],s['libraries']['libInfraFtpClient.so']['final_sha256'])
if __name__=='__main__':unittest.main()
