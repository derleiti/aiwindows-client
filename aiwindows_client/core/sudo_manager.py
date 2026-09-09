"""Windows elevation helpers. Kept API-compatible with the Linux client."""
from __future__ import annotations
import ctypes, subprocess, sys
from pathlib import Path

class SudoManager:
    def is_admin(self) -> bool:
        try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception: return False
    def run(self, args, cwd=None) -> int:
        if isinstance(args, str):
            command=args
        else:
            command=subprocess.list2cmdline([str(x) for x in args])
        if self.is_admin():
            return subprocess.run(command, cwd=cwd, shell=True, check=False).returncode
        rc=ctypes.windll.shell32.ShellExecuteW(None,"runas","cmd.exe",f'/c {command}',str(cwd or Path.home()),1)
        return 0 if rc > 32 else 1

_manager=SudoManager()
def get_sudo_manager(): return _manager
def sudo_run(args, cwd=None): return _manager.run(args,cwd)
def sudo_restart_service(service): return _manager.run(["sc.exe","stop",service]) or _manager.run(["sc.exe","start",service])
def sudo_write_file(path, content):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding="utf-8"); return True
