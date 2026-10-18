#!/usr/bin/env python3
"""Bounded Linux inventory over an existing trusted OpenSSH config alias.

No password input, sudo, package installation, benchmark or configuration writes.
Inventory can contain private network identifiers; review before sharing.
"""

import argparse
import os
import re
import selectors
import signal
import subprocess
import sys
import time

MAX_BYTES = 128 * 1024
TIMEOUT_SECONDS = 45
REMOTE_SCRIPT = r'''
export LC_ALL=C
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
section() { printf '\n## %s\n' "$1"; }
run() {
  if command -v "$1" >/dev/null 2>&1; then
    "$@" 2>&1 || printf '[unavailable or insufficient permission]\n'
  else
    printf '[command unavailable: %s]\n' "$1"
  fi
}
section os
run uname -srm
if [ -r /etc/os-release ]; then cat /etc/os-release; fi
section cpu
run getconf _NPROCESSORS_ONLN
section memory
run free -m
section block_devices
run lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT
section filesystem_capacity
run df -h -l
section filesystem_inodes
run df -i -l
section addresses
run ip -brief address
section routes_v4
run ip -4 route show
section routes_v6
run ip -6 route show
section listening_ports
run ss -lntu
section runtimes
if command -v systemctl >/dev/null 2>&1; then
  for service in docker containerd k3s k3s-agent ufw nftables firewalld; do
    printf '%s: ' "$service"
    systemctl is-active "$service" 2>/dev/null || :
  done
else
  printf '[systemctl unavailable]\n'
fi
section firewall_visibility
if [ "$(id -u)" = 0 ]; then
  run nft list ruleset
  run iptables -S
  run iptables -S DOCKER-USER
  run ip6tables -S
else
  printf '[firewall rules not collected without existing root access]\n'
fi
'''


def ssh_command(alias):
    """Alias only, never a user-controlled command or SSH option."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,252}", alias):
        raise ValueError("Use an SSH config alias with letters, digits, dots, underscores or hyphens")
    return [
        "ssh", "-T", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
        "-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=10",
        "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
        "-o", "ClearAllForwardings=yes", "-o", "PermitLocalCommand=no",
        alias, "sh -s",
    ]


def terminate(process):
    # Stop SSH and its local proxy children together; do not leave a pipe reader stuck.
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    except ProcessLookupError:
        process.wait()


def collect(command, script=REMOTE_SCRIPT, timeout=TIMEOUT_SECONDS, max_bytes=MAX_BYTES):
    """Bound memory/time, including large stderr and hosts that never close output."""
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, start_new_session=True,
    )
    output = bytearray()
    deadline = time.monotonic() + timeout
    try:
        process.stdin.write(script.encode())
        process.stdin.close()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Inventory timed out; results are incomplete")
                for key, _ in selector.select(min(remaining, 0.2)):
                    chunk = os.read(key.fileobj.fileno(), min(8192, max_bytes - len(output) + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    output.extend(chunk)
                    if len(output) > max_bytes:
                        raise ValueError("Inventory output limit exceeded; results are incomplete")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Inventory timed out")
        return process.wait(timeout=remaining), bytes(output)
    finally:
        if process.poll() is None:
            terminate(process)
        process.stdout.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-alias", required=True, help="Alias in your trusted SSH config")
    args = parser.parse_args(argv)
    try:
        command = ssh_command(args.ssh_alias)
        status, output = collect(command)
    except (ValueError, OSError, TimeoutError, subprocess.TimeoutExpired) as error:
        print(f"Inventory failed: {error}", file=sys.stderr)
        return 2
    # Remove terminal control/escape bytes from untrusted remote output.
    decoded = output.decode("utf-8", errors="replace")
    decoded = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", decoded)
    decoded = "".join(char for char in decoded if char in "\n\t" or (char.isprintable() and char != "\x7f"))
    print(decoded, end="")
    if status:
        print("\nInventory incomplete: SSH failed. Check access and trusted host key; no automatic retry.", file=sys.stderr)
    return status


if __name__ == "__main__":
    sys.exit(main())
