#!/usr/bin/env python3
"""
Advanced 3-Phase Wound Rotor Induction Motor Laboratory
Multi-Physics Simulation with Electromagnetic-Thermal-Mechanical Coupling
Author: Claude
Date: 2025-11-19
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.integrate import odeint, solve_ivp
from scipy.optimize import fsolve
import threading
import time
from dataclasses import dataclass
from typing import Tuple, List, Dict

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MotorParameters:
    """Motor electrical and mechanical parameters"""
    poles: int = 6
    frequency: float = 50.0  # Hz
    rated_voltage: float = 400.0  # V (line-to-line RMS)
    stator_resistance: float = 0.5  # Ohms
    rotor_resistance: float = 0.3  # Ohms
    stator_leakage: float = 0.002  # H
    rotor_leakage: float = 0.002  # H
    magnetizing_inductance: float = 0.1  # H
    moment_of_inertia: float = 1000.0  # kg-m^2
    viscous_damping: float = 0.5  # N-m-s/rad
    rated_power: float = 100000.0  # W
    efficiency: float = 0.92
    power_factor: float = 0.85

    # Thermal parameters
    thermal_resistance_stator: float = 0.15  # K/W
    thermal_resistance_rotor: float = 0.20  # K/W
    thermal_capacitance_stator: float = 5000.0  # J/K
    thermal_capacitance_rotor: float = 3000.0  # J/K
    ambient_temperature: float = 25.0  # °C
    max_temperature: float = 155.0  # °C (Class F insulation)

    # Mechanical parameters
    shaft_diameter: float = 0.08  # m
    shaft_length: float = 0.5  # m
    shaft_material_modulus: float = 200e9  # Pa (steel)
    bearing_friction: float = 10.0  # N-m


@dataclass
class SimulationState:
    """Current simulation state"""
    time: float = 0.0
    speed: float = 0.0  # rad/s
    slip: float = 1.0
    torque: float = 0.0  # N-m
    current_rms: float = 0.0  # A
    voltage_rms: float = 0.0  # V
    temperature_stator: float = 25.0  # °C
    temperature_rotor: float = 25.0  # °C
    power_input: float = 0.0  # W
    power_output: float = 0.0  # W
    efficiency: float = 0.0
    copper_loss: float = 0.0  # W
    iron_loss: float = 0.0  # W
    mechanical_loss: float = 0.0  # W
    stray_loss: float = 0.0  # W
    shaft_stress: float = 0.0  # Pa


# =============================================================================
# INDUCTION MOTOR MODEL
# =============================================================================

class InductionMotorModel:
    """Complete induction motor mathematical model"""

    def __init__(self, params: MotorParameters):
        self.params = params
        self.sync_speed = (4 * np.pi * params.frequency) / params.poles  # rad/s
        self.sync_speed_rpm = (120 * params.frequency) / params.poles

    def calculate_slip(self, speed: float) -> float:
        """Calculate slip from rotor speed"""
        return (self.sync_speed - speed) / self.sync_speed

    def calculate_speed_from_slip(self, slip: float) -> float:
        """Calculate rotor speed from slip"""
        return self.sync_speed * (1 - slip)

    def calculate_torque(self, slip: float) -> float:
        """Calculate electromagnetic torque using equivalent circuit"""
        if abs(slip) < 1e-6:
            slip = 1e-6

        p = self.params

        # Phase voltage (RMS)
        V_ph = p.rated_voltage / np.sqrt(3)

        # Equivalent circuit parameters
        R1 = p.stator_resistance
        R2 = p.rotor_resistance
        X1 = 2 * np.pi * p.frequency * p.stator_leakage
        X2 = 2 * np.pi * p.frequency * p.rotor_leakage
        Xm = 2 * np.pi * p.frequency * p.magnetizing_inductance

        # Thevenin equivalent
        Zth = 1j * Xm * (R1 + 1j * X1) / (R1 + 1j * (X1 + Xm))
        Vth = V_ph * 1j * Xm / (R1 + 1j * (X1 + Xm))
        Rth = Zth.real
        Xth = Zth.imag
        Vth_mag = abs(Vth)

        # Rotor current (referred to stator)
        Z_rotor = Rth + R2/slip + 1j * (Xth + X2)
        I2 = Vth_mag / abs(Z_rotor)

        # Torque (3-phase)
        omega_s = 2 * np.pi * p.frequency
        torque = 3 * (I2**2) * (R2/slip) / omega_s

        return torque

    def calculate_current(self, slip: float) -> float:
        """Calculate stator current (RMS)"""
        if abs(slip) < 1e-6:
            slip = 1e-6

        p = self.params
        V_ph = p.rated_voltage / np.sqrt(3)

        R1 = p.stator_resistance
        R2 = p.rotor_resistance
        X1 = 2 * np.pi * p.frequency * p.stator_leakage
        X2 = 2 * np.pi * p.frequency * p.rotor_leakage
        Xm = 2 * np.pi * p.frequency * p.magnetizing_inductance

        # Total impedance
        Z_rotor = R2/slip + 1j * X2
        Z_parallel = (1j * Xm * Z_rotor) / (1j * Xm + Z_rotor)
        Z_total = R1 + 1j * X1 + Z_parallel

        I_stator = V_ph / abs(Z_total)
        return I_stator

    def calculate_losses(self, slip: float, current: float, speed: float) -> Dict[str, float]:
        """Calculate detailed loss breakdown"""
        p = self.params

        # Copper losses (I^2 * R for 3 phases)
        copper_loss_stator = 3 * current**2 * p.stator_resistance
        copper_loss_rotor = 3 * current**2 * p.rotor_resistance * slip
        copper_loss = copper_loss_stator + copper_loss_rotor

        # Iron losses (core losses) - Steinmetz equation
        # P_iron = k_h * f * B^2 + k_e * f^2 * B^2
        # Simplified: proportional to frequency and flux density squared
        flux_density = current * 0.01  # Simplified relationship
        k_h = 50.0  # Hysteresis constant
        k_e = 0.5   # Eddy current constant
        iron_loss = k_h * p.frequency * flux_density**2 + k_e * p.frequency**2 * flux_density**2

        # Mechanical losses (friction and windage)
        # P_mech = k_f * omega^2
        mechanical_loss = p.bearing_friction * abs(speed) + 0.001 * speed**2

        # Stray load losses (approximately 1-2% of output power)
        torque = self.calculate_torque(slip)
        output_power = torque * speed
        stray_loss = 0.015 * abs(output_power)

        return {
            'copper': copper_loss,
            'copper_stator': copper_loss_stator,
            'copper_rotor': copper_loss_rotor,
            'iron': iron_loss,
            'mechanical': mechanical_loss,
            'stray': stray_loss,
            'total': copper_loss + iron_loss + mechanical_loss + stray_loss
        }

    def calculate_max_torque(self) -> Tuple[float, float]:
        """Calculate maximum torque and critical slip"""
        p = self.params

        R1 = p.stator_resistance
        R2 = p.rotor_resistance
        X1 = 2 * np.pi * p.frequency * p.stator_leakage
        X2 = 2 * np.pi * p.frequency * p.rotor_leakage
        Xm = 2 * np.pi * p.frequency * p.magnetizing_inductance

        # Thevenin equivalent
        Zth = 1j * Xm * (R1 + 1j * X1) / (R1 + 1j * (X1 + Xm))
        Rth = Zth.real
        Xth = Zth.imag

        # Critical slip
        s_max = R2 / np.sqrt(Rth**2 + (Xth + X2)**2)

        # Maximum torque
        T_max = self.calculate_torque(s_max)

        return T_max, s_max

    def calculate_shaft_stress(self, torque: float) -> float:
        """Calculate shaft torsional stress"""
        p = self.params

        # Torsional stress: τ = (T * r) / J
        # where J = π * d^4 / 32 for solid circular shaft
        radius = p.shaft_diameter / 2
        polar_moment = np.pi * p.shaft_diameter**4 / 32

        stress = abs(torque) * radius / polar_moment

        return stress


# =============================================================================
# MULTI-PHYSICS SIMULATOR
# =============================================================================

class MultiPhysicsSimulator:
    """Coupled electromagnetic-thermal-mechanical simulator"""

    def __init__(self, motor_model: InductionMotorModel):
        self.motor = motor_model
        self.state = SimulationState()
        self.history = {
            'time': [],
            'speed': [],
            'torque': [],
            'current': [],
            'temp_stator': [],
            'temp_rotor': [],
            'power_input': [],
            'power_output': [],
            'efficiency': [],
            'losses': [],
            'slip': [],
            'shaft_stress': []
        }

    def dynamics(self, t: float, y: np.ndarray, load_torque_func) -> np.ndarray:
        """
        System dynamics: coupled differential equations
        State vector y = [omega, T_stator, T_rotor]
        """
        omega = y[0]  # Rotor speed (rad/s)
        T_stator = y[1]  # Stator temperature (°C)
        T_rotor = y[2]  # Rotor temperature (°C)

        # Calculate slip
        slip = self.motor.calculate_slip(omega)
        if slip < 0:
            slip = max(slip, -0.5)
        if slip > 1:
            slip = min(slip, 1.5)

        # Electromagnetic torque
        T_em = self.motor.calculate_torque(slip)

        # Load torque
        T_load = load_torque_func(t)

        # Mechanical equation: J * dω/dt = T_em - T_load - B * ω
        p = self.motor.params
        d_omega = (T_em - T_load - p.viscous_damping * omega) / p.moment_of_inertia

        # Calculate losses for thermal model
        current = self.motor.calculate_current(slip)
        losses = self.motor.calculate_losses(slip, current, omega)

        # Thermal equations: C * dT/dt = P_loss - (T - T_amb) / R_th
        dT_stator = (losses['copper_stator'] + losses['iron'] -
                     (T_stator - p.ambient_temperature) / p.thermal_resistance_stator) / p.thermal_capacitance_stator

        dT_rotor = (losses['copper_rotor'] + losses['mechanical'] -
                    (T_rotor - p.ambient_temperature) / p.thermal_resistance_rotor) / p.thermal_capacitance_rotor

        return np.array([d_omega, dT_stator, dT_rotor])

    def euler_step(self, t: float, y: np.ndarray, dt: float, load_torque_func) -> np.ndarray:
        """Euler integration step"""
        dy = self.dynamics(t, y, load_torque_func)
        return y + dt * dy

    def rk45_step(self, t: float, y: np.ndarray, dt: float, load_torque_func) -> np.ndarray:
        """4th order Runge-Kutta step"""
        k1 = self.dynamics(t, y, load_torque_func)
        k2 = self.dynamics(t + dt/2, y + dt*k1/2, load_torque_func)
        k3 = self.dynamics(t + dt/2, y + dt*k2/2, load_torque_func)
        k4 = self.dynamics(t + dt, y + dt*k3, load_torque_func)

        return y + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)

    def simulate(self, duration: float, load_torque_func, method='RK45', dt=0.01,
                 progress_callback=None):
        """
        Run simulation

        Args:
            duration: Simulation time (seconds)
            load_torque_func: Function returning load torque at time t
            method: 'RK45' or 'Euler'
            dt: Time step for Euler method
            progress_callback: Optional callback for progress updates
        """
        # Initial conditions: [omega, T_stator, T_rotor]
        y0 = np.array([0.0, self.motor.params.ambient_temperature,
                       self.motor.params.ambient_temperature])

        # Clear history
        for key in self.history:
            self.history[key] = []

        if method == 'RK45':
            # Use scipy's RK45 solver
            t_eval = np.linspace(0, duration, int(duration/dt))
            sol = solve_ivp(
                lambda t, y: self.dynamics(t, y, load_torque_func),
                [0, duration],
                y0,
                method='RK45',
                t_eval=t_eval,
                max_step=dt
            )

            times = sol.t
            states = sol.y.T

        else:  # Euler method
            times = np.arange(0, duration, dt)
            states = [y0]

            for i, t in enumerate(times[:-1]):
                y_next = self.euler_step(t, states[-1], dt, load_torque_func)
                states.append(y_next)

                if progress_callback and i % 100 == 0:
                    progress_callback(t / duration * 100)

            states = np.array(states)

        # Process results
        for i, t in enumerate(times):
            omega = states[i, 0]
            T_stator = states[i, 1]
            T_rotor = states[i, 2]

            slip = self.motor.calculate_slip(omega)
            torque = self.motor.calculate_torque(slip)
            current = self.motor.calculate_current(slip)
            losses = self.motor.calculate_losses(slip, current, omega)

            power_input = 3 * self.motor.params.rated_voltage / np.sqrt(3) * current * 0.85
            power_output = torque * omega
            efficiency = (power_output / power_input * 100) if power_input > 0 else 0
            shaft_stress = self.motor.calculate_shaft_stress(torque)

            # Store history
            self.history['time'].append(t)
            self.history['speed'].append(omega * 60 / (2*np.pi))  # Convert to RPM
            self.history['torque'].append(torque)
            self.history['current'].append(current)
            self.history['temp_stator'].append(T_stator)
            self.history['temp_rotor'].append(T_rotor)
            self.history['power_input'].append(power_input)
            self.history['power_output'].append(power_output)
            self.history['efficiency'].append(efficiency)
            self.history['losses'].append(losses['total'])
            self.history['slip'].append(slip)
            self.history['shaft_stress'].append(shaft_stress / 1e6)  # Convert to MPa

        # Update final state
        self.state.time = times[-1]
        self.state.speed = states[-1, 0]
        self.state.slip = self.motor.calculate_slip(self.state.speed)
        self.state.torque = self.motor.calculate_torque(self.state.slip)
        self.state.temperature_stator = states[-1, 1]
        self.state.temperature_rotor = states[-1, 2]
        self.state.current_rms = self.motor.calculate_current(self.state.slip)


# =============================================================================
# PROBLEM SOLUTION
# =============================================================================

def solve_problem(params: MotorParameters):
    """
    Solve the specific problem:
    6 pole, 50 Hz, wound rotor IM with J=1000 kg-m^2
    Load: 1000 N-m for 10 sec, then no load
    Slip = 5% at 500 N-m
    Find: (a) Max torque, (b) Speed after deceleration
    """

    # Given data
    print("=" * 80)
    print("INDUCTION MOTOR PROBLEM SOLUTION")
    print("=" * 80)
    print(f"\nGiven:")
    print(f"  Poles (P) = {params.poles}")
    print(f"  Frequency (f) = {params.frequency} Hz")
    print(f"  Moment of Inertia (J) = {params.moment_of_inertia} kg-m²")
    print(f"  Load Torque = 1000 N-m for 10 seconds")
    print(f"  Slip at 500 N-m = 5%")

    # Synchronous speed
    n_s = 120 * params.frequency / params.poles
    omega_s = 2 * np.pi * n_s / 60

    print(f"\nSynchronous Speed:")
    print(f"  n_s = 120 × {params.frequency} / {params.poles} = {n_s} RPM")
    print(f"  ω_s = {omega_s:.4f} rad/s")

    # Find motor parameters from given slip-torque point
    # At s=0.05, T=500 N-m
    # Using simplified torque equation: T = K * s (for small slip)
    # We need to find rotor resistance to match this

    # Adjust rotor resistance to match the given operating point
    target_slip = 0.05
    target_torque = 500.0

    # Create motor model
    motor = InductionMotorModel(params)

    # Adjust rotor resistance iteratively
    def torque_error(R2):
        params.rotor_resistance = R2
        motor_temp = InductionMotorModel(params)
        T_calc = motor_temp.calculate_torque(target_slip)
        return T_calc - target_torque

    from scipy.optimize import fsolve
    R2_optimal = fsolve(torque_error, params.rotor_resistance)[0]
    params.rotor_resistance = R2_optimal

    # Recreate motor with optimized parameters
    motor = InductionMotorModel(params)

    print(f"\nOptimized rotor resistance: R2 = {R2_optimal:.4f} Ω")

    # (a) Calculate maximum torque
    T_max, s_max = motor.calculate_max_torque()

    print(f"\n(a) MAXIMUM TORQUE:")
    print(f"  Critical Slip (s_max) = {s_max:.4f}")
    print(f"  Maximum Torque (T_max) = {T_max:.2f} N-m")

    # (b) Speed at end of deceleration period
    # The motor is loaded with 1000 N-m for 10 seconds
    # Need to find steady-state slip at T=1000 N-m

    def find_slip_for_torque(T_target):
        """Find slip that produces target torque"""
        def error(s):
            return motor.calculate_torque(s) - T_target

        # Search between 0 and s_max
        s_result = fsolve(error, 0.1)[0]
        return s_result

    # At T_load = 1000 N-m
    s_load = find_slip_for_torque(1000.0)
    n_load = n_s * (1 - s_load)
    omega_load = omega_s * (1 - s_load)

    print(f"\n(b) SPEED AT END OF DECELERATION (Under 1000 N-m load):")
    print(f"  Slip = {s_load:.4f} ({s_load*100:.2f}%)")
    print(f"  Speed = {n_load:.2f} RPM")
    print(f"  Speed = {omega_load:.4f} rad/s")

    # Dynamic analysis
    print(f"\nDYNAMIC ANALYSIS:")
    print(f"  During acceleration (0-10s with 1000 N-m load):")
    print(f"    Motor torque must overcome load + inertia")
    print(f"    At steady state: T_motor = T_load = 1000 N-m")

    # Additional calculations
    I_load = motor.calculate_current(s_load)
    losses = motor.calculate_losses(s_load, I_load, omega_load)
    P_out = 1000.0 * omega_load
    P_in = P_out + losses['total']
    eff = P_out / P_in * 100

    print(f"\n  Electrical Parameters at 1000 N-m:")
    print(f"    Stator Current = {I_load:.2f} A (RMS)")
    print(f"    Input Power = {P_in/1000:.2f} kW")
    print(f"    Output Power = {P_out/1000:.2f} kW")
    print(f"    Efficiency = {eff:.2f}%")
    print(f"\n  Loss Breakdown:")
    print(f"    Copper Losses = {losses['copper']:.2f} W")
    print(f"      - Stator = {losses['copper_stator']:.2f} W")
    print(f"      - Rotor = {losses['copper_rotor']:.2f} W")
    print(f"    Iron Losses = {losses['iron']:.2f} W")
    print(f"    Mechanical Losses = {losses['mechanical']:.2f} W")
    print(f"    Stray Losses = {losses['stray']:.2f} W")
    print(f"    Total Losses = {losses['total']:.2f} W")

    print("\n" + "=" * 80)

    return {
        'T_max': T_max,
        's_max': s_max,
        's_load': s_load,
        'n_load': n_load,
        'omega_load': omega_load,
        'current': I_load,
        'efficiency': eff,
        'losses': losses
    }


# =============================================================================
# GUI APPLICATION
# =============================================================================

class InductionMotorLab(tk.Tk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.title("Advanced Induction Motor Laboratory - Multi-Physics Simulation")
        self.geometry("1400x900")

        # Initialize parameters
        self.params = MotorParameters()
        self.motor_model = InductionMotorModel(self.params)
        self.simulator = MultiPhysicsSimulator(self.motor_model)

        # Simulation control
        self.is_running = False
        self.sim_thread = None

        # Setup GUI
        self.setup_ui()

        # Bind resize event
        self.bind('<Configure>', self.on_resize)

        # Initial problem solution
        self.solve_initial_problem()

    def setup_ui(self):
        """Create all UI elements"""

        # Main container
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Controls
        left_panel = ttk.Frame(main_container, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_panel.pack_propagate(False)

        # Right panel: Tabs
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Setup left panel
        self.setup_control_panel(left_panel)

        # Setup right panel with tabs
        self.setup_tabs(right_panel)

    def setup_control_panel(self, parent):
        """Setup control panel with parameters and buttons"""

        # Title
        title = ttk.Label(parent, text="Motor Parameters", font=('Arial', 12, 'bold'))
        title.pack(pady=10)

        # Scrollable frame for parameters
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Parameter sliders
        self.sliders = {}

        param_config = [
            ('Poles', 'poles', 2, 12, 2),
            ('Frequency (Hz)', 'frequency', 10, 100, 50),
            ('Rated Voltage (V)', 'rated_voltage', 100, 1000, 400),
            ('Stator Resistance (Ω)', 'stator_resistance', 0.1, 5.0, 0.5),
            ('Rotor Resistance (Ω)', 'rotor_resistance', 0.1, 5.0, 0.3),
            ('Moment of Inertia (kg-m²)', 'moment_of_inertia', 100, 5000, 1000),
            ('Rated Power (kW)', 'rated_power', 10, 500, 100),
            ('Ambient Temp (°C)', 'ambient_temperature', 0, 50, 25),
            ('Max Temp (°C)', 'max_temperature', 100, 200, 155),
            ('Bearing Friction (N-m)', 'bearing_friction', 1, 50, 10),
        ]

        for label, attr, min_val, max_val, default in param_config:
            frame = ttk.LabelFrame(scrollable_frame, text=label, padding=5)
            frame.pack(fill=tk.X, padx=5, pady=3)

            var = tk.DoubleVar(value=default)
            slider = ttk.Scale(frame, from_=min_val, to=max_val,
                              variable=var, orient=tk.HORIZONTAL)
            slider.pack(fill=tk.X)

            value_label = ttk.Label(frame, textvariable=var)
            value_label.pack()

            self.sliders[attr] = (var, slider, value_label)

            # Update parameter on change
            var.trace('w', lambda *args, a=attr, v=var: self.update_parameter(a, v))

        # Control buttons frame
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)

        # Start button
        self.start_btn = ttk.Button(btn_frame, text="▶ Start",
                                     command=self.start_simulation)
        self.start_btn.pack(fill=tk.X, pady=2)

        # Stop button
        self.stop_btn = ttk.Button(btn_frame, text="⬛ Stop",
                                    command=self.stop_simulation, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)

        # Reset button
        self.reset_btn = ttk.Button(btn_frame, text="↻ Reset",
                                     command=self.reset_simulation)
        self.reset_btn.pack(fill=tk.X, pady=2)

        # Solver selection
        solver_frame = ttk.LabelFrame(scrollable_frame, text="Solver Settings", padding=5)
        solver_frame.pack(fill=tk.X, padx=5, pady=5)

        self.solver_var = tk.StringVar(value="RK45")
        ttk.Radiobutton(solver_frame, text="RK45 (Adaptive)",
                       variable=self.solver_var, value="RK45").pack(anchor=tk.W)
        ttk.Radiobutton(solver_frame, text="Euler (Fixed Step)",
                       variable=self.solver_var, value="Euler").pack(anchor=tk.W)

        ttk.Label(solver_frame, text="Time Step (s):").pack(anchor=tk.W)
        self.dt_var = tk.DoubleVar(value=0.01)
        ttk.Scale(solver_frame, from_=0.001, to=0.1,
                 variable=self.dt_var, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(solver_frame, textvariable=self.dt_var).pack()

        ttk.Label(solver_frame, text="Duration (s):").pack(anchor=tk.W)
        self.duration_var = tk.DoubleVar(value=20.0)
        ttk.Scale(solver_frame, from_=1, to=100,
                 variable=self.duration_var, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(solver_frame, textvariable=self.duration_var).pack()

        # Load profile
        load_frame = ttk.LabelFrame(scrollable_frame, text="Load Profile", padding=5)
        load_frame.pack(fill=tk.X, padx=5, pady=5)

        self.load_type = tk.StringVar(value="step")
        ttk.Radiobutton(load_frame, text="Step Load (1000 N-m for 10s)",
                       variable=self.load_type, value="step").pack(anchor=tk.W)
        ttk.Radiobutton(load_frame, text="Constant Load",
                       variable=self.load_type, value="constant").pack(anchor=tk.W)
        ttk.Radiobutton(load_frame, text="Ramp Load",
                       variable=self.load_type, value="ramp").pack(anchor=tk.W)
        ttk.Radiobutton(load_frame, text="Sinusoidal Load",
                       variable=self.load_type, value="sinusoidal").pack(anchor=tk.W)

        ttk.Label(load_frame, text="Load Amplitude (N-m):").pack(anchor=tk.W)
        self.load_amplitude = tk.DoubleVar(value=1000.0)
        ttk.Scale(load_frame, from_=0, to=5000,
                 variable=self.load_amplitude, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(load_frame, textvariable=self.load_amplitude).pack()

    def setup_tabs(self, parent):
        """Setup tabbed interface"""

        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Dynamic Simulation
        self.setup_simulation_tab()

        # Tab 2: Steady-State Analysis
        self.setup_steady_state_tab()

        # Tab 3: Thermal Analysis
        self.setup_thermal_tab()

        # Tab 4: Loss Analysis
        self.setup_loss_tab()

        # Tab 5: Economic Analysis
        self.setup_economic_tab()

        # Tab 6: Results & Reports
        self.setup_results_tab()

    def setup_simulation_tab(self):
        """Setup dynamic simulation tab"""

        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dynamic Simulation")

        # Create figure with subplots
        self.sim_fig = Figure(figsize=(10, 8))

        self.ax_speed = self.sim_fig.add_subplot(3, 2, 1)
        self.ax_torque = self.sim_fig.add_subplot(3, 2, 2)
        self.ax_current = self.sim_fig.add_subplot(3, 2, 3)
        self.ax_power = self.sim_fig.add_subplot(3, 2, 4)
        self.ax_temp = self.sim_fig.add_subplot(3, 2, 5)
        self.ax_efficiency = self.sim_fig.add_subplot(3, 2, 6)

        self.sim_fig.tight_layout(pad=3.0)

        # Create canvas
        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, tab)
        self.sim_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_steady_state_tab(self):
        """Setup steady-state characteristics tab"""

        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Steady-State Characteristics")

        # Create figure
        self.ss_fig = Figure(figsize=(10, 8))

        self.ax_torque_speed = self.ss_fig.add_subplot(2, 2, 1)
        self.ax_current_speed = self.ss_fig.add_subplot(2, 2, 2)
        self.ax_power_speed = self.ss_fig.add_subplot(2, 2, 3)
        self.ax_eff_speed = self.ss_fig.add_subplot(2, 2, 4)

        self.ss_fig.tight_layout(pad=3.0)

        # Create canvas
        self.ss_canvas = FigureCanvasTkAgg(self.ss_fig, tab)
        self.ss_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Plot steady-state characteristics
        self.plot_steady_state()

    def setup_thermal_tab(self):
        """Setup thermal analysis tab"""

        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Thermal Analysis")

        # Create figure
        self.thermal_fig = Figure(figsize=(10, 8))

        self.ax_thermal_map = self.thermal_fig.add_subplot(2, 2, 1)
        self.ax_temp_time = self.thermal_fig.add_subplot(2, 2, 2)
        self.ax_derating = self.thermal_fig.add_subplot(2, 2, 3)
        self.ax_hotspot = self.thermal_fig.add_subplot(2, 2, 4)

        self.thermal_fig.tight_layout(pad=3.0)

        # Create canvas
        self.thermal_canvas = FigureCanvasTkAgg(self.thermal_fig, tab)
        self.thermal_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_loss_tab(self):
        """Setup loss analysis tab"""

        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Loss Analysis")

        # Create figure
        self.loss_fig = Figure(figsize=(10, 8))

        self.ax_loss_pie = self.loss_fig.add_subplot(2, 2, 1)
        self.ax_loss_bar = self.loss_fig.add_subplot(2, 2, 2)
        self.ax_loss_time = self.loss_fig.add_subplot(2, 2, 3)
        self.ax_stress = self.loss_fig.add_subplot(2, 2, 4)

        self.loss_fig.tight_layout(pad=3.0)

        # Create canvas
        self.loss_canvas = FigureCanvasTkAgg(self.loss_fig, tab)
        self.loss_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_economic_tab(self):
        """Setup economic analysis tab"""

        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Economic Analysis")

        # Create frames
        input_frame = ttk.LabelFrame(tab, text="Economic Parameters", padding=10)
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        results_frame = ttk.LabelFrame(tab, text="Economic Results", padding=10)
        results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Economic parameters
        self.econ_params = {}

        econ_config = [
            ('Electricity Cost ($/kWh)', 'electricity_cost', 0.12),
            ('Operating Hours/Year', 'operating_hours', 8760),
            ('Motor Cost ($)', 'motor_cost', 15000),
            ('Maintenance Cost/Year ($)', 'maintenance_cost', 1000),
            ('Interest Rate (%)', 'interest_rate', 5),
            ('Lifetime (years)', 'lifetime', 15),
        ]

        for label, key, default in econ_config:
            frame = ttk.Frame(input_frame)
            frame.pack(fill=tk.X, pady=5)

            ttk.Label(frame, text=label + ":").pack(side=tk.LEFT)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=15)
            entry.pack(side=tk.RIGHT)

            self.econ_params[key] = var

        # Calculate button
        ttk.Button(input_frame, text="Calculate Economics",
                  command=self.calculate_economics).pack(pady=10)

        # Results text
        self.econ_text = tk.Text(results_frame, wrap=tk.WORD, height=20)
        self.econ_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(results_frame, command=self.econ_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.econ_text.config(yscrollcommand=scrollbar.set)

    def setup_results_tab(self):
        """Setup results and reports tab"""

        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Results & Reports")

        # Results text area
        self.results_text = tk.Text(tab, wrap=tk.WORD, font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tab, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(btn_frame, text="Generate Report",
                  command=self.generate_report).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Export Data",
                  command=self.export_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear",
                  command=lambda: self.results_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)

    def update_parameter(self, attr, var):
        """Update motor parameter"""
        value = var.get()
        setattr(self.params, attr, value)

        # Recreate models
        self.motor_model = InductionMotorModel(self.params)
        self.simulator = MultiPhysicsSimulator(self.motor_model)

        # Update steady-state plots
        self.plot_steady_state()

    def get_load_torque_function(self):
        """Create load torque function based on selection"""

        load_type = self.load_type.get()
        amplitude = self.load_amplitude.get()

        if load_type == "step":
            # 1000 N-m for 10 seconds, then no load
            def load_func(t):
                return amplitude if t <= 10.0 else 0.0
        elif load_type == "constant":
            def load_func(t):
                return amplitude
        elif load_type == "ramp":
            def load_func(t):
                return min(amplitude, amplitude * t / 10.0)
        elif load_type == "sinusoidal":
            def load_func(t):
                return amplitude * (1 + 0.5 * np.sin(2 * np.pi * 0.1 * t)) / 2
        else:
            def load_func(t):
                return 0.0

        return load_func

    def start_simulation(self):
        """Start simulation in background thread"""

        if self.is_running:
            return

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # Run simulation in thread
        self.sim_thread = threading.Thread(target=self.run_simulation)
        self.sim_thread.start()

    def stop_simulation(self):
        """Stop simulation"""

        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def reset_simulation(self):
        """Reset simulation"""

        self.stop_simulation()

        # Clear history
        self.simulator = MultiPhysicsSimulator(self.motor_model)

        # Clear plots
        self.clear_dynamic_plots()

    def run_simulation(self):
        """Run simulation (called in thread)"""

        try:
            duration = self.duration_var.get()
            method = self.solver_var.get()
            dt = self.dt_var.get()
            load_func = self.get_load_torque_function()

            # Run simulation
            self.simulator.simulate(duration, load_func, method=method, dt=dt)

            # Update plots
            self.after(0, self.update_dynamic_plots)
            self.after(0, self.update_thermal_plots)
            self.after(0, self.update_loss_plots)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Simulation Error", str(e)))

        finally:
            self.is_running = False
            self.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def clear_dynamic_plots(self):
        """Clear dynamic simulation plots"""

        for ax in [self.ax_speed, self.ax_torque, self.ax_current,
                   self.ax_power, self.ax_temp, self.ax_efficiency]:
            ax.clear()

        self.sim_canvas.draw()

    def update_dynamic_plots(self):
        """Update dynamic simulation plots"""

        h = self.simulator.history

        if len(h['time']) == 0:
            return

        # Speed vs time
        self.ax_speed.clear()
        self.ax_speed.plot(h['time'], h['speed'], 'b-', linewidth=2)
        self.ax_speed.set_xlabel('Time (s)')
        self.ax_speed.set_ylabel('Speed (RPM)')
        self.ax_speed.set_title('Rotor Speed')
        self.ax_speed.grid(True, alpha=0.3)

        # Torque vs time
        self.ax_torque.clear()
        self.ax_torque.plot(h['time'], h['torque'], 'r-', linewidth=2)
        self.ax_torque.set_xlabel('Time (s)')
        self.ax_torque.set_ylabel('Torque (N-m)')
        self.ax_torque.set_title('Electromagnetic Torque')
        self.ax_torque.grid(True, alpha=0.3)

        # Current vs time
        self.ax_current.clear()
        self.ax_current.plot(h['time'], h['current'], 'g-', linewidth=2)
        self.ax_current.set_xlabel('Time (s)')
        self.ax_current.set_ylabel('Current (A RMS)')
        self.ax_current.set_title('Stator Current')
        self.ax_current.grid(True, alpha=0.3)

        # Power vs time
        self.ax_power.clear()
        self.ax_power.plot(h['time'], np.array(h['power_input'])/1000, 'b-',
                          linewidth=2, label='Input')
        self.ax_power.plot(h['time'], np.array(h['power_output'])/1000, 'r-',
                          linewidth=2, label='Output')
        self.ax_power.set_xlabel('Time (s)')
        self.ax_power.set_ylabel('Power (kW)')
        self.ax_power.set_title('Power')
        self.ax_power.legend()
        self.ax_power.grid(True, alpha=0.3)

        # Temperature vs time
        self.ax_temp.clear()
        self.ax_temp.plot(h['time'], h['temp_stator'], 'r-',
                         linewidth=2, label='Stator')
        self.ax_temp.plot(h['time'], h['temp_rotor'], 'b-',
                         linewidth=2, label='Rotor')
        self.ax_temp.axhline(y=self.params.max_temperature, color='k',
                            linestyle='--', label='Max Temp')
        self.ax_temp.set_xlabel('Time (s)')
        self.ax_temp.set_ylabel('Temperature (°C)')
        self.ax_temp.set_title('Temperature Rise')
        self.ax_temp.legend()
        self.ax_temp.grid(True, alpha=0.3)

        # Efficiency vs time
        self.ax_efficiency.clear()
        self.ax_efficiency.plot(h['time'], h['efficiency'], 'm-', linewidth=2)
        self.ax_efficiency.set_xlabel('Time (s)')
        self.ax_efficiency.set_ylabel('Efficiency (%)')
        self.ax_efficiency.set_title('Efficiency')
        self.ax_efficiency.grid(True, alpha=0.3)

        self.sim_fig.tight_layout(pad=3.0)
        self.sim_canvas.draw()

    def plot_steady_state(self):
        """Plot steady-state characteristics"""

        # Generate slip range
        slips = np.linspace(0.001, 1.0, 100)
        speeds_rpm = self.motor_model.sync_speed_rpm * (1 - slips)

        torques = []
        currents = []
        powers_in = []
        powers_out = []
        efficiencies = []

        for s in slips:
            T = self.motor_model.calculate_torque(s)
            I = self.motor_model.calculate_current(s)
            omega = self.motor_model.calculate_speed_from_slip(s)
            losses = self.motor_model.calculate_losses(s, I, omega)

            P_out = T * omega
            P_in = P_out + losses['total']
            eff = (P_out / P_in * 100) if P_in > 0 else 0

            torques.append(T)
            currents.append(I)
            powers_in.append(P_in / 1000)  # kW
            powers_out.append(P_out / 1000)  # kW
            efficiencies.append(eff)

        # Torque-speed
        self.ax_torque_speed.clear()
        self.ax_torque_speed.plot(speeds_rpm, torques, 'b-', linewidth=2)
        self.ax_torque_speed.set_xlabel('Speed (RPM)')
        self.ax_torque_speed.set_ylabel('Torque (N-m)')
        self.ax_torque_speed.set_title('Torque-Speed Characteristic')
        self.ax_torque_speed.grid(True, alpha=0.3)

        # Current-speed
        self.ax_current_speed.clear()
        self.ax_current_speed.plot(speeds_rpm, currents, 'g-', linewidth=2)
        self.ax_current_speed.set_xlabel('Speed (RPM)')
        self.ax_current_speed.set_ylabel('Current (A RMS)')
        self.ax_current_speed.set_title('Current-Speed Characteristic')
        self.ax_current_speed.grid(True, alpha=0.3)

        # Power-speed
        self.ax_power_speed.clear()
        self.ax_power_speed.plot(speeds_rpm, powers_in, 'b-', linewidth=2, label='Input')
        self.ax_power_speed.plot(speeds_rpm, powers_out, 'r-', linewidth=2, label='Output')
        self.ax_power_speed.set_xlabel('Speed (RPM)')
        self.ax_power_speed.set_ylabel('Power (kW)')
        self.ax_power_speed.set_title('Power-Speed Characteristic')
        self.ax_power_speed.legend()
        self.ax_power_speed.grid(True, alpha=0.3)

        # Efficiency-speed
        self.ax_eff_speed.clear()
        self.ax_eff_speed.plot(speeds_rpm, efficiencies, 'm-', linewidth=2)
        self.ax_eff_speed.set_xlabel('Speed (RPM)')
        self.ax_eff_speed.set_ylabel('Efficiency (%)')
        self.ax_eff_speed.set_title('Efficiency-Speed Characteristic')
        self.ax_eff_speed.grid(True, alpha=0.3)

        self.ss_fig.tight_layout(pad=3.0)
        self.ss_canvas.draw()

    def update_thermal_plots(self):
        """Update thermal analysis plots"""

        h = self.simulator.history

        if len(h['time']) == 0:
            return

        # Temperature vs time (detailed)
        self.ax_temp_time.clear()
        self.ax_temp_time.plot(h['time'], h['temp_stator'], 'r-',
                              linewidth=2, label='Stator')
        self.ax_temp_time.plot(h['time'], h['temp_rotor'], 'b-',
                              linewidth=2, label='Rotor')
        self.ax_temp_time.axhline(y=self.params.max_temperature, color='k',
                                  linestyle='--', label='Max Limit')
        self.ax_temp_time.fill_between(h['time'], 0, self.params.max_temperature,
                                       alpha=0.1, color='g', label='Safe Zone')
        self.ax_temp_time.set_xlabel('Time (s)')
        self.ax_temp_time.set_ylabel('Temperature (°C)')
        self.ax_temp_time.set_title('Temperature Rise Over Time')
        self.ax_temp_time.legend()
        self.ax_temp_time.grid(True, alpha=0.3)

        # Thermal map (simplified)
        self.ax_thermal_map.clear()
        final_temp_stator = h['temp_stator'][-1]
        final_temp_rotor = h['temp_rotor'][-1]

        components = ['Stator\nWinding', 'Rotor\nWinding', 'Bearing', 'Shaft']
        temps = [final_temp_stator, final_temp_rotor,
                self.params.ambient_temperature + 15,
                self.params.ambient_temperature + 10]
        colors = ['red' if t > self.params.max_temperature else 'orange' if t > 100 else 'green'
                 for t in temps]

        bars = self.ax_thermal_map.bar(components, temps, color=colors, alpha=0.7)
        self.ax_thermal_map.axhline(y=self.params.max_temperature, color='r',
                                    linestyle='--', linewidth=2, label='Max Temp')
        self.ax_thermal_map.set_ylabel('Temperature (°C)')
        self.ax_thermal_map.set_title('Component Temperature Distribution')
        self.ax_thermal_map.legend()
        self.ax_thermal_map.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar, temp in zip(bars, temps):
            height = bar.get_height()
            self.ax_thermal_map.text(bar.get_x() + bar.get_width()/2., height,
                                    f'{temp:.1f}°C', ha='center', va='bottom')

        # Derating curve
        self.ax_derating.clear()
        ambient_range = np.linspace(0, 60, 50)
        max_power = self.params.rated_power / 1000  # kW

        # Simple derating: 100% at 25°C, reduce by 1% per degree above
        derating_factor = np.maximum(0, 1 - 0.01 * (ambient_range - 25))
        derated_power = max_power * derating_factor

        self.ax_derating.plot(ambient_range, derated_power, 'b-', linewidth=2)
        self.ax_derating.axvline(x=self.params.ambient_temperature, color='r',
                                linestyle='--', label='Current Ambient')
        self.ax_derating.set_xlabel('Ambient Temperature (°C)')
        self.ax_derating.set_ylabel('Rated Power (kW)')
        self.ax_derating.set_title('Derating Curve')
        self.ax_derating.legend()
        self.ax_derating.grid(True, alpha=0.3)

        # Hotspot analysis
        self.ax_hotspot.clear()
        if len(h['time']) > 0:
            max_temp_overall = max(max(h['temp_stator']), max(h['temp_rotor']))
            margin = self.params.max_temperature - max_temp_overall

            labels = ['Max\nTemperature', 'Temperature\nMargin']
            values = [max_temp_overall, margin]
            colors_hotspot = ['red' if margin < 10 else 'orange' if margin < 30 else 'green',
                             'green' if margin > 30 else 'orange']

            bars = self.ax_hotspot.bar(labels, values, color=colors_hotspot, alpha=0.7)
            self.ax_hotspot.set_ylabel('Temperature (°C)')
            self.ax_hotspot.set_title('Hotspot Analysis')
            self.ax_hotspot.grid(True, alpha=0.3, axis='y')

            for bar, val in zip(bars, values):
                height = bar.get_height()
                self.ax_hotspot.text(bar.get_x() + bar.get_width()/2., height,
                                    f'{val:.1f}°C', ha='center', va='bottom')

        self.thermal_fig.tight_layout(pad=3.0)
        self.thermal_canvas.draw()

    def update_loss_plots(self):
        """Update loss analysis plots"""

        h = self.simulator.history

        if len(h['time']) == 0:
            return

        # Get final state losses
        final_slip = h['slip'][-1]
        final_current = h['current'][-1]
        final_speed = h['speed'][-1] * 2 * np.pi / 60  # Convert to rad/s

        losses = self.motor_model.calculate_losses(final_slip, final_current, final_speed)

        # Loss pie chart
        self.ax_loss_pie.clear()
        loss_labels = ['Copper\nStator', 'Copper\nRotor', 'Iron', 'Mechanical', 'Stray']
        loss_values = [losses['copper_stator'], losses['copper_rotor'],
                      losses['iron'], losses['mechanical'], losses['stray']]
        colors_pie = ['#ff9999', '#ffcc99', '#99ccff', '#99ff99', '#cc99ff']

        wedges, texts, autotexts = self.ax_loss_pie.pie(loss_values, labels=loss_labels,
                                                         colors=colors_pie, autopct='%1.1f%%',
                                                         startangle=90)
        self.ax_loss_pie.set_title('Loss Distribution (Final State)')

        # Loss bar chart
        self.ax_loss_bar.clear()
        bars = self.ax_loss_bar.bar(loss_labels, loss_values, color=colors_pie, alpha=0.7)
        self.ax_loss_bar.set_ylabel('Loss (W)')
        self.ax_loss_bar.set_title(f'Loss Breakdown (Total: {losses["total"]:.0f} W)')
        self.ax_loss_bar.grid(True, alpha=0.3, axis='y')

        for bar, val in zip(bars, loss_values):
            height = bar.get_height()
            self.ax_loss_bar.text(bar.get_x() + bar.get_width()/2., height,
                                 f'{val:.0f}W', ha='center', va='bottom')

        # Losses vs time
        self.ax_loss_time.clear()
        self.ax_loss_time.plot(h['time'], np.array(h['losses'])/1000, 'r-',
                              linewidth=2, label='Total Losses')
        self.ax_loss_time.set_xlabel('Time (s)')
        self.ax_loss_time.set_ylabel('Losses (kW)')
        self.ax_loss_time.set_title('Total Losses Over Time')
        self.ax_loss_time.legend()
        self.ax_loss_time.grid(True, alpha=0.3)

        # Shaft stress
        self.ax_stress.clear()
        self.ax_stress.plot(h['time'], h['shaft_stress'], 'b-', linewidth=2)
        self.ax_stress.set_xlabel('Time (s)')
        self.ax_stress.set_ylabel('Shaft Stress (MPa)')
        self.ax_stress.set_title('Shaft Torsional Stress')
        self.ax_stress.grid(True, alpha=0.3)

        # Add safe stress limit (typical for steel: 400 MPa yield strength)
        safe_limit = 400 * 0.5  # 50% of yield strength
        self.ax_stress.axhline(y=safe_limit, color='r', linestyle='--',
                              label=f'Safe Limit ({safe_limit:.0f} MPa)')
        self.ax_stress.legend()

        self.loss_fig.tight_layout(pad=3.0)
        self.loss_canvas.draw()

    def calculate_economics(self):
        """Calculate economic analysis"""

        # Get parameters
        elec_cost = self.econ_params['electricity_cost'].get()
        op_hours = self.econ_params['operating_hours'].get()
        motor_cost = self.econ_params['motor_cost'].get()
        maint_cost = self.econ_params['maintenance_cost'].get()
        interest = self.econ_params['interest_rate'].get() / 100
        lifetime = self.econ_params['lifetime'].get()

        # Calculate average power from simulation or use rated
        if len(self.simulator.history['power_input']) > 0:
            avg_power = np.mean(self.simulator.history['power_input']) / 1000  # kW
        else:
            avg_power = self.params.rated_power / 1000 * 0.75  # kW, assume 75% load

        # Annual energy consumption
        annual_energy = avg_power * op_hours  # kWh

        # Annual energy cost
        annual_energy_cost = annual_energy * elec_cost

        # Total annual operating cost
        annual_operating_cost = annual_energy_cost + maint_cost

        # Present value of operating costs (annuity)
        if interest > 0:
            pv_operating = annual_operating_cost * (1 - (1 + interest)**(-lifetime)) / interest
        else:
            pv_operating = annual_operating_cost * lifetime

        # Life cycle cost
        life_cycle_cost = motor_cost + pv_operating

        # Energy efficiency analysis
        if len(self.simulator.history['efficiency']) > 0:
            avg_efficiency = np.mean(self.simulator.history['efficiency'])
        else:
            avg_efficiency = self.params.efficiency * 100

        # Cost of losses
        avg_losses = avg_power * (100 - avg_efficiency) / avg_efficiency  # kW
        annual_loss_energy = avg_losses * op_hours  # kWh
        annual_loss_cost = annual_loss_energy * elec_cost

        # Format results
        results = f"""
ECONOMIC ANALYSIS RESULTS
{'=' * 70}

OPERATING PARAMETERS:
  Average Power Consumption:        {avg_power:.2f} kW
  Operating Hours per Year:         {op_hours:.0f} hours
  Motor Efficiency:                 {avg_efficiency:.2f}%
  Electricity Cost:                 ${elec_cost:.4f}/kWh
  Analysis Period:                  {lifetime:.0f} years
  Discount Rate:                    {interest*100:.2f}%

ENERGY CONSUMPTION:
  Annual Energy Consumption:        {annual_energy:.0f} kWh/year
  Lifetime Energy Consumption:      {annual_energy * lifetime:.0f} kWh

  Annual Energy in Losses:          {annual_loss_energy:.0f} kWh/year
  Lifetime Energy in Losses:        {annual_loss_energy * lifetime:.0f} kWh

COSTS:
  Motor Purchase Cost:              ${motor_cost:,.2f}

  Annual Energy Cost:               ${annual_energy_cost:,.2f}/year
  Annual Maintenance Cost:          ${maint_cost:,.2f}/year
  Annual Operating Cost:            ${annual_operating_cost:,.2f}/year

  Annual Cost of Losses:            ${annual_loss_cost:,.2f}/year

  Lifetime Operating Cost (PV):     ${pv_operating:,.2f}
  Total Life Cycle Cost:            ${life_cycle_cost:,.2f}

ECONOMIC METRICS:
  Cost per kWh Delivered:           ${life_cycle_cost / (annual_energy * lifetime):.4f}/kWh
  Payback Period (vs 100% eff):     N/A
  Energy Cost Fraction:             {annual_energy_cost / annual_operating_cost * 100:.1f}%

IMPROVEMENT POTENTIAL:
  If efficiency improved to 95%:
    Annual Energy Savings:          {annual_energy * (1 - avg_efficiency/100) * (95/avg_efficiency - 1):.0f} kWh
    Annual Cost Savings:            ${annual_energy * (1 - avg_efficiency/100) * (95/avg_efficiency - 1) * elec_cost:,.2f}
    Lifetime Savings (PV):          ${annual_energy * (1 - avg_efficiency/100) * (95/avg_efficiency - 1) * elec_cost * (1 - (1 + interest)**(-lifetime)) / interest:,.2f}

CARBON FOOTPRINT (assuming 0.5 kg CO2/kWh):
  Annual CO2 Emissions:             {annual_energy * 0.5:.0f} kg/year
  Lifetime CO2 Emissions:           {annual_energy * lifetime * 0.5:.0f} kg
  Annual CO2 from Losses:           {annual_loss_energy * 0.5:.0f} kg/year

{'=' * 70}
        """

        self.econ_text.delete(1.0, tk.END)
        self.econ_text.insert(1.0, results)

    def generate_report(self):
        """Generate comprehensive report"""

        report = f"""
{'=' * 80}
ADVANCED INDUCTION MOTOR LABORATORY - COMPREHENSIVE REPORT
{'=' * 80}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

MOTOR SPECIFICATIONS:
{'-' * 80}
  Type:                         3-Phase Wound Rotor Induction Motor
  Poles:                        {self.params.poles}
  Frequency:                    {self.params.frequency} Hz
  Rated Voltage:                {self.params.rated_voltage} V (line-to-line, RMS)
  Rated Power:                  {self.params.rated_power/1000:.2f} kW

  Synchronous Speed:            {self.motor_model.sync_speed_rpm:.2f} RPM
                                {self.motor_model.sync_speed:.4f} rad/s

  Stator Resistance:            {self.params.stator_resistance:.4f} Ω
  Rotor Resistance:             {self.params.rotor_resistance:.4f} Ω
  Stator Leakage Inductance:    {self.params.stator_leakage*1000:.2f} mH
  Rotor Leakage Inductance:     {self.params.rotor_leakage*1000:.2f} mH
  Magnetizing Inductance:       {self.params.magnetizing_inductance*1000:.2f} mH

  Moment of Inertia:            {self.params.moment_of_inertia} kg-m²
  Viscous Damping:              {self.params.viscous_damping} N-m-s/rad

MAXIMUM TORQUE ANALYSIS:
{'-' * 80}
"""

        T_max, s_max = self.motor_model.calculate_max_torque()
        n_max = self.motor_model.sync_speed_rpm * (1 - s_max)

        report += f"""  Maximum Torque:               {T_max:.2f} N-m
  Critical Slip:                {s_max:.4f} ({s_max*100:.2f}%)
  Speed at Max Torque:          {n_max:.2f} RPM

"""

        if len(self.simulator.history['time']) > 0:
            report += f"""
SIMULATION RESULTS:
{'-' * 80}
  Simulation Duration:          {self.simulator.history['time'][-1]:.2f} seconds
  Solver Method:                {self.solver_var.get()}
  Time Step:                    {self.dt_var.get():.4f} seconds

  Final State:
    Speed:                      {self.simulator.history['speed'][-1]:.2f} RPM
    Slip:                       {self.simulator.history['slip'][-1]:.4f} ({self.simulator.history['slip'][-1]*100:.2f}%)
    Torque:                     {self.simulator.history['torque'][-1]:.2f} N-m
    Current:                    {self.simulator.history['current'][-1]:.2f} A (RMS)
    Stator Temperature:         {self.simulator.history['temp_stator'][-1]:.2f} °C
    Rotor Temperature:          {self.simulator.history['temp_rotor'][-1]:.2f} °C
    Input Power:                {self.simulator.history['power_input'][-1]/1000:.2f} kW
    Output Power:               {self.simulator.history['power_output'][-1]/1000:.2f} kW
    Efficiency:                 {self.simulator.history['efficiency'][-1]:.2f}%
    Total Losses:               {self.simulator.history['losses'][-1]:.2f} W
    Shaft Stress:               {self.simulator.history['shaft_stress'][-1]:.2f} MPa

  Peak Values:
    Maximum Speed:              {max(self.simulator.history['speed']):.2f} RPM
    Maximum Torque:             {max(self.simulator.history['torque']):.2f} N-m
    Maximum Current:            {max(self.simulator.history['current']):.2f} A
    Maximum Stator Temp:        {max(self.simulator.history['temp_stator']):.2f} °C
    Maximum Rotor Temp:         {max(self.simulator.history['temp_rotor']):.2f} °C
    Maximum Shaft Stress:       {max(self.simulator.history['shaft_stress']):.2f} MPa

"""

        report += f"""
THERMAL ANALYSIS:
{'-' * 80}
  Ambient Temperature:          {self.params.ambient_temperature:.2f} °C
  Maximum Rated Temperature:    {self.params.max_temperature:.2f} °C
  Thermal Resistance (Stator):  {self.params.thermal_resistance_stator:.4f} K/W
  Thermal Resistance (Rotor):   {self.params.thermal_resistance_rotor:.4f} K/W
  Thermal Capacitance (Stator): {self.params.thermal_capacitance_stator:.0f} J/K
  Thermal Capacitance (Rotor):  {self.params.thermal_capacitance_rotor:.0f} J/K

MECHANICAL ANALYSIS:
{'-' * 80}
  Shaft Diameter:               {self.params.shaft_diameter*1000:.1f} mm
  Shaft Length:                 {self.params.shaft_length*1000:.1f} mm
  Material Modulus:             {self.params.shaft_material_modulus/1e9:.0f} GPa
  Bearing Friction:             {self.params.bearing_friction:.2f} N-m

{'=' * 80}
END OF REPORT
{'=' * 80}
        """

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, report)

        messagebox.showinfo("Report Generated",
                           "Comprehensive report has been generated in the Results tab.")

    def export_data(self):
        """Export simulation data"""

        if len(self.simulator.history['time']) == 0:
            messagebox.showwarning("No Data", "No simulation data to export. Run a simulation first.")
            return

        try:
            filename = f"motor_sim_data_{time.strftime('%Y%m%d_%H%M%S')}.csv"

            with open(filename, 'w') as f:
                # Header
                f.write("Time(s),Speed(RPM),Torque(Nm),Current(A),Power_In(W),Power_Out(W)," +
                       "Efficiency(%),Temp_Stator(C),Temp_Rotor(C),Losses(W),Slip," +
                       "Shaft_Stress(MPa)\n")

                # Data
                h = self.simulator.history
                for i in range(len(h['time'])):
                    f.write(f"{h['time'][i]:.4f}," +
                           f"{h['speed'][i]:.4f}," +
                           f"{h['torque'][i]:.4f}," +
                           f"{h['current'][i]:.4f}," +
                           f"{h['power_input'][i]:.4f}," +
                           f"{h['power_output'][i]:.4f}," +
                           f"{h['efficiency'][i]:.4f}," +
                           f"{h['temp_stator'][i]:.4f}," +
                           f"{h['temp_rotor'][i]:.4f}," +
                           f"{h['losses'][i]:.4f}," +
                           f"{h['slip'][i]:.6f}," +
                           f"{h['shaft_stress'][i]:.4f}\n")

            messagebox.showinfo("Export Successful",
                               f"Data exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting data: {str(e)}")

    def solve_initial_problem(self):
        """Solve the initial problem and display results"""

        results = solve_problem(self.params)

        # Update results tab
        problem_text = f"""
PROBLEM SOLUTION
{'=' * 80}

Given Problem:
  A 6 pole, 50 Hz, 3-φ wound rotor Induction Motor has a flywheel coupled
  to its shaft. The total moment of inertia is 1000 kg-m². Load torque is
  1000 N-m for 10 sec, followed by a no load period which is long enough
  for the motor to reach its no-load speed. Motor has a slip of 5% at a
  torque of 500 N-m.

  Find:
    (a) Maximum torque developed by motor
    (b) Speed at the end of deceleration period

SOLUTION:
{'=' * 80}

(a) MAXIMUM TORQUE:
    Maximum Torque (T_max) = {results['T_max']:.2f} N-m
    Critical Slip (s_max)  = {results['s_max']:.4f} ({results['s_max']*100:.2f}%)

(b) SPEED AT END OF DECELERATION (Under 1000 N-m load):
    Slip                   = {results['s_load']:.4f} ({results['s_load']*100:.2f}%)
    Speed                  = {results['n_load']:.2f} RPM
    Speed                  = {results['omega_load']:.4f} rad/s

Additional Information:
    Stator Current         = {results['current']:.2f} A (RMS)
    Efficiency             = {results['efficiency']:.2f}%
    Total Losses           = {results['losses']['total']:.2f} W

{'=' * 80}

To run dynamic simulation with the given load profile, go to the
"Dynamic Simulation" tab and click "Start".

To analyze steady-state characteristics, see "Steady-State Characteristics" tab.

To perform thermal and economic analysis, see respective tabs.
        """

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, problem_text)

    def on_resize(self, event):
        """Handle window resize for auto-scaling"""
        # Canvas auto-resize is handled by pack(fill=BOTH, expand=True)
        pass


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point"""

    print("\n" + "=" * 80)
    print("ADVANCED INDUCTION MOTOR LABORATORY")
    print("Multi-Physics Simulation with Electromagnetic-Thermal-Mechanical Coupling")
    print("=" * 80 + "\n")

    # Create and run application
    app = InductionMotorLab()
    app.mainloop()


if __name__ == "__main__":
    main()
