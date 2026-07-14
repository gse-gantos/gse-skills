# Control System Relationships Protocol

`views/control_system_relationships.md` documents the complete control
architecture for an instrumented set: how instrument signals flow through the
control system, which controllers receive which inputs, which actuators receive
commands from which controllers, and where power comes from.

It is an **analytical view built by Claude from the indexed database** — it is
never derived from a single sheet, because the control architecture is
distributed across multiple discipline sheets (L-005) and is only visible by
correlating them. Like every file under `views/`, it reads from `machine/*.json`
and the already-rendered `sheets/`; it never re-reads the raw PDF.

---

## When to build this view

Build it for **any set that includes any of the following:**

- Instrumented valves (actuated valves with position feedback or modulating control)
- Flow meters (FIT, FE, FT) with analog output signals
- Analytical instruments (DO probes, turbidity, pH, conductivity — AIT type)
- PLCs, RTUs, or DCS controllers receiving instrument inputs
- MCCs or VFDs receiving PLC outputs
- SCADA or HMI systems
- PID control loops of any kind

If any of these are present, this view is expected — flag its absence as a
coverage gap for the control/instrumentation question domain in
`coverage_status.json`.

---

## Required sections

### 1. Control Architecture Summary
One paragraph: what is controlled, what is measured, how the system responds.
Name the primary controllers and actuators.

### 2. Instrument → Controller Mapping

| Field | Description |
|---|---|
| Instrument tag | Full tag, verbatim (e.g., AIT-24.B611A) |
| Measurement type | DO, flow, position, pressure, etc. |
| Signal type | 4-20mA, discrete, digital, etc. |
| Destination controller | PLC tag, MCC tag, panel name |
| Terminal/channel | If shown on a schematic or panel schedule |
| Confidence | `high` / `medium` / `low` (per the provenance ceiling) |
| Source sheet(s) | Where the relationship was found |

### 3. Controller → Actuator Mapping

| Field | Description |
|---|---|
| Controller tag | PLC, MCC, panel |
| Output destination | Actuator tag (valve, VFD, etc.) |
| Command type | Discrete on/off, analog 4-20mA, etc. |
| Power source | MCC circuit, panel circuit, UPS |
| Confidence | `high` / `medium` / `low` |
| Source sheet(s) | Where the relationship was found |

### 4. Power Sources

| Device tag | Voltage/phase | Power source | Source sheet |
|---|---|---|---|
| (fill per set) | | | |

### 5. Confirmed vs. Inferred

- **Confirmed** — shown on a control diagram, P&ID, or connection schedule.
- **Inferred** — deduced from tags appearing together on a plan, proximity on a
  riser, or naming convention. Every inferred relationship is `confidence: low`
  and carries an open question until a second source confirms it.

Never present an inferred relationship as confirmed.

---

## How to build it

Work bottom-up, and pull every fact from the indexed database (tag_index,
sheet_index, the per-sheet `classification.json` and `page_NNNN.txt`, and
high-DPI crops via `crop_region.py`) — not from a fresh PDF read:

1. **P&IDs (I-series)** — process instruments and loop identifiers. Remember the
   balloon interiors do not render (L-002); use the sheet's schedule/loop-list
   block and key notes for the loop tags, not the balloons.
2. **Electrical plans (E-series)** — single-lines and electrical plans give panel
   assignments and power sources.
3. **Instrument detail sheets** — signal types, installation details, terminations.
4. **Conduit schedules** — FROM/TO designations confirm which instrument connects
   to which panel. Usually the most reliable single source for a signal path.
5. Assemble: instrument → conduit → panel → MCC/PLC → controller output → actuator.

When a conduit-schedule endpoint conflicts with a P&ID inference, **prefer the
conduit schedule** — it represents the actual wired connection.

---

## Needs-verification flag

When a relationship can't be confirmed from two independent sources, say so
explicitly and keep it `confidence: low`:

```
| AIT-24.B612A | 4-20mA | PLC-32 | needs verification — inferred from zone pattern; P&ID I-201 balloon unreadable |
```

The flag stays until a second source confirms the relationship.

---

## Validated example

**Control architecture:** DO closed-loop control (AIT → PLC-32 → EMV position
command) plus airflow modulation (FIT → BLOWER MCP → VFD speed command).

| Instrument | Signal | Destination | Confidence | Source |
|---|---|---|---|---|
| AIT-24.Bxxx (DO probe) | 4-20mA | PLC-32 | high | E-302 conduit schedule, I-107 Detail N100 |
| FIT-24.Bxxx (thermal mass) | 4-20mA | BLOWER MCP | high | E-302 A-series conduit, I-107 Detail M295 |
| ZIT-24.Bxxx (valve position) | 4-20mA | BLOWER MCP | low | naming convention; I-200–I-203 balloons unreadable |

| Controller | Output | Actuator | Command | Power | Source |
|---|---|---|---|---|---|
| PLC-32 | DO setpoint loop | EMV-24.Bxxx | 4-20mA modulating | MCC-24/25 480V 3-phase | E-202, E-302 |
| BLOWER MCP | Airflow modulation | VFD-441/442/443 | Speed reference | E-202 | E-202 |

Source sheets: I-200–I-203, E-200, E-201, E-202, E-302, I-105, I-107.

---

*Protocol merged into drawing-engine from drawing-library Beta 1, based on a
field-validated finding (L-005, 2026-06-19).*
