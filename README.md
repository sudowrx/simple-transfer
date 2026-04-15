# Simple Transfer Enhanced

Cross-platform file transfer tool with LAN device discovery, drag-and-drop, batch transfer, and resume support.

## ✨ Features

- 🔍 **Device Discovery** - Auto-discover devices on LAN, support manual cross-subnet IP
- 📁 **Drag & Drop** - Drag files directly into the window to transfer
- 📋 **Batch Transfer** - Queue multiple files for sequential transfer
- ⏸️ **Resume Transfer** - Resume interrupted transfers after network failure
- 📊 **Real-time Progress** - Live speed display and ETA
- 📜 **Transfer History** - Keep last 50 transfer records
- ❌ **Cancel Transfer** - Cancel ongoing transfers anytime
- 🔄 **Auto Retry** - Network failures auto-retry 3 times

## 📥 Downloads

| Platform | Download |
|----------|----------|
| 🐧 Linux | [simple-transfer-enhanced-linux](./dist/SimpleTransferEnhanced-linux) |
| 🪟 Windows | [Download Windows ZIP](https://github.com/sudowrx/simple-transfer/releases) |
| 🍎 macOS | [Download macOS ZIP](https://github.com/sudowrx/simple-transfer/releases) |

## 🚀 Quick Start

### Linux
```bash
chmod +x SimpleTransferEnhanced-linux
./SimpleTransferEnhanced-linux
```

### Windows
Download the zip, extract, and double-click `SimpleTransferEnhanced.exe`

### macOS
Download the zip, extract, and double-click `SimpleTransferEnhanced.app`

## 🔧 Run from Source

Requires Python 3.8+ and tkinter

```bash
python3 simple-transfer-enhanced.py
```

## 📋 Requirements

- Python 3.8+
- tkinter (GUI)
- Devices on the same LAN

## 📝 License

MIT License
