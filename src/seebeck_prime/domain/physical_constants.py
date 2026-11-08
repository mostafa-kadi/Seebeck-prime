import numpy as np

# Fundamental Physical Constants (CODATA 2018, exact values where specified)
BOLTZMANN = 1.380649e-23  # J/K (exact)
ELECTRON_CHARGE = 1.602176634e-19  # C (exact)
AVOGADRO = 6.02214076e23  # mol^-1 (exact)
GAS_CONSTANT = AVOGADRO * BOLTZMANN  # J/(mol*K) (exact)
PLANCK = 6.62607015e-34  # J*s (exact)
ELECTRON_MASS = 9.1093837015e-31  # kg
FARADAY = AVOGADRO * ELECTRON_CHARGE  # C/mol (exact)

# Project-specific constants (placeholders, actual values to be confirmed from codebase)
DEFAULT_LORENZ = (
    (np.pi**2 / 3) * (BOLTZMANN**2) / (ELECTRON_CHARGE**2)
)  # Sommerfeld value for Lorenz number
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
