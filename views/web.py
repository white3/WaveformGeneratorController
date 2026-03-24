import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple
from urllib.parse import urlparse

from models.session_tracker import SessionTracker


HTML_PAGE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <title>33500B Web Console</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 24px; background: #f4f7fb; color: #223; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
        .card { background: white; border-radius: 10px; padding: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
        input, select, button { width: 100%; margin-top: 6px; margin-bottom: 10px; padding: 8px; }
        button { cursor: pointer; }
        code { background: #eef3ff; padding: 2px 6px; border-radius: 4px; }
        ul { padding-left: 20px; }
    </style>
</head>
<body>
    <h1>Keysight 33500B Controller</h1>
    <p>在线人数：<strong id=\"online-count\">0</strong></p>
    <div class=\"grid\">
        <div class=\"card\">
            <h2>设备状态</h2>
            <div id=\"status\"></div>
            <button onclick=\"refreshStatus()\">刷新状态</button>
        </div>
        <div class=\"card\">
            <h2>受保护控制</h2>
            <label>控制密码</label>
            <input id=\"password\" type=\"password\" placeholder=\"输入控制密码\" />
            <label>资源地址</label>
            <select id=\"resource\"></select>
            <button onclick=\"connectDevice()\">连接设备</button>
            <label>Waveform</label>
            <select id=\"waveform\"><option>SIN</option><option>SQU</option><option>TRI</option><option>RAMP</option></select>
            <label>Frequency</label><input id=\"frequency\" type=\"number\" value=\"1000\" />
            <label>Amplitude</label><input id=\"amplitude\" type=\"number\" value=\"1\" />
            <label>Offset</label><input id=\"offset\" type=\"number\" value=\"0\" />
            <label>Phase</label><input id=\"phase\" type=\"number\" value=\"0\" />
            <button onclick=\"applyConfig()\">应用配置</button>
            <button onclick=\"setOutput(true)\">开启输出</button>
            <button onclick=\"setOutput(false)\">关闭输出</button>
        </div>
        <div class=\"card\">
            <h2>SQLite 配置缓存</h2>
            <label>配置名称</label>
            <input id=\"profile-name\" placeholder=\"例如 startup-default\" />
            <button onclick=\"saveProfile()\">保存当前配置</button>
            <button onclick=\"loadSelectedProfile(true)\">加载并应用选中配置</button>
            <ul id=\"profiles\"></ul>
        </div>
    </div>
    <script>
        const clientId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
        let selectedProfile = null;

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
            const profiles = document.getElementById('profiles');
            profiles.innerHTML = '';
            data.profiles.forEach((profile) => {
                const li = document.createElement('li');
                const button = document.createElement('button');
                button.textContent = `${profile.name} (${profile.waveform}, ${profile.frequency}Hz)`;
                button.onclick = () => { selectedProfile = profile.name; };
                li.appendChild(button);
                profiles.appendChild(li);
            });
        }

        async function heartbeat() {
            const data = await api('/api/session/heartbeat', {
                method: 'POST',
                body: JSON.stringify({ client_id: clientId })
            });
            document.getElementById('online-count').innerText = data.online_users;
        }

        function currentPassword() {
            return document.getElementById('password').value;
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

        async function loadSelectedProfile(applyToDevice) {
            if (!selectedProfile) {
                alert('请先选中一个配置');
                return;
            }
            await api('/api/profiles/load', {
                method: 'POST',
                body: JSON.stringify({ password: currentPassword(), name: selectedProfile, apply_to_device: applyToDevice })
            });
            await refreshStatus();
        }

        refreshStatus();
        heartbeat();
        setInterval(heartbeat, 10000);
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
        self.session_tracker = SessionTracker()
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
