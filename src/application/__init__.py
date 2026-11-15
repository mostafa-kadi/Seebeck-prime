"""Application layer: use cases, ports, table contracts, and services.

This layer orchestrates the domain scientific core. It must not depend on
Presentation, GUI, or concrete Infrastructure implementations, and it performs
no direct file I/O (persistence goes through the injected TabularDataStore
port).
"""
