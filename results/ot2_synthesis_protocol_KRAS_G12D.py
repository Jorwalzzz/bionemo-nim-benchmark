# =============================================================================
# UNVALIDATED PROTOCOL WARNING
# This script was auto-generated for illustrative purposes only.
# It has NOT been reviewed or validated by a qualified chemist.
# DO NOT use in a wet laboratory without independent expert review,
# risk assessment, and compliance with all applicable safety regulations.
# Expected yields and volumes are illustrative and may be incorrect.
# =============================================================================
"""
Opentrons OT-2 Automated Dilution Protocol
Target Candidate: KRAS G12D Inhibitor Assay Series
Generated for: BioNeMo NIM Benchmark Suite
Author: Aarav Jorwal (@Jorwalzzz)
"""

from opentrons import protocol_api

metadata = {
    'protocolName': 'KRAS G12D inhibitor serial dilution (illustrative)',
    'author': 'Aarav Jorwal (@Jorwalzzz)',
    'description': '2-fold serial dilution assay protocol for KRAS G12D inhibitor candidates',
    'apiLevel': '2.15'
}

def run(protocol: protocol_api.ProtocolContext):
    # 1. Deck labware configuration
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)
    res = protocol.load_labware('nest_12_reservoir_15ml', 3)
    tips = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tips])
    p300.flow_rate.aspirate = 25   # µL/s, throttled for DMSO viscosity
    p300.flow_rate.dispense = 25

    row = plate.rows()[0]  # Row A: A1 to A12
    # 2. Dispense diluent (50 µL) into columns 2-12
    p300.transfer(50, res['A1'], row[1:], new_tip='once')
    # 3. 2-fold serial dilution down Row A with mixing
    p300.transfer(50, row[:11], row[1:12], mix_after=(3, 40), new_tip='always')
    protocol.comment("OT-2 KRAS G12D serial dilution protocol complete.")
