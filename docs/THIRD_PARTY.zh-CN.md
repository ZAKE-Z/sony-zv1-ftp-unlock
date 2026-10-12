# 第三方与本地资源

PMCA 与 fwtool 是 ma1co 的开源项目，保留 MIT 许可于 `scripts/vendor/PMCA-LICENSE.txt`、`scripts/vendor/FWTOOL-LICENSE.txt`。fwtool 基于早期 oz_paulb／nex-hack 工作，本项目仅包含开源解析代码，不包含索尼固件。

Python 由用户自行安装，PyUSB、libusb-package、importlib_resources、PyCryptodome 由 pip 获取，不在仓库打包。

索尼相关的四个库由用户手动下载的指定固件在本地提取，其中 FTP 客户端还需应用本项目补丁。仓库和公开 Release 不发布这些生成的二进制库，也不发布完整固件。不要把 PMCA/fwtool 的 MIT 许可理解为索尼库的再分发授权。详见 [固件来源](docs/FIRMWARE_SOURCES.zh-CN.md)。

原创代码尚未选择项目级开源许可证。
