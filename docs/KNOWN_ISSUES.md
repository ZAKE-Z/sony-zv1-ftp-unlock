# Known issues and verification scope

| Item | Status / limits |
| --- | --- |
| DNS / domains | Missing NSS DNS module added; native primary/secondary DNS enabled. Owner confirmed the page and FTP-domain connection/transfer on 2026-10-17. One camera/network only; not every router or manual-DNS editing combination is covered |
| Full factory restoration | Step 4 restore, in-camera initialization, official 2.01 reinstall after changing the reported version, or a combination may help, but each can leave changes or traces. Even reinstalling 2.01 does not guarantee an untouched state |
| Camera coverage | Previously successful FTP transfer on the owner's single ZV-1 only; no guarantee for other units or models |
| IP/port entry | May fail initially. The latest owner test found that one FTP connection attempt, even a failed attempt, allows subsequent in-camera IP editing; the reason is unknown. If it remains unusable, use `ftp_config.json` and step 3. Username/password entry worked; further input-page patching is deferred |
| Final menu | Single auto-transfer item and adjusted paging installed/verified as files in prior work; latest navigation still needs on-camera confirmation |
| New workflow | Actual extraction from both original packages passes and all five generated hashes match. Root install/restore/version workflow has only offline tests, not fresh on-camera end-to-end verification |
| Transfer / DISP | Earlier user tests passed connection, photo transfer and hiding the FTP icon. Does not cover all servers, RAW, FTPS or background transfer scenarios |
| Wired/wireless | Kept selectable by request; wired FTP on ZV-1 has not been demonstrated |
| Profile writing | The rebuilt helper wrote all nine slots with camera readback; FTP1 displayed 127.0.0.1:21 on 2026-10-12. Connection to a real server with this helper remains untested |
| Default slots | All nine default to 127.0.0.1:21; fill real server details before installing |
| USB / driver | Reconnection/authentication issues occurred historically. Scripts do not change Windows device drivers or camera USB mode |
| Restore | en_4_restore.py only supports stock or final hash-matched firmware, clears FTP settings, preserves Wi-Fi/USB settings and is not a factory reset. Unrecognized intermediate states are refused. New implementation not tested live |
| Version record | en_5_set_firmware_version.py only writes a verified 2.00 report record; official reinstall is a separate action, with no complete-reset guarantee |
| Power / channel loss | Ordinary failures have guarded rollback; lost USB or power can interrupt it. Preserve private logs for diagnosis, not for public upload |
| Donor availability | Exact historical Windows EXEs are required. Newer versions are rejected; historical Sony links may cease to work |

Report model, firmware, command and exact error without uploading passwords, complete logs, Backup.bin or Sony binaries.

Additional on-camera result: after setting the reported version to 2.00 and reinstalling 2.01 with the official updater, the owner also needed an in-camera initialization for normal restoration. The version script does not run the official update or camera initialization.

This release recognizes stock, the previous installation without DNS repair, and the current final hashes. Unknown modifications remain refused. The expanded restore has not been rerun on camera.
