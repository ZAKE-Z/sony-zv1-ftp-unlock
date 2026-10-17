"""DNS upgrade/restore compatibility and cross-partition donor selection."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,io,json,stat,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/vendor')]
import extract_firmware as extract
import restore,zv1_ftp
from fwtool import archive
from fwtool.sony import dat,fdat

class DnsReleaseTests(unittest.TestCase):
 def setUp(self):
  self.catalog=json.loads((ROOT/'resources/catalog.json').read_text())
 def test_previous_install_upgrades_only_dns_ui(self):
  final={v['target']:v['candidate_md5'] for v in self.catalog['variants']}
  old=next(v for v in self.catalog['legacy_restore_variants'] if v['target']=='/usr/lib/viewUnified4.so')
  selected=zv1_ftp.select(self.catalog,{**final,old['target']:old['candidate_md5']})
  self.assertEqual(len(selected),1)
  self.assertEqual(selected[0]['writer'],'dns_ui.elf')
  self.assertEqual(selected[0]['patches'][0]['new'],'02207047')
 def test_restore_accepts_legacy_and_current(self):
  originals={v['target']:v['original_md5'] for v in restore.stock_variants(self.catalog)}
  legacy=self.catalog['legacy_restore_variants'][0]
  result=restore.restore_plan(self.catalog,{**originals,legacy['target']:legacy['candidate_md5']})
  self.assertEqual(len(result),1);self.assertEqual(result[0]['writer'],'bounded_input.elf')
  current=next(v for v in restore.stock_variants(self.catalog) if v['target']==legacy['target'])
  result=restore.restore_plan(self.catalog,{**originals,current['target']:current['candidate_md5']})
  self.assertEqual(result[0]['writer'],'bounded_input_dns.elf')
 def test_running_memory_uses_full_patch_not_upgrade_only(self):
  finals=zv1_ftp.final_variants(self.catalog)
  view=next(v for v in finals if v['target']=='/usr/lib/viewUnified4.so')
  self.assertEqual(view['writer'],'bounded_input_dns.elf')
  self.assertEqual(len(view['patches']),3)
  self.assertEqual(view['patches'][-1]['offset'],'0x1a2e24')
  self.assertEqual(len(finals),4)
 def test_nss_source_runtime_hash_and_probe(self):
  source=json.loads((ROOT/'resources/firmware_sources.json').read_text())['libraries']['libnss_dns.so.2']
  self.assertEqual(source['firmware'],'a7c_200')
  self.assertEqual(source['source_partition'],'nflasha7')
  self.assertEqual(source['source_path'],'/lib/libnss_dns-2.11.2.so')
  self.assertEqual(source['final_sha256'],self.catalog['libraries']['libnss_dns.so.2']['sha256'])
  runtime=self.catalog['dns_runtime']
  self.assertEqual(hashlib.sha256((ROOT/'assets'/runtime['probe']).read_bytes()).hexdigest(),runtime['probe_sha256'])

class DnsPartitionExtractionTests(unittest.TestCase):
 def extract(self,root_present=True,wrong_hash=False):
  crypto=b'synthetic-crypto';dns=b'synthetic-dns'
  wanted={
   'crypto.so':{'source_names':['crypto.original.so'],'source_sha256':hashlib.sha256(crypto).hexdigest()},
   'libnss_dns.so.2':{'source_names':['libnss_dns-original.so'],'source_partition':'nflasha7',
      'source_path':'/lib/libnss_dns-original.so','source_sha256':hashlib.sha256(dns).hexdigest()}}
  def entry(path,content):return SimpleNamespace(mode=stat.S_IFREG,path=path,contents=content)
  lists={'firmware':[entry('/dev/nflasha15','user'),entry('/dev/nflasha7','root')],
         'user':[entry('/lib/crypto.original.so',io.BytesIO(crypto)),
                 entry('/lib/libnss_dns-original.so',io.BytesIO(b'wrong partition must be ignored'))],
         'root':[entry('/wrong/libnss_dns-original.so',io.BytesIO(b'wrong path must be ignored'))]}
  if root_present:lists['root'].append(entry('/lib/libnss_dns-original.so',io.BytesIO(b'wrong hash' if wrong_hash else dns)))
  with patch.object(extract,'extract_dat'), \
       patch.object(dat,'readDat',return_value=SimpleNamespace(firmwareData=None)), \
       patch.object(fdat,'decryptFdat',return_value=(None,io.BytesIO(b'payload'))), \
       patch.object(fdat,'readFdat',return_value=SimpleNamespace(model=1,version='2.00',firmware='firmware')), \
       patch.object(archive,'readArchive',side_effect=lambda value:iter(lists[value])):
   return extract.extract_libraries('unused.exe',{'model_id':'0x1','version':'2.00','camera':'synthetic'},wanted)
 def test_both_partitions_and_exact_path(self):
  self.assertEqual(self.extract(),{'crypto.so':b'synthetic-crypto','libnss_dns.so.2':b'synthetic-dns'})
 def test_wrong_partition_does_not_satisfy_missing_root_file(self):
  with self.assertRaises(ValueError):self.extract(root_present=False)
 def test_hash_mismatch_refuses(self):
  with self.assertRaises(ValueError):self.extract(wrong_hash=True)

if __name__=='__main__':unittest.main()
