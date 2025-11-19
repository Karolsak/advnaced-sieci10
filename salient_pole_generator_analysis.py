import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from matplotlib.patches import FancyArrowPatch
import matplotlib.patches as mpatches

# Given nominal parameters
Sn = 25e6  # VA (apparent power)
V1Ln = 12.5e3  # V (line-to-line voltage nominal)
Ian = 1105  # A (armature current nominal)
fn = 50  # Hz (frequency)
cos_phi_n = 0.86  # lagging
Ifn = 475  # A (field current nominal)
Xsd = 4.2  # Ω (d-axis synchronous reactance)
Xsq = 2.4  # Ω (q-axis synchronous reactance)

# Operating conditions
If_actual = 425  # A (actual field current)
V1L = 10.5e3  # V (terminal voltage line-to-line)
Q_load = 10.6e6  # VAr (reactive power delivered to load, inductive)

# Convert to phase values
V1n = V1Ln / np.sqrt(3)  # Nominal phase voltage
V1 = V1L / np.sqrt(3)  # Actual phase voltage
Q_phase = Q_load / 3  # Reactive power per phase

# Calculate nominal powers
Pn = Sn * cos_phi_n  # Total active power nominal
phi_n = np.arccos(cos_phi_n)  # Power factor angle nominal
Qn = Sn * np.sin(phi_n)  # Total reactive power nominal
Pn_phase = Pn / 3  # Active power per phase nominal
Qn_phase = Qn / 3  # Reactive power per phase nominal

print("="*70)
print("SALIENT-POLE SYNCHRONOUS GENERATOR ANALYSIS")
print("="*70)
print("\n1. NOMINAL PARAMETERS:")
print(f"   Apparent Power: Sn = {Sn/1e6:.2f} MVA")
print(f"   Line Voltage: V1Ln = {V1Ln/1e3:.2f} kV")
print(f"   Phase Voltage: V1n = {V1n/1e3:.3f} kV")
print(f"   Armature Current: Ian = {Ian:.1f} A")
print(f"   Power Factor: cos(φn) = {cos_phi_n:.2f} lagging")
print(f"   Field Current: Ifn = {Ifn:.1f} A")
print(f"   d-axis Reactance: Xsd = {Xsd:.1f} Ω")
print(f"   q-axis Reactance: Xsq = {Xsq:.1f} Ω")
print(f"   Active Power: Pn = {Pn/1e6:.2f} MW")
print(f"   Reactive Power: Qn = {Qn/1e6:.3f} MVAr")

# Step 1: Find nominal EMF (Efn) and load angle (δn) at nominal conditions
# Using power equations for salient-pole generator:
# P = (V1*Ef/Xsd)*sin(δ) + V1²*(Xsd - Xsq)/(2*Xsd*Xsq)*sin(2δ)
# Q = (V1*Ef/Xsd)*cos(δ) - V1²/Xsd + V1²*(Xsd - Xsq)/(2*Xsd*Xsq)*(1 - cos(2δ))

def power_equations_nominal(vars):
    """Power equations for nominal conditions"""
    Efn, delta_n = vars

    # Calculate power components
    P_calc = (V1n * Efn / Xsd) * np.sin(delta_n) + \
             (V1n**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * np.sin(2 * delta_n)

    Q_calc = (V1n * Efn / Xsd) * np.cos(delta_n) - V1n**2 / Xsd + \
             (V1n**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * (1 - np.cos(2 * delta_n))

    # Return residuals
    return [P_calc - Pn_phase, Q_calc - Qn_phase]

# Initial guess: Efn ≈ V1n + some voltage drop, δn ≈ 20-30 degrees
initial_guess = [V1n * 1.5, np.radians(25)]
solution_nominal = fsolve(power_equations_nominal, initial_guess)
Efn, delta_n = solution_nominal
delta_n_deg = np.degrees(delta_n)

print(f"\n2. NOMINAL OPERATING POINT (at Ifn = {Ifn} A):")
print(f"   Internal EMF: Efn = {Efn/1e3:.3f} kV")
print(f"   Load Angle: δn = {delta_n_deg:.2f}°")

# Verify the solution
P_verify = (V1n * Efn / Xsd) * np.sin(delta_n) + \
           (V1n**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * np.sin(2 * delta_n)
Q_verify = (V1n * Efn / Xsd) * np.cos(delta_n) - V1n**2 / Xsd + \
           (V1n**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * (1 - np.cos(2 * delta_n))
print(f"   Verification: P = {P_verify/1e6:.3f} MW, Q = {Q_verify/1e6:.3f} MVAr")

# Step 2: Scale EMF based on field current ratio (assuming linear magnetization)
Ef = Efn * (If_actual / Ifn)

print(f"\n3. ACTUAL OPERATING CONDITIONS:")
print(f"   Field Current: If = {If_actual} A")
print(f"   Scaling Factor: If/Ifn = {If_actual/Ifn:.4f}")
print(f"   Internal EMF: Ef = {Ef/1e3:.3f} kV")
print(f"   Terminal Voltage: V1 = {V1/1e3:.3f} kV")
print(f"   Reactive Power: Q = {Q_load/1e6:.2f} MVAr (inductive load)")

# Step 3: Solve for load angle (δ) and active power (P) at actual conditions
def power_equations_actual(vars):
    """Power equations for actual operating conditions"""
    P, delta = vars

    # Q equation (known)
    Q_calc = (V1 * Ef / Xsd) * np.cos(delta) - V1**2 / Xsd + \
             (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * (1 - np.cos(2 * delta))

    # P equation
    P_calc = (V1 * Ef / Xsd) * np.sin(delta) + \
             (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * np.sin(2 * delta)

    # Return residuals
    return [Q_calc - Q_phase, P_calc - P]

# Initial guess
initial_guess_actual = [Pn_phase * 0.5, np.radians(20)]
solution_actual = fsolve(power_equations_actual, initial_guess_actual)
P_phase, delta = solution_actual
delta_deg = np.degrees(delta)

# Total three-phase power
P_total = 3 * P_phase
Q_total = 3 * Q_phase

print(f"\n" + "="*70)
print("SOLUTION:")
print("="*70)
print(f"\n(a) LOAD ANGLE:")
print(f"    δ = {delta_deg:.2f}° = {delta:.4f} rad")

print(f"\n(b) ACTIVE POWER DELIVERED:")
print(f"    P (per phase) = {P_phase/1e6:.3f} MW")
print(f"    P (total) = {P_total/1e6:.2f} MW")

# Verify using power equations
P_verify_actual = (V1 * Ef / Xsd) * np.sin(delta) + \
                  (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * np.sin(2 * delta)
Q_verify_actual = (V1 * Ef / Xsd) * np.cos(delta) - V1**2 / Xsd + \
                  (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * (1 - np.cos(2 * delta))

print(f"\n    Verification:")
print(f"    P calculated = {P_verify_actual/1e6:.3f} MW")
print(f"    Q calculated = {Q_verify_actual/1e6:.3f} MVAr")

# Step 4: Calculate load current and power factor
# Calculate current components in dq frame
# Using the relationship between power and voltage/current
S_phase = P_phase + 1j * Q_phase
Ia_complex = np.conj(S_phase / V1)  # Conjugate for generator convention
Ia = np.abs(Ia_complex)
phi = -np.angle(Ia_complex)  # Negative because current lags voltage
cos_phi = np.cos(phi)
phi_deg = np.degrees(phi)

print(f"\n(c) LOAD CURRENT AND POWER FACTOR:")
print(f"    Ia = {Ia:.2f} A")
print(f"    Power factor angle: φ = {phi_deg:.2f}°")
print(f"    cos(φ) = {cos_phi:.4f} lagging")

# Additional calculations for visualization
# Calculate current components in dq reference frame
Id = Ia * np.sin(delta + phi)
Iq = Ia * np.cos(delta + phi)

print(f"\n4. CURRENT COMPONENTS (d-q frame):")
print(f"   Id = {Id:.2f} A")
print(f"   Iq = {Iq:.2f} A")
print(f"   Verification: Ia = √(Id² + Iq²) = {np.sqrt(Id**2 + Iq**2):.2f} A")

# Voltage drops
Vd = -Xsq * Iq
Vq = Ef - Xsd * Id

print(f"\n5. VOLTAGE COMPONENTS (d-q frame):")
print(f"   Vd = {Vd:.2f} V")
print(f"   Vq = {Vq:.2f} V")
print(f"   Verification: V1 = √(Vd² + Vq²) = {np.sqrt(Vd**2 + Vq**2):.2f} V")
print(f"   Load angle from voltage: δ = {np.degrees(np.arctan2(-Vd, Vq)):.2f}°")

# Calculate apparent power
S_total = np.sqrt(P_total**2 + Q_total**2)
print(f"\n6. APPARENT POWER:")
print(f"   S = {S_total/1e6:.2f} MVA")
print(f"   Verification: S = √3 × V1L × Ia = {np.sqrt(3) * V1L * Ia / 1e6:.2f} MVA")

print("\n" + "="*70)

# ============================================================================
# VISUALIZATION
# ============================================================================

fig = plt.figure(figsize=(16, 12))

# Subplot 1: Phasor Diagram in stationary reference frame
ax1 = fig.add_subplot(2, 3, 1)

# Reference: Terminal voltage V1 on real axis
V1_phasor = V1
Ia_angle = -phi  # Current lags voltage
Ia_phasor = Ia * np.exp(1j * Ia_angle)
Ef_phasor = Ef * np.exp(1j * delta)

# Voltage drops
jXsd_Id = 1j * Xsd * Id
jXsq_Iq = 1j * Xsq * Iq

# Plot phasors
origin = [0, 0]

# Terminal voltage V1 (reference)
ax1.arrow(0, 0, V1, 0, head_width=200, head_length=300, fc='blue', ec='blue', linewidth=2)
ax1.text(V1/2, -400, r'$\vec{V_1}$', fontsize=12, color='blue', fontweight='bold')

# Current Ia
Ia_real = np.real(Ia_phasor)
Ia_imag = np.imag(Ia_phasor)
ax1.arrow(0, 0, Ia_real*5, Ia_imag*5, head_width=200, head_length=300,
          fc='red', ec='red', linewidth=2, linestyle='--')
ax1.text(Ia_real*5/2 - 500, Ia_imag*5/2, r'$\vec{I_a}$', fontsize=12,
         color='red', fontweight='bold')

# Internal EMF Ef
Ef_real = np.real(Ef_phasor)
Ef_imag = np.imag(Ef_phasor)
ax1.arrow(0, 0, Ef_real, Ef_imag, head_width=200, head_length=300,
          fc='green', ec='green', linewidth=2.5)
ax1.text(Ef_real/2 + 300, Ef_imag/2 + 300, r'$\vec{E_f}$', fontsize=12,
         color='green', fontweight='bold')

# Load angle
arc_radius = 1500
angle_arc = mpatches.Arc((0, 0), 2*arc_radius, 2*arc_radius,
                         angle=0, theta1=0, theta2=delta_deg,
                         color='purple', linewidth=2)
ax1.add_patch(angle_arc)
ax1.text(arc_radius*1.2, 200, f'δ = {delta_deg:.1f}°',
         fontsize=10, color='purple', fontweight='bold')

# Power factor angle
pf_arc_radius = 1000
pf_arc = mpatches.Arc((0, 0), 2*pf_arc_radius, 2*pf_arc_radius,
                       angle=0, theta1=Ia_angle*180/np.pi, theta2=0,
                       color='orange', linewidth=1.5, linestyle='--')
ax1.add_patch(pf_arc)
ax1.text(pf_arc_radius*0.8, -600, f'φ = {phi_deg:.1f}°',
         fontsize=10, color='orange', fontweight='bold')

ax1.grid(True, alpha=0.3)
ax1.axis('equal')
ax1.set_xlabel('Real Axis (V, A×5)', fontsize=11)
ax1.set_ylabel('Imaginary Axis (V, A×5)', fontsize=11)
ax1.set_title('Phasor Diagram (Stationary Reference Frame)', fontsize=13, fontweight='bold')
ax1.legend([r'$V_1$ (Terminal Voltage)', r'$I_a$ (Current, scaled ×5)',
            r'$E_f$ (Internal EMF)'],
           loc='upper right', fontsize=9)

# Subplot 2: d-q Reference Frame
ax2 = fig.add_subplot(2, 3, 2)

# d-q axes
ax2.arrow(0, 0, 0, 7000, head_width=15, head_length=300, fc='gray', ec='gray', linewidth=1.5)
ax2.text(-150, 7200, 'q-axis', fontsize=11, color='gray', fontweight='bold')
ax2.arrow(0, 0, 500, 0, head_width=250, head_length=20, fc='gray', ec='gray', linewidth=1.5)
ax2.text(520, -300, 'd-axis', fontsize=11, color='gray', fontweight='bold')

# Terminal voltage components
ax2.arrow(0, 0, -Vd/10, 0, head_width=200, head_length=20, fc='blue', ec='blue', linewidth=2)
ax2.text(-Vd/10/2, -500, f'$V_d$ = {Vd:.0f} V', fontsize=10, color='blue')

ax2.arrow(0, 0, 0, Vq, head_width=15, head_length=250, fc='blue', ec='blue', linewidth=2)
ax2.text(150, Vq/2, f'$V_q$ = {Vq:.0f} V', fontsize=10, color='blue')

# Resultant V1
ax2.arrow(0, 0, -Vd/10, Vq, head_width=200, head_length=300,
          fc='darkblue', ec='darkblue', linewidth=2.5, linestyle='--')
ax2.text(-Vd/10/2 - 150, Vq/2 + 300, r'$\vec{V_1}$', fontsize=12,
         color='darkblue', fontweight='bold')

# Current components
ax2.arrow(-Vd/10, Vq, Id*3, 0, head_width=200, head_length=30,
          fc='red', ec='red', linewidth=2, alpha=0.7)
ax2.text(-Vd/10 + Id*3/2, Vq + 400, f'$I_d$ = {Id:.0f} A', fontsize=10, color='red')

ax2.arrow(-Vd/10, Vq, 0, Iq*3, head_width=30, head_length=100,
          fc='darkred', ec='darkred', linewidth=2, alpha=0.7)
ax2.text(-Vd/10 - 200, Vq + Iq*3/2, f'$I_q$ = {Iq:.0f} A', fontsize=10, color='darkred')

# Ef on q-axis
ax2.arrow(0, 0, 0, Ef, head_width=15, head_length=300,
          fc='green', ec='green', linewidth=2.5)
ax2.text(200, Ef/2, r'$E_f$', fontsize=12, color='green', fontweight='bold')

ax2.grid(True, alpha=0.3)
ax2.axis('equal')
ax2.set_xlabel('d-axis (V, A×3)', fontsize=11)
ax2.set_ylabel('q-axis (V)', fontsize=11)
ax2.set_title('d-q Reference Frame (Rotor Frame)', fontsize=13, fontweight='bold')
ax2.set_xlim(-800, 800)
ax2.set_ylim(-500, 9000)

# Subplot 3: Power Triangle
ax3 = fig.add_subplot(2, 3, 3)

# Power triangle
ax3.arrow(0, 0, P_total/1e6, 0, head_width=0.3, head_length=0.5,
          fc='green', ec='green', linewidth=3)
ax3.text(P_total/1e6/2, -0.7, f'P = {P_total/1e6:.2f} MW',
         fontsize=11, color='green', fontweight='bold')

ax3.arrow(P_total/1e6, 0, 0, Q_total/1e6, head_width=0.5, head_length=0.3,
          fc='red', ec='red', linewidth=3)
ax3.text(P_total/1e6 + 0.5, Q_total/1e6/2, f'Q = {Q_total/1e6:.2f} MVAr',
         fontsize=11, color='red', fontweight='bold')

ax3.arrow(0, 0, P_total/1e6, Q_total/1e6, head_width=0.4, head_length=0.5,
          fc='blue', ec='blue', linewidth=3, linestyle='--')
ax3.text(P_total/1e6/2 - 1, Q_total/1e6/2 + 0.5, f'S = {S_total/1e6:.2f} MVA',
         fontsize=11, color='blue', fontweight='bold')

# Power factor angle
pf_angle_power = np.degrees(np.arctan2(Q_total, P_total))
arc_pf = mpatches.Arc((0, 0), 4, 4, angle=0, theta1=0, theta2=pf_angle_power,
                       color='purple', linewidth=2)
ax3.add_patch(arc_pf)
ax3.text(2.5, 0.5, f'φ = {phi_deg:.1f}°\ncos φ = {cos_phi:.3f}',
         fontsize=10, color='purple', fontweight='bold')

ax3.grid(True, alpha=0.3)
ax3.axis('equal')
ax3.set_xlabel('Active Power (MW)', fontsize=11)
ax3.set_ylabel('Reactive Power (MVAr)', fontsize=11)
ax3.set_title('Power Triangle', fontsize=13, fontweight='bold')
ax3.set_xlim(-2, 18)
ax3.set_ylim(-2, 14)

# Subplot 4: Power vs Load Angle Characteristics
ax4 = fig.add_subplot(2, 3, 4)

delta_range = np.linspace(0, np.pi/2, 200)
P_curve = [(V1 * Ef / Xsd) * np.sin(d) +
           (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * np.sin(2*d)
           for d in delta_range]
P_curve = np.array(P_curve) / 1e6  # Convert to MW per phase

Q_curve = [(V1 * Ef / Xsd) * np.cos(d) - V1**2 / Xsd +
           (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * (1 - np.cos(2*d))
           for d in delta_range]
Q_curve = np.array(Q_curve) / 1e6  # Convert to MVAr per phase

ax4.plot(np.degrees(delta_range), P_curve, 'g-', linewidth=2.5, label='Active Power P')
ax4.plot(np.degrees(delta_range), Q_curve, 'r-', linewidth=2.5, label='Reactive Power Q')
ax4.axvline(delta_deg, color='blue', linestyle='--', linewidth=2, label=f'Operating Point (δ={delta_deg:.1f}°)')
ax4.plot(delta_deg, P_phase/1e6, 'go', markersize=10, label=f'P = {P_phase/1e6:.2f} MW')
ax4.plot(delta_deg, Q_phase/1e6, 'ro', markersize=10, label=f'Q = {Q_phase/1e6:.2f} MVAr')

ax4.grid(True, alpha=0.3)
ax4.set_xlabel('Load Angle δ (degrees)', fontsize=11)
ax4.set_ylabel('Power per Phase (MW, MVAr)', fontsize=11)
ax4.set_title('Power vs Load Angle Characteristics', fontsize=13, fontweight='bold')
ax4.legend(fontsize=9, loc='best')
ax4.set_xlim(0, 90)

# Subplot 5: Operating Point Comparison
ax5 = fig.add_subplot(2, 3, 5)

categories = ['Voltage\n(kV)', 'Power\n(MW)', 'Reactive\n(MVAr)',
              'Current\n(A)', 'Power\nFactor']
nominal_values = [V1Ln/1e3, Pn/1e6, Qn/1e6, Ian, cos_phi_n]
actual_values = [V1L/1e3, P_total/1e6, Q_total/1e6, Ia, cos_phi]

x = np.arange(len(categories))
width = 0.35

bars1 = ax5.bar(x - width/2, nominal_values, width, label='Nominal',
                color='skyblue', edgecolor='black', linewidth=1.5)
bars2 = ax5.bar(x + width/2, actual_values, width, label='Actual Operating',
                color='lightcoral', edgecolor='black', linewidth=1.5)

# Add value labels on bars
for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
    height1 = bar1.get_height()
    height2 = bar2.get_height()
    ax5.text(bar1.get_x() + bar1.get_width()/2., height1,
             f'{nominal_values[i]:.1f}', ha='center', va='bottom', fontsize=9)
    ax5.text(bar2.get_x() + bar2.get_width()/2., height2,
             f'{actual_values[i]:.1f}', ha='center', va='bottom', fontsize=9)

ax5.set_ylabel('Values', fontsize=11)
ax5.set_title('Nominal vs Actual Operating Conditions', fontsize=13, fontweight='bold')
ax5.set_xticks(x)
ax5.set_xticklabels(categories, fontsize=10)
ax5.legend(fontsize=10)
ax5.grid(True, alpha=0.3, axis='y')

# Subplot 6: Summary Table
ax6 = fig.add_subplot(2, 3, 6)
ax6.axis('off')

summary_data = [
    ['Parameter', 'Value', 'Unit'],
    ['', '', ''],
    ['GIVEN CONDITIONS', '', ''],
    ['Terminal Voltage (L-L)', f'{V1L/1e3:.2f}', 'kV'],
    ['Field Current', f'{If_actual:.0f}', 'A'],
    ['Reactive Power Load', f'{Q_load/1e6:.2f}', 'MVAr'],
    ['', '', ''],
    ['CALCULATED RESULTS', '', ''],
    ['(a) Load Angle δ', f'{delta_deg:.2f}', '°'],
    ['', f'{delta:.4f}', 'rad'],
    ['(b) Active Power P', f'{P_total/1e6:.2f}', 'MW'],
    ['(c) Load Current Ia', f'{Ia:.2f}', 'A'],
    ['    Power Factor cos φ', f'{cos_phi:.4f}', 'lagging'],
    ['    PF Angle φ', f'{phi_deg:.2f}', '°'],
    ['', '', ''],
    ['Apparent Power S', f'{S_total/1e6:.2f}', 'MVA'],
    ['Internal EMF Ef', f'{Ef/1e3:.3f}', 'kV'],
]

table = ax6.table(cellText=summary_data, cellLoc='left', loc='center',
                  colWidths=[0.5, 0.3, 0.2])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)

# Style the table
for i in range(len(summary_data)):
    for j in range(3):
        cell = table[(i, j)]
        if i == 0:  # Header row
            cell.set_facecolor('#4472C4')
            cell.set_text_props(weight='bold', color='white')
        elif i in [2, 7]:  # Section headers
            cell.set_facecolor('#B4C7E7')
            cell.set_text_props(weight='bold')
        elif i in [1, 6, 14]:  # Empty rows
            cell.set_facecolor('#F0F0F0')
        else:
            if i % 2 == 0:
                cell.set_facecolor('#FFFFFF')
            else:
                cell.set_facecolor('#F8F8F8')
        cell.set_edgecolor('black')
        cell.set_linewidth(1)

ax6.set_title('Summary of Results', fontsize=13, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('/home/user/advnaced-sieci10/salient_pole_generator_analysis.png',
            dpi=300, bbox_inches='tight')
print("\n" + "="*70)
print("Visualization saved as: salient_pole_generator_analysis.png")
print("="*70)

plt.show()

# Additional analysis: Capability curve
fig2, ax = plt.subplots(1, 1, figsize=(10, 8))

# Generate P-Q capability curve for the generator at this voltage and excitation
delta_capability = np.linspace(0, np.pi/2, 500)
P_capability = []
Q_capability = []

for d in delta_capability:
    P_temp = (V1 * Ef / Xsd) * np.sin(d) + \
             (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * np.sin(2*d)
    Q_temp = (V1 * Ef / Xsd) * np.cos(d) - V1**2 / Xsd + \
             (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * (1 - np.cos(2*d))
    P_capability.append(P_temp * 3 / 1e6)  # Three-phase MW
    Q_capability.append(Q_temp * 3 / 1e6)  # Three-phase MVAr

ax.plot(P_capability, Q_capability, 'b-', linewidth=2.5,
        label=f'Capability Curve (Ef = {Ef/1e3:.2f} kV, V1 = {V1/1e3:.2f} kV)')

# Plot operating point
ax.plot(P_total/1e6, Q_total/1e6, 'ro', markersize=12,
        label=f'Operating Point (P={P_total/1e6:.2f} MW, Q={Q_total/1e6:.2f} MVAr)')

# Add constant load angle lines
for d_line in [10, 20, 30, 40, 50, 60, 70, 80]:
    d_rad = np.radians(d_line)
    P_line = (V1 * Ef / Xsd) * np.sin(d_rad) + \
             (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * np.sin(2*d_rad)
    Q_line = (V1 * Ef / Xsd) * np.cos(d_rad) - V1**2 / Xsd + \
             (V1**2 * (Xsd - Xsq) / (2 * Xsd * Xsq)) * (1 - np.cos(2*d_rad))
    ax.plot([0, P_line*3/1e6], [0, Q_line*3/1e6], 'g--',
            alpha=0.3, linewidth=1)
    ax.text(P_line*3/1e6*1.05, Q_line*3/1e6*1.05, f'{d_line}°',
            fontsize=8, color='green', alpha=0.7)

ax.grid(True, alpha=0.3)
ax.set_xlabel('Active Power P (MW)', fontsize=12)
ax.set_ylabel('Reactive Power Q (MVAr)', fontsize=12)
ax.set_title('P-Q Capability Diagram with Operating Point', fontsize=14, fontweight='bold')
ax.legend(fontsize=10, loc='best')
ax.axhline(0, color='k', linewidth=0.5)
ax.axvline(0, color='k', linewidth=0.5)

plt.tight_layout()
plt.savefig('/home/user/advnaced-sieci10/capability_curve.png', dpi=300, bbox_inches='tight')
print("Capability curve saved as: capability_curve.png")

plt.show()

print("\n" + "="*70)
print("ANALYSIS COMPLETE!")
print("="*70)
