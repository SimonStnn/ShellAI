"""
System information collector for ShellAI.

This module gathers various system information that can be queried
using natural language through the LLM-powered ask interface.
"""

import subprocess
from pathlib import Path
from typing import Dict, Optional


class SystemInfoCollector:
    """Collects and stores system information for LLM querying."""

    def __init__(self, output_dir: str = "system_info"):
        """Initialize the collector with an output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Define system commands to collect information
        self.commands = {
            "os.txt": "uname -a",
            "disk.txt": "df -h",
            "memory.txt": "free -m",
            "processes.txt": "ps aux --sort=-%cpu | head -20",
            "network.txt": "ip addr show",
            "uptime.txt": "uptime",
            "cpu.txt": "lscpu",
            "mount.txt": "mount",
            "users.txt": "who",
            "environment.txt": "env | sort",
        }

    def run_command(self, command: str) -> Optional[str]:
        """Safely run a system command and return its output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return result.stdout if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"Command failed: {command} - {e}")
            return None

    def collect_all(self) -> Dict[str, bool]:
        """Collect all system information and save to files."""
        results: Dict[str, bool] = {}

        print("🔍 Collecting system information...")

        for filename, cmd in self.commands.items():
            print(f"  📋 Running: {cmd}")
            output = self.run_command(cmd)

            if output:
                file_path = self.output_dir / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"Command: {cmd}\n")
                    f.write("=" * 50 + "\n")
                    f.write(output)
                results[filename] = True
                print(f"  ✅ Saved: {filename}")
            else:
                results[filename] = False
                print(f"  ❌ Failed: {filename}")

        return results

    def collect_custom(self, name: str, command: str) -> bool:
        """Collect custom system information."""
        print(f"🔍 Running custom command: {command}")
        output = self.run_command(command)

        if output:
            file_path = self.output_dir / f"{name}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Custom Command: {command}\n")
                f.write("=" * 50 + "\n")
                f.write(output)
            print(f"✅ Saved custom info: {name}.txt")
            return True
        else:
            print(f"❌ Failed to run: {command}")
            return False


def main():
    """Main function to collect system information."""
    collector = SystemInfoCollector()
    results = collector.collect_all()

    successful = sum(results.values())
    total = len(results)

    print("\n✅ System info collection complete!")
    print(f"📊 Successfully collected {successful}/{total} pieces of information")
    print(f"📁 Files saved to: {collector.output_dir}")


if __name__ == "__main__":
    main()
