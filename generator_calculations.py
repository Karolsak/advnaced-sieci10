"""
Synchronous Generator Calculation Modules
Contains all mathematical models without GUI dependencies
"""

import numpy as np
from scipy.integrate import solve_ivp
import math


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

        # Calculate EMF for generator B
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
        """
        # First get part (a) results
        results_a = self.solve_part_a()
        IfB = results_a['IfB']
        EfB = results_a['EfB']
        QB = results_a['QB'] * 1e3

        # New load conditions
        P_additional = 130e3  # W
        PL_total_new = 720e3 + P_additional  # Total 850 kW
        QL_total_new = 720e3 * np.tan(np.arccos(0.8))

        # Assume power sharing proportional to ratings
        total_rating = self.PnA + self.PnB
        PA_new = PL_total_new * (self.PnA / total_rating)
        PB_new = PL_total_new * (self.PnB / total_rating)

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
    """

    def __init__(self, params):
        self.params = params
        self.H = params.get('H', 3.5)
        self.D = params.get('D', 2.0)
        self.Xd = params.get('Xd', 1.5)
        self.Xq = params.get('Xq', 1.5)
        self.Xd_prime = params.get('Xd_prime', 0.3)
        self.Td0_prime = params.get('Td0_prime', 5.0)
        self.omega_s = 2 * np.pi * params.get('freq', 60)

    def swing_equation(self, t, y, Pm, Ef, V):
        """Swing equation and voltage dynamics"""
        delta, omega, Eq_prime = y

        Pe = (Eq_prime * V / self.Xd_prime) * np.sin(delta) + \
             (V**2 / (2 * self.Xd_prime * self.Xq)) * (self.Xd_prime - self.Xq) * np.sin(2 * delta)

        ddelta_dt = omega - self.omega_s
        domega_dt = (self.omega_s / (2 * self.H)) * (Pm - Pe - self.D * (omega - self.omega_s))
        dEq_prime_dt = (1 / self.Td0_prime) * (Ef - Eq_prime - (self.Xd - self.Xd_prime) * \
                       (V / self.Xd_prime) * np.cos(delta))

        return [ddelta_dt, domega_dt, dEq_prime_dt]

    def simulate(self, t_span, y0, Pm, Ef, V, method='RK45'):
        """Simulate generator dynamics"""
        if method == 'RK45':
            sol = solve_ivp(lambda t, y: self.swing_equation(t, y, Pm, Ef, V),
                          t_span, y0, method='RK45', dense_output=True,
                          max_step=0.001)
        elif method == 'Euler':
            t = np.arange(t_span[0], t_span[1], 0.001)
            y = np.zeros((len(t), len(y0)))
            y[0] = y0
            for i in range(1, len(t)):
                dt = t[i] - t[i-1]
                dydt = self.swing_equation(t[i-1], y[i-1], Pm, Ef, V)
                y[i] = y[i-1] + np.array(dydt) * dt

            class EulerSolution:
                def __init__(self, t, y):
                    self.t = t
                    self.y = y.T
                    self.success = True

            sol = EulerSolution(t, y)

        return sol


class ThermalModel:
    """Thermal model for generator"""

    def __init__(self, params):
        self.C_winding = params.get('C_winding', 5000)
        self.C_core = params.get('C_core', 8000)
        self.C_frame = params.get('C_frame', 3000)
        self.R_winding_core = params.get('R_winding_core', 0.05)
        self.R_core_frame = params.get('R_core_frame', 0.03)
        self.R_frame_ambient = params.get('R_frame_ambient', 0.02)
        self.T_ambient = params.get('T_ambient', 25)
        self.T_max_winding = params.get('T_max_winding', 130)
        self.T_max_core = params.get('T_max_core', 110)

    def thermal_network(self, t, T, P_losses):
        """Thermal network equations"""
        T_winding, T_core, T_frame = T
        P_copper, P_iron, P_friction = P_losses

        Q_winding_core = (T_winding - T_core) / self.R_winding_core
        Q_core_frame = (T_core - T_frame) / self.R_core_frame
        Q_frame_ambient = (T_frame - self.T_ambient) / self.R_frame_ambient

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
        """Calculate power derating"""
        if T_winding <= self.T_max_winding:
            derating_factor = 1.0
        else:
            derating_factor = max(0, 1.0 - 0.02 * (T_winding - self.T_max_winding))
        return derating_factor


class LossAnalysis:
    """Loss calculation"""

    def __init__(self, params):
        self.params = params
        self.Ra = params.get('Ra', 0.01)
        self.Rf = params.get('Rf', 50)

    def calculate_copper_losses(self, Ia, If):
        """Calculate copper losses"""
        P_copper_stator = 3 * Ia**2 * self.Ra
        P_copper_rotor = If**2 * self.Rf
        return P_copper_stator, P_copper_rotor

    def calculate_iron_losses(self, V, f, B_max):
        """Calculate iron losses"""
        k_h = self.params.get('k_h', 0.001)
        k_e = self.params.get('k_e', 0.0001)
        P_hysteresis = k_h * f * B_max**2
        P_eddy = k_e * f**2 * B_max**2
        return P_hysteresis, P_eddy

    def calculate_mechanical_losses(self, speed_rpm):
        """Calculate mechanical losses"""
        P_friction = self.params.get('k_friction', 500) * (speed_rpm / 1800)
        P_windage = self.params.get('k_windage', 300) * (speed_rpm / 1800)**2
        return P_friction, P_windage

    def calculate_stray_losses(self, P_output):
        """Calculate stray losses"""
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
        """Get detailed loss breakdown"""
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
    """Economic analysis"""

    def __init__(self):
        self.electricity_price = 0.12
        self.fuel_cost = 0.05
        self.maintenance_cost = 0.02
        self.capital_cost_per_kw = 800
        self.lifetime_years = 20
        self.interest_rate = 0.05

    def calculate_operating_cost(self, P_output_kW, hours):
        """Calculate operating cost"""
        fuel_cost = (P_output_kW / 0.4) * self.fuel_cost * hours
        maint_cost = P_output_kW * self.maintenance_cost * hours
        total_cost = fuel_cost + maint_cost
        return {
            'fuel_cost': fuel_cost,
            'maintenance_cost': maint_cost,
            'total_cost': total_cost
        }

    def calculate_revenue(self, P_output_kW, hours):
        """Calculate revenue"""
        return P_output_kW * self.electricity_price * hours

    def calculate_payback_period(self, capacity_kW, annual_hours):
        """Calculate payback period"""
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
        """Calculate NPV"""
        capital_cost = capacity_kW * self.capital_cost_per_kw
        annual_revenue = self.calculate_revenue(capacity_kW, annual_hours)
        annual_cost = self.calculate_operating_cost(capacity_kW, annual_hours)['total_cost']
        annual_net = annual_revenue - annual_cost

        npv = -capital_cost
        for year in range(1, self.lifetime_years + 1):
            npv += annual_net / ((1 + self.interest_rate) ** year)

        return npv
