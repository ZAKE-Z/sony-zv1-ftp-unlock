Place the two exact official Windows firmware EXEs here. See ../docs/FIRMWARE_SOURCES.md. Names can be changed; SHA-256 and internal model/version identify each package. Do not run these donor updaters against a ZV-1. Downloaded EXEs and extracted libraries are ignored by Git.

## Numbered language entries and startup confirmation

| Operation | English entry | Chinese entry |
| --- | --- | --- |
| 1 Extract firmware | en_1_extract_firmware.cmd | zh_1_提取固件.cmd |
| 2 Unlock FTP | en_2_unlock_ftp.cmd | zh_2_解锁FTP.cmd |
| 3 Restore firmware | en_3_restore.cmd | zh_3_还原.cmd |
| 4 Set reported version | en_4_set_firmware_version.cmd | zh_4_修改版本号.cmd |

Matching `.py` entries run with ordinary Python. The English-named `en_` and Chinese-named versions share the same logic, with different human-facing output languages.
The console first displays the selected action and arguments. A fresh key press starts it; Esc or closing the window cancels. Before that key, no dependency installation, firmware reading or camera access occurs. There is no confirmation-bypass flag; noninteractive input is refused. `--help` only displays help and does not require a key.
Steps 1 and 2 are the install path. Steps 3 and 4 are independent recovery actions; do not run all four in sequence. Double-click launchers also wait before closing after completion.
Project prompts, progress, errors and results use the selected language. Paths, hashes, property IDs and machine report codes stay stable; third-party pip output and raw low-level diagnostics retain their original text.

Additional on-camera result: after setting the reported version to 2.00 and reinstalling 2.01 with the official updater, the owner also needed an in-camera initialization for normal restoration. The version script does not run the official update or camera initialization.

## Folder layout and USB checkpoints

The root contains the eight CMD launchers, bilingual READMEs and FTP configuration files. All Python implementation and language entry files are under `scripts/`; CMD launchers invoke them automatically.
`resources/` holds manifests/patch data, `assets/` contains required helpers/local generated libraries, `docs/` contains detailed documentation, `firmware/` receives downloaded firmware, and `logs/` contains private operation records.
After a firmware-triggered reboot, a key checkpoint replaces the old fixed 8-second automatic continuation. Wait for the camera and USB to recover, then press a key for verification. A second checkpoint precedes server configuration, allowing USB to stabilize after exiting the service session. This configuration checkpoint also applies on reruns when firmware is already installed. Reconnect USB if needed; do not toggle FTP.
Esc only cancels future steps, retaining completed firmware changes. The new checkpoint sequence has offline checks and still needs on-camera validation.
