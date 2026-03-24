import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple
from urllib.parse import urlparse

from models.session_tracker import SessionTracker


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>33500B Web Console</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: Arial, sans-serif; margin: 24px; background: #f4f7fb; color: #223; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
        .card { background: white; border-radius: 10px; padding: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); min-width: 0; }
        input, select, button, textarea { width: 100%; max-width: 100%; min-width: 0; margin-top: 6px; margin-bottom: 10px; padding: 8px; }
        button { cursor: pointer; }
        code { background: #eef3ff; padding: 2px 6px; border-radius: 4px; word-break: break-all; }
        .profiles { display: flex; flex-wrap: wrap; gap: 12px; }
        .profile-card { width: 240px; min-height: 88px; display: flex; flex-direction: column; justify-content: space-between; border: 1px solid #d9e2f2; border-radius: 10px; padding: 12px; background: #fafcff; }
        .profile-card.active { background: #dff5df; border-color: #4caf50; }
        .profile-name { flex: 1; width: 100%; text-align: left; background: transparent; border: none; padding: 0; margin: 0 0 10px 0; color: #1b2b44; font-weight: bold; white-space: normal; word-break: break-word; overflow-wrap: anywhere; }
        .profile-actions { display: flex; gap: 8px; }
        .profile-actions button { margin: 0; }
        .muted { color: #5f6b7a; font-size: 0.95em; }
    </style>
</head>
<body>
    <h1>Keysight 33500B Controller</h1>
    <p>在线人数（最近 10 秒内）：<strong id="online-count">0</strong></p>
    <div class="grid">
        <div class="card">
            <h2>设备状态</h2>
            <div id="status"></div>
            <button onclick="refreshStatus()">刷新状态（自动 15 秒）</button>
        </div>
        <div class="card">
            <h2>受保护控制</h2>
            <label>控制密码</label>
            <input id="password" type="password" placeholder="输入控制密码" />
            <label>资源地址</label>
            <select id="resource"></select>
            <button onclick="connectDevice()">连接设备</button>
            <label>Waveform</label>
            <select id="waveform"><option>SIN</option><option>SQU</option><option>TRI</option><option>RAMP</option></select>
            <label>Frequency</label><input id="frequency" type="number" value="1000" />
            <label>Amplitude</label><input id="amplitude" type="number" value="1" />
            <label>Offset</label><input id="offset" type="number" value="0" />
            <label>Phase</label><input id="phase" type="number" value="0" />
            <button onclick="applyConfig()">应用配置</button>
            <button onclick="setOutput(true)">开启输出</button>
            <button onclick="setOutput(false)">关闭输出</button>
        </div>
        <div class="card">
            <h2>SQLite 配置缓存</h2>
            <label>配置名称</label>
            <input id="profile-name" placeholder="例如 startup-default" />
            <button onclick="saveProfile()">保存当前配置</button>
            <p class="muted">点击配置名称会直接加载并应用；绿色表示当前设备状态与该配置一致。</p>
            <div id="profiles" class="profiles"></div>
        </div>
    </div>
    <script>
        const clientId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

        async function api(path, options = {}) {
            const response = await fetch(path, {
                headers: { 'Content-Type': 'application/json' },
                ...options,
            });
            const data = await response.json();
            if (!response.ok) {
                alert(data.error || 'Request failed');
                throw new Error(data.error || 'Request failed');
            }
            return data;
        }

        function currentPassword() {
            return document.getElementById('password').value;
        }

        function fillCurrentForm(state) {
            document.getElementById('waveform').value = state.waveform;
            document.getElementById('frequency').value = state.frequency;
            document.getElementById('amplitude').value = state.amplitude;
            document.getElementById('offset').value = state.offset;
            document.getElementById('phase').value = state.phase;
        }

        function renderProfiles(data) {
            const profiles = document.getElementById('profiles');
            profiles.innerHTML = '';
            data.profiles.forEach((profile) => {
                const card = document.createElement('div');
                card.className = `profile-card${profile.name === data.active_profile_name ? ' active' : ''}`;

                const nameButton = document.createElement('button');
                nameButton.className = 'profile-name';
                nameButton.textContent = profile.name;
                nameButton.title = `点击加载配置 ${profile.name}`;
                nameButton.onclick = () => loadProfile(profile.name);

                const actions = document.createElement('div');
                actions.className = 'profile-actions';

                const editButton = document.createElement('button');
                editButton.textContent = 'EDIT';
                editButton.onclick = async (event) => {
                    event.stopPropagation();
                    const newName = prompt('请输入新的配置名称（仅修改名称，不改配置内容）', profile.name);
                    if (!newName) return;
                    await api('/api/profiles/rename', {
                        method: 'POST',
                        body: JSON.stringify({ password: currentPassword(), old_name: profile.name, new_name: newName.trim() })
                    });
                    document.getElementById('profile-name').value = newName;
                    await refreshStatus();
                };

                const deleteButton = document.createElement('button');
                deleteButton.textContent = 'DEL';
                deleteButton.onclick = async (event) => {
                    event.stopPropagation();
                    if (!confirm(`确认删除配置 ${profile.name} 吗？`)) return;
                    await api('/api/profiles/delete', {
                        method: 'POST',
                        body: JSON.stringify({ password: currentPassword(), name: profile.name })
                    });
                    await refreshStatus();
                };

                actions.appendChild(editButton);
                actions.appendChild(deleteButton);
                card.appendChild(nameButton);
                card.appendChild(actions);
                profiles.appendChild(card);
            });
        }

        async function refreshStatus() {
            const data = await api('/api/status');
            document.getElementById('online-count').innerText = data.online_users;
            document.getElementById('status').innerHTML = `
                <p>地址：<code>${data.current_address || '未选择'}</code></p>
                <p>连接状态：<strong>${data.connected ? '已连接' : '未连接'}</strong></p>
                <p>波形：<strong>${data.state.waveform}</strong></p>
                <p>频率：<strong>${data.state.frequency}</strong></p>
                <p>幅值：<strong>${data.state.amplitude}</strong></p>
                <p>偏置：<strong>${data.state.offset}</strong></p>
                <p>相位：<strong>${data.state.phase}</strong></p>
                <p>输出：<strong>${data.state.output_enabled ? '开启' : '关闭'}</strong></p>
                <p>当前匹配配置：<strong>${data.active_profile_name || '无'}</strong></p>
            `;
            const resource = document.getElementById('resource');
            resource.innerHTML = '';
            for (const item of data.resources) {
                const option = document.createElement('option');
                option.value = item;
                option.text = item;
                if (item === data.current_address) option.selected = true;
                resource.appendChild(option);
            }
            fillCurrentForm(data.state);
            renderProfiles(data);
        }

        async function heartbeat() {
            const data = await api('/api/session/heartbeat', {
                method: 'POST',
                body: JSON.stringify({ client_id: clientId })
            });
            document.getElementById('online-count').innerText = data.online_users;
        }

        async function connectDevice() {
            await api('/api/connect', {
                method: 'POST',
                body: JSON.stringify({ password: currentPassword(), resource_address: document.getElementById('resource').value })
            });
            await refreshStatus();
        }

        async function applyConfig() {
            await api('/api/config', {
                method: 'POST',
                body: JSON.stringify({
                    password: currentPassword(),
                    waveform: document.getElementById('waveform').value,
                    frequency: Number(document.getElementById('frequency').value),
                    amplitude: Number(document.getElementById('amplitude').value),
                    offset: Number(document.getElementById('offset').value),
                    phase: Number(document.getElementById('phase').value)
                })
            });
            await refreshStatus();
        }

        async function setOutput(enabled) {
            await api('/api/output', {
                method: 'POST',
                body: JSON.stringify({ password: currentPassword(), enabled })
            });
            await refreshStatus();
        }

        async function saveProfile() {
            await api('/api/profiles', {
                method: 'POST',
                body: JSON.stringify({ password: currentPassword(), name: document.getElementById('profile-name').value })
            });
            await refreshStatus();
        }

        async function loadProfile(name) {
            await api('/api/profiles/load', {
                method: 'POST',
                body: JSON.stringify({ password: currentPassword(), name, apply_to_device: true })
            });
            await refreshStatus();
        }

        refreshStatus();
        heartbeat();
        setInterval(heartbeat, 5000);
        setInterval(refreshStatus, 15000);
    </script>
</body>
</html>
"""


class WebServer:
    def __init__(self, controller, host: str = "127.0.0.1", port: int = 8000):
        self.controller = controller
        self.host = host
        self.port = port
        self.session_tracker = SessionTracker(ttl_seconds=10)
        self._httpd = ThreadingHTTPServer((host, port), self._build_handler())
        self._thread = None

    def _build_handler(self):
        controller = self.controller
        session_tracker = self.session_tracker

        class Handler(BaseHTTPRequestHandler):
            def _json_response(self, payload, status=HTTPStatus.OK):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _read_json(self):
                length = int(self.headers.get("Content-Length", "0"))
                if length == 0:
                    return {}
                return json.loads(self.rfile.read(length).decode("utf-8"))

            def _success(self, extra=None):
                payload = controller.get_status()
                payload["online_users"] = session_tracker.active_count()
                if extra:
                    payload.update(extra)
                self._json_response(payload)

            def _handle_error(self, exc):
                status = HTTPStatus.FORBIDDEN if isinstance(exc, PermissionError) else HTTPStatus.BAD_REQUEST
                self._json_response({"error": str(exc)}, status=status)

            def do_GET(self):
                if self.path == "/":
                    body = HTML_PAGE.encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if self.path == "/api/status":
                    self._success()
                    return
                self.send_error(HTTPStatus.NOT_FOUND)

            def do_POST(self):
                parsed = urlparse(self.path)
                payload = self._read_json()
                try:
                    if parsed.path == "/api/session/heartbeat":
                        online = session_tracker.heartbeat(payload.get("client_id", "anonymous"))
                        self._json_response({"online_users": online})
                        return
                    if parsed.path == "/api/connect":
                        controller.connect_device(
                            password=payload.get("password"),
                            resource_address=payload.get("resource_address"),
                        )
                        self._success()
                        return
                    if parsed.path == "/api/config":
                        controller.update_waveform(payload["waveform"], password=payload.get("password"))
                        controller.update_parameters(
                            payload["frequency"],
                            payload["amplitude"],
                            payload["offset"],
                            payload["phase"],
                            password=payload.get("password"),
                        )
                        self._success()
                        return
                    if parsed.path == "/api/output":
                        if payload.get("enabled"):
                            controller.enable_output(password=payload.get("password"))
                        else:
                            controller.disable_output(password=payload.get("password"))
                        self._success()
                        return
                    if parsed.path == "/api/profiles":
                        controller.save_current_profile(payload["name"], password=payload.get("password"))
                        self._success()
                        return
                    if parsed.path == "/api/profiles/load":
                        profile = controller.load_profile(
                            payload["name"],
                            apply_to_device=bool(payload.get("apply_to_device")),
                            password=payload.get("password"),
                        )
                        self._success({"profile": profile})
                        return
                    if parsed.path == "/api/profiles/delete":
                        controller.delete_profile(payload["name"], password=payload.get("password"))
                        self._success()
                        return
                    if parsed.path == "/api/profiles/rename":
                        controller.rename_profile(
                            payload.get("old_name"),
                            payload.get("new_name"),
                            password=payload.get("password"),
                        )
                        self._success()
                        return
                    raise ValueError("Unsupported endpoint.")
                except Exception as exc:  # deliberate API boundary
                    self._handle_error(exc)

            def log_message(self, format: str, *args) -> None:
                return

        return Handler

    def start(self) -> Tuple[str, int]:
        if self._thread and self._thread.is_alive():
            return self.host, self.port
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self.host, self.port

    def stop(self):
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
