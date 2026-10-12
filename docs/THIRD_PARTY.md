# Third-party code and locally prepared resources

- `scripts/vendor/pmca`: Sony-PMCA-RE by ma1co, MIT; see `scripts/vendor/PMCA-LICENSE.txt`, https://github.com/ma1co/Sony-PMCA-RE .
- `scripts/vendor/fwtool`: Sony-Firmware-Tools by ma1co, based on earlier fwtool work by oz_paulb / nex-hack, MIT; see `scripts/vendor/FWTOOL-LICENSE.txt`, https://github.com/ma1co/Sony-Firmware-Tools . Vendored parser source is included, not Sony firmware. Two regex literals may be modernized for current Python compatibility.
- Python itself must be installed by the user. PyUSB, libusb-package, importlib_resources and PyCryptodome are installed through pip, not bundled. Their upstream licensing remains applicable.

No Sony firmware EXE or Sony-derived shared-library binary is distributed in this repository. `libInfraFtpClient.so`, `libInfraCertificate.so`, `libcurl.so.4` and `libssh2.so.1` are generated locally from exact user-supplied firmware; see `docs/FIRMWARE_SOURCES.md`. The final FTP client also uses the project's minimal patch plan. Generated binaries must not be added to Git or public releases. Do not infer any Sony binary redistribution permission from PMCA/fwtool MIT licenses.

No project-wide open-source license has been selected for original code.
