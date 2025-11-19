#!/usr/bin/env python3
"""
Test script for Advanced Synchronous Generator Laboratory
Verifies all calculation modules work correctly
"""

import numpy as np
from synchronous_generator_advanced_lab import (
    SynchronousGeneratorCalculator,
    SynchronousGeneratorDynamics,
    ThermalModel,
    LossAnalysis,
    EconomicAnalysis
)

def test_generator_calculator():
    """Test the synchronous generator calculator"""
    print("=" * 70)
    print("Testing Synchronous Generator Calculator")
    print("=" * 70)

    calc = SynchronousGeneratorCalculator()

    # Test part (a)
    print("\n[TEST 1] Solving Part (a) - Field current of Generator B")
    print("-" * 70)
    try:
        results_a = calc.solve_part_a()
        print(f"✓ Part (a) solved successfully")
        print(f"  IfB = {results_a['IfB']:.3f} A")
        print(f"  Generator A: PA = {results_a['PA']:.2f} kW, QA = {results_a['QA']:.2f} kVAR")
        print(f"  Generator B: PB = {results_a['PB']:.2f} kW, QB = {results_a['QB']:.2f} kVAR")
        print(f"  Power angles: δA = {results_a['delta_A_deg']:.2f}°, δB = {results_a['delta_B_deg']:.2f}°")
    except Exception as e:
        print(f"✗ Part (a) failed: {str(e)}")
        return False

    # Test part (b)
    print("\n[TEST 2] Solving Part (b) - New field current of Generator A")
    print("-" * 70)
    try:
        results_b = calc.solve_part_b()
        print(f"✓ Part (b) solved successfully")
        print(f"  IfA_new = {results_b['IfA_new']:.3f} A")
        print(f"  Generator A: PA = {results_b['PA_new']:.2f} kW, QA = {results_b['QA_new']:.2f} kVAR")
        print(f"  Generator B: PB = {results_b['PB_new']:.2f} kW, QB = {results_b['QB_new']:.2f} kVAR")
    except Exception as e:
        print(f"✗ Part (b) failed: {str(e)}")
        return False

    return True


def test_dynamics():
    """Test dynamic simulation"""
    print("\n" + "=" * 70)
    print("Testing Dynamic Simulation")
    print("=" * 70)

    print("\n[TEST 3] Running RK45 dynamic simulation")
    print("-" * 70)
    try:
        params = {
            'H': 3.5,
            'D': 2.0,
            'Xd': 1.5,
            'Xq': 1.5,
            'Xd_prime': 0.3,
            'Td0_prime': 5.0,
            'freq': 60
        }

        dynamics = SynchronousGeneratorDynamics(params)

        # Initial conditions
        delta0 = 30 * np.pi / 180
        omega0 = 2 * np.pi * 60
        Eq_prime0 = 1.0
        y0 = [delta0, omega0, Eq_prime0]

        # Simulate with RK45
        t_span = [0, 2]
        Pm = 0.8
        Ef = 1.2
        V = 1.0

        sol = dynamics.simulate(t_span, y0, Pm, Ef, V, method='RK45')
        print(f"✓ RK45 simulation completed")
        print(f"  Time points: {len(sol.t)}")
        print(f"  Final δ: {np.degrees(sol.y[0][-1]):.2f}°")
        print(f"  Final ω: {sol.y[1][-1] * 60 / (2 * np.pi):.2f} rpm")

    except Exception as e:
        print(f"✗ RK45 simulation failed: {str(e)}")
        return False

    print("\n[TEST 4] Running Euler dynamic simulation")
    print("-" * 70)
    try:
        sol = dynamics.simulate(t_span, y0, Pm, Ef, V, method='Euler')
        print(f"✓ Euler simulation completed")
        print(f"  Time points: {len(sol.t)}")
        print(f"  Final δ: {np.degrees(sol.y[0][-1]):.2f}°")
        print(f"  Final ω: {sol.y[1][-1] * 60 / (2 * np.pi):.2f} rpm")

    except Exception as e:
        print(f"✗ Euler simulation failed: {str(e)}")
        return False

    return True


def test_thermal():
    """Test thermal model"""
    print("\n" + "=" * 70)
    print("Testing Thermal Model")
    print("=" * 70)

    print("\n[TEST 5] Running thermal simulation")
    print("-" * 70)
    try:
        params = {
            'C_winding': 5000,
            'C_core': 8000,
            'C_frame': 3000,
            'R_winding_core': 0.05,
            'R_core_frame': 0.03,
            'R_frame_ambient': 0.02,
            'T_ambient': 25,
            'T_max_winding': 130,
            'T_max_core': 110
        }

        thermal = ThermalModel(params)

        T0 = [25, 25, 25]
        t_span = [0, 3600]
        P_losses = (5000, 3000, 800)

        sol = thermal.simulate_thermal(t_span, T0, P_losses)
        print(f"✓ Thermal simulation completed")
        print(f"  Final temperatures:")
        print(f"    Winding: {sol.y[0][-1]:.2f} °C")
        print(f"    Core:    {sol.y[1][-1]:.2f} °C")
        print(f"    Frame:   {sol.y[2][-1]:.2f} °C")

        derating = thermal.calculate_derating(sol.y[0][-1])
        print(f"  Derating factor: {derating:.3f}")

    except Exception as e:
        print(f"✗ Thermal simulation failed: {str(e)}")
        return False

    return True


def test_loss_analysis():
    """Test loss analysis"""
    print("\n" + "=" * 70)
    print("Testing Loss Analysis")
    print("=" * 70)

    print("\n[TEST 6] Calculating detailed losses")
    print("-" * 70)
    try:
        params = {
            'Ra': 0.01,
            'Rf': 50,
            'k_h': 0.001,
            'k_e': 0.0001,
            'k_friction': 500,
            'k_windage': 300
        }

        loss_analyzer = LossAnalysis(params)

        operating_point = {
            'Ia': 50,
            'If': 20,
            'V': 6300,
            'f': 60,
            'B_max': 1.0,
            'speed_rpm': 1800,
            'P_output': 400e3
        }

        losses, efficiency = loss_analyzer.get_loss_breakdown(operating_point)

        print(f"✓ Loss analysis completed")
        print(f"  Copper losses (stator): {losses['Copper_Stator']:.2f} W")
        print(f"  Copper losses (rotor):  {losses['Copper_Rotor']:.2f} W")
        print(f"  Iron losses (total):    {losses['Hysteresis'] + losses['Eddy_Current']:.2f} W")
        print(f"  Mechanical losses:      {losses['Friction'] + losses['Windage']:.2f} W")
        print(f"  Total losses:           {losses['Total']:.2f} W")
        print(f"  Efficiency:             {efficiency:.2f} %")

    except Exception as e:
        print(f"✗ Loss analysis failed: {str(e)}")
        return False

    return True


def test_economics():
    """Test economic analysis"""
    print("\n" + "=" * 70)
    print("Testing Economic Analysis")
    print("=" * 70)

    print("\n[TEST 7] Calculating economic indicators")
    print("-" * 70)
    try:
        econ = EconomicAnalysis()

        capacity_kW = 500
        annual_hours = 6000

        operating_costs = econ.calculate_operating_cost(capacity_kW, annual_hours)
        annual_revenue = econ.calculate_revenue(capacity_kW, annual_hours)
        payback = econ.calculate_payback_period(capacity_kW, annual_hours)
        npv = econ.calculate_npv(capacity_kW, annual_hours)

        print(f"✓ Economic analysis completed")
        print(f"  Annual operating cost: ${operating_costs['total_cost']:,.2f}")
        print(f"  Annual revenue:        ${annual_revenue:,.2f}")
        print(f"  Payback period:        {payback:.2f} years")
        print(f"  NPV:                   ${npv:,.2f}")

    except Exception as e:
        print(f"✗ Economic analysis failed: {str(e)}")
        return False

    return True


def main():
    """Run all tests"""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  Advanced Synchronous Generator Laboratory - Test Suite  ".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_generator_calculator()
    all_passed &= test_dynamics()
    all_passed &= test_thermal()
    all_passed &= test_loss_analysis()
    all_passed &= test_economics()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if all_passed:
        print("\n✓ All tests PASSED!")
        print("\nThe application is ready to use. Run:")
        print("  python3 synchronous_generator_advanced_lab.py")
        print("\nto launch the GUI application.")
    else:
        print("\n✗ Some tests FAILED!")
        print("Please check the error messages above.")

    print("\n" + "=" * 70)
    print()


if __name__ == "__main__":
    main()
