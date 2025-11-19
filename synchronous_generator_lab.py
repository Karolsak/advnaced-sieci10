"""
Advanced Synchronous Generator Simulation Lab
Example 7.3 Solution with Multi-Physics Simulation
Includes: Electromagnetic, Thermal, Mechanical Analysis
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.integrate import solve_ivp, odeint
import math
from dataclasses import dataclass
from typing import Tuple, Dict, List
import threading
import time


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
            'In': In
        }

    def electromagnetic_equations(self, t, state, Te_load, omega_ref):
        """
        Electromagnetic differential equations for dynamic simulation
        state = [id, iq, if_flux, delta, omega]
        """
        id, iq, psi_f, delta, omega = state

        # Electrical parameters
        Ld = self.params.Xsd / (2 * np.pi * self.params.fn)  # d-axis inductance
        Lq = self.params.Xsq / (2 * np.pi * self.params.fn)  # q-axis inductance
        Ra = self.params.Ra

        # Terminal voltage (RMS converted to peak)
        Vt = self.params.V1Ln / np.sqrt(3) * np.sqrt(2)

        # Park transformation equations (dq0)
        vd = -Vt * np.sin(delta)
        vq = Vt * np.cos(delta)

        # Stator voltage equations
        did_dt = (vd - Ra * id + omega * Lq * iq) / Ld
        diq_dt = (vq - Ra * iq - omega * Ld * id - omega * psi_f) / Lq

        # Field flux dynamics (simplified)
        dpsi_f_dt = (self.params.Vfn - self.params.Rfn * self.params.Ifn) / 10

        # Electromagnetic torque
        Te = 1.5 * self.params.p * (psi_f * iq + (Ld - Lq) * id * iq)

        # Mechanical equation
        omega_m = omega / self.params.p
        ddelta_dt = omega - omega_ref
        domega_dt = (Te - Te_load - self.params.D * (omega_m - omega_ref/self.params.p)) / self.params.J

        return [did_dt, diq_dt, dpsi_f_dt, ddelta_dt, domega_dt]

    def calculate_losses(self, operating_point: Dict) -> Dict:
        """Calculate detailed loss breakdown"""
        In = operating_point.get('In', 0)
        Ifn = operating_point.get('Ifn', 0)
        omega = 2 * np.pi * self.params.fn

        # Copper losses
        P_cu_stator = 3 * In**2 * self.params.Ra  # 3-phase stator copper loss
        Rf_temp = self.params.Rf_20C * (1 + 0.00393 * (self.params.temp_field - 20))
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
        """
        Thermal model for temperature prediction
        Simple lumped parameter thermal network
        """
        # Thermal resistances (K/W) - adjusted for realistic values
        R_th_stator = 0.02  # Stator to ambient (for 50kVA machine with cooling)
        R_th_rotor = 0.05  # Rotor to ambient

        # Thermal capacitances (J/K)
        C_th_stator = 5000
        C_th_rotor = 3000

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
        F_bearing = torque / (d_shaft / 2)

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


class EconomicAnalysis:
    """Economic analysis module"""

    @staticmethod
    def calculate_economics(params: GeneratorParameters, losses: Dict,
                          operating_hours: float = 8760) -> Dict:
        """Calculate economic parameters"""
        # Energy cost
        energy_cost = 0.12  # $/kWh

        # Annual energy loss cost
        annual_loss_cost = (losses['Total'] / 1000) * operating_hours * energy_cost

        # Efficiency calculation
        P_out = params.Sn * params.cos_phi_n
        efficiency = P_out / (P_out + losses['Total']) * 100

        # Maintenance cost (simplified)
        maintenance_cost_annual = 0.02 * params.Sn / 1000  # 2% of kW rating

        # Total operating cost
        total_annual_cost = annual_loss_cost + maintenance_cost_annual

        # Lifecycle cost (20 years)
        years = 20
        discount_rate = 0.05
        npv_factor = sum([1 / (1 + discount_rate)**year for year in range(years)])
        lifecycle_cost = total_annual_cost * npv_factor

        return {
            'Efficiency_%': efficiency,
            'Annual_Loss_Cost_$': annual_loss_cost,
            'Maintenance_Cost_$': maintenance_cost_annual,
            'Total_Annual_Cost_$': total_annual_cost,
            'Lifecycle_Cost_$': lifecycle_cost,
            'Energy_Cost_$/kWh': energy_cost
        }


class AdvancedGeneratorGUI:
    """Advanced Tkinter GUI for Synchronous Generator Lab"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Synchronous Generator Simulation Lab - Example 7.3")
        self.root.geometry("1400x900")

        # Parameters
        self.params = GeneratorParameters()
        self.model = SynchronousGeneratorModel(self.params)

        # Simulation control
        self.simulation_running = False
        self.simulation_thread = None
        self.time_data = []
        self.current_data = []
        self.voltage_data = []
        self.torque_data = []
        self.temp_data = []

        # Setup GUI
        self.setup_gui()
        self.root.bind('<Configure>', self.on_window_resize)

    def setup_gui(self):
        """Setup main GUI layout"""
        # Main container with grid layout
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure grid weights for auto-scaling
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)

        # Left panel - Controls
        control_frame = ttk.LabelFrame(main_container, text="Control Panel", padding=10)
        control_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Right panel - Notebook with tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Setup control panel
        self.setup_control_panel(control_frame)

        # Setup tabs
        self.setup_parameters_tab()
        self.setup_results_tab()
        self.setup_dynamic_simulation_tab()
        self.setup_losses_tab()
        self.setup_thermal_tab()
        self.setup_mechanical_tab()
        self.setup_economic_tab()

    def setup_control_panel(self, parent):
        """Setup control panel with buttons and sliders"""
        # Control buttons
        button_frame = ttk.LabelFrame(parent, text="Simulation Control", padding=5)
        button_frame.pack(fill=tk.X, pady=5)

        self.start_btn = ttk.Button(button_frame, text="Start", command=self.start_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = ttk.Button(button_frame, text="Reset", command=self.reset_simulation)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Calculate", command=self.calculate_example).pack(side=tk.LEFT, padx=5)

        # Control sliders
        slider_frame = ttk.LabelFrame(parent, text="Real-Time Adjustments", padding=5)
        slider_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Load torque slider
        ttk.Label(slider_frame, text="Load Torque (%)").pack(anchor=tk.W)
        self.load_slider = ttk.Scale(slider_frame, from_=0, to=150, orient=tk.HORIZONTAL)
        self.load_slider.set(100)
        self.load_slider.pack(fill=tk.X, pady=2)
        self.load_value_label = ttk.Label(slider_frame, text="100%")
        self.load_value_label.pack(anchor=tk.W)
        self.load_slider.config(command=self.update_load)

        # Field current slider
        ttk.Label(slider_frame, text="Field Current (%)").pack(anchor=tk.W, pady=(10,0))
        self.field_slider = ttk.Scale(slider_frame, from_=50, to=150, orient=tk.HORIZONTAL)
        self.field_slider.set(100)
        self.field_slider.pack(fill=tk.X, pady=2)
        self.field_value_label = ttk.Label(slider_frame, text="100%")
        self.field_value_label.pack(anchor=tk.W)
        self.field_slider.config(command=self.update_field)

        # Speed slider
        ttk.Label(slider_frame, text="Speed (%)").pack(anchor=tk.W, pady=(10,0))
        self.speed_slider = ttk.Scale(slider_frame, from_=80, to=120, orient=tk.HORIZONTAL)
        self.speed_slider.set(100)
        self.speed_slider.pack(fill=tk.X, pady=2)
        self.speed_value_label = ttk.Label(slider_frame, text="100%")
        self.speed_value_label.pack(anchor=tk.W)
        self.speed_slider.config(command=self.update_speed)

        # Temperature slider
        ttk.Label(slider_frame, text="Ambient Temp (°C)").pack(anchor=tk.W, pady=(10,0))
        self.temp_slider = ttk.Scale(slider_frame, from_=0, to=50, orient=tk.HORIZONTAL)
        self.temp_slider.set(25)
        self.temp_slider.pack(fill=tk.X, pady=2)
        self.temp_value_label = ttk.Label(slider_frame, text="25°C")
        self.temp_value_label.pack(anchor=tk.W)
        self.temp_slider.config(command=self.update_temperature)

        # Status display
        status_frame = ttk.LabelFrame(parent, text="Status", padding=5)
        status_frame.pack(fill=tk.X, pady=5)

        self.status_text = scrolledtext.ScrolledText(status_frame, height=10, width=30)
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def setup_parameters_tab(self):
        """Parameters input tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Parameters")

        # Create canvas for scrolling
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Nominal parameters
        nominal_frame = ttk.LabelFrame(scrollable_frame, text="Nominal Parameters", padding=10)
        nominal_frame.pack(fill=tk.X, padx=10, pady=5)

        params_list = [
            ("Apparent Power Sn (kVA)", self.params.Sn/1000, "Sn"),
            ("Line Voltage V1Ln (V)", self.params.V1Ln, "V1Ln"),
            ("Frequency fn (Hz)", self.params.fn, "fn"),
            ("Speed nn (rpm)", self.params.nn, "nn"),
            ("Power Factor cos φn", self.params.cos_phi_n, "cos_phi_n"),
        ]

        self.param_entries = {}
        for i, (label, value, key) in enumerate(params_list):
            ttk.Label(nominal_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(nominal_frame, width=15)
            entry.insert(0, str(value))
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.param_entries[key] = entry

        # Test parameters
        test_frame = ttk.LabelFrame(scrollable_frame, text="Test Parameters", padding=10)
        test_frame.pack(fill=tk.X, padx=10, pady=5)

        test_params = [
            ("Test Voltage Vs (V)", self.params.Vs_test, "Vs_test"),
            ("Maximum Current Imax (A)", self.params.Imax, "Imax"),
            ("Minimum Current Imin (A)", self.params.Imin, "Imin"),
            ("Test Speed n (rpm)", self.params.n_test, "n_test"),
        ]

        for i, (label, value, key) in enumerate(test_params):
            ttk.Label(test_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(test_frame, width=15)
            entry.insert(0, str(value))
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.param_entries[key] = entry

        # Field winding parameters
        field_frame = ttk.LabelFrame(scrollable_frame, text="Field Winding", padding=10)
        field_frame.pack(fill=tk.X, padx=10, pady=5)

        field_params = [
            ("Field Resistance Rf @ 20°C (Ω)", self.params.Rf_20C, "Rf_20C"),
            ("Field Current at No Load If0 (A)", self.params.If0, "If0"),
            ("Field Temperature (°C)", self.params.temp_field, "temp_field"),
        ]

        for i, (label, value, key) in enumerate(field_params):
            ttk.Label(field_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(field_frame, width=15)
            entry.insert(0, str(value))
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.param_entries[key] = entry

        # Update button
        ttk.Button(scrollable_frame, text="Update Parameters",
                  command=self.update_parameters).pack(pady=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_results_tab(self):
        """Results display tab - Example 7.3 solution"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Results - Ex 7.3")

        # Results text
        results_frame = ttk.LabelFrame(tab, text="Example 7.3 Solution", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.results_text = scrolledtext.ScrolledText(results_frame, height=25,
                                                      font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Display initial results
        self.display_results()

    def setup_dynamic_simulation_tab(self):
        """Dynamic simulation with ODE solver"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dynamic Simulation")

        # Solver selection
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(control_frame, text="ODE Solver:").pack(side=tk.LEFT, padx=5)
        self.solver_var = tk.StringVar(value="RK45")
        ttk.Radiobutton(control_frame, text="RK45", variable=self.solver_var,
                       value="RK45").pack(side=tk.LEFT)
        ttk.Radiobutton(control_frame, text="Euler", variable=self.solver_var,
                       value="Euler").pack(side=tk.LEFT)

        ttk.Button(control_frame, text="Run Simulation",
                  command=self.run_dynamic_simulation).pack(side=tk.LEFT, padx=10)

        # Graph area
        self.fig_dynamic = Figure(figsize=(10, 6))
        self.canvas_dynamic = FigureCanvasTkAgg(self.fig_dynamic, tab)
        self.canvas_dynamic.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def setup_losses_tab(self):
        """Detailed losses breakdown"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Loss Analysis")

        # Loss breakdown
        text_frame = ttk.Frame(tab)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.losses_text = scrolledtext.ScrolledText(text_frame, height=20,
                                                     font=('Courier', 10))
        self.losses_text.pack(fill=tk.BOTH, expand=True)

        # Pie chart
        chart_frame = ttk.Frame(tab)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.fig_losses = Figure(figsize=(6, 6))
        self.canvas_losses = FigureCanvasTkAgg(self.fig_losses, chart_frame)
        self.canvas_losses.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_thermal_tab(self):
        """Thermal analysis and derating"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Thermal & Derating")

        # Temperature display
        temp_frame = ttk.LabelFrame(tab, text="Temperature Distribution", padding=10)
        temp_frame.pack(fill=tk.X, padx=10, pady=5)

        self.thermal_text = scrolledtext.ScrolledText(temp_frame, height=10,
                                                      font=('Courier', 10))
        self.thermal_text.pack(fill=tk.BOTH, expand=True)

        # Thermal graph
        self.fig_thermal = Figure(figsize=(10, 5))
        self.canvas_thermal = FigureCanvasTkAgg(self.fig_thermal, tab)
        self.canvas_thermal.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def setup_mechanical_tab(self):
        """Mechanical stress analysis"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Mechanical Analysis")

        self.mechanical_text = scrolledtext.ScrolledText(tab, height=25,
                                                         font=('Courier', 10))
        self.mechanical_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_economic_tab(self):
        """Economic analysis"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Economic Analysis")

        # Input parameters
        input_frame = ttk.LabelFrame(tab, text="Economic Parameters", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="Operating Hours/Year:").grid(row=0, column=0, sticky=tk.W)
        self.hours_entry = ttk.Entry(input_frame, width=15)
        self.hours_entry.insert(0, "8760")
        self.hours_entry.grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="Energy Cost ($/kWh):").grid(row=1, column=0, sticky=tk.W)
        self.cost_entry = ttk.Entry(input_frame, width=15)
        self.cost_entry.insert(0, "0.12")
        self.cost_entry.grid(row=1, column=1, padx=5)

        ttk.Button(input_frame, text="Calculate Economics",
                  command=self.calculate_economics).grid(row=2, column=0, columnspan=2, pady=10)

        # Results
        self.economic_text = scrolledtext.ScrolledText(tab, height=20,
                                                       font=('Courier', 10))
        self.economic_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def update_load(self, value):
        """Update load torque slider"""
        if hasattr(self, 'load_value_label'):
            self.load_value_label.config(text=f"{float(value):.1f}%")

    def update_field(self, value):
        """Update field current slider"""
        if hasattr(self, 'field_value_label'):
            self.field_value_label.config(text=f"{float(value):.1f}%")

    def update_speed(self, value):
        """Update speed slider"""
        if hasattr(self, 'speed_value_label'):
            self.speed_value_label.config(text=f"{float(value):.1f}%")

    def update_temperature(self, value):
        """Update temperature slider"""
        if hasattr(self, 'temp_value_label'):
            self.temp_value_label.config(text=f"{float(value):.1f}°C")

    def update_parameters(self):
        """Update parameters from entries"""
        try:
            for key, entry in self.param_entries.items():
                value = float(entry.get())
                if key == "Sn":
                    value *= 1000  # Convert kVA to VA
                setattr(self.params, key, value)

            self.model = SynchronousGeneratorModel(self.params)
            messagebox.showinfo("Success", "Parameters updated successfully!")
            self.display_results()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid parameter values:\n{str(e)}")

    def calculate_example(self):
        """Calculate Example 7.3 solution"""
        self.model.calculate_parameters()
        self.display_results()
        self.calculate_losses_display()
        self.calculate_thermal_display()
        self.calculate_mechanical_display()

    def display_results(self):
        """Display Example 7.3 results"""
        results = self.model.calculate_parameters()

        output = "="*70 + "\n"
        output += "EXAMPLE 7.3 - SALIENT-POLE SYNCHRONOUS GENERATOR SOLUTION\n"
        output += "="*70 + "\n\n"

        output += "GIVEN DATA:\n"
        output += "-" * 70 + "\n"
        output += f"Apparent Power Sn          : {self.params.Sn/1000:.1f} kVA\n"
        output += f"Line Voltage V1Ln          : {self.params.V1Ln:.1f} V\n"
        output += f"Frequency fn               : {self.params.fn:.1f} Hz\n"
        output += f"Speed nn                   : {self.params.nn:.1f} rpm\n"
        output += f"Power Factor cos φn        : {self.params.cos_phi_n:.2f}\n"
        output += f"\nTest Voltage Vs            : {self.params.Vs_test:.1f} V\n"
        output += f"Maximum Test Current Imax  : {self.params.Imax:.2f} A\n"
        output += f"Minimum Test Current Imin  : {self.params.Imin:.2f} A\n"
        output += f"Field Resistance @ 20°C    : {self.params.Rf_20C:.2f} Ω\n"
        output += f"Field Current at No Load   : {self.params.If0:.2f} A\n"
        output += f"Operating Temperature      : {self.params.temp_field:.1f} °C\n"

        output += "\n" + "="*70 + "\n"
        output += "SOLUTION:\n"
        output += "="*70 + "\n\n"

        output += "(a) SYNCHRONOUS REACTANCES (from slip test):\n"
        output += "-" * 70 + "\n"
        output += f"d-axis reactance Xsd = Vs / Imin\n"
        output += f"Xsd = {self.params.Vs_test:.1f} / {self.params.Imin:.2f}\n"
        output += f"Xsd = {results['Xsd']:.3f} Ω\n\n"

        output += f"q-axis reactance Xsq = Vs / Imax\n"
        output += f"Xsq = {self.params.Vs_test:.1f} / {self.params.Imax:.2f}\n"
        output += f"Xsq = {results['Xsq']:.3f} Ω\n\n"

        output += "(b) NOMINAL FIELD EXCITATION CURRENT:\n"
        output += "-" * 70 + "\n"
        output += f"Phase Voltage V1n          : {results['V1n_phase']:.2f} V\n"
        output += f"Nominal Current In         : {results['In']:.2f} A\n"
        output += f"Excitation Voltage Ef      : {results['Ef']:.2f} V\n"
        output += f"\nUsing linear magnetization curve:\n"
        output += f"Ifn / If0 = Ef / V1n\n"
        output += f"Ifn = {self.params.If0:.2f} × ({results['Ef']:.2f} / {results['V1n_phase']:.2f})\n"
        output += f"Ifn = {results['Ifn']:.3f} A\n\n"

        output += "(c) FIELD VOLTAGE AT OPERATING TEMPERATURE:\n"
        output += "-" * 70 + "\n"
        alpha = 0.00393
        T_ref = 20
        Rf_temp = self.params.Rf_20C * (1 + alpha * (self.params.temp_field - T_ref))
        output += f"Temperature coefficient α  : {alpha:.5f} /°C\n"
        output += f"Rf({self.params.temp_field}°C) = Rf(20°C) × [1 + α(T - 20)]\n"
        output += f"Rf({self.params.temp_field}°C) = {self.params.Rf_20C:.2f} × [1 + {alpha:.5f} × {self.params.temp_field - T_ref}]\n"
        output += f"Rf({self.params.temp_field}°C) = {Rf_temp:.4f} Ω\n\n"
        output += f"Field Voltage Vfn = Ifn × Rf\n"
        output += f"Vfn = {results['Ifn']:.3f} × {Rf_temp:.4f}\n"
        output += f"Vfn = {results['Vfn']:.3f} V\n\n"

        output += "="*70 + "\n"
        output += "FINAL ANSWERS:\n"
        output += "="*70 + "\n"
        output += f"(a) Xsd = {results['Xsd']:.3f} Ω,  Xsq = {results['Xsq']:.3f} Ω\n"
        output += f"(b) Ifn = {results['Ifn']:.3f} A\n"
        output += f"(c) Vfn = {results['Vfn']:.3f} V @ {self.params.temp_field}°C\n"
        output += "="*70 + "\n"

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, output)

        # Update status
        self.update_status("Example 7.3 calculated successfully!")

    def calculate_losses_display(self):
        """Calculate and display losses"""
        results = self.model.calculate_parameters()
        losses = self.model.calculate_losses(results)

        output = "="*60 + "\n"
        output += "DETAILED LOSS BREAKDOWN\n"
        output += "="*60 + "\n\n"

        output += f"Stator Copper Loss    : {losses['Copper_Stator']:8.2f} W\n"
        output += f"Rotor Copper Loss     : {losses['Copper_Rotor']:8.2f} W\n"
        output += f"Iron (Core) Loss      : {losses['Iron']:8.2f} W\n"
        output += f"Friction Loss         : {losses['Friction']:8.2f} W\n"
        output += f"Windage Loss          : {losses['Windage']:8.2f} W\n"
        output += f"Stray Load Loss       : {losses['Stray']:8.2f} W\n"
        output += "-"*60 + "\n"
        output += f"TOTAL LOSSES          : {losses['Total']:8.2f} W\n"
        output += "="*60 + "\n\n"

        P_out = self.params.Sn * self.params.cos_phi_n
        efficiency = P_out / (P_out + losses['Total']) * 100
        output += f"Output Power          : {P_out/1000:.2f} kW\n"
        output += f"Efficiency            : {efficiency:.2f} %\n"

        self.losses_text.delete(1.0, tk.END)
        self.losses_text.insert(1.0, output)

        # Plot pie chart
        self.fig_losses.clear()
        ax = self.fig_losses.add_subplot(111)

        labels = ['Stator Cu', 'Rotor Cu', 'Iron', 'Friction', 'Windage', 'Stray']
        values = [losses['Copper_Stator'], losses['Copper_Rotor'], losses['Iron'],
                 losses['Friction'], losses['Windage'], losses['Stray']]

        colors = ['#ff9999', '#ff6666', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title('Loss Distribution')

        self.canvas_losses.draw()

    def calculate_thermal_display(self):
        """Calculate and display thermal analysis"""
        results = self.model.calculate_parameters()
        losses = self.model.calculate_losses(results)

        ambient = float(self.temp_slider.get())
        thermal = self.model.thermal_model(losses, ambient)

        output = "="*60 + "\n"
        output += "THERMAL ANALYSIS & DERATING\n"
        output += "="*60 + "\n\n"

        output += f"Ambient Temperature      : {thermal['Ambient_Temp']:.1f} °C\n"
        output += f"Stator Temperature       : {thermal['Stator_Temp']:.1f} °C\n"
        output += f"Rotor Temperature        : {thermal['Rotor_Temp']:.1f} °C\n"
        output += f"Maximum Allowed Temp     : {thermal['Max_Temp']:.1f} °C (Class F)\n"
        output += f"\nDerating Factor          : {thermal['Derating_Factor']:.2%}\n"

        if thermal['Stator_Temp'] > thermal['Max_Temp']:
            output += "\n*** WARNING: Stator temperature exceeds maximum! ***\n"
            output += "*** Reduce load or improve cooling! ***\n"

        self.thermal_text.delete(1.0, tk.END)
        self.thermal_text.insert(1.0, output)

        # Plot thermal distribution
        self.fig_thermal.clear()
        ax = self.fig_thermal.add_subplot(111)

        components = ['Ambient', 'Stator', 'Rotor', 'Max Allow']
        temperatures = [thermal['Ambient_Temp'], thermal['Stator_Temp'],
                       thermal['Rotor_Temp'], thermal['Max_Temp']]
        colors = ['blue', 'orange', 'red', 'green']

        bars = ax.bar(components, temperatures, color=colors, alpha=0.7)
        ax.set_ylabel('Temperature (°C)')
        ax.set_title('Temperature Distribution')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for bar, temp in zip(bars, temperatures):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{temp:.1f}°C', ha='center', va='bottom')

        self.canvas_thermal.draw()

    def calculate_mechanical_display(self):
        """Calculate and display mechanical analysis"""
        # Calculate rated torque
        T_rated = self.params.Sn / (2 * np.pi * self.params.nn / 60)
        load_percent = float(self.load_slider.get()) / 100
        T_current = T_rated * load_percent

        mechanical = self.model.mechanical_stress_analysis(T_current)

        output = "="*60 + "\n"
        output += "MECHANICAL STRESS ANALYSIS\n"
        output += "="*60 + "\n\n"

        output += "TORQUE:\n"
        output += f"Rated Torque             : {mechanical['Rated_Torque_Nm']:.2f} N·m\n"
        output += f"Current Operating Torque : {mechanical['Current_Torque_Nm']:.2f} N·m\n"
        output += f"Load Percentage          : {load_percent*100:.1f} %\n\n"

        output += "SHAFT STRESS:\n"
        output += f"Torsional Stress         : {mechanical['Shaft_Stress_MPa']:.2f} MPa\n"
        output += f"Safety Factor            : {mechanical['Safety_Factor']:.2f}\n\n"

        output += "BEARING LOADS:\n"
        output += f"Radial Bearing Load      : {mechanical['Bearing_Load_N']:.2f} N\n\n"

        if mechanical['Safety_Factor'] < 2.0:
            output += "*** WARNING: Low safety factor! ***\n"
            output += "*** Consider reducing load or upgrading shaft! ***\n"

        self.mechanical_text.delete(1.0, tk.END)
        self.mechanical_text.insert(1.0, output)

    def calculate_economics(self):
        """Calculate and display economic analysis"""
        try:
            results = self.model.calculate_parameters()
            losses = self.model.calculate_losses(results)

            hours = float(self.hours_entry.get())

            economics = EconomicAnalysis.calculate_economics(
                self.params, losses, hours
            )

            output = "="*70 + "\n"
            output += "ECONOMIC ANALYSIS\n"
            output += "="*70 + "\n\n"

            output += "EFFICIENCY:\n"
            output += f"Generator Efficiency     : {economics['Efficiency_%']:.2f} %\n\n"

            output += "ANNUAL COSTS:\n"
            output += f"Energy Cost Rate         : ${economics['Energy_Cost_$/kWh']:.3f} /kWh\n"
            output += f"Operating Hours/Year     : {hours:.0f} hours\n"
            output += f"Annual Energy Loss Cost  : ${economics['Annual_Loss_Cost_$']:.2f}\n"
            output += f"Annual Maintenance Cost  : ${economics['Maintenance_Cost_$']:.2f}\n"
            output += f"Total Annual Cost        : ${economics['Total_Annual_Cost_$']:.2f}\n\n"

            output += "LIFECYCLE ANALYSIS (20 years, 5% discount rate):\n"
            output += f"Net Present Value Cost   : ${economics['Lifecycle_Cost_$']:.2f}\n\n"

            output += "COST BREAKDOWN:\n"
            output += f"Energy losses contribute : {economics['Annual_Loss_Cost_$']/economics['Total_Annual_Cost_$']*100:.1f}% of annual costs\n"
            output += f"Maintenance contributes  : {economics['Maintenance_Cost_$']/economics['Total_Annual_Cost_$']*100:.1f}% of annual costs\n"

            self.economic_text.delete(1.0, tk.END)
            self.economic_text.insert(1.0, output)

            self.update_status("Economic analysis completed!")

        except Exception as e:
            messagebox.showerror("Error", f"Economic calculation failed:\n{str(e)}")

    def run_dynamic_simulation(self):
        """Run dynamic simulation with ODE solver"""
        solver = self.solver_var.get()

        # Initial conditions [id, iq, psi_f, delta, omega]
        y0 = [0, 0, 1.0, 0, 2*np.pi*self.params.fn]

        # Time span
        t_span = (0, 2.0)  # 2 seconds
        t_eval = np.linspace(0, 2.0, 1000)

        # Load torque
        T_rated = self.params.Sn / (2 * np.pi * self.params.nn / 60)
        Te_load = T_rated * float(self.load_slider.get()) / 100
        omega_ref = 2 * np.pi * self.params.fn

        try:
            if solver == "RK45":
                # Use scipy's RK45 solver
                sol = solve_ivp(
                    lambda t, y: self.model.electromagnetic_equations(t, y, Te_load, omega_ref),
                    t_span, y0, method='RK45', t_eval=t_eval, max_step=0.01
                )
                t = sol.t
                y = sol.y
            else:
                # Simple Euler method
                dt = 0.001
                t = np.arange(0, 2.0, dt)
                y = np.zeros((5, len(t)))
                y[:, 0] = y0

                for i in range(1, len(t)):
                    dydt = self.model.electromagnetic_equations(
                        t[i-1], y[:, i-1], Te_load, omega_ref
                    )
                    y[:, i] = y[:, i-1] + np.array(dydt) * dt

            # Plot results
            self.fig_dynamic.clear()

            ax1 = self.fig_dynamic.add_subplot(311)
            ax1.plot(t, y[0, :], label='id (d-axis current)')
            ax1.plot(t, y[1, :], label='iq (q-axis current)')
            ax1.set_ylabel('Current (A)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_title(f'Dynamic Simulation using {solver} solver')

            ax2 = self.fig_dynamic.add_subplot(312)
            ax2.plot(t, np.degrees(y[3, :]))
            ax2.set_ylabel('Load Angle δ (deg)')
            ax2.grid(True, alpha=0.3)

            ax3 = self.fig_dynamic.add_subplot(313)
            ax3.plot(t, y[4, :] / (2*np.pi))
            ax3.set_ylabel('Speed (Hz)')
            ax3.set_xlabel('Time (s)')
            ax3.grid(True, alpha=0.3)

            self.fig_dynamic.tight_layout()
            self.canvas_dynamic.draw()

            self.update_status(f"Dynamic simulation completed using {solver} solver!")

        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed:\n{str(e)}")
            self.update_status(f"Simulation error: {str(e)}")

    def start_simulation(self):
        """Start real-time simulation"""
        if not self.simulation_running:
            self.simulation_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

            self.time_data = []
            self.current_data = []
            self.voltage_data = []

            self.simulation_thread = threading.Thread(target=self.simulation_loop)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()

            self.update_status("Simulation started...")

    def stop_simulation(self):
        """Stop real-time simulation"""
        self.simulation_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("Simulation stopped.")

    def reset_simulation(self):
        """Reset simulation"""
        self.stop_simulation()
        self.time_data = []
        self.current_data = []
        self.voltage_data = []
        self.update_status("Simulation reset.")

    def simulation_loop(self):
        """Real-time simulation loop"""
        t = 0
        dt = 0.05

        while self.simulation_running and t < 10:
            # Simulate varying conditions
            results = self.model.calculate_parameters()
            In = results['In'] * (1 + 0.1 * np.sin(2*np.pi*0.5*t))  # Varying load

            self.time_data.append(t)
            self.current_data.append(In)
            self.voltage_data.append(results['V1n_phase'])

            t += dt
            time.sleep(dt)

        self.simulation_running = False
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def update_status(self, message):
        """Update status text"""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

    def on_window_resize(self, event):
        """Handle window resize for auto-scaling"""
        # This is called when window is resized
        # The grid layout automatically handles scaling
        pass


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = AdvancedGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
