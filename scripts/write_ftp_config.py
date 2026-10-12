"""Update nine FTP profiles without modifying firmware files."""
from pathlib import Path
import argparse, json
from ui_language import print, tr, announce
import zv1_ftp as core


def main():
    p = argparse.ArgumentParser(description=tr('单独写入或更新 FTP1–FTP9 配置'))
    p.add_argument('--config', type=Path, default=core.ROOT/'ftp_config.json')
    p.add_argument('--validate', action='store_true', help=tr('只检查配置文件和本地资源，不访问相机'))
    p.add_argument('--check', action='store_true', help=tr('只读核验相机已安装 FTP 固件'))
    p.add_argument('--verify', action='store_true', help=tr('只读核验机内 FTP 配置'))
    args = p.parse_args()
    if sum((args.validate, args.check, args.verify)) > 1:
        p.error(tr('检查模式一次只能选择一个'))
    if args.config == core.ROOT/'ftp_config.json' and not args.config.exists():
        raise FileNotFoundError(tr('请先复制 ftp_config.example.json 为 ftp_config.json 并填写服务器'))
    config = core.load_configuration(args.config)
    catalog = json.loads((core.ROOT/'resources/catalog.json').read_text(encoding='utf-8'))
    cipher = (core.ROOT/'assets/config_cipher.elf').read_bytes()
    if len(cipher) != catalog['config_cipher']['bytes'] or core.sha(cipher) != catalog['config_cipher']['sha256']:
        raise RuntimeError(tr('配置加密工具校验失败'))
    if args.validate:
        print('PASS_CONFIG_LOCAL_VALIDATION：FTP1–FTP9 配置有效，未连接相机。')
        return
    from setup_environment import ensure_environment
    ensure_environment()
    firmware_check = argparse.Namespace(
        runtime_root=str(core.ROOT/'scripts/support'), check=True, verify=True,
        skip_local_assets=True)
    print('配置已读取：FTP1–FTP9。开始核验相机。')
    if args.check:
        core.run(firmware_check)
        return
    announce('config')
    core.configure_camera(firmware_check, config, verify=args.verify)
    print('配置操作完成。拔下 USB 后检查相机 FTP 服务器设置。')


if __name__ == '__main__':
    from operation_launcher import run
    import os, sys
    sys.exit(run('config', os.environ.get('ZV1_FTP_LANG','en')))
