# Photon Transport Implementation Prompts

This directory contains 5 formalized prompt files for Claude Code—one for each development phase. Each prompt is self-contained and ready to copy-paste.

## Quick Navigation

| Phase | File | Duration | Goal |
|-------|------|----------|------|
| **1** | `PHASE_1_Foundation.md` | ~0.5 days | Create skeleton files, docstrings, structure |
| **2** | `PHASE_2_CrossSections.md` | ~1 day | Implement cross-section formulas, NIST validation |
| **3** | `PHASE_3_Distributions.md` | ~1 day | Implement sampling algorithms, kinematics |
| **4** | `PHASE_4_Integration.md` | ~1.5 days | Full interface, regression tests, MCDC integration |
| **5** | `PHASE_5_Documentation.md` | ~0.5-1 day | Sphinx docs, examples, code coverage |

## How to Use

1. **Before each phase:** Read the corresponding `.md` file
2. **Copy the entire file** into your Claude Code prompt
3. **Claude will:**
   - Read the documentation references (FILE_STRUCTURE_GUIDE.md, etc.)
   - Generate the specified code files
   - Run validation tests
   - Stop when phase is complete
4. **Between phases:** Clear the chat to conserve tokens (existing files persist in photon-transport-code/)

## Key Principles

- ✅ Each prompt references only the docs needed for that phase
- ✅ Deliverables are specific and directly tied to FILE_STRUCTURE_GUIDE.md
- ✅ Validation criteria are taken directly from VALIDATION_STRATEGY.md
- ✅ Prompts minimize reading/context to conserve tokens (~22K per phase)
- ✅ Each phase has explicit STOP instruction—no phase creep

## Total Token Budget

- Phase 1: ~30-35K tokens (skeleton creation)
- Phase 2: ~30-35K tokens (formula implementation)
- Phase 3: ~30-35K tokens (sampling algorithms)
- Phase 4: ~25-30K tokens (integration)
- Phase 5: ~15-20K tokens (documentation)

**Total: ~130-155K tokens** for full project completion

## File Structure

```
photon-transport-directions/
├── README.md                    (this file)
├── PHASE_1_Foundation.md        (skeleton files)
├── PHASE_2_CrossSections.md     (formula implementation)
├── PHASE_3_Distributions.md     (sampling algorithms)
├── PHASE_4_Integration.md       (full interface + integration)
└── PHASE_5_Documentation.md     (docs, examples, coverage)
```

## After Each Phase

Following each successful phase completion:

1. **Verify the validation checks passed** (shown at end of Claude output)
2. **Check that deliverable files exist** in `photon-transport-code/`
3. **Before next phase:** Clear the chat to free tokens
4. **In new chat:** Provide the next phase prompt from this directory

## Documentation References

All prompts reference these core documentation files:
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` — Files to create per phase
- `photon-transport-docs/VALIDATION_STRATEGY.md` — How to validate each phase
- `photon-transport-docs/THREE_CRITICAL_FILES_TIMELINE.md` — Critical file progression
- `photon-transport-docs/MCDC_FILE_ARCHITECTURE.md` — MCDC integration patterns
- `.claude/projects/c--Projects-MCDC/memory/photon_physics_reference.md` — Physics formulas

These files are persistent and complete—no need to recreate them between phases.

## Token Conservation Tips

- Use `/clear` between major phases to remove chat history
- In new chat, start with "CONTEXT: Phase X complete" prompt
- Each prompt references only essential docs (not the full 11-document suite)
- Batch related work (implementation + unit tests) in same phase

## Questions?

- Check the referenced documentation files in each prompt
- Refer to DOCUMENTATION_GUIDE.md for general project questions
- All validation procedures are in VALIDATION_STRATEGY.md
