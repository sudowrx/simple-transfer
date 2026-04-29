# Simple Transfer Enhanced

**跨平台局域网文件传输工具**

✨ 特性 | 📥 下载 | 🚀 使用 | 🔧 构建 | 📝 协议

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🔍 **设备自动发现** | 自动发现同局域网在线设备 |
| 🔎 **网络扫描** | 支持自定义超时扫描整个网段 |
| 📁 **拖拽传输** | 直接拖拽文件到窗口即可传输 |
| 📋 **批量传输** | 多文件自动排队传输 |
| ⏸️ **断点续传** | 网络中断后可继续传输 |
| 📊 **实时进度** | 显示传输速度、剩余时间 |
| 📜 **传输历史** | 记录最近 50 条传输记录 |
| 🕐 **IP 历史** | 常用 IP 自动保存，一键选择 |
| 🌐 **多语言** | 支持中文和英文，APP 内实时切换 |
| ❌ **取消传输** | 随时取消正在进行的传输 |
| 🔄 **错误重试** | 网络失败自动重试 3 次 |

---

## 📥 下载

| 平台 | 文件 | 说明 |
|------|------|------|
| 🐧 Linux | [SimpleTransferEnhanced](./dist/SimpleTransferEnhanced) | 执行 `chmod +x && ./SimpleTransferEnhanced` |
| 🪟 Windows | [SimpleTransferEnhanced.exe](https://github.com/sudowrx/simple-transfer/releases) | 下载后双击运行 |
| 🍎 macOS | [SimpleTransferEnhanced-macos.zip](https://github.com/sudowrx/simple-transfer/releases) | 下载解压后双击运行 |

---

## 🚀 快速开始

### Linux

```bash
# 下载并赋予执行权限
chmod +x SimpleTransferEnhanced
./SimpleTransferEnhanced
```

### Windows

1. 下载 `SimpleTransferEnhanced.exe`
2. 双击运行（无需安装）

### macOS

1. 下载并解压 `SimpleTransferEnhanced-macos.zip`
2. 双击 `SimpleTransferEnhanced.app`
3. 首次运行需在「系统设置 → 隐私与安全性」允许运行

---

## 📖 使用指南

### 发现设备

应用启动后自动扫描同网段设备，也可用「扫描网络」功能手动扫描。

### 添加设备

- **同网段设备**：自动发现列表中直接点击选择
- **跨网段设备**：在 IP 输入框输入目标 IP，点击「添加」

### 传输文件

1. 选择目标设备
2. 点击「选择文件」或直接拖拽文件到窗口
3. 等待传输完成

### 语言切换

点击窗口右上角语言下拉框，可实时切换中/英文界面。

---

## 🔧 从源码运行

### 环境要求

- Python 3.8+
- tkinter

### 运行

```bash
# 克隆项目
git clone https://github.com/sudowrx/simple-transfer.git
cd simple-transfer

# 安装依赖
pip install pyinstaller

# 直接运行
python3 simple-transfer-enhanced.py

# 或打包为可执行文件
pyinstaller --onefile --windowed --name SimpleTransferEnhanced simple-transfer-enhanced.py
```

---

## 🗂️ 项目结构

```
simple-transfer/
├── simple-transfer-enhanced.py    # 主程序
├── dist/                          # 构建输出目录
│   └── SimpleTransferEnhanced     # Linux 可执行文件
├── build/                         # PyInstaller 构建缓存
├── .github/
│   └── workflows/
│       └── build.yml              # CI/CD 构建流程
├── README.md                      # 英文说明
├── README_zh.md                   # 中文说明
└── FEATURES_IMPLEMENTATION.md     # 功能实现详情
```

---

## 🌐 多语言支持

应用支持以下语言：

| 语言代码 | 语言 |
|----------|------|
| `zh` | 简体中文 |
| `en` | English |

语言偏好保存在 `~/.simple_transfer_config.json`

---

## 📝 协议

MIT License

---

## 🙏 致谢

基于 [Simple Transfer](https://github.com/sudowrx/simple-transfer) 开发
