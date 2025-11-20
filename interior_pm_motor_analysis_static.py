"""
Three-phase Interior PM Synchronous Motor Analysis
Static version with saved plots (for non-GUI environments)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.patches as mpatches

# Motor parameters (default values)
class MotorParameters:
    def __init__(self):
        self.poles = 4
        self.f = 50  # Hz
        self.P_rated = 1500  # W
        self.V_LL = 380  # V line-to-line
        self.R1 = 4.98  # Ω
        self.Xsd = 18.5  # Ω (d-axis)
        self.Xsq = 40.5  # Ω (q-axis)
        self.N1 = 240  # turns per phase
        self.kw1 = 0.96  # winding factor
        self.Li = 0.103  # m
        self.D = 0.0825  # m
        self.delta = 45  # degrees (power angle)
        self.Bmg = 0.685  # T
        self.Prot = 40  # W
        self.Pstr_factor = 0.05  # Pstr = 0.05*Pout

def calculate_motor_performance(params):
    """
    Calculate motor performance parameters
    """
    # Basic calculations
    V_ph = params.V_LL / np.sqrt(3)  # Phase voltage (Y-connected)
    n_s = 120 * params.f / params.poles  # Synchronous speed (rpm)
    omega_s = 2 * np.pi * n_s / 60  # Synchronous speed (rad/s)

    # Flux per pole from permanent magnets
    Phi_pm = params.Bmg * (np.pi * params.D * params.Li) / params.poles

    # EMF induced by permanent magnets
    E_f = 4.44 * params.f * params.N1 * params.kw1 * Phi_pm

    # Convert power angle to radians
    delta_rad = np.radians(params.delta)

    # For motor operation with rotor d-axis as reference:
    # Power angle δ is measured from q-axis (EMF axis) to voltage phasor
    # In the synchronous reference frame aligned with rotor d-axis:
    V_d = V_ph * np.sin(delta_rad)
    V_q = V_ph * np.cos(delta_rad)

    # Standard motor voltage equations (current positive into motor):
    # V_d = -R1*I_d + X_sq*I_q
    # V_q = -R1*I_q - X_sd*I_d + E_f

    # Rearranging:
    # R1*I_d - X_sq*I_q = -V_d
    # X_sd*I_d + R1*I_q = E_f - V_q

    A = np.array([[params.R1, -params.Xsq],
                  [params.Xsd, params.R1]])
    b = np.array([-V_d, E_f - V_q])

    currents = np.linalg.solve(A, b)
    I_d = currents[0]
    I_q = currents[1]

    # Armature current magnitude
    I_a = np.sqrt(I_d**2 + I_q**2)

    # Current angle
    gamma = np.arctan2(I_q, I_d)

    # Power factor angle
    phi = delta_rad - gamma
    cos_phi = np.cos(phi)

    # Electromagnetic power
    P_elm = 3 * (V_d * I_d + V_q * I_q)

    # Electromagnetic torque
    T_elm = P_elm / omega_s

    # Output power
    P_out = (P_elm - params.Prot) / (1 + params.Pstr_factor)

    # Stray losses
    P_str = params.Pstr_factor * P_out

    # Copper losses
    P_cu = 3 * I_a**2 * params.R1

    # Input power
    P_in = P_elm + P_cu

    # Efficiency
    efficiency = (P_out / P_in) * 100 if P_in > 0 else 0

    # Output torque
    T_out = P_out / omega_s

    results = {
        'V_ph': V_ph,
        'n_s': n_s,
        'omega_s': omega_s,
        'Phi_pm': Phi_pm,
        'E_f': E_f,
        'I_d': I_d,
        'I_q': I_q,
        'I_a': I_a,
        'gamma': gamma,
        'phi': phi,
        'cos_phi': cos_phi,
        'P_elm': P_elm,
        'T_elm': T_elm,
        'P_out': P_out,
        'P_str': P_str,
        'P_cu': P_cu,
        'P_in': P_in,
        'efficiency': efficiency,
        'T_out': T_out,
        'V_d': V_d,
        'V_q': V_q,
        'delta_rad': delta_rad
    }

    return results

def create_static_visualization(params):
    """
    Create static visualization and save to file
    """
    # Create figure with subplots
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.35)

    # Create axes
    ax_phasor = fig.add_subplot(gs[0, 0])
    ax_dq = fig.add_subplot(gs[0, 1])
    ax_power = fig.add_subplot(gs[0, 2])
    ax_torque = fig.add_subplot(gs[1, 0])
    ax_efficiency = fig.add_subplot(gs[1, 1])
    ax_current = fig.add_subplot(gs[1, 2])
    ax_power_flow = fig.add_subplot(gs[2, :])

    # Calculate results
    results = calculate_motor_performance(params)

    # Plot all diagrams
    plot_phasor_diagram(ax_phasor, results, params)
    plot_dq_diagram(ax_dq, results, params)
    plot_power_distribution(ax_power, results, params)
    plot_torque_vs_angle(ax_torque, params, results)
    plot_efficiency_vs_load(ax_efficiency, params, results)
    plot_current_components(ax_current, results)
    plot_power_flow(ax_power_flow, results, params)

    # Title
    title_text = (f"Interior PM Synchronous Motor Analysis\n"
                 f"I_a = {results['I_a']:.2f} A, "
                 f"T_elm = {results['T_elm']:.2f} Nm, "
                 f"P_out = {results['P_out']:.1f} W, "
                 f"η = {results['efficiency']:.2f}%, "
                 f"cos φ = {results['cos_phi']:.3f}")
    fig.suptitle(title_text, fontsize=14, fontweight='bold')

    # Save figure
    plt.savefig('interior_pm_motor_analysis.png', dpi=300, bbox_inches='tight')
    print("\n✓ Plot saved as 'interior_pm_motor_analysis.png'")

    return results

def plot_phasor_diagram(ax, results, params):
    """Plot voltage and current phasor diagram"""
    scale_v = 50
    scale_i = 3

    V_ph = results['V_ph']
    delta = results['delta_rad']
    I_a = results['I_a']
    gamma = results['gamma']
    E_f = results['E_f']

    # Voltage phasor
    ax.arrow(0, 0, V_ph * np.sin(delta) / scale_v, V_ph * np.cos(delta) / scale_v,
            head_width=0.3, head_length=0.2, fc='red', ec='red', linewidth=2,
            label=f'V_ph = {V_ph:.1f} V')

    # Current phasor
    ax.arrow(0, 0, I_a * np.sin(gamma) / scale_i, I_a * np.cos(gamma) / scale_i,
            head_width=0.3, head_length=0.2, fc='blue', ec='blue', linewidth=2,
            label=f'I_a = {I_a:.2f} A')

    # EMF phasor
    ax.arrow(0, 0, 0, E_f / scale_v,
            head_width=0.3, head_length=0.2, fc='green', ec='green', linewidth=2,
            label=f'E_f = {E_f:.1f} V')

    # Axes
    ax.plot([-6, 6], [0, 0], 'k--', alpha=0.3, linewidth=0.5)
    ax.plot([0, 0], [-2, 6], 'k--', alpha=0.3, linewidth=0.5)
    ax.text(5.5, 0.3, 'd-axis', fontsize=8)
    ax.text(0.3, 5.5, 'q-axis', fontsize=8)

    phi_deg = np.degrees(results['phi'])
    delta_deg = params.delta
    ax.text(2, -1.5, f'δ = {delta_deg:.1f}°\nφ = {phi_deg:.1f}°',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_xlim(-6, 6)
    ax.set_ylim(-2, 6)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=8)
    ax.set_title('Phasor Diagram (Synchronous Frame)', fontweight='bold')
    ax.set_xlabel('d-axis (scaled)')
    ax.set_ylabel('q-axis (scaled)')

def plot_dq_diagram(ax, results, params):
    """Plot d-q axis components"""
    I_d = results['I_d']
    I_q = results['I_q']
    V_d = results['V_d']
    V_q = results['V_q']

    components = ['I_d', 'I_q', 'V_d', 'V_q']
    values = [I_d, I_q, V_d / 50, V_q / 50]
    colors = ['#ff6b6b', '#4ecdc4', '#ff9ff3', '#95e1d3']

    bars = ax.bar(range(len(components)), values, color=colors, alpha=0.7, edgecolor='black')
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.set_xticks(range(len(components)))
    ax.set_xticklabels(components)
    ax.set_ylabel('Value')
    ax.set_title('d-q Axis Components', fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    for i, (bar, val) in enumerate(zip(bars, values)):
        if i < 2:
            label_text = f'{val:.2f} A'
        else:
            label_text = f'{val*50:.1f} V'
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               label_text, ha='center', va='bottom' if height > 0 else 'top',
               fontsize=8, fontweight='bold')

    ax.text(0.5, 0.02, 'Note: Voltages scaled ÷50',
            transform=ax.transAxes, fontsize=7, style='italic')

def plot_power_distribution(ax, results, params):
    """Plot power distribution"""
    P_out = abs(results['P_out'])
    P_cu = abs(results['P_cu'])
    P_rot = abs(params.Prot)
    P_str = abs(results['P_str'])

    powers = [P_out, P_cu, P_rot, P_str]
    labels = [f'Output\n{P_out:.1f} W',
             f'Copper Loss\n{P_cu:.1f} W',
             f'Rotational Loss\n{P_rot:.1f} W',
             f'Stray Loss\n{P_str:.1f} W']
    colors = ['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
    explode = (0.1, 0, 0, 0)

    # Only plot if all powers are positive
    if all(p >= 0 for p in powers):
        ax.pie(powers, labels=labels, colors=colors, autopct='%1.1f%%',
              startangle=90, explode=explode)
    else:
        # Bar chart as alternative
        ax.barh(range(len(powers)), powers, color=colors)
        ax.set_yticks(range(len(powers)))
        ax.set_yticklabels(['Output', 'Copper Loss', 'Rot. Loss', 'Stray Loss'])
        ax.set_xlabel('Power (W)')

    ax.set_title('Power Distribution', fontweight='bold')

def plot_torque_vs_angle(ax, params, current_results):
    """Plot torque vs power angle"""
    angles = np.linspace(0, 90, 100)
    torques = []

    original_delta = params.delta
    for angle in angles:
        params.delta = angle
        res = calculate_motor_performance(params)
        torques.append(res['T_elm'])
    params.delta = original_delta

    ax.plot(angles, torques, 'b-', linewidth=2, label='T_elm vs δ')
    ax.plot(params.delta, current_results['T_elm'], 'ro',
           markersize=10, label=f'Operating Point')
    ax.axvline(x=params.delta, color='r', linestyle='--', alpha=0.5)
    ax.axhline(y=current_results['T_elm'], color='r', linestyle='--', alpha=0.5)

    ax.set_xlabel('Power Angle δ (degrees)')
    ax.set_ylabel('Electromagnetic Torque (Nm)')
    ax.set_title('Torque vs Power Angle', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

def plot_efficiency_vs_load(ax, params, current_results):
    """Plot efficiency vs load"""
    load_factors = np.linspace(0.2, 1.5, 50)
    efficiencies = []
    power_outputs = []

    original_delta = params.delta

    for factor in load_factors:
        params.delta = original_delta * factor * 0.8
        if params.delta > 90:
            params.delta = 90
        res = calculate_motor_performance(params)
        efficiencies.append(res['efficiency'])
        power_outputs.append(res['P_out'])

    params.delta = original_delta

    ax.plot(np.array(power_outputs) / 1000, efficiencies, 'g-', linewidth=2)
    ax.plot(current_results['P_out'] / 1000, current_results['efficiency'],
           'ro', markersize=10, label='Operating Point')

    ax.set_xlabel('Output Power (kW)')
    ax.set_ylabel('Efficiency (%)')
    ax.set_title('Efficiency vs Load', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_ylim(0, 100)

def plot_current_components(ax, results):
    """Plot current components"""
    I_d = results['I_d']
    I_q = results['I_q']
    I_a = results['I_a']

    ax.arrow(0, 0, I_d, 0, head_width=0.2, head_length=0.1,
            fc='red', ec='red', linewidth=2, label=f'I_d = {I_d:.2f} A')
    ax.arrow(I_d, 0, 0, I_q, head_width=0.2, head_length=0.1,
            fc='blue', ec='blue', linewidth=2, label=f'I_q = {I_q:.2f} A')
    ax.arrow(0, 0, I_d, I_q, head_width=0.2, head_length=0.1,
            fc='green', ec='green', linewidth=3, linestyle='--',
            label=f'I_a = {I_a:.2f} A')

    circle = Circle((0, 0), I_a, fill=False, edgecolor='green',
                   linestyle=':', linewidth=1, alpha=0.5)
    ax.add_patch(circle)

    ax.set_xlim(-2, max(6, I_d + 1))
    ax.set_ylim(-1, max(6, I_q + 1))
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_title('Armature Current Components', fontweight='bold')
    ax.set_xlabel('I_d (A)')
    ax.set_ylabel('I_q (A)')

def plot_power_flow(ax, results, params):
    """Plot power flow diagram"""
    P_in = results['P_in']
    P_elm = results['P_elm']
    P_cu = results['P_cu']
    P_out = results['P_out']
    P_rot = params.Prot
    P_str = results['P_str']

    positions = [0, 2, 4, 6]

    # Main flow line
    ax.plot([0, 6], [5, 5], 'k-', linewidth=20, alpha=0.3)

    box_width = 1.2
    box_height = 1.5

    # Boxes
    rect1 = mpatches.FancyBboxPatch((positions[0] - box_width/2, 5 - box_height/2),
                                   box_width, box_height,
                                   boxstyle="round,pad=0.1",
                                   edgecolor='black', facecolor='lightblue', linewidth=2)
    ax.add_patch(rect1)
    ax.text(positions[0], 5, f'P_in\n{P_in:.1f} W',
           ha='center', va='center', fontweight='bold', fontsize=9)

    rect2 = mpatches.FancyBboxPatch((positions[1] - box_width/2, 5 - box_height/2),
                                   box_width, box_height,
                                   boxstyle="round,pad=0.1",
                                   edgecolor='black', facecolor='lightgreen', linewidth=2)
    ax.add_patch(rect2)
    ax.text(positions[1], 5, f'P_elm\n{P_elm:.1f} W',
           ha='center', va='center', fontweight='bold', fontsize=9)

    rect3 = mpatches.FancyBboxPatch((positions[2] - box_width/2, 5 - box_height/2),
                                   box_width, box_height,
                                   boxstyle="round,pad=0.1",
                                   edgecolor='black', facecolor='lightyellow', linewidth=2)
    ax.add_patch(rect3)
    ax.text(positions[2], 5, f'P_mech\n{P_elm:.1f} W',
           ha='center', va='center', fontweight='bold', fontsize=9)

    rect4 = mpatches.FancyBboxPatch((positions[3] - box_width/2, 5 - box_height/2),
                                   box_width, box_height,
                                   boxstyle="round,pad=0.1",
                                   edgecolor='black', facecolor='lightcoral', linewidth=2)
    ax.add_patch(rect4)
    ax.text(positions[3], 5, f'P_out\n{P_out:.1f} W',
           ha='center', va='center', fontweight='bold', fontsize=9)

    # Loss arrows
    ax.annotate('', xy=(positions[0] + 0.8, 3), xytext=(positions[0] + 0.8, 4.2),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(positions[0] + 0.8, 2.5, f'P_cu\n{P_cu:.1f} W',
           ha='center', va='top', fontsize=8, color='red', fontweight='bold')

    ax.annotate('', xy=(positions[2] + 0.7, 3), xytext=(positions[2] + 0.7, 4.2),
               arrowprops=dict(arrowstyle='->', color='orange', lw=2))
    ax.text(positions[2] + 0.7, 2.5, f'P_rot\n{P_rot:.1f} W',
           ha='center', va='top', fontsize=8, color='orange', fontweight='bold')

    ax.annotate('', xy=(positions[3] - 0.7, 3), xytext=(positions[3] - 0.7, 4.2),
               arrowprops=dict(arrowstyle='->', color='purple', lw=2))
    ax.text(positions[3] - 0.7, 2.5, f'P_str\n{P_str:.1f} W',
           ha='center', va='top', fontsize=8, color='purple', fontweight='bold')

    # Efficiency
    ax.text(3, 7, f'Efficiency: η = {results["efficiency"]:.2f}%',
           ha='center', va='center', fontsize=12, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    ax.set_xlim(-1, 7)
    ax.set_ylim(1, 8)
    ax.axis('off')
    ax.set_title('Power Flow Diagram', fontweight='bold', fontsize=12, pad=20)

def print_detailed_results(params, results):
    """Print detailed analysis results"""
    print("="*80)
    print("INTERIOR PM SYNCHRONOUS MOTOR ANALYSIS RESULTS")
    print("="*80)
    print(f"\nMotor Specifications:")
    print(f"  Poles: {params.poles}")
    print(f"  Frequency: {params.f} Hz")
    print(f"  Line-to-Line Voltage: {params.V_LL} V")
    print(f"  Phase Voltage: {results['V_ph']:.2f} V")
    print(f"  Synchronous Speed: {results['n_s']:.1f} rpm ({results['omega_s']:.2f} rad/s)")
    print(f"  Stator Resistance: {params.R1} Ω")
    print(f"  d-axis Reactance: {params.Xsd} Ω")
    print(f"  q-axis Reactance: {params.Xsq} Ω")

    print(f"\nPermanent Magnet Parameters:")
    print(f"  Air Gap Flux Density: {params.Bmg} T")
    print(f"  Flux per Pole: {results['Phi_pm']*1000:.4f} mWb")
    print(f"  Induced EMF: {results['E_f']:.2f} V")

    print(f"\nOperating Point (δ = {params.delta}°):")
    print(f"  d-axis Voltage: {results['V_d']:.2f} V")
    print(f"  q-axis Voltage: {results['V_q']:.2f} V")
    print(f"  d-axis Current: {results['I_d']:.3f} A")
    print(f"  q-axis Current: {results['I_q']:.3f} A")
    print(f"  Armature Current: {results['I_a']:.3f} A")

    print(f"\n*** KEY RESULTS ***")
    print(f"  Armature Current (I_a): {results['I_a']:.3f} A")
    print(f"  Electromagnetic Torque (T_elm): {results['T_elm']:.3f} Nm")
    print(f"  Output Power (P_out): {results['P_out']:.2f} W ({results['P_out']/1000:.3f} kW)")
    print(f"  Efficiency (η): {results['efficiency']:.2f} %")
    print(f"  Power Factor (cos φ): {results['cos_phi']:.4f}")
    print(f"  Power Factor Angle: {np.degrees(results['phi']):.2f}°")

    print(f"\nPerformance Details:")
    print(f"  Electromagnetic Power: {results['P_elm']:.2f} W")
    print(f"  Output Torque: {results['T_out']:.3f} Nm")

    print(f"\nLosses:")
    print(f"  Copper Losses: {results['P_cu']:.2f} W")
    print(f"  Rotational Losses: {params.Prot:.2f} W")
    print(f"  Stray Losses: {results['P_str']:.2f} W")
    print(f"  Total Losses: {results['P_cu'] + params.Prot + results['P_str']:.2f} W")

    print(f"\nPower Balance:")
    print(f"  Input Power: {results['P_in']:.2f} W")
    print(f"  Output Power: {results['P_out']:.2f} W")
    print(f"  Total Losses: {results['P_in'] - results['P_out']:.2f} W")

    print("="*80)

if __name__ == "__main__":
    # Initialize motor parameters
    motor_params = MotorParameters()

    # Perform analysis
    results = create_static_visualization(motor_params)

    # Print results
    print_detailed_results(motor_params, results)

    print("\n✓ Analysis complete!")
    print("✓ Interactive version available in: interior_pm_motor_analysis.py")
    print("  (Run with GUI support to use sliders)")
