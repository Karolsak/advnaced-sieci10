# Troubleshooting Guide - Synchronous Generator Lab

## Issue 1: AttributeError - 'AdvancedGeneratorGUI' object has no attribute 'load_value_label'

### Symptom
```
AttributeError: 'AdvancedGeneratorGUI' object has no attribute 'load_value_label'
AttributeError: 'AdvancedGeneratorGUI' object has no attribute 'field_value_label'
...
```

### Cause
You are running the code from **Jupyter Notebook** which caches Python modules. Even though the code has been fixed, Jupyter is still using the old cached version.

### Solution

**Option 1: Restart Jupyter Kernel (Recommended)**
1. In Jupyter Notebook, click: `Kernel` → `Restart Kernel`
2. Re-run your cells
3. The updated code will now be loaded

**Option 2: Force Reload in Jupyter**
Add this at the top of your Jupyter cell:
```python
import sys
import importlib

# Remove cached module
if 'synchronous_generator_lab' in sys.modules:
    del sys.modules['synchronous_generator_lab']

# Now import
from synchronous_generator_lab import AdvancedGeneratorGUI
import tkinter as tk

# Create and run
root = tk.Tk()
app = AdvancedGeneratorGUI(root)
root.mainloop()
```

**Option 3: Run from Terminal (Best)**
Instead of Jupyter, run directly from terminal:
```bash
python3 run_gui.py
```
or
```bash
python3 synchronous_generator_lab.py
```

**Option 4: Use the Standalone Launcher**
```bash
python3 run_gui.py
```
This script automatically clears the cache before importing.

---

## Issue 2: 'GeneratorParameters' object has no attribute 'Rfn'

### Symptom
```
AttributeError: 'GeneratorParameters' object has no attribute 'Rfn'
```

### Cause
Fixed in latest version. The electromagnetic equations were referencing `self.params.Rfn` which doesn't exist.

### Solution
1. **Make sure you have the latest code** (already fixed)
2. **Restart Jupyter kernel** if running in Jupyter
3. **Or run from terminal**: `python3 run_gui.py`

---

## Issue 3: GUI Not Displaying / Tkinter Not Found

### Symptom
```
ModuleNotFoundError: No module named 'tkinter'
```

### Solution

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**macOS:**
Tkinter is included with Python. Reinstall Python if needed:
```bash
brew reinstall python
```

**Windows:**
Tkinter is included. If missing, reinstall Python from python.org and check "tcl/tk and IDLE".

---

## Issue 4: Import Errors - numpy, scipy, matplotlib

### Symptom
```
ModuleNotFoundError: No module named 'numpy'
ModuleNotFoundError: No module named 'scipy'
ModuleNotFoundError: No module named 'matplotlib'
```

### Solution
Install required packages:
```bash
pip install -r requirements.txt
```

Or individually:
```bash
pip install numpy scipy matplotlib
```

---

## Jupyter Notebook Best Practices

### Always Restart Kernel After Code Changes

When you modify `.py` files, Jupyter doesn't automatically reload them:

1. **Restart Kernel**: `Kernel` → `Restart Kernel`
2. **Clear Outputs**: `Cell` → `All Output` → `Clear`
3. **Run All**: `Cell` → `Run All`

### Auto-Reload Extension (Alternative)

Add this to the first cell of your notebook:
```python
%load_ext autoreload
%autoreload 2
```

This automatically reloads changed modules, but **it's not 100% reliable** for class definitions.

---

## Running the Application

### Method 1: Direct Python (Recommended)
```bash
cd /path/to/advnaced-sieci10
python3 synchronous_generator_lab.py
```

### Method 2: Standalone Launcher
```bash
python3 run_gui.py
```

### Method 3: Calculations Only (No GUI)
```bash
python3 generator_core.py
```

### Method 4: Run Tests
```bash
python3 test_generator.py
```

---

## Verification Commands

Check if fixes are applied:
```bash
# Check for defensive hasattr() checks
grep -n "hasattr" synchronous_generator_lab.py

# Check for Rfn bug (should NOT appear)
grep -n "\.Rfn" synchronous_generator_lab.py

# Verify Python syntax
python3 -m py_compile synchronous_generator_lab.py
echo "Syntax OK"
```

Expected output:
- `hasattr` should appear in lines 593, 598, 603, 608 (slider callbacks)
- `.Rfn` should NOT appear (fixed to use Rf_temp)
- Syntax check should show "Syntax OK"

---

## Still Having Issues?

1. **Make sure you're using the latest code**:
   ```bash
   git pull origin claude/synchronous-generator-example-01DaSJUb2wQBFn12GWCYogJW
   ```

2. **Check Python version**:
   ```bash
   python3 --version
   # Should be 3.7 or higher
   ```

3. **Verify dependencies**:
   ```bash
   python3 -c "import numpy; import scipy; import matplotlib; print('All dependencies OK')"
   ```

4. **Run without GUI** to test calculations:
   ```bash
   python3 generator_core.py
   ```

5. **Check file modifications**:
   ```bash
   ls -la *.py
   # Verify timestamps are recent
   ```

---

## Quick Fix Summary

### For Jupyter Users:
1. **Restart the kernel**: `Kernel` → `Restart Kernel`
2. Clear all outputs
3. Re-run all cells

### For Terminal Users:
```bash
python3 run_gui.py
```

### For Calculation Only (No GUI):
```bash
python3 generator_core.py
```

---

## Contact

If issues persist, check:
- Latest git commit has the fixes
- Python version >= 3.7
- All dependencies installed
- Not running from cached Jupyter kernel
