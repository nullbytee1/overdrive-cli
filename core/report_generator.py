"""
OVERDRIVE - Audit & Benchmark Report Exporter Subsystem
Generates professional Markdown and Black & White Monochrome Terminal HTML reports.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional

REPORTS_DIR = os.path.join(os.getcwd(), "reports")

ASCII_BANNER = r"""
 ██████╗ ██╗   ██╗███████╗██████╗ ██████╗ ██████╗ ██╗██╗   ██╗███████╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║██║   ██║██╔════╝
██║   ██║██║   ██║█████╗  ██████╔╝██║  ██║██████╔╝██║██║   ██║█████╗  
██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝  
╚██████╔╝ ╚████╔╝ ███████╗██║  ██║██████╔╝██║  ██║██║ ╚████╔╝ ███████╗
 ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝
"""

class ReportGenerator:
    @staticmethod
    def export_audit_report(
        host: str,
        username: str,
        topo_info: Dict[str, Any],
        audit_results: List[Dict[str, Any]],
        benchmark_results: Optional[List[Dict[str, Any]]] = None,
        vps_bench_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Generates both Markdown and Monochrome Terminal HTML audit documentation in ./reports/"""
        os.makedirs(REPORTS_DIR, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_host = host.replace(":", "_").replace("/", "_")
        
        md_file = os.path.join(REPORTS_DIR, f"overdrive_audit_{clean_host}_{timestamp_str}.md")
        html_file = os.path.join(REPORTS_DIR, f"overdrive_audit_{clean_host}_{timestamp_str}.html")
        
        # 1. Build Markdown Document
        md_lines = []
        md_lines.append(f"# OVERDRIVE System Audit & Optimization Report")
        md_lines.append(f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
        md_lines.append(f"> **Target Node:** `{username}@{host}`  ")
        md_lines.append(f"> **Architecture:** {topo_info.get('arch', 'x86_64')} | **Kernel:** {topo_info.get('kernel', 'Linux')}  ")
        md_lines.append(f"> **Environment:** {topo_info.get('virt', 'Linux Server')}\n")
        md_lines.append("---")
        
        md_lines.append("\n## 🖥️ System Topology & Hardware Discovery\n")
        md_lines.append("| Hardware Dimension | Discovered Specification |")
        md_lines.append("| :--- | :--- |")
        md_lines.append(f"| **Compute Architecture** | {topo_info.get('cpu_cores', 'N/A')} vCPUs ({topo_info.get('arch', 'x86_64')}) |")
        md_lines.append(f"| **Memory Pool** | {topo_info.get('mem_total_mb', 0)} MB ({topo_info.get('mem_total_gb', 0)} GB RAM) |")
        md_lines.append(f"| **Virtualization / Hypervisor** | {topo_info.get('virt', 'KVM')} |")
        md_lines.append(f"| **Primary Network Interface** | `{topo_info.get('primary_iface', 'eth0')}` (MTU: {topo_info.get('current_mtu', 1500)}) |")
        md_lines.append(f"| **Kernel Release** | `{topo_info.get('kernel', 'Linux')}` |")
        stacks = ", ".join(topo_info.get("detected_stacks", [])) if topo_info.get("detected_stacks") else "Standard Linux Server"
        md_lines.append(f"| **Detected Workloads** | {stacks} |")
        
        if vps_bench_data:
            md_lines.append("\n## 🏎️ VPS Hardware & Compute Benchmark\n")
            md_lines.append("| Subsystem Vector | Benchmark Target | Measured Performance |")
            md_lines.append("| :--- | :--- | :---: |")
            md_lines.append(f"| **Compute Engine (CPU)** | SHA-256 Multi-Thread Loop | `{vps_bench_data.get('cpu_score', 'N/A')}` |")
            md_lines.append(f"| **Memory Bandwidth (RAM)** | 2GB Virtual Memory Stream | `{vps_bench_data.get('ram_speed_gb', 'N/A')}` |")
            md_lines.append(f"| **Block Storage (Disk I/O)** | 512MB Direct Sync Writeback | `{vps_bench_data.get('disk_seq_write', 'N/A')}` |")
            md_lines.append(f"| **Network Edge Throughput** | Anycast CDN 50MB Stream | `{vps_bench_data.get('net_speed_mbps', 'N/A')}` |")

        md_lines.append("\n## 📊 Subsystem Verification Matrix\n")
        md_lines.append("| Layer / Subsystem | Kernel Directive / Parameter | Verified Live State | Status |")
        md_lines.append("| :--- | :--- | :--- | :---: |")
        
        for r in audit_results:
            status_pill = "PASS" if r.get("pass", False) else "NOTICE"
            md_lines.append(f"| **{r.get('layer', '')}** | `{r.get('param', '')}` | {r.get('value', '')} | `[{status_pill}]` |")
            
        if benchmark_results:
            md_lines.append("\n## 🌐 Multi-Region Global Transit Latency\n")
            md_lines.append("| Target Region | Probe Gateway | Ping RTT | Jitter Variance | Transit Tier |")
            md_lines.append("| :--- | :--- | :---: | :---: | :---: |")
            for b in benchmark_results:
                md_lines.append(f"| **{b.get('region', '')}** | `{b.get('gateway', '')}` | **{b.get('avg_rtt', 'N/A')} ms** | ±{b.get('jitter', '0.0')} ms | `[{b.get('tier', 'OPTIMAL')}]` |")
                
        md_lines.append("\n---\n*Report generated by OVERDRIVE Enterprise CLI • #OVERDRIVE • MIT License*")
        md_content = "\n".join(md_lines)
        
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        # 2. Build High-End Black & White Monochrome Terminal HTML Document
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        stacks_html = ", ".join(topo_info.get("detected_stacks", [])) if topo_info.get("detected_stacks") else "Standard Linux Server"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OVERDRIVE Audit: {username}@{host}</title>
    <style>
        :root {{
            --bg-page: #000000;
            --bg-term: #0a0a0c;
            --bg-card: #121214;
            --border-color: #27272a;
            --border-bright: #3f3f46;
            --text-main: #ffffff;
            --text-muted: #a1a1aa;
            --text-dim: #71717a;
            --chip-bg: #ffffff;
            --chip-fg: #000000;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-page);
            color: var(--text-main);
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Courier New', monospace;
            padding: 32px 16px;
            display: flex;
            justify-content: center;
        }}
        .terminal-window {{
            width: 100%;
            max-width: 960px;
            background-color: var(--bg-term);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
        }}
        .window-header {{
            background-color: #18181b;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .window-dots {{
            display: flex;
            gap: 6px;
        }}
        .dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #3f3f46;
        }}
        .window-title {{
            font-size: 12px;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }}
        .window-tag {{
            font-size: 11px;
            color: #ffffff;
            background-color: #27272a;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .content {{
            padding: 24px;
        }}
        .ascii-art {{
            color: #ffffff;
            font-size: 10px;
            line-height: 1.15;
            white-space: pre;
            margin-bottom: 24px;
            overflow-x: auto;
        }}
        .hero-bar {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 14px 18px;
            margin-bottom: 24px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            font-size: 13px;
        }}
        .chip {{
            display: inline-block;
            background-color: var(--chip-bg);
            color: var(--chip-fg);
            font-weight: bold;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 3px;
            letter-spacing: 0.5px;
            margin-right: 6px;
        }}
        .chip-outline {{
            display: inline-block;
            border: 1px solid #71717a;
            color: #ffffff;
            font-size: 10px;
            padding: 1px 5px;
            border-radius: 3px;
        }}
        .section-title {{
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #ffffff;
            margin: 28px 0 12px 0;
            padding-bottom: 6px;
            border-bottom: 1px dashed var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 16px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border: 1px solid var(--border-color);
        }}
        th {{
            background-color: #18181b;
            color: #ffffff;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }}
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.02);
        }}
        .bold {{ font-weight: bold; color: #ffffff; }}
        .muted {{ color: var(--text-muted); }}
        .dim {{ color: var(--text-dim); }}
        code {{
            background-color: #18181b;
            border: 1px solid #27272a;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
            color: #ffffff;
        }}
        .footer {{
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: var(--text-dim);
        }}
        .footer a {{
            color: #ffffff;
            text-decoration: none;
        }}
        .hashtag-bar {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
        }}
        .hashtag {{
            color: #a1a1aa;
            font-size: 11px;
            border: 1px solid #27272a;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        @media print {{
            body {{ background: #ffffff; color: #000000; padding: 0; }}
            .terminal-window {{ border: 1px solid #000000; box-shadow: none; }}
            .window-header {{ background: #eeeeee; border-bottom: 1px solid #000000; }}
            .chip {{ background: #000000; color: #ffffff; }}
            table, th, td {{ border-color: #cccccc; }}
            th {{ background: #f4f4f4; color: #000000; }}
            code {{ background: #f0f0f0; border-color: #cccccc; color: #000000; }}
        }}
    </style>
</head>
<body>
    <div class="terminal-window">
        <div class="window-header">
            <div class="window-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
            <div class="window-title">overdrive@system-audit: ~ /telemetry-verification-report</div>
            <div class="window-tag">#OVERDRIVE</div>
        </div>
        
        <div class="content">
            <div class="ascii-art">{ASCII_BANNER}</div>
            
            <div class="hero-bar">
                <div><span class="chip">TARGET NODE</span> <span class="bold">{username}@{host}</span></div>
                <div><span class="chip">STATUS</span> <span class="bold">OPTIMIZED</span></div>
                <div><span class="chip">VIRT</span> <span class="bold">{topo_info.get('virt', 'KVM')}</span></div>
                <div><span class="dim">SYNC:</span> <span class="muted">{gen_time}</span></div>
            </div>

            <div class="hashtag-bar">
                <span class="hashtag">#OVERDRIVE</span>
                <span class="hashtag">#PEAK_OPTIMIZATION</span>
                <span class="hashtag">#ZERO_DROP</span>
                <span class="hashtag">#BBR_ACCELERATED</span>
                <span class="hashtag">#ENTERPRISE_CLI</span>
            </div>

            <div class="section-title">01 // System Topology & Hardware Discovery</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 35%;">Hardware Dimension</th>
                        <th style="width: 65%;">Discovered Specification</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="muted">Compute Architecture</td>
                        <td class="bold">{topo_info.get('cpu_cores', 'N/A')} vCPUs ({topo_info.get('arch', 'x86_64')})</td>
                    </tr>
                    <tr>
                        <td class="muted">Memory Pool</td>
                        <td class="bold">{topo_info.get('mem_total_mb', 0)} MB ({topo_info.get('mem_total_gb', 0)} GB Total RAM)</td>
                    </tr>
                    <tr>
                        <td class="muted">Virtualization / Hypervisor</td>
                        <td class="bold">{topo_info.get('virt', 'KVM (Hardware Virtualization)')}</td>
                    </tr>
                    <tr>
                        <td class="muted">Primary Network Interface</td>
                        <td><code>{topo_info.get('primary_iface', 'eth0')}</code> <span class="dim">(MTU: {topo_info.get('current_mtu', 1500)})</span></td>
                    </tr>
                    <tr>
                        <td class="muted">Kernel Release</td>
                        <td><code>{topo_info.get('kernel', 'Linux')}</code></td>
                    </tr>
                    <tr>
                        <td class="muted">Detected Workload Stacks</td>
                        <td class="bold">{stacks_html}</td>
                    </tr>
                </tbody>
            </table>
"""

        if vps_bench_data:
            html_content += f"""            <div class="section-title">02 // VPS Hardware & Compute Benchmark</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 35%;">Hardware / Subsystem Vector</th>
                        <th style="width: 35%;">Benchmark Target</th>
                        <th style="width: 30%; text-align: center;">Measured Performance</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="bold">Compute Engine (CPU)</td>
                        <td class="muted">SHA-256 Multi-Thread Digest Loop</td>
                        <td style="text-align: center;" class="bold">{vps_bench_data.get('cpu_score', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td class="bold">Memory Subsystem (RAM)</td>
                        <td class="muted">2GB Virtual Memory Stream</td>
                        <td style="text-align: center;" class="bold">{vps_bench_data.get('ram_speed_gb', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td class="bold">Block Storage (Disk I/O)</td>
                        <td class="muted">512MB Direct Sync Writeback</td>
                        <td style="text-align: center;" class="bold">{vps_bench_data.get('disk_seq_write', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td class="bold">Network Edge Throughput</td>
                        <td class="muted">Cloudflare Anycast CDN 50MB Stream</td>
                        <td style="text-align: center;" class="bold">{vps_bench_data.get('net_speed_mbps', 'N/A')}</td>
                    </tr>
                </tbody>
            </table>
"""

        html_content += """            <div class="section-title">03 // Subsystem Verification Matrix</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%;">Layer / Subsystem</th>
                        <th style="width: 30%;">Kernel Parameter / Directive</th>
                        <th style="width: 33%;">Live Verified State</th>
                        <th style="width: 12%; text-align: center;">Status</th>
                    </tr>
                </thead>
                <tbody>
"""
        for r in audit_results:
            is_pass = r.get("pass", False)
            status_chip = '<span class="chip">PASS</span>' if is_pass else '<span class="chip-outline">NOTICE</span>'
            html_content += f"""                    <tr>
                        <td class="bold">{r.get('layer', '')}</td>
                        <td><code>{r.get('param', '')}</code></td>
                        <td class="muted">{r.get('value', '')}</td>
                        <td style="text-align: center;">{status_chip}</td>
                    </tr>\n"""
                    
        html_content += """                </tbody>
            </table>\n"""
            
        if benchmark_results:
            html_content += """            <div class="section-title">04 // Multi-Region Global Transit Latency</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 30%;">Target Region</th>
                        <th style="width: 25%;">Probe Gateway</th>
                        <th style="width: 15%; text-align: center;">Avg Latency</th>
                        <th style="width: 15%; text-align: center;">Jitter</th>
                        <th style="width: 15%; text-align: center;">Tier</th>
                    </tr>
                </thead>
                <tbody>\n"""
            for b in benchmark_results:
                html_content += f"""                    <tr>
                        <td class="bold">{b.get('region', '')}</td>
                        <td><code>{b.get('gateway', '')}</code></td>
                        <td style="text-align: center;" class="bold">{b.get('avg_rtt', 'N/A')} ms</td>
                        <td style="text-align: center;" class="muted">±{b.get('jitter', '0.0')} ms</td>
                        <td style="text-align: center;"><span class="chip-outline">{b.get('tier', 'OPTIMAL')}</span></td>
                    </tr>\n"""
            html_content += """                </tbody>
            </table>\n"""

        html_content += f"""            <div class="footer">
                <div>OVERDRIVE Enterprise Systems Platform • <strong>#OVERDRIVE</strong></div>
                <div>Generated: {gen_time} • MIT License</div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return {
            "md_path": md_file,
            "html_path": html_file
        }
