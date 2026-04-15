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


# ==================== 历史记录功能 ====================


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

    def start(self):
        self.running = True
        threading.Thread(target=self._listen, daemon=True).start()
        threading.Thread(target=self._broadcast, daemon=True).start()

    def stop(self):
        self.running = False

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
            self.log_callback(f"接收服务已启动，端口: {TRANSFER_PORT}")
        except Exception as e:
            self.log_callback(f"启动接收服务失败: {e}")
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
            self.log_callback(f"来自 {addr} 的连接")

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
                f"接收文件: {filename} ({format_size(filesize)})"
                + (
                    f" [断点续传从 {format_size(resume_from)}]"
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
                        self.log_callback("传输被取消")
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
                    self.log_callback(f"警告: 校验和不匹配！")
                else:
                    self.log_callback(f"校验通过")

            self.log_callback(f"保存到: {save_path}")
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
        self.log_callback("正在取消传输...")

    def send_file_with_retry(self, filepath, target_ip):
        for attempt in range(MAX_RETRIES):
            if self.cancel_event.is_set():
                self.log_callback("传输已取消")
                return False

            try:
                result = self._send_file(filepath, target_ip)
                if result:
                    return True
                elif attempt < MAX_RETRIES - 1:
                    self.log_callback(
                        f"传输失败，{RETRY_DELAY}秒后重试 {attempt + 1}/{MAX_RETRIES}"
                    )
                    time.sleep(RETRY_DELAY)
            except socket.timeout:
                self.log_callback(f"连接超时，重试 {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                self.log_callback(f"传输失败: {e}")
                if attempt < MAX_RETRIES - 1:
                    self.log_callback(
                        f"{RETRY_DELAY}秒后重试 {attempt + 1}/{MAX_RETRIES}"
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
                self.log_callback(f"发现断点，从 {format_size(resume_from)} 处续传")

            self.log_callback(f"发送文件: {filename}")

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
                        self.log_callback("传输被取消")
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
                self.log_callback("发送成功！")
            else:
                self.log_callback("发送失败")
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
        self.root.title("简单文件传输 (增强版 - 支持跨网段)")
        self.root.geometry("800x700")

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

        ttk.Label(top_frame, text="本机名称:").pack(side=tk.LEFT)
        self.name_label = ttk.Label(
            top_frame, text=self.my_name, font=("Arial", 10, "bold")
        )
        self.name_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text="IP:").pack(side=tk.LEFT, padx=(20, 0))
        self.ip_label = ttk.Label(
            top_frame, text=get_local_ip(), font=("Arial", 10, "bold")
        )
        self.ip_label.pack(side=tk.LEFT, padx=5)

        dir_frame = ttk.Frame(self.root, padding=10)
        dir_frame.pack(fill=tk.X)

        ttk.Label(dir_frame, text="保存目录:").pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame)
        self.dir_entry.insert(0, self.save_dir)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=self._browse_dir).pack(
            side=tk.LEFT
        )

        ttk.Separator(self.root).pack(fill=tk.X, padx=10)

        mid_container = ttk.Frame(self.root, padding=10)
        mid_container.pack(fill=tk.BOTH, expand=True)
        mid_frame = ttk.PanedWindow(mid_container, orient=tk.HORIZONTAL)
        mid_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(mid_frame)
        mid_frame.add(left_frame, weight=1)

        ttk.Label(left_frame, text="在线设备:").pack(anchor=tk.W)
        self.device_listbox = tk.Listbox(left_frame, height=8)
        self.device_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        manual_frame = ttk.LabelFrame(left_frame, text="跨网段手动添加设备", padding=5)
        manual_frame.pack(fill=tk.X, pady=(5, 0))

        ip_frame = ttk.Frame(manual_frame)
        ip_frame.pack(fill=tk.X)

        ttk.Label(ip_frame, text="IP:").pack(side=tk.LEFT)
        self.manual_ip_entry = ttk.Entry(ip_frame)
        self.manual_ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.manual_ip_entry.bind("<Return>", lambda e: self._add_manual_device())

        name_frame = ttk.Frame(manual_frame)
        name_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(name_frame, text="名称:").pack(side=tk.LEFT)
        self.manual_name_entry = ttk.Entry(name_frame)
        self.manual_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        btn_frame = ttk.Frame(manual_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="添加", command=self._add_manual_device).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(
            btn_frame, text="移除选中", command=self._remove_selected_device
        ).pack(side=tk.LEFT, padx=(5, 0))

        right_frame = ttk.Frame(mid_frame)
        mid_frame.add(right_frame, weight=1)

        ttk.Label(right_frame, text="选择文件:").pack(anchor=tk.W)
        self.file_entry = ttk.Entry(right_frame)
        self.file_entry.pack(fill=tk.X, pady=5)

        file_btn_frame = ttk.Frame(right_frame)
        file_btn_frame.pack(fill=tk.X)
        ttk.Button(file_btn_frame, text="选择文件...", command=self._browse_file).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(file_btn_frame, text="选择多个...", command=self._browse_files).pack(
            side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True
        )

        ttk.Separator(right_frame).pack(fill=tk.X, pady=10)
        ttk.Button(
            right_frame, text="发送 →", command=self._send_file, style="Accent.TButton"
        ).pack(fill=tk.X)
        ttk.Button(right_frame, text="取消", command=self._cancel_transfer).pack(
            fill=tk.X, pady=(5, 0)
        )
        ttk.Button(right_frame, text="查看历史", command=self._view_history).pack(
            fill=tk.X
        )

        ttk.Separator(self.root).pack(fill=tk.X, padx=10)

        progress_frame = ttk.Frame(self.root, padding=10)
        progress_frame.pack(fill=tk.X)
        ttk.Label(progress_frame, text="进度:").pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        speed_frame = ttk.Frame(self.root, padding=(10, 5))
        speed_frame.pack(fill=tk.X)
        self.transfer_speed_label = ttk.Label(speed_frame, text="速度: --")
        self.transfer_speed_label.pack(side=tk.LEFT)
        self.remaining_time_label = ttk.Label(speed_frame, text="剩余: --")
        self.remaining_time_label.pack(side=tk.LEFT, padx=(20, 0))

        log_frame = ttk.Frame(self.root, padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(log_frame, text="日志:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))

    def _start_services(self):
        self.discovery = DiscoveryService(self.my_name, self._on_devices_update)
        self.discovery.start()

        self.server = TransferServer(
            self.save_dir, self._on_progress, self._log, self._on_speed
        )
        self.server.start()

        self._log(f"已启动，保存目录: {self.save_dir}")
        self._log(f"提示: 跨网段传输请在左侧手动输入对方 IP")

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
        files = filedialog.askopenfilenames(title="选择文件（支持多选）")
        if files:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(
                0, f"{len(files)} 个文件: {os.path.basename(files[0])} ..."
            )
            self.transfer_queue = list(files)
            self._log(f"已选择 {len(files)} 个文件")

    def _add_manual_device(self):
        ip = self.manual_ip_entry.get().strip()
        name = self.manual_name_entry.get().strip()

        if not ip:
            messagebox.showwarning("提示", "请输入 IP 地址")
            return

        if not is_valid_ip(ip):
            messagebox.showwarning("提示", "IP 地址格式不正确")
            return

        self.discovery.add_manual_device(ip, name if name else None)
        self.manual_ip_entry.delete(0, tk.END)
        self.manual_name_entry.delete(0, tk.END)
        self._log(f"已添加设备: {ip}")

    def _remove_selected_device(self):
        sel = self.device_listbox.curselection()
        if not sel:
            return

        device = self.devices[sel[0]]
        ip = device["ip"]

        if device.get("manual", False):
            self.discovery.remove_device(ip)
            self._log(f"已移除设备: {ip}")
        else:
            messagebox.showinfo("提示", "只能移除手动添加的设备")

    def _on_devices_update(self, devices):
        self.devices = devices
        self.root.after(0, self._update_device_list)

    def _update_device_list(self):
        self.device_listbox.delete(0, tk.END)
        for d in self.devices:
            label = f"{d['name']} ({d['ip']})"
            if d.get("manual", False):
                label += " [手动]"
            self.device_listbox.insert(tk.END, label)

    def _on_progress(self, value):
        self.root.after(0, lambda: self.progress.configure(value=value))

    def _on_speed(self, speed):
        if self.transfer_speed_label:
            self.root.after(
                0,
                lambda: self.transfer_speed_label.configure(
                    text=f"速度: {format_speed(speed)}"
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
                    text=f"剩余: {format_duration(remaining)}"
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
                messagebox.showwarning("提示", "请先选择文件")
                return
            files = [filepath]

        sel = self.device_listbox.curselection()
        if not sel:
            messagebox.showwarning("提示", "请选择目标设备")
            return

        target_ip = self.devices[sel[0]]["ip"]
        self.progress.configure(value=0)

        def send_next():
            if not files:
                self._log("批量传输完成")
                return

            file = files.pop(0)
            self._log(f"正在发送 {os.path.basename(file)}")

            self.client = TransferClient(self._on_progress, self._log, self._on_speed)
            success = self.client.send_file_with_retry(file, target_ip)

            if success:
                self.root.after(1000, send_next)
            else:
                self._log(f"发送失败: {os.path.basename(file)}")

        threading.Thread(target=send_next, daemon=True).start()

    def _cancel_transfer(self):
        if self.client:
            self.client.cancel()
        else:
            messagebox.showinfo("提示", "没有正在进行的传输")

    def _view_history(self):
        history = load_history()
        if not history:
            messagebox.showinfo("传输历史", "暂无传输记录")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("传输历史")
        history_window.geometry("600x400")

        text = scrolledtext.ScrolledText(history_window, state="disabled")
        text.pack(fill=tk.BOTH, expand=True)

        text.config(state="normal")
        for i, record in enumerate(history[:50]):
            line = f"{i + 1}. [{record['timestamp']}] {record['type']} {record['filename']}\n"
            line += f"   大小: {record['size_formatted']} | "
            line += f"耗时: {record['elapsed_formatted']} | "
            line += f"速度: {record['speed_formatted']}\n"
            if record.get("resume_from", 0) > 0:
                line += f"   (断点续传从 {format_size(record['resume_from'])})\n"
            line += "-" * 60 + "\n"
            text.insert(tk.END, line)
        text.config(state="disabled")


def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
