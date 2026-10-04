"""
Photon transport physics module.

Public API re-exported from interface.py. Mirrors the neutron physics
module structure at mcdc/transport/physics/neutron/.
"""

from photon_transport_code.transport.physics.photon.interface import (
    collision,
    macro_xs,
    particle_speed,
    photon_production_xs,
)
from photon_transport_code.transport.physics.photon import cross_sections
from photon_transport_code.transport.physics.photon import distributions
from photon_transport_code.transport.physics.photon import util
from photon_transport_code.transport.physics.photon.data_loader import (
    load_photon_element,
    load_photon_shell_resolved_pe,
    load_water_data,
)
