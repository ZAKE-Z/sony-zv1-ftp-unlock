"""Install normal Python dependencies, without a bundled Python runtime."""
from ui_language import print
from pathlib import Path
import importlib, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
GROUPS={
 'crypto': [('Cryptodome.Cipher.AES','pycryptodomex>=3.20,<4')],
 'usb': [('usb.core','pyusb>=1.3,<2'),('libusb_package','libusb-package>=1.0.26,<2'),('Cryptodome.Cipher.AES','pycryptodomex>=3.20,<4')],
}
def ensure_environment(group='usb'):
 if sys.version_info<(3,10):raise RuntimeError('Python 3.10 or newer is required; Python 3.12 is recommended.')
 missing=[]
 for module,requirement in GROUPS[group]:
  try:importlib.import_module(module)
  except ImportError:missing.append(requirement)
 if missing:
  print('Installing Python dependencies:',', '.join(missing),flush=True)
  cmd=[sys.executable,'-m','pip','install']
  if sys.prefix==sys.base_prefix:cmd.append('--user')
  subprocess.run(cmd+missing,check=True)
  # Newly created user-site directories need adding in the same process.
  import site
  site.addsitedir(site.getusersitepackages());importlib.invalidate_caches()
 for module,_ in GROUPS[group]:importlib.import_module(module)
 for folder in ['vendor','support']:
  path=str(ROOT/'scripts'/folder)
  if path not in sys.path:sys.path.insert(0,path)
if __name__=='__main__':
 ensure_environment();print('PASS_PYTHON_ENVIRONMENT_READY; camera not accessed')
