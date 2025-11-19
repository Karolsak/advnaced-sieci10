"""
Core Synchronous Generator Calculations (No GUI Required)
Example 7.3 Solution - Standalone Module
"""

import numpy as np
from scipy.integrate import solve_ivp
from dataclasses import dataclass
from typing import Dict


@dataclass
class GeneratorParameters:
    """Synchronous Generator Parameters"""
    # Nominal parameters
    Sn: float = 50e3  # Apparent power (VA)
    V1Ln: float = 380  # Line voltage (V)
    fn: float = 60  # Frequency (Hz)
    nn: float = 1800  # Speed (rpm)
    cos_phi_n: float = 0.82  # Power factor

    # Test results
    Vs_test: float = 115  # Test voltage (V)
    n_test: float = 1768  # Test speed (rpm)
    fs_test: float = 60  # Test frequency (Hz)
    Imax: float = 22.2  # Maximum current (A)
    Imin: float = 11.3  # Minimum current (A)

    # Field winding
    Rf_20C: float = 0.8  # Field resistance at 20°C (Ω)
    If0: float = 10.5  # Field current at no load (A)
    temp_field: float = 120  # Field temperature (°C)

    # Calculated parameters
    Xsd: float = 0  # d-axis synchronous reactance
    Xsq: float = 0  # q-axis synchronous reactance
    Ifn: float = 0  # Nominal field current
    Vfn: float = 0  # Nominal field voltage
    Ra: float = 0.05  # Stator resistance (assumed small)

    # Mechanical parameters
    J: float = 2.0  # Moment of inertia (kg·m²)
    D: float = 0.5  # Damping coefficient (N·m·s)
    p: int = 2  # Number of pole pairs


class SynchronousGeneratorModel:
    """Mathematical model of salient-pole synchronous generator"""

    def __init__(self, params: GeneratorParameters):
        self.params = params
        self.calculate_parameters()

    def calculate_parameters(self):
        """Calculate synchronous reactances and field parameters - Example 7.3"""
        # Part (a): Synchronous reactances from slip test
        self.params.Xsd = self.params.Vs_test / self.params.Imin
        self.params.Xsq = self.params.Vs_test / self.params.Imax

        # Nominal phase voltage and current
        V1n_phase = self.params.V1Ln / np.sqrt(3)
        In = self.params.Sn / (np.sqrt(3) * self.params.V1Ln)

        # Part (b): Nominal field current
        phi_n = np.arccos(self.params.cos_phi_n)
        sin_phi_n = np.sin(phi_n)

        # For synchronous generator with lagging power factor
        # Standard approximation formula for excitation voltage:
        # Ef ≈ √[(V + Xq*I*sin(φ))² + (Xd*I*cos(φ))²]
        # This accounts for the salient pole effect

        # Using engineering approximation (neglecting Ra as stated)
        Ef_horizontal = V1n_phase + self.params.Xsq * In * sin_phi_n
        Ef_vertical = self.params.Xsd * In * self.params.cos_phi_n

        Ef = np.sqrt(Ef_horizontal**2 + Ef_vertical**2)

        # Calculate actual d-q components for reference
        Id = In * sin_phi_n
        Iq = In * self.params.cos_phi_n

        # Linear magnetization: If proportional to Ef
        # At no load: Ef0 = V1n_phase, If0 = 10.5 A
        self.params.Ifn = self.params.If0 * (Ef / V1n_phase)

        # Part (c): Field voltage at operating temperature
        # Temperature coefficient for copper
        alpha_cu = 0.00393  # per °C
        T_ref = 20  # Reference temperature (°C)

        Rf_temp = self.params.Rf_20C * (1 + alpha_cu * (self.params.temp_field - T_ref))
        self.params.Vfn = self.params.Ifn * Rf_temp

        return {
            'Xsd': self.params.Xsd,
            'Xsq': self.params.Xsq,
            'Ifn': self.params.Ifn,
            'Vfn': self.params.Vfn,
            'Ef': Ef,
            'V1n_phase': V1n_phase,
            'In': In,
            'Id': Id,
            'Iq': Iq,
            'Rf_temp': Rf_temp
        }

    def calculate_losses(self, operating_point: Dict) -> Dict:
        """Calculate detailed loss breakdown"""
        In = operating_point.get('In', 0)
        Ifn = operating_point.get('Ifn', 0)
        Rf_temp = operating_point.get('Rf_temp', self.params.Rf_20C)

        # Copper losses
        P_cu_stator = 3 * In**2 * self.params.Ra  # 3-phase stator copper loss
        P_cu_rotor = Ifn**2 * Rf_temp  # Rotor (field) copper loss

        # Iron losses (simplified Steinmetz equation)
        # Typically 0.5-1.5% of rated power for generators
        V_phase = self.params.V1Ln / np.sqrt(3)
        k_h = 0.00001  # Hysteresis coefficient (adjusted)
        k_e = 0.0000001  # Eddy current coefficient (adjusted)
        P_iron = k_h * self.params.fn * V_phase**2 + k_e * (self.params.fn * V_phase)**2

        # Mechanical losses
        P_friction = 0.01 * self.params.Sn  # 1% of rated power
        P_windage = 0.005 * self.params.Sn  # 0.5% of rated power

        # Stray load losses
        P_stray = 0.01 * self.params.Sn * (In / (self.params.Sn / (np.sqrt(3) * self.params.V1Ln)))**2

        total_losses = P_cu_stator + P_cu_rotor + P_iron + P_friction + P_windage + P_stray

        return {
            'Copper_Stator': P_cu_stator,
            'Copper_Rotor': P_cu_rotor,
            'Iron': P_iron,
            'Friction': P_friction,
            'Windage': P_windage,
            'Stray': P_stray,
            'Total': total_losses
        }

    def thermal_model(self, losses: Dict, ambient_temp: float = 25) -> Dict:
        """Thermal model for temperature prediction"""
        # Thermal resistances (K/W) - adjusted for realistic values
        R_th_stator = 0.02  # Stator to ambient (for 50kVA machine with cooling)
        R_th_rotor = 0.05  # Rotor to ambient

        # Steady-state temperatures
        T_stator = ambient_temp + (losses['Copper_Stator'] + losses['Iron']) * R_th_stator
        T_rotor = ambient_temp + losses['Copper_Rotor'] * R_th_rotor

        # Derating factor based on temperature
        T_max = 155  # Class F insulation
        derating_factor = max(0, (T_max - T_stator) / T_max)

        return {
            'Stator_Temp': T_stator,
            'Rotor_Temp': T_rotor,
            'Ambient_Temp': ambient_temp,
            'Derating_Factor': derating_factor,
            'Max_Temp': T_max
        }

    def mechanical_stress_analysis(self, torque: float) -> Dict:
        """Mechanical stress and bearing load analysis"""
        # Shaft torque
        T_rated = self.params.Sn / (2 * np.pi * self.params.nn / 60)

        # Shaft stress (simplified)
        d_shaft = 0.05  # Assumed shaft diameter (m)
        tau_shaft = 16 * torque / (np.pi * d_shaft**3)  # Torsional stress (Pa)

        # Bearing loads (simplified radial load)
        F_bearing = torque / (d_shaft / 2) if d_shaft > 0 else 0

        # Safety factor
        tau_yield = 250e6  # Typical steel yield stress (Pa)
        safety_factor = tau_yield / tau_shaft if tau_shaft > 0 else float('inf')

        return {
            'Shaft_Stress_MPa': tau_shaft / 1e6,
            'Bearing_Load_N': F_bearing,
            'Safety_Factor': safety_factor,
            'Rated_Torque_Nm': T_rated,
            'Current_Torque_Nm': torque
        }

    def calculate_efficiency(self, losses: Dict) -> float:
        """Calculate generator efficiency"""
        P_out = self.params.Sn * self.params.cos_phi_n
        efficiency = P_out / (P_out + losses['Total']) * 100
        return efficiency


def print_example_7_3_solution():
    """Print complete Example 7.3 solution"""
    params = GeneratorParameters()
    model = SynchronousGeneratorModel(params)
    results = model.calculate_parameters()

    print("=" * 70)
    print("EXAMPLE 7.3 - SALIENT-POLE SYNCHRONOUS GENERATOR SOLUTION")
    print("=" * 70)
    print()

    print("GIVEN DATA:")
    print("-" * 70)
    print(f"Apparent Power Sn          : {params.Sn/1000:.1f} kVA")
    print(f"Line Voltage V1Ln          : {params.V1Ln:.1f} V")
    print(f"Frequency fn               : {params.fn:.1f} Hz")
    print(f"Speed nn                   : {params.nn:.1f} rpm")
    print(f"Power Factor cos φn        : {params.cos_phi_n:.2f}")
    print(f"\nTest Voltage Vs            : {params.Vs_test:.1f} V")
    print(f"Maximum Test Current Imax  : {params.Imax:.2f} A")
    print(f"Minimum Test Current Imin  : {params.Imin:.2f} A")
    print(f"Field Resistance @ 20°C    : {params.Rf_20C:.2f} Ω")
    print(f"Field Current at No Load   : {params.If0:.2f} A")
    print(f"Operating Temperature      : {params.temp_field:.1f} °C")

    print()
    print("=" * 70)
    print("SOLUTION:")
    print("=" * 70)
    print()

    print("(a) SYNCHRONOUS REACTANCES (from slip test):")
    print("-" * 70)
    print(f"d-axis reactance Xsd = Vs / Imin")
    print(f"Xsd = {params.Vs_test:.1f} / {params.Imin:.2f}")
    print(f"Xsd = {results['Xsd']:.3f} Ω")
    print()
    print(f"q-axis reactance Xsq = Vs / Imax")
    print(f"Xsq = {params.Vs_test:.1f} / {params.Imax:.2f}")
    print(f"Xsq = {results['Xsq']:.3f} Ω")
    print()

    print("(b) NOMINAL FIELD EXCITATION CURRENT:")
    print("-" * 70)
    print(f"Phase Voltage V1n          : {results['V1n_phase']:.2f} V")
    print(f"Nominal Current In         : {results['In']:.2f} A")
    print(f"d-axis current Id          : {results['Id']:.2f} A")
    print(f"q-axis current Iq          : {results['Iq']:.2f} A")
    print(f"Excitation Voltage Ef      : {results['Ef']:.2f} V")
    print(f"\nUsing linear magnetization curve:")
    print(f"Ifn / If0 = Ef / V1n")
    print(f"Ifn = {params.If0:.2f} × ({results['Ef']:.2f} / {results['V1n_phase']:.2f})")
    print(f"Ifn = {results['Ifn']:.3f} A")
    print()

    print("(c) FIELD VOLTAGE AT OPERATING TEMPERATURE:")
    print("-" * 70)
    alpha = 0.00393
    print(f"Temperature coefficient α  : {alpha:.5f} /°C")
    print(f"Rf({params.temp_field}°C) = Rf(20°C) × [1 + α(T - 20)]")
    print(f"Rf({params.temp_field}°C) = {params.Rf_20C:.2f} × [1 + {alpha:.5f} × {params.temp_field - 20}]")
    print(f"Rf({params.temp_field}°C) = {results['Rf_temp']:.4f} Ω")
    print()
    print(f"Field Voltage Vfn = Ifn × Rf")
    print(f"Vfn = {results['Ifn']:.3f} × {results['Rf_temp']:.4f}")
    print(f"Vfn = {results['Vfn']:.3f} V")
    print()

    print("=" * 70)
    print("FINAL ANSWERS:")
    print("=" * 70)
    print(f"(a) Xsd = {results['Xsd']:.3f} Ω,  Xsq = {results['Xsq']:.3f} Ω")
    print(f"(b) Ifn = {results['Ifn']:.3f} A")
    print(f"(c) Vfn = {results['Vfn']:.3f} V @ {params.temp_field}°C")
    print("=" * 70)
    print()

    # Additional analysis
    losses = model.calculate_losses(results)
    thermal = model.thermal_model(losses)
    T_rated = params.Sn / (2 * np.pi * params.nn / 60)
    mechanical = model.mechanical_stress_analysis(T_rated)
    efficiency = model.calculate_efficiency(losses)

    print()
    print("=" * 70)
    print("ADDITIONAL ANALYSIS:")
    print("=" * 70)
    print()

    print("LOSS BREAKDOWN:")
    print("-" * 70)
    for key, value in losses.items():
        print(f"{key:20s}: {value:8.2f} W")
    print(f"\nEfficiency              : {efficiency:.2f} %")

    print()
    print("THERMAL ANALYSIS:")
    print("-" * 70)
    for key, value in thermal.items():
        if 'Temp' in key or 'Max' in key:
            print(f"{key:20s}: {value:8.2f} °C")
        else:
            print(f"{key:20s}: {value:8.4f}")

    print()
    print("MECHANICAL ANALYSIS:")
    print("-" * 70)
    for key, value in mechanical.items():
        print(f"{key:20s}: {value:10.2f}")

    return results, losses, thermal, mechanical


if __name__ == "__main__":
    print_example_7_3_solution()
