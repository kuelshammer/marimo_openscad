"""
Playwright configuration and fixtures for marimo-openscad E2E testing

This module provides browser-based testing infrastructure to detect real
integration problems without mocks. Expected to fail initially - this
documents the 4 critical issues identified in Step 5 analysis.
"""

import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from pathlib import Path
import tempfile
import json


@pytest.fixture(scope="session")
def browser() -> Browser:
    """Real browser instance for anywidget testing"""
    with sync_playwright() as p:
        # Use Chromium for consistent behavior
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',  # Required for CI environments
                '--disable-dev-shm-usage',  # Prevent /dev/shm issues
                '--disable-extensions',
                '--disable-gpu',
                '--disable-web-security',  # Allow local file access
                '--allow-running-insecure-content',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def browser_context(browser: Browser) -> BrowserContext:
    """Clean browser context for each test"""
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        permissions=['camera', 'microphone'],  # For potential WASM needs
        ignore_https_errors=True,
        bypass_csp=True,  # Bypass Content Security Policy for testing
        java_script_enabled=True
    )
    yield context
    context.close()


@pytest.fixture
def test_page(browser_context: BrowserContext) -> Page:
    """Clean page for each test with console monitoring"""
    page = browser_context.new_page()
    
    # Store console messages for analysis
    page.console_messages = []
    page.on("console", lambda msg: page.console_messages.append({
        'type': msg.type,
        'text': msg.text,
        'location': msg.location
    }))
    
    # Store network failures
    page.network_failures = []
    page.on("requestfailed", lambda req: page.network_failures.append({
        'url': req.url,
        'method': req.method,
        'failure': req.failure
    }))
    
    yield page
    page.close()


@pytest.fixture
def test_files_dir():
    """Directory containing test HTML files"""
    return Path(__file__).parent / "test_files"


@pytest.fixture
def create_test_html():
    """Factory to create temporary test HTML files"""
    created_files = []
    
    def _create_html(content: str, filename: str = None) -> Path:
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.html', 
                delete=False,
                encoding='utf-8'
            )
            temp_file.write(content)
            temp_file.close()
            created_files.append(temp_file.name)
            return Path(temp_file.name)
        else:
            test_dir = Path(__file__).parent / "test_files"
            test_dir.mkdir(exist_ok=True)
            file_path = test_dir / filename
            file_path.write_text(content, encoding='utf-8')
            created_files.append(str(file_path))
            return file_path
    
    yield _create_html
    
    # Cleanup created files
    for file_path in created_files:
        try:
            Path(file_path).unlink()
        except FileNotFoundError:
            pass


def capture_console_errors(page: Page) -> list:
    """Helper to extract console errors from page"""
    return [msg for msg in getattr(page, 'console_messages', []) 
            if msg['type'] == 'error']


def capture_network_failures(page: Page) -> list:
    """Helper to extract network failures from page"""
    return getattr(page, 'network_failures', [])


def analyze_import_errors(console_errors: list) -> dict:
    """Analyze console errors for import-related issues"""
    import_keywords = [
        'import', 'module', 'resolve', 'fetch', 'load', 
        'CORS', 'network', 'file://', 'relative'
    ]
    
    import_errors = []
    for error in console_errors:
        error_text = error['text'].lower()
        if any(keyword in error_text for keyword in import_keywords):
            import_errors.append(error)
    
    return {
        'total_errors': len(console_errors),
        'import_related_errors': len(import_errors),
        'import_errors': import_errors,
        'has_import_issues': len(import_errors) > 0
    }


def analyze_wasm_errors(console_errors: list, network_failures: list) -> dict:
    """Analyze errors for WASM-related issues"""
    wasm_keywords = ['wasm', 'webassembly', 'instantiate', 'compile']
    
    wasm_console_errors = []
    for error in console_errors:
        error_text = error['text'].lower()
        if any(keyword in error_text for keyword in wasm_keywords):
            wasm_console_errors.append(error)
    
    wasm_network_failures = []
    for failure in network_failures:
        if '.wasm' in failure['url'].lower():
            wasm_network_failures.append(failure)
    
    return {
        'wasm_console_errors': len(wasm_console_errors),
        'wasm_network_failures': len(wasm_network_failures),
        'wasm_errors_details': wasm_console_errors,
        'wasm_failures_details': wasm_network_failures,
        'has_wasm_issues': len(wasm_console_errors) > 0 or len(wasm_network_failures) > 0
    }


@pytest.fixture
def error_analyzer():
    """Fixture providing error analysis functions"""
    return {
        'capture_console_errors': capture_console_errors,
        'capture_network_failures': capture_network_failures,
        'analyze_import_errors': analyze_import_errors,
        'analyze_wasm_errors': analyze_wasm_errors
    }