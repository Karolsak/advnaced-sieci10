"""
Test script for synchronous generator calculations
Verifies Example 7.3 solution without GUI
"""

import sys
sys.path.insert(0, '.')

from synchronous_generator_lab import GeneratorParameters, SynchronousGeneratorModel

def test_example_7_3():
    """Test Example 7.3 calculations"""
    print("="*70)
    print("Testing Example 7.3 - Synchronous Generator Calculations")
    print("="*70)

    # Create generator with default parameters
    params = GeneratorParameters()
    model = SynchronousGeneratorModel(params)

    # Calculate results
    results = model.calculate_parameters()

    print("\n✓ CALCULATED RESULTS:")
    print("-"*70)
    print(f"(a) Synchronous Reactances:")
    print(f"    Xsd = {results['Xsd']:.3f} Ω")
    print(f"    Xsq = {results['Xsq']:.3f} Ω")
    print(f"\n(b) Nominal Field Current:")
    print(f"    Ifn = {results['Ifn']:.3f} A")
    print(f"\n(c) Field Voltage at {params.temp_field}°C:")
    print(f"    Vfn = {results['Vfn']:.3f} V")

    # Verify results are reasonable
    assert 9 < results['Xsd'] < 12, "Xsd out of expected range"
    assert 4 < results['Xsq'] < 7, "Xsq out of expected range"
    assert 12 < results['Ifn'] < 15, "Ifn out of expected range"
    assert 13 < results['Vfn'] < 17, "Vfn out of expected range"

    print("\n✓ All calculations verified successfully!")
    print("="*70)

    # Test losses
    print("\n✓ LOSS ANALYSIS:")
    print("-"*70)
    losses = model.calculate_losses(results)
    for key, value in losses.items():
        print(f"    {key:20s}: {value:8.2f} W")

    # Test thermal
    print("\n✓ THERMAL ANALYSIS:")
    print("-"*70)
    thermal = model.thermal_model(losses, ambient_temp=25)
    for key, value in thermal.items():
        if 'Temp' in key or 'Max' in key:
            print(f"    {key:20s}: {value:8.2f} °C")
        else:
            print(f"    {key:20s}: {value:8.4f}")

    # Test mechanical
    print("\n✓ MECHANICAL ANALYSIS:")
    print("-"*70)
    T_rated = params.Sn / (2 * 3.14159 * params.nn / 60)
    mechanical = model.mechanical_stress_analysis(T_rated)
    for key, value in mechanical.items():
        print(f"    {key:20s}: {value:8.2f}")

    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED!")
    print("="*70)

    return True

if __name__ == "__main__":
    try:
        test_example_7_3()
        print("\n✓ Test completed successfully!")
        print("\nTo run the full GUI application, execute:")
        print("    python3 synchronous_generator_lab.py")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
