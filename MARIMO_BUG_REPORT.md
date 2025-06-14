# 🐛 Bug Report: Service Worker Registration Error - `registration.active is null`

## **Bug Summary**
Marimo 0.13.15 generates invalid Service Worker code that causes JavaScript errors in browser console, preventing proper widget functionality.

## **Error Details**
```
Error registering service worker: TypeError: registration.active is null
    <anonymous> http://127.0.0.1:2721/:72
127.0.0.1:2721:75:33
SyntaxError: return not in function
```

## **Root Cause**
Marimo generates Service Worker registration code that assumes `registration.active` is immediately available, but it's `null` during registration:

**Problematic Generated Code (Lines 70 & 77):**
```javascript
// Line 70 - Fails because registration.active is null
navigator.serviceWorker.register('./public-files-sw.js?v=2')
    .then(registration => {
        registration.active.postMessage({ notebookId }); // ❌ registration.active is null
    })

// Line 77 - Same issue
navigator.serviceWorker.ready
    .then(registration => {
        registration.update().then(() => registration.active.postMessage({ notebookId })); // ❌ registration.active is null
    })
```

## **Environment**
- **Marimo Version:** 0.13.15
- **Python Version:** 3.12.6
- **OS:** macOS 15.5 (also reproduced on other systems)
- **Browser:** Chrome, Firefox, Safari (all affected)
- **Installation:** `uv` package manager

## **Reproduction Steps**
1. Create any Marimo notebook with anywidget
2. Run: `uv run marimo run notebook.py --host 0.0.0.0 --port 2721`
3. Open browser and check F12 Developer Console
4. See the Service Worker registration errors

**Minimal Reproduction:**
```python
import marimo
import anywidget
import traitlets

__generated_with = "0.13.15"
app = marimo.App(width="medium")

@app.cell
def _():
    class TestWidget(anywidget.AnyWidget):
        _esm = """
        function render({ model, el }) {
            el.innerHTML = '<div>Test Widget</div>';
        }
        export default { render };
        """
    
    widget = TestWidget()
    widget
    return widget,

if __name__ == "__main__":
    app.run()
```

## **Expected Behavior**
Service Worker should register without errors and not prevent widget functionality.

## **Actual Behavior**
- Console shows `TypeError: registration.active is null`
- Subsequent `SyntaxError: return not in function` 
- Widgets may fail to render properly due to JavaScript execution being interrupted

## **Suggested Fix**
Check if `registration.active` exists before calling `postMessage`:

```javascript
navigator.serviceWorker.register('./public-files-sw.js?v=2')
    .then(registration => {
        if (registration.active) {
            registration.active.postMessage({ notebookId });
        } else {
            // Wait for service worker to become active
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'activated') {
                        newWorker.postMessage({ notebookId });
                    }
                });
            });
        }
    })
```

## **Impact**
- ❌ JavaScript errors in console for all Marimo notebooks
- ❌ Potential widget rendering issues 
- ❌ Poor developer experience with anywidget integration
- ❌ May affect production deployments

## **Workaround**
Currently no clean workaround available. The error comes from Marimo's generated HTML, not user code.

## **Additional Context**
This issue was discovered while developing a production-ready anywidget for OpenSCAD visualization. The Service Worker error appears regardless of the widget complexity and affects the overall JavaScript execution environment.

**Browser Console Screenshot:**
```
Error registering service worker: TypeError: registration.active is null
    <anonymous> http://127.0.0.1:2721/:72
127.0.0.1:2721:75:33
SyntaxError: return not in function
```

## **Files to Check**
The bug is in Marimo's Service Worker generation logic, likely in:
- Service Worker registration template
- HTML generation for notebook pages  
- Public files Service Worker handling

---

**Priority:** High (affects all anywidget users)  
**Labels:** bug, service-worker, anywidget, javascript-error