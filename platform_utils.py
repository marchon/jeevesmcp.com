#!/usr/bin/env python3
"""
Platform and Shell Detection Utilities for Jeeves

Provides cross-platform detection for:
- Operating System (Windows, macOS, Linux)
- Shell type (Bash, Zsh, Fish, PowerShell, CMD)
- Terminal capabilities
- Platform-specific command adaptations
"""

import os
import platform
import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any


class OperatingSystem(Enum):
    """Supported operating systems"""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class ShellType(Enum):
    """Supported shell types"""
    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"
    POWERSHELL = "powershell"
    CMD = "cmd"
    UNKNOWN = "unknown"


class TerminalType(Enum):
    """Common terminal emulators"""
    TERMINAL_APP = "Terminal.app"  # macOS default
    ITERM2 = "iTerm2"  # macOS popular
    GNOME_TERMINAL = "gnome-terminal"  # Linux GNOME
    KONSOLE = "konsole"  # Linux KDE
    XFCE_TERMINAL = "xfce4-terminal"  # Linux XFCE
    WINDOWS_TERMINAL = "Windows Terminal"  # Windows modern
    CMD_EXE = "cmd.exe"  # Windows legacy
    ALACRITTY = "alacritty"  # Cross-platform
    HYPER = "hyper"  # Cross-platform
    VSCODE = "vscode"  # VS Code integrated
    PYCHARM = "pycharm"  # PyCharm integrated
    UNKNOWN = "unknown"


class PlatformInfo:
    """Comprehensive platform information container"""
    
    def __init__(self):
        self.os = self._detect_os()
        self.shell = self._detect_shell()
        self.terminal = self._detect_terminal()
        self.is_wsl = self._detect_wsl()
        self.home_dir = Path.home()
        self.config_dir = self._get_config_dir()
        self.shell_config_file = self._get_shell_config_file()
        self.supports_ansi_colors = self._detect_ansi_support()
        
    def _detect_os(self) -> OperatingSystem:
        """Detect the operating system"""
        system = platform.system().lower()
        if system == "windows" or system == "win32":
            return OperatingSystem.WINDOWS
        elif system == "darwin":
            return OperatingSystem.MACOS
        elif system == "linux":
            return OperatingSystem.LINUX
        else:
            return OperatingSystem.UNKNOWN
    
    def _detect_wsl(self) -> bool:
        """Detect if running under Windows Subsystem for Linux"""
        if self.os != OperatingSystem.LINUX:
            return False
        try:
            with open("/proc/version", "r") as f:
                version = f.read().lower()
                return "microsoft" in version or "wsl" in version
        except:
            return False
    
    def _detect_shell(self) -> ShellType:
        """Detect the current shell type"""
        # First check SHELL environment variable
        shell_path = os.environ.get("SHELL", "")
        if shell_path:
            shell_name = Path(shell_path).name.lower()
            if "bash" in shell_name:
                return ShellType.BASH
            elif "zsh" in shell_name:
                return ShellType.ZSH
            elif "fish" in shell_name:
                return ShellType.FISH
        
        # Check Windows shells
        if self.os == OperatingSystem.WINDOWS:
            # Check if running in PowerShell
            if os.environ.get("PSModulePath"):
                return ShellType.POWERSHELL
            return ShellType.CMD
        
        # Try to detect from parent process
        try:
            import psutil
            parent = psutil.Process(os.getppid())
            parent_name = parent.name().lower()
            if "bash" in parent_name:
                return ShellType.BASH
            elif "zsh" in parent_name:
                return ShellType.ZSH
            elif "fish" in parent_name:
                return ShellType.FISH
        except ImportError:
            pass
        
        return ShellType.UNKNOWN
    
    def _detect_terminal(self) -> TerminalType:
        """Detect the terminal emulator"""
        env_vars = os.environ
        
        # Check for specific terminal environment variables
        term_program = env_vars.get("TERM_PROGRAM", "").lower()
        term = env_vars.get("TERM", "").lower()
        terminal = env_vars.get("TERMINAL", "").lower()
        
        # macOS terminals
        if term_program == "apple_terminal":
            return TerminalType.TERMINAL_APP
        elif term_program == "iterm.app":
            return TerminalType.ITERM2
        
        # VS Code detection
        if env_vars.get("TERM_PROGRAM") == "vscode" or env_vars.get("VSCODE_CWD"):
            return TerminalType.VSCODE
        
        # PyCharm detection
        if "jetbrains" in term or "pycharm" in env_vars.get("TERMINAL_EMULATOR", "").lower():
            return TerminalType.PYCHARM
        
        # Windows Terminal
        if env_vars.get("WT_SESSION") or env_vars.get("WT_PROFILE_ID"):
            return TerminalType.WINDOWS_TERMINAL
        
        # Linux terminals (check process name)
        try:
            import psutil
            # Get all parent processes
            proc = psutil.Process()
            while proc.pid > 1:
                proc_name = proc.name().lower()
                if "gnome-terminal" in proc_name:
                    return TerminalType.GNOME_TERMINAL
                elif "konsole" in proc_name:
                    return TerminalType.KONSOLE
                elif "xfce4-terminal" in proc_name or "xfce-terminal" in proc_name:
                    return TerminalType.XFCE_TERMINAL
                elif "alacritty" in proc_name:
                    return TerminalType.ALACRITTY
                elif "hyper" in proc_name:
                    return TerminalType.HYPER
                try:
                    proc = proc.parent()
                    if proc is None:
                        break
                except:
                    break
        except ImportError:
            pass
        
        # Check TERM variable for hints
        if "alacritty" in term:
            return TerminalType.ALACRITTY
        
        return TerminalType.UNKNOWN
    
    def _get_config_dir(self) -> Path:
        """Get the platform-appropriate config directory"""
        if self.os == OperatingSystem.WINDOWS:
            return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "jeeves"
        elif self.os == OperatingSystem.MACOS:
            return Path.home() / "Library/Application Support/jeeves"
        else:  # Linux and others
            return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "jeeves"
    
    def _get_shell_config_file(self) -> Optional[Path]:
        """Get the shell configuration file path"""
        if self.shell == ShellType.BASH:
            return Path.home() / ".bashrc"
        elif self.shell == ShellType.ZSH:
            # Check for .zshrc first, then .zprofile
            zshrc = Path.home() / ".zshrc"
            if zshrc.exists():
                return zshrc
            return Path.home() / ".zprofile"
        elif self.shell == ShellType.FISH:
            return Path.home() / ".config/fish/config.fish"
        elif self.shell == ShellType.POWERSHELL:
            # PowerShell profile
            if self.os == OperatingSystem.WINDOWS:
                docs = Path.home() / "Documents"
            else:
                docs = Path.home() / "Documents"
            return docs / "PowerShell/Microsoft.PowerShell_profile.ps1"
        return None
    
    def _detect_ansi_support(self) -> bool:
        """Detect if terminal supports ANSI color codes"""
        # Windows Terminal, modern terminals all support ANSI
        if self.os == OperatingSystem.WINDOWS:
            # Windows 10 version 1511+ supports ANSI
            return (self.terminal in [
                TerminalType.WINDOWS_TERMINAL, 
                TerminalType.VSCODE,
                TerminalType.PYCHARM
            ] or os.environ.get("ANSICON") is not None)
        
        # Unix-like systems generally support ANSI
        if self.os in [OperatingSystem.LINUX, OperatingSystem.MACOS]:
            return os.environ.get("TERM") != "dumb"
        
        return False
    
    def get_shell_launch_command(self, command: str, title: Optional[str] = None) -> List[str]:
        """
        Get the platform-specific command to launch a shell command in a new terminal.
        
        Args:
            command: The command to execute
            title: Optional window title
            
        Returns:
            List of command arguments
        """
        if self.os == OperatingSystem.WINDOWS:
            if self.terminal == TerminalType.WINDOWS_TERMINAL:
                wt_cmd = ["wt", "new-tab"]
                if title:
                    wt_cmd.extend(["--title", title])
                wt_cmd.extend(["--", "powershell", "-Command", command])
                return wt_cmd
            elif self.shell == ShellType.POWERSHELL:
                ps_cmd = ["powershell", "-Command", f"Start-Process powershell -ArgumentList '-NoExit','-Command','{command}'"]
                return ps_cmd
            else:
                # CMD
                return ["cmd", "/k", command]
                
        elif self.os == OperatingSystem.MACOS:
            script = command.replace('"', '\\"')
            if self.terminal == TerminalType.ITERM2:
                # iTerm2 AppleScript
                apple_script = f'''
                tell application "iTerm2"
                    tell current window
                        create tab with default profile
                        tell current session
n                            write text "{script}"
                        end tell
                    end tell
                end tell
                '''
                return ["osascript", "-e", apple_script]
            else:
                # Terminal.app AppleScript
                apple_script = f'''
                tell application "Terminal"
                    do script "{script}"
                    activate
                end tell
                '''
                return ["osascript", "-e", apple_script]
        
        else:  # Linux
            # Try to detect available terminal emulator
            terminals = [
                (TerminalType.GNOME_TERMINAL, ["gnome-terminal", "--"]),
                (TerminalType.KONSOLE, ["konsole", "-e"]),
                (TerminalType.XFCE_TERMINAL, ["xfce4-terminal", "-e"]),
                (TerminalType.ALACRITTY, ["alacritty", "-e"]),
                (TerminalType.HYPER, ["hyper", "-e"]),
            ]
            
            # Check which terminal is available
            for term_type, term_cmd in terminals:
                try:
                    subprocess.run(
                        ["which", term_cmd[0]], 
                        check=True, 
                        capture_output=True
                    )
                    return term_cmd + [self.shell.value, "-c", command]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            # Fallback: try xterm
            try:
                subprocess.run(["which", "xterm"], check=True, capture_output=True)
                return ["xterm", "-e", self.shell.value, "-c", command]
            except:
                pass
        
        # Ultimate fallback: just run in current shell
        return [self.shell.value, "-c", command]
    
    def get_path_separator(self) -> str:
        """Get the platform path separator"""
        return os.sep
    
    def get_path_env_separator(self) -> str:
        """Get the PATH environment variable separator"""
        return ";" if self.os == OperatingSystem.WINDOWS else ":"
    
    def get_install_dir(self) -> Path:
        """Get the platform-appropriate installation directory"""
        if self.os == OperatingSystem.WINDOWS:
            local_app_data = os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")
            return Path(local_app_data) / "jeeves"
        else:
            return Path.home() / ".local/share/jeeves"
    
    def get_bin_dir(self) -> Path:
        """Get the platform-appropriate binary directory"""
        if self.os == OperatingSystem.WINDOWS:
            return self.get_install_dir() / "bin"
        else:
            return Path.home() / ".local/bin"
    
    def format_command_for_shell(self, command: str) -> str:
        """Format a command appropriately for the detected shell"""
        if self.shell == ShellType.POWERSHELL:
            # PowerShell uses different escaping
            return command.replace("'", "''")
        elif self.shell == ShellType.CMD:
            # CMD has specific escaping rules
            return command.replace("^", "^^").replace("&", "^&").replace("|", "^|")
        else:
            # POSIX shells
            return command.replace("'", "'\"'\"'")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert platform info to dictionary"""
        return {
            "os": self.os.value,
            "os_name": self.get_os_display_name(),
            "shell": self.shell.value,
            "terminal": self.terminal.value,
            "is_wsl": self.is_wsl,
            "home_dir": str(self.home_dir),
            "config_dir": str(self.config_dir),
            "shell_config_file": str(self.shell_config_file) if self.shell_config_file else None,
            "supports_ansi_colors": self.supports_ansi_colors,
            "path_separator": self.get_path_separator(),
            "install_dir": str(self.get_install_dir()),
            "bin_dir": str(self.get_bin_dir()),
        }
    
    def get_os_display_name(self) -> str:
        """Get human-readable OS name"""
        if self.is_wsl:
            return "Windows (WSL)"
        return {
            OperatingSystem.WINDOWS: "Windows",
            OperatingSystem.MACOS: "macOS",
            OperatingSystem.LINUX: "Linux",
            OperatingSystem.UNKNOWN: "Unknown",
        }.get(self.os, "Unknown")
    
    def __str__(self) -> str:
        """String representation"""
        return (
            f"Platform: {self.get_os_display_name()}\n"
            f"Shell: {self.shell.value}\n"
            f"Terminal: {self.terminal.value}\n"
            f"Config Dir: {self.config_dir}\n"
            f"Shell Config: {self.shell_config_file}"
        )


def get_platform_info() -> PlatformInfo:
    """Get platform information singleton"""
    return PlatformInfo()


# Convenience functions for common checks
def is_windows() -> bool:
    """Check if running on Windows"""
    return PlatformInfo().os == OperatingSystem.WINDOWS


def is_macos() -> bool:
    """Check if running on macOS"""
    return PlatformInfo().os == OperatingSystem.MACOS


def is_linux() -> bool:
    """Check if running on Linux"""
    return PlatformInfo().os == OperatingSystem.LINUX


def is_wsl() -> bool:
    """Check if running under WSL"""
    return PlatformInfo().is_wsl


def get_shell_type() -> ShellType:
    """Get the detected shell type"""
    return PlatformInfo().shell


def open_in_terminal(command: str, title: Optional[str] = None) -> subprocess.Popen:
    """
    Open a command in a new terminal window.
    
    Args:
        command: The command to execute
        title: Optional window title
        
    Returns:
        subprocess.Popen object
    """
    platform_info = PlatformInfo()
    launch_cmd = platform_info.get_shell_launch_command(command, title)
    return subprocess.Popen(launch_cmd)


if __name__ == "__main__":
    # Test platform detection
    info = get_platform_info()
    print(info)
    print("\n--- JSON Output ---")
    import json
    print(json.dumps(info.to_dict(), indent=2))
