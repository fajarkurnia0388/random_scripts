import subprocess
import sys
import threading
import time
from datetime import datetime

class TerminalLogger:
    def __init__(self, output_file="terminal_log.txt"):
        self.output_file = output_file
        self.log_file = None
        
    def write_log(self, message):
        """Menulis pesan ke file log dengan timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        if self.log_file:
            self.log_file.write(log_entry)
            self.log_file.flush()
        
        print(message, end='')
    
    def start_logging(self):
        """Memulai logging ke file"""
        try:
            self.log_file = open(self.output_file, 'w', encoding='utf-8')
            self.write_log("=== Terminal Logging Started ===\n")
            print(f"Logging dimulai. Output akan disimpan ke: {self.output_file}")
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
            self.write_log(f"$ {command}\n")
            
            # Menjalankan command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Membaca output secara real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.write_log(output)
            
            # Membaca error jika ada
            stderr_output = process.stderr.read()
            if stderr_output:
                self.write_log(f"ERROR: {stderr_output}")
            
            return_code = process.poll()
            self.write_log(f"Command finished with return code: {return_code}\n")
            
        except Exception as e:
            self.write_log(f"Error executing command: {e}\n")
    
    def interactive_terminal(self):
        """Terminal interaktif yang mencatat semua aktivitas"""
        print("\n=== Terminal Interaktif (ketik 'exit' untuk keluar) ===")
        print("Semua command dan output akan dicatat ke file log.")
        
        while True:
            try:
                # Input command dari user
                command = input("\n$ ").strip()
                
                if command.lower() in ['exit', 'quit']:
                    self.write_log("User exited terminal\n")
                    break
                elif command == '':
                    continue
                elif command.lower() == 'clear':
                    # Clear screen tapi tetap log
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.write_log("Screen cleared\n")
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
    print("1. Membuat file output untuk logging")
    print("2. Menjalankan terminal interaktif")
    print("3. Mencatat semua aktivitas ke file")
    
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
        print(f"\nLogging selesai. Cek file 'terminal_output.txt' untuk melihat log.")

if __name__ == "__main__":
    main()