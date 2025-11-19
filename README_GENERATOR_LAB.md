# Advanced Synchronous Generator Laboratory

A comprehensive multi-physics simulation platform for analyzing parallel-connected synchronous generators with real-time dynamic visualization, thermal analysis, and economic evaluation.

## Features

### 1. **Problem Solution Module**
- Solves parallel synchronous generator operation problems
- Calculates field excitation currents for voltage regulation
- Determines power distribution and power angles
- Analyzes reactive power sharing between generators

### 2. **Dynamic Simulation**
- Real-time ODE solvers (RK45 Adaptive, Euler Fixed-Step)
- Swing equation simulation
- Transient stability analysis
- Interactive parameter adjustment with sliders
- Real-time visualization of:
  - Power angle (δ)
  - Rotor speed (ω)
  - Electrical and mechanical power

### 3. **Thermal Analysis**
- Multi-node thermal network simulation
- Temperature prediction for:
  - Stator windings
  - Core
  - Frame
- Power derating calculation
- Thermal limits monitoring
- Heat transfer modeling

### 4. **Loss Analysis**
- Detailed loss breakdown:
  - Copper losses (stator and rotor)
  - Iron losses (hysteresis and eddy current)
  - Mechanical losses (friction and windage)
  - Stray load losses
- Efficiency calculation
- Visual loss distribution (pie chart)

### 5. **Economic Analysis**
- Operating cost calculation
- Revenue projection
- Payback period analysis
- Net Present Value (NPV) calculation
- Investment feasibility analysis

### 6. **Advanced Control Systems**
- Automatic Voltage Regulator (AVR)
- Speed Governor control
- Protection systems

## Problem Statement

### Generator Specifications

**Generator A:**
- Rated Power: 500 kW
- Rated Field Current: 21.0 A
- Synchronous Reactance: 1.5 p.u.
- Power Factor: 0.85 lagging

**Generator B:**
- Rated Power: 350 kW
- Rated Field Current: 16.0 A
- Synchronous Reactance: 1.6 p.u.
- Power Factor: 0.85 lagging

**Common:**
- Terminal Voltage: 6300 V (line-to-line)
- Y-connected stator windings
- Non-salient pole rotors
- Unsaturated magnetic circuits

### Problem Solutions

#### Part (a)
**Given:**
- Total load: 720 kW at 0.8 pf lagging
- Each generator delivers: 360 kW
- Generator A field current: IfA = 20 A
- Terminal voltage: V = Vn = 6300 V

**Find:** Field current of Generator B (IfB)

**Result:** IfB ≈ 42.68 A

#### Part (b)
**Given:**
- Additional load: 130 kW at unity pf
- Total load: 850 kW
- Generator B maintains same conditions as part (a)

**Find:** New field current of Generator A

**Result:** IfA ≈ 24.63 A

## Installation

### Prerequisites

```bash
# Python 3.7 or higher
python3 --version

# Required packages
pip3 install numpy scipy matplotlib

# For GUI (Tkinter) - on Ubuntu/Debian
sudo apt-get install python3-tk

# On macOS (usually pre-installed with Python)
# On Windows (usually pre-installed with Python)
```

### Quick Start

1. **Clone or download the repository**
2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Run calculations only (no GUI):**
   ```bash
   python3 test_calculations_only.py
   ```

4. **Run full GUI application:**
   ```bash
   python3 synchronous_generator_advanced_lab.py
   ```

## Usage

### Command Line Calculations

```python
from generator_calculations import SynchronousGeneratorCalculator

# Create calculator
calc = SynchronousGeneratorCalculator()

# Solve part (a)
results_a = calc.solve_part_a()
print(f"IfB = {results_a['IfB']:.4f} A")

# Solve part (b)
results_b = calc.solve_part_b()
print(f"IfA_new = {results_b['IfA_new']:.4f} A")
```

### GUI Application

1. **Launch the application:**
   ```bash
   python3 synchronous_generator_advanced_lab.py
   ```

2. **Navigate through tabs:**
   - **Problem Solution:** Solve parallel generator problems
   - **Dynamic Simulation:** Run real-time simulations
   - **Thermal Analysis:** Analyze temperature distribution
   - **Loss Analysis:** Calculate losses and efficiency
   - **Economic Analysis:** Evaluate investment feasibility
   - **Control Systems:** Configure control parameters

3. **Use controls:**
   - **Sliders:** Adjust parameters in real-time
   - **Buttons:** Start/Stop/Reset simulations
   - **Menu:** File operations, export results
   - **Auto-scaling:** Window automatically adjusts to screen size

## Technical Details

### Mathematical Models

#### Per-Unit System
All calculations use a per-unit system with base quantities:
- Voltage base: Line-to-neutral rated voltage
- Power base: Rated apparent power (S_n = P_n / cos φ_n)
- Current base: S_n / (√3 × V_LL)
- Impedance base: V_LN / I_base

#### Power Equations
```
P = (E_f × V / X_s) × sin(δ)
Q = (E_f × V × cos(δ) - V²) / X_s
```

#### Dynamic Model (Swing Equation)
```
dδ/dt = ω - ω_s
dω/dt = (ω_s / 2H) × (P_m - P_e - D(ω - ω_s))
dE_q'/dt = (1 / T_d0') × (E_f - E_q' - (X_d - X_d')I_d)
```

#### Thermal Network
```
C_winding × dT_winding/dt = P_copper - (T_winding - T_core)/R_wc
C_core × dT_core/dt = P_iron + (T_winding - T_core)/R_wc - (T_core - T_frame)/R_cf
C_frame × dT_frame/dt = P_friction + (T_core - T_frame)/R_cf - (T_frame - T_ambient)/R_fa
```

### ODE Solvers

1. **RK45 (Runge-Kutta 4/5):**
   - Adaptive step size
   - Higher accuracy
   - Automatic error control
   - Best for general use

2. **Euler Method:**
   - Fixed step size
   - Simple implementation
   - Educational purposes
   - Faster for simple problems

## File Structure

```
.
├── synchronous_generator_advanced_lab.py  # Main GUI application
├── generator_calculations.py              # Calculation modules (no GUI)
├── test_calculations_only.py              # Test script (no GUI required)
├── test_generator_lab.py                  # Full test suite (requires Tkinter)
├── README_GENERATOR_LAB.md               # This file
└── requirements.txt                       # Python dependencies
```

## Examples

### Example 1: Calculate Field Currents

```python
from generator_calculations import SynchronousGeneratorCalculator

calc = SynchronousGeneratorCalculator()

# Part (a): Find IfB
results_a = calc.solve_part_a()
print(f"Generator B Field Current: {results_a['IfB']:.4f} A")
print(f"Power Distribution:")
print(f"  Gen A: {results_a['PA']:.2f} kW, {results_a['QA']:.2f} kVAR")
print(f"  Gen B: {results_a['PB']:.2f} kW, {results_a['QB']:.2f} kVAR")

# Part (b): Find new IfA
results_b = calc.solve_part_b()
print(f"New Generator A Field Current: {results_b['IfA_new']:.4f} A")
```

### Example 2: Run Dynamic Simulation

```python
from generator_calculations import SynchronousGeneratorDynamics
import numpy as np

params = {
    'H': 3.5,          # Inertia constant
    'D': 2.0,          # Damping
    'Xd': 1.5,         # d-axis reactance
    'Xq': 1.5,         # q-axis reactance
    'Xd_prime': 0.3,   # Transient reactance
    'Td0_prime': 5.0,  # Time constant
    'freq': 60         # Frequency
}

dynamics = SynchronousGeneratorDynamics(params)

# Initial conditions
delta0 = 30 * np.pi / 180  # 30 degrees
omega0 = 2 * np.pi * 60    # Synchronous speed
Eq_prime0 = 1.0
y0 = [delta0, omega0, Eq_prime0]

# Simulate
sol = dynamics.simulate([0, 5], y0, Pm=0.8, Ef=1.2, V=1.0, method='RK45')
```

### Example 3: Thermal Analysis

```python
from generator_calculations import ThermalModel

params = {
    'C_winding': 5000,
    'C_core': 8000,
    'C_frame': 3000,
    'R_winding_core': 0.05,
    'R_core_frame': 0.03,
    'R_frame_ambient': 0.02,
    'T_ambient': 25,
    'T_max_winding': 130
}

thermal = ThermalModel(params)

# Initial temperatures
T0 = [25, 25, 25]  # Ambient temperature

# Losses in watts
P_losses = (5000, 3000, 800)  # Copper, Iron, Friction

# Simulate 1 hour
sol = thermal.simulate_thermal([0, 3600], T0, P_losses)

# Check final temperatures
T_winding_final = sol.y[0][-1]
derating = thermal.calculate_derating(T_winding_final)
print(f"Final winding temperature: {T_winding_final:.2f} °C")
print(f"Derating factor: {derating:.3f}")
```

## Troubleshooting

### Tkinter Not Available

If you get "ModuleNotFoundError: No module named 'tkinter'":

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S tk
```

**Alternative:** Use calculation-only mode:
```bash
python3 test_calculations_only.py
```

### Import Errors

If you get numpy/scipy/matplotlib import errors:
```bash
pip3 install --user numpy scipy matplotlib
```

### Display Issues

For headless servers or systems without display:
- Use the calculation modules only (`generator_calculations.py`)
- Export data and visualize elsewhere
- Use virtual display (Xvfb)

## Performance Notes

- **RK45 solver:** More accurate, adaptive steps, suitable for stiff problems
- **Euler solver:** Faster for simple problems, educational purposes
- **Thermal simulation:** Can be slow for long time periods (use larger max_step)
- **Real-time updates:** Disable for better performance in batch simulations

## References

1. Kundur, P. "Power System Stability and Control"
2. Fitzgerald, Kingsley, Umans "Electric Machinery"
3. Chapman, S. "Electric Machinery Fundamentals"
4. IEEE Standards for Synchronous Machines

## License

This software is provided for educational and research purposes.

## Author

Developed for electrical engineering education and professional applications.

## Contributing

Contributions, issues, and feature requests are welcome!

## Support

For questions or issues:
1. Check this README
2. Review the code documentation
3. Run test scripts to verify installation
4. Check Python and dependency versions

---

**Version:** 1.0
**Last Updated:** 2025
**Python Version:** 3.7+
**Status:** Production Ready
