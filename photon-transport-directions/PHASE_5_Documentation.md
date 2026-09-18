# PHASE 5: Documentation - Sphinx Docs, Examples & Code Polish

## Quick Context
Phase 5 completes documentation with Sphinx RST files, creates 3 example problems demonstrating photon transport, generates code coverage reports, and performs final code review. All physics code is complete; Phase 5 is about documentation and demonstration.

## READ FIRST (Documentation)
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` (Phase 5 section — RST docs, examples)
- `photon-transport-docs/DOCUMENTATION_GUIDE.md` (Sphinx/RST format requirements)
- `photon-transport-docs/VALIDATION_STRATEGY.md` (Phase 5 Acceptance Criteria section)

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon-transport-code\
```

## REFERENCE PATTERNS
- `docs/source/user/neutron/` — RST documentation structure for neutron module
- `examples/` — Existing example problems (mesh slab, etc.)

## DELIVERABLES (6 RST Doc Files + 3 Examples)

### Sphinx Documentation (RST format)
1. `docs/source/user/photon/overview.rst` — Module overview, quickstart
2. `docs/source/user/photon/physics.rst` — Physics model (Compton, PE, pair prod)
3. `docs/source/user/photon/examples.rst` — Links to example problems
4. `docs/source/pythonapi/photon_transport.rst` — API reference for transport/physics/photon/
5. `docs/source/pythonapi/photon_material.rst` — API reference for mcdc_set/photon_material
6. `docs/source/pythonapi/photon_validation.rst` — Validation results, test coverage

### Example Problems (3 standalone scripts)
7. `examples/photon_transport_compton/problem.py` — Compton scattering-dominated scenario
8. `examples/photon_transport_pair_production/problem.py` — Pair production threshold testing
9. `examples/photon_transport_photoelectric/problem.py` — Photoelectric absorption scenario

Each example should:
- Demo one primary interaction type
- Show material definition and source setup
- Include tally configuration
- Run successfully with `python problem.py`
- Produce output file compatible with MCDC visualization

### Code Quality
10. Generate pytest coverage report
    ```bash
    pytest test/ --cov=transport/physics/photon --cov=mcdc_set/photon_material \
      --cov-report=html --cov-report=term
    ```

## REQUIREMENTS
✅ All RST files follow Sphinx format (cross-references, code blocks, etc.)
✅ All example problems run without errors
✅ All example problems produce valid MCDC output
✅ Code coverage ≥95% for all photon physics modules
✅ Sphinx documentation builds cleanly (0 warnings)
✅ All docstrings present and complete (no "pass" stubs remain)
✅ Black formatting compliant on all files (including examples)

## VALIDATION (from VALIDATION_STRATEGY.md Phase 5)
Run these commands:
```bash
# 1. Build Sphinx documentation
cd docs/source && sphinx-build -W . _build/html

# 2. Check code coverage
pytest test/ --cov=transport/physics/photon --cov=mcdc_set/photon_material --cov-report=term-missing
# Coverage must be ≥95%

# 3. Run example problems
python examples/photon_transport_compton/problem.py
python examples/photon_transport_pair_production/problem.py
python examples/photon_transport_photoelectric/problem.py

# 4. Black formatting on all files
black --check transport/ mcdc_set/ mcdc_get/ test/ examples/ docs/

# 5. Final import/integration check
python -c "from transport.physics.photon import interface; from mcdc_set.photon_material import PhotonMaterial; print('✓ All imports work')"
```

## SUCCESS CRITERIA
✅ All 6 RST documentation files created and Sphinx builds cleanly
✅ All 3 example problems run successfully
✅ Code coverage ≥95% for photon transport modules
✅ Sphinx build produces 0 warnings
✅ All docstrings complete and formatted correctly
✅ All Black formatting passes
✅ Full integration test passes (all imports, all tests)
✅ Project ready for MCDC integration or standalone use

## IMPORTANT
Phase 5 is the final phase. After Phase 5 completion, the photon transport module is feature-complete and ready for production use or integration into MCDC main branch.

All code is complete. All physics validated. All documentation finalized.
