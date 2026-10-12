from pathlib import Path
import contextlib,io,unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import operation_launcher as launcher
import ui_language as ui
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
class LanguageAndGateTests(unittest.TestCase):
 def setUp(self):
  self.lang,self.console=ui.LANG,ui.CONSOLE
 def tearDown(self):ui.LANG,ui.CONSOLE=self.lang,self.console
 def test_cancel_prevents_operation_import_in_both_languages(self):
  for language in ['en','zh']:
   stream=io.StringIO()
   with contextlib.redirect_stdout(stream),patch.object(launcher,'wait_for_key',return_value=False),patch.object(launcher.importlib,'import_module') as import_operation:
    self.assertEqual(launcher.run('unlock',language,['--validate']),0);import_operation.assert_not_called()
   self.assertIn('Cancelled' if language=='en' else '已取消',stream.getvalue())
 def test_confirmation_precedes_operation_import(self):
  events=[]
  class Operation:
   @staticmethod
   def main():events.append('main')
  def key():events.append('key');return True
  def load(name):events.append('import');return Operation
  with contextlib.redirect_stdout(io.StringIO()),patch.object(launcher,'wait_for_key',side_effect=key),patch.object(launcher.importlib,'import_module',side_effect=load):
   self.assertEqual(launcher.run('extract','en',[]),0)
  self.assertEqual(events,['key','import','main'])
 def test_noninteractive_input_refuses_before_import(self):
  with contextlib.redirect_stdout(io.StringIO()),patch.object(launcher.sys.stdin,'isatty',return_value=False),patch.object(launcher.importlib,'import_module') as load:
   self.assertEqual(launcher.run('restore','en',[]),1);load.assert_not_called()
 def test_core_message_language(self):
  ui.set_language('en')
  self.assertEqual(ui.tr('port 必须是 1–65535 的整数'),'port must be an integer within 1-65535')
  self.assertEqual(ui.tr('配置已读取：FTP1–FTP9。开始核验相机。'),'Configuration loaded: FTP1-FTP9. Checking camera.')
  ui.set_language('zh')
  self.assertEqual(ui.tr('Firmware mismatch'),'固件不匹配')
  self.assertIn('配置已保存',ui.tr('PASS_CONFIG_SAVED'))
 def test_numbered_bilingual_files(self):
  for name in ['en_1_extract_firmware','zh_1_提取固件','en_2_unlock_ftp','zh_2_解锁FTP','en_3_write_config','zh_3_写入配置','en_4_restore','zh_4_还原','en_5_set_firmware_version','zh_5_修改版本号']:
   self.assertTrue((ROOT/'scripts'/(name+'.py')).is_file());self.assertTrue((ROOT/(name+'.cmd')).is_file())
   cmd=(ROOT/(name+'.cmd')).read_text(encoding='utf-8')
   self.assertIn('scripts\\'+name+'.py',cmd)

 def test_usb_checkpoint_cancel_does_not_continue(self):
  for stage in ['reboot','configuration']:
   with contextlib.redirect_stdout(io.StringIO()),patch.object(launcher,'wait_for_key',return_value=False) as wait:
    with self.assertRaises(SystemExit) as stopped:launcher.continue_after_usb(stage)
    self.assertEqual(stopped.exception.code,0);wait.assert_called_once()
 def test_usb_checkpoint_requires_key_before_return(self):
  with contextlib.redirect_stdout(io.StringIO()),patch.object(launcher,'wait_for_key',return_value=True) as wait:
   launcher.continue_after_usb('configuration');wait.assert_called_once()

if __name__=='__main__':unittest.main()
