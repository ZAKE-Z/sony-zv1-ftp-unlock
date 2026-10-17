# sony-zv1-ftp-unlock

English | [简体中文](README.zh-CN.md)

Unlocks FTP on a Sony ZV-1 by replacing **View on TV** and applying initialization, transfer, menu and icon patches. A separate script writes FTP1–FTP9 from JSON.

**Experimental, tested on one owner's camera only. There is currently no proven way to return every setting and file to a perfectly untouched factory state. Firmware reinstall, camera initialization and this project's restore operation can each leave detectable changes. Use with care and only if you accept that limitation.** Supported firmware: `29114_04.2021031701`. Earlier revisions connected and transferred photos successfully; the latest menu/input changes and the refactored install/restore/version workflows do not have complete on-camera validation. See [known issues](docs/KNOWN_ISSUES.md).


## DNS repair (2026-10-17)

FTP domain-name resolution and the native Wi-Fi DNS fields were confirmed working by the owner after this repair on ZV-1 2.01.

- Unlock now adds the missing `libnss_dns.so.2` resolver module, extracted from the **a7C 2.00** system partition. ZV-1 and this donor have byte-identical libc/libresolv. The firmware downloads are unchanged; no Sony libraries are shipped in this repository.
- The Wi-Fi access-point IP settings page now includes primary/secondary DNS using the existing native display, editing, save and navigation paths. Automatic IP follows the native automatic-DNS behavior; manual IP offers DNS entry. No fixed DNS addresses or Wi-Fi profiles are written by the installer.
- **Existing users:** keep both exact donor EXEs in `firmware/`, rerun entry **1**, then **2**. The previous hash-matched FTP installation upgrades without clearing server profiles. Entry **3** is needed only to change FTP server configuration.
- Entry **4** supports both the previous and current installations, restores the stock UI and removes the added DNS module along with the other added libraries. It clears FTP configuration and retains Wi-Fi settings, including any DNS values you entered; it is not a full factory reset.

The owner's DNS-page and FTP-domain/transfer confirmation covers one camera and network. Fresh stock-to-final installation and the expanded restore paths have offline tests; they have not each been rerun end-to-end on a freshly reset camera. [DNS details](docs/DNS.md).

## Prepare

1. Install ordinary **64-bit Python 3.10+** (3.12 recommended), with Python available on PATH. There is no bundled `runtime/python.exe` or `site-packages/`. Entry scripts install missing dependencies with the same interpreter's pip. You can instead run `python -m pip install -r scripts/requirements.txt`, or `python scripts/setup_environment.py`.
2. Manually download **a7 III 4.01** and **a7C 2.00** Windows firmware installers into `firmware/`. Names do not need changing; contents must match the recorded hashes. [Exact sources, download links, hashes and extraction instructions](docs/FIRMWARE_SOURCES.md).
3. Run `python scripts/en_1_extract_firmware.py`. If required libraries are missing, the unlock script invokes this same local extraction automatically. Firmware is never downloaded automatically, and Sony library binaries are not distributed in this repository.
4. Before running step 3, copy `ftp_config.example.json` to `ftp_config.json`, and edit all nine slots. Defaults are `127.0.0.1:21`, not a usable computer/server destination. Omit optional `username`/`password` to retain stored values, or set empty strings to clear them. Step 3 writes all nine slots; `selected_slot: null` preserves a valid selected slot, otherwise selects FTP1.
5. Connect exactly one powered-on ZV-1 in **Mass Storage** mode using the already working USB service driver. Python dependency setup does not install or change Windows device drivers. Windows service access may need a WinUSB/libusb-compatible driver; bind only the appropriate camera interface, not arbitrary devices.

## Root CMD entries

| Operation | Command | Windows double-click |
| --- | --- | --- |
| Extract donor libraries | `python scripts/en_1_extract_firmware.py` | en_1_extract_firmware.cmd |
| Unlock FTP firmware | `python scripts/en_2_unlock_ftp.py` | en_2_unlock_ftp.cmd |
| Write or update nine FTP profiles | `python scripts/en_3_write_config.py` | en_3_write_config.cmd |
| Restore supported stock firmware files | `python scripts/en_4_restore.py` | en_4_restore.cmd |
| Set reported version to 2.00 | `python scripts/en_5_set_firmware_version.py` | en_5_set_firmware_version.cmd |

Python implementations live under `scripts/`; root CMD entries call them. No private local directory is required.

Read-only checks: step 2 `--validate` checks local patch resources, `--check` checks camera firmware, and `--verify` checks installed FTP firmware. Step 3 `--validate` checks `ftp_config.json` and its helper without accessing the camera; `--check` verifies the installed firmware, and `--verify` checks stored FTP profiles. Steps 4 and 5 support `--check`. `--help` never accesses a camera. Step 3 accepts `--config PATH` for a different JSON file.

The tool does not enable FTP or alter Wi-Fi/USB settings. The wired/wireless option remains selectable; ZV-1 wired FTP has not been validated. Load/save configuration and duplicate auto-transfer menu entries are removed in the final menu patch. Earlier user feedback confirmed photo transfer and the FTP icon following DISP **No Disp. Info.**.

## Restore and reported version

`en_4_restore.py` restores the four known modified system files to their stock byte spans and removes the four hash-matched added dependencies. It rejects unknown/older intermediate modified states. FTP profiles, credentials, switches and cache are reset; Wi-Fi/USB settings are preserved; it is **not a factory settings reset**. Files are backed up and checked before writing, then read back and rebooted. The new restore path has offline checks but has not been tested on a camera. A lost USB channel or power loss can leave a partial operation; inspect the saved report.

`en_5_set_firmware_version.py` only changes `/setting/updater/dat4` from a recognized 2.00/2.01 record to 2.00. It does not downgrade, reinstall firmware or remove patches. Possible recovery routes include step 4, in-camera initialization, and changing the reported version before a separate official reinstall of 2.01. They may be combined, but even an official reinstall may leave changes or traces. None guarantees a return to a completely untouched factory state. This project does not run the official updater or camera initialization. The version script has not been verified live; it checks firmware identity, record length and readback, and saves originals.

## Known limitations and privacy

After FTP is first enabled, entering or confirming the server IP address and port on the camera may fail. The latest owner test found a workaround: attempt to connect to an FTP server once. Even if that connection attempt fails, the IP address can then be edited on the camera. The reason is not yet understood; further input-page patching is deferred. If entry remains unusable, edit `ftp_config.json` and run step 3 to write the server address and port. In-camera username and password entry worked in earlier tests. Keep other camera modification programs closed.

`logs/` contains original firmware and private settings; never upload it. Downloaded EXEs and locally generated Sony libraries are Git-ignored. No Sony firmware/library binary, Python runtime, personal configuration or old reverse-engineering dump is included in the rebuilt repository.

## Documents and checks

- [Firmware sources](docs/FIRMWARE_SOURCES.md)
- [Known issues](docs/KNOWN_ISSUES.md)
- [Changes](docs/CHANGES.md)
- [Third-party code](docs/THIRD_PARTY.md)

Run `python -m unittest discover -s tests -v` for offline checks. Local extraction was tested against the original downloaded packages; this does not prove refactored camera-writing workflows work end-to-end. Native patch helpers are included, with available sources under `scripts/native/` and minimal FTP library patch data under `resources/patches/`.

The camera owner leads practical validation, with AI assistance for analysis, code and documentation. Original project code has no open-source license selected; vendored PMCA/fwtool retain their MIT licenses.

## Numbered language entries and startup confirmation

| Operation | English entry | Chinese entry |
| --- | --- | --- |
| 1 Extract firmware | en_1_extract_firmware.cmd | zh_1_提取固件.cmd |
| 2 Unlock FTP | en_2_unlock_ftp.cmd | zh_2_解锁FTP.cmd |
| 3 Write FTP configuration | en_3_write_config.cmd | zh_3_写入配置.cmd |
| 4 Restore firmware | en_4_restore.cmd | zh_4_还原.cmd |
| 5 Set reported version | en_5_set_firmware_version.cmd | zh_5_修改版本号.cmd |

Matching `.py` entries under `scripts/` run with ordinary Python. The English-named `en_` and Chinese-named versions share the same logic, with different human-facing output languages.
The console first displays the selected action and arguments. A fresh key press starts it; Esc or closing the window cancels. Before that key, no dependency installation, firmware reading or camera access occurs. There is no confirmation-bypass flag; noninteractive input is refused. `--help` only displays help and does not require a key.
Steps 1 and 2 install FTP. Step 3 updates server profiles and can be rerun later without reinstalling FTP. Steps 4 and 5 are independent recovery actions; do not run all five in sequence. Double-click launchers also wait before closing after completion.
Project prompts, progress, errors and results use the selected language. Paths, hashes, property IDs and machine report codes stay stable; third-party pip output and raw low-level diagnostics retain their original text.

Additional on-camera result: after setting the reported version to 2.00 and reinstalling 2.01 with the official updater, the owner also needed an in-camera initialization for normal restoration. The version script does not run the official update or camera initialization.

## Folder layout and USB checkpoints

The root contains the ten CMD launchers, bilingual READMEs and FTP configuration files. All Python implementation and language entry files are under `scripts/`; CMD launchers invoke them automatically.
`resources/` holds manifests/patch data, `assets/` contains required helpers/local generated libraries, `docs/` contains detailed documentation, `firmware/` receives downloaded firmware, and `logs/` contains private operation records.
After a firmware-triggered reboot, a key checkpoint replaces the old fixed 8-second automatic continuation. Wait for the camera and USB to recover, then press a key for verification. Step 3 is a separate action. Wait for the camera to recover and reconnect USB before running it. It can be rerun to change server details without touching firmware files. Reconnect USB if needed; do not toggle FTP.
Esc only cancels future steps, retaining completed firmware changes. The new checkpoint sequence has offline checks and still needs on-camera validation.

Restoration now resets all nine FTP profiles, credentials, directories, related switches and cache to validated unused native defaults, even if firmware files are already stock. It never replaces Backup.bin. Values are privately backed up and read back; the new clearing path still needs an on-camera test. A specifically recognized disconnect after verification and the reboot request is recorded as reboot disconnect, not restore failure; post-reboot verification is not claimed.

Configuration helper: a previous 149108-byte build caused an illegal instruction on the camera before any configuration property was written. The locally rebuilt 4636-byte helper uses the compilation and link settings of an earlier successful on-camera helper. The script now verifies installed firmware and writes settings within one USB service session, since a second immediate session returned zero cameras. On 2026-10-12 the nine-slot write completed with on-camera readback, and the owner confirmed FTP1 displays 127.0.0.1:21. Connection to a real server using this rebuilt helper remains untested.
