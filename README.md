# Simple Transfer Enhanced

跨平台文件传输工具，支持局域网设备发现、拖拽传输、批量传输、断点续传。

## ✨ 功能特性

- 🔍 **设备发现** - 自动发现同网段设备，支持手动添加跨网段 IP
- 📁 **拖拽传输** - 支持拖拽文件到窗口传输
- 📋 **批量传输** - 支持多文件排队传输
- ⏸️ **断点续传** - 网络中断后可继续传输
- 📊 **实时进度** - 显示传输速度、剩余时间
- 📜 **传输历史** - 记录最近 50 条传输历史
- ❌ **取消传输** - 随时取消正在进行的传输
- 🔄 **错误重试** - 网络失败自动重试 3 次

## 📥 下载

| 平台 | 下载 |
|------|------|
| 🐧 Linux | [simple-transfer-enhanced-linux](./dist/SimpleTransferEnhanced-linux) |
| 🪟 Windows | [Download Windows ZIP](https://github.com/sudowrx/simple-transfer/releases) |
| 🍎 macOS | [Download macOS ZIP](https://github.com/sudowrx/simple-transfer/releases) |

## 🚀 使用方法

### Linux
```bash
chmod +x SimpleTransferEnhanced-linux
./SimpleTransferEnhanced-linux
```

### Windows
下载 zip 解压后双击 `SimpleTransferEnhanced.exe` 运行

### macOS
下载 zip 解压后双击 `SimpleTransferEnhanced.app` 运行

## 🔧 从源码运行

需要 Python 3.8+ 和 tkinter

```bash
python3 simple-transfer-enhanced.py
```

## 📋 环境要求

- Python 3.8+
- tkinter (GUI)
- 同一局域网内的设备

## 📝 协议

MIT License
