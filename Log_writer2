import subprocess
import sys
import threading
import time
import os
import platform
from datetime import datetime
from pathlib import Path


class TerminalLogger:
    def __init__(self, output_file="terminal_log.txt"):
        # Simpan file log di direktori yang sama dengan script
        script_dir = Path(__file__).parent.absolute()
        self.output_file = script_dir / output_file
        self.log_file = None
        self.aliases = {}
        self.shell_config = self.detect_shell_config()
        self.load_aliases()

    def detect_shell_config(self):
        """Mendeteksi file konfigurasi shell yang digunakan"""
        home = Path.home()
        possible_configs = [
            home / ".bashrc",
            home / ".bash_profile",
            home / ".zshrc",
            home / ".profile",
            home / ".bash_aliases",
        ]

        # Untuk Windows, cek PowerShell profile
        if platform.system() == "Windows":
            ps_profile = (
                Path(os.environ.get("USERPROFILE", ""))
                / "Documents"
                / "WindowsPowerShell"
                / "Microsoft.PowerShell_profile.ps1"
            )
            if ps_profile.exists():
                return ps_profile

        # Cari file config yang ada
        for config in possible_configs:
            if config.exists():
                return config

        return None

    def load_aliases(self):
        """Load aliases dari shell configuration files"""
        print("Loading aliases...")

        # Load dari environment variable jika ada
        if platform.system() != "Windows":
            try:
                # Coba ambil aliases dari bash
                result = subprocess.run(
                    'bash -i -c "alias"', shell=True, capture_output=True, text=True
                )

                if result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        if "=" in line:
                            # Parse alias format: alias name='command'
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                name = parts[0].replace("alias ", "").strip()
                                command = parts[1].strip().strip("'\"")
                                self.aliases[name] = command

                print(f"Loaded {len(self.aliases)} aliases")

            except Exception as e:
                print(f"Could not load aliases automatically: {e}")

        # Manual parsing dari config file sebagai backup
        if self.shell_config and self.shell_config.exists():
            try:
                with open(
                    self.shell_config, "r", encoding="utf-8", errors="ignore"
                ) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("alias "):
                            # Parse alias definition
                            alias_def = line[6:].strip()
                            if "=" in alias_def:
                                name, command = alias_def.split("=", 1)
                                name = name.strip()
                                command = command.strip().strip("'\"")
                                self.aliases[name] = command

                if self.aliases:
                    print(f"Loaded aliases from {self.shell_config.name}")

            except Exception as e:
                print(f"Error reading config file: {e}")

    def expand_aliases(self, command):
        """Expand aliases dalam command"""
        # Split command untuk cek apakah command pertama adalah alias
        parts = command.split()
        if not parts:
            return command

        cmd_name = parts[0]

        # Cek apakah command adalah alias
        if cmd_name in self.aliases:
            # Replace alias dengan command sebenarnya
            expanded = self.aliases[cmd_name]
            if len(parts) > 1:
                # Tambahkan arguments jika ada
                expanded += " " + " ".join(parts[1:])

            print(f"Expanding alias: {cmd_name} -> {self.aliases[cmd_name]}")
            return expanded

        return command

    def write_log(self, message):
        """Menulis pesan ke file log dengan timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        if self.log_file:
            self.log_file.write(log_entry)
            self.log_file.flush()

        print(message, end="")

    def start_logging(self):
        """Memulai logging ke file"""
        try:
            self.log_file = open(self.output_file, "w", encoding="utf-8")
            self.write_log("=== Terminal Logging Started ===\n")
            print(f"Logging dimulai. Output akan disimpan ke: {self.output_file}")

            # Log loaded aliases
            if self.aliases:
                self.write_log(f"Loaded {len(self.aliases)} aliases:\n")
                for alias, cmd in self.aliases.items():
                    self.write_log(f"  {alias} = {cmd}\n")
                self.write_log("\n")

            return True
        except Exception as e:
            print(f"Error membuka file log: {e}")
            return False

    def stop_logging(self):
        """Menghentikan logging"""
        if self.log_file:
            self.write_log("=== Terminal Logging Stopped ===\n")
            self.log_file.close()
            self.log_file = None

    def run_command(self, command):
        """Menjalankan command dan mencatat output"""
        try:
            original_command = command
            # Expand aliases
            command = self.expand_aliases(command)

            self.write_log(f"$ {original_command}\n")
            if original_command != command:
                self.write_log(f"  (expanded to: {command})\n")

            # Tentukan shell yang akan digunakan
            if platform.system() == "Windows":
                shell_cmd = command
            else:
                # Untuk Unix/Linux/Mac, gunakan bash dengan mode interaktif
                # untuk memastikan aliases dan functions tersedia
                shell_cmd = f'bash -i -c "{command}"'

            # Menjalankan command
            process = subprocess.Popen(
                shell_cmd,
                shell=True,
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
                # Filter out bash interactive mode warnings
                filtered_errors = []
                for line in stderr_output.split("\n"):
                    if (
                        "bash: cannot set terminal process group" not in line
                        and "bash: no job control in this shell" not in line
                        and line.strip()
                    ):
                        filtered_errors.append(line)

                if filtered_errors:
                    self.write_log(f"ERROR: {chr(10).join(filtered_errors)}\n")

            return_code = process.poll()
            self.write_log(f"Command finished with return code: {return_code}\n")

        except Exception as e:
            self.write_log(f"Error executing command: {e}\n")

    def show_aliases(self):
        """Menampilkan daftar aliases yang tersedia"""
        if not self.aliases:
            self.write_log("No aliases loaded.\n")
        else:
            self.write_log("Available aliases:\n")
            for alias, cmd in sorted(self.aliases.items()):
                self.write_log(f"  {alias:<15} = {cmd}\n")

    def add_alias(self, alias_def):
        """Menambahkan alias baru secara temporary"""
        if "=" not in alias_def:
            self.write_log("Format: alias name=command\n")
            return

        name, command = alias_def.split("=", 1)
        name = name.strip()
        command = command.strip().strip("'\"")

        self.aliases[name] = command
        self.write_log(f"Alias added: {name} = {command}\n")

    def interactive_terminal(self):
        """Terminal interaktif yang mencatat semua aktivitas"""
        print("\n=== Terminal Interaktif (ketik 'exit' untuk keluar) ===")
        print("Semua command dan output akan dicatat ke file log.")
        print("Commands khusus:")
        print("  'show aliases' - Tampilkan daftar aliases")
        print("  'alias name=cmd' - Tambah alias temporary")
        print("  'reload aliases' - Reload aliases dari config")
        print("  'clear' - Bersihkan layar")
        print("  'exit' atau 'quit' - Keluar\n")

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
                    self.load_aliases()
                    self.write_log(
                        f"Aliases reloaded. {len(self.aliases)} aliases available.\n"
                    )
                    continue

                # Jalankan command dan catat hasilnya
                self.run_command(command)

            except KeyboardInterrupt:
                self.write_log("\nKeyboard interrupt received\n")
                break
            except EOFError:
                self.write_log("\nEOF received\n")
                break


def main():
    # Inisialisasi logger
    logger = TerminalLogger("terminal_output.txt")

    print("=== Program Terminal Logger ===")
    print("Program ini akan:")
    print("1. Membuat file output untuk logging di direktori yang sama dengan script")
    print("2. Load aliases dari shell configuration")
    print("3. Menjalankan terminal interaktif")
    print("4. Mencatat semua aktivitas ke file")

    # Mulai logging
    if not logger.start_logging():
        print("Gagal memulai logging. Program dihentikan.")
        return

    try:
        # Jalankan terminal interaktif
        logger.interactive_terminal()

    except Exception as e:
        print(f"Error dalam program: {e}")

    finally:
        # Hentikan logging
        logger.stop_logging()
        print(f"\nLogging selesai. Cek file '{logger.output_file}' untuk melihat log.")


if __name__ == "__main__":
    main()
