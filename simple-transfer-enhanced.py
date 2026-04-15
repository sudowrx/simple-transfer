#!/usr/bin/env python3
"""
简单文件传输工具 - 零依赖跨平台版本（增强版）
兼容 Windows、macOS、Linux
支持跨网段手动输入 IP

增强功能：
1. 传输速度显示（MB/s、KB/s、B/s）
2. 剩余时间估算
3. 传输历史记录保存
4. 取消传输功能
5. 断点续传支持
6. 批量文件传输
7. 错误处理和重试机制
8. 跨网段自动发现优化
"""

import os
import sys
import socket
import threading
import time
import json
import struct
import hashlib
from pathlib import Path
from datetime import datetime

# 尝试导入 tkinter
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except ImportError:
    print("错误: 未找到 tkinter，请安装 Python-tk")
    sys.exit(1)

# 常量
DISCOVERY_PORT = 45678
TRANSFER_PORT = 45679
BUFFER_SIZE = 65536  # 64KB
BROADCAST_INTERVAL = 3  # 秒
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒
HISTORY_FILE = os.path.expanduser("~/.simple_transfer_history.json")
MAX_HISTORY = 50
IP_HISTORY_FILE = os.path.expanduser("~/.simple_transfer_ip_history.json")
CONFIG_FILE = os.path.expanduser("~/.simple_transfer_config.json")
MAX_IP_HISTORY = 20

# ==================== 多语言支持 ====================

current_lang = "zh"  # Default to Chinese

LANGUAGES = {
    "zh": {
        "window_title": "简单文件传输 (增强版 - 支持跨网段)",
        "local_name": "本机名称:",
        "ip_label": "IP:",
        "save_dir": "保存目录:",
        "browse": "浏览...",
        "online_devices": "在线设备:",
        "manual_add": "跨网段手动添加设备",
        "ip": "IP:",
        "name": "名称:",
        "add": "添加",
        "remove_selected": "移除选中",
        "scan_network": "扫描网络",
        "select_file": "选择文件:",
        "select_files": "选择多个...",
        "send": "发送 →",
        "cancel": "取消",
        "view_history": "查看历史",
        "progress": "进度:",
        "speed": "速度:",
        "remaining": "剩余:",
        "log": "日志:",
        "manual_device": "手动",
        "scan_device": "扫描发现",
        "select_target": "请选择目标设备",
        "select_file_warning": "请先选择文件",
        "input_ip": "请输入 IP 地址",
        "invalid_ip": "IP 地址格式不正确",
        "added_device": "已添加设备:",
        "removed_device": "已移除设备:",
        "only_remove_manual": "只能移除手动添加的设备",
        "scan_progress": "扫描进度:",
        "scan_complete_found": "扫描完成，发现",
        "scan_complete_none": "扫描完成，未发现设备",
        "discovered_device": "发现设备:",
        "scanning_network": "扫描网络:",
        "no_transfer": "没有正在进行的传输",
        "transfer_history": "传输历史",
        "no_history": "暂无传输记录",
        "select_multiple_files": "选择文件（支持多选）",
        "selected_files": "个文件:",
        "batch_transfer_complete": "批量传输完成",
        "sending": "正在发送",
        "send_failed": "发送失败:",
        "service_started": "已启动，保存目录:",
        "cross_subnet_hint": "提示: 跨网段传输请在左侧手动输入对方 IP",
        "receiving_service": "接收服务已启动，端口:",
        "start_receive_failed": "启动接收服务失败:",
        "connection_from": "来自",
        "connection": "的连接",
        "receiving_file": "接收文件:",
        "resume_from": "[断点续传从",
        "transfer_cancelled": "传输被取消",
        "saving_to": "保存到:",
        "checksum_warn": "警告: 校验和不匹配！",
        "checksum_ok": "校验通过",
        "sending_file": "发送文件:",
        "found_resume": "发现断点，从",
        "resume_continue": "处续传",
        "send_success": "发送成功！",
        "send_failed_short": "发送失败",
        "send_failed_long": "发送失败:",
        "receive_failed": "接收失败:",
        "cancelling": "正在取消传输...",
        "transfer_cancelled_short": "传输已取消",
        "timeout_retry": "连接超时，重试",
        "timeout_retry2": "传输失败，",
        "seconds_retry": "秒后重试",
        "seconds_retry2": "秒后重试",
        "language": "语言:",
        "timeout_setting": "超时(秒):",
        "size": "大小:",
        "elapsed": "耗时:",
        "speed": "速度:",
        "resume_info": "(断点续传从",
    },
    "en": {
        "window_title": "Simple File Transfer (Enhanced - Cross-Subnet Support)",
        "local_name": "Local Name:",
        "ip_label": "IP:",
        "save_dir": "Save Directory:",
        "browse": "Browse...",
        "online_devices": "Online Devices:",
        "manual_add": "Cross-Subnet Manual Device Addition",
        "ip": "IP:",
        "name": "Name:",
        "add": "Add",
        "remove_selected": "Remove Selected",
        "scan_network": "Scan Network",
        "select_file": "Select File:",
        "select_files": "Select Multiple...",
        "send": "Send →",
        "cancel": "Cancel",
        "view_history": "View History",
        "progress": "Progress:",
        "speed": "Speed:",
        "remaining": "Remaining:",
        "log": "Log:",
        "manual_device": "Manual",
        "scan_device": "Scan Discovered",
        "select_target": "Please select target device",
        "select_file_warning": "Please select a file first",
        "input_ip": "Please enter IP address",
        "invalid_ip": "Invalid IP address format",
        "added_device": "Added device: ",
        "removed_device": "Removed device: ",
        "only_remove_manual": "Can only remove manually added devices",
        "scan_progress": "Scan progress:",
        "scan_complete_found": "Scan complete, found",
        "scan_complete_none": "Scan complete, no devices found",
        "discovered_device": "Discovered device: ",
        "scanning_network": "Scanning network:",
        "no_transfer": "No transfer in progress",
        "transfer_history": "Transfer History",
        "no_history": "No transfer records",
        "select_multiple_files": "Select Files (Multi-Select)",
        "selected_files": "files:",
        "batch_transfer_complete": "Batch transfer complete",
        "sending": "Sending",
        "send_failed": "Send failed:",
        "service_started": "Started, save directory:",
        "cross_subnet_hint": "Tip: For cross-subnet transfer, manually enter target IP on the left",
        "receiving_service": "Receiving service started, port:",
        "start_receive_failed": "Failed to start receiving service:",
        "connection_from": "Connection from",
        "connection": "connected",
        "receiving_file": "Receiving file:",
        "resume_from": "[Resume from",
        "transfer_cancelled": "Transfer cancelled",
        "saving_to": "Saving to:",
        "checksum_warn": "Warning: Checksum mismatch!",
        "checksum_ok": "Checksum OK",
        "sending_file": "Sending file:",
        "found_resume": "Found resume point, continue from",
        "resume_continue": "resume",
        "send_success": "Send successful!",
        "send_failed_short": "Send failed",
        "send_failed_long": "Send failed:",
        "receive_failed": "Receive failed:",
        "cancelling": "Cancelling transfer...",
        "transfer_cancelled_short": "Transfer cancelled",
        "timeout_retry": "Connection timeout, retry",
        "timeout_retry2": "Transfer failed,",
        "seconds_retry": "seconds until retry",
        "seconds_retry2": "seconds until retry",
        "language": "Language:",
        "timeout_setting": "Timeout(s):",
        "size": "Size:",
        "elapsed": "Elapsed:",
        "speed": "Speed:",
        "resume_info": "(Resume from",
    },
}


def get_text(key):
    """获取本地化文本"""
    return LANGUAGES[current_lang].get(key, key)


def load_config():
    """加载配置文件"""
    global current_lang
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                current_lang = config.get("language", "zh")
    except:
        pass


def save_config():
    """保存配置文件"""
    try:
        config = {"language": current_lang}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except:
        pass


def get_local_ip():
    """获取本机 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_hostname():
    """获取主机名"""
    return socket.gethostname()


def compute_checksum(filepath):
    """计算文件校验和"""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(BUFFER_SIZE), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def is_valid_ip(ip):
    """验证 IP 地址格式"""
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except:
        return False


# ==================== 格式化函数 ====================


def format_size(size):
    """格式化文件大小"""
    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"
    elif size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    elif size >= 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size} B"


def format_speed(speed):
    """格式化传输速度"""
    if speed >= 1024 * 1024:
        return f"{speed / (1024 * 1024):.2f} MB/s"
    elif speed >= 1024:
        return f"{speed / 1024:.2f} KB/s"
    else:
        return f"{speed:.0f} B/s"


def format_duration(seconds):
    """格式化时间长度"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        mins = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{mins}分{secs}秒"
    else:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}小时{mins}分"


# ==================== IP 历史记录功能 ====================


def load_ip_history():
    """加载 IP 历史记录"""
    try:
        if os.path.exists(IP_HISTORY_FILE):
            with open(IP_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []


def save_ip_history(history):
    """保存 IP 历史记录"""
    try:
        with open(IP_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except:
        pass


def add_to_ip_history(ip):
    """添加 IP 到历史记录"""
    if not is_valid_ip(ip):
        return

    history = load_ip_history()

    if ip in history:
        history.remove(ip)

    history.insert(0, ip)

    if len(history) > MAX_IP_HISTORY:
        history = history[:MAX_IP_HISTORY]

    save_ip_history(history)


# ==================== 传输历史记录功能 ====================


def load_history():
    """加载传输历史"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []


def save_history(history):
    """保存传输历史"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except:
        pass


def add_to_history(record):
    """添加记录到历史"""
    history = load_history()
    history.insert(0, record)
    if len(history) > MAX_HISTORY:
        history = history[:MAX_HISTORY]
    save_history(history)


class DiscoveryService:
    """设备发现服务"""

    def __init__(self, my_name, callback):
        self.my_name = my_name
        self.callback = callback
        self.running = False
        self.devices = {}
        self.lock = threading.Lock()
        self.scan_timeout = 1.0  # Default timeout per host
        self.log_callback = None

    def set_log_callback(self, callback):
        """Set log callback for scan progress"""
        self.log_callback = callback

    def start(self):
        self.running = True
        threading.Thread(target=self._listen, daemon=True).start()
        threading.Thread(target=self._broadcast, daemon=True).start()

    def stop(self):
        self.running = False

    def scan_network(self, subnet=None, timeout=1.0):
        """扫描本地网络查找设备"""
        self.scan_timeout = timeout

        if not subnet:
            local_ip = get_local_ip()
            parts = local_ip.split(".")
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"

        if self.log_callback:
            self.log_callback(f"{get_text('scanning_network')} {subnet}.0/24")

        found_devices = []

        for i in range(1, 255):
            if not self.running:
                break

            target_ip = f"{subnet}.{i}"

            if i % 25 == 0 and self.log_callback:
                self.log_callback(f"{get_text('scan_progress')} {i}/254")

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((target_ip, DISCOVERY_PORT))
                sock.close()

                if result == 0:
                    found_devices.append(target_ip)
                    if self.log_callback:
                        self.log_callback(
                            f"{get_text('discovered_device')} {target_ip}"
                        )
            except:
                pass

        if found_devices:
            if self.log_callback:
                self.log_callback(
                    f"{get_text('scan_complete_found')} {len(found_devices)} 个设备"
                )

            for ip in found_devices:
                self.add_manual_device(ip, name=f"{get_text('scan_device')} ({ip})")
        else:
            if self.log_callback:
                self.log_callback(get_text("scan_complete_none"))

    def _listen(self):
        """监听广播"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        sock.bind(("", DISCOVERY_PORT))

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                info = json.loads(data.decode())
                ip = addr[0]
                if info.get("name") != self.my_name:
                    with self.lock:
                        self.devices[ip] = {
                            "name": info.get("name"),
                            "ip": ip,
                            "last_seen": time.time(),
                            "manual": False,
                        }
                    self.callback(self.get_devices())
            except socket.timeout:
                continue
            except:
                continue

    def _broadcast(self):
        """广播自己"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        msg = json.dumps({"name": self.my_name, "ip": get_local_ip()}).encode()

        while self.running:
            try:
                sock.sendto(msg, ("255.255.255.255", DISCOVERY_PORT))
            except:
                pass
            time.sleep(BROADCAST_INTERVAL)

    def get_devices(self):
        """获取在线设备列表"""
        now = time.time()
        with self.lock:
            return [
                d
                for d in list(self.devices.values())
                if d.get("manual", False)
                or (now - d["last_seen"] < BROADCAST_INTERVAL * 3)
            ]

    def add_manual_device(self, ip, name=None):
        """手动添加设备"""
        with self.lock:
            self.devices[ip] = {
                "name": name or f"手动添加 ({ip})",
                "ip": ip,
                "last_seen": time.time(),
                "manual": True,
            }
        self.callback(self.get_devices())

    def remove_device(self, ip):
        """移除设备"""
        with self.lock:
            if ip in self.devices:
                del self.devices[ip]
        self.callback(self.get_devices())


class TransferServer:
    """接收文件服务器"""

    def __init__(self, save_dir, progress_callback, log_callback, speed_callback=None):
        self.save_dir = save_dir
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.speed_callback = speed_callback
        self.running = False
        self.server_socket = None

    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    def _run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(1.0)

        try:
            self.server_socket.bind(("", TRANSFER_PORT))
            self.server_socket.listen(5)
            self.log_callback(f"{get_text('receiving_service')} {TRANSFER_PORT}")
        except Exception as e:
            self.log_callback(f"{get_text('start_receive_failed')} {e}")
            return

        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client, args=(client_socket, addr), daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.log_callback(f"错误: {e}")

    def _handle_client(self, sock, raddr):
        try:
            addr = raddr[0]
            self.log_callback(
                f"{get_text('connection_from')} {addr} {get_text('connection')}"
            )

            header_data = sock.recv(4)
            if not header_data:
                return
            header_len = struct.unpack("!I", header_data)[0]

            header_json = sock.recv(header_len).decode()
            header = json.loads(header_json)

            filename = header["filename"]
            filesize = header["filesize"]
            checksum = header.get("checksum", "")
            resume_from = header.get("resume_from", 0)

            save_path = os.path.join(self.save_dir, filename)
            if os.path.exists(save_path) and resume_from == 0:
                name, ext = os.path.splitext(filename)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(self.save_dir, f"{name}_{ts}{ext}")

            mode = "ab" if resume_from > 0 else "wb"
            self.log_callback(
                f"{get_text('receiving_file')} {filename} ({format_size(filesize)})"
                + (
                    f" [{get_text('resume_from')} {format_size(resume_from)}]"
                    if resume_from > 0
                    else ""
                )
            )

            received = resume_from
            last_update = time.time()
            last_speed_time = time.time()
            last_speed_bytes = resume_from
            start_time = time.time()

            with open(save_path, mode) as f:
                if resume_from > 0:
                    f.seek(resume_from)

                while received < filesize:
                    if not self.running:
                        self.log_callback(get_text("transfer_cancelled"))
                        break

                    chunk = sock.recv(min(BUFFER_SIZE, filesize - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

                    now = time.time()
                    if now - last_update > 0.1 or received == filesize:
                        progress = (received / filesize) * 100
                        self.progress_callback(progress)
                        last_update = now

                    if now - last_speed_time > 0.5:
                        bytes_since = received - last_speed_bytes
                        time_since = now - last_speed_time
                        if time_since > 0:
                            speed = bytes_since / time_since
                            if self.speed_callback:
                                self.speed_callback(speed)
                        last_speed_time = now
                        last_speed_bytes = received

            if checksum:
                calc_checksum = compute_checksum(save_path)
                if calc_checksum != checksum:
                    self.log_callback(get_text("checksum_warn"))
                else:
                    self.log_callback(get_text("checksum_ok"))

            self.log_callback(f"{get_text('saving_to')} {save_path}")
            self.progress_callback(100)

            elapsed = time.time() - start_time
            avg_speed = filesize / elapsed if elapsed > 0 else 0
            add_to_history(
                {
                    "type": "receive",
                    "filename": filename,
                    "size": filesize,
                    "size_formatted": format_size(filesize),
                    "elapsed": elapsed,
                    "elapsed_formatted": format_duration(elapsed),
                    "speed": avg_speed,
                    "speed_formatted": format_speed(avg_speed),
                    "timestamp": datetime.now().isoformat(),
                    "ip": addr,
                    "resume_from": resume_from,
                }
            )

            sock.sendall(b"OK")

        except Exception as e:
            self.log_callback(f"接收失败: {e}")
        finally:
            sock.close()


class TransferClient:
    """发送文件客户端"""

    def __init__(self, progress_callback, log_callback, speed_callback=None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.speed_callback = speed_callback
        self.cancel_event = threading.Event()
        self.current_file = None
        self.current_ip = None

    def cancel(self):
        self.cancel_event.set()
        self.log_callback(get_text("cancelling"))

    def send_file_with_retry(self, filepath, target_ip):
        for attempt in range(MAX_RETRIES):
            if self.cancel_event.is_set():
                self.log_callback(get_text("transfer_cancelled_short"))
                return False

            try:
                result = self._send_file(filepath, target_ip)
                if result:
                    return True
                elif attempt < MAX_RETRIES - 1:
                    self.log_callback(
                        f"{get_text('timeout_retry2')} {RETRY_DELAY}{get_text('seconds_retry2')} {attempt + 1}/{MAX_RETRIES}"
                    )
                    time.sleep(RETRY_DELAY)
            except socket.timeout:
                self.log_callback(
                    f"{get_text('timeout_retry')} {attempt + 1}/{MAX_RETRIES}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                self.log_callback(f"{get_text('send_failed_long')} {e}")
                if attempt < MAX_RETRIES - -1:
                    self.log_callback(
                        f"{RETRY_DELAY}{get_text('seconds_retry')} {attempt + 1}/{MAX_RETRIES}"
                    )
                    time.sleep(RETRY_DELAY)

        self._cleanup_resume_file(filepath)
        return False

    def _send_file(self, filepath, target_ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((target_ip, TRANSFER_PORT))

            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            checksum = compute_checksum(filepath)

            resume_from = self._load_resume_position(filepath)
            if resume_from > 0:
                self.log_callback(
                    f"{get_text('found_resume')} {format_size(resume_from)} {get_text('resume_continue')}"
                )

            self.log_callback(f"{get_text('sending_file')} {filename}")

            header = {
                "filename": filename,
                "filesize": filesize,
                "checksum": checksum,
                "resume_from": resume_from,
            }
            header_json = json.dumps(header).encode()
            sock.sendall(struct.pack("!I", len(header_json)))
            sock.sendall(header_json)

            sent = resume_from
            last_update = time.time()
            last_speed_time = time.time()
            last_speed_bytes = resume_from
            start_time = time.time()

            with open(filepath, "rb") as f:
                if resume_from > 0:
                    f.seek(resume_from)

                while sent < filesize:
                    if self.cancel_event.is_set():
                        self.log_callback(get_text("transfer_cancelled"))
                        self._save_resume_position(filepath, sent)
                        sock.close()
                        return False

                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    sent += len(chunk)

                    now = time.time()
                    if now - last_update > 0.1 or sent == filesize:
                        progress = (sent / filesize) * 100
                        self.progress_callback(progress)
                        last_update = now

                    if now - last_speed_time > 0.5:
                        bytes_since = sent - last_speed_bytes
                        time_since = now - last_speed_time
                        if time_since > 0:
                            speed = bytes_since / time_since
                            if self.speed_callback:
                                self.speed_callback(speed)
                        last_speed_time = now
                        last_speed_bytes = sent

            resp = sock.recv(2)
            if resp == b"OK":
                self.log_callback(get_text("send_success"))
            else:
                self.log_callback(get_text("send_failed_short"))
                sock.close()
                return False

            sock.close()
            self._cleanup_resume_file(filepath)

            elapsed = time.time() - start_time
            avg_speed = filesize / elapsed if elapsed > 0 else 0
            add_to_history(
                {
                    "type": "send",
                    "filename": filename,
                    "size": filesize,
                    "size_formatted": format_size(filesize),
                    "elapsed": elapsed,
                    "elapsed_formatted": format_duration(elapsed),
                    "speed": avg_speed,
                    "speed_formatted": format_speed(avg_speed),
                    "timestamp": datetime.now().isoformat(),
                    "ip": target_ip,
                    "resume_from": resume_from,
                }
            )

            return True

        except Exception as e:
            self.log_callback(f"发送失败: {e}")
            return False

    def _get_resume_filename(self, filepath):
        return os.path.join(
            os.path.dirname(filepath), f".resume_{os.path.basename(filepath)}"
        )

    def _load_resume_position(self, filepath):
        resume_file = self._get_resume_filename(filepath)
        try:
            if os.path.exists(resume_file):
                with open(resume_file, "r") as f:
                    return int(f.read().strip())
        except:
            pass
        return 0

    def _save_resume_position(self, filepath, position):
        resume_file = self._get_resume_filename(filepath)
        try:
            with open(resume_file, "w") as f:
                f.write(str(position))
        except:
            pass

    def _cleanup_resume_file(self, filepath):
        resume_file = self._get_resume_filename(filepath)
        try:
            if os.path.exists(resume_file):
                os.remove(resume_file)
        except:
            pass


class MainWindow:
    """主界面"""

    def __init__(self, root):
        self.root = root
        self.root.title(get_text("window_title"))
        self.root.geometry("800x700")

        load_config()

        self.save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self.my_name = get_hostname()

        self.discovery = None
        self.server = None
        self.client = None
        self.devices = []
        self.transfer_speed_label = None
        self.remaining_time_label = None

        self._create_widgets()
        self._start_services()

    def _create_widgets(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text=get_text("local_name")).pack(side=tk.LEFT)
        self.name_label = ttk.Label(
            top_frame, text=self.my_name, font=("Arial", 10, "bold")
        )
        self.name_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text=get_text("ip_label")).pack(side=tk.LEFT, padx=(20, 0))
        self.ip_label = ttk.Label(
            top_frame, text=get_local_ip(), font=("Arial", 10, "bold")
        )
        self.ip_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text=get_text("language")).pack(side=tk.LEFT, padx=(20, 0))
        self.lang_var = tk.StringVar(value=current_lang)
        self.lang_combo = ttk.Combobox(
            top_frame,
            textvariable=self.lang_var,
            values=["zh", "en"],
            width=5,
            state="readonly",
        )
        self.lang_combo.pack(side=tk.LEFT, padx=5)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        dir_frame = ttk.Frame(self.root, padding=10)
        dir_frame.pack(fill=tk.X)

        ttk.Label(dir_frame, text=get_text("save_dir")).pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame)
        self.dir_entry.insert(0, self.save_dir)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text=get_text("browse"), command=self._browse_dir).pack(
            side=tk.LEFT
        )

        ttk.Separator(self.root).pack(fill=tk.X, padx=10)

        mid_container = ttk.Frame(self.root, padding=10)
        mid_container.pack(fill=tk.BOTH, expand=True)
        mid_frame = ttk.PanedWindow(mid_container, orient=tk.HORIZONTAL)
        mid_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(mid_frame)
        mid_frame.add(left_frame, weight=1)

        ttk.Label(left_frame, text=get_text("online_devices")).pack(anchor=tk.W)
        self.device_listbox = tk.Listbox(left_frame, height=8)
        self.device_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        manual_frame = ttk.LabelFrame(
            left_frame, text=get_text("manual_add"), padding=5
        )
        manual_frame.pack(fill=tk.X, pady=(5, 0))

        ip_frame = ttk.Frame(manual_frame)
        ip_frame.pack(fill=tk.X)

        ttk.Label(ip_frame, text=get_text("ip")).pack(side=tk.LEFT)
        ip_history = load_ip_history()
        self.manual_ip_entry = ttk.Combobox(ip_frame, values=ip_history)
        if ip_history:
            self.manual_ip_entry.set(ip_history[0])
        self.manual_ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.manual_ip_entry.bind("<Return>", lambda e: self._add_manual_device())

        name_frame = ttk.Frame(manual_frame)
        name_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(name_frame, text=get_text("name")).pack(side=tk.LEFT)
        self.manual_name_entry = ttk.Entry(name_frame)
        self.manual_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        btn_frame = ttk.Frame(manual_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(
            btn_frame, text=get_text("add"), command=self._add_manual_device
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            btn_frame,
            text=get_text("remove_selected"),
            command=self._remove_selected_device,
        ).pack(side=tk.LEFT, padx=(5, 0))

        scan_frame = ttk.Frame(manual_frame)
        scan_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(scan_frame, text=get_text("timeout_setting")).pack(side=tk.LEFT)
        self.timeout_entry = ttk.Entry(scan_frame, width=5)
        self.timeout_entry.insert(0, "1")
        self.timeout_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            scan_frame, text=get_text("scan_network"), command=self._scan_network
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        right_frame = ttk.Frame(mid_frame)
        mid_frame.add(right_frame, weight=1)

        ttk.Label(right_frame, text=get_text("select_file")).pack(anchor=tk.W.W)
        self.file_entry = ttk.Entry(right_frame)
        self.file_entry.pack(fill=tk.X, pady=5)

        file_btn_frame = ttk.Frame(right_frame)
        file_btn_frame.pack(fill=tk.X)
        ttk.Button(
            file_btn_frame, text=get_text("browse"), command=self._browse_file
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            file_btn_frame, text=get_text("select_files"), command=self._browse_files
        ).pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        ttk.Separator(right_frame).pack(fill=tk.X, pady=10)
        ttk.Button(
            right_frame,
            text=get_text("send"),
            command=self._send_file,
            style="Accent.TButton",
        ).pack(fill=tk.X)
        ttk.Button(
            right_frame, text=get_text("cancel"), command=self._cancel_transfer
        ).pack(fill=tk.X, pady=(5, 0))
        ttk.Button(
            right_frame, text=get_text("view_history"), command=self._view_history
        ).pack(fill=tk.X)

        ttk.Separator(self.root).pack(fill=tk.X, padx=10)

        progress_frame = ttk.Frame(self.root, padding=10)
        progress_frame.pack(fill=tk.X)
        ttk.Label(progress_frame, text=get_text("progress")).pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        speed_frame = ttk.Frame(self.root, padding=(10, 5))
        speed_frame.pack(fill=tk.X)
        self.transfer_speed_label = ttk.Label(
            speed_frame, text=f"{get_text('speed')} --"
        )
        self.transfer_speed_label.pack(side=tk.LEFT)
        self.remaining_time_label = ttk.Label(
            speed_frame, text=f"{get_text('remaining')} --"
        )
        self.remaining_time_label.pack(side=tk.LEFT, padx=(20, 0))

        log_frame = ttk.Frame(self.root, padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(log_frame, text=get_text("log")).pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))

    def _start_services(self):
        self.discovery = DiscoveryService(self.my_name, self._on_devices_update)
        self.discovery.set_log_callback(self._log)
        self.discovery.start()

        self.server = TransferServer(
            self.save_dir, self._on_progress, self._log, self._on_speed
        )
        self.server.start()

        self._log(f"{get_text('service_started')} {self.save_dir}")
        self._log(get_text("cross_subnet_hint"))

    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.save_dir)
        if d:
            self.save_dir = d
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, d)
            if self.server:
                self.server.save_dir = d

    def _browse_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, f)

    def _browse_files(self):
        files = filedialog.askopenfilenames(title=get_text("select_multiple_files"))
        if files:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(
                0,
                f"{len(files)} {get_text('selected_files')} {os.path.basename(files[0])} ...",
            )
            self.transfer_queue = list(files)
            self._log(f"{get_text('selected_files')} {len(files)}")

    def _add_manual_device(self):
        ip = self.manual_ip_entry.get().strip()
        name = self.manual_name_entry.get().strip()

        if not ip:
            messagebox.showwarning("提示", get_text("input_ip"))
            return

        if not is_valid_ip(ip):
            messagebox.showwarning("", get_text("invalid_ip"))
            return

        self.discovery.add_manual_device(ip, name if name else None)
        add_to_ip_history(ip)

        ip_history = load_ip_history()
        self.manual_ip_entry["values"] = ip_history

        self.manual_ip_entry.delete(0, tk.END)
        self.manual_name_entry.delete(0, tk.END)
        self._log(f"{get_text('added_device')} {ip}")

    def _scan_network(self):
        """扫描网络"""
        try:
            timeout = float(self.timeout_entry.get())
        except:
            timeout = 1.0

        threading.Thread(
            target=self.discovery.scan_network, args=(None, timeout), daemon=True
        ).start()

    def _on_language_change(self, event):
        """语言切换回调"""
        global current_lang
        new_lang = self.lang_var.get()
        if new_lang != current_lang:
            current_lang = new_lang
            save_config()
            self.root.title(get_text("window_title"))

    def _remove_selected_device(self):
        sel = self.device_listbox.curselection()
        if not sel:
            return

        device = self.devices[sel[0]]
        ip = device["ip"]

        if device.get("manual", False):
            self.discovery.remove_device(ip)
            self._log(f"{get_text('removed_device')} {ip}")
        else:
            messagebox.showinfo("", get_text("only_remove_manual"))

    def _on_devices_update(self, devices):
        self.devices = devices
        self.root.after(0, self._update_device_list)

    def _update_device_list(self):
        self.device_listbox.delete(0, tk.END)
        for d in self.devices:
            label = f"{d['name']} ({d['ip']})"
            if d.get("manual", False):
                label += f" [{get_text('manual_device')}]"
            self.device_listbox.insert(tk.END, label)

    def _on_progress(self, value):
        self.root.after(0, lambda: self.progress.configure(value=value))

    def _on_speed(self, speed):
        if self.transfer_speed_label:
            self.root.after(
                0,
                lambda: self.transfer_speed_label.configure(
                    text=f"{get_text('speed')} {format_speed(speed)}"
                ),
            )

        current_progress = self.progress["value"]
        if (
            current_progress > 0
            and current_progress < 100
            and self.remaining_time_label
        ):
            remaining = (100 - current_progress) / (
                current_progress / time.time() if current_progress > 0 else 1
            )
            self.root.after(
                0,
                lambda: self.remaining_time_label.configure(
                    text=f"{get_text('remaining')} {format_duration(remaining)}"
                ),
            )

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.root.after(0, lambda: self._append_log(f"[{ts}] {msg}"))

    def _append_log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _send_file(self):
        filepath = self.file_entry.get()

        if hasattr(self, "transfer_queue") and self.transfer_queue:
            files = self.transfer_queue
        else:
            if not filepath or not os.path.exists(filepath):
                messagebox.showwarning("", get_text("select_file_warning"))
                return
            files = [filepath]

        sel = self.device_listbox.curselection()
        if not sel:
            messagebox.showwarning("", get_text("select_target"))
            return

        target_ip = self.devices[sel[0]]["ip"]
        self.progress.configure(value=0)

        def send_next():
            if not files:
                self._log(get_text("batch_transfer_complete"))
                return

            file = files.pop(0)
            self._log(f"{get_text('sending')} {os.path.basename(file)}")

            self.client = TransferClient(self._on_progress, self._log, self._on_speed)
            success = self.client.send_file_with_retry(file, target_ip)

            if success:
                self.root.after(1000, send_next)
            else:
                self._log(f"{get_text('send_failed')} {os.path.basename(file)}")

        threading.Thread(target=send_next, daemon=True).start()

    def _cancel_transfer(self):
        if self.client:
            self.client.cancel()
        else:
            messagebox.showinfo("", get_text("no_transfer"))

    def _view_history(self):
        history = load_history()
        if not history:
            messagebox.showinfo(get_text("transfer_history"), get_text("no_history"))
            return

        history_window = tk.Toplevel(self.root)
        history_window.title(get_text("transfer_history"))
        history_window.geometry("600x400")

        text = scrolledtext.ScrolledText(history_window, state="disabled")
        text.pack(fill=tk.BOTH, expand=True)

        text.config(state="normal")
        for i, record in enumerate(history[:50]):
            line = f"{i + 1}. [{record['timestamp']}] {record['type']} {record['filename']}\n"
            line += f"   {get_text('size')} {record['size_formatted']} | "
            line += f"{get_text('elapsed')} {record['elapsed_formatted']} | "
            line += f"{get_text('speed')} {record['speed_formatted']}\n"
            if record.get("resume_from", 0) > 0:
                line += f"   {get_text('resume_info')} {format_size(record['resume_from'])})\n"
            line += "-" * 60 + "\n"
            text.insert(tk.END, line)
        text.config(state="disabled")


def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
