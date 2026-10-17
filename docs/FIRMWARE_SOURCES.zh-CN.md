# 固件下载与库来源

| 最终库 | 来源机型／固件 | 固件内的原文件 | 处理 |
| --- | --- | --- | --- |
| libInfraFtpClient.so | a7 III（ILCE-7M3）4.01 | libInfraFtpClient.so | 提取后应用最终传输修复补丁，再校验 |
| libInfraCertificate.so | a7C（ILCE-7C）2.00 | libInfraCertificate.so | 原样；与 a7 III 4.01 同名库逐字节一致 |
| libcurl.so.4 | a7C 2.00 | libcurl.so.4.7.0 | 原样，输出名改为安装使用的 SONAME |
| libssh2.so.1 | a7C 2.00 | libssh2.so.1.0.1 | 原样，输出名改为安装使用的 SONAME |
| libnss_dns.so.2 | a7C（ILCE-7C）2.00 | nflasha7: /lib/libnss_dns-2.11.2.so | 原样，按运行时名称输出；无须手动重命名 |

来源根据本项目原始固件与曾成功工作的备份逐一核对，不根据旧文档猜测。`4.7.0` 是 curl 文件名中的版本，不是 a7C 固件版本。原版 FTP 库与最终修正版的哈希不同，脚本负责生成最终修正版。

DNS 模块来自系统分区 `nflasha7`，其余四个库来自用户分区 `nflasha15`。提取脚本会读取这两个分区，只输出清单规定且哈希匹配的文件。模块源名是 `libnss_dns-2.11.2.so`，输出名是 `libnss_dns.so.2`；不需要手动复制或重命名。

## 手动下载

- [a7 III 4.01：Update_ILCE7M3V401.exe](https://di.update.sony.net/IMT/Update_ILCE7M3V401.exe)
- [a7C 2.00：Update_ILCE7CV200.exe](https://di.update.sony.net/IMT/Update_ILCE7CV200.exe)

这是当时保存的索尼服务器直链，不能保证历史文件永久可下载。当前官方页面可能只提供更新版本，不能用更新版本或其他机型／macOS 包替代。若拿不到指定原包，脚本会停止；本项目不提供固件镜像。

把两份 Windows `.exe` 放到根目录的 `firmware/` 文件夹，**无需改名**。即使改名，只要保留 `.exe` 后缀且完整文件哈希符合要求也可以。不要只修改其他版本的文件名来冒充指定版本。

```powershell
python scripts/zh_1_提取固件.py --check
python scripts/zh_1_提取固件.py
```

也可双击根目录“zh_1_提取固件.cmd”。使用其他文件夹时：`python scripts/zh_1_提取固件.py --firmware-dir "D:\固件下载"`。

原包 SHA-256：

- `Update_ILCE7M3V401.exe`: `ff33440ddf27d9eb6c5869789d396dce7401e8529d84b800c8fd8dd13ef6568f`
- `Update_ILCE7CV200.exe`: `801af0faed88ede1d46402297bf8e94b35ccb8fecd83d4b6b350c24cccaa5ce9`

脚本用开源 fwtool 解密与解析指定系统／用户分区，仅提取需要的库；验证内部机型、固件版本和原始库，再应用 FTP 客户端的最终补丁。五库均匹配最终 catalog 哈希后才输出到 `assets/`。建议临时磁盘至少有 1 GB 空间。生成的库和来源记录、下载固件均不会提交到 Git。

**不要对 ZV-1 运行这些供体升级程序**，它们只是本地提取的输入。刷写脚本检测缺库时会自动调用同一提取流程，不自动下载固件、不上传固件。
