# Photon Transport: AI-Accelerated Development Timeline

**Status**: Revised for AI-assisted code generation
**Original Timeline**: 5-6 weeks | **Revised Timeline**: 3-5 working days intensive

---

## Revised 5-Phase Timeline (Claude Code)

### Phase 1: Foundation (Day 0.5)
**Objective**: Structure + data definitions ready to code

```
Task                              Time      Status
─────────────────────────────────────────────────
1.1a Directory structure          15 min    [Auto-generate]
1.1b Memory files                 15 min    [Auto-generate]
1.2  Data structure def           30 min    [Review & confirm definitions]
1.3  GitHub setup                 15 min    [Manual or auto]
─────────────────────────────────────────────────
Total Phase 1                      ~1.5 hrs
```

**What Claude does:**
- Creates all directory structure + `__init__.py` files
- Generates memory file templates
- Auto-generates data structure type hints + docstrings

**What you do:**
- ✅ Confirm data struct layouts are correct
- ✅ Review/adjust directory organization
- ✅ Create GitHub issue (or Claude creates + you review)

---

### Phase 2: Cross-Sections (Days 0.5-1.5)
**Objective**: All cross-sections implemented + validated vs NIST

```
Interaction               Code Gen  Validation  Tests    Total
─────────────────────────────────────────────────────────────
Klein-Nishina            1-2 hr    1-2 hr      30 min   3-4 hrs
Photoelectric            1-2 hr    1-2 hr      30 min   3-4 hrs
Pair Production          1-2 hr    1-2 hr      30 min   3-4 hrs
Total σ(E) composition   30 min    30 min      15 min   1 hr
─────────────────────────────────────────────────────────────
Total Phase 2                               ~12-15 hrs (1 day intensive)
```

**What Claude does:**
- Writes Klein-Nishina formula + numerical integration
- Loads NIST XCOM data (CSV or web fetch)
- Generates comparison plots (theoretical vs NIST)
- Writes unit tests + runs them
- Fixes any numerical accuracy issues
- Documents formulas in `photon_physics_reference.md`

**What you do:**
- ✅ Approve physics formulas (confirm Evans/IAEA references are used)
- ✅ Review NIST validation plots (should overlap within 1-2%)
- ✅ Confirm thresholds & energy ranges

**Output**: 4 validated cross-section functions + 12+ passing tests

---

### Phase 3: Interaction Physics (Days 1.5-2.5)
**Objective**: Scattering kernels + kinematics working

```
Interaction               Sampling  Validation  Tests    Total
─────────────────────────────────────────────────────────────
Compton kernel            2 hrs     2 hrs       30 min   4.5 hrs
Pair production KE        1-2 hrs   1-2 hrs     30 min   3-4 hrs
Photoelectric effect      1 hr      1 hr        30 min   2.5 hrs
─────────────────────────────────────────────────────────────
Total Phase 3                               ~10-11 hrs (1 day)
```

**What Claude does:**
- Implements Klein-Nishina acceptance-rejection sampling
- Generates energy/angle conservation tests
- Creates distribution visualizations
- Writes kinematics validation code
- Runs all tests + fixes issues
- Generates example histograms

**What you do:**
- ✅ Review energy conservation tests (should be exact to floating-point)
- ✅ Confirm angle distributions look physical (plots provided)
- ✅ Approve handling of edge cases (threshold energies, etc.)

**Output**: 3 working interaction kernels + 10+ passing tests + validation plots

---

### Phase 4: Integration (Days 2.5-4, ~1.5 days total)
**Objective**: Full system integration + 3 working examples

```
Component                 Code      Testing     Total
────────────────────────────────────────────────
Transport loop           1-2 hrs    1-2 hrs     2-4 hrs
Tally compatibility      1 hr       1-2 hrs     2-3 hrs
Geometry/mesh            30 min     1-2 hrs     2-3 hrs
Bank/census system       30 min     1 hr        1.5 hrs
Example 1 (absorption)   1 hr       30 min      1.5 hrs
Example 2 (Compton)      1 hr       30 min      1.5 hrs
Example 3 (pair prod)    1 hr       30 min      1.5 hrs
Regression test suite    2 hrs      2 hrs       4 hrs
────────────────────────────────────────────────
Total Phase 4                         ~18-20 hrs (1.5 days)
```

**What Claude does:**
- Modifies main transport loop to branch on particle type (photon vs neutron)
- Verifies tally system works with photon data
- Tests photon interactions in various geometries
- Creates 3 complete, runnable example scripts with expected outputs
- Generates comparison plots
- Writes 5+ regression tests with reference solutions
- Runs full test suite; fixes any failures

**What you do:**
- ✅ Review transport loop branching logic (ensure neutron tests still pass)
- ✅ Run example problems, verify outputs make physical sense
- ✅ Compare example results to hand-calculated expectations (Claude provides these)
- ✅ Approve integration approach (e.g., shared vs separate banks)

**Output**: Fully integrated photon transport + 3 working examples + 20+ tests passing

---

### Phase 5: Documentation (Days 4-5)
**Objective**: Sphinx docs complete + 95%+ test coverage

```
Component                         Time
────────────────────────────────────────
Sphinx chapters (4)               3-4 hrs
API auto-generation              1 hr
Example walkthroughs             2 hrs
Physics reference (formatted)    1-2 hrs
Coverage report + gaps           1 hr
Final test run + validation      2 hrs
────────────────────────────────────────
Total Phase 5                     ~10-12 hrs (0.5-1 day)
```

**What Claude does:**
- Generates 4 Sphinx RST chapters (overview, physics, usage, validation)
- Auto-generates API docs from docstrings
- Creates example walkthroughs with plots/output
- Formats physics reference with LaTeX formulas
- Runs coverage report; generates any missing tests
- Builds Sphinx docs locally + verifies no errors

**What you do:**
- ✅ Review Sphinx chapters for accuracy & clarity
- ✅ Verify coverage report (should be >95%)
- ✅ Build docs locally + confirm rendering correct
- ✅ Final sign-off

**Output**: Full Sphinx documentation + 95%+ code coverage

---

## Side-by-Side Timeline Comparison

### Original (Manual) Timeline
```
Phase 1: Foundation    ████████  Week 1-2
Phase 2: Physics       ████████  Week 2-3
Phase 3: Interactions  ████████  Week 3-4
Phase 4: Integration   ████████  Week 4-5
Phase 5: Docs          ████████  Week 5-6
                       ═════════════════════
Total:                 5-6 WEEKS
```

### Revised (AI-Assisted) Timeline
```
Phase 1: Foundation    ███  0.5 days
Phase 2: Physics       ███████  1 day
Phase 3: Interactions  ███████  1 day
Phase 4: Integration   █████████████  1.5 days
Phase 5: Docs          █████████  0.5-1 days
                       ════════════════════
Total:                 3-5 WORKING DAYS
```

---

## Compression Strategy: Key Optimizations

### 1. **Parallel Generation** (Days 0-1)
- Claude generates all 5 phases of directory structure in Phase 1
- All memory files created upfront (skeleton content, you fill in as you go)
- All docstring templates created immediately

### 2. **Batch Formula Implementation** (Day 0.5)
- Instead of serial Klein-Nishina → test → Photoelectric → test
- Claude generates all 3 cross-section formulas simultaneously
- Runs all validation tests in parallel
- You review results once at end of phase

### 3. **Rapid Iteration** (Days 1-2)
- Claude runs tests after each function → detects bugs immediately
- Generates plots/comparisons → you approve or request changes
- Fixes numerical issues in real-time (no manual rebuild cycle)

### 4. **Example + Testing Pipeline** (Days 2-3)
- 3 examples written in parallel
- Regression tests auto-generated from examples
- All tests run automatically → failures caught instantly

### 5. **Auto-Generated Documentation** (Day 4)
- Extract docstrings → auto-generate API docs
- Create Sphinx chapters from memory files
- Generate plots/tables from validation data
- You review for accuracy, not generation

---

## Decision: What You Approve vs What Claude Does

| Aspect | Claude Handles | You Approve |
|--------|---|---|
| **Code writing** | ✅ All functions, loops, array operations | - |
| **Testing** | ✅ Write tests, run pytest, fix bugs | - |
| **Examples** | ✅ Create working simulations | ✅ Verify outputs |
| **Documentation** | ✅ Write Sphinx, format, build | ✅ Review accuracy |
| **Physics formulas** | ✅ Implement from references | ✅ Confirm references (Evans, NIST) |
| **Architecture** | ✅ Follow existing patterns | ✅ Approve design (e.g., secondary electrons) |
| **Integration** | ✅ Connect to transport loop | ✅ Verify neutron tests pass |
| **Validation** | ✅ Compare to NIST, generate plots | ✅ Confirm accuracy within tolerance |

---

## Key Assumptions for This Timeline

1. **NIST data available**: XCOM can be fetched or provided (otherwise +1-2 hrs)
2. **Existing MCDC working**: Your local setup runs neutron transport
3. **Clear physics decisions upfront**: What to include (Compton, photoelectric, pair prod, Rayleigh?)
4. **No major architecture changes needed**: Uses existing geometry/tally/bank systems
5. **Reference materials available**: Evans, ICRU, IAEA references on hand or web-accessible
6. **Claude has write access**: Can create files, modify code immediately

---

## What Gets Done Each Day

### Day 0 (Prep Phase - 2 hrs)
```
├─ Phase 1: Foundation created
├─ All memory files generated
├─ Data structures defined
├─ GitHub issue created
└─ Ready to code
```

### Day 1 (Physics Phase - 8-10 hrs concentrated)
```
├─ All 4 cross-sections implemented
├─ NIST validation plots generated
├─ 12+ unit tests passing
├─ Formula frozen (ready for interactions)
└─ photon_physics_reference.md populated
```

### Day 2 (Interactions Phase - 8-10 hrs concentrated)
```
├─ Klein-Nishina kernel implemented
├─ Pair production kinematics working
├─ Photoelectric absorption implemented
├─ Energy/momentum conservation verified
├─ 10+ validation tests passing
└─ Distribution plots generated
```

### Day 3 (Integration Phase - 8-10 hrs concentrated)
```
├─ Transport loop modified (photon branching)
├─ All existing neutron tests still pass ✅
├─ Tally system verified with photons
├─ Geometry/mesh integration confirmed
├─ 3 example problems created + working
└─ 20+ regression tests passing
```

### Day 4 (Documentation Phase - 6-8 hrs concentrated)
```
├─ Sphinx docs generated (4 chapters)
├─ API docs auto-generated from code
├─ Example walkthroughs written
├─ Example plots/outputs included
├─ Coverage report >95%
└─ Docs build locally without errors
```

---

## Potential Blockers & How to Handle

| Blocker | Timeline Impact | Mitigation |
|---------|---|---|
| **NIST data not available** | +1-2 hrs | Claude fetches + caches, or you provide CSV |
| **Physics formula ambiguous** | +2-4 hrs | You confirm reference (Evans pg. X, etc.) |
| **Integration conflicts** | +2-4 hrs | Claude tests against neutron; you review |
| **Numba incompatibility** | +1-2 hrs | Claude rewrites to Numba-compatible code |
| **Test failures** | +1-3 hrs | Claude debugs + generates fixes |

---

## How to Run This Timeline

### Start of Each Phase
```
You: "Phase X: [description]. Here's the approach: [brief notes]"
Claude: Creates all code, runs tests, generates plots, documents
You: Reviews output, approves or requests changes
```

### Checkpoints
1. **After Phase 1**: Confirm data structures correct
2. **After Phase 2**: Review NIST validation plots
3. **After Phase 3**: Check energy conservation plots
4. **After Phase 4**: Run example simulations, verify outputs
5. **After Phase 5**: Review Sphinx docs, approve final structure

### Rollback if Needed
If a decision is wrong (e.g., secondary electrons needed sooner):
- Claude regenerates affected code
- Tests rerun automatically
- Takes 30 min - 1 hr, not 1 week

---

## Sample Day 1 Workflow

```
09:00 - You: "Ready for Phase 2. Implement Klein-Nishina,
        Photoelectric, Pair production cross-sections. Use NIST XCOM."

09:15 - Claude: Generates 3 functions + NIST loader + unit tests
        → All pass ✅

09:45 - Claude: Generates comparison plots (theory vs NIST)
        → All within 1% ✅

10:00 - You: "Looks good. Proceed with pair production threshold check."

10:15 - Claude: Adds threshold validation + test
        → Passes ✅

10:30 - You: "Move to Phase 3?"

10:30 - Claude: Starts kinematic implementations...
```

---

## What This Means for Your Workflow

### You Become a **Reviewer & Validator**
- Not writing code, but validating logic
- Checking physics accuracy against references
- Approving architectural decisions
- Reviewing output (plots, examples, tests)

### Claude Becomes **Developer & Tester**
- Writes all code + applies fixes automatically
- Runs all tests + generates reports
- Creates examples + documentation
- Generates validation plots for your review

### Bottleneck Shifts to **Physics Review**
- Not "does this code work?" (tests verify)
- But "is this physics correct?" (you confirm against references)
- And "does this match our design?" (you approve architecture)

---

## Questions for Revised Timeline

Before starting Day 0, confirm:

1. **Physics scope**: Include Rayleigh scattering? (adds ~2-3 hrs)
2. **Secondary particles**: Track electrons/positrons? (defers to Phase 2 if not)
3. **Data source**: Use web NIST XCOM or provide CSVs?
4. **Examples scope**: 3 examples enough, or want 5+?
5. **Documentation depth**: 4 chapters adequate, or expand?

**Answers adjust timeline by ±2 hrs max.**

---

**Revised Plan Status**: Ready to execute
**Estimated Total Time**: 3-5 working days of focused development
**Actual Calendar Time**: 1-2 weeks (depending on review turnaround)

