from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


TASKS: dict[str, dict[str, object]] = {
    "task-1": {"id": "task-1", "title": "Write docs", "completed": False},
}


class TodoHandler(BaseHTTPRequestHandler):
    server_version = "safe-oas2mcp-todo-demo/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/tasks":
            self._json({"error": "not found"}, status=404)
            return

        status = parse_qs(parsed.query).get("status", [None])[0]
        tasks = list(TASKS.values())
        if status == "done":
            tasks = [task for task in tasks if task.get("completed") is True]
        if status == "open":
            tasks = [task for task in tasks if task.get("completed") is False]
        self._json({"items": tasks})

    def do_POST(self) -> None:
        if self.path != "/tasks":
            self._json({"error": "not found"}, status=404)
            return

        body = self._body()
        task_id = f"task-{len(TASKS) + 1}"
        task = {
            "id": task_id,
            "title": body.get("title", "Untitled"),
            "completed": False,
        }
        TASKS[task_id] = task
        self._json(task, status=201)

    def do_PATCH(self) -> None:
        prefix = "/tasks/"
        if not self.path.startswith(prefix):
            self._json({"error": "not found"}, status=404)
            return

        task_id = self.path[len(prefix) :]
        task = TASKS.get(task_id)
        if task is None:
            self._json({"error": "not found"}, status=404)
            return

        task.update(self._body())
        self._json(task)

    def do_DELETE(self) -> None:
        prefix = "/tasks/"
        if not self.path.startswith(prefix):
            self._json({"error": "not found"}, status=404)
            return

        task_id = self.path[len(prefix) :]
        TASKS.pop(task_id, None)
        self.send_response(204)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return

    def _body(self) -> dict[str, object]:
        length = int(self.headers.get("content-length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _json(self, data: object, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8088), TodoHandler)
    print("Todo demo API listening on http://127.0.0.1:8088")
    server.serve_forever()


if __name__ == "__main__":
    main()
