# FTP domain names and Wi-Fi DNS

ZV-1 2.01 lacks the NSS DNS backend used by the installed FTP client's `getaddrinfo` calls. A valid nameserver in `/etc/resolv.conf` alone was insufficient: the owner camera's native probe could not load `libnss_dns.so.2`. a7C 2.00 includes it and has byte-identical libc and libresolv.

Entry 1 now extracts `/lib/libnss_dns-2.11.2.so` from a7C **2.00**, partition `nflasha7`, and saves it locally as `assets/libnss_dns.so.2`. Entry 2 installs it under `/usr/lib/`, verifies the native-library hashes, and checks that a fresh native process can load the module and find its DNS backend entry point. The installer reboots after changes so the camera process does not retain a previous module-load failure.

The access-point page already has the DNS controls and corresponding editor/save/navigation code. Entry 2 enables that native branch in `viewUnified4.so`, preserving the existing input protection. In-camera automatic IP uses the native automatic-DNS behavior; the manual-IP page offers primary and secondary DNS. This does not add independent manual DNS while IP remains automatic. No DNS addresses, SSIDs, passwords or IP modes are written by the installer.

## Existing installation

Keep the exact a7 III 4.01 and a7C 2.00 Windows EXEs in `firmware/`, then rerun entries **1 → 2**. The previous known FTP installation only needs the additional four-byte UI patch and missing library; the existing FTP server profiles are retained. Run entry 3 only if server details need changing. There is no separate DNS-configuration script.

The root CMD numbering remains 1 extraction, 2 unlock, 3 FTP configuration, 4 restore and 5 version record, in both languages.

## Restore and verification limits

Entry 4 recognizes the previous installation and this DNS release. It restores stock viewUnified4, removes the hash-matched DNS module and other added libraries, and clears FTP configuration. Wi-Fi settings, including DNS values entered by the user, are retained. Full factory restoration remains unproven.

On **2026-10-17**, file hashes, unchanged FTP settings, automatic-IP/DNS settings and native module loading were verified after reboot. The owner then confirmed success after being asked to check the DNS fields and connect/transfer a photo using the original FTP domain. This covers that camera and network, not all resolvers, domains, routers or manual-DNS editing combinations. The combined fresh-install and expanded restore paths have offline coverage but were not separately repeated from a newly reset camera.

Installer module-load verification does not itself test DHCP delivery, DNS queries or FTP connectivity. If a domain still fails, keep the exact error and use the read-only entry-2 `--check`/`--verify` modes for diagnostics. Do not post private logs, Wi-Fi/FTP credentials or firmware binaries.

## Files

Source identities and hashes are in `resources/firmware_sources.json` and `resources/catalog.json`. The DNS module is never distributed by this repository. Custom ARM helpers are project code; sources are in `scripts/native/`. They use ARM Linux EABI/soft-float, the old camera libc ABI, and were built with Zig 0.13.0; users do not need a compiler for installation.
