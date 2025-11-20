# Interior PM Synchronous Motor Analysis

## Overview
Complete Python implementation for analyzing a three-phase interior permanent magnet (PM) synchronous motor with interactive visualization and performance calculations.

## Motor Specifications

- **Type**: Interior PM synchronous motor, Y-connected
- **Power**: 1.5 kW (rated)
- **Voltage**: 380 V (line-to-line)
- **Frequency**: 50 Hz
- **Poles**: 4
- **Synchronous Speed**: 1500 rpm
- **Stator Resistance**: R₁ = 4.98 Ω
- **d-axis Reactance**: Xsd = 18.5 Ω
- **q-axis Reactance**: Xsq = 40.5 Ω (Note: Xsd < Xsq for interior PM motors)
- **Winding Turns**: N₁ = 240 per phase
- **Winding Factor**: kw₁ = 0.96
- **Core Length**: Li = 0.103 m
- **Inner Diameter**: D = 0.0825 m
- **Air Gap Flux Density**: Bmg = 0.685 T
- **Rotational Losses**: Prot = 40 W
- **Stray Losses**: Pstr = 0.05 × Pout

## Results at δ = 45°

### Key Performance Metrics
- **Armature Current (I_a)**: 5.24 A
- **Electromagnetic Torque (T_elm)**: 21.73 Nm
- **Output Power (P_out)**: 3212.5 W (3.21 kW)
- **Efficiency (η)**: 84.01%
- **Power Factor (cos φ)**: 0.989 (leading)

### Detailed Results
- **Phase Voltage**: 219.39 V
- **Induced EMF**: 233.83 V
- **d-axis Current**: 3.12 A
- **q-axis Current**: 4.21 A
- **Electromagnetic Power**: 3413.1 W
- **Input Power**: 3823.8 W

### Loss Breakdown
- **Copper Losses**: 410.7 W (10.7%)
- **Rotational Losses**: 40.0 W (1.0%)
- **Stray Losses**: 160.6 W (4.2%)
- **Total Losses**: 611.3 W (16.0%)

## Files

### 1. `interior_pm_motor_analysis.py`
**Interactive version with sliders** - Full GUI with real-time parameter adjustment

**Features:**
- Interactive sliders for all key parameters:
  - Power angle δ (0° - 90°)
  - Line voltage (200V - 500V)
  - Air gap flux density (0.3T - 1.2T)
  - Stator resistance (1Ω - 10Ω)
  - d-axis reactance (5Ω - 40Ω)
  - q-axis reactance (10Ω - 80Ω)
- Real-time plot updates
- Comprehensive visualization with 7 subplots

**Usage:**
```bash
python3 interior_pm_motor_analysis.py
```

### 2. `interior_pm_motor_analysis_static.py`
**Static version** - Generates high-resolution plots saved to file

**Usage:**
```bash
python3 interior_pm_motor_analysis_static.py
```

**Output:** `interior_pm_motor_analysis.png` (300 DPI)

## Visualization Components

The analysis includes 7 comprehensive visualizations:

1. **Phasor Diagram** (Synchronous Frame)
   - Voltage phasor (V_ph)
   - Current phasor (I_a)
   - EMF phasor (E_f)
   - d-q axis reference frame
   - Power angle δ and power factor angle φ

2. **d-q Axis Components**
   - Bar chart showing I_d, I_q, V_d, V_q
   - Current and voltage decomposition

3. **Power Distribution** (Pie Chart)
   - Output power (84%)
   - Copper losses (10.7%)
   - Rotational losses (1.0%)
   - Stray losses (4.2%)

4. **Torque vs Power Angle**
   - Electromagnetic torque characteristic
   - Operating point marker
   - δ range: 0° to 90°

5. **Efficiency vs Load**
   - Efficiency curve across load range
   - Operating point indication
   - Peak efficiency identification

6. **Armature Current Components**
   - Vector diagram of I_d and I_q
   - Resultant current I_a
   - Current magnitude circle

7. **Power Flow Diagram**
   - Sankey-style flow from input to output
   - Loss visualization at each stage
   - Overall efficiency display

## Technical Details

### d-q Axis Voltage Equations
For motor operation with rotor d-axis as reference:

```
V_d = -R₁·I_d + X_sq·I_q
V_q = -R₁·I_q - X_sd·I_d + E_f
```

Where:
- V_d = V_ph·sin(δ)
- V_q = V_ph·cos(δ)
- δ = power angle (measured from q-axis to voltage phasor)

### Power and Torque Calculations

**Electromagnetic Power:**
```
P_elm = 3(V_d·I_d + V_q·I_q)
     = 3·E_f·I_q + 3(X_sd - X_sq)·I_d·I_q
```

**Electromagnetic Torque:**
```
T_elm = P_elm / ω_s
```

**Output Power:**
```
P_out = (P_elm - P_rot) / (1 + 0.05)
```

**Efficiency:**
```
η = P_out / P_in × 100%
```

Where P_in = P_elm + P_cu (copper losses)

## Requirements

```
numpy >= 1.21.0
matplotlib >= 3.4.0
```

Install with:
```bash
pip3 install numpy matplotlib
```

## Key Features of Interior PM Motors

1. **Reluctance Torque Component**: Due to X_sd < X_sq, the motor produces both:
   - PM torque: proportional to I_q
   - Reluctance torque: proportional to I_d·I_q

2. **High Power Density**: Permanent magnets provide constant excitation

3. **High Efficiency**: No field winding losses

4. **Excellent Power Factor**: Can operate at near-unity power factor

5. **Field Weakening Capability**: Negative d-axis current enables high-speed operation

## Applications

- Electric vehicles (traction motors)
- Industrial drives
- Robotics
- Wind turbines
- Home appliances

## References

This implementation follows standard synchronous motor theory with d-q axis transformation in the synchronous reference frame aligned with the rotor.

## Author Notes

The code provides:
- Accurate modeling of interior PM motor behavior
- Educational visualization of motor operation
- Interactive parameter exploration
- Publication-quality plots
- Comprehensive performance metrics

All calculations use SI units and follow IEEE/IEC conventions for motor analysis.
