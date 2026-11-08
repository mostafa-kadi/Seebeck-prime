COL_TEMP = 0
COL_EC = 1
COL_SEEBECK = 2
COL_PF = 3
COL_K_TOTAL = 4
COL_K_E = 5
COL_K_L = 6
COL_ZT = 7
BASE_COLUMN_COUNT = 8

# Column headers for base mode
COLUMN_HEADERS = [
    "Temperature",
    "Electrical Conductivity",
    "Seebeck Coeff.",
    "Power Factor",
    "Thermal Cond.",
    "Electronic TC",
    "Lattice TC",
    "ZT",
]

# Column headers with error bars (Note: T does not have an error column)
ERROR_COLUMN_HEADERS = [
    "Temperature",
    "Electrical Conductivity",
    "±σ",
    "Seebeck Coeff.",
    "±S",
    "Power Factor",
    "±PF",
    "Thermal Cond.",
    "±κ",
    "Electronic TC",
    "±κₑ",
    "Lattice TC",
    "±κₗ",
    "ZT",
    "±ZT",
]

INPUT_COLUMNS_BASE = [COL_TEMP, COL_EC, COL_SEEBECK, COL_K_TOTAL]
