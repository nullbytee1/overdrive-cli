"""
OVERDRIVE - Comprehensive End-to-End Test Suite
Validates all subsystems, edge cases, state management, report generation, and module integrity.
"""

import os
import sys
import unittest
import json
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.ansi_colorizer import AnsiColorizer, PRESET_PALETTES, hex_to_rgb, lerp_rgb
from core.ascii_engine import (
    AsciiMotion,
    OVERDRIVE_BANNER,
    BANNER_BOX_INNER_WIDTH,
    BANNER_HEADER_TITLE,
    strip_ansi,
    get_display_cell_width
)
from core.logger import Logger
from core.session_manager import SessionManager, CONFIG_DIR, SERVERS_FILE
from core.system_detector import SystemDetector
from core.telemetry import TelemetryData, TelemetryCollector
from core.report_generator import ReportGenerator, REPORTS_DIR
from core.ui_components import render_server_badge, render_audit_table
from core.interactive_menu import InteractiveMenu, MODULE_METADATA, render_meter, NonBlockingKeyReader
from core.ssh_client import SSHClientWrapper

from modules.base_module import BaseOptimizerModule
from modules.system_provisioning import SystemProvisioningOptimizer
from modules.kernel_bbr import KernelBBROptimizer
from modules.carrier_mss import CarrierMSSOptimizer
from modules.multicore_rps import MultiCoreRPSOptimizer
from modules.memory_limits import MemoryLimitsOptimizer
from modules.storage_io import StorageIOOptimizer
from modules.dns_accelerator import DNSAcceleratorOptimizer
from modules.ssh_hardening import SSHHardenOptimizer
from modules.grub_tuning import GRUBPerformanceOptimizer
from modules.xray_3xui import Xray3xuiOptimizer
from modules.overdrive_master import OverdriveMasterOptimizer
from modules.vps_benchmark import VPSBenchmarkOptimizer
from modules.benchmark_module import BenchmarkModule, GLOBAL_GATEWAYS
from modules.rollback_module import RollbackModule
from audits.system_auditor import SystemAuditor
from core.updater import UpdateManager
from core.version import __version__
import core.theme as theme


class TestAnsiColorizer(unittest.TestCase):
    def test_hex_to_rgb(self):
        self.assertEqual(hex_to_rgb("#ffffff"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("#000000"), (0, 0, 0))
        self.assertEqual(hex_to_rgb("a855f7"), (168, 85, 247))

    def test_lerp_rgb(self):
        c1 = (0, 0, 0)
        c2 = (100, 200, 50)
        mid = lerp_rgb(c1, c2, 0.5)
        self.assertEqual(mid, (50, 100, 25))

    def test_colorize_text_all_palettes(self):
        sample = "OVERDRIVE Performance"
        for palette_name in PRESET_PALETTES:
            colored, plain = AnsiColorizer.colorize_text(sample, palette=palette_name)
            self.assertEqual(plain, sample)
            self.assertIn("\x1b[", colored)

    def test_colorize_empty_and_spaces(self):
        colored, plain = AnsiColorizer.colorize_text("", palette="neon-purple-gradient")
        self.assertEqual(colored, "")
        self.assertEqual(plain, "")

        colored_spaces, plain_spaces = AnsiColorizer.colorize_text("   \t  ", keep_spaces=False)
        self.assertEqual(plain_spaces, "   \t  ")

    def test_colorize_no_color(self):
        with patch.object(AnsiColorizer, "is_no_color_enabled", return_value=True):
            sample = "TEST"
            colored, plain = AnsiColorizer.colorize_text(sample)
            self.assertEqual(colored, sample)
            self.assertEqual(plain, sample)


class TestAsciiMotion(unittest.TestCase):
    def test_strip_ansi(self):
        colored = "\x1b[38;2;168;85;247mOVERDRIVE\x1b[0m"
        self.assertEqual(strip_ansi(colored), "OVERDRIVE")
        self.assertEqual(strip_ansi("PLAIN_TEXT"), "PLAIN_TEXT")

    def test_get_display_cell_width(self):
        self.assertEqual(get_display_cell_width("OVERDRIVE"), 9)
        self.assertEqual(get_display_cell_width("\x1b[1mOVERDRIVE\x1b[0m"), 9)
        self.assertEqual(get_display_cell_width(BANNER_HEADER_TITLE), 33)

    def test_render_centered_banner_frame(self):
        frame = AsciiMotion.render_centered_banner_frame(wave=False)
        self.assertIsNotNone(frame)
        rendered_plain = frame.plain
        lines = rendered_plain.splitlines()
        
        # Top border
        self.assertTrue(lines[0].startswith("╭"))
        self.assertTrue(lines[0].endswith("╮"))
        self.assertEqual(get_display_cell_width(lines[0]), BANNER_BOX_INNER_WIDTH + 2)
        
        # Header line
        self.assertTrue(lines[1].startswith("│"))
        self.assertTrue(lines[1].endswith("│"))
        self.assertIn(BANNER_HEADER_TITLE, lines[1])
        self.assertEqual(get_display_cell_width(lines[1]), BANNER_BOX_INNER_WIDTH + 2)
        
        # Bottom border
        self.assertTrue(lines[-1].startswith("╰"))
        self.assertTrue(lines[-1].endswith("╯"))
        self.assertEqual(get_display_cell_width(lines[-1]), BANNER_BOX_INNER_WIDTH + 2)

    def test_artwork_bounding_box_centering(self):
        max_artwork_w = max(get_display_cell_width(line) for line in OVERDRIVE_BANNER)
        self.assertEqual(max_artwork_w, 71)
        
        left_pad = (BANNER_BOX_INNER_WIDTH - max_artwork_w) // 2
        self.assertEqual(left_pad, 2)
        
        # Total inner width is 76, artwork width is 71, left pad is 2 -> right space is 76 - (71 + 2) = 3
        right_space = BANNER_BOX_INNER_WIDTH - (max_artwork_w + left_pad)
        self.assertEqual(right_space, 3)
        self.assertLessEqual(abs(left_pad - right_space), 1)



class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher_dir = patch("core.session_manager.CONFIG_DIR", self.test_dir)
        self.patcher_file = patch("core.session_manager.SERVERS_FILE", os.path.join(self.test_dir, "servers.json"))
        self.patcher_dir.start()
        self.patcher_file.start()

    def tearDown(self):
        self.patcher_file.stop()
        self.patcher_dir.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_retrieve_server(self):
        self.assertEqual(SessionManager.get_all_servers(), [])
        self.assertIsNone(SessionManager.get_last_server())

        saved = SessionManager.save_server(
            host="1.2.3.4",
            port=22,
            username="root",
            auth_type="key",
            key_path="/id_ed25519",
            label="Node-1"
        )
        self.assertTrue(saved)
        servers = SessionManager.get_all_servers()
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["host"], "1.2.3.4")
        self.assertEqual(servers[0]["label"], "Node-1")

        last = SessionManager.get_last_server()
        self.assertIsNotNone(last)
        self.assertEqual(last["host"], "1.2.3.4")

    def test_update_existing_server(self):
        SessionManager.save_server("1.1.1.1", 22, "root", "key", label="Node-A")
        SessionManager.save_server("1.1.1.1", 22, "root", "password", label="Node-A-Updated")
        servers = SessionManager.get_all_servers()
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["label"], "Node-A-Updated")
        self.assertEqual(servers[0]["auth_type"], "password")

    def test_delete_server(self):
        SessionManager.save_server("1.1.1.1", 22, "root", "key", label="Node-1")
        SessionManager.save_server("2.2.2.2", 22, "root", "password", label="Node-2")
        self.assertEqual(len(SessionManager.get_all_servers()), 2)

        deleted = SessionManager.delete_server(0)
        self.assertTrue(deleted)
        self.assertEqual(len(SessionManager.get_all_servers()), 1)
        self.assertEqual(SessionManager.get_all_servers()[0]["host"], "1.1.1.1")

    def test_render_cards(self):
        SessionManager.save_server("1.1.1.1", 22, "root", "key", label="Singapore Edge")
        servers = SessionManager.get_all_servers()
        panel_table = SessionManager.render_server_selector(servers)
        self.assertIsNotNone(panel_table)

        panel_card = SessionManager.render_session_card(servers[0])
        self.assertIsNotNone(panel_card)


class TestSystemDetector(unittest.TestCase):
    def test_detect_all_parsing(self):
        mock_ssh = MagicMock()
        mock_output = (
            "x86_64\n===UNAME===\n6.8.0-generic\n===VIRT===\nkvm\n"
            "===CPU===\n4\nIntel Core Processor\n"
            "===MEM===\n4194304\n"
            "===NET===\neth0\n"
            "===MTU===\n2: eth0: <BROADCAST> mtu 1500\n"
            "===DISKS===\nvda 0 disk\n"
            "===STACKS===\n3x-ui\nxray-core\n"
            "===CONG===\nbbr\n===QDISC===\nfq"
        )
        mock_ssh.execute_command.return_value = (0, mock_output, "")
        info = SystemDetector.detect_all(mock_ssh)

        self.assertEqual(info["arch"], "x86_64")
        self.assertEqual(info["kernel"], "6.8.0-generic")
        self.assertEqual(info["cpu_cores"], 4)
        self.assertEqual(info["mem_total_gb"], 4.0)
        self.assertEqual(info["primary_iface"], "eth0")
        self.assertEqual(info["current_mtu"], 1500)
        self.assertTrue(info["has_3xui"])
        self.assertTrue(info["has_xray"])
        self.assertFalse(info["is_container"])

    def test_detect_all_container(self):
        mock_ssh = MagicMock()
        mock_output = "aarch64\n===UNAME===\n5.15.0\n===VIRT===\nlxc\n===CPU===\n2\n===MEM===\n1048576"
        mock_ssh.execute_command.return_value = (0, mock_output, "")
        info = SystemDetector.detect_all(mock_ssh)

        self.assertEqual(info["arch"], "aarch64")
        self.assertTrue(info["is_container"])
        self.assertIn("Container (LXC)", info["virt"])
        self.assertEqual(info["cpu_cores"], 2)


class TestTelemetryData(unittest.TestCase):
    def test_sparkline_generation(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        spark = TelemetryData.format_sparkline(data, width=8)
        self.assertEqual(len(spark), 8)

        const_data = [5.0, 5.0, 5.0, 5.0]
        spark_const = TelemetryData.format_sparkline(const_data, width=4)
        self.assertEqual(len(spark_const), 4)

        spark_empty = TelemetryData.format_sparkline([], width=8)
        self.assertEqual(len(spark_empty), 8)

    def test_telemetry_snapshot(self):
        t = TelemetryData()
        t.update({
            "cpu_pct": 25.0,
            "mem_pct": 50.0,
            "ping_rtt_ms": 1.5,
            "load_avg": "0.10, 0.05, 0.01"
        })
        snap = t.get_snapshot()
        self.assertEqual(snap["cpu_pct"], 25.0)
        self.assertEqual(snap["mem_pct"], 50.0)
        self.assertEqual(snap["ping_rtt_ms"], 1.5)
        self.assertTrue(snap["is_healthy"])


class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch("core.report_generator.REPORTS_DIR", self.test_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_report_monochrome_html(self):
        topo = {
            "cpu_cores": 4, "arch": "x86_64", "mem_total_mb": 4096, "mem_total_gb": 4.0,
            "virt": "KVM", "primary_iface": "eth0", "current_mtu": 1500, "kernel": "Linux 6.8",
            "detected_stacks": ["3x-ui"]
        }
        audits = [
            {"layer": "Kernel BBR", "param": "tcp_congestion_control", "value": "bbr", "pass": True}
        ]
        bench = [
            {"region": "Singapore", "gateway": "1.1.1.1", "avg_rtt": "1.2", "jitter": "0.1", "tier": "SUB-30MS"}
        ]
        res = ReportGenerator.export_audit_report("1.2.3.4", "root", topo, audits, bench)
        self.assertTrue(os.path.exists(res["md_path"]))
        self.assertTrue(os.path.exists(res["html_path"]))

        with open(res["html_path"], "r", encoding="utf-8") as f:
            html = f.read()
            self.assertIn("#OVERDRIVE", html)
            self.assertIn("TARGET NODE", html)
            self.assertIn("1.2.3.4", html)
            self.assertIn("JetBrains Mono", html)


class TestOptimizationModules(unittest.TestCase):
    def test_all_modules_instantiate(self):
        mods = [
            SystemProvisioningOptimizer(),
            KernelBBROptimizer(),
            CarrierMSSOptimizer(),
            MultiCoreRPSOptimizer(),
            MemoryLimitsOptimizer(),
            StorageIOOptimizer(),
            DNSAcceleratorOptimizer(),
            SSHHardenOptimizer(),
            GRUBPerformanceOptimizer(),
            Xray3xuiOptimizer(),
            OverdriveMasterOptimizer(),
            VPSBenchmarkOptimizer(),
            BenchmarkModule(),
            RollbackModule()
        ]
        for m in mods:
            self.assertIsInstance(m, BaseOptimizerModule)
            self.assertTrue(len(m.name) > 0)
            self.assertTrue(len(m.description) > 0)
            self.assertTrue(len(m.category) > 0)

    def test_provisioning_module(self):
        mod = SystemProvisioningOptimizer()
        mock_ssh = MagicMock()
        mock_ssh.execute_script.return_value = (0, "Success", "")
        mock_ssh.execute_command.return_value = (0, "UTC 2026---3", "")
        mock_console = MagicMock()
        success, msg = mod.run(mock_ssh, mock_console)
        self.assertTrue(success)
        v = mod.verify(mock_ssh, mock_console)
        self.assertTrue(v["pass"])

    def test_ssh_hardening_module(self):
        mod = SSHHardenOptimizer()
        mock_ssh = MagicMock()
        mock_ssh.execute_script.return_value = (0, "SSHD OK", "")
        mock_ssh.execute_command.return_value = (0, "UseDNS no\nClientAliveInterval 30", "")
        mock_console = MagicMock()
        success, msg = mod.run(mock_ssh, mock_console)
        self.assertTrue(success)
        v = mod.verify(mock_ssh, mock_console)
        self.assertTrue(v["pass"])

    def test_dns_accelerator_module(self):
        mod = DNSAcceleratorOptimizer()
        mock_ssh = MagicMock()
        mock_ssh.execute_script.return_value = (0, "DNS OK", "")
        mock_ssh.execute_command.return_value = (0, "nameserver 1.1.1.1\noptions single-request-reopen", "")
        mock_console = MagicMock()
        success, msg = mod.run(mock_ssh, mock_console)
        self.assertTrue(success)
        v = mod.verify(mock_ssh, mock_console)
        self.assertTrue(v["pass"])

    def test_grub_tuning_module(self):
        mod = GRUBPerformanceOptimizer()
        mock_ssh = MagicMock()
        mock_ssh.execute_script.return_value = (0, "GRUB OK", "")
        mock_ssh.execute_command.return_value = (0, "transparent_hugepage=madvise", "")
        mock_console = MagicMock()
        success, msg = mod.run(mock_ssh, mock_console)
        self.assertTrue(success)
        v = mod.verify(mock_ssh, mock_console)
        self.assertTrue(v["pass"])

    def test_vps_benchmark_module(self):
        mod = VPSBenchmarkOptimizer()
        mock_ssh = MagicMock()
        mock_ssh.execute_command.side_effect = [
            (0, "450000", ""),           # CPU
            (0, "6.2 GB/s", ""),          # RAM
            (0, "520 MB/s", ""),          # Disk
            (0, "45000000.0", "")         # Network
        ]
        mock_console = MagicMock()
        success, msg = mod.run(mock_ssh, mock_console)
        self.assertTrue(success)
        self.assertIn("Ops/sec", mod.last_benchmark_data["cpu_score"])
        self.assertIn("GB/s", mod.last_benchmark_data["ram_speed_gb"])

    def test_benchmark_module_parsing(self):
        bm = BenchmarkModule()
        mock_ssh = MagicMock()
        mock_ssh.execute_command.return_value = (
            0,
            "3 packets transmitted, 3 received, 0% packet loss, time 2002ms\nrtt min/avg/max/mdev = 1.100/1.250/1.400/0.120 ms",
            ""
        )
        mock_console = MagicMock()
        success, msg = bm.run(mock_ssh, mock_console)
        self.assertTrue(success)
        self.assertEqual(len(bm.last_results), len(GLOBAL_GATEWAYS))
        self.assertEqual(bm.last_results[0]["avg_rtt"], "1.2")
        self.assertEqual(bm.last_results[0]["packet_loss"], "0%")

    def test_rollback_module_run(self):
        rb = RollbackModule()
        mock_ssh = MagicMock()
        mock_ssh.execute_script.return_value = (0, "Rollback success", "")
        mock_console = MagicMock()
        success, msg = rb.run(mock_ssh, mock_console)
        self.assertTrue(success)
        self.assertIn("Rollback successfully completed", msg)

    def test_overdrive_master_run(self):
        om = OverdriveMasterOptimizer()
        mock_ssh = MagicMock()
        mock_ssh.execute_command.return_value = (0, "x86_64\n===UNAME===\n6.8.0\n===VIRT===\nkvm", "")
        mock_ssh.execute_script.return_value = (0, "All OK", "")
        mock_console = MagicMock()
        success, msg = om.run(mock_ssh, mock_console)
        self.assertTrue(success)


class TestInteractiveMenu(unittest.TestCase):
    def test_menu_metadata_structure(self):
        ids = [m["id"] for m in MODULE_METADATA]
        expected = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "A", "E", "R", "Q"]
        self.assertEqual(ids, expected)

    def test_render_meter(self):
        m0 = render_meter(0.0, 8)
        self.assertIn("░", m0)
        m100 = render_meter(100.0, 8)
        self.assertIn("█", m100)
        m50 = render_meter(50.0, 8)
        self.assertIn("█", m50)
        self.assertIn("░", m50)

    def test_render_full_dashboard(self):
        t = TelemetryData()
        snap = t.get_snapshot()
        table = InteractiveMenu.render_full_dashboard(0, "1.2.3.4", "root", snap)
        self.assertIsNotNone(table)


class TestSystemAuditor(unittest.TestCase):
    def test_system_auditor_run(self):
        mock_ssh = MagicMock()
        mock_ssh.execute_command.side_effect = [
            # Top discovery probe
            (0, "x86_64\n===UNAME===\n6.8.0\n===VIRT===\nkvm", ""),
            # Sysctl
            (0, "net.ipv4.tcp_congestion_control = bbr\nnet.core.default_qdisc = fq\nnet.core.rmem_max = 67108864\nnet.ipv4.tcp_notsent_lowat = 4294967295\nnet.ipv4.tcp_mtu_probing = 1\nnet.core.netdev_budget = 600", ""),
            # MSS
            (0, "TCPMSS set 1360\nTCPMSS set 1360\nTCPMSS set 1360", ""),
            # RPS
            (0, "active", ""),
            # Memory & Swap
            (0, "/swapfile partition\nGOMEMLIMIT=1300MiB", ""),
            # FD & Memlock
            (0, "1048576", ""),
            # Readahead
            (0, "1024", ""),
            # DNS
            (0, "nameserver 1.1.1.1\nnameserver 8.8.8.8", ""),
            # SSH
            (0, "UseDNS no", ""),
            # NTP
            (0, "System clock synchronized: yes", ""),
            # haveged
            (0, "active", ""),
            # hosts
            (0, "127.0.1.1 ubuntu-node", ""),
            # Ping
            (0, "time=1.23 ms", "")
        ]
        mock_console = MagicMock()
        results = SystemAuditor.run_full_audit(mock_ssh, mock_console)
        self.assertEqual(len(results), 18)
        self.assertTrue(all(r["pass"] for r in results))

class TestThemeSystem(unittest.TestCase):
    def test_theme_tokens_present(self):
        self.assertTrue(theme.BRAND_PURPLE.startswith("#"))
        self.assertTrue(theme.BRAND_LAVENDER.startswith("#"))
        self.assertTrue(theme.BRAND_LILAC.startswith("#"))
        self.assertTrue(theme.BORDER_PURPLE.startswith("#"))
        self.assertTrue(theme.SEMANTIC_SUCCESS.startswith("#"))
        self.assertIn("neon-purple-gradient", theme.PRESET_PALETTES)
        self.assertIn("synthwave-purple", theme.PRESET_PALETTES)


class TestUpdateManager(unittest.TestCase):
    def test_parse_version_tuple(self):
        self.assertEqual(UpdateManager.parse_version_tuple("v1.2.3"), (1, 2, 3))
        self.assertEqual(UpdateManager.parse_version_tuple("1.0.0"), (1, 0, 0))
        self.assertEqual(UpdateManager.parse_version_tuple("2.1"), (2, 1, 0))
        self.assertEqual(UpdateManager.parse_version_tuple("v2"), (2, 0, 0))

    def test_is_newer_version(self):
        self.assertTrue(UpdateManager.is_newer_version("1.0.0", "1.0.1"))
        self.assertTrue(UpdateManager.is_newer_version("1.0.0", "1.1.0"))
        self.assertTrue(UpdateManager.is_newer_version("1.0.0", "2.0.0"))
        self.assertTrue(UpdateManager.is_newer_version("1.9.0", "1.10.0"))
        self.assertFalse(UpdateManager.is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(UpdateManager.is_newer_version("1.1.0", "1.0.9"))
        self.assertFalse(UpdateManager.is_newer_version("2.0.0", "1.9.9"))

    def test_render_update_modal(self):
        panel = UpdateManager.render_update_modal("1.1.0", "New feature\nPerformance fix")
        self.assertIsNotNone(panel)

    def test_check_for_update_offline(self):
        # Mock network failure
        with patch("urllib.request.urlopen", side_effect=Exception("Network down")):
            has_up, latest, notes = UpdateManager.check_for_update(timeout=0.1)
            self.assertFalse(has_up)
            self.assertEqual(latest, __version__)


if __name__ == "__main__":
    unittest.main()

