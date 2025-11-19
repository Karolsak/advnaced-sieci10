# Advanced Synchronous Generator Simulation Lab

## Example 7.3 - Salient-Pole Synchronous Generator Analysis

This comprehensive Python application solves Example 7.3 and provides an advanced simulation laboratory for analyzing salient-pole synchronous generators with multi-physics modeling.

## Problem Statement (Example 7.3)

A salient-pole synchronous generator with the following specifications:
- **Apparent power**: Sn = 50 kVA
- **Line voltage**: V1Ln = 380 V
- **Frequency**: fn = 60 Hz
- **Speed**: nn = 1800 rpm
- **Power factor**: cos φn = 0.82

### Laboratory Test Results:
1. **Slip test** (for measuring Xsd and Xsq):
   - Test voltage: Vs = 115 V at 1768 rpm, 60 Hz
   - Maximum current: Imax = 22.2 A
   - Minimum current: Imin = 11.3 A

2. **Field winding** (copper wire):
   - Resistance: Rf = 0.8 Ω at 20°C
   - No-load field current: If0 = 10.5 A

### Required Calculations:
- **(a)** Synchronous reactances Xsd and Xsq
- **(b)** Nominal field excitation current Ifn
- **(c)** Field voltage at 120°C operating temperature

## Solution Summary

### (a) Synchronous Reactances
From the slip test method:
- **Xsd = Vs / Imin = 115 / 11.3 = 10.177 Ω** (d-axis reactance)
- **Xsq = Vs / Imax = 115 / 22.2 = 5.180 Ω** (q-axis reactance)

### (b) Nominal Field Current
Using the voltage equation and linear magnetization:
- Phase voltage: V1n = 380/√3 = 219.4 V
- Nominal current: In = 50000/(√3 × 380) = 76.0 A
- Power angle: φn = arccos(0.82) = 34.9°
- **Ifn ≈ 13.2 A** (calculated from excitation voltage)

### (c) Field Voltage at 120°C
Accounting for copper temperature coefficient (α = 0.00393):
- Rf(120°C) = 0.8 × [1 + 0.00393 × (120 - 20)] = 1.115 Ω
- **Vfn = Ifn × Rf(120°C) ≈ 14.7 V**

## Installation

### Prerequisites
- Python 3.7 or higher
- tkinter (usually included with Python)

### Install Dependencies
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install numpy matplotlib scipy
```

## Running the Application

### ⚠️ IMPORTANT: Jupyter Notebook Users
If you're running from **Jupyter Notebook**, you MUST restart the kernel after any code changes:
1. Click: `Kernel` → `Restart Kernel`
2. Re-run your cells

Otherwise, Jupyter will use cached (old) versions of the code!

### Method 1: Standalone Launcher (Recommended)
```bash
python3 run_gui.py
```

### Method 2: Direct Execution
```bash
python3 synchronous_generator_lab.py
```

### Method 3: Calculations Only (No GUI Required)
```bash
python3 generator_core.py
```

### Method 4: Run Tests
```bash
python3 test_generator.py
```

## Features

### 1. **Example 7.3 Solution Tab**
- Complete step-by-step solution with explanations
- All intermediate calculations shown
- Professional formatting of results

### 2. **Multi-Physics Simulation**
- **Electromagnetic Model**:
  - d-q axis dynamic equations
  - Park transformation
  - Phasor diagrams

- **Thermal Model**:
  - Lumped parameter thermal network
  - Temperature distribution (stator, rotor)
  - Thermal derating calculations
  - Class F insulation limits (155°C)

- **Mechanical Model**:
  - Shaft stress analysis
  - Bearing load calculations
  - Safety factor evaluation
  - Torque transient analysis

### 3. **Dynamic Simulation**
- **ODE Solvers**:
  - RK45 (Runge-Kutta 4/5) - High accuracy
  - Euler - Simple and fast
- Real-time waveform visualization
- Transient response analysis
- Load angle dynamics

### 4. **Loss Analysis**
- **Detailed Loss Breakdown**:
  - Stator copper losses (I²R)
  - Rotor copper losses
  - Iron losses (hysteresis + eddy current)
  - Mechanical friction losses
  - Windage losses
  - Stray load losses
- Visual pie chart representation
- Efficiency calculation

### 5. **Economic Analysis**
- Annual energy loss costs
- Maintenance cost estimation
- Lifecycle cost analysis (NPV)
- Cost-benefit analysis
- Customizable energy rates

### 6. **Interactive Controls**
- **Real-time Sliders**:
  - Load torque adjustment (0-150%)
  - Field current control (50-150%)
  - Speed variation (80-120%)
  - Ambient temperature (0-50°C)
- Start/Stop/Reset simulation controls
- Parameter modification interface

### 7. **Advanced Features**
- Auto-scaling GUI (responsive to window resizing)
- Multiple visualization tabs
- Scrollable parameter inputs
- Professional engineering output formatting
- Thread-based real-time simulation

## Application Structure

```
synchronous_generator_lab.py
├── GeneratorParameters (dataclass)
│   └── All machine parameters and test data
├── SynchronousGeneratorModel
│   ├── calculate_parameters() - Example 7.3 solution
│   ├── electromagnetic_equations() - Dynamic model
│   ├── calculate_losses() - Loss breakdown
│   ├── thermal_model() - Temperature analysis
│   └── mechanical_stress_analysis() - Stress/bearing loads
├── EconomicAnalysis
│   └── calculate_economics() - Cost analysis
└── AdvancedGeneratorGUI
    ├── 7 Tabbed interfaces
    ├── Control panel with sliders
    ├── Real-time plotting
    └── Auto-scaling layout
```

## GUI Tabs Description

1. **Parameters**: Input and modify all generator parameters
2. **Results - Ex 7.3**: Complete solution with detailed calculations
3. **Dynamic Simulation**: Real-time ODE solver visualization
4. **Loss Analysis**: Detailed loss breakdown with pie chart
5. **Thermal & Derating**: Temperature distribution and limits
6. **Mechanical Analysis**: Stress, torque, and bearing loads
7. **Economic Analysis**: Cost calculations and efficiency

## Technical Details

### Electromagnetic Modeling
The application uses Park's transformation to convert three-phase quantities to d-q reference frame:

```
vd = -V·sin(δ)
vq = V·cos(δ)

did/dt = (vd - Ra·id + ω·Lq·iq) / Ld
diq/dt = (vq - Ra·iq - ω·Ld·id - ω·ψf) / Lq
```

### Thermal Modeling
Lumped parameter thermal network:
```
T_stator = T_ambient + P_loss × R_thermal
Derating = (T_max - T_stator) / T_max
```

### Loss Calculations
- **Copper losses**: P_cu = 3·I²·R (stator), If²·Rf (rotor)
- **Iron losses**: Steinmetz equation: P_fe = k_h·f·B² + k_e·(f·B)²
- **Mechanical**: Friction and windage (empirical)

## Usage Examples

### Running a Quick Analysis
1. Launch the application
2. Click "Calculate" button
3. View results in "Results - Ex 7.3" tab
4. Explore other tabs for detailed analysis

### Dynamic Simulation
1. Go to "Dynamic Simulation" tab
2. Select solver (RK45 recommended)
3. Click "Run Simulation"
4. Observe current, load angle, and speed transients

### Adjusting Operating Conditions
1. Use sliders in Control Panel
2. Modify load torque, field current, speed, temperature
3. Click "Calculate" to update all analyses
4. Observe changes in losses, thermal, and economics

### Economic Analysis
1. Go to "Economic Analysis" tab
2. Enter operating hours per year
3. Set energy cost ($/kWh)
4. Click "Calculate Economics"
5. Review annual and lifecycle costs

## Educational Value

This application demonstrates:
- Electrical machine theory (synchronous generators)
- Multi-physics coupling (electromagnetic-thermal-mechanical)
- Numerical methods (ODE solvers, RK45, Euler)
- GUI development (Tkinter)
- Data visualization (Matplotlib)
- Engineering economics
- Professional software development

## Practical Applications

- **Power system design**: Generator sizing and specification
- **Efficiency optimization**: Loss minimization strategies
- **Thermal management**: Cooling system design
- **Economic evaluation**: Lifecycle cost analysis
- **Educational tool**: Teaching electrical machines
- **Research**: Parameter sensitivity studies

## Key Learning Outcomes

1. **Slip Test Method**: Understanding d-q axis reactance measurement
2. **Magnetization Curves**: Linear approximation and field current calculation
3. **Temperature Effects**: Resistance variation with temperature
4. **Loss Mechanisms**: Comprehensive understanding of efficiency
5. **Thermal Limits**: Derating and insulation classes
6. **Economic Analysis**: Total cost of ownership
7. **Dynamic Behavior**: Transient response and stability

## Troubleshooting

### ⚠️ Common Issues & Solutions

**See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive troubleshooting guide!**

#### Quick Fixes:

1. **AttributeError in Jupyter Notebook**
   - **Solution**: Restart kernel (`Kernel` → `Restart Kernel`)
   - Or run from terminal: `python3 run_gui.py`

2. **Import Errors**
   ```bash
   pip install --upgrade numpy matplotlib scipy
   ```

3. **GUI Not Displaying**
   - **Ubuntu/Debian**: `sudo apt-get install python3-tk`
   - **macOS**: Included with Python
   - **Windows**: Included with Python

4. **Slow Simulation**
   - Use Euler solver instead of RK45
   - Reduce simulation time or time steps

📖 **For detailed solutions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

## Advanced Customization

### Modifying Parameters
Edit the `GeneratorParameters` dataclass to change default values:
```python
@dataclass
class GeneratorParameters:
    Sn: float = 50e3  # Change to your generator rating
    V1Ln: float = 380  # Change to your voltage
    # ... etc
```

### Adding New Features
The modular design allows easy extension:
- Add new tabs in `setup_gui()`
- Implement new analysis methods in `SynchronousGeneratorModel`
- Create additional visualization functions

## References

1. P.C. Sen, "Principles of Electric Machines and Power Electronics"
2. S.J. Chapman, "Electric Machinery Fundamentals"
3. IEEE Standards for Synchronous Machines
4. IEC 60034 - Rotating Electrical Machines

## License

This educational software is provided as-is for learning purposes.

## Author

Created for advanced electrical engineering education and practical applications in power system design.

## Version

Version 1.0 - Complete implementation with all requested features

---

**Note**: This application combines theoretical calculations with practical simulation, making it ideal for both educational purposes and preliminary engineering design work.
