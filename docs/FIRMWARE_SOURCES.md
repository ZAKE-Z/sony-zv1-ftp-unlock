# Donor firmware: download manually, extract locally

The source of each installed library was checked against the original firmware files and the saved, successfully used camera backup. The final FTP client is modified; extracting the raw library alone is not enough.

| Installed name | Donor model | Firmware | Name inside firmware | Preparation |
| --- | --- | --- | --- | --- |
| libInfraFtpClient.so | Sony a7 III (ILCE-7M3) | 4.01 | libInfraFtpClient.so | Apply resources/patches/ftp_client.json after extraction |
| libInfraCertificate.so | Sony a7C (ILCE-7C) | 2.00 | libInfraCertificate.so | Unmodified bytes |
| libcurl.so.4 | Sony a7C (ILCE-7C) | 2.00 | libcurl.so.4.7.0 | Unmodified bytes |
| libssh2.so.1 | Sony a7C (ILCE-7C) | 2.00 | libssh2.so.1.0.1 | Unmodified bytes |
| libnss_dns.so.2 | Sony a7C (ILCE-7C) | 2.00 | nflasha7: /lib/libnss_dns-2.11.2.so | Unmodified bytes; output runtime name selected automatically |

`libInfraCertificate.so` is byte-identical in a7C 2.00 and a7 III 4.01. This workflow consistently extracts it from a7C 2.00. The installed curl SONAME is `libcurl.so.4`; the source file is `libcurl.so.4.7.0`. **4.7.0 here is the library filename, not the camera firmware version.** Likewise ssh2 is extracted from `libssh2.so.1.0.1` and written locally as `libssh2.so.1`.

The DNS module is in system partition `nflasha7`; the other four libraries come from user partition `nflasha15`. Extraction reads both partitions and outputs only manifest-selected, hash-matched files. Its source name is `libnss_dns-2.11.2.so`, and its output/runtime name is `libnss_dns.so.2`; no manual copying or renaming is needed.

## Required downloads

Download these **Windows** installers manually:

1. **a7 III / ILCE-7M3, firmware 4.01:** [Update_ILCE7M3V401.exe](https://di.update.sony.net/IMT/Update_ILCE7M3V401.exe).
2. **a7C / ILCE-7C, firmware 2.00:** [Update_ILCE7CV200.exe](https://di.update.sony.net/IMT/Update_ILCE7CV200.exe).

These are the Sony-hosted historical URLs recorded for the original packages. Availability may change. Current Sony download pages may offer newer versions; **do not substitute newer firmware**, a macOS package, or firmware for a7C II/a7 III successors. If the exact historical package is unavailable, extraction cannot proceed; the project does not host a mirror.

Place both EXEs directly inside `firmware/`, next to its README. **No renaming is required.** Renamed EXEs are accepted when their contents match the recorded SHA-256; they must keep an `.exe` extension. One directory must contain both packages. To use another directory: `python scripts/en_1_extract_firmware.py --firmware-dir "C:\Downloads\Sony"`.

Package SHA-256:

- `Update_ILCE7M3V401.exe`: `ff33440ddf27d9eb6c5869789d396dce7401e8529d84b800c8fd8dd13ef6568f`
- `Update_ILCE7CV200.exe`: `801af0faed88ede1d46402297bf8e94b35ccb8fecd83d4b6b350c24cccaa5ce9`

## Run extraction

```powershell
python scripts/en_1_extract_firmware.py --check
python scripts/en_1_extract_firmware.py
```

`--check` checks the exact downloaded files without unpacking or accessing a camera. Normal extraction uses the bundled MIT-licensed fwtool source and standard Python crypto dependencies. It decrypts the firmware into temporary local files, reads only the needed libraries from the specified system/user partitions, validates internal model/version and original library hashes, applies the final FTP transfer patch, and validates all output hashes against `resources/catalog.json` before publishing files under `assets/`.

Only local files are read; no firmware is automatically downloaded, and no camera is accessed. Temporary decrypted images are closed/deleted by Python. About 1 GB of free temporary disk space is recommended. `assets/extraction.private.json` records the source evidence. EXEs, extracted libraries and evidence are ignored by Git. `en_2_unlock_ftp.py` automatically invokes extraction if any required library is missing.

Never run the donor firmware updaters against the ZV-1: they are inputs for extraction only. See `resources/firmware_sources.json` for machine-readable identities, exact hashes, and output names.
