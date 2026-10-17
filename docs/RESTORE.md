# Recovery options and limits

There are several ways to try to undo the FTP changes, but none is proven to return every file and setting to an untouched factory state.

1. Run `python scripts/en_4_restore.py --check` for a read-only preflight, then `python scripts/en_4_restore.py` to restore supported stock file bytes, remove only hash-matched added libraries, and clear FTP settings. Wi-Fi and USB settings are preserved. Unknown intermediate firmware states are refused. Private backups and a report are saved under `logs/restore-*`. The script checks the result before reboot; a post-reboot live-memory check is not claimed. The new restore path has not been tested on camera.
2. Use the camera's own initialization if appropriate. Earlier owner testing found that initialization was needed after an official 2.01 reinstall to return to normal operation, but it did not prove that all FTP configuration or modification traces were removed.
3. The optional `python scripts/en_5_set_firmware_version.py` changes only the reported record to 2.00. The owner can then run Sony's official ZV-1 2.01 updater separately. The script itself neither reinstalls firmware nor removes patches. Never run either donor-model updater on the ZV-1.

These methods may be combined, yet an official reinstall of 2.01 can still leave detectable changes. Do not rely on any of them as a complete factory restoration. Keep private backups and reports until you have checked the camera's behavior.

The DNS release removes only the hash-matched `/usr/lib/libnss_dns.so.2` and restores stock viewUnified4 by undoing both the DNS-page gate and existing input patches. The previous known installation without DNS repair is also accepted. Wi-Fi settings, including manual DNS values, are retained. No earlier experimental DNS-setting script or forced DNS default is used.
