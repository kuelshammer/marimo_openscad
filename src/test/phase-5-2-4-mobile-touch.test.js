/**
 * Phase 5.2.4 Mobile Touch Manager Tests
 * Comprehensive tests for mobile touch controls and gesture recognition
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
        extractBasis: vi.fn(() => new THREE.Vector3())
    }
};

global.window = {
    ontouchstart: true,
    innerWidth: 768,
    innerHeight: 1024,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    requestAnimationFrame: vi.fn((cb) => setTimeout(cb, 16)),
    cancelAnimationFrame: vi.fn(),
    DeviceMotionEvent: class {},
    DeviceOrientationEvent: class {}
};

global.navigator = {
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)',
    maxTouchPoints: 5,
    vibrate: vi.fn()
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
        innerHTML: '',
        textContent: '',
        parentNode: null,
        remove: vi.fn()
    })),
    body: {
        appendChild: vi.fn(),
        removeChild: vi.fn()
    }
};

// Create touch event mocks
function createTouch(id, clientX, clientY) {
    return {
        identifier: id,
        clientX: clientX,
        clientY: clientY,
        pageX: clientX,
        pageY: clientY,
        target: null
    };
}

function createTouchEvent(type, touches = [], changedTouches = []) {
    return {
        type: type,
        touches: touches,
        changedTouches: changedTouches,
        targetTouches: touches,
        preventDefault: vi.fn(),
        stopPropagation: vi.fn(),
        clientX: touches[0]?.clientX || 0,
        clientY: touches[0]?.clientY || 0,
        scale: 1.0
    };
}

// Create MobileTouchManager test class
function createMobileTouchManager() {
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
        getBoundingClientRect: () => ({ width: 600, height: 400, left: 0, top: 0 }),
        requestFullscreen: vi.fn()
    };

    const canvas = {
        style: {},
        width: 600,
        height: 400
    };

    const controls = {
        object: {
            position: new THREE.Vector3(10, 10, 10),
            up: new THREE.Vector3(0, 1, 0),
            lookAt: vi.fn(),
            getWorldDirection: vi.fn(() => new THREE.Vector3(0, 0, -1)),
            matrix: {
                extractBasis: vi.fn(() => new THREE.Vector3())
            }
        },
        target: new THREE.Vector3(0, 0, 0),
        update: vi.fn()
    };

    // Simplified MobileTouchManager for testing
    class MobileTouchManager {
        constructor(container, canvas) {
            this.container = container;
            this.canvas = canvas;
            this.enabled = true;
            
            // Touch state management
            this.touches = new Map();
            this.lastTouchTime = 0;
            this.touchStartTime = 0;
            this.gestureActive = false;
            this.initialPinchDistance = 0;
            this.initialTouchCenter = { x: 0, y: 0 };
            
            // Mobile detection
            this.isMobile = this.detectMobile();
            this.isTablet = this.detectTablet();
            this.hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            
            // Touch sensitivity settings
            this.sensitivity = {
                rotation: this.isMobile ? 0.008 : 0.005,
                pan: this.isMobile ? 0.4 : 0.3,
                zoom: this.isMobile ? 0.3 : 0.2,
                doubleTap: 300,
                longPress: 800,
                swipeThreshold: 50
            };
            
            // Gesture recognition
            this.gestureTypes = {
                NONE: 'none',
                ROTATE: 'rotate',
                PAN: 'pan',
                ZOOM: 'zoom',
                SWIPE: 'swipe',
                TAP: 'tap',
                DOUBLE_TAP: 'double_tap',
                LONG_PRESS: 'long_press'
            };
            
            this.currentGesture = this.gestureTypes.NONE;
            this.lastTap = 0;
            this.longPressTimer = null;
            
            // Performance optimization for mobile
            this.frameThrottle = this.isMobile ? 33 : 16;
            this.lastFrameTime = 0;
            
            // Haptic feedback support
            this.hapticEnabled = this.detectHapticSupport();
            
            // Controls reference
            this.controls = null;
            
            this.initializeMobileControls();
        }

        detectMobile() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        }

        detectTablet() {
            return /iPad|Android.*Tablet|Windows.*Touch/i.test(navigator.userAgent) || 
                   (navigator.maxTouchPoints > 1 && window.innerWidth > 768);
        }

        detectHapticSupport() {
            return 'vibrate' in navigator || 'hapticFeedback' in navigator;
        }

        initializeMobileControls() {
            if (!this.hasTouch) return;
            
            this.applyMobileStyles();
            this.setupTouchListeners();
            this.createMobileUI();
            this.optimizeForMobile();
        }

        applyMobileStyles() {
            this.container.style.touchAction = 'none';
            this.container.style.userSelect = 'none';
            this.container.style.webkitUserSelect = 'none';
            this.container.style.webkitTouchCallout = 'none';
            
            if (this.isMobile) {
                this.container.style.cursor = 'grab';
            }
            
            this.container.classList.add('mobile-touch-enabled');
            if (this.isMobile) this.container.classList.add('mobile-device');
            if (this.isTablet) this.container.classList.add('tablet-device');
        }

        setupTouchListeners() {
            this.container.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
            this.container.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
            this.container.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: false });
            this.container.addEventListener('touchcancel', (e) => this.handleTouchCancel(e), { passive: false });
            
            this.container.addEventListener('gesturestart', (e) => this.handleGestureStart(e), { passive: false });
            this.container.addEventListener('gesturechange', (e) => this.handleGestureChange(e), { passive: false });
            this.container.addEventListener('gestureend', (e) => this.handleGestureEnd(e), { passive: false });
        }

        handleTouchStart(event) {
            event.preventDefault();
            
            const now = Date.now();
            this.touchStartTime = now;
            this.lastTouchTime = now;
            
            for (let i = 0; i < event.touches.length; i++) {
                const touch = event.touches[i];
                this.touches.set(touch.identifier, {
                    id: touch.identifier,
                    startX: touch.clientX,
                    startY: touch.clientY,
                    currentX: touch.clientX,
                    currentY: touch.clientY,
                    startTime: now
                });
            }
            
            this.determineGesture(event);
            
            if (event.touches.length === 1) {
                this.longPressTimer = setTimeout(() => {
                    this.triggerLongPress(event.touches[0]);
                }, this.sensitivity.longPress);
            }
            
            this.hapticFeedback('light');
        }

        handleTouchMove(event) {
            event.preventDefault();
            
            const now = Date.now();
            if (now - this.lastFrameTime < this.frameThrottle) return;
            this.lastFrameTime = now;
            
            if (this.longPressTimer) {
                clearTimeout(this.longPressTimer);
                this.longPressTimer = null;
            }
            
            for (let i = 0; i < event.touches.length; i++) {
                const touch = event.touches[i];
                const stored = this.touches.get(touch.identifier);
                if (stored) {
                    stored.currentX = touch.clientX;
                    stored.currentY = touch.clientY;
                }
            }
            
            this.handleGestureMove(event);
        }

        handleTouchEnd(event) {
            event.preventDefault();
            
            const now = Date.now();
            const touchDuration = now - this.touchStartTime;
            
            if (this.longPressTimer) {
                clearTimeout(this.longPressTimer);
                this.longPressTimer = null;
            }
            
            if (event.changedTouches.length === 1 && touchDuration < this.sensitivity.doubleTap) {
                this.handleTap(event.changedTouches[0], now);
            }
            
            for (let i = 0; i < event.changedTouches.length; i++) {
                const touch = event.changedTouches[i];
                this.touches.delete(touch.identifier);
            }
            
            if (event.touches.length === 0) {
                this.currentGesture = this.gestureTypes.NONE;
                this.gestureActive = false;
            }
            
            this.hapticFeedback('light');
        }

        handleTouchCancel(event) {
            this.touches.clear();
            this.currentGesture = this.gestureTypes.NONE;
            this.gestureActive = false;
            
            if (this.longPressTimer) {
                clearTimeout(this.longPressTimer);
                this.longPressTimer = null;
            }
        }

        determineGesture(event) {
            const touchCount = event.touches.length;
            
            if (touchCount === 1) {
                this.currentGesture = this.gestureTypes.PAN;
            } else if (touchCount === 2) {
                this.currentGesture = this.gestureTypes.ZOOM;
                this.setupPinchGesture(event);
            } else if (touchCount === 3) {
                this.currentGesture = this.gestureTypes.ROTATE;
            }
            
            this.gestureActive = true;
        }

        setupPinchGesture(event) {
            const touch1 = event.touches[0];
            const touch2 = event.touches[1];
            
            this.initialPinchDistance = this.getDistance(touch1, touch2);
            this.initialTouchCenter = this.getCenter(touch1, touch2);
        }

        handleGestureMove(event) {
            if (!this.gestureActive || !this.controls) return;
            
            switch (this.currentGesture) {
                case this.gestureTypes.PAN:
                    this.handlePanGesture(event);
                    break;
                case this.gestureTypes.ZOOM:
                    this.handleZoomGesture(event);
                    break;
                case this.gestureTypes.ROTATE:
                    this.handleRotateGesture(event);
                    break;
            }
        }

        handlePanGesture(event) {
            if (event.touches.length !== 1) return;
            
            const touch = event.touches[0];
            const stored = this.touches.get(touch.identifier);
            if (!stored) return;
            
            const deltaX = touch.clientX - stored.startX;
            const deltaY = touch.clientY - stored.startY;
            
            const rect = this.container.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const touchX = touch.clientX - rect.left;
            const touchY = touch.clientY - rect.top;
            
            const distanceFromCenter = Math.sqrt(
                Math.pow(touchX - centerX, 2) + Math.pow(touchY - centerY, 2)
            );
            
            const edgeThreshold = Math.min(rect.width, rect.height) * 0.3;
            
            if (distanceFromCenter > edgeThreshold) {
                this.applyCameraRotation(-deltaX * this.sensitivity.rotation, -deltaY * this.sensitivity.rotation);
            } else {
                this.applyCameraPan(deltaX * this.sensitivity.pan, -deltaY * this.sensitivity.pan);
            }
            
            stored.startX = touch.clientX;
            stored.startY = touch.clientY;
        }

        handleZoomGesture(event) {
            if (event.touches.length !== 2) return;
            
            const touch1 = event.touches[0];
            const touch2 = event.touches[1];
            
            const currentDistance = this.getDistance(touch1, touch2);
            const zoomFactor = currentDistance / this.initialPinchDistance;
            
            this.applyCameraZoom(zoomFactor);
            
            this.initialPinchDistance = currentDistance;
            
            this.hapticFeedback('medium');
        }

        handleRotateGesture(event) {
            if (event.touches.length < 2) return;
            
            const touch1 = event.touches[0];
            const touch2 = event.touches[1];
            
            const stored1 = this.touches.get(touch1.identifier);
            const stored2 = this.touches.get(touch2.identifier);
            
            if (!stored1 || !stored2) return;
            
            const deltaX = ((touch1.clientX - stored1.startX) + (touch2.clientX - stored2.startX)) / 2;
            const deltaY = ((touch1.clientY - stored1.startY) + (touch2.clientY - stored2.startY)) / 2;
            
            this.applyCameraRotation(deltaX * this.sensitivity.rotation * 0.5, deltaY * this.sensitivity.rotation * 0.5);
            
            stored1.startX = touch1.clientX;
            stored1.startY = touch1.clientY;
            stored2.startX = touch2.clientX;
            stored2.startY = touch2.clientY;
        }

        handleTap(touch, now) {
            const timeSinceLastTap = now - this.lastTap;
            
            if (timeSinceLastTap < this.sensitivity.doubleTap) {
                this.resetCamera();
                this.hapticFeedback('strong');
            } else {
                this.hapticFeedback('light');
            }
            
            this.lastTap = now;
        }

        triggerLongPress(touch) {
            this.showMobileMenu(touch);
            this.hapticFeedback('strong');
        }

        applyCameraRotation(deltaX, deltaY) {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            const spherical = new THREE.Spherical();
            spherical.setFromVector3(camera.position.clone().sub(this.controls.target));
            
            spherical.theta += deltaX;
            spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi + deltaY));
            
            camera.position.setFromSpherical = () => camera.position.add(this.controls.target);
            camera.lookAt(this.controls.target);
            this.controls.update();
        }

        applyCameraPan(deltaX, deltaY) {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            const offset = new THREE.Vector3();
            
            const right = new THREE.Vector3();
            const up = new THREE.Vector3();
            camera.getWorldDirection(offset);
            right.crossVectors(offset, camera.up).normalize();
            up.crossVectors(right, offset).normalize();
            
            const panOffset = new THREE.Vector3();
            panOffset.addScaledVector(right, deltaX * 0.01);
            panOffset.addScaledVector(up, deltaY * 0.01);
            
            camera.position.add(panOffset);
            this.controls.target.add(panOffset);
            this.controls.update();
        }

        applyCameraZoom(factor) {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            const direction = new THREE.Vector3();
            direction.subVectors(this.controls.target, camera.position).normalize();
            
            const distance = camera.position.distanceTo(this.controls.target);
            const newDistance = Math.max(0.1, distance / factor);
            
            camera.position.copy(this.controls.target).addScaledVector(direction, -newDistance);
            this.controls.update();
        }

        resetCamera() {
            if (!this.controls?.object) return;
            
            const camera = this.controls.object;
            camera.position.set(10, 10, 10);
            this.controls.target.set(0, 0, 0);
            camera.lookAt(this.controls.target);
            this.controls.update();
        }

        getDistance(touch1, touch2) {
            const dx = touch1.clientX - touch2.clientX;
            const dy = touch1.clientY - touch2.clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }

        getCenter(touch1, touch2) {
            return {
                x: (touch1.clientX + touch2.clientX) / 2,
                y: (touch1.clientY + touch2.clientY) / 2
            };
        }

        hapticFeedback(intensity = 'light') {
            if (!this.hapticEnabled) return;
            
            if (navigator.vibrate) {
                const patterns = {
                    light: [10],
                    medium: [20],
                    strong: [50]
                };
                navigator.vibrate(patterns[intensity] || patterns.light);
            }
        }

        createMobileUI() {
            if (!this.isMobile && !this.isTablet) return;
            
            const hints = document.createElement('div');
            hints.className = 'mobile-hints';
            hints.innerHTML = '📱 1 finger: Rotate/Pan | ✌️ 2 fingers: Zoom | 👆 Double tap: Reset';
            this.container.appendChild(hints);
            
            setTimeout(() => {
                hints.style.opacity = '0';
                setTimeout(() => hints.remove(), 500);
            }, 5000);
        }

        showMobileMenu(touch) {
            const menu = document.createElement('div');
            menu.className = 'mobile-context-menu';
            
            const options = [
                { text: '🏠 Reset View', action: () => this.resetCamera() },
                { text: '📐 Fit to Screen', action: () => this.fitToScreen() },
                { text: '🔄 Toggle Quality', action: () => this.toggleMobileQuality() },
                { text: '❌ Close', action: () => menu.remove() }
            ];
            
            options.forEach(option => {
                const item = document.createElement('div');
                item.textContent = option.text;
                item.addEventListener('click', () => {
                    option.action();
                    menu.remove();
                });
                menu.appendChild(item);
            });
            
            document.body.appendChild(menu);
            setTimeout(() => menu.remove(), 5000);
        }

        optimizeForMobile() {
            if (this.isMobile) {
                if (window.adaptiveQuality) {
                    window.adaptiveQuality.forceQuality('medium', 'Mobile optimization');
                }
                this.container.classList.add('mobile-optimized');
            }
        }

        fitToScreen() {
            console.log('📱 Fit to screen triggered');
        }

        toggleMobileQuality() {
            if (window.adaptiveQuality) {
                const current = window.adaptiveQuality.currentQuality;
                const newQuality = current === 'low' ? 'medium' : 'low';
                window.adaptiveQuality.forceQuality(newQuality, 'Mobile quality toggle');
            }
        }

        handleGestureStart(event) {
            event.preventDefault();
        }

        handleGestureChange(event) {
            event.preventDefault();
            this.applyCameraZoom(event.scale);
        }

        handleGestureEnd(event) {
            event.preventDefault();
        }

        setControls(controls) {
            this.controls = controls;
        }

        getMobileInfo() {
            return {
                isMobile: this.isMobile,
                isTablet: this.isTablet,
                hasTouch: this.hasTouch,
                hapticEnabled: this.hapticEnabled,
                currentGesture: this.currentGesture,
                activeTouches: this.touches.size,
                sensitivity: this.sensitivity
            };
        }

        dispose() {
            this.enabled = false;
            
            if (this.longPressTimer) {
                clearTimeout(this.longPressTimer);
                this.longPressTimer = null;
            }
            
            this.touches.clear();
        }
    }

    const manager = new MobileTouchManager(container, canvas);
    manager.setControls(controls);
    return manager;
}

describe('Phase 5.2.4 MobileTouchManager', () => {
    let mobileTouchManager;
    let container;
    let controls;

    beforeEach(() => {
        vi.clearAllMocks();
        mobileTouchManager = createMobileTouchManager();
        container = mobileTouchManager.container;
        controls = mobileTouchManager.controls;
    });

    afterEach(() => {
        if (mobileTouchManager) {
            mobileTouchManager.dispose();
        }
    });

    describe('Initialization', () => {
        it('should initialize with correct default values', () => {
            expect(mobileTouchManager.enabled).toBe(true);
            expect(mobileTouchManager.gestureActive).toBe(false);
            expect(mobileTouchManager.currentGesture).toBe('none');
            expect(mobileTouchManager.touches.size).toBe(0);
        });

        it('should detect mobile device correctly', () => {
            expect(mobileTouchManager.isMobile).toBe(true);
            expect(mobileTouchManager.hasTouch).toBe(true);
        });

        it('should detect tablet correctly', () => {
            expect(typeof mobileTouchManager.isTablet).toBe('boolean');
        });

        it('should detect haptic feedback support', () => {
            expect(mobileTouchManager.hapticEnabled).toBe(true);
        });

        it('should set appropriate sensitivity for mobile', () => {
            expect(mobileTouchManager.sensitivity.rotation).toBe(0.008);
            expect(mobileTouchManager.sensitivity.pan).toBe(0.4);
            expect(mobileTouchManager.sensitivity.zoom).toBe(0.3);
        });

        it('should apply mobile styles correctly', () => {
            expect(container.style.touchAction).toBe('none');
            expect(container.style.userSelect).toBe('none');
            expect(container.classList.add).toHaveBeenCalledWith('mobile-touch-enabled');
            expect(container.classList.add).toHaveBeenCalledWith('mobile-device');
        });
    });

    describe('Touch Event Handling', () => {
        it('should handle touch start event', () => {
            const touch = createTouch(1, 100, 200);
            const event = createTouchEvent('touchstart', [touch]);
            
            mobileTouchManager.handleTouchStart(event);
            
            expect(event.preventDefault).toHaveBeenCalled();
            expect(mobileTouchManager.touches.size).toBe(1);
            expect(mobileTouchManager.gestureActive).toBe(true);
            expect(mobileTouchManager.currentGesture).toBe('pan');
        });

        it('should handle touch move event', () => {
            const touch1 = createTouch(1, 100, 200);
            const touch2 = createTouch(1, 150, 250);
            const startEvent = createTouchEvent('touchstart', [touch1]);
            const moveEvent = createTouchEvent('touchmove', [touch2]);
            
            mobileTouchManager.handleTouchStart(startEvent);
            mobileTouchManager.handleTouchMove(moveEvent);
            
            expect(moveEvent.preventDefault).toHaveBeenCalled();
            expect(mobileTouchManager.touches.get(1).currentX).toBe(150);
            expect(mobileTouchManager.touches.get(1).currentY).toBe(250);
        });

        it('should handle touch end event', () => {
            const touch = createTouch(1, 100, 200);
            const startEvent = createTouchEvent('touchstart', [touch]);
            const endEvent = createTouchEvent('touchend', [], [touch]);
            
            mobileTouchManager.handleTouchStart(startEvent);
            mobileTouchManager.handleTouchEnd(endEvent);
            
            expect(endEvent.preventDefault).toHaveBeenCalled();
            expect(mobileTouchManager.touches.size).toBe(0);
            expect(mobileTouchManager.gestureActive).toBe(false);
        });

        it('should handle touch cancel event', () => {
            const touch = createTouch(1, 100, 200);
            const startEvent = createTouchEvent('touchstart', [touch]);
            const cancelEvent = createTouchEvent('touchcancel');
            
            mobileTouchManager.handleTouchStart(startEvent);
            mobileTouchManager.handleTouchCancel(cancelEvent);
            
            expect(mobileTouchManager.touches.size).toBe(0);
            expect(mobileTouchManager.gestureActive).toBe(false);
            expect(mobileTouchManager.currentGesture).toBe('none');
        });
    });

    describe('Gesture Recognition', () => {
        it('should recognize single finger pan gesture', () => {
            const touch = createTouch(1, 100, 200);
            const event = createTouchEvent('touchstart', [touch]);
            
            mobileTouchManager.determineGesture(event);
            
            expect(mobileTouchManager.currentGesture).toBe('pan');
            expect(mobileTouchManager.gestureActive).toBe(true);
        });

        it('should recognize two finger zoom gesture', () => {
            const touch1 = createTouch(1, 100, 200);
            const touch2 = createTouch(2, 200, 300);
            const event = createTouchEvent('touchstart', [touch1, touch2]);
            
            mobileTouchManager.determineGesture(event);
            
            expect(mobileTouchManager.currentGesture).toBe('zoom');
            expect(mobileTouchManager.gestureActive).toBe(true);
        });

        it('should recognize three finger rotation gesture', () => {
            const touch1 = createTouch(1, 100, 200);
            const touch2 = createTouch(2, 200, 300);
            const touch3 = createTouch(3, 150, 150);
            const event = createTouchEvent('touchstart', [touch1, touch2, touch3]);
            
            mobileTouchManager.determineGesture(event);
            
            expect(mobileTouchManager.currentGesture).toBe('rotate');
            expect(mobileTouchManager.gestureActive).toBe(true);
        });

        it('should setup pinch gesture for zoom', () => {
            const touch1 = createTouch(1, 100, 200);
            const touch2 = createTouch(2, 200, 300);
            const event = createTouchEvent('touchstart', [touch1, touch2]);
            
            mobileTouchManager.setupPinchGesture(event);
            
            expect(mobileTouchManager.initialPinchDistance).toBeGreaterThan(0);
            expect(mobileTouchManager.initialTouchCenter.x).toBe(150);
            expect(mobileTouchManager.initialTouchCenter.y).toBe(250);
        });
    });

    describe('Pan Gesture Handling', () => {
        it('should handle center pan gesture', () => {
            const applyCameraPanSpy = vi.spyOn(mobileTouchManager, 'applyCameraPan');
            
            // Touch in center (should trigger pan)
            const touch = createTouch(1, 300, 200); // Center of 600x400 container
            const event = createTouchEvent('touchmove', [touch]);
            
            mobileTouchManager.touches.set(1, {
                id: 1,
                startX: 250,
                startY: 150,
                currentX: 300,
                currentY: 200
            });
            
            mobileTouchManager.handlePanGesture(event);
            
            expect(applyCameraPanSpy).toHaveBeenCalled();
        });

        it('should handle edge rotation gesture', () => {
            const applyCameraRotationSpy = vi.spyOn(mobileTouchManager, 'applyCameraRotation');
            
            // Touch near edge (should trigger rotation)
            const touch = createTouch(1, 550, 50); // Near edge of 600x400 container
            const event = createTouchEvent('touchmove', [touch]);
            
            mobileTouchManager.touches.set(1, {
                id: 1,
                startX: 500,
                startY: 0,
                currentX: 550,
                currentY: 50
            });
            
            mobileTouchManager.handlePanGesture(event);
            
            expect(applyCameraRotationSpy).toHaveBeenCalled();
        });

        it('should ignore pan gesture with wrong touch count', () => {
            const applyCameraPanSpy = vi.spyOn(mobileTouchManager, 'applyCameraPan');
            
            const touch1 = createTouch(1, 100, 200);
            const touch2 = createTouch(2, 200, 300);
            const event = createTouchEvent('touchmove', [touch1, touch2]);
            
            mobileTouchManager.handlePanGesture(event);
            
            expect(applyCameraPanSpy).not.toHaveBeenCalled();
        });
    });

    describe('Zoom Gesture Handling', () => {
        it('should handle zoom gesture correctly', () => {
            const applyCameraZoomSpy = vi.spyOn(mobileTouchManager, 'applyCameraZoom');
            const hapticFeedbackSpy = vi.spyOn(mobileTouchManager, 'hapticFeedback');
            
            const touch1 = createTouch(1, 100, 200);
            const touch2 = createTouch(2, 200, 300);
            const event = createTouchEvent('touchmove', [touch1, touch2]);
            
            mobileTouchManager.initialPinchDistance = 100;
            
            mobileTouchManager.handleZoomGesture(event);
            
            expect(applyCameraZoomSpy).toHaveBeenCalled();
            expect(hapticFeedbackSpy).toHaveBeenCalledWith('medium');
        });

        it('should ignore zoom gesture with wrong touch count', () => {
            const applyCameraZoomSpy = vi.spyOn(mobileTouchManager, 'applyCameraZoom');
            
            const touch = createTouch(1, 100, 200);
            const event = createTouchEvent('touchmove', [touch]);
            
            mobileTouchManager.handleZoomGesture(event);
            
            expect(applyCameraZoomSpy).not.toHaveBeenCalled();
        });
    });

    describe('Rotation Gesture Handling', () => {
        it('should handle rotation gesture with multiple touches', () => {
            const applyCameraRotationSpy = vi.spyOn(mobileTouchManager, 'applyCameraRotation');
            
            const touch1 = createTouch(1, 100, 200);
            const touch2 = createTouch(2, 200, 300);
            const event = createTouchEvent('touchmove', [touch1, touch2]);
            
            mobileTouchManager.touches.set(1, { id: 1, startX: 80, startY: 180 });
            mobileTouchManager.touches.set(2, { id: 2, startX: 180, startY: 280 });
            
            mobileTouchManager.handleRotateGesture(event);
            
            expect(applyCameraRotationSpy).toHaveBeenCalled();
        });

        it('should ignore rotation gesture with insufficient touches', () => {
            const applyCameraRotationSpy = vi.spyOn(mobileTouchManager, 'applyCameraRotation');
            
            const touch = createTouch(1, 100, 200);
            const event = createTouchEvent('touchmove', [touch]);
            
            mobileTouchManager.handleRotateGesture(event);
            
            expect(applyCameraRotationSpy).not.toHaveBeenCalled();
        });
    });

    describe('Tap Handling', () => {
        it('should handle single tap', () => {
            const hapticFeedbackSpy = vi.spyOn(mobileTouchManager, 'hapticFeedback');
            const touch = createTouch(1, 100, 200);
            const now = Date.now();
            
            mobileTouchManager.lastTap = now - 1000; // Long time ago
            
            mobileTouchManager.handleTap(touch, now);
            
            expect(hapticFeedbackSpy).toHaveBeenCalledWith('light');
            expect(mobileTouchManager.lastTap).toBe(now);
        });

        it('should handle double tap and reset camera', () => {
            const resetCameraSpy = vi.spyOn(mobileTouchManager, 'resetCamera');
            const hapticFeedbackSpy = vi.spyOn(mobileTouchManager, 'hapticFeedback');
            const touch = createTouch(1, 100, 200);
            const now = Date.now();
            
            mobileTouchManager.lastTap = now - 200; // Within double tap threshold
            
            mobileTouchManager.handleTap(touch, now);
            
            expect(resetCameraSpy).toHaveBeenCalled();
            expect(hapticFeedbackSpy).toHaveBeenCalledWith('strong');
        });
    });

    describe('Long Press Handling', () => {
        it('should trigger long press action', () => {
            const showMobileMenuSpy = vi.spyOn(mobileTouchManager, 'showMobileMenu');
            const hapticFeedbackSpy = vi.spyOn(mobileTouchManager, 'hapticFeedback');
            const touch = createTouch(1, 100, 200);
            
            mobileTouchManager.triggerLongPress(touch);
            
            expect(showMobileMenuSpy).toHaveBeenCalledWith(touch);
            expect(hapticFeedbackSpy).toHaveBeenCalledWith('strong');
        });

        it('should clear long press timer on touch move', () => {
            const touch = createTouch(1, 100, 200);
            const startEvent = createTouchEvent('touchstart', [touch]);
            const moveEvent = createTouchEvent('touchmove', [touch]);
            
            mobileTouchManager.handleTouchStart(startEvent);
            expect(mobileTouchManager.longPressTimer).not.toBeNull();
            
            mobileTouchManager.handleTouchMove(moveEvent);
            expect(mobileTouchManager.longPressTimer).toBeNull();
        });
    });

    describe('Camera Operations', () => {
        it('should apply camera rotation', () => {
            mobileTouchManager.applyCameraRotation(0.1, 0.2);
            
            expect(controls.object.lookAt).toHaveBeenCalledWith(controls.target);
            expect(controls.update).toHaveBeenCalled();
        });

        it('should apply camera pan', () => {
            mobileTouchManager.applyCameraPan(10, 20);
            
            expect(controls.object.position.add).toHaveBeenCalled();
            expect(controls.target.add).toHaveBeenCalled();
            expect(controls.update).toHaveBeenCalled();
        });

        it('should apply camera zoom', () => {
            mobileTouchManager.applyCameraZoom(1.5);
            
            expect(controls.object.position.copy).toHaveBeenCalled();
            expect(controls.update).toHaveBeenCalled();
        });

        it('should reset camera to default position', () => {
            mobileTouchManager.resetCamera();
            
            expect(controls.object.position.set).toHaveBeenCalledWith(10, 10, 10);
            expect(controls.target.set).toHaveBeenCalledWith(0, 0, 0);
            expect(controls.object.lookAt).toHaveBeenCalledWith(controls.target);
            expect(controls.update).toHaveBeenCalled();
        });

        it('should handle camera operations when controls are null', () => {
            mobileTouchManager.controls = null;
            
            expect(() => {
                mobileTouchManager.applyCameraRotation(0.1, 0.2);
                mobileTouchManager.applyCameraPan(10, 20);
                mobileTouchManager.applyCameraZoom(1.5);
                mobileTouchManager.resetCamera();
            }).not.toThrow();
        });
    });

    describe('Distance and Center Calculations', () => {
        it('should calculate distance between two touches correctly', () => {
            const touch1 = createTouch(1, 0, 0);
            const touch2 = createTouch(2, 3, 4);
            
            const distance = mobileTouchManager.getDistance(touch1, touch2);
            
            expect(distance).toBe(5); // 3-4-5 triangle
        });

        it('should calculate center point between two touches', () => {
            const touch1 = createTouch(1, 100, 200);
            const touch2 = createTouch(2, 300, 400);
            
            const center = mobileTouchManager.getCenter(touch1, touch2);
            
            expect(center.x).toBe(200);
            expect(center.y).toBe(300);
        });
    });

    describe('Haptic Feedback', () => {
        it('should provide light haptic feedback', () => {
            mobileTouchManager.hapticFeedback('light');
            
            expect(navigator.vibrate).toHaveBeenCalledWith([10]);
        });

        it('should provide medium haptic feedback', () => {
            mobileTouchManager.hapticFeedback('medium');
            
            expect(navigator.vibrate).toHaveBeenCalledWith([20]);
        });

        it('should provide strong haptic feedback', () => {
            mobileTouchManager.hapticFeedback('strong');
            
            expect(navigator.vibrate).toHaveBeenCalledWith([50]);
        });

        it('should handle haptic feedback when not supported', () => {
            mobileTouchManager.hapticEnabled = false;
            
            expect(() => {
                mobileTouchManager.hapticFeedback('light');
            }).not.toThrow();
        });
    });

    describe('Mobile UI Creation', () => {
        it('should create mobile UI hints for mobile devices', () => {
            mobileTouchManager.createMobileUI();
            
            expect(document.createElement).toHaveBeenCalledWith('div');
            expect(container.appendChild).toHaveBeenCalled();
        });

        it('should show mobile context menu on long press', () => {
            const touch = createTouch(1, 100, 200);
            
            mobileTouchManager.showMobileMenu(touch);
            
            expect(document.createElement).toHaveBeenCalledWith('div');
            expect(document.body.appendChild).toHaveBeenCalled();
        });
    });

    describe('Safari Gesture Events', () => {
        it('should handle gesture start', () => {
            const event = { preventDefault: vi.fn() };
            
            mobileTouchManager.handleGestureStart(event);
            
            expect(event.preventDefault).toHaveBeenCalled();
        });

        it('should handle gesture change with zoom', () => {
            const applyCameraZoomSpy = vi.spyOn(mobileTouchManager, 'applyCameraZoom');
            const event = { preventDefault: vi.fn(), scale: 1.5 };
            
            mobileTouchManager.handleGestureChange(event);
            
            expect(event.preventDefault).toHaveBeenCalled();
            expect(applyCameraZoomSpy).toHaveBeenCalledWith(1.5);
        });

        it('should handle gesture end', () => {
            const event = { preventDefault: vi.fn() };
            
            mobileTouchManager.handleGestureEnd(event);
            
            expect(event.preventDefault).toHaveBeenCalled();
        });
    });

    describe('Mobile Info and Controls', () => {
        it('should return comprehensive mobile info', () => {
            const info = mobileTouchManager.getMobileInfo();
            
            expect(info).toHaveProperty('isMobile');
            expect(info).toHaveProperty('isTablet');
            expect(info).toHaveProperty('hasTouch');
            expect(info).toHaveProperty('hapticEnabled');
            expect(info).toHaveProperty('currentGesture');
            expect(info).toHaveProperty('activeTouches');
            expect(info).toHaveProperty('sensitivity');
            expect(typeof info.activeTouches).toBe('number');
        });

        it('should set controls correctly', () => {
            const newControls = { test: 'controls' };
            
            mobileTouchManager.setControls(newControls);
            
            expect(mobileTouchManager.controls).toBe(newControls);
        });
    });

    describe('Performance Throttling', () => {
        it('should throttle touch move events for performance', () => {
            const touch = createTouch(1, 100, 200);
            const event = createTouchEvent('touchmove', [touch]);
            
            mobileTouchManager.lastFrameTime = Date.now();
            
            // This should be throttled and not process
            mobileTouchManager.handleTouchMove(event);
            
            expect(event.preventDefault).toHaveBeenCalled();
            // Touch positions should not be updated due to throttling
        });

        it('should process touch move when enough time has passed', () => {
            const touch = createTouch(1, 100, 200);
            const event = createTouchEvent('touchmove', [touch]);
            
            mobileTouchManager.touches.set(1, {
                id: 1,
                startX: 80,
                startY: 180,
                currentX: 80,
                currentY: 180
            });
            
            mobileTouchManager.lastFrameTime = Date.now() - 50; // Old timestamp
            
            mobileTouchManager.handleTouchMove(event);
            
            // Touch positions should be updated
            expect(mobileTouchManager.touches.get(1).currentX).toBe(100);
            expect(mobileTouchManager.touches.get(1).currentY).toBe(200);
        });
    });

    describe('Cleanup and Disposal', () => {
        it('should dispose properly', () => {
            mobileTouchManager.longPressTimer = setTimeout(() => {}, 1000);
            
            mobileTouchManager.dispose();
            
            expect(mobileTouchManager.enabled).toBe(false);
            expect(mobileTouchManager.longPressTimer).toBeNull();
            expect(mobileTouchManager.touches.size).toBe(0);
        });

        it('should handle disposal when no timer exists', () => {
            mobileTouchManager.longPressTimer = null;
            
            expect(() => {
                mobileTouchManager.dispose();
            }).not.toThrow();
        });
    });
});