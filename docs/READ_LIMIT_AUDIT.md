# File read limit audit

This is an offline code/resource audit, not an on-camera test. All five operations and the auxiliary readers were inspected.

| Reader | Limit | Evidence / result |
| --- | --- | --- |
| Installation / restore: full system modules | 64 MiB | All captured supported module backups are smaller; maximum listed below |
| Uploaded patch/probe helpers | Actual file size + 1024 bytes | Sized from the exact helper blob, not a fixed 64 KiB cap |
| Restore: five added dependency libraries | 1 MiB | Largest dependency is 364820 bytes |
| Configuration: native cipher helper | Actual file size + 1024 bytes | Rebuilt 4636-byte helper; exact payload and hash are checked |
| Configuration: encrypted batch | 2048 bytes | 1024-byte expected output; final exact length also checked |
| Reported version record | 4096 bytes | Expected record is 2 bytes; record length checked |
| Firmware version string | 65536 bytes | Small exact firmware string, not a helper payload |
| Legacy MWF diagnostic | 2 MiB | Saved libMWF.so samples fit the limit; this main diagnostic is not an install entry |
| Local firmware extractor | No USB capture limit | 4 MiB reads are incremental SHA-256 chunks, not a complete-file maximum |

No further instances of the original helper-too-large-for-cap defect were found in the supported resources. Unknown/larger resources are not implicitly accepted; identity/hash checks remain. New firmware versions require a fresh audit. The receive adapter remains bounded and does not discard extra data to conceal an oversized response.

Machine-readable evidence: `../resources/read_limit_audit.json`. This audit does not prove that camera configuration writes or other hardware operations succeeded after the fix.
