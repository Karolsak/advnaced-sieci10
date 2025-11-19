"""
Advanced Synchronous Generator Laboratory
Multi-Physics Simulation with Dynamic Analysis

This application provides comprehensive simulation and analysis of parallel-connected
synchronous generators including:
- Electromagnetic modeling
- Thermal analysis
- Economic analysis
- Real-time dynamic simulation
- Loss breakdown and efficiency analysis
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.integrate import solve_ivp, odeint
import math
from datetime import datetime
import json


class SynchronousGeneratorCalculator:
    """
    Core calculation engine for synchronous generator problems
    Solves parallel generator operation with field excitation control
    """

    def __init__(self):
        # Generator A parameters
        self.PnA = 500e3  # W
        self.IfnA = 21.0  # A
        self.xsA = 1.5  # p.u.
        self.cos_phi_nA = 0.85

        # Generator B parameters
        self.PnB = 350e3  # W
        self.IfnB = 16.0  # A
        self.xsB = 1.6  # p.u.
        self.cos_phi_nB = 0.85

        # Common parameters
        self.V1n = 6300  # V (line-to-line)
        self.Vph_n = self.V1n / np.sqrt(3)  # Phase voltage

        # Calculate base quantities for each generator
        self.calculate_base_quantities()

    def calculate_base_quantities(self):
        """Calculate base values for per-unit system"""
        # Generator A
        self.SnA = self.PnA / self.cos_phi_nA
        self.InA = self.SnA / (np.sqrt(3) * self.V1n)
        self.ZbaseA = self.V1n / (np.sqrt(3) * self.InA)
        self.XsA = self.xsA * self.ZbaseA  # Ohms

        # Generator B
        self.SnB = self.PnB / self.cos_phi_nB
        self.InB = self.SnB / (np.sqrt(3) * self.V1n)
        self.ZbaseB = self.V1n / (np.sqrt(3) * self.InB)
        self.XsB = self.xsB * self.ZbaseB  # Ohms

    def calculate_emf_coefficient(self, generator='A'):
        """Calculate EMF coefficient (Ef/If relationship)"""
        if generator == 'A':
            Pn = self.PnA
            Ifn = self.IfnA
            xs = self.xsA  # Use per-unit
            cos_phi_n = self.cos_phi_nA
            Sn = self.SnA
            Vbase = self.Vph_n
            Ibase = self.InA
        else:
            Pn = self.PnB
            Ifn = self.IfnB
            xs = self.xsB  # Use per-unit
            cos_phi_n = self.cos_phi_nB
            Sn = self.SnB
            Vbase = self.Vph_n
            Ibase = self.InB

        # Power factor angle
        phi_n = np.arccos(cos_phi_n)

        # Work in per-unit
        V_pu = 1.0  # Rated voltage
        I_pu = 1.0  # Rated current

        # Calculate EMF using phasor diagram (lagging power factor)
        # Ef = V + j*Xs*I, where I lags V by phi
        I_real = I_pu * cos_phi_n
        I_imag = -I_pu * np.sin(phi_n)  # Negative for lagging

        Ef_real = V_pu + xs * I_imag
        Ef_imag = xs * I_real
        Ef_pu = np.sqrt(Ef_real**2 + Ef_imag**2)

        # Convert back to actual voltage
        Ef_n = Ef_pu * Vbase

        # EMF coefficient
        k_emf = Ef_n / Ifn

        return k_emf, Ef_n

    def solve_part_a(self):
        """
        Solve part (a): Find IfB for given conditions
        - Load: 720 kW at 0.8 pf lagging
        - Each generator: 360 kW
        - Generator A: IfA = 20 A
        - Maintain V = Vn
        """
        # Load conditions
        PL_total = 720e3  # W
        cos_phi_L = 0.8
        QL_total = PL_total * np.tan(np.arccos(cos_phi_L))

        # Each generator delivers
        PA = 360e3  # W
        PB = 360e3  # W

        # Generator A field current
        IfA = 20.0  # A

        # Calculate EMF coefficients
        k_emfA, _ = self.calculate_emf_coefficient('A')
        k_emfB, _ = self.calculate_emf_coefficient('B')

        # EMF of generator A
        EfA = k_emfA * IfA

        # Work in per-unit for generator A
        PA_pu = PA / self.SnA
        Vph_pu = 1.0
        EfA_pu = EfA / self.Vph_n

        # Power angle calculation for generator A
        sin_delta_A = PA_pu * self.xsA / EfA_pu
        if abs(sin_delta_A) > 1.0:
            sin_delta_A = np.clip(sin_delta_A, -1.0, 1.0)
        delta_A = np.arcsin(sin_delta_A)

        # Reactive power of generator A (per-unit)
        QA_pu = (EfA_pu * Vph_pu * np.cos(delta_A) - Vph_pu**2) / self.xsA
        QA = QA_pu * self.SnA  # Convert to actual VAR

        # Reactive power of generator B (by balance)
        QB = QL_total - QA

        # Work in per-unit for generator B
        PB_pu = PB / self.SnB
        QB_pu = QB / self.SnB

        # Calculate EMF for generator B using power equations
        # P = (Ef * V / Xs) * sin(delta)
        # Q = (Ef * V * cos(delta) - V^2) / Xs
        # Solving: Ef^2 = (P * Xs)^2 + (Q * Xs + V^2)^2 / V^2

        term1 = (PB_pu * self.xsB)**2
        term2 = (QB_pu * self.xsB + Vph_pu)**2
        EfB_pu = np.sqrt(term1 + term2)
        EfB = EfB_pu * self.Vph_n

        # Calculate field current for generator B
        IfB = EfB / k_emfB

        # Power angle for generator B
        sin_delta_B = PB_pu * self.xsB / EfB_pu
        if abs(sin_delta_B) > 1.0:
            sin_delta_B = np.clip(sin_delta_B, -1.0, 1.0)
        delta_B = np.arcsin(sin_delta_B)

        results_a = {
            'IfB': IfB,
            'EfB': EfB,
            'PA': PA / 1e3,
            'PB': PB / 1e3,
            'QA': QA / 1e3,
            'QB': QB / 1e3,
            'delta_A_deg': np.degrees(delta_A),
            'delta_B_deg': np.degrees(delta_B),
            'k_emfA': k_emfA,
            'k_emfB': k_emfB
        }

        return results_a

    def solve_part_b(self):
        """
        Solve part (b): Additional load added
        - Additional load: 130 kW at unity pf
        - Keep generator B conditions same
        - Find new IfA to maintain constant voltage
        """
        # First get part (a) results
        results_a = self.solve_part_a()
        IfB = results_a['IfB']
        EfB = results_a['EfB']
        QB = results_a['QB'] * 1e3  # Convert back to W

        # New load conditions
        P_additional = 130e3  # W
        PL_total_new = 720e3 + P_additional  # Total 850 kW
        QL_total_new = 720e3 * np.tan(np.arccos(0.8))  # Only original load has reactive

        # Assume power sharing proportional to ratings
        total_rating = self.PnA + self.PnB
        PA_new = PL_total_new * (self.PnA / total_rating)
        PB_new = PL_total_new * (self.PnB / total_rating)

        # Generator B keeps same field current
        # QB remains the same

        # Generator A provides remaining reactive power
        QA_new = QL_total_new - QB

        # Work in per-unit for generator A
        PA_new_pu = PA_new / self.SnA
        QA_new_pu = QA_new / self.SnA
        Vph_pu = 1.0

        # Calculate new EMF for generator A
        term1 = (PA_new_pu * self.xsA)**2
        term2 = (QA_new_pu * self.xsA + Vph_pu)**2
        EfA_new_pu = np.sqrt(term1 + term2)
        EfA_new = EfA_new_pu * self.Vph_n

        # Calculate new field current for generator A
        k_emfA = results_a['k_emfA']
        IfA_new = EfA_new / k_emfA

        # Power angles
        sin_delta_A_new = PA_new_pu * self.xsA / EfA_new_pu
        if abs(sin_delta_A_new) > 1.0:
            sin_delta_A_new = np.clip(sin_delta_A_new, -1.0, 1.0)
        delta_A_new = np.arcsin(sin_delta_A_new)

        # Generator B
        PB_new_pu = PB_new / self.SnB
        EfB_pu = EfB / self.Vph_n
        sin_delta_B_new = PB_new_pu * self.xsB / EfB_pu
        if abs(sin_delta_B_new) > 1.0:
            sin_delta_B_new = np.clip(sin_delta_B_new, -1.0, 1.0)
        delta_B_new = np.arcsin(sin_delta_B_new)

        results_b = {
            'IfA_new': IfA_new,
            'EfA_new': EfA_new,
            'PA_new': PA_new / 1e3,
            'PB_new': PB_new / 1e3,
            'QA_new': QA_new / 1e3,
            'QB_new': QB / 1e3,
            'delta_A_new_deg': np.degrees(delta_A_new),
            'delta_B_new_deg': np.degrees(delta_B_new)
        }

        return results_b


class SynchronousGeneratorDynamics:
    """
    Dynamic model of synchronous generator
    Implements differential equations for electromagnetic and mechanical dynamics
    """

    def __init__(self, params):
        self.params = params
        self.H = params.get('H', 3.5)  # Inertia constant (s)
        self.D = params.get('D', 2.0)  # Damping coefficient
        self.Xd = params.get('Xd', 1.5)  # d-axis reactance (p.u.)
        self.Xq = params.get('Xq', 1.5)  # q-axis reactance (p.u.)
        self.Xd_prime = params.get('Xd_prime', 0.3)  # Transient reactance
        self.Td0_prime = params.get('Td0_prime', 5.0)  # d-axis time constant
        self.omega_s = 2 * np.pi * params.get('freq', 60)  # Synchronous speed

    def swing_equation(self, t, y, Pm, Ef, V):
        """
        Swing equation and voltage dynamics
        State variables: [delta, omega, Eq_prime]
        """
        delta, omega, Eq_prime = y

        # Electrical power
        Pe = (Eq_prime * V / self.Xd_prime) * np.sin(delta) + \
             (V**2 / (2 * self.Xd_prime * self.Xq)) * (self.Xd_prime - self.Xq) * np.sin(2 * delta)

        # Swing equation
        ddelta_dt = omega - self.omega_s
        domega_dt = (self.omega_s / (2 * self.H)) * (Pm - Pe - self.D * (omega - self.omega_s))

        # Field voltage dynamics
        dEq_prime_dt = (1 / self.Td0_prime) * (Ef - Eq_prime - (self.Xd - self.Xd_prime) * \
                       (V / self.Xd_prime) * np.cos(delta))

        return [ddelta_dt, domega_dt, dEq_prime_dt]

    def simulate(self, t_span, y0, Pm, Ef, V, method='RK45'):
        """
        Simulate generator dynamics
        """
        if method == 'RK45':
            sol = solve_ivp(lambda t, y: self.swing_equation(t, y, Pm, Ef, V),
                          t_span, y0, method='RK45', dense_output=True,
                          max_step=0.001)
        elif method == 'Euler':
            # Implement Euler method
            t = np.arange(t_span[0], t_span[1], 0.001)
            y = np.zeros((len(t), len(y0)))
            y[0] = y0
            for i in range(1, len(t)):
                dt = t[i] - t[i-1]
                dydt = self.swing_equation(t[i-1], y[i-1], Pm, Ef, V)
                y[i] = y[i-1] + np.array(dydt) * dt

            # Create solution object similar to solve_ivp
            class EulerSolution:
                def __init__(self, t, y):
                    self.t = t
                    self.y = y.T
                    self.success = True

            sol = EulerSolution(t, y)

        return sol


class ThermalModel:
    """
    Thermal model for generator heating and cooling
    Includes thermal network with multiple nodes
    """

    def __init__(self, params):
        # Thermal capacitances (J/K)
        self.C_winding = params.get('C_winding', 5000)
        self.C_core = params.get('C_core', 8000)
        self.C_frame = params.get('C_frame', 3000)

        # Thermal resistances (K/W)
        self.R_winding_core = params.get('R_winding_core', 0.05)
        self.R_core_frame = params.get('R_core_frame', 0.03)
        self.R_frame_ambient = params.get('R_frame_ambient', 0.02)

        # Ambient temperature
        self.T_ambient = params.get('T_ambient', 25)  # °C

        # Maximum temperatures
        self.T_max_winding = params.get('T_max_winding', 130)  # °C
        self.T_max_core = params.get('T_max_core', 110)  # °C

    def thermal_network(self, t, T, P_losses):
        """
        Thermal network differential equations
        State variables: [T_winding, T_core, T_frame]
        """
        T_winding, T_core, T_frame = T
        P_copper, P_iron, P_friction = P_losses

        # Heat flow equations
        Q_winding_core = (T_winding - T_core) / self.R_winding_core
        Q_core_frame = (T_core - T_frame) / self.R_core_frame
        Q_frame_ambient = (T_frame - self.T_ambient) / self.R_frame_ambient

        # Temperature derivatives
        dT_winding_dt = (P_copper - Q_winding_core) / self.C_winding
        dT_core_dt = (P_iron + Q_winding_core - Q_core_frame) / self.C_core
        dT_frame_dt = (P_friction + Q_core_frame - Q_frame_ambient) / self.C_frame

        return [dT_winding_dt, dT_core_dt, dT_frame_dt]

    def simulate_thermal(self, t_span, T0, P_losses, method='RK45'):
        """Simulate thermal behavior"""
        sol = solve_ivp(lambda t, T: self.thermal_network(t, T, P_losses),
                       t_span, T0, method=method, max_step=1.0)
        return sol

    def calculate_derating(self, T_winding):
        """Calculate power derating based on temperature"""
        if T_winding <= self.T_max_winding:
            derating_factor = 1.0
        else:
            # Linear derating above max temperature
            derating_factor = max(0, 1.0 - 0.02 * (T_winding - self.T_max_winding))

        return derating_factor


class LossAnalysis:
    """
    Detailed loss calculation and efficiency analysis
    """

    def __init__(self, params):
        self.params = params
        self.Ra = params.get('Ra', 0.01)  # Armature resistance (p.u.)
        self.Rf = params.get('Rf', 50)  # Field resistance (Ohms)

    def calculate_copper_losses(self, Ia, If):
        """Calculate copper losses in stator and rotor"""
        # Stator copper loss (3-phase)
        P_copper_stator = 3 * Ia**2 * self.Ra

        # Rotor (field) copper loss
        P_copper_rotor = If**2 * self.Rf

        return P_copper_stator, P_copper_rotor

    def calculate_iron_losses(self, V, f, B_max):
        """
        Calculate iron losses (hysteresis + eddy current)
        Steinmetz equation: P_iron = k_h * f * B^2 + k_e * f^2 * B^2
        """
        k_h = self.params.get('k_h', 0.001)
        k_e = self.params.get('k_e', 0.0001)

        P_hysteresis = k_h * f * B_max**2
        P_eddy = k_e * f**2 * B_max**2

        return P_hysteresis, P_eddy

    def calculate_mechanical_losses(self, speed_rpm):
        """Calculate friction and windage losses"""
        # Proportional to speed^2 for windage, linear for friction
        P_friction = self.params.get('k_friction', 500) * (speed_rpm / 1800)
        P_windage = self.params.get('k_windage', 300) * (speed_rpm / 1800)**2

        return P_friction, P_windage

    def calculate_stray_losses(self, P_output):
        """Calculate stray load losses (typically 1% of output)"""
        return 0.01 * P_output

    def calculate_efficiency(self, P_output, P_losses_total):
        """Calculate efficiency"""
        P_input = P_output + P_losses_total
        if P_input > 0:
            efficiency = (P_output / P_input) * 100
        else:
            efficiency = 0
        return efficiency

    def get_loss_breakdown(self, operating_point):
        """Get detailed loss breakdown for operating point"""
        Ia = operating_point.get('Ia', 0)
        If = operating_point.get('If', 0)
        V = operating_point.get('V', 0)
        f = operating_point.get('f', 60)
        B_max = operating_point.get('B_max', 1.0)
        speed_rpm = operating_point.get('speed_rpm', 1800)
        P_output = operating_point.get('P_output', 0)

        P_cu_stator, P_cu_rotor = self.calculate_copper_losses(Ia, If)
        P_hyst, P_eddy = self.calculate_iron_losses(V, f, B_max)
        P_fric, P_wind = self.calculate_mechanical_losses(speed_rpm)
        P_stray = self.calculate_stray_losses(P_output)

        losses = {
            'Copper_Stator': P_cu_stator,
            'Copper_Rotor': P_cu_rotor,
            'Hysteresis': P_hyst,
            'Eddy_Current': P_eddy,
            'Friction': P_fric,
            'Windage': P_wind,
            'Stray': P_stray,
            'Total': P_cu_stator + P_cu_rotor + P_hyst + P_eddy + P_fric + P_wind + P_stray
        }

        efficiency = self.calculate_efficiency(P_output, losses['Total'])

        return losses, efficiency


class EconomicAnalysis:
    """
    Economic analysis for generator operation
    Includes cost calculation, energy pricing, and optimization
    """

    def __init__(self):
        self.electricity_price = 0.12  # $/kWh
        self.fuel_cost = 0.05  # $/kWh thermal
        self.maintenance_cost = 0.02  # $/kWh
        self.capital_cost_per_kw = 800  # $/kW
        self.lifetime_years = 20
        self.interest_rate = 0.05

    def calculate_operating_cost(self, P_output_kW, hours):
        """Calculate operating cost"""
        # Fuel cost (assuming 40% efficiency for prime mover)
        fuel_cost = (P_output_kW / 0.4) * self.fuel_cost * hours

        # Maintenance cost
        maint_cost = P_output_kW * self.maintenance_cost * hours

        total_cost = fuel_cost + maint_cost

        return {
            'fuel_cost': fuel_cost,
            'maintenance_cost': maint_cost,
            'total_cost': total_cost
        }

    def calculate_revenue(self, P_output_kW, hours):
        """Calculate revenue from electricity sales"""
        return P_output_kW * self.electricity_price * hours

    def calculate_payback_period(self, capacity_kW, annual_hours):
        """Calculate simple payback period"""
        capital_cost = capacity_kW * self.capital_cost_per_kw
        annual_revenue = self.calculate_revenue(capacity_kW, annual_hours)
        annual_cost = self.calculate_operating_cost(capacity_kW, annual_hours)['total_cost']
        annual_net = annual_revenue - annual_cost

        if annual_net > 0:
            payback_years = capital_cost / annual_net
        else:
            payback_years = float('inf')

        return payback_years

    def calculate_npv(self, capacity_kW, annual_hours):
        """Calculate Net Present Value"""
        capital_cost = capacity_kW * self.capital_cost_per_kw
        annual_revenue = self.calculate_revenue(capacity_kW, annual_hours)
        annual_cost = self.calculate_operating_cost(capacity_kW, annual_hours)['total_cost']
        annual_net = annual_revenue - annual_cost

        # Calculate NPV
        npv = -capital_cost
        for year in range(1, self.lifetime_years + 1):
            npv += annual_net / ((1 + self.interest_rate) ** year)

        return npv


class AdvancedGeneratorLabGUI:
    """
    Main GUI application for advanced synchronous generator laboratory
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Synchronous Generator Laboratory - Multi-Physics Simulation")
        self.root.geometry("1400x900")

        # Make window responsive
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Initialize calculation engines
        self.calculator = SynchronousGeneratorCalculator()
        self.is_simulation_running = False
        self.simulation_data = {'time': [], 'delta': [], 'omega': [], 'power': [],
                               'T_winding': [], 'T_core': [], 'T_frame': []}

        # Create main menu
        self.create_menu()

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Create tabs
        self.create_problem_solution_tab()
        self.create_dynamic_simulation_tab()
        self.create_thermal_analysis_tab()
        self.create_loss_analysis_tab()
        self.create_economic_analysis_tab()
        self.create_control_systems_tab()

        # Status bar
        self.status_bar = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky='ew')

        # Bind resize event
        self.root.bind('<Configure>', self.on_resize)

    def create_menu(self):
        """Create main menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_command(label="Load Configuration", command=self.load_config)
        file_menu.add_command(label="Save Configuration", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Start", command=self.start_simulation)
        sim_menu.add_command(label="Stop", command=self.stop_simulation)
        sim_menu.add_command(label="Reset", command=self.reset_simulation)

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Solve Part (a)", command=self.solve_part_a)
        analysis_menu.add_command(label="Solve Part (b)", command=self.solve_part_b)
        analysis_menu.add_command(label="Run Thermal Analysis", command=self.run_thermal_analysis)
        analysis_menu.add_command(label="Calculate Losses", command=self.calculate_losses)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_documentation)

    def create_problem_solution_tab(self):
        """Tab for solving the original generator problem"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Problem Solution")

        # Configure grid
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = tk.Label(tab, text="Parallel Synchronous Generators Problem",
                        font=('Arial', 14, 'bold'))
        title.grid(row=0, column=0, pady=10)

        # Main container
        main_frame = ttk.Frame(tab)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Left panel - Input parameters
        input_frame = ttk.LabelFrame(main_frame, text="Generator Parameters", padding=10)
        input_frame.grid(row=0, column=0, sticky='nsew', padx=5)

        # Generator A parameters
        ttk.Label(input_frame, text="Generator A", font=('Arial', 11, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=5)
        ttk.Label(input_frame, text="Rated Power (kW):").grid(row=1, column=0, sticky='w')
        ttk.Label(input_frame, text="500").grid(row=1, column=1, sticky='w')
        ttk.Label(input_frame, text="Rated Field Current (A):").grid(row=2, column=0, sticky='w')
        ttk.Label(input_frame, text="21.0").grid(row=2, column=1, sticky='w')
        ttk.Label(input_frame, text="Synchronous Reactance (p.u.):").grid(row=3, column=0, sticky='w')
        ttk.Label(input_frame, text="1.5").grid(row=3, column=1, sticky='w')

        ttk.Separator(input_frame, orient='horizontal').grid(row=4, column=0, columnspan=2,
                                                            sticky='ew', pady=10)

        # Generator B parameters
        ttk.Label(input_frame, text="Generator B", font=('Arial', 11, 'bold')).grid(
            row=5, column=0, columnspan=2, pady=5)
        ttk.Label(input_frame, text="Rated Power (kW):").grid(row=6, column=0, sticky='w')
        ttk.Label(input_frame, text="350").grid(row=6, column=1, sticky='w')
        ttk.Label(input_frame, text="Rated Field Current (A):").grid(row=7, column=0, sticky='w')
        ttk.Label(input_frame, text="16.0").grid(row=7, column=1, sticky='w')
        ttk.Label(input_frame, text="Synchronous Reactance (p.u.):").grid(row=8, column=0, sticky='w')
        ttk.Label(input_frame, text="1.6").grid(row=8, column=1, sticky='w')

        ttk.Separator(input_frame, orient='horizontal').grid(row=9, column=0, columnspan=2,
                                                            sticky='ew', pady=10)

        # Common parameters
        ttk.Label(input_frame, text="Common Parameters", font=('Arial', 11, 'bold')).grid(
            row=10, column=0, columnspan=2, pady=5)
        ttk.Label(input_frame, text="Terminal Voltage (V):").grid(row=11, column=0, sticky='w')
        ttk.Label(input_frame, text="6300").grid(row=11, column=1, sticky='w')
        ttk.Label(input_frame, text="Power Factor:").grid(row=12, column=0, sticky='w')
        ttk.Label(input_frame, text="0.85 lagging").grid(row=12, column=1, sticky='w')

        # Right panel - Results
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Buttons
        button_frame = ttk.Frame(results_frame)
        button_frame.grid(row=0, column=0, pady=5)

        ttk.Button(button_frame, text="Solve Part (a)", command=self.solve_part_a).pack(
            side='left', padx=5)
        ttk.Button(button_frame, text="Solve Part (b)", command=self.solve_part_b).pack(
            side='left', padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_results).pack(
            side='left', padx=5)

        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, height=25, width=60,
                                                       font=('Courier', 10))
        self.results_text.grid(row=1, column=0, sticky='nsew', pady=5)

    def create_dynamic_simulation_tab(self):
        """Tab for dynamic simulation with ODE solvers"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dynamic Simulation")

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=3)
        tab.grid_columnconfigure(1, weight=1)

        # Title
        title = tk.Label(tab, text="Real-Time Dynamic Simulation",
                        font=('Arial', 14, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=10)

        # Left panel - Visualization
        viz_frame = ttk.LabelFrame(tab, text="Dynamic Response", padding=5)
        viz_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        viz_frame.grid_rowconfigure(0, weight=1)
        viz_frame.grid_columnconfigure(0, weight=1)

        # Create matplotlib figure
        self.fig_dynamic = Figure(figsize=(8, 6), dpi=80)
        self.ax_delta = self.fig_dynamic.add_subplot(311)
        self.ax_omega = self.fig_dynamic.add_subplot(312)
        self.ax_power = self.fig_dynamic.add_subplot(313)

        self.ax_delta.set_ylabel('Angle δ (deg)')
        self.ax_delta.grid(True)
        self.ax_omega.set_ylabel('Speed ω (rad/s)')
        self.ax_omega.grid(True)
        self.ax_power.set_ylabel('Power (p.u.)')
        self.ax_power.set_xlabel('Time (s)')
        self.ax_power.grid(True)

        self.fig_dynamic.tight_layout()

        self.canvas_dynamic = FigureCanvasTkAgg(self.fig_dynamic, viz_frame)
        self.canvas_dynamic.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Right panel - Controls
        control_frame = ttk.LabelFrame(tab, text="Simulation Controls", padding=10)
        control_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

        # ODE Solver selection
        ttk.Label(control_frame, text="ODE Solver:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', pady=5)
        self.solver_var = tk.StringVar(value='RK45')
        ttk.Radiobutton(control_frame, text="RK45 (Adaptive)", variable=self.solver_var,
                       value='RK45').grid(row=1, column=0, sticky='w')
        ttk.Radiobutton(control_frame, text="Euler (Fixed Step)", variable=self.solver_var,
                       value='Euler').grid(row=2, column=0, sticky='w')

        ttk.Separator(control_frame, orient='horizontal').grid(row=3, column=0,
                                                              sticky='ew', pady=10)

        # Parameters
        ttk.Label(control_frame, text="Parameters:", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky='w', pady=5)

        # Mechanical power
        ttk.Label(control_frame, text="Mechanical Power (p.u.):").grid(
            row=5, column=0, sticky='w', pady=2)
        self.Pm_var = tk.DoubleVar(value=0.8)
        self.Pm_scale = ttk.Scale(control_frame, from_=0, to=2, orient='horizontal',
                                  variable=self.Pm_var, length=200)
        self.Pm_scale.grid(row=6, column=0, sticky='ew', pady=2)
        self.Pm_label = ttk.Label(control_frame, text="0.80")
        self.Pm_label.grid(row=7, column=0, sticky='w')
        self.Pm_var.trace('w', self.update_Pm_label)

        # Field voltage
        ttk.Label(control_frame, text="Field Voltage (p.u.):").grid(
            row=8, column=0, sticky='w', pady=2)
        self.Ef_var = tk.DoubleVar(value=1.2)
        self.Ef_scale = ttk.Scale(control_frame, from_=0, to=3, orient='horizontal',
                                  variable=self.Ef_var, length=200)
        self.Ef_scale.grid(row=9, column=0, sticky='ew', pady=2)
        self.Ef_label = ttk.Label(control_frame, text="1.20")
        self.Ef_label.grid(row=10, column=0, sticky='w')
        self.Ef_var.trace('w', self.update_Ef_label)

        # Inertia constant
        ttk.Label(control_frame, text="Inertia H (s):").grid(
            row=11, column=0, sticky='w', pady=2)
        self.H_var = tk.DoubleVar(value=3.5)
        self.H_scale = ttk.Scale(control_frame, from_=1, to=10, orient='horizontal',
                                 variable=self.H_var, length=200)
        self.H_scale.grid(row=12, column=0, sticky='ew', pady=2)
        self.H_label = ttk.Label(control_frame, text="3.50")
        self.H_label.grid(row=13, column=0, sticky='w')
        self.H_var.trace('w', self.update_H_label)

        ttk.Separator(control_frame, orient='horizontal').grid(row=14, column=0,
                                                              sticky='ew', pady=10)

        # Control buttons
        ttk.Label(control_frame, text="Control:", font=('Arial', 10, 'bold')).grid(
            row=15, column=0, sticky='w', pady=5)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=16, column=0, pady=5)

        self.btn_start = ttk.Button(btn_frame, text="Start", command=self.start_simulation,
                                     width=12)
        self.btn_start.pack(pady=2)

        self.btn_stop = ttk.Button(btn_frame, text="Stop", command=self.stop_simulation,
                                    width=12, state='disabled')
        self.btn_stop.pack(pady=2)

        self.btn_reset = ttk.Button(btn_frame, text="Reset", command=self.reset_simulation,
                                     width=12)
        self.btn_reset.pack(pady=2)

    def create_thermal_analysis_tab(self):
        """Tab for thermal analysis and derating"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Thermal Analysis")

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = tk.Label(tab, text="Multi-Node Thermal Analysis & Derating",
                        font=('Arial', 14, 'bold'))
        title.grid(row=0, column=0, pady=10)

        # Main container
        main_frame = ttk.Frame(tab)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)

        # Left panel - Temperature plots
        plot_frame = ttk.LabelFrame(main_frame, text="Temperature Distribution", padding=5)
        plot_frame.grid(row=0, column=0, sticky='nsew', padx=5)
        plot_frame.grid_rowconfigure(0, weight=1)
        plot_frame.grid_columnconfigure(0, weight=1)

        self.fig_thermal = Figure(figsize=(7, 6), dpi=80)
        self.ax_temp = self.fig_thermal.add_subplot(211)
        self.ax_derating = self.fig_thermal.add_subplot(212)

        self.ax_temp.set_ylabel('Temperature (°C)')
        self.ax_temp.set_xlabel('Time (s)')
        self.ax_temp.grid(True)
        self.ax_temp.legend(['Winding', 'Core', 'Frame'])

        self.ax_derating.set_ylabel('Derating Factor')
        self.ax_derating.set_xlabel('Time (s)')
        self.ax_derating.grid(True)

        self.fig_thermal.tight_layout()

        self.canvas_thermal = FigureCanvasTkAgg(self.fig_thermal, plot_frame)
        self.canvas_thermal.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Right panel - Parameters and results
        param_frame = ttk.LabelFrame(main_frame, text="Thermal Parameters", padding=10)
        param_frame.grid(row=0, column=1, sticky='nsew', padx=5)

        # Loss inputs
        ttk.Label(param_frame, text="Losses (W):", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=5)

        ttk.Label(param_frame, text="Copper Losses:").grid(row=1, column=0, sticky='w')
        self.P_copper_entry = ttk.Entry(param_frame, width=15)
        self.P_copper_entry.insert(0, "5000")
        self.P_copper_entry.grid(row=1, column=1, pady=2)

        ttk.Label(param_frame, text="Iron Losses:").grid(row=2, column=0, sticky='w')
        self.P_iron_entry = ttk.Entry(param_frame, width=15)
        self.P_iron_entry.insert(0, "3000")
        self.P_iron_entry.grid(row=2, column=1, pady=2)

        ttk.Label(param_frame, text="Friction Losses:").grid(row=3, column=0, sticky='w')
        self.P_friction_entry = ttk.Entry(param_frame, width=15)
        self.P_friction_entry.insert(0, "800")
        self.P_friction_entry.grid(row=3, column=1, pady=2)

        ttk.Separator(param_frame, orient='horizontal').grid(row=4, column=0, columnspan=2,
                                                            sticky='ew', pady=10)

        # Thermal resistances
        ttk.Label(param_frame, text="Thermal Resistances (K/W):",
                 font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=2,
                                                 sticky='w', pady=5)

        ttk.Label(param_frame, text="Winding-Core:").grid(row=6, column=0, sticky='w')
        self.R_wc_entry = ttk.Entry(param_frame, width=15)
        self.R_wc_entry.insert(0, "0.05")
        self.R_wc_entry.grid(row=6, column=1, pady=2)

        ttk.Label(param_frame, text="Core-Frame:").grid(row=7, column=0, sticky='w')
        self.R_cf_entry = ttk.Entry(param_frame, width=15)
        self.R_cf_entry.insert(0, "0.03")
        self.R_cf_entry.grid(row=7, column=1, pady=2)

        ttk.Label(param_frame, text="Frame-Ambient:").grid(row=8, column=0, sticky='w')
        self.R_fa_entry = ttk.Entry(param_frame, width=15)
        self.R_fa_entry.insert(0, "0.02")
        self.R_fa_entry.grid(row=8, column=1, pady=2)

        ttk.Separator(param_frame, orient='horizontal').grid(row=9, column=0, columnspan=2,
                                                            sticky='ew', pady=10)

        # Buttons
        ttk.Button(param_frame, text="Run Thermal Analysis",
                  command=self.run_thermal_analysis).grid(row=10, column=0,
                                                         columnspan=2, pady=10)

        # Results display
        ttk.Label(param_frame, text="Results:", font=('Arial', 10, 'bold')).grid(
            row=11, column=0, columnspan=2, sticky='w', pady=5)

        self.thermal_results_text = scrolledtext.ScrolledText(param_frame, height=10,
                                                             width=30, font=('Courier', 9))
        self.thermal_results_text.grid(row=12, column=0, columnspan=2, sticky='nsew', pady=5)

    def create_loss_analysis_tab(self):
        """Tab for detailed loss breakdown"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Loss Analysis")

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = tk.Label(tab, text="Detailed Loss Breakdown & Efficiency Analysis",
                        font=('Arial', 14, 'bold'))
        title.grid(row=0, column=0, pady=10)

        # Main container
        main_frame = ttk.Frame(tab)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Left panel - Loss pie chart
        chart_frame = ttk.LabelFrame(main_frame, text="Loss Distribution", padding=5)
        chart_frame.grid(row=0, column=0, sticky='nsew', padx=5)
        chart_frame.grid_rowconfigure(0, weight=1)
        chart_frame.grid_columnconfigure(0, weight=1)

        self.fig_loss = Figure(figsize=(6, 6), dpi=80)
        self.ax_pie = self.fig_loss.add_subplot(111)

        self.canvas_loss = FigureCanvasTkAgg(self.fig_loss, chart_frame)
        self.canvas_loss.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Right panel - Parameters and results
        loss_param_frame = ttk.LabelFrame(main_frame, text="Operating Point", padding=10)
        loss_param_frame.grid(row=0, column=1, sticky='nsew', padx=5)

        # Operating parameters
        ttk.Label(loss_param_frame, text="Operating Conditions:",
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2,
                                                 sticky='w', pady=5)

        ttk.Label(loss_param_frame, text="Output Power (kW):").grid(row=1, column=0, sticky='w')
        self.P_out_entry = ttk.Entry(loss_param_frame, width=15)
        self.P_out_entry.insert(0, "400")
        self.P_out_entry.grid(row=1, column=1, pady=2)

        ttk.Label(loss_param_frame, text="Armature Current (A):").grid(row=2, column=0, sticky='w')
        self.Ia_entry = ttk.Entry(loss_param_frame, width=15)
        self.Ia_entry.insert(0, "50")
        self.Ia_entry.grid(row=2, column=1, pady=2)

        ttk.Label(loss_param_frame, text="Field Current (A):").grid(row=3, column=0, sticky='w')
        self.If_entry = ttk.Entry(loss_param_frame, width=15)
        self.If_entry.insert(0, "20")
        self.If_entry.grid(row=3, column=1, pady=2)

        ttk.Label(loss_param_frame, text="Voltage (V):").grid(row=4, column=0, sticky='w')
        self.V_entry = ttk.Entry(loss_param_frame, width=15)
        self.V_entry.insert(0, "6300")
        self.V_entry.grid(row=4, column=1, pady=2)

        ttk.Label(loss_param_frame, text="Speed (rpm):").grid(row=5, column=0, sticky='w')
        self.speed_entry = ttk.Entry(loss_param_frame, width=15)
        self.speed_entry.insert(0, "1800")
        self.speed_entry.grid(row=5, column=1, pady=2)

        ttk.Separator(loss_param_frame, orient='horizontal').grid(row=6, column=0,
                                                                 columnspan=2, sticky='ew', pady=10)

        # Calculate button
        ttk.Button(loss_param_frame, text="Calculate Losses & Efficiency",
                  command=self.calculate_losses).grid(row=7, column=0, columnspan=2, pady=10)

        # Results
        ttk.Label(loss_param_frame, text="Results:", font=('Arial', 10, 'bold')).grid(
            row=8, column=0, columnspan=2, sticky='w', pady=5)

        self.loss_results_text = scrolledtext.ScrolledText(loss_param_frame, height=15,
                                                          width=35, font=('Courier', 9))
        self.loss_results_text.grid(row=9, column=0, columnspan=2, sticky='nsew', pady=5)
        loss_param_frame.grid_rowconfigure(9, weight=1)

    def create_economic_analysis_tab(self):
        """Tab for economic analysis"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Economic Analysis")

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = tk.Label(tab, text="Economic Analysis & Investment Evaluation",
                        font=('Arial', 14, 'bold'))
        title.grid(row=0, column=0, pady=10)

        # Main container
        main_frame = ttk.Frame(tab)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Left panel - Parameters
        param_frame = ttk.LabelFrame(main_frame, text="Economic Parameters", padding=10)
        param_frame.grid(row=0, column=0, sticky='nsew', padx=5)

        ttk.Label(param_frame, text="Generator Capacity (kW):").grid(row=0, column=0, sticky='w')
        self.capacity_entry = ttk.Entry(param_frame, width=15)
        self.capacity_entry.insert(0, "500")
        self.capacity_entry.grid(row=0, column=1, pady=3)

        ttk.Label(param_frame, text="Annual Operating Hours:").grid(row=1, column=0, sticky='w')
        self.hours_entry = ttk.Entry(param_frame, width=15)
        self.hours_entry.insert(0, "6000")
        self.hours_entry.grid(row=1, column=1, pady=3)

        ttk.Label(param_frame, text="Electricity Price ($/kWh):").grid(row=2, column=0, sticky='w')
        self.price_entry = ttk.Entry(param_frame, width=15)
        self.price_entry.insert(0, "0.12")
        self.price_entry.grid(row=2, column=1, pady=3)

        ttk.Label(param_frame, text="Fuel Cost ($/kWh thermal):").grid(row=3, column=0, sticky='w')
        self.fuel_entry = ttk.Entry(param_frame, width=15)
        self.fuel_entry.insert(0, "0.05")
        self.fuel_entry.grid(row=3, column=1, pady=3)

        ttk.Label(param_frame, text="Maintenance Cost ($/kWh):").grid(row=4, column=0, sticky='w')
        self.maint_entry = ttk.Entry(param_frame, width=15)
        self.maint_entry.insert(0, "0.02")
        self.maint_entry.grid(row=4, column=1, pady=3)

        ttk.Label(param_frame, text="Capital Cost ($/kW):").grid(row=5, column=0, sticky='w')
        self.capital_entry = ttk.Entry(param_frame, width=15)
        self.capital_entry.insert(0, "800")
        self.capital_entry.grid(row=5, column=1, pady=3)

        ttk.Label(param_frame, text="Interest Rate (%):").grid(row=6, column=0, sticky='w')
        self.interest_entry = ttk.Entry(param_frame, width=15)
        self.interest_entry.insert(0, "5")
        self.interest_entry.grid(row=6, column=1, pady=3)

        ttk.Label(param_frame, text="Lifetime (years):").grid(row=7, column=0, sticky='w')
        self.lifetime_entry = ttk.Entry(param_frame, width=15)
        self.lifetime_entry.insert(0, "20")
        self.lifetime_entry.grid(row=7, column=1, pady=3)

        ttk.Button(param_frame, text="Calculate Economics",
                  command=self.calculate_economics).grid(row=8, column=0, columnspan=2, pady=15)

        # Right panel - Results
        results_frame = ttk.LabelFrame(main_frame, text="Economic Results", padding=10)
        results_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        self.econ_results_text = scrolledtext.ScrolledText(results_frame, height=20,
                                                          width=50, font=('Courier', 10))
        self.econ_results_text.grid(row=0, column=0, sticky='nsew')

    def create_control_systems_tab(self):
        """Tab for advanced control systems"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Control Systems")

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title = tk.Label(tab, text="Advanced Generator Control Systems",
                        font=('Arial', 14, 'bold'))
        title.grid(row=0, column=0, pady=10)

        # Main container
        main_frame = ttk.Frame(tab)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Notebook for control types
        control_notebook = ttk.Notebook(main_frame)
        control_notebook.grid(row=0, column=0, sticky='nsew')

        # AVR tab
        avr_frame = ttk.Frame(control_notebook)
        control_notebook.add(avr_frame, text="Automatic Voltage Regulator")

        ttk.Label(avr_frame, text="AVR Type:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', padx=10, pady=10)
        self.avr_type = tk.StringVar(value='PID')
        ttk.Radiobutton(avr_frame, text="PID Controller", variable=self.avr_type,
                       value='PID').grid(row=1, column=0, sticky='w', padx=20)
        ttk.Radiobutton(avr_frame, text="Adaptive Control", variable=self.avr_type,
                       value='Adaptive').grid(row=2, column=0, sticky='w', padx=20)

        # Governor tab
        gov_frame = ttk.Frame(control_notebook)
        control_notebook.add(gov_frame, text="Speed Governor")

        ttk.Label(gov_frame, text="Governor Type:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', padx=10, pady=10)
        self.gov_type = tk.StringVar(value='Isochronous')
        ttk.Radiobutton(gov_frame, text="Isochronous", variable=self.gov_type,
                       value='Isochronous').grid(row=1, column=0, sticky='w', padx=20)
        ttk.Radiobutton(gov_frame, text="Droop Control", variable=self.gov_type,
                       value='Droop').grid(row=2, column=0, sticky='w', padx=20)

        # Protection tab
        prot_frame = ttk.Frame(control_notebook)
        control_notebook.add(prot_frame, text="Protection Systems")

        ttk.Label(prot_frame, text="Protection Features:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', padx=10, pady=10)

        self.overcurrent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prot_frame, text="Overcurrent Protection",
                       variable=self.overcurrent_var).grid(row=1, column=0, sticky='w', padx=20)

        self.overvoltage_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prot_frame, text="Overvoltage Protection",
                       variable=self.overvoltage_var).grid(row=2, column=0, sticky='w', padx=20)

        self.underfreq_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prot_frame, text="Under-frequency Protection",
                       variable=self.underfreq_var).grid(row=3, column=0, sticky='w', padx=20)

        self.thermal_prot_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(prot_frame, text="Thermal Overload Protection",
                       variable=self.thermal_prot_var).grid(row=4, column=0, sticky='w', padx=20)

    # Callback functions for sliders
    def update_Pm_label(self, *args):
        self.Pm_label.config(text=f"{self.Pm_var.get():.2f}")

    def update_Ef_label(self, *args):
        self.Ef_label.config(text=f"{self.Ef_var.get():.2f}")

    def update_H_label(self, *args):
        self.H_label.config(text=f"{self.H_var.get():.2f}")

    def on_resize(self, event):
        """Handle window resize events"""
        pass  # Auto-scaling handled by grid weight configuration

    # Problem solution methods
    def solve_part_a(self):
        """Solve part (a) of the problem"""
        self.status_bar.config(text="Calculating part (a)...")

        try:
            results = self.calculator.solve_part_a()

            output = "=" * 60 + "\n"
            output += "PART (a) SOLUTION\n"
            output += "=" * 60 + "\n\n"
            output += "Given Conditions:\n"
            output += f"  Total Load: 720 kW at 0.8 pf lagging\n"
            output += f"  Generator A: IfA = 20 A, PA = 360 kW\n"
            output += f"  Generator B: PB = 360 kW\n"
            output += f"  Terminal Voltage: V = Vn = 6300 V\n\n"
            output += "-" * 60 + "\n"
            output += "Results:\n"
            output += "-" * 60 + "\n"
            output += f"  Field Current of Generator B:  IfB = {results['IfB']:.3f} A\n"
            output += f"  EMF of Generator B:            EfB = {results['EfB']:.2f} V\n\n"
            output += "Power Distribution:\n"
            output += f"  Generator A:  PA = {results['PA']:.2f} kW,  QA = {results['QA']:.2f} kVAR\n"
            output += f"  Generator B:  PB = {results['PB']:.2f} kW,  QB = {results['QB']:.2f} kVAR\n\n"
            output += "Power Angles:\n"
            output += f"  Generator A:  δA = {results['delta_A_deg']:.2f}°\n"
            output += f"  Generator B:  δB = {results['delta_B_deg']:.2f}°\n\n"
            output += "EMF Coefficients:\n"
            output += f"  Generator A:  k_emf = {results['k_emfA']:.2f} V/A\n"
            output += f"  Generator B:  k_emf = {results['k_emfB']:.2f} V/A\n"
            output += "=" * 60 + "\n"

            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, output)

            self.status_bar.config(text="Part (a) calculation completed successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")
            self.status_bar.config(text="Error in calculation")

    def solve_part_b(self):
        """Solve part (b) of the problem"""
        self.status_bar.config(text="Calculating part (b)...")

        try:
            results = self.calculator.solve_part_b()

            output = "=" * 60 + "\n"
            output += "PART (b) SOLUTION\n"
            output += "=" * 60 + "\n\n"
            output += "Given Conditions:\n"
            output += f"  Additional Load: 130 kW at unity pf\n"
            output += f"  Total Load: 850 kW\n"
            output += f"  Generator B: Same conditions as part (a)\n\n"
            output += "-" * 60 + "\n"
            output += "Results:\n"
            output += "-" * 60 + "\n"
            output += f"  New Field Current of Gen A:   IfA = {results['IfA_new']:.3f} A\n"
            output += f"  New EMF of Generator A:       EfA = {results['EfA_new']:.2f} V\n\n"
            output += "New Power Distribution:\n"
            output += f"  Generator A:  PA = {results['PA_new']:.2f} kW,  QA = {results['QA_new']:.2f} kVAR\n"
            output += f"  Generator B:  PB = {results['PB_new']:.2f} kW,  QB = {results['QB_new']:.2f} kVAR\n\n"
            output += "New Power Angles:\n"
            output += f"  Generator A:  δA = {results['delta_A_new_deg']:.2f}°\n"
            output += f"  Generator B:  δB = {results['delta_B_new_deg']:.2f}°\n"
            output += "=" * 60 + "\n"

            self.results_text.insert(tk.END, "\n\n" + output)

            self.status_bar.config(text="Part (b) calculation completed successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")
            self.status_bar.config(text="Error in calculation")

    def clear_results(self):
        """Clear results text area"""
        self.results_text.delete(1.0, tk.END)
        self.status_bar.config(text="Results cleared")

    # Simulation methods
    def start_simulation(self):
        """Start dynamic simulation"""
        if self.is_simulation_running:
            messagebox.showwarning("Warning", "Simulation is already running")
            return

        self.is_simulation_running = True
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.status_bar.config(text="Simulation running...")

        # Run simulation
        try:
            params = {
                'H': self.H_var.get(),
                'D': 2.0,
                'Xd': 1.5,
                'Xq': 1.5,
                'Xd_prime': 0.3,
                'Td0_prime': 5.0,
                'freq': 60
            }

            dynamics = SynchronousGeneratorDynamics(params)

            # Initial conditions
            delta0 = 30 * np.pi / 180  # 30 degrees
            omega0 = 2 * np.pi * 60  # Synchronous speed
            Eq_prime0 = 1.0  # p.u.
            y0 = [delta0, omega0, Eq_prime0]

            # Simulate
            t_span = [0, 5]  # 5 seconds
            Pm = self.Pm_var.get()
            Ef = self.Ef_var.get()
            V = 1.0  # p.u.

            method = self.solver_var.get()
            sol = dynamics.simulate(t_span, y0, Pm, Ef, V, method=method)

            # Plot results
            self.ax_delta.clear()
            self.ax_omega.clear()
            self.ax_power.clear()

            delta_deg = np.degrees(sol.y[0])
            omega_rpm = sol.y[1] * 60 / (2 * np.pi)

            # Calculate power
            Pe = (sol.y[2] * V / params['Xd_prime']) * np.sin(sol.y[0])

            self.ax_delta.plot(sol.t, delta_deg)
            self.ax_delta.set_ylabel('Angle δ (deg)')
            self.ax_delta.grid(True)
            self.ax_delta.set_title(f'Dynamic Response ({method} solver)')

            self.ax_omega.plot(sol.t, omega_rpm)
            self.ax_omega.set_ylabel('Speed (rpm)')
            self.ax_omega.axhline(y=1800, color='r', linestyle='--', label='Synchronous')
            self.ax_omega.grid(True)
            self.ax_omega.legend()

            self.ax_power.plot(sol.t, Pe, label='Electrical')
            self.ax_power.axhline(y=Pm, color='r', linestyle='--', label='Mechanical')
            self.ax_power.set_ylabel('Power (p.u.)')
            self.ax_power.set_xlabel('Time (s)')
            self.ax_power.grid(True)
            self.ax_power.legend()

            self.fig_dynamic.tight_layout()
            self.canvas_dynamic.draw()

            # Store data
            self.simulation_data['time'] = sol.t.tolist()
            self.simulation_data['delta'] = delta_deg.tolist()
            self.simulation_data['omega'] = omega_rpm.tolist()
            self.simulation_data['power'] = Pe.tolist()

            self.status_bar.config(text="Simulation completed successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Simulation error: {str(e)}")
            self.status_bar.config(text="Simulation error")

        finally:
            self.is_simulation_running = False
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')

    def stop_simulation(self):
        """Stop running simulation"""
        self.is_simulation_running = False
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
        self.status_bar.config(text="Simulation stopped")

    def reset_simulation(self):
        """Reset simulation parameters and plots"""
        self.simulation_data = {'time': [], 'delta': [], 'omega': [], 'power': [],
                               'T_winding': [], 'T_core': [], 'T_frame': []}

        self.ax_delta.clear()
        self.ax_omega.clear()
        self.ax_power.clear()

        self.ax_delta.set_ylabel('Angle δ (deg)')
        self.ax_delta.grid(True)
        self.ax_omega.set_ylabel('Speed ω (rad/s)')
        self.ax_omega.grid(True)
        self.ax_power.set_ylabel('Power (p.u.)')
        self.ax_power.set_xlabel('Time (s)')
        self.ax_power.grid(True)

        self.canvas_dynamic.draw()

        self.status_bar.config(text="Simulation reset")

    def run_thermal_analysis(self):
        """Run thermal analysis"""
        self.status_bar.config(text="Running thermal analysis...")

        try:
            # Get parameters
            P_copper = float(self.P_copper_entry.get())
            P_iron = float(self.P_iron_entry.get())
            P_friction = float(self.P_friction_entry.get())

            R_wc = float(self.R_wc_entry.get())
            R_cf = float(self.R_cf_entry.get())
            R_fa = float(self.R_fa_entry.get())

            params = {
                'C_winding': 5000,
                'C_core': 8000,
                'C_frame': 3000,
                'R_winding_core': R_wc,
                'R_core_frame': R_cf,
                'R_frame_ambient': R_fa,
                'T_ambient': 25,
                'T_max_winding': 130,
                'T_max_core': 110
            }

            thermal = ThermalModel(params)

            # Initial temperatures (all at ambient)
            T0 = [25, 25, 25]

            # Simulate
            t_span = [0, 3600]  # 1 hour
            P_losses = (P_copper, P_iron, P_friction)

            sol = thermal.simulate_thermal(t_span, T0, P_losses)

            # Plot results
            self.ax_temp.clear()
            self.ax_derating.clear()

            self.ax_temp.plot(sol.t / 60, sol.y[0], label='Winding', linewidth=2)
            self.ax_temp.plot(sol.t / 60, sol.y[1], label='Core', linewidth=2)
            self.ax_temp.plot(sol.t / 60, sol.y[2], label='Frame', linewidth=2)
            self.ax_temp.axhline(y=params['T_max_winding'], color='r', linestyle='--',
                                label='Max Winding Temp')
            self.ax_temp.set_ylabel('Temperature (°C)')
            self.ax_temp.set_xlabel('Time (min)')
            self.ax_temp.grid(True)
            self.ax_temp.legend()
            self.ax_temp.set_title('Temperature Distribution')

            # Calculate derating
            derating = [thermal.calculate_derating(T) for T in sol.y[0]]

            self.ax_derating.plot(sol.t / 60, derating, linewidth=2, color='orange')
            self.ax_derating.set_ylabel('Derating Factor')
            self.ax_derating.set_xlabel('Time (min)')
            self.ax_derating.grid(True)
            self.ax_derating.set_title('Power Derating vs Time')

            self.fig_thermal.tight_layout()
            self.canvas_thermal.draw()

            # Display results
            final_T_winding = sol.y[0][-1]
            final_T_core = sol.y[1][-1]
            final_T_frame = sol.y[2][-1]
            final_derating = derating[-1]

            output = "Thermal Analysis Results\n"
            output += "=" * 40 + "\n\n"
            output += "Steady-State Temperatures:\n"
            output += f"  Winding:  {final_T_winding:.2f} °C\n"
            output += f"  Core:     {final_T_core:.2f} °C\n"
            output += f"  Frame:    {final_T_frame:.2f} °C\n\n"
            output += f"Maximum Allowable:\n"
            output += f"  Winding:  {params['T_max_winding']:.2f} °C\n"
            output += f"  Core:     {params['T_max_core']:.2f} °C\n\n"
            output += f"Power Derating Factor: {final_derating:.3f}\n\n"

            if final_T_winding > params['T_max_winding']:
                output += "WARNING: Winding temperature exceeds\n"
                output += "maximum allowable temperature!\n"
                output += "Reduce loading or improve cooling.\n"
            else:
                output += "Temperature within safe limits.\n"

            self.thermal_results_text.delete(1.0, tk.END)
            self.thermal_results_text.insert(1.0, output)

            # Store data
            self.simulation_data['T_winding'] = sol.y[0].tolist()
            self.simulation_data['T_core'] = sol.y[1].tolist()
            self.simulation_data['T_frame'] = sol.y[2].tolist()

            self.status_bar.config(text="Thermal analysis completed")

        except Exception as e:
            messagebox.showerror("Error", f"Thermal analysis error: {str(e)}")
            self.status_bar.config(text="Error in thermal analysis")

    def calculate_losses(self):
        """Calculate detailed loss breakdown"""
        self.status_bar.config(text="Calculating losses...")

        try:
            # Get parameters
            P_output = float(self.P_out_entry.get()) * 1000  # Convert to W
            Ia = float(self.Ia_entry.get())
            If = float(self.If_entry.get())
            V = float(self.V_entry.get())
            speed_rpm = float(self.speed_entry.get())

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
                'Ia': Ia,
                'If': If,
                'V': V,
                'f': 60,
                'B_max': 1.0,
                'speed_rpm': speed_rpm,
                'P_output': P_output
            }

            losses, efficiency = loss_analyzer.get_loss_breakdown(operating_point)

            # Plot pie chart
            self.ax_pie.clear()

            loss_labels = ['Copper\nStator', 'Copper\nRotor', 'Hysteresis',
                          'Eddy\nCurrent', 'Friction', 'Windage', 'Stray']
            loss_values = [losses['Copper_Stator'], losses['Copper_Rotor'],
                          losses['Hysteresis'], losses['Eddy_Current'],
                          losses['Friction'], losses['Windage'], losses['Stray']]

            colors = ['#ff9999', '#ff6666', '#66b3ff', '#3399ff',
                     '#99ff99', '#66ff66', '#ffcc99']

            self.ax_pie.pie(loss_values, labels=loss_labels, autopct='%1.1f%%',
                           colors=colors, startangle=90)
            self.ax_pie.set_title('Loss Distribution')

            self.fig_loss.tight_layout()
            self.canvas_loss.draw()

            # Display results
            output = "Loss Analysis Results\n"
            output += "=" * 45 + "\n\n"
            output += "Detailed Loss Breakdown:\n"
            output += "-" * 45 + "\n"
            output += f"Copper Losses (Stator):  {losses['Copper_Stator']:>10.2f} W\n"
            output += f"Copper Losses (Rotor):   {losses['Copper_Rotor']:>10.2f} W\n"
            output += f"Hysteresis Losses:       {losses['Hysteresis']:>10.2f} W\n"
            output += f"Eddy Current Losses:     {losses['Eddy_Current']:>10.2f} W\n"
            output += f"Friction Losses:         {losses['Friction']:>10.2f} W\n"
            output += f"Windage Losses:          {losses['Windage']:>10.2f} W\n"
            output += f"Stray Load Losses:       {losses['Stray']:>10.2f} W\n"
            output += "-" * 45 + "\n"
            output += f"Total Losses:            {losses['Total']:>10.2f} W\n"
            output += f"                         {losses['Total']/1000:>10.2f} kW\n\n"
            output += f"Output Power:            {P_output/1000:>10.2f} kW\n"
            output += f"Input Power:             {(P_output+losses['Total'])/1000:>10.2f} kW\n\n"
            output += f"Efficiency:              {efficiency:>10.2f} %\n"
            output += "=" * 45 + "\n"

            self.loss_results_text.delete(1.0, tk.END)
            self.loss_results_text.insert(1.0, output)

            self.status_bar.config(text="Loss calculation completed")

        except Exception as e:
            messagebox.showerror("Error", f"Loss calculation error: {str(e)}")
            self.status_bar.config(text="Error in loss calculation")

    def calculate_economics(self):
        """Calculate economic analysis"""
        self.status_bar.config(text="Calculating economics...")

        try:
            # Get parameters
            capacity_kW = float(self.capacity_entry.get())
            annual_hours = float(self.hours_entry.get())

            econ = EconomicAnalysis()
            econ.electricity_price = float(self.price_entry.get())
            econ.fuel_cost = float(self.fuel_entry.get())
            econ.maintenance_cost = float(self.maint_entry.get())
            econ.capital_cost_per_kw = float(self.capital_entry.get())
            econ.interest_rate = float(self.interest_entry.get()) / 100
            econ.lifetime_years = int(self.lifetime_entry.get())

            # Calculate costs
            operating_costs = econ.calculate_operating_cost(capacity_kW, annual_hours)
            annual_revenue = econ.calculate_revenue(capacity_kW, annual_hours)
            payback = econ.calculate_payback_period(capacity_kW, annual_hours)
            npv = econ.calculate_npv(capacity_kW, annual_hours)

            capital_cost = capacity_kW * econ.capital_cost_per_kw

            # Display results
            output = "Economic Analysis Results\n"
            output += "=" * 60 + "\n\n"
            output += "Investment Summary:\n"
            output += "-" * 60 + "\n"
            output += f"Generator Capacity:        {capacity_kW:>12.2f} kW\n"
            output += f"Capital Cost:              ${capital_cost:>12,.2f}\n"
            output += f"Annual Operating Hours:    {annual_hours:>12.0f} hrs\n\n"

            output += "Annual Operating Costs:\n"
            output += "-" * 60 + "\n"
            output += f"Fuel Cost:                 ${operating_costs['fuel_cost']:>12,.2f}\n"
            output += f"Maintenance Cost:          ${operating_costs['maintenance_cost']:>12,.2f}\n"
            output += f"Total Operating Cost:      ${operating_costs['total_cost']:>12,.2f}\n\n"

            output += "Annual Revenue:\n"
            output += "-" * 60 + "\n"
            output += f"Electricity Sales:         ${annual_revenue:>12,.2f}\n\n"

            output += "Profitability Analysis:\n"
            output += "-" * 60 + "\n"
            output += f"Annual Net Revenue:        ${annual_revenue - operating_costs['total_cost']:>12,.2f}\n"
            output += f"Simple Payback Period:     {payback:>12.2f} years\n"
            output += f"Net Present Value (NPV):   ${npv:>12,.2f}\n\n"

            output += "Financial Indicators:\n"
            output += "-" * 60 + "\n"

            if npv > 0:
                output += "✓ NPV is POSITIVE - Investment is economically viable\n"
            else:
                output += "✗ NPV is NEGATIVE - Investment is not economically viable\n"

            if payback < econ.lifetime_years:
                output += f"✓ Payback period ({payback:.1f} yrs) is within lifetime\n"
            else:
                output += f"✗ Payback period ({payback:.1f} yrs) exceeds lifetime\n"

            output += "\n" + "=" * 60 + "\n"

            self.econ_results_text.delete(1.0, tk.END)
            self.econ_results_text.insert(1.0, output)

            self.status_bar.config(text="Economic analysis completed")

        except Exception as e:
            messagebox.showerror("Error", f"Economic analysis error: {str(e)}")
            self.status_bar.config(text="Error in economic analysis")

    # Menu action methods
    def export_results(self):
        """Export results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generator_results_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump(self.simulation_data, f, indent=2)

            messagebox.showinfo("Export Successful",
                              f"Results exported to {filename}")
            self.status_bar.config(text=f"Results exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def load_config(self):
        """Load configuration from file"""
        messagebox.showinfo("Load Configuration",
                          "Configuration loading not yet implemented")

    def save_config(self):
        """Save configuration to file"""
        messagebox.showinfo("Save Configuration",
                          "Configuration saving not yet implemented")

    def show_about(self):
        """Show about dialog"""
        about_text = """
Advanced Synchronous Generator Laboratory
Version 1.0

Multi-Physics Simulation Platform

Features:
• Parallel generator operation analysis
• Dynamic electromagnetic simulation
• Thermal analysis with derating
• Detailed loss breakdown
• Economic analysis
• Advanced control systems

Developed for electrical engineering education
and professional applications.
        """
        messagebox.showinfo("About", about_text)

    def show_documentation(self):
        """Show documentation"""
        doc_text = """
Documentation

This application provides comprehensive analysis
of synchronous generators including:

1. Problem Solution Tab:
   - Solve parallel generator problems
   - Calculate field currents and power distribution

2. Dynamic Simulation Tab:
   - Real-time ODE solvers (RK45, Euler)
   - Swing equation simulation
   - Transient stability analysis

3. Thermal Analysis Tab:
   - Multi-node thermal network
   - Temperature prediction
   - Power derating calculation

4. Loss Analysis Tab:
   - Copper, iron, and mechanical losses
   - Efficiency calculation
   - Loss distribution visualization

5. Economic Analysis Tab:
   - Operating cost calculation
   - Payback period analysis
   - NPV calculation

6. Control Systems Tab:
   - AVR and governor controls
   - Protection systems

For detailed help, refer to the user manual.
        """
        messagebox.showinfo("Documentation", doc_text)


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = AdvancedGeneratorLabGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
