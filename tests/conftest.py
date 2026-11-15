import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# The package root is src/ (flat layout): "seebeck_prime" resolves to the
# shim in src/seebeck_prime/, which exposes src/<layer> as subpackages.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
