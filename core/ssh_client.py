"""
OVERDRIVE - Advanced SSH Connection & Command Streaming Engine
Supports dual authentication (private key auto-discovery / custom key path and password fallback),
real-time stdout/stderr streaming, and session keepalive.
"""

import os
import glob
import subprocess
import time
from typing import Tuple, List, Optional
import paramiko
from rich.console import Console

console = Console()

class SSHClientWrapper:
    def __init__(self, host: str, port: int = 22, username: str = "root", key_path: Optional[str] = None, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.key_path = key_path
        self.password = password
        self.client: Optional[paramiko.SSHClient] = None
        self.is_connected = False

    @staticmethod
    def discover_local_keys() -> List[str]:
        """Scans local ~/.ssh directory for common private keys"""
        home = os.path.expanduser("~")
        ssh_dir = os.path.join(home, ".ssh")
        found = []
        if os.path.exists(ssh_dir):
            for candidate in ["id_ed25519", "id_rsa", "id_ecdsa", "id_dsa"]:
                path = os.path.join(ssh_dir, candidate)
                if os.path.isfile(path):
                    found.append(path)
            # Also find any other private key files without .pub
            for f in glob.glob(os.path.join(ssh_dir, "*")):
                if os.path.isfile(f) and not f.endswith(".pub") and not f.endswith("known_hosts") and not f.endswith("config"):
                    if f not in found:
                        found.append(f)
        return found

    def connect(self) -> Tuple[bool, str]:
        """Establishes an SSH connection using key or password"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.key_path and os.path.exists(self.key_path):
                # Try connecting with key
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    passphrase=self.password if self.password else None,
                    timeout=12,
                    banner_timeout=15
                )
            elif self.password:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=12,
                    banner_timeout=15
                )
            else:
                return False, "No authentication method provided (neither key nor password)."
                
            self.is_connected = True
            return True, "Connected successfully."
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed. Invalid password or rejected SSH key."
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def execute_command(self, cmd: str, stream_output: bool = False) -> Tuple[int, str, str]:
        """Executes a remote command and returns (exit_code, stdout, stderr)"""
        if not self.is_connected or not self.client:
            raise RuntimeError("SSH client is not connected.")
            
        stdin, stdout, stderr = self.client.exec_command(cmd)
        
        out_lines = []
        err_lines = []
        
        if stream_output:
            for line in iter(stdout.readline, ""):
                line_clean = line.rstrip()
                out_lines.append(line_clean)
                console.print(f"  [dim #6d28d9]│[/dim #6d28d9] [white]{line_clean}[/white]")
            for line in iter(stderr.readline, ""):
                line_clean = line.rstrip()
                err_lines.append(line_clean)
                console.print(f"  [dim #f43f5e]│[/dim #f43f5e] [#fecdd3]{line_clean}[/#fecdd3]")
        else:
            out_lines = [l.rstrip() for l in stdout.readlines()]
            err_lines = [l.rstrip() for l in stderr.readlines()]
            
        exit_code = stdout.channel.recv_exit_status()
        return exit_code, "\n".join(out_lines), "\n".join(err_lines)

    def execute_script(self, script_content: str, stream_output: bool = False) -> Tuple[int, str, str]:
        """Executes a multi-line bash script on the remote system via stdin"""
        cleaned_script = script_content.replace("\r\n", "\n")
        cmd = "bash -s"
        stdin, stdout, stderr = self.client.exec_command(cmd)
        stdin.write(cleaned_script)
        stdin.flush()
        stdin.channel.shutdown_write()
        
        out_lines = []
        err_lines = []
        
        if stream_output:
            for line in iter(stdout.readline, ""):
                line_clean = line.rstrip()
                out_lines.append(line_clean)
                console.print(f"  [dim #6d28d9]│[/dim #6d28d9] [white]{line_clean}[/white]")
            for line in iter(stderr.readline, ""):
                line_clean = line.rstrip()
                err_lines.append(line_clean)
                console.print(f"  [dim #f43f5e]│[/dim #f43f5e] [#fecdd3]{line_clean}[/#fecdd3]")
        else:
            out_lines = [l.rstrip() for l in stdout.readlines()]
            err_lines = [l.rstrip() for l in stderr.readlines()]
            
        exit_code = stdout.channel.recv_exit_status()
        return exit_code, "\n".join(out_lines), "\n".join(err_lines)

    def close(self):
        """Closes the active SSH connection"""
        if self.client:
            self.client.close()
            self.is_connected = False
