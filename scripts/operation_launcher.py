"""Numbered bilingual entry gate. Imports operation code only after a key press."""
import argparse,importlib,os,sys
from ui_language import set_language,tr,print,announce
OPERATIONS={
 'extract':('extract_firmware','1. Extract donor firmware','1. 提取供体固件','Reads a7 III 4.01 and a7C 2.00 Windows EXEs in firmware/. No camera is accessed.','读取 firmware/ 中的 a7 III 4.01 和 a7C 2.00 Windows 固件，不访问相机。'),
 'unlock':('zv1_ftp','2. Unlock FTP','2. 解锁 FTP','Installs FTP firmware modifications only. Connect one ZV-1 in Mass Storage mode.','仅安装 FTP 固件修改。请连接一台大容量存储模式的 ZV-1。'),
 'config':('write_ftp_config','3. Write FTP configuration','3. 写入 FTP 配置','Writes FTP1-FTP9 from ftp_config.json without changing firmware files.','读取 ftp_config.json 写入 FTP1–FTP9，不修改固件文件。'),
 'restore':('restore','4. Restore firmware','4. 还原固件','Restores supported stock firmware files, removes added libraries and clears all FTP configuration. Wi-Fi/USB settings are preserved.','还原已支持的原版固件文件、移除新增库并清除全部 FTP 配置；保留 Wi-Fi 和 USB 设置。'),
 'version':('set_reported_version','5. Set reported firmware version','5. 修改报告固件版本','Only changes the reported record to 2.00. It does not reinstall or downgrade firmware.','仅把报告版本记录改为 2.00，不重装或降级固件。'),
}
def wait_for_key():
 if not sys.stdin.isatty():raise RuntimeError(tr('Interactive console required; no operation started.'))
 if os.name=='nt':
  import msvcrt
  # Discard keys left by opening the console; require a fresh key press.
  while msvcrt.kbhit():msvcrt.getwch()
  key=msvcrt.getwch()
  if key in ('\x00','\xe0'):msvcrt.getwch()
  if key in ('\x1b','\x03'):return False
 else:
  import termios,tty
  fd=sys.stdin.fileno();old=termios.tcgetattr(fd)
  try:
   tty.setcbreak(fd);key=sys.stdin.read(1)
  finally:termios.tcsetattr(fd,termios.TCSADRAIN,old)
  if key in ('\x1b','\x03'):return False
 return True
def continue_after_usb(stage):
 import ui_language as language
 zh=language.LANG=='zh'
 print('='*60)
 if stage=='reboot':
  print('固件已写入。请等相机重启完成，并恢复 USB 大容量存储连接。' if zh else 'Firmware has been written. Wait for the camera to finish rebooting and restore its USB mass-storage connection.')
 else:
  print('固件核验已结束。请等 USB 连接稳定，再继续服务器配置步骤。' if zh else 'Firmware verification has ended. Wait for USB to stabilize before the server configuration stage.')
 print('若连接未恢复，请重插 USB。不要开关 FTP。' if zh else 'If USB has not recovered, reconnect the cable. Do not toggle FTP.')
 print('连接恢复后按任意键继续，Esc 取消后续操作。' if zh else 'Press any key after the connection is ready; Esc cancels the remaining steps.',flush=True)
 if not wait_for_key():
  print('已取消后续操作；已完成的固件写入保留，本轮配置步骤尚未执行。' if zh else 'Remaining steps cancelled; completed firmware writes are retained and this configuration stage has not run.')
  raise SystemExit(0)

def run(operation,language,argv=None):
 set_language(language);argv=list(sys.argv[1:] if argv is None else argv)
 spec=OPERATIONS[operation]
 help_only=any(x in ('-h','--help') for x in argv)
 if help_only:
  print(spec[2 if language=='zh' else 1]);print(spec[4 if language=='zh' else 3])
  print('本入口在任何操作之前等待按键；Esc 取消。' if language=='zh' else 'This entry waits for a key before any operation; Esc cancels.')
 else:
  print('='*60);print(spec[2 if language=='zh' else 1]);print(spec[4 if language=='zh' else 3])
  print('检查参数：' if language=='zh' else 'Arguments:', ' '.join(argv) or ('默认操作' if language=='zh' else 'default operation'))
  print('尚未安装依赖、读取固件或访问相机。' if language=='zh' else 'No dependencies installed, firmware read or camera accessed yet.')
  print('按任意键开始，Esc 取消；也可直接关闭窗口。' if language=='zh' else 'Press any key to begin, Esc to cancel; closing the window also cancels.',flush=True)
  try:
   if not wait_for_key():
    print('已取消，未执行操作。' if language=='zh' else 'Cancelled; no operation started.');return 0
  except (KeyboardInterrupt,EOFError):
   print('已取消，未执行操作。' if language=='zh' else 'Cancelled; no operation started.');return 130
  except Exception as e:print('未开始：' if language=='zh' else 'Not started:',tr(e));return 1
  announce('start')
 previous=sys.argv;sys.argv=[spec[0]+'.py',*argv]
 try:
  # Argparse's built-in labels/errors are translated without changing report codes.
  original=argparse._
  argparse._=tr
  try:importlib.import_module(spec[0]).main()
  finally:argparse._=original
  if not help_only:announce('success')
  return 0
 except SystemExit as e:return e.code or 0
 except KeyboardInterrupt:
  print('用户中断；如已开始写入，请检查日志中的相机状态。' if language=='zh' else 'Interrupted; if writing started, inspect the camera state in the saved report.');return 130
 except Exception as e:
  announce('error');print(tr(e));return 1
 finally:sys.argv=previous
