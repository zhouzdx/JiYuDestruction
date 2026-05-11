<div align="center">

# 极域 UDP 攻击工具

✨ _极域电子教室 UDP 数据包重放攻击脚本 - GUI 易操作版_ ✨

<div>
    <img alt="platform" src="https://img.shields.io/badge/Platform-Windows-blue?style=flat-square&logo=windows">
    <img alt="python" src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white">
    <img alt="license" src="https://img.shields.io/badge/License-MIT-green?style=flat-square">
    <img alt="version" src="https://img.shields.io/badge/Version-1.0-orange?style=flat-square">
</div>

</div>

---

> 极域电子教室的学生端对接收到的 UDP 数据包没有做身份验证，因此可以伪造特定数据包让学生端执行任意指令，从而实现对目标机器的远程控制。

## 功能

| 功能 | 说明 |
|------|------|
| 🔄 重启 | 远程重启学生端电脑 |
| ⏻ 关机 | 远程关闭学生端电脑 |
| 🔒 锁定屏幕 | 通过防火墙阻止 StudentMain.exe 联网（需管理员权限） |
| 🔓 解锁屏幕 | 恢复 StudentMain.exe 联网 |
| ℹ️ 获取信息 | 获取本机 IP 地址及学生端监听端口 |
| 💻 反弹 Shell | 通过 powercat 获取远程 cmd shell |
| 📨 发送消息 | 向学生端发送弹窗消息 |
| ⚡ 执行命令 | 远程执行任意系统命令 |

## 截图

![GUI 界面](screenshot.png)

## 下载

👉 **[前往 Releases 页面下载最新版](https://github.com/zhouzdx/JiYuDestruction/releases)**

## 使用方法

### GUI 版（推荐）
1. 下载 `JiyuUdpAttack.exe`
2. 双击运行
3. 输入目标 IP，选择操作

### IP 格式支持
- 单 IP: `192.168.80.12`
- IP 范围: `192.168.80.10-56`
- C 段: `192.168.80.1/24`

### 命令行版
```
python Jiyu_udp_attack.py -ip <目标IP> -e <动作>
```

## 注意事项
- 锁定屏幕功能需要**管理员权限**运行
- 本工具仅用于教育研究和授权测试
- 请遵守当地法律法规

## 致谢
- 基于 [ht0Ruial/Jiyu_udp_attack](https://github.com/ht0Ruial/Jiyu_udp_attack) 核心逻辑

## 许可证
- **MIT License**
