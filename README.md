# OVERDRIVE // CLI
> *Linux Kernel, Network & System Performance Optimizer*

[![Author: nullbyte](https://img.shields.io/badge/Author-nullbyte-a855f7.svg)](https://github.com/nullbytee1)
[![License: MIT](https://img.shields.io/badge/License-MIT-34d399.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-c084fc.svg)](https://www.python.org/downloads/)
[![Tests: 36 Passing](https://img.shields.io/badge/Tests-36%20Passing-34d399.svg)](tests/)

**OVERDRIVE** is an open-source Linux kernel, network, and system performance optimization CLI tool. It provides real-time hardware telemetry, an interactive terminal dashboard, and remote server tuning over encrypted SSH.

OVERDRIVE tunes kernel networking parameters, TCP window buffers, multi-core CPU queue balancing, memory governance, storage I/O, DNS resolution, and SSH latency with automated pre-flight safety backups.

---

## 🖥️ Interface Preview

### 🔐 Remote Node Authentication & Multi-Server Profile Manager
![OVERDRIVE CLI Connection Wizard & Profile Manager](https://github.com/nullbytee1/overdrive-cli/raw/main/assets/connect_preview.png)

### 📊 Live Telemetry & Kernel Optimization Dashboard
![OVERDRIVE CLI Live Telemetry & Optimization Dashboard](https://github.com/nullbytee1/overdrive-cli/raw/main/assets/preview.png)

---

## ⚙️ Architectural Subsystems & Module Breakdown

### 1. Full-Stack System Optimization (Automated)
* **Technical Function**: Master orchestrator that executes all 10 optimization tiers sequentially in automated, conflict-free dependency order.
* **Problem Solved**: Manually configuring dozens of kernel sysctl directives, systemd services, ulimits, and firewall tables is error-prone. God Mode runs a single pass with automated pre-flight safety backups, applying a complete production baseline in under 15 seconds.

### 2. Kernel BBRv3 / BBR & TCP Window Buffers
* **Technical Function**: Auto-probes the running Linux kernel for `BBRv3`, `BBR2`, or `BBR` congestion control, paired with `CAKE` or `FQ` queue disciplines, and expands dynamic TCP socket memory buffers up to 64MB (`rmem_max` / `wmem_max`).
* **Problem Solved**: Legacy loss-based congestion algorithms (`Cubic`, `Reno`) misinterpret shallow packet loss as network congestion, prematurely cutting throughput by 50%. BBR models real-time bandwidth and bottleneck round-trip time, unlocking full bandwidth utilization across high-latency international transit.

### 3. TCP MSS Path MTU Clamping (1360)
* **Technical Function**: Clamps the TCP Maximum Segment Size (`TCPMSS`) to `1360` bytes using persistent Netfilter (`iptables -t mangle`) rules managed by an auto-reloading systemd unit.
* **Problem Solved**: Mobile carriers (4G/5G/LTE), cellular tunneling (GTP-U), and VPN overlays (WireGuard, VLESS, VMess) add packet encapsulation overhead. Standard 1500-byte MTU packets exceed path MTU limits and get dropped by carrier firewalls without ICMP responses ("Path MTU Black Hole"). Clamping to 1360 prevents packet fragmentation worldwide.

### 4. Multi-Core RPS/XPS Network Queue Steering
* **Technical Function**: Calculates CPU affinity bitmasks across all available CPU cores and binds them to network interface receive and transmit queues (`/sys/class/net/*/queues/rx-*/rps_cpus`).
* **Problem Solved**: Default Linux network drivers process all inbound packets on `CPU0`, causing a single core to peg at 100% under high traffic while remaining cores sit idle. RPS/XPS spreads SoftIRQ interrupts evenly across all vCPUs.

### 5. Memory Governance, Swap & Process Limits
* **Technical Function**: Provisions an NVMe/SSD swapfile (tuned with `vm.swappiness=10`), enforces Go runtime memory governance (`GOMEMLIMIT=90%`), accelerates garbage collection memory reclaiming (`madvdontneed`), and raises system-wide file descriptor limits to `1,048,576`.
* **Problem Solved**: Protects critical services from kernel `OOM-killer` termination during memory spikes and prevents high-concurrency proxies from throwing `"Too many open files"` socket errors.

### 6. Storage I/O Scheduler & Dirty Writeback Tuning
* **Technical Function**: Sets block device readahead to `1024 KB` via persistent udev rules and tunes kernel dirty page memory writeback ratios (`vm.dirty_background_ratio=5`, `vm.dirty_ratio=10`).
* **Problem Solved**: Prevents system-wide I/O micro-stutters and blocking disk write stalls during heavy logging or database transactions by flushing dirty pages smoothly in the background.

### 7. System DNS Optimization (Anycast Resolvers)
* **Technical Function**: Configures Anycast resolvers (Cloudflare `1.1.1.1`, Google `8.8.8.8`) with `options single-request-reopen` and parallel resolution in `/etc/resolv.conf`.
* **Problem Solved**: Resolves DNS lookup latency when establishing outbound connections and prevents dual-stack IPv4/IPv6 socket lookup collisions.

### 8. SSH Daemon Latency & Security Hardening
* **Technical Function**: Disables reverse DNS resolution (`UseDNS no`), strips GSSAPI authentication delays, enforces keepalive pings (`ClientAliveInterval 30`), and verifies syntax (`sshd -t`) before reloading `sshd`.
* **Problem Solved**: Eliminates the 3-5 second login delay when connecting over SSH and prevents idle terminal sessions from dropping.

### 9. Base System Provisioning & Entropy Daemon
* **Technical Function**: Updates repository mirrors, installs core diagnostic toolchains (`curl`, `socat`, `jq`, `iperf3`, `mtr`, `haveged`), syncs server timezones with GeoIP datacenter location, and opens QUIC / HTTP/3 UDP ports (`443/udp`).
* **Problem Solved**: The `haveged` daemon provides hardware entropy to prevent cryptographic TLS handshake delays, while timezone synchronization ensures log timestamps align accurately.

### 10. Kernel Bootloader & GRUB Parameter Tuning
* **Technical Function**: Injects kernel boot parameters (`transparent_hugepage=madvise`, `elevator=none`) into `/etc/default/grub` and updates the bootloader.
* **Problem Solved**: Reduces memory allocation latency and allows virtual machines to utilize host hypervisor I/O schedulers directly without guest scheduling overhead.

### 11. Proxy Engine Socket Optimization (3x-ui / Xray)
* **Technical Function**: Injects low-latency TCP socket parameters (`TCP_NODELAY`, `SO_KEEPALIVE`, `TCP_FASTOPEN`), cached DNS rules, and global SNIs into `3x-ui` (`/etc/x-ui/x-ui.db`) and `xray-core`.
* **Problem Solved**: Eliminates connection establishment latency via 0-RTT FastOpen and prevents proxy socket timeouts on long-lived connections.

### 12. VPS Hardware & Compute Benchmark
* **Technical Function**: Runs genuine hardware stress tests: CPU SHA-256 hash throughput (Ops/sec), RAM memory copy bandwidth (GB/s), direct sync disk write I/O (MB/s), and real-time CDN edge download throughput (Mbps).
* **Problem Solved**: Provides authentic, non-simulated performance metrics to benchmark server capabilities before and after tuning.

### 13. Multi-Region Network Transit & Jitter Benchmark
* **Technical Function**: Measures real-time ICMP round-trip latency, jitter, and packet loss across 6 true unicast looking-glass gateways (Frankfurt, London, New York, San Jose, Singapore, Tokyo).
* **Problem Solved**: Verifies international routing quality and identifies routing anomalies across global backbone paths.

### 🔍 System Diagnostic Verification Matrix (Audit) (`[A]`)
* **Technical Function**: Non-destructive, read-only audit matrix verifying kernel congestion control, QDiscs, buffers, Netfilter tables, RPS masks, memory limits, DNS, and SSH configuration.

### ↺ System Configuration Rollback & Restore (`[R]`)
* **Technical Function**: Restores `/etc/sysctl.d/`, `/etc/ssh/`, Netfilter tables, and proxy databases from pre-flight backups, with an explicit safety confirmation modal (`REVERT` / `Y`).

---

## 🚀 Quickstart & Installation

### Option 1: One-Line Quick Install
```bash
curl -sSL https://raw.githubusercontent.com/nullbytee1/overdrive-cli/main/run.sh | bash
```

### Option 2: Clone & Run via Python
```bash
git clone https://github.com/nullbytee1/overdrive-cli.git
cd overdrive-cli

# Install dependencies
pip install -r requirements.txt

# Launch OVERDRIVE
python overdrive.py
```

### Option 3: Windows Quick Launch
```cmd
run.bat
```

---

## ⌨️ Keyboard Controls

| Key | Action |
| :--- | :--- |
| `↑` / `↓` or `W` / `S` | Navigate modules in real time |
| `ENTER` | Execute selected module |
| `1` – `13` | Direct numeric module shortcut |
| `A` | Run 18-Point System Diagnostic Audit |
| `E` | Export Black & White Monochrome Terminal HTML Report to `./reports/` |
| `R` | 1-Click Rollback & restore from pre-flight backups |
| `Q` / `ESC` | Safely disconnect SSH session and exit |

---

## 🧪 Automated Test Suite

OVERDRIVE includes a complete unit and integration test suite:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

```text
Ran 36 tests in 0.838s
OK
```

---

## 🔒 Safety & Idempotency

- **Automated Pre-Flight Backups**: Archives `/etc/sysctl.d/`, `/etc/ssh/sshd_config`, `/etc/hosts`, `/etc/default/grub`, and databases prior to any modification.
- **Strict Idempotency**: Running modules multiple times or running "God Mode" on a pre-configured server will never create duplicate rules or corrupt settings.
- **Zero-Flicker Live UI**: Built using Rich's `Live` terminal rendering for smooth, flicker-free telemetry and navigation.

---

## 📄 License

Created by **[nullbyte](https://github.com/nullbytee1)**.

Distributed under the **MIT License**. Free for personal and commercial use.
