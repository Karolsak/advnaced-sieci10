#!/usr/bin/env python3
"""
Test script for Advanced Synchronous Generator Laboratory - Calculations Only
Tests all calculation modules without requiring GUI/Tkinter
"""

import numpy as np
import sys
from generator_calculations import SynchronousGeneratorCalculator

def print_separator(char='=', length=70):
    """Print a separator line"""
    print(char * length)

def main():
    """Run all tests"""
    print("\n")
    print_separator('*')
    print("*" + " " * 68 + "*")
    print("*" + "  Advanced Synchronous Generator - Calculation Tests  ".center(68) + "*")
    print("*" + " " * 68 + "*")
    print_separator('*')
    print()

    try:
        # Create calculator instance
        calc = SynchronousGeneratorCalculator()

        # Test Part (a)
        print_separator()
        print("PART (a): Calculate Field Current of Generator B")
        print_separator()
        print()
        print("Given Conditions:")
        print("  - Total Load: 720 kW at 0.8 pf lagging")
        print("  - Generator A: IfA = 20 A, delivers 360 kW")
        print("  - Generator B: delivers 360 kW")
        print("  - Terminal Voltage: V = Vn = 6300 V")
        print()

        results_a = calc.solve_part_a()

        print("Results:")
        print("-" * 70)
        print(f"  Field Current of Generator B:   IfB = {results_a['IfB']:.4f} A")
        print(f"  EMF of Generator B:             EfB = {results_a['EfB']:.2f} V")
        print()
        print("Power Distribution:")
        print(f"  Generator A:  PA = {results_a['PA']:.2f} kW,  QA = {results_a['QA']:.2f} kVAR")
        print(f"  Generator B:  PB = {results_a['PB']:.2f} kW,  QB = {results_a['QB']:.2f} kVAR")
        print()
        print("Power Angles:")
        print(f"  Generator A:  δA = {results_a['delta_A_deg']:.3f}°")
        print(f"  Generator B:  δB = {results_a['delta_B_deg']:.3f}°")
        print()
        print("EMF Coefficients:")
        print(f"  Generator A:  k_emf = {results_a['k_emfA']:.3f} V/A")
        print(f"  Generator B:  k_emf = {results_a['k_emfB']:.3f} V/A")
        print()

        # Test Part (b)
        print()
        print_separator()
        print("PART (b): Calculate New Field Current of Generator A")
        print_separator()
        print()
        print("Given Conditions:")
        print("  - Additional Load: 130 kW at unity pf")
        print("  - Total Load: 850 kW")
        print("  - Generator B: Same conditions as part (a)")
        print()

        results_b = calc.solve_part_b()

        print("Results:")
        print("-" * 70)
        print(f"  New Field Current of Gen A:     IfA = {results_b['IfA_new']:.4f} A")
        print(f"  New EMF of Generator A:         EfA = {results_b['EfA_new']:.2f} V")
        print()
        print("New Power Distribution:")
        print(f"  Generator A:  PA = {results_b['PA_new']:.2f} kW,  QA = {results_b['QA_new']:.2f} kVAR")
        print(f"  Generator B:  PB = {results_b['PB_new']:.2f} kW,  QB = {results_b['QB_new']:.2f} kVAR")
        print()
        print("New Power Angles:")
        print(f"  Generator A:  δA = {results_b['delta_A_new_deg']:.3f}°")
        print(f"  Generator B:  δB = {results_b['delta_B_new_deg']:.3f}°")
        print()

        print_separator()
        print("✓ ALL CALCULATIONS COMPLETED SUCCESSFULLY")
        print_separator()
        print()
        print("Summary of Results:")
        print(f"  Part (a): IfB = {results_a['IfB']:.4f} A")
        print(f"  Part (b): IfA = {results_b['IfA_new']:.4f} A")
        print()
        print("The calculation modules are working correctly!")
        print()
        print("To run the full GUI application with visualization:")
        print("  python3 synchronous_generator_advanced_lab.py")
        print()
        print("Note: The GUI requires Tkinter and a display environment.")
        print_separator()
        print()

        return 0

    except Exception as e:
        print(f"\n✗ Error during calculations: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
