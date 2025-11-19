# Advanced 3-Phase Wound Rotor Induction Motor Laboratory

## Multi-Physics Simulation with Electromagnetic-Thermal-Mechanical Coupling

A comprehensive Python + Tkinter application for analyzing and simulating 3-phase wound rotor induction motors with advanced multi-physics modeling.

## Features

### 1. **Comprehensive GUI (Tkinter)**
- Main menu with tabbed interface
- Interactive parameter adjustment with real-time sliders
- Control buttons: Start, Stop, Reset
- Auto-scaling window with responsive layout

### 2. **Mathematical Modeling**
- **Circuit Model**: Complete equivalent circuit analysis using RMS values
- **Torque-Slip Characteristics**: Accurate electromagnetic torque calculation
- **Maximum Torque Analysis**: Analytical calculation of pull-out torque
- **Dynamic Simulation**: Real-time ODE solvers (RK45 and Euler methods)

### 3. **Multi-Physics Simulation**
- **Electromagnetic**: 3-phase circuit equations with mutual inductances
- **Thermal**: Coupled heat transfer equations for stator and rotor
- **Mechanical**: Shaft stress analysis and bearing load calculations
- **Loss Breakdown**:
  - Copper losses (stator and rotor)
  - Iron losses (hysteresis and eddy currents)
  - Mechanical friction and windage losses
  - Stray load losses

### 4. **Advanced Control Systems**
- Multiple load profiles (step, constant, ramp, sinusoidal)
- Real-time parameter adjustment
- Solver selection (RK45 adaptive or Euler fixed-step)
- Configurable simulation duration and time steps

### 5. **Visualization Tabs**

#### Tab 1: Dynamic Simulation
- Real-time plots of:
  - Rotor speed vs time
  - Electromagnetic torque vs time
  - Stator current vs time
  - Input/output power vs time
  - Temperature rise vs time
  - Efficiency vs time

#### Tab 2: Steady-State Characteristics
- Torque-speed curve
- Current-speed curve
- Power-speed curve
- Efficiency-speed curve

#### Tab 3: Thermal Analysis
- Temperature distribution across components
- Temperature rise over time
- Derating curves
- Hotspot analysis
- Safe operating zone visualization

#### Tab 4: Loss Analysis
- Loss pie chart (distribution)
- Loss bar chart (detailed breakdown)
- Losses over time
- Shaft torsional stress analysis

#### Tab 5: Economic Analysis
- Life cycle cost calculation
- Energy consumption analysis
- Operating cost breakdown
- Carbon footprint estimation
- Efficiency improvement potential

#### Tab 6: Results & Reports
- Comprehensive text reports
- Data export to CSV
- Problem solution display

## Problem Solution

The application solves the following specific problem:

**Given:**
- 6 pole, 50 Hz, 3-φ wound rotor Induction Motor
- Moment of inertia: 1000 kg-m²
- Load torque: 1000 N-m for 10 seconds, then no load
- Slip = 5% at torque = 500 N-m

**Find:**
- (a) Maximum torque developed by motor
- (b) Speed at the end of deceleration period

**Solution is automatically calculated and displayed in the Results tab.**

## Installation

### Prerequisites
- Python 3.7 or higher
- tkinter (usually comes with Python)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install numpy scipy matplotlib
```

### For Ubuntu/Debian (if tkinter is not installed):
```bash
sudo apt-get install python3-tk
```

### For macOS:
```bash
brew install python-tk
```

## Usage

### Run the Application

```bash
python3 induction_motor_lab.py
```

Or make it executable:
```bash
chmod +x induction_motor_lab.py
./induction_motor_lab.py
```

### Using the GUI

1. **Adjust Parameters**: Use sliders in the left panel to modify motor parameters
2. **Select Solver**: Choose between RK45 (adaptive) or Euler (fixed-step)
3. **Configure Load**: Select load profile type and amplitude
4. **Start Simulation**: Click "▶ Start" to run the simulation
5. **View Results**: Navigate through tabs to see different analyses
6. **Export Data**: Use "Export Data" button to save results to CSV

## Technical Details

### Mathematical Models

#### Equivalent Circuit
The motor is modeled using the per-phase equivalent circuit with:
- Stator resistance (R₁)
- Rotor resistance (R₂)
- Stator leakage inductance (L₁)
- Rotor leakage inductance (L₂)
- Magnetizing inductance (Lₘ)

#### Electromagnetic Torque
```
T = (3/ωₛ) × (I₂² × R₂/s)
```

#### Mechanical Dynamics
```
J × dω/dt = Tₑₘ - Tₗₒₐd - B×ω
```

#### Thermal Dynamics
```
C × dT/dt = Pₗₒₛₛ - (T - Tₐₘb)/Rₜₕ
```

### ODE Solvers

#### RK45 (Runge-Kutta 4th/5th order)
- Adaptive step size
- Higher accuracy
- Recommended for most simulations

#### Euler Method
- Fixed step size
- Faster but less accurate
- Good for quick analyses

## Data Export

Simulation data is exported in CSV format with the following columns:
- Time (s)
- Speed (RPM)
- Torque (N-m)
- Current (A, RMS)
- Power Input (W)
- Power Output (W)
- Efficiency (%)
- Stator Temperature (°C)
- Rotor Temperature (°C)
- Total Losses (W)
- Slip
- Shaft Stress (MPa)

## Practical Applications

This laboratory tool is designed for:
- **Education**: Teaching induction motor theory and operation
- **Design**: Motor parameter optimization
- **Analysis**: Performance prediction and validation
- **Research**: Multi-physics coupling studies
- **Industry**: Motor selection and sizing

## Key Features for Electrical Engineering Practice

1. **Realistic Modeling**: Uses industry-standard equivalent circuit
2. **RMS Values**: All voltages and currents in RMS for practical use
3. **Thermal Limits**: Includes insulation class temperature limits
4. **Derating**: Automatic derating calculations
5. **Economics**: Life cycle cost and energy analysis
6. **Safety**: Shaft stress and safe operating zone indicators

## Example Use Cases

### Case 1: Motor Starting Analysis
- Set high moment of inertia
- Use step load profile
- Observe starting current and acceleration time

### Case 2: Thermal Performance
- Run extended simulation (60+ seconds)
- Monitor temperature rise
- Check against rated limits

### Case 3: Efficiency Optimization
- Vary motor parameters
- Compare steady-state efficiency curves
- Find optimal operating point

### Case 4: Economic Analysis
- Input local electricity costs
- Calculate life cycle costs
- Compare different motor options

## Limitations and Assumptions

1. Linear magnetic circuit (no saturation)
2. Sinusoidal supply voltage
3. Balanced 3-phase operation
4. Symmetric motor construction
5. Simplified thermal model (lumped parameters)

## License

This code is provided for educational and research purposes.

## Author

Created by Claude for Advanced Electrical Engineering Laboratory

## Version

1.0.0 - Initial release with full multi-physics simulation

---

**Note**: For best results, ensure all Python dependencies are properly installed and use a system with GUI support for the Tkinter interface.
