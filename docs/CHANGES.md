# Scope of firmware modifications

[English](CHANGES.md) | [简体中文](CHANGES.zh-CN.md)

| File / scope | Purpose |
| --- | --- |
| CautionConfig.so | Opens FTP from the View on TV menu entry; unifies the menu and page count, removes duplicate items and the load/save configuration items |
| libObj.so | Deferred-initialization fix for the FTP / certificate clients |
| libInfraFtpClient.so | Verified donor build with photo buffer / transfer fixes |
| libInfraCertificate.so, libcurl.so.4, libssh2.so.1 | Required dependencies added for the current implementation |
| viewUnified2.so | The FTP icon follows the DISP display mode |
| libnss_dns.so.2 | Provide the missing NSS DNS backend used by getaddrinfo for FTP domains |
| viewUnified4.so | Buffer protection for address/port commits (not a confirmed standalone fix); enable native Wi-Fi DNS display/edit/save/navigation |
| FTP-related in-camera setting records | Nine slots updated from the configuration file; unspecified credentials and unrelated settings are preserved |

Source files, target files, offsets, and hashes are defined by `resources/catalog.json`. The whole `Backup.bin` is never replaced; no default configuration for third-party tethered-shooting software is written; Wi-Fi and USB default settings are untouched. `libSysDef.so` is used for verification only — the early inhibit-table experiment patches are not reused.
