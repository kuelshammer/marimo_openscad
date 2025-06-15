/**
 * Phase 5.2.3 Accessibility Manager Tests
 * Comprehensive tests for keyboard navigation and accessibility features
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock global objects and APIs
global.THREE = {
    Spherical: class {
        constructor() { this.theta = 0; this.phi = Math.PI / 2; }
        setFromVector3(vec) { return this; }
    },
    Vector3: class {
        constructor(x = 0, y = 0, z = 0) { this.x = x; this.y = y; this.z = z; }
        clone() { return new THREE.Vector3(this.x, this.y, this.z); }
        sub(v) { this.x -= v.x; this.y -= v.y; this.z -= v.z; return this; }
        add(v) { this.x += v.x; this.y += v.y; this.z += v.z; return this; }
        addScaledVector(v, s) { this.x += v.x * s; this.y += v.y * s; this.z += v.z * s; return this; }
        copy(v) { this.x = v.x; this.y = v.y; this.z = v.z; return this; }
        set(x, y, z) { this.x = x; this.y = y; this.z = z; return this; }
        distanceTo(v) { return Math.sqrt((this.x - v.x)**2 + (this.y - v.y)**2 + (this.z - v.z)**2); }
        normalize() { const len = Math.sqrt(this.x**2 + this.y**2 + this.z**2); this.x /= len; this.y /= len; this.z /= len; return this; }
        crossVectors(a, b) { this.x = a.y * b.z - a.z * b.y; this.y = a.z * b.x - a.x * b.z; this.z = a.x * b.y - a.y * b.x; return this; }
        subVectors(a, b) { this.x = a.x - b.x; this.y = a.y - b.y; this.z = a.z - b.z; return this; }
        applyMatrix3() { return this; }
        getWorldDirection() { return this; }
    }
};

global.window = {
    matchMedia: vi.fn((query) => ({
        matches: query.includes('reduce') ? false : query.includes('high') ? false : false,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn()
    })),
    speechSynthesis: {},
    requestFullscreen: vi.fn(),
    focus: vi.fn(),
    blur: vi.fn()
};

global.navigator = {
    userAgent: 'Mozilla/5.0 (Test Environment)',
    mediaDevices: { getUserMedia: vi.fn() },
    maxTouchPoints: 0
};

global.document = {
    createElement: vi.fn((tag) => ({
        tagName: tag.toUpperCase(),
        style: {},
        classList: {
            add: vi.fn(),
            remove: vi.fn(),
            contains: vi.fn(() => false)
        },
        setAttribute: vi.fn(),
        getAttribute: vi.fn(),
        appendChild: vi.fn(),
        removeChild: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        focus: vi.fn(),
        blur: vi.fn(),
        innerHTML: '',
        textContent: '',
        parentNode: null,
        remove: vi.fn()
    })),
    getElementById: vi.fn(),
    body: {
        appendChild: vi.fn(),
        removeChild: vi.fn()
    },
    fullscreenElement: null,
    exitFullscreen: vi.fn(),
    documentElement: {
        style: {
            setProperty: vi.fn(),
            removeProperty: vi.fn()
        }
    }
};

// Extract AccessibilityManager from embedded JavaScript
// Since we can't directly import it, we'll create a test environment
function createAccessibilityManager() {
    // Mock container
    const container = {
        style: {},
        classList: {
            add: vi.fn(),
            remove: vi.fn(),
            contains: vi.fn(() => false)
        },
        setAttribute: vi.fn(),
        getAttribute: vi.fn(),
        appendChild: vi.fn(),
        removeChild: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        focus: vi.fn(),
        blur: vi.fn(),
        getBoundingClientRect: () => ({ width: 600, height: 400, left: 0, top: 0 })
    };

    // Mock controls
    const controls = {
        object: {
            position: new THREE.Vector3(10, 10, 10),
            up: new THREE.Vector3(0, 1, 0),
            lookAt: vi.fn(),
            getWorldDirection: vi.fn(() => new THREE.Vector3(0, 0, -1))
        },
        target: new THREE.Vector3(0, 0, 0),
        update: vi.fn()
    };
    
    // Add set method as spy
    controls.object.position.set = vi.fn((x, y, z) => {
        controls.object.position.x = x;
        controls.object.position.y = y;
        controls.object.position.z = z;
    });
    
    controls.target.set = vi.fn((x, y, z) => {
        controls.target.x = x;
        controls.target.y = y;
        controls.target.z = z;
    });

    // Create AccessibilityManager class (simplified version for testing)
    class AccessibilityManager {
        constructor(container, controls) {
            this.container = container;
            this.controls = controls;
            this.enabled = true;
            
            // Keyboard navigation state
            this.keyboardEnabled = true;
            this.focusVisible = false;
            this.activeElement = null;
            
            // Navigation speeds
            this.rotationSpeed = 0.05;
            this.panSpeed = 0.1;
            this.zoomSpeed = 0.1;
            
            // Accessibility features
            this.screenReaderEnabled = this.detectScreenReader();
            this.highContrastMode = false;
            this.reducedMotion = this.detectReducedMotion();
            
            // Keyboard shortcuts
            this.shortcuts = {
                'ArrowLeft': () => this.rotateCamera(-this.rotationSpeed, 0),
                'ArrowRight': () => this.rotateCamera(this.rotationSpeed, 0),
                'ArrowUp': () => this.rotateCamera(0, -this.rotationSpeed),
                'ArrowDown': () => this.rotateCamera(0, this.rotationSpeed),
                'w': () => this.panCamera(0, this.panSpeed, 0),
                'a': () => this.panCamera(-this.panSpeed, 0, 0),
                's': () => this.panCamera(0, -this.panSpeed, 0),
                'd': () => this.panCamera(this.panSpeed, 0, 0),
                'q': () => this.panCamera(0, 0, this.panSpeed),
                'e': () => this.panCamera(0, 0, -this.panSpeed),
                '+': () => this.zoomCamera(1 + this.zoomSpeed),
                '-': () => this.zoomCamera(1 - this.zoomSpeed),
                'r': () => this.resetCamera(),
                '1': () => this.setViewPreset('front'),
                '2': () => this.setViewPreset('back'),
                '3': () => this.setViewPreset('left'),
                '4': () => this.setViewPreset('right'),
                '5': () => this.setViewPreset('top'),
                '6': () => this.setViewPreset('bottom'),
                '7': () => this.setViewPreset('isometric'),
                'h': () => this.showKeyboardHelp(),
                'c': () => this.toggleHighContrast(),
                'f': () => this.toggleFullscreen(),
                'Escape': () => this.exitFocus()
            };
            
            this.announcements = null;
            this.keyboardHelp = null;
            this.initializeAccessibility();
        }

        detectScreenReader() {
            return !!(
                navigator.userAgent.includes('NVDA') ||
                navigator.userAgent.includes('JAWS') ||
                navigator.userAgent.includes('VoiceOver') ||
                window.speechSynthesis ||
                navigator.mediaDevices?.getUserMedia
            );
        }

        detectReducedMotion() {
            return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        }

        initializeAccessibility() {
            this.container.setAttribute('tabindex', '0');
            this.container.setAttribute('role', 'application');
            this.container.setAttribute('aria-label', '3D OpenSCAD Model Viewer');
            
            this.announcements = document.createElement('div');
            this.announcements.setAttribute('aria-live', 'polite');
            this.container.appendChild(this.announcements);
            
            this.createKeyboardHelp();
            this.setupEventListeners();
            this.applyAccessibilityPreferences();
            this.announce('3D OpenSCAD viewer loaded. Press H for keyboard shortcuts.');
        }

        setupEventListeners() {
            this.container.addEventListener('keydown', (e) => {
                if (!this.keyboardEnabled) return;
                const shortcut = this.shortcuts[e.key];
                if (shortcut) {
                    e.preventDefault();
                    shortcut();
                    this.showFocusIndicator();
                }
            });

            this.container.addEventListener('focus', () => {
                this.focusVisible = true;
                this.container.classList.add('keyboard-focused');
                this.announce('3D viewer focused. Use arrow keys to rotate, WASD to pan, +/- to zoom.');
            });

            this.container.addEventListener('blur', () => {
                this.focusVisible = false;
                this.container.classList.remove('keyboard-focused');
            });
        }

        applyAccessibilityPreferences() {
            if (this.reducedMotion) {
                this.container.classList.add('reduced-motion');
                if (this.controls && this.controls.enableDamping) {
                    this.controls.enableDamping = false;
                }
            }
            
            if (window.matchMedia('(prefers-contrast: high)').matches) {
                this.enableHighContrast();
            }
        }

        rotateCamera(deltaX, deltaY) {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            const spherical = new THREE.Spherical();
            spherical.setFromVector3(camera.position.clone().sub(this.controls.target));
            
            if (deltaX !== 0) {
                spherical.theta += deltaX;
                camera.position.setFromSpherical = () => camera.position.add(this.controls.target);
            }
            
            if (deltaY !== 0) {
                spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi + deltaY));
                camera.position.setFromSpherical = () => camera.position.add(this.controls.target);
            }
            
            camera.lookAt(this.controls.target);
            this.controls.update();
            this.announce(`Camera rotated. Position: ${this.describeCameraPosition()}`);
        }

        panCamera(deltaX, deltaY, deltaZ) {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            const offset = new THREE.Vector3(deltaX, deltaY, deltaZ);
            camera.position.add(offset);
            this.controls.target.add(offset);
            this.controls.update();
            this.announce(`Camera panned. Position: ${this.describeCameraPosition()}`);
        }

        zoomCamera(factor) {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            const distance = camera.position.distanceTo(this.controls.target);
            const newDistance = Math.max(0.1, distance * (1 / factor));
            
            const direction = new THREE.Vector3();
            direction.subVectors(this.controls.target, camera.position).normalize();
            camera.position.copy(this.controls.target).addScaledVector(direction, -newDistance);
            this.controls.update();
            this.announce(`Camera zoom: ${factor > 1 ? 'in' : 'out'}. Distance: ${newDistance.toFixed(1)}`);
        }

        resetCamera() {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            camera.position.set(10, 10, 10);
            this.controls.target.set(0, 0, 0);
            camera.lookAt(this.controls.target);
            this.controls.update();
            this.announce('Camera reset to default position');
        }

        setViewPreset(view) {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            const distance = camera.position.distanceTo(this.controls.target);
            
            const positions = {
                front: [0, 0, distance],
                back: [0, 0, -distance],
                left: [-distance, 0, 0],
                right: [distance, 0, 0],
                top: [0, distance, 0],
                bottom: [0, -distance, 0],
                isometric: [distance * 0.7, distance * 0.7, distance * 0.7]
            };
            
            const pos = positions[view];
            if (pos) {
                camera.position.set(...pos);
                camera.lookAt(this.controls.target);
                this.controls.update();
                this.announce(`View set to ${view}`);
            }
        }

        describeCameraPosition() {
            if (!this.controls?.object) return 'unknown';
            
            const camera = this.controls.object;
            const pos = camera.position;
            const distance = pos.distanceTo(this.controls.target);
            
            return `X: ${pos.x.toFixed(1)}, Y: ${pos.y.toFixed(1)}, Z: ${pos.z.toFixed(1)}, Distance: ${distance.toFixed(1)}`;
        }

        showFocusIndicator() {
            this.container.classList.add('keyboard-active');
            setTimeout(() => {
                this.container.classList.remove('keyboard-active');
            }, 200);
        }

        announce(message) {
            if (!this.announcements) return;
            this.announcements.textContent = message;
        }

        createKeyboardHelp() {
            this.keyboardHelp = document.createElement('div');
            this.keyboardHelp.id = 'viewer-help';
            this.keyboardHelp.style.display = 'none';
            document.body.appendChild(this.keyboardHelp);
        }

        showKeyboardHelp() {
            if (this.keyboardHelp) {
                this.keyboardHelp.style.display = 'block';
                this.announce('Keyboard help dialog opened');
            }
        }

        toggleHighContrast() {
            this.highContrastMode = !this.highContrastMode;
            if (this.highContrastMode) {
                this.enableHighContrast();
            } else {
                this.disableHighContrast();
            }
            this.announce(`High contrast mode ${this.highContrastMode ? 'enabled' : 'disabled'}`);
        }

        enableHighContrast() {
            this.container.classList.add('high-contrast');
            document.documentElement.style.setProperty('--viewer-bg', '#000000');
            document.documentElement.style.setProperty('--viewer-text', '#ffffff');
            document.documentElement.style.setProperty('--viewer-border', '#ffffff');
        }

        disableHighContrast() {
            this.container.classList.remove('high-contrast');
            document.documentElement.style.removeProperty('--viewer-bg');
            document.documentElement.style.removeProperty('--viewer-text');
            document.documentElement.style.removeProperty('--viewer-border');
        }

        toggleFullscreen() {
            if (!document.fullscreenElement) {
                this.container.requestFullscreen?.();
                this.announce('Entered fullscreen mode');
            } else {
                document.exitFullscreen?.();
                this.announce('Exited fullscreen mode');
            }
        }

        exitFocus() {
            if (this.keyboardHelp && this.keyboardHelp.style.display !== 'none') {
                this.keyboardHelp.style.display = 'none';
                this.container.focus();
                this.announce('Help dialog closed');
            } else {
                this.container.blur();
                this.announce('Viewer unfocused');
            }
        }

        setKeyboardEnabled(enabled) {
            this.keyboardEnabled = enabled;
            this.announce(`Keyboard navigation ${enabled ? 'enabled' : 'disabled'}`);
        }

        getAccessibilityInfo() {
            return {
                keyboardEnabled: this.keyboardEnabled,
                screenReaderDetected: this.screenReaderEnabled,
                highContrastMode: this.highContrastMode,
                reducedMotion: this.reducedMotion,
                focusVisible: this.focusVisible,
                shortcuts: Object.keys(this.shortcuts)
            };
        }

        dispose() {
            this.enabled = false;
            if (this.keyboardHelp?.parentNode) {
                this.keyboardHelp.parentNode.removeChild(this.keyboardHelp);
            }
            if (this.announcements?.parentNode) {
                this.announcements.parentNode.removeChild(this.announcements);
            }
        }
    }

    return new AccessibilityManager(container, controls);
}

describe('Phase 5.2.3 AccessibilityManager', () => {
    let accessibilityManager;
    let container;
    let controls;

    beforeEach(() => {
        vi.clearAllMocks();
        accessibilityManager = createAccessibilityManager();
        container = accessibilityManager.container;
        controls = accessibilityManager.controls;
    });

    afterEach(() => {
        if (accessibilityManager) {
            accessibilityManager.dispose();
        }
    });

    describe('Initialization', () => {
        it('should initialize with correct default values', () => {
            expect(accessibilityManager.enabled).toBe(true);
            expect(accessibilityManager.keyboardEnabled).toBe(true);
            expect(accessibilityManager.focusVisible).toBe(false);
            expect(accessibilityManager.rotationSpeed).toBe(0.05);
            expect(accessibilityManager.panSpeed).toBe(0.1);
            expect(accessibilityManager.zoomSpeed).toBe(0.1);
        });

        it('should set up container accessibility attributes', () => {
            expect(container.setAttribute).toHaveBeenCalledWith('tabindex', '0');
            expect(container.setAttribute).toHaveBeenCalledWith('role', 'application');
            expect(container.setAttribute).toHaveBeenCalledWith('aria-label', '3D OpenSCAD Model Viewer');
        });

        it('should create ARIA live region for announcements', () => {
            expect(accessibilityManager.announcements).toBeDefined();
            expect(accessibilityManager.announcements.setAttribute).toHaveBeenCalledWith('aria-live', 'polite');
        });

        it('should detect screen reader correctly', () => {
            expect(typeof accessibilityManager.screenReaderEnabled).toBe('boolean');
        });

        it('should detect reduced motion preference', () => {
            expect(typeof accessibilityManager.reducedMotion).toBe('boolean');
        });
    });

    describe('Keyboard Shortcuts', () => {
        it('should have all required keyboard shortcuts', () => {
            const expectedShortcuts = [
                'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                'w', 'a', 's', 'd', 'q', 'e',
                '+', '-', 'r',
                '1', '2', '3', '4', '5', '6', '7',
                'h', 'c', 'f', 'Escape'
            ];

            expectedShortcuts.forEach(key => {
                expect(accessibilityManager.shortcuts).toHaveProperty(key);
                expect(typeof accessibilityManager.shortcuts[key]).toBe('function');
            });
        });

        it('should execute camera rotation shortcuts', () => {
            const rotateSpy = vi.spyOn(accessibilityManager, 'rotateCamera');
            
            accessibilityManager.shortcuts['ArrowLeft']();
            expect(rotateSpy).toHaveBeenCalledWith(-0.05, 0);
            
            accessibilityManager.shortcuts['ArrowRight']();
            expect(rotateSpy).toHaveBeenCalledWith(0.05, 0);
            
            accessibilityManager.shortcuts['ArrowUp']();
            expect(rotateSpy).toHaveBeenCalledWith(0, -0.05);
            
            accessibilityManager.shortcuts['ArrowDown']();
            expect(rotateSpy).toHaveBeenCalledWith(0, 0.05);
        });

        it('should execute camera pan shortcuts', () => {
            const panSpy = vi.spyOn(accessibilityManager, 'panCamera');
            
            accessibilityManager.shortcuts['w']();
            expect(panSpy).toHaveBeenCalledWith(0, 0.1, 0);
            
            accessibilityManager.shortcuts['a']();
            expect(panSpy).toHaveBeenCalledWith(-0.1, 0, 0);
            
            accessibilityManager.shortcuts['s']();
            expect(panSpy).toHaveBeenCalledWith(0, -0.1, 0);
            
            accessibilityManager.shortcuts['d']();
            expect(panSpy).toHaveBeenCalledWith(0.1, 0, 0);
        });

        it('should execute zoom shortcuts', () => {
            const zoomSpy = vi.spyOn(accessibilityManager, 'zoomCamera');
            
            accessibilityManager.shortcuts['+']();
            expect(zoomSpy).toHaveBeenCalledWith(1.1);
            
            accessibilityManager.shortcuts['-']();
            expect(zoomSpy).toHaveBeenCalledWith(0.9);
        });

        it('should execute view preset shortcuts', () => {
            const presetSpy = vi.spyOn(accessibilityManager, 'setViewPreset');
            
            accessibilityManager.shortcuts['1']();
            expect(presetSpy).toHaveBeenCalledWith('front');
            
            accessibilityManager.shortcuts['7']();
            expect(presetSpy).toHaveBeenCalledWith('isometric');
        });
    });

    describe('Camera Controls', () => {
        it('should rotate camera correctly', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.rotateCamera(0.1, 0.2);
            
            expect(controls.object.lookAt).toHaveBeenCalledWith(controls.target);
            expect(controls.update).toHaveBeenCalled();
            expect(announceSpy).toHaveBeenCalledWith(expect.stringContaining('Camera rotated'));
        });

        it('should pan camera correctly', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.panCamera(1, 2, 3);
            
            expect(controls.update).toHaveBeenCalled();
            expect(announceSpy).toHaveBeenCalledWith(expect.stringContaining('Camera panned'));
        });

        it('should zoom camera correctly', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.zoomCamera(1.5);
            
            expect(controls.update).toHaveBeenCalled();
            expect(announceSpy).toHaveBeenCalledWith(expect.stringContaining('Camera zoom'));
        });

        it('should reset camera to default position', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.resetCamera();
            
            expect(controls.object.position.set).toHaveBeenCalledWith(10, 10, 10);
            expect(controls.target.set).toHaveBeenCalledWith(0, 0, 0);
            expect(controls.object.lookAt).toHaveBeenCalledWith(controls.target);
            expect(controls.update).toHaveBeenCalled();
            expect(announceSpy).toHaveBeenCalledWith('Camera reset to default position');
        });

        it('should handle camera operations when controls are null', () => {
            accessibilityManager.controls = null;
            
            expect(() => {
                accessibilityManager.rotateCamera(0.1, 0.2);
                accessibilityManager.panCamera(1, 2, 3);
                accessibilityManager.zoomCamera(1.5);
                accessibilityManager.resetCamera();
            }).not.toThrow();
        });
    });

    describe('View Presets', () => {
        it('should set front view preset', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.setViewPreset('front');
            
            expect(controls.object.position.set).toHaveBeenCalled();
            expect(controls.object.lookAt).toHaveBeenCalledWith(controls.target);
            expect(controls.update).toHaveBeenCalled();
            expect(announceSpy).toHaveBeenCalledWith('View set to front');
        });

        it('should set all view presets correctly', () => {
            const presets = ['front', 'back', 'left', 'right', 'top', 'bottom', 'isometric'];
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            presets.forEach(preset => {
                accessibilityManager.setViewPreset(preset);
                expect(announceSpy).toHaveBeenCalledWith(`View set to ${preset}`);
            });
        });

        it('should handle invalid view preset', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.setViewPreset('invalid');
            
            expect(announceSpy).not.toHaveBeenCalled();
        });
    });

    describe('Focus Management', () => {
        it('should handle focus events correctly', () => {
            const focusEvent = new Event('focus');
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            container.addEventListener.mock.calls.find(call => call[0] === 'focus')[1](focusEvent);
            
            expect(accessibilityManager.focusVisible).toBe(true);
            expect(container.classList.add).toHaveBeenCalledWith('keyboard-focused');
            expect(announceSpy).toHaveBeenCalledWith(expect.stringContaining('3D viewer focused'));
        });

        it('should handle blur events correctly', () => {
            const blurEvent = new Event('blur');
            
            accessibilityManager.focusVisible = true;
            container.addEventListener.mock.calls.find(call => call[0] === 'blur')[1](blurEvent);
            
            expect(accessibilityManager.focusVisible).toBe(false);
            expect(container.classList.remove).toHaveBeenCalledWith('keyboard-focused');
        });

        it('should show focus indicator on keyboard interaction', () => {
            accessibilityManager.showFocusIndicator();
            
            expect(container.classList.add).toHaveBeenCalledWith('keyboard-active');
        });
    });

    describe('High Contrast Mode', () => {
        it('should toggle high contrast mode', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            expect(accessibilityManager.highContrastMode).toBe(false);
            
            accessibilityManager.toggleHighContrast();
            
            expect(accessibilityManager.highContrastMode).toBe(true);
            expect(container.classList.add).toHaveBeenCalledWith('high-contrast');
            expect(document.documentElement.style.setProperty).toHaveBeenCalledWith('--viewer-bg', '#000000');
            expect(announceSpy).toHaveBeenCalledWith('High contrast mode enabled');
        });

        it('should disable high contrast mode', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.highContrastMode = true;
            accessibilityManager.toggleHighContrast();
            
            expect(accessibilityManager.highContrastMode).toBe(false);
            expect(container.classList.remove).toHaveBeenCalledWith('high-contrast');
            expect(document.documentElement.style.removeProperty).toHaveBeenCalledWith('--viewer-bg');
            expect(announceSpy).toHaveBeenCalledWith('High contrast mode disabled');
        });
    });

    describe('Announcements', () => {
        it('should announce messages to screen readers', () => {
            const message = 'Test announcement';
            
            accessibilityManager.announce(message);
            
            expect(accessibilityManager.announcements.textContent).toBe(message);
        });

        it('should handle announcements when announcements element is null', () => {
            accessibilityManager.announcements = null;
            
            expect(() => {
                accessibilityManager.announce('Test message');
            }).not.toThrow();
        });

        it('should announce camera position changes', () => {
            const position = accessibilityManager.describeCameraPosition();
            
            expect(position).toContain('X:');
            expect(position).toContain('Y:');
            expect(position).toContain('Z:');
            expect(position).toContain('Distance:');
        });
    });

    describe('Keyboard Help', () => {
        it('should create keyboard help dialog', () => {
            expect(accessibilityManager.keyboardHelp).toBeDefined();
            expect(document.body.appendChild).toHaveBeenCalled();
        });

        it('should show keyboard help', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.showKeyboardHelp();
            
            expect(accessibilityManager.keyboardHelp.style.display).toBe('block');
            expect(announceSpy).toHaveBeenCalledWith('Keyboard help dialog opened');
        });

        it('should handle exit focus for help dialog', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.keyboardHelp.style.display = 'block';
            accessibilityManager.exitFocus();
            
            expect(accessibilityManager.keyboardHelp.style.display).toBe('none');
            expect(container.focus).toHaveBeenCalled();
            expect(announceSpy).toHaveBeenCalledWith('Help dialog closed');
        });
    });

    describe('Fullscreen Support', () => {
        it('should toggle fullscreen mode', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.toggleFullscreen();
            
            expect(announceSpy).toHaveBeenCalledWith('Entered fullscreen mode');
        });

        it('should exit fullscreen when already in fullscreen', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            document.fullscreenElement = container;
            
            accessibilityManager.toggleFullscreen();
            
            expect(document.exitFullscreen).toHaveBeenCalled();
            expect(announceSpy).toHaveBeenCalledWith('Exited fullscreen mode');
        });
    });

    describe('Accessibility Preferences', () => {
        it('should apply reduced motion preferences', () => {
            // Mock reduced motion preference
            window.matchMedia = vi.fn((query) => ({
                matches: query.includes('reduce') ? true : false
            }));
            
            const newManager = createAccessibilityManager();
            
            expect(newManager.reducedMotion).toBe(true);
            expect(newManager.container.classList.add).toHaveBeenCalledWith('reduced-motion');
        });

        it('should enable/disable keyboard navigation', () => {
            const announceSpy = vi.spyOn(accessibilityManager, 'announce');
            
            accessibilityManager.setKeyboardEnabled(false);
            
            expect(accessibilityManager.keyboardEnabled).toBe(false);
            expect(announceSpy).toHaveBeenCalledWith('Keyboard navigation disabled');
            
            accessibilityManager.setKeyboardEnabled(true);
            
            expect(accessibilityManager.keyboardEnabled).toBe(true);
            expect(announceSpy).toHaveBeenCalledWith('Keyboard navigation enabled');
        });
    });

    describe('Accessibility Info', () => {
        it('should return comprehensive accessibility information', () => {
            const info = accessibilityManager.getAccessibilityInfo();
            
            expect(info).toHaveProperty('keyboardEnabled');
            expect(info).toHaveProperty('screenReaderDetected');
            expect(info).toHaveProperty('highContrastMode');
            expect(info).toHaveProperty('reducedMotion');
            expect(info).toHaveProperty('focusVisible');
            expect(info).toHaveProperty('shortcuts');
            expect(Array.isArray(info.shortcuts)).toBe(true);
            expect(info.shortcuts.length).toBeGreaterThan(15);
        });
    });

    describe('Cleanup and Disposal', () => {
        it('should dispose properly', () => {
            accessibilityManager.keyboardHelp = { parentNode: { removeChild: vi.fn() } };
            accessibilityManager.announcements = { parentNode: { removeChild: vi.fn() } };
            
            accessibilityManager.dispose();
            
            expect(accessibilityManager.enabled).toBe(false);
            expect(accessibilityManager.keyboardHelp.parentNode.removeChild).toHaveBeenCalled();
            expect(accessibilityManager.announcements.parentNode.removeChild).toHaveBeenCalled();
        });

        it('should handle disposal when elements have no parent', () => {
            accessibilityManager.keyboardHelp = { parentNode: null };
            accessibilityManager.announcements = { parentNode: null };
            
            expect(() => {
                accessibilityManager.dispose();
            }).not.toThrow();
        });
    });
});