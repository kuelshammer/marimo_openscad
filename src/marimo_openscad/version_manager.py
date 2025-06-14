"""
OpenSCAD Version Management System

Detects, manages, and validates OpenSCAD versions across local installations,
WASM modules, and provides compatibility checking for cross-version support.
"""

import re
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Optional, List, Dict, NamedTuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VersionInfo(NamedTuple):
    """Structured version information."""
    major: int
    minor: int
    patch: int
    build: Optional[str] = None
    
    def __str__(self) -> str:
        base = f"{self.major}.{self.minor:02d}.{self.patch:02d}"
        return f"{base}.{self.build}" if self.build else base
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, VersionInfo):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __gt__(self, other) -> bool:
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)


class OpenSCADVersionType(Enum):
    """Types of OpenSCAD installations."""
    LOCAL = "local"          # Local OpenSCAD executable
    WASM_BUNDLED = "wasm_bundled"  # Bundled WASM module
    WASM_DOWNLOADED = "wasm_downloaded"  # Downloaded WASM module
    UNKNOWN = "unknown"


@dataclass
class OpenSCADInstallation:
    """Information about an OpenSCAD installation."""
    version_info: VersionInfo
    installation_type: OpenSCADVersionType
    executable_path: Optional[Path] = None
    wasm_path: Optional[Path] = None
    is_available: bool = True
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class LocalOpenSCADDetector:
    """Detects local OpenSCAD installations across platforms."""
    
    # Common OpenSCAD executable names
    OPENSCAD_EXECUTABLES = [
        "openscad",
        "openscad.exe", 
        "OpenSCAD",
        "OpenSCAD.exe"
    ]
    
    # Platform-specific search paths
    SEARCH_PATHS = {
        "Windows": [
            Path("C:/Program Files/OpenSCAD"),
            Path("C:/Program Files (x86)/OpenSCAD"),
            Path.home() / "AppData/Local/OpenSCAD",
        ],
        "Darwin": [  # macOS
            Path("/Applications/OpenSCAD.app/Contents/MacOS"),
            Path("/usr/local/bin"),
            Path("/opt/homebrew/bin"),
            Path.home() / "Applications/OpenSCAD.app/Contents/MacOS"
        ],
        "Linux": [
            Path("/usr/bin"),
            Path("/usr/local/bin"), 
            Path("/opt/openscad/bin"),
            Path.home() / ".local/bin",
            Path("/snap/openscad/current/bin")
        ]
    }
    
    def find_openscad_executable(self) -> Optional[Path]:
        """
        Find OpenSCAD executable on the system.
        
        Returns:
            Path to OpenSCAD executable if found, None otherwise
        """
        # First try PATH
        for executable in self.OPENSCAD_EXECUTABLES:
            path = shutil.which(executable)
            if path:
                return Path(path)
        
        # Then try platform-specific paths
        system = platform.system()
        search_paths = self.SEARCH_PATHS.get(system, [])
        
        for search_dir in search_paths:
            if not search_dir.exists():
                continue
                
            for executable in self.OPENSCAD_EXECUTABLES:
                full_path = search_dir / executable
                if full_path.exists() and full_path.is_file():
                    # Verify it's executable
                    if self._is_executable(full_path):
                        return full_path
        
        return None
    
    def _is_executable(self, path: Path) -> bool:
        """Check if path is executable."""
        try:
            # Try to get version to verify it's a valid OpenSCAD executable
            result = subprocess.run(
                [str(path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and "OpenSCAD" in result.stdout
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_version_string(self, executable: Path) -> Optional[str]:
        """
        Get version string from OpenSCAD executable.
        
        Args:
            executable: Path to OpenSCAD executable
            
        Returns:
            Version string if successful, None otherwise
        """
        try:
            result = subprocess.run(
                [str(executable), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(f"OpenSCAD version check failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting version from {executable}")
            return None
        except Exception as e:
            logger.error(f"Error getting version from {executable}: {e}")
            return None
    
    def parse_version_info(self, version_string: str) -> Optional[VersionInfo]:
        """
        Parse OpenSCAD version string into structured format.
        
        Args:
            version_string: Raw version output from OpenSCAD
            
        Returns:
            Parsed version information
            
        Examples:
            "OpenSCAD version 2021.01" -> VersionInfo(2021, 1, 0)
            "OpenSCAD version 2023.06.23 (git a1b2c3d)" -> VersionInfo(2023, 6, 23, "a1b2c3d")
        """
        # Common version patterns in OpenSCAD output
        patterns = [
            # Standard release: "OpenSCAD version 2021.01"
            r"OpenSCAD version (\d{4})\.(\d{2})(?:\.(\d{2}))?",
            # Development build: "OpenSCAD version 2023.06.23 (git a1b2c3d)"
            r"OpenSCAD version (\d{4})\.(\d{2})\.(\d{2})\s*\(git\s+([a-f0-9]+)\)",
            # Alternative format: "OpenSCAD 2021.01.03"
            r"OpenSCAD (\d{4})\.(\d{2})\.(\d{2})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_string)
            if match:
                groups = match.groups()
                
                major = int(groups[0])
                minor = int(groups[1])
                patch = int(groups[2]) if groups[2] else 0
                build = groups[3] if len(groups) > 3 and groups[3] else None
                
                return VersionInfo(major, minor, patch, build)
        
        logger.warning(f"Could not parse version string: {version_string}")
        return None


class WASMVersionDetector:
    """Detects and manages WASM OpenSCAD modules."""
    
    def __init__(self, package_root: Optional[Path] = None):
        """
        Initialize WASM detector.
        
        Args:
            package_root: Root path of marimo_openscad package
        """
        if package_root is None:
            # Auto-detect package root
            package_root = Path(__file__).parent
        
        self.package_root = package_root
        self.wasm_dirs = [
            self.package_root / "wasm",
            self.package_root / "static" / "wasm"
        ]
    
    def find_bundled_wasm_files(self) -> List[Path]:
        """Find all bundled WASM files."""
        wasm_files = []
        
        for wasm_dir in self.wasm_dirs:
            if wasm_dir.exists():
                # Look for .wasm files
                wasm_files.extend(wasm_dir.glob("*.wasm"))
        
        return wasm_files
    
    def detect_bundled_wasm_version(self) -> Optional[str]:
        """
        Detect version of bundled WASM module.
        
        This is challenging because WASM modules don't typically embed 
        version information. We use heuristics and metadata files.
        """
        # Check for version metadata files
        for wasm_dir in self.wasm_dirs:
            if not wasm_dir.exists():
                continue
                
            # Look for manifest or version files
            version_files = [
                wasm_dir / "manifest.json",
                wasm_dir / "version.txt",
                wasm_dir / "openscad-version.txt"
            ]
            
            for version_file in version_files:
                if version_file.exists():
                    version = self._read_version_from_file(version_file)
                    if version:
                        return version
        
        # Fallback: try to infer from file sizes and timestamps
        return self._infer_version_from_metadata()
    
    def _read_version_from_file(self, version_file: Path) -> Optional[str]:
        """Read version from metadata file."""
        try:
            content = version_file.read_text().strip()
            
            if version_file.suffix == ".json":
                import json
                data = json.loads(content)
                return data.get("openscad_version") or data.get("version")
            else:
                # Plain text version file
                return content
                
        except Exception as e:
            logger.debug(f"Could not read version from {version_file}: {e}")
            return None
    
    def _infer_version_from_metadata(self) -> Optional[str]:
        """
        Infer WASM version from file metadata.
        
        This is a best-effort approach when no explicit version info exists.
        """
        wasm_files = self.find_bundled_wasm_files()
        if not wasm_files:
            return None
        
        # Use the largest WASM file (likely the main OpenSCAD module)
        main_wasm = max(wasm_files, key=lambda f: f.stat().st_size)
        
        # Try to extract version info from file stats
        file_size = main_wasm.stat().st_size
        
        # Known file size ranges for different OpenSCAD versions (approximate)
        # These would need to be updated based on actual WASM builds
        size_version_map = {
            (7_000_000, 8_000_000): "2021.01",  # ~7.7MB
            (8_000_000, 9_000_000): "2022.03",  # ~8.2MB
            (8_500_000, 9_500_000): "2023.06",  # ~8.8MB
        }
        
        for (min_size, max_size), version in size_version_map.items():
            if min_size <= file_size <= max_size:
                logger.info(f"Inferred WASM version {version} from file size {file_size}")
                return version
        
        logger.warning(f"Could not infer WASM version from file size {file_size}")
        return "unknown"
    
    def validate_wasm_integrity(self, wasm_path: Path) -> bool:
        """
        Validate WASM file integrity.
        
        Args:
            wasm_path: Path to WASM file
            
        Returns:
            True if WASM file appears valid
        """
        if not wasm_path.exists():
            return False
        
        try:
            # Read WASM header to verify it's a valid WASM file
            with wasm_path.open("rb") as f:
                header = f.read(8)
                
            # WASM files start with magic number and version
            # Magic: 0x00 0x61 0x73 0x6D (\0asm)
            # Version: 0x01 0x00 0x00 0x00 (version 1)
            expected_header = b'\x00asm\x01\x00\x00\x00'
            
            return header == expected_header
            
        except Exception as e:
            logger.error(f"Error validating WASM file {wasm_path}: {e}")
            return False


class OpenSCADVersionManager:
    """
    Comprehensive OpenSCAD version management system.
    
    Coordinates detection, validation, and management of multiple
    OpenSCAD installations (local and WASM).
    """
    
    def __init__(self):
        self.local_detector = LocalOpenSCADDetector()
        self.wasm_detector = WASMVersionDetector()
        self._detected_installations: Optional[List[OpenSCADInstallation]] = None
    
    def detect_all_installations(self) -> List[OpenSCADInstallation]:
        """
        Detect all available OpenSCAD installations.
        
        Returns:
            List of detected OpenSCAD installations
        """
        if self._detected_installations is not None:
            return self._detected_installations
        
        installations = []
        
        # Detect local installation
        local_install = self._detect_local_installation()
        if local_install:
            installations.append(local_install)
        
        # Detect bundled WASM
        wasm_install = self._detect_bundled_wasm()
        if wasm_install:
            installations.append(wasm_install)
        
        self._detected_installations = installations
        return installations
    
    def _detect_local_installation(self) -> Optional[OpenSCADInstallation]:
        """Detect local OpenSCAD installation."""
        executable = self.local_detector.find_openscad_executable()
        if not executable:
            return None
        
        version_string = self.local_detector.get_version_string(executable)
        if not version_string:
            return None
        
        version_info = self.local_detector.parse_version_info(version_string)
        if not version_info:
            return None
        
        return OpenSCADInstallation(
            version_info=version_info,
            installation_type=OpenSCADVersionType.LOCAL,
            executable_path=executable,
            capabilities=["full_openscad", "file_operations", "command_line"]
        )
    
    def _detect_bundled_wasm(self) -> Optional[OpenSCADInstallation]:
        """Detect bundled WASM installation."""
        wasm_files = self.wasm_detector.find_bundled_wasm_files()
        if not wasm_files:
            return None
        
        # Use the main WASM file (largest)
        main_wasm = max(wasm_files, key=lambda f: f.stat().st_size)
        
        if not self.wasm_detector.validate_wasm_integrity(main_wasm):
            logger.warning(f"WASM file {main_wasm} failed integrity check")
            return None
        
        # Get version (may be inferred)
        version_string = self.wasm_detector.detect_bundled_wasm_version()
        if version_string and version_string != "unknown":
            # Try to parse as version info
            try:
                # Handle simple version strings like "2023.06"
                parts = version_string.split(".")
                if len(parts) >= 2:
                    major = int(parts[0])
                    minor = int(parts[1])
                    patch = int(parts[2]) if len(parts) > 2 else 0
                    version_info = VersionInfo(major, minor, patch)
                else:
                    # Fallback version
                    version_info = VersionInfo(2023, 6, 0, "bundled")
            except ValueError:
                version_info = VersionInfo(2023, 6, 0, "bundled")
        else:
            # Default version for bundled WASM
            version_info = VersionInfo(2023, 6, 0, "bundled")
        
        return OpenSCADInstallation(
            version_info=version_info,
            installation_type=OpenSCADVersionType.WASM_BUNDLED,
            wasm_path=main_wasm,
            capabilities=["browser_rendering", "wasm_execution"]
        )
    
    def get_preferred_installation(self) -> Optional[OpenSCADInstallation]:
        """
        Get the preferred OpenSCAD installation.
        
        Preference order:
        1. Newest local installation
        2. Bundled WASM
        3. Any available installation
        """
        installations = self.detect_all_installations()
        if not installations:
            return None
        
        # Separate by type
        local_installs = [i for i in installations if i.installation_type == OpenSCADVersionType.LOCAL]
        wasm_installs = [i for i in installations if i.installation_type.name.startswith("WASM")]
        
        # Prefer newest local installation
        if local_installs:
            return max(local_installs, key=lambda i: i.version_info)
        
        # Fall back to WASM
        if wasm_installs:
            return wasm_installs[0]
        
        # Any installation is better than none
        return installations[0]
    
    def get_installation_by_version(self, target_version: Union[str, VersionInfo]) -> Optional[OpenSCADInstallation]:
        """
        Find installation matching target version.
        
        Args:
            target_version: Target version string or VersionInfo
            
        Returns:
            Matching installation if found
        """
        if isinstance(target_version, str):
            # Parse version string
            try:
                parts = target_version.split(".")
                major = int(parts[0])
                minor = int(parts[1]) if len(parts) > 1 else 0
                patch = int(parts[2]) if len(parts) > 2 else 0
                target_version = VersionInfo(major, minor, patch)
            except (ValueError, IndexError):
                logger.error(f"Invalid version string: {target_version}")
                return None
        
        installations = self.detect_all_installations()
        
        # Look for exact match first
        for installation in installations:
            if installation.version_info == target_version:
                return installation
        
        # Look for compatible version (same major.minor)
        for installation in installations:
            if (installation.version_info.major == target_version.major and
                installation.version_info.minor == target_version.minor):
                return installation
        
        return None
    
    def get_version_summary(self) -> Dict[str, any]:
        """Get summary of all detected versions."""
        installations = self.detect_all_installations()
        
        summary = {
            "total_installations": len(installations),
            "local_installations": [],
            "wasm_installations": [],
            "preferred_version": None
        }
        
        for installation in installations:
            install_info = {
                "version": str(installation.version_info),
                "type": installation.installation_type.value,
                "path": str(installation.executable_path or installation.wasm_path),
                "capabilities": installation.capabilities
            }
            
            if installation.installation_type == OpenSCADVersionType.LOCAL:
                summary["local_installations"].append(install_info)
            else:
                summary["wasm_installations"].append(install_info)
        
        preferred = self.get_preferred_installation()
        if preferred:
            summary["preferred_version"] = str(preferred.version_info)
        
        return summary


# Convenience functions for easy access
def detect_openscad_version() -> Optional[str]:
    """Quick version detection - returns version string of preferred installation."""
    manager = OpenSCADVersionManager()
    preferred = manager.get_preferred_installation()
    return str(preferred.version_info) if preferred else None


def is_openscad_available() -> bool:
    """Check if any OpenSCAD installation is available."""
    manager = OpenSCADVersionManager()
    installations = manager.detect_all_installations()
    return len(installations) > 0


def get_openscad_capabilities() -> List[str]:
    """Get capabilities of preferred OpenSCAD installation."""
    manager = OpenSCADVersionManager()
    preferred = manager.get_preferred_installation()
    return preferred.capabilities if preferred else []