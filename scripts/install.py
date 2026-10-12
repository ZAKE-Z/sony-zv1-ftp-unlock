"""Compatibility entry; waits for a key before installing."""
import os,sys
from operation_launcher import run
if __name__=='__main__':sys.exit(run('unlock',os.environ.get('ZV1_FTP_LANG','en')))
