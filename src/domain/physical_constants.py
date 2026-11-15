import numpy as np

# Fundamental Physical Constants (CODATA 2018, exact values where specified)
BOLTZMANN = 1.380649e-23  # J/K (exact)
ELECTRON_CHARGE = 1.602176634e-19  # C (exact)
AVOGADRO = 6.02214076e23  # mol^-1 (exact)
GAS_CONSTANT = AVOGADRO * BOLTZMANN  # J/(mol*K) (exact)

# Rounded legacy API value; keep separate from the CODATA-derived GAS_CONSTANT.
LEGACY_GAS_CONSTANT = 8.314462618  # J/(mol*K)

# Retained material defaults from the legacy constants module (Silicon).
SILICON_DEFAULT_DEBYE_T = 645.0  # K
SILICON_DEFAULT_SOUND_VELOCITY = 5880.0  # m/s
PLANCK = 6.62607015e-34  # J*s (exact)
ELECTRON_MASS = 9.1093837015e-31  # kg
KB_OVER_E_UV_K = (BOLTZMANN / ELECTRON_CHARGE) * 1e6  # µV/K
FARADAY = AVOGADRO * ELECTRON_CHARGE  # C/mol (exact)

# Model constants and established application defaults
#
# Lorenz number (W*Ohm/K^2).
#
# Author decision (2026-11-11, audit issue SE-015): the application-wide value
# is the rounded standard 2.44e-8, so that the main table and the Multi-Sample
# workflow report identical kappa_e and ZT. The exact Sommerfeld value
# (pi^2/3)(k_B/e)^2 = 2.443004509e-8 differs by 0.12 % and is retained below
# for reference and documentation only.
DEFAULT_LORENZ = 2.44e-8  # W*Ohm/K^2 (application-wide)

# Exact Sommerfeld value of the electronic Lorenz number, for reference.
SOMMERFELD_LORENZ_EXACT = (
    (np.pi**2 / 3) * (BOLTZMANN**2) / (ELECTRON_CHARGE**2)
)  # 2.443004509e-08 W*Ohm/K^2

# Historical alias: the Multi-Sample workflow already used the rounded value.
# Kept for backward compatibility; it now equals DEFAULT_LORENZ.
LEGACY_DEFAULT_LORENZ = DEFAULT_LORENZ  # W*Ohm/K^2
ATOMIC_WEIGHTS = {
    "Bi": 208.98040,  # Bismuth
    "C": 12.011,  # Carbon (representative value for natural abundance)
    "Ge": 72.630,  # Germanium
    "H": 1.008,  # Hydrogen (representative value for natural abundance)
    "O": 15.999,  # Oxygen (representative value for natural abundance)
    "Pb": 207.2,  # Lead (representative value for natural abundance)
    "Se": 78.971,  # Selenium
    "Si": 28.085,  # Silicon (representative value for natural abundance)
    "Sn": 118.710,  # Tin
    "Sb": 121.760,  # Antimony
    "Te": 127.60,  # Tellurium
    "Al": 26.9815384,  # Aluminium
}


# Exact legacy masses retained for compatibility with the formula tool.
LEGACY_ATOMIC_WEIGHTS = {'H': 1.008,
 'He': 4.0026,
 'Li': 6.94,
 'Be': 9.0122,
 'B': 10.81,
 'C': 12.011,
 'N': 14.007,
 'O': 15.999,
 'F': 18.998,
 'Ne': 20.18,
 'Na': 22.99,
 'Mg': 24.305,
 'Al': 26.982,
 'Si': 28.085,
 'P': 30.974,
 'S': 32.06,
 'Cl': 35.45,
 'Ar': 39.948,
 'K': 39.098,
 'Ca': 40.078,
 'Sc': 44.956,
 'Ti': 47.867,
 'V': 50.942,
 'Cr': 51.996,
 'Mn': 54.938,
 'Fe': 55.845,
 'Co': 58.933,
 'Ni': 58.693,
 'Cu': 63.546,
 'Zn': 65.38,
 'Ga': 69.723,
 'Ge': 72.63,
 'As': 74.922,
 'Se': 78.971,
 'Br': 79.904,
 'Kr': 83.798,
 'Rb': 85.468,
 'Sr': 87.62,
 'Y': 88.906,
 'Zr': 91.224,
 'Nb': 92.906,
 'Mo': 95.96,
 'Tc': 98.0,
 'Ru': 101.07,
 'Rh': 102.91,
 'Pd': 106.42,
 'Ag': 107.87,
 'Cd': 112.41,
 'In': 114.82,
 'Sn': 118.71,
 'Sb': 121.76,
 'Te': 127.6,
 'I': 126.9,
 'Xe': 131.29,
 'Cs': 132.91,
 'Ba': 137.33,
 'La': 138.91,
 'Ce': 140.12,
 'Pr': 140.91,
 'Nd': 144.24,
 'Pm': 145.0,
 'Sm': 150.36,
 'Eu': 151.96,
 'Gd': 157.25,
 'Tb': 158.93,
 'Dy': 162.5,
 'Ho': 164.93,
 'Er': 167.26,
 'Tm': 168.93,
 'Yb': 173.05,
 'Lu': 174.97,
 'Hf': 178.49,
 'Ta': 180.95,
 'W': 183.84,
 'Re': 186.21,
 'Os': 190.23,
 'Ir': 192.22,
 'Pt': 195.08,
 'Au': 196.97,
 'Hg': 200.59,
 'Tl': 204.38,
 'Pb': 207.2,
 'Bi': 208.98,
 'Po': 209.0,
 'At': 210.0,
 'Rn': 222.0,
 'Fr': 223.0,
 'Ra': 226.0,
 'Ac': 227.0,
 'Th': 232.04,
 'Pa': 231.04,
 'U': 238.03,
 'Np': 237.0,
 'Pu': 244.0,
 'Am': 243.0,
 'Cm': 247.0,
 'Bk': 247.0,
 'Cf': 251.0,
 'Es': 252.0,
 'Fm': 257.0,
 'Md': 258.0,
 'No': 259.0,
 'Lr': 262.0,
 'Rf': 267.0,
 'Db': 268.0,
 'Sg': 271.0,
 'Bh': 272.0,
 'Hs': 277.0,
 'Mt': 276.0,
 'Ds': 281.0,
 'Rg': 280.0,
 'Cn': 285.0,
 'Nh': 286.0,
 'Fl': 289.0,
 'Mc': 290.0,
 'Lv': 293.0,
 'Ts': 294.0,
 'Og': 294.0}
