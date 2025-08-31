import subprocess
import sys
import threading
import time
import os
import platform
import json
import re
from datetime import datetime
from pathlib import Path


class TerminalLogger:
    def __init__(self, output_file="terminal_log.txt"):
        """Inisialisasi TerminalLogger dengan file output untuk logging"""
        # Simpan file log di direktori yang sama dengan script
        script_dir = Path(__file__).parent.absolute()
        self.output_file = script_dir / output_file
        self.log_file = None
        self.aliases = {}
        self.functions = {}
        self.is_windows = platform.system() == "Windows"
        self.shell_config = self.detect_shell_config()
        self.load_aliases()

    def detect_shell_config(self):
        """Mendeteksi file konfigurasi shell yang digunakan"""
        configs_found = []

        if self.is_windows:
            # Cek PowerShell profiles
            possible_ps_profiles = [
                Path(os.environ.get("USERPROFILE", ""))
                / "Documents"
                / "WindowsPowerShell"
                / "Microsoft.PowerShell_profile.ps1",
                Path(os.environ.get("USERPROFILE", ""))
                / "Documents"
                / "PowerShell"
                / "Microsoft.PowerShell_profile.ps1",
            ]

            for profile in possible_ps_profiles:
                if profile.exists():
                    configs_found.append(profile)
                    print(f"Found PowerShell profile: {profile}")

            # Cek juga Git Bash jika ada
            git_bash_rc = Path.home() / ".bashrc"
            if git_bash_rc.exists():
                configs_found.append(git_bash_rc)
                print(f"Found Git Bash config: {git_bash_rc}")

        else:
            # Unix/Linux/Mac
            home = Path.home()
            possible_configs = [
                home / ".bashrc",
                home / ".bash_profile",
                home / ".zshrc",
                home / ".profile",
                home / ".bash_aliases",
            ]

            for config in possible_configs:
                if config.exists():
                    configs_found.append(config)
                    print(f"Found shell config: {config}")

        return configs_found if configs_found else []

    def load_powershell_aliases(self):
        """Load aliases dan functions dari PowerShell"""
        try:
            # Get aliases dari PowerShell
            ps_command = """
            $aliases = @{}
            Get-Alias | ForEach-Object {
                $aliases[$_.Name] = $_.Definition
            }
            
            # Get custom functions
            $functions = @{}
            Get-Command -CommandType Function | Where-Object {
                $_.Source -eq "" -and $_.Name -notlike "*:*"
            } | ForEach-Object {
                $functions[$_.Name] = $_.Definition
            }
            
            @{
                Aliases = $aliases
                Functions = $functions
            } | ConvertTo-Json -Depth 3
            """

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_command],
                capture_output=True,
                text=True,
                shell=False,
                timeout=10,  # Tambahkan timeout untuk menghindari hang
            )

            if result.stdout:
                try:
                    data = json.loads(result.stdout)

                    # Load aliases
                    if "Aliases" in data and data["Aliases"]:
                        for name, definition in data["Aliases"].items():
                            self.aliases[name] = definition
                        print(f"Loaded {len(data['Aliases'])} PowerShell aliases")

                    # Load functions (yang bisa berfungsi seperti aliases)
                    if "Functions" in data and data["Functions"]:
                        for name, definition in data["Functions"].items():
                            # Skip built-in functions yang terlalu complex
                            if len(str(definition)) < 500:  # Simple functions only
                                self.functions[name] = definition
                        print(f"Loaded {len(self.functions)} PowerShell functions")
                except json.JSONDecodeError as e:
                    print(f"Error parsing PowerShell output: {e}")

        except subprocess.TimeoutExpired:
            print("PowerShell command timed out")
        except Exception as e:
            print(f"Could not load PowerShell aliases: {e}")

    def parse_powershell_profile(self, profile_path):
        """Parse PowerShell profile untuk mencari alias dan function definitions"""
        try:
            with open(profile_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

                # Pattern untuk Set-Alias
                alias_pattern = (
                    r"Set-Alias\s+(?:-Name\s+)?([^\s]+)\s+(?:-Value\s+)?([^\s\n]+)"
                )
                for match in re.finditer(alias_pattern, content, re.IGNORECASE):
                    name = match.group(1).strip("\"'")
                    value = match.group(2).strip("\"'")
                    self.aliases[name] = value

                # Pattern untuk New-Alias
                new_alias_pattern = (
                    r"New-Alias\s+(?:-Name\s+)?([^\s]+)\s+(?:-Value\s+)?([^\s\n]+)"
                )
                for match in re.finditer(new_alias_pattern, content, re.IGNORECASE):
                    name = match.group(1).strip("\"'")
                    value = match.group(2).strip("\"'")
                    self.aliases[name] = value

                # Pattern untuk function definitions yang simple
                func_pattern = r"function\s+([^\s\{]+)\s*\{([^\}]+)\}"
                for match in re.finditer(func_pattern, content):
                    name = match.group(1).strip()
                    body = match.group(2).strip()
                    # Hanya ambil function yang simple (one-liner)
                    if "\n" not in body and len(body) < 200:
                        self.functions[name] = body

                print(
                    f"Parsed {len(self.aliases)} aliases and {len(self.functions)} functions from {profile_path.name}"
                )

        except Exception as e:
            print(f"Error parsing PowerShell profile {profile_path}: {e}")

    def load_aliases(self):
        """Load aliases dari shell configuration files"""
        print("\nLoading aliases and functions...")

        if self.is_windows:
            # Load dari PowerShell
            self.load_powershell_aliases()

            # Parse profile files jika ada
            if self.shell_config:
                for config in self.shell_config:
                    if config.suffix == ".ps1":
                        self.parse_powershell_profile(config)
                    elif config.name in [".bashrc", ".bash_profile"]:
                        self.parse_bash_config(config)
        else:
            # Unix/Linux/Mac
            self.load_bash_aliases()

            if self.shell_config:
                for config in self.shell_config:
                    self.parse_bash_config(config)

        print(
            f"Total loaded: {len(self.aliases)} aliases, {len(self.functions)} functions\n"
        )

    def load_bash_aliases(self):
        """Load aliases dari bash"""
        try:
            result = subprocess.run(
                'bash -i -c "alias"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if "=" in line:
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            name = parts[0].replace("alias ", "").strip()
                            command = parts[1].strip().strip("'\"")
                            self.aliases[name] = command

                print(f"Loaded {len(self.aliases)} bash aliases")

        except subprocess.TimeoutExpired:
            print("Bash command timed out")
        except Exception as e:
            print(f"Could not load bash aliases: {e}")

    def parse_bash_config(self, config_path):
        """Parse bash configuration file"""
        try:
            with open(config_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("alias "):
                        alias_def = line[6:].strip()
                        if "=" in alias_def:
                            name, command = alias_def.split("=", 1)
                            name = name.strip()
                            command = command.strip().strip("'\"")
                            self.aliases[name] = command

            print(f"Parsed aliases from {config_path.name}")

        except Exception as e:
            print(f"Error reading {config_path}: {e}")

    def expand_aliases(self, command):
        """Expand aliases dalam command"""
        if not command:
            return command

        parts = command.split()
        if not parts:
            return command

        cmd_name = parts[0]

        # Cek apakah command adalah alias
        if cmd_name in self.aliases:
            expanded = self.aliases[cmd_name]
            if len(parts) > 1:
                expanded += " " + " ".join(parts[1:])

            print(f"Expanding alias: {cmd_name} -> {self.aliases[cmd_name]}")
            return expanded

        # Cek apakah command adalah function
        if cmd_name in self.functions:
            print(f"Found function: {cmd_name}")
            # Untuk function, kita perlu menjalankannya berbeda
            return command  # Return as-is, akan dihandle di run_command

        return command

    def write_log(self, message):
        """Menulis pesan ke file log dengan timestamp"""
        if not message:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        if self.log_file:
            try:
                self.log_file.write(log_entry)
                self.log_file.flush()
            except Exception as e:
                print(f"Error writing to log: {e}")

        print(message, end="")

    def start_logging(self):
        """Memulai logging ke file"""
        try:
            self.log_file = open(self.output_file, "w", encoding="utf-8")
            self.write_log("=== Terminal Logging Started ===\n")
            self.write_log(f"Platform: {platform.system()} {platform.release()}\n")
            print(f"Logging dimulai. Output akan disimpan ke: {self.output_file}")

            # Log configuration files found
            if self.shell_config:
                self.write_log("Configuration files found:\n")
                for config in self.shell_config:
                    self.write_log(f"  - {config}\n")

            # Log loaded aliases
            if self.aliases:
                self.write_log(f"\nLoaded {len(self.aliases)} aliases:\n")
                for alias, cmd in sorted(self.aliases.items())[:10]:  # Show first 10
                    self.write_log(f"  {alias} = {cmd}\n")
                if len(self.aliases) > 10:
                    self.write_log(f"  ... and {len(self.aliases) - 10} more\n")

            # Log loaded functions
            if self.functions:
                self.write_log(f"\nLoaded {len(self.functions)} functions:\n")
                for func in sorted(self.functions.keys())[:10]:  # Show first 10
                    self.write_log(f"  {func}\n")
                if len(self.functions) > 10:
                    self.write_log(f"  ... and {len(self.functions) - 10} more\n")

            self.write_log("\n")
            return True

        except Exception as e:
            print(f"Error membuka file log: {e}")
            return False

    def stop_logging(self):
        """Menghentikan logging"""
        if self.log_file:
            try:
                self.write_log("=== Terminal Logging Stopped ===\n")
                self.log_file.close()
            except Exception as e:
                print(f"Error closing log file: {e}")
            finally:
                self.log_file = None

    def run_command(self, command):
        """Menjalankan command dan mencatat output"""
        if not command:
            return

        try:
            original_command = command
            expanded_command = self.expand_aliases(command)

            self.write_log(f"$ {original_command}\n")
            if original_command != expanded_command:
                self.write_log(f"  (expanded to: {expanded_command})\n")

            # Tentukan cara menjalankan command
            if self.is_windows:
                # Cek apakah ini function PowerShell
                cmd_name = command.split()[0] if command.split() else ""
                if cmd_name in self.functions:
                    # Jalankan sebagai PowerShell command
                    shell_cmd = ["powershell", "-Command", command]
                    use_shell = False
                else:
                    # Coba dulu dengan PowerShell untuk support aliases
                    shell_cmd = ["powershell", "-Command", expanded_command]
                    use_shell = False
            else:
                # Unix/Linux/Mac
                shell_cmd = f'bash -i -c "{expanded_command}"'
                use_shell = True

            # Menjalankan command dengan timeout
            process = subprocess.Popen(
                shell_cmd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=os.environ.copy(),
            )

            # Membaca output secara real-time
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    self.write_log(output)

            # Membaca error jika ada
            stderr_output = process.stderr.read()
            if stderr_output:
                # Filter out common warnings
                filtered_errors = []
                for line in stderr_output.split("\n"):
                    if (
                        not any(
                            skip in line
                            for skip in [
                                "bash: cannot set terminal process group",
                                "bash: no job control in this shell",
                                "Unable to find type",
                                "ObjectNotFound",
                            ]
                        )
                        and line.strip()
                    ):
                        filtered_errors.append(line)

                if filtered_errors:
                    self.write_log(f"ERROR: {chr(10).join(filtered_errors)}\n")

            return_code = process.poll()
            if return_code != 0 and return_code is not None:
                self.write_log(f"Command finished with return code: {return_code}\n")

        except Exception as e:
            self.write_log(f"Error executing command: {e}\n")

    def show_aliases(self):
        """Menampilkan daftar aliases yang tersedia"""
        if not self.aliases and not self.functions:
            self.write_log("No aliases or functions loaded.\n")
        else:
            if self.aliases:
                self.write_log(f"Available aliases ({len(self.aliases)}):\n")
                for alias, cmd in sorted(self.aliases.items()):
                    self.write_log(
                        f"  {alias:<20} = {cmd[:60]}{'...' if len(cmd) > 60 else ''}\n"
                    )

            if self.functions:
                self.write_log(f"\nAvailable functions ({len(self.functions)}):\n")
                for func in sorted(self.functions.keys()):
                    self.write_log(f"  {func}\n")

    def add_alias(self, alias_def):
        """Menambahkan alias baru secara temporary"""
        if not alias_def or "=" not in alias_def:
            self.write_log("Format: alias name=command\n")
            return

        name, command = alias_def.split("=", 1)
        name = name.strip()
        command = command.strip().strip("'\"")

        if not name:
            self.write_log("Error: Alias name cannot be empty\n")
            return

        self.aliases[name] = command
        self.write_log(f"Alias added: {name} = {command}\n")

    def interactive_terminal(self):
        """Terminal interaktif yang mencatat semua aktivitas"""
        print("\n=== Terminal Interaktif (ketik 'exit' untuk keluar) ===")
        print("Semua command dan output akan dicatat ke file log.")
        print("\nCommands khusus:")
        print("  'show aliases' - Tampilkan daftar aliases dan functions")
        print("  'alias name=cmd' - Tambah alias temporary")
        print("  'reload aliases' - Reload aliases dari config")
        print("  'clear' - Bersihkan layar")
        print("  'exit' atau 'quit' - Keluar")

        if self.is_windows:
            print("\nNote: Menggunakan PowerShell untuk eksekusi commands")
            print("PowerShell aliases dan functions sudah di-load")

        print("-" * 50)

        while True:
            try:
                # Input command dari user
                command = input("\n$ ").strip()

                if command.lower() in ["exit", "quit"]:
                    self.write_log("User exited terminal\n")
                    break
                elif command == "":
                    continue
                elif command.lower() == "clear":
                    # Clear screen tapi tetap log
                    os.system("cls" if os.name == "nt" else "clear")
                    self.write_log("Screen cleared\n")
                    continue
                elif command.lower() == "show aliases":
                    self.show_aliases()
                    continue
                elif command.lower().startswith("alias "):
                    self.add_alias(command[6:])
                    continue
                elif command.lower() == "reload aliases":
                    self.aliases.clear()
                    self.functions.clear()
                    self.load_aliases()
                    self.write_log(
                        f"Aliases reloaded. {len(self.aliases)} aliases, {len(self.functions)} functions available.\n"
                    )
                    continue

                # Jalankan command dan catat hasilnya
                self.run_command(command)

            except KeyboardInterrupt:
                self.write_log("\nKeyboard interrupt received\n")
                print("\nUse 'exit' to quit properly")
                continue
            except EOFError:
                self.write_log("\nEOF received\n")
                break
            except Exception as e:
                self.write_log(f"Error in interactive terminal: {e}\n")
                print(f"Error: {e}")


def test_powershell_profile():
    """Test function untuk cek PowerShell profile"""
    print("=== Checking PowerShell Profile ===")

    # Cek berbagai lokasi PowerShell profile
    possible_profiles = [
        Path(os.environ.get("USERPROFILE", ""))
        / "Documents"
        / "WindowsPowerShell"
        / "Microsoft.PowerShell_profile.ps1",
        Path(os.environ.get("USERPROFILE", ""))
        / "Documents"
        / "PowerShell"
        / "Microsoft.PowerShell_profile.ps1",
        Path(os.environ.get("USERPROFILE", ""))
        / "Documents"
        / "WindowsPowerShell"
        / "profile.ps1",
        Path(os.environ.get("USERPROFILE", ""))
        / "Documents"
        / "PowerShell"
        / "profile.ps1",
    ]

    print("\nChecking profile locations:")
    for profile in possible_profiles:
        exists = "✓ EXISTS" if profile.exists() else "✗ NOT FOUND"
        print(f"  {exists}: {profile}")

        if profile.exists():
            try:
                size = profile.stat().st_size
                print(f"         Size: {size} bytes")

                # Baca beberapa baris pertama
                with open(profile, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[:5]
                    if lines:
                        print(f"         First lines:")
                        for line in lines:
                            print(f"           {line.rstrip()[:60]}")
            except Exception as e:
                print(f"         Error reading: {e}")

    # Cek PowerShell $PROFILE variable
    print("\nChecking PowerShell $PROFILE variable:")
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "$PROFILE"],
            capture_output=True,
            text=True,
            shell=False,
            timeout=5,
        )
        if result.stdout:
            profile_path = result.stdout.strip()
            print(f"  $PROFILE points to: {profile_path}")
            if Path(profile_path).exists():
                print(f"  ✓ Profile exists at this location")
            else:
                print(f"  ✗ Profile does not exist at this location")
    except subprocess.TimeoutExpired:
        print(f"  PowerShell command timed out")
    except Exception as e:
        print(f"  Error checking $PROFILE: {e}")

    print("\n" + "=" * 50 + "\n")


def main():
    """Main function untuk menjalankan Terminal Logger"""
    try:
        # Jika di Windows, jalankan test profile dulu
        if platform.system() == "Windows":
            test_powershell_profile()

        # Inisialisasi logger
        logger = TerminalLogger("terminal_output.txt")

        print("=== Program Terminal Logger ===")
        print("Program ini akan:")
        print(
            "1. Membuat file output untuk logging di direktori yang sama dengan script"
        )
        print("2. Load aliases dan functions dari shell configuration")
        print("3. Menjalankan terminal interaktif")
        print("4. Mencatat semua aktivitas ke file")

        # Mulai logging
        if not logger.start_logging():
            print("Gagal memulai logging. Program dihentikan.")
            return 1

        try:
            # Jalankan terminal interaktif
            logger.interactive_terminal()

        except Exception as e:
            print(f"Error dalam program: {e}")
            return 1

        finally:
            # Hentikan logging
            logger.stop_logging()
            print(
                f"\nLogging selesai. Cek file '{logger.output_file}' untuk melihat log."
            )

            # Tampilkan summary
            if logger.aliases or logger.functions:
                print(f"\nSummary:")
                print(f"  Total aliases loaded: {len(logger.aliases)}")
                print(f"  Total functions loaded: {len(logger.functions)}")

                # Tampilkan beberapa contoh aliases
                if logger.aliases:
                    print(f"\n  Sample aliases:")
                    for alias, cmd in list(logger.aliases.items())[:5]:
                        print(
                            f"    {alias} = {cmd[:50]}{'...' if len(cmd) > 50 else ''}"
                        )

        return 0

    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
