"""
Multi-WASM Version Management System

Handles downloading, caching, and dynamic switching between different
OpenSCAD WASM versions to support version compatibility requirements.
"""

import os
import json
import hashlib
import tempfile
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

from .version_manager import VersionInfo, OpenSCADVersionType

logger = logging.getLogger(__name__)


@dataclass
class WASMVersion:
    """Information about a WASM version."""
    version: str
    version_info: VersionInfo
    download_url: str
    file_size: int
    checksum: str
    download_date: Optional[datetime] = None
    local_path: Optional[Path] = None
    is_available: bool = False
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["browser_rendering", "wasm_execution"]


@dataclass 
class WASMDownloadResult:
    """Result of WASM download operation."""
    success: bool
    wasm_version: Optional[WASMVersion] = None
    error_message: Optional[str] = None
    download_time_ms: Optional[float] = None


class WASMVersionRegistry:
    """Registry of available WASM versions."""
    
    # Known WASM versions with download information
    KNOWN_VERSIONS = {
        "2021.01": {
            "download_url": "https://cdn.jsdelivr.net/npm/openscad-wasm@2021.01/dist/openscad.wasm",
            "backup_urls": [
                "https://unpkg.com/openscad-wasm@2021.01/dist/openscad.wasm"
            ],
            "expected_size": 7_700_000,  # ~7.7MB
            "checksum": "sha256:placeholder_for_2021_01_checksum"
        },
        "2022.03": {
            "download_url": "https://cdn.jsdelivr.net/npm/openscad-wasm@2022.03/dist/openscad.wasm",
            "backup_urls": [
                "https://unpkg.com/openscad-wasm@2022.03/dist/openscad.wasm"
            ],
            "expected_size": 8_200_000,  # ~8.2MB
            "checksum": "sha256:placeholder_for_2022_03_checksum"
        },
        "2023.06": {
            "download_url": "https://cdn.jsdelivr.net/npm/openscad-wasm@2023.06/dist/openscad.wasm",
            "backup_urls": [
                "https://unpkg.com/openscad-wasm@2023.06/dist/openscad.wasm"
            ],
            "expected_size": 8_800_000,  # ~8.8MB
            "checksum": "sha256:placeholder_for_2023_06_checksum"
        }
    }
    
    @classmethod
    def get_available_versions(cls) -> List[str]:
        """Get list of available WASM versions."""
        return list(cls.KNOWN_VERSIONS.keys())
    
    @classmethod
    def get_version_info(cls, version: str) -> Optional[Dict]:
        """Get information about a specific version."""
        return cls.KNOWN_VERSIONS.get(version)
    
    @classmethod
    def parse_version_string(cls, version_str: str) -> VersionInfo:
        """Parse version string into VersionInfo."""
        try:
            parts = version_str.split(".")
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return VersionInfo(major, minor, patch)
        except (ValueError, IndexError):
            logger.warning(f"Could not parse version string: {version_str}")
            return VersionInfo(2023, 6, 0, "unknown")


class WASMDownloader:
    """Downloads and validates WASM modules."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize WASM downloader.
        
        Args:
            cache_dir: Directory to cache downloaded WASM files
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "marimo_openscad" / "wasm"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Download configuration
        self.timeout_seconds = 60
        self.max_retries = 3
        self.chunk_size = 8192
    
    async def download_version(self, version: str) -> WASMDownloadResult:
        """
        Download a specific WASM version.
        
        Args:
            version: Version string to download
            
        Returns:
            Download result with success status
        """
        version_info = WASMVersionRegistry.get_version_info(version)
        if not version_info:
            return WASMDownloadResult(
                success=False,
                error_message=f"Unknown version: {version}"
            )
        
        start_time = datetime.now()
        
        try:
            # Try primary download URL first
            wasm_version = await self._download_from_url(
                version=version,
                url=version_info["download_url"],
                expected_size=version_info["expected_size"],
                expected_checksum=version_info["checksum"]
            )
            
            if wasm_version:
                download_time = (datetime.now() - start_time).total_seconds() * 1000
                return WASMDownloadResult(
                    success=True,
                    wasm_version=wasm_version,
                    download_time_ms=download_time
                )
            
            # Try backup URLs if primary failed
            for backup_url in version_info.get("backup_urls", []):
                logger.info(f"Trying backup URL for {version}: {backup_url}")
                wasm_version = await self._download_from_url(
                    version=version,
                    url=backup_url,
                    expected_size=version_info["expected_size"],
                    expected_checksum=version_info["checksum"]
                )
                if wasm_version:
                    download_time = (datetime.now() - start_time).total_seconds() * 1000
                    return WASMDownloadResult(
                        success=True,
                        wasm_version=wasm_version,
                        download_time_ms=download_time
                    )
            
            return WASMDownloadResult(
                success=False,
                error_message=f"Failed to download {version} from all available URLs"
            )
            
        except Exception as e:
            logger.error(f"Error downloading WASM version {version}: {e}")
            return WASMDownloadResult(
                success=False,
                error_message=str(e)
            )
    
    async def _download_from_url(self, version: str, url: str, 
                                expected_size: int, expected_checksum: str) -> Optional[WASMVersion]:
        """Download WASM from specific URL."""
        local_filename = f"openscad-{version}.wasm"
        local_path = self.cache_dir / local_filename
        
        # Check if already downloaded and valid
        if local_path.exists() and await self._validate_wasm_file(local_path, expected_checksum):
            logger.info(f"WASM {version} already cached at {local_path}")
            return self._create_wasm_version(version, url, local_path, expected_size, expected_checksum)
        
        logger.info(f"Downloading WASM {version} from {url}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    
                    # Check content length
                    content_length = response.headers.get('content-length')
                    if content_length and abs(int(content_length) - expected_size) > expected_size * 0.1:
                        logger.warning(f"Unexpected file size for {version}: {content_length} vs {expected_size}")
                    
                    # Download with progress
                    total_downloaded = 0
                    temp_path = local_path.with_suffix('.tmp')
                    
                    with open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            f.write(chunk)
                            total_downloaded += len(chunk)
                    
                    # Validate downloaded file
                    if await self._validate_wasm_file(temp_path, expected_checksum):
                        temp_path.rename(local_path)
                        logger.info(f"Successfully downloaded WASM {version} ({total_downloaded} bytes)")
                        
                        return self._create_wasm_version(version, url, local_path, expected_size, expected_checksum)
                    else:
                        temp_path.unlink()
                        logger.error(f"Downloaded WASM {version} failed validation")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to download from {url}: {e}")
            return None
    
    async def _validate_wasm_file(self, file_path: Path, expected_checksum: str) -> bool:
        """Validate WASM file integrity."""
        if not file_path.exists():
            return False
        
        try:
            # Check WASM magic number
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if header[:4] != b'\x00asm':
                    logger.error(f"Invalid WASM magic number in {file_path}")
                    return False
            
            # TODO: Implement proper checksum validation
            # For now, just check file size and magic number
            file_size = file_path.stat().st_size
            if file_size < 1_000_000:  # Less than 1MB is suspicious
                logger.error(f"WASM file {file_path} too small: {file_size} bytes")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating WASM file {file_path}: {e}")
            return False
    
    def _create_wasm_version(self, version: str, url: str, local_path: Path, 
                           expected_size: int, expected_checksum: str) -> WASMVersion:
        """Create WASMVersion object from downloaded file."""
        version_info = WASMVersionRegistry.parse_version_string(version)
        
        return WASMVersion(
            version=version,
            version_info=version_info,
            download_url=url,
            file_size=local_path.stat().st_size,
            checksum=expected_checksum,
            download_date=datetime.now(),
            local_path=local_path,
            is_available=True,
            capabilities=["browser_rendering", "wasm_execution", f"openscad_{version}"]
        )
    
    def list_cached_versions(self) -> List[WASMVersion]:
        """List all cached WASM versions."""
        cached_versions = []
        
        for wasm_file in self.cache_dir.glob("openscad-*.wasm"):
            # Extract version from filename
            version_match = wasm_file.stem.replace("openscad-", "")
            version_info = WASMVersionRegistry.get_version_info(version_match)
            
            if version_info:
                wasm_version = WASMVersion(
                    version=version_match,
                    version_info=WASMVersionRegistry.parse_version_string(version_match),
                    download_url=version_info["download_url"],
                    file_size=wasm_file.stat().st_size,
                    checksum=version_info["checksum"],
                    download_date=datetime.fromtimestamp(wasm_file.stat().st_mtime),
                    local_path=wasm_file,
                    is_available=True
                )
                cached_versions.append(wasm_version)
        
        return sorted(cached_versions, key=lambda v: v.version_info, reverse=True)
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear WASM cache.
        
        Args:
            older_than_days: Only clear files older than this many days
            
        Returns:
            Number of files cleared
        """
        cleared_count = 0
        cutoff_time = None
        
        if older_than_days:
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
        
        for wasm_file in self.cache_dir.glob("openscad-*.wasm"):
            should_clear = True
            
            if cutoff_time:
                file_time = datetime.fromtimestamp(wasm_file.stat().st_mtime)
                should_clear = file_time < cutoff_time
            
            if should_clear:
                try:
                    wasm_file.unlink()
                    cleared_count += 1
                    logger.info(f"Cleared cached WASM: {wasm_file}")
                except Exception as e:
                    logger.error(f"Failed to clear {wasm_file}: {e}")
        
        return cleared_count


class DynamicWASMLoader:
    """Manages dynamic loading and switching of WASM versions."""
    
    def __init__(self, downloader: Optional[WASMDownloader] = None):
        """
        Initialize dynamic WASM loader.
        
        Args:
            downloader: WASM downloader instance
        """
        self.downloader = downloader or WASMDownloader()
        self.active_version: Optional[str] = None
        self.loaded_versions: Dict[str, WASMVersion] = {}
        
        # Load information about cached versions
        self._refresh_cached_versions()
    
    def _refresh_cached_versions(self):
        """Refresh information about cached WASM versions."""
        cached_versions = self.downloader.list_cached_versions()
        self.loaded_versions = {v.version: v for v in cached_versions}
    
    async def ensure_version_available(self, version: str) -> bool:
        """
        Ensure a WASM version is available (download if needed).
        
        Args:
            version: Version to ensure is available
            
        Returns:
            True if version is now available
        """
        # Check if already cached
        if version in self.loaded_versions:
            return True
        
        # Try to download
        result = await self.downloader.download_version(version)
        if result.success and result.wasm_version:
            self.loaded_versions[version] = result.wasm_version
            logger.info(f"Successfully ensured WASM {version} is available")
            return True
        else:
            logger.error(f"Failed to ensure WASM {version} availability: {result.error_message}")
            return False
    
    async def load_wasm_version(self, version: str) -> Optional[WASMVersion]:
        """
        Load a specific WASM version.
        
        Args:
            version: Version to load
            
        Returns:
            WASMVersion if successful, None otherwise
        """
        # Ensure version is available
        if not await self.ensure_version_available(version):
            return None
        
        wasm_version = self.loaded_versions.get(version)
        if wasm_version:
            self.active_version = version
            logger.info(f"Loaded WASM version {version}")
            return wasm_version
        
        return None
    
    async def switch_wasm_version(self, new_version: str) -> bool:
        """
        Switch to a different WASM version.
        
        Args:
            new_version: Version to switch to
            
        Returns:
            True if switch was successful
        """
        if new_version == self.active_version:
            logger.debug(f"Already using WASM version {new_version}")
            return True
        
        wasm_version = await self.load_wasm_version(new_version)
        if wasm_version:
            previous_version = self.active_version
            self.active_version = new_version
            logger.info(f"Switched WASM version from {previous_version} to {new_version}")
            return True
        
        logger.error(f"Failed to switch to WASM version {new_version}")
        return False
    
    def get_active_wasm_version(self) -> Optional[WASMVersion]:
        """Get currently active WASM version."""
        if self.active_version:
            return self.loaded_versions.get(self.active_version)
        return None
    
    def get_available_versions(self) -> List[str]:
        """Get list of available WASM versions."""
        registry_versions = WASMVersionRegistry.get_available_versions()
        cached_versions = list(self.loaded_versions.keys())
        
        # Combine and deduplicate
        all_versions = list(set(registry_versions + cached_versions))
        return sorted(all_versions, reverse=True)
    
    def get_version_info_summary(self) -> Dict[str, any]:
        """Get summary of WASM version information."""
        return {
            "active_version": self.active_version,
            "available_versions": self.get_available_versions(),
            "cached_versions": list(self.loaded_versions.keys()),
            "registry_versions": WASMVersionRegistry.get_available_versions(),
            "cache_dir": str(self.downloader.cache_dir),
            "total_cached_size": sum(
                v.file_size for v in self.loaded_versions.values()
            )
        }


class WASMVersionSelector:
    """Intelligent WASM version selection based on requirements."""
    
    def __init__(self, loader: DynamicWASMLoader):
        """
        Initialize version selector.
        
        Args:
            loader: Dynamic WASM loader instance
        """
        self.loader = loader
    
    def select_optimal_version(self, requirements: Dict[str, any]) -> Optional[str]:
        """
        Select optimal WASM version based on requirements.
        
        Args:
            requirements: Dictionary of requirements
                - min_version: Minimum required version
                - preferred_version: Preferred version if available
                - features: List of required features
                - performance: "fastest" or "stable"
        
        Returns:
            Optimal version string, or None if no suitable version
        """
        available_versions = self.loader.get_available_versions()
        if not available_versions:
            return None
        
        # Parse requirements
        min_version_str = requirements.get("min_version")
        preferred_version = requirements.get("preferred_version")
        required_features = requirements.get("features", [])
        performance_preference = requirements.get("performance", "stable")
        
        # Convert to VersionInfo for comparison
        min_version = None
        if min_version_str:
            min_version = WASMVersionRegistry.parse_version_string(min_version_str)
        
        # Filter versions that meet minimum requirements
        suitable_versions = []
        for version_str in available_versions:
            version_info = WASMVersionRegistry.parse_version_string(version_str)
            
            # Check minimum version
            if min_version and version_info < min_version:
                continue
            
            # TODO: Check required features
            # For now, assume all WASM versions have basic features
            
            suitable_versions.append(version_str)
        
        if not suitable_versions:
            logger.warning(f"No WASM versions meet requirements: {requirements}")
            return None
        
        # Try preferred version first
        if preferred_version and preferred_version in suitable_versions:
            logger.info(f"Using preferred WASM version: {preferred_version}")
            return preferred_version
        
        # Sort by version (newest first for "fastest", oldest stable for "stable")
        if performance_preference == "fastest":
            # Use newest version
            sorted_versions = sorted(
                suitable_versions,
                key=lambda v: WASMVersionRegistry.parse_version_string(v),
                reverse=True
            )
        else:
            # Use most stable (often not the newest)
            # For now, prefer 2022.03 as stable, then others
            stability_order = ["2022.03", "2021.01", "2023.06"]
            sorted_versions = sorted(
                suitable_versions,
                key=lambda v: stability_order.index(v) if v in stability_order else 999
            )
        
        selected = sorted_versions[0]
        logger.info(f"Selected WASM version {selected} for requirements: {requirements}")
        return selected
    
    def analyze_scad_requirements(self, scad_code: str) -> Dict[str, any]:
        """
        Analyze SCAD code to determine version requirements.
        
        Args:
            scad_code: OpenSCAD code to analyze
            
        Returns:
            Dictionary of requirements
        """
        requirements = {
            "min_version": "2021.01",  # Conservative default
            "features": [],
            "performance": "stable"
        }
        
        # Simple pattern-based analysis
        # This would be expanded with proper AST parsing
        
        # Check for newer syntax features
        if "**" in scad_code:  # Exponent operator (2023.06+)
            requirements["min_version"] = "2023.06"
            requirements["features"].append("exponent_operator")
        
        if "list(" in scad_code or "[for" in scad_code:
            requirements["features"].append("list_comprehension")
        
        if "assert(" in scad_code:
            requirements["features"].append("assertions")
        
        # Prefer newer versions for complex models
        if len(scad_code) > 10000:  # Large model
            requirements["performance"] = "fastest"
        
        logger.debug(f"Analyzed SCAD requirements: {requirements}")
        return requirements


# Convenience class that combines all functionality
class WASMVersionManager:
    """
    Complete WASM version management system.
    
    Combines downloading, caching, loading, and selection functionality
    into a single easy-to-use interface.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize WASM version manager.
        
        Args:
            cache_dir: Directory for caching WASM files
        """
        self.downloader = WASMDownloader(cache_dir)
        self.loader = DynamicWASMLoader(self.downloader)
        self.selector = WASMVersionSelector(self.loader)
    
    async def get_optimal_version_for_scad(self, scad_code: str, 
                                         user_preferences: Optional[Dict] = None) -> Optional[str]:
        """
        Get optimal WASM version for SCAD code.
        
        Args:
            scad_code: OpenSCAD code to analyze
            user_preferences: User preferences to consider
            
        Returns:
            Optimal version string
        """
        # Analyze SCAD code requirements
        requirements = self.selector.analyze_scad_requirements(scad_code)
        
        # Apply user preferences
        if user_preferences:
            requirements.update(user_preferences)
        
        # Select optimal version
        return self.selector.select_optimal_version(requirements)
    
    async def ensure_version_ready(self, version: str) -> bool:
        """Ensure a version is downloaded and ready to use."""
        return await self.loader.ensure_version_available(version)
    
    async def switch_to_version(self, version: str) -> bool:
        """Switch to a specific WASM version."""
        return await self.loader.switch_wasm_version(version)
    
    def get_system_info(self) -> Dict[str, any]:
        """Get comprehensive system information."""
        loader_info = self.loader.get_version_info_summary()
        
        return {
            "wasm_manager": {
                "cache_dir": str(self.downloader.cache_dir),
                "available_versions": WASMVersionRegistry.get_available_versions(),
                "cached_versions": list(self.loader.loaded_versions.keys()),
                "active_version": self.loader.active_version,
                "total_cache_size_mb": loader_info["total_cached_size"] / (1024 * 1024)
            },
            "registry": {
                "known_versions": list(WASMVersionRegistry.KNOWN_VERSIONS.keys()),
                "version_count": len(WASMVersionRegistry.KNOWN_VERSIONS)
            }
        }