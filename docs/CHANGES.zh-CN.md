# 固件修改范围

[English](CHANGES.md) | 简体中文

| 文件／范围 | 目的 |
| --- | --- |
| CautionConfig.so | 从在电视上观看（View on TV）菜单入口打开 FTP；统一菜单与页数，移除重复项及加载／保存配置项 |
| libObj.so | FTP／证书客户端延迟初始化修正 |
| libInfraFtpClient.so | 采用已核实的供体版本，含照片缓冲／传输修正 |
| libInfraCertificate.so、libcurl.so.4、libssh2.so.1 | 为当前实现补齐必需依赖 |
| viewUnified2.so | FTP 图标跟随 DISP 显示模式 |
| libnss_dns.so.2 | 补齐 getaddrinfo 所需的 NSS DNS 模块，支持 FTP 域名解析 |
| viewUnified4.so | 地址／端口提交的缓冲保护（未证实单独根治）；启用原生 Wi-Fi DNS 显示、编辑、保存及导航分支 |
| FTP 相关机内设置记录 | 按配置文件更新九个槽位；保留未指定的账号密码及无关设置 |

源文件、目标文件、偏移与哈希以 `resources/catalog.json` 为准。不替换整份 `Backup.bin`；不写入任何第三方联机拍摄软件的默认配置；不修改 Wi-Fi、USB 默认设置。`libSysDef.so` 仅用于校验，不沿用早期的 inhibit 表试验补丁。
