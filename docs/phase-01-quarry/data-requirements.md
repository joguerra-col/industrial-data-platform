# Phase 01 — Quarry & Limestone Crushing: Data Requirements

> **Status:** draft for review.
> **Scope:** from the quarry bench to the crushed-limestone stockpile (and the waste dump for overburden).
> **Principle:** this document defines **raw (Bronze) data only**, exactly as each source system would deliver it. Metrics such as mine productivity, powder factor, availability or average t/h are **not generated**; they are calculated later in Silver/Gold from these fields.

---

## 1. Process context

```text
Bench (HG / MG / waste layer)
   │  drilling + blasting
   ▼
Loading (excavator / loader) ──► Haul truck
                                 (on-board payload sensor: approx. weight per trip)
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
         High-grade (HG)      Medium-grade (MG)        Waste
                 │                   │                   │
                 └──► Crusher hopper ──► Crusher      Waste dump
                                          │          (weight = on-board payload only)
                                          ▼
                              Belt conveyor
                              ├─ Belt scale      (measured tonnage)
                              └─ Online analyzer (measured chemistry)
                                          │
                                          ▼
                     Single blended limestone stockpile (HG + MG)
```

- The quarry is mined **in layers**. Each bench has a dominant material type, known in advance from the mine's geological model: high-grade (HG), medium-grade (MG) or waste.
- **There is no truck weighbridge.** Trip weight comes from two complementary sources:
  - **On-board payload sensor** on every truck (suspension pressure). Gives an approximate weight for every trip, limestone and waste alike. Typical accuracy is about ±5 %.
  - **Belt scale** on the conveyor after the crusher. Measures the actual tonnage that reaches the stockpile continuously, with much better accuracy (about ±0.5–1 %). It cannot tell which truck the material came from.
- **Waste never goes to the crusher**, so its weight comes **only from the on-board payload sensor**.
- **Quality** also comes from two sources: the **expected quality per bench** (geological model) and the **measured quality** from the **online radiometric cross-belt analyzer** on the same conveyor.
- **Tonnage and quality per trip are attributed in Silver** by linking each truck dump at the crusher to the belt-scale and analyzer readings it produced (see section 4).
- **HG and MG are crushed into a single blended stockpile.** Blending to the quality target requested by the raw-meal process is a Phase 02 concern.
- The laboratory **validates and calibrates the analyzer**. There is no per-trip sampling.

---

## 2. Master data (shared by all sources)

Stored in the simulator configuration and also published as reference files (`reference/`), so Silver can build dimensions.

### 2.1 Naming convention

**Structure:** `A-GL-TTT-NN`

| Segment | Length | Meaning | Example |
|---|---|---|---|
| `A` | 1 digit | Process area | `1` = extraction |
| `GL` | 2 digits | Technical group (G) and line/face (L) | `91` = transport, line 1 |
| `TTT` | 3 letters | Equipment type (project-specific abbreviation) | `TRK` = haul truck |
| `NN` | 2 digits | Sequence number | `01` |

Full example: `1-91-TRK-01` is haul truck 01 in the transport group (line 1) of the extraction area.

Area and group numbering follows the general logic of cement-plant asset coding. The dash-separated format and the type abbreviations are specific to this project: no equipment codes from any external guide are used.

**Process areas (whole project):**

| Area | Process | Project phase |
|---|---|---|
| 1 | Raw material extraction & transport | Phase 01 |
| 2 | Raw material preparation (crushing & storage) | Phase 01 |
| 3 | Raw meal preparation | Future |
| 4 | Clinker production | Future |
| 5 | Cement grinding | Future |
| 6 | Shipping | Future |

**Technical groups used in Phase 01:**

| A-GL | Description |
|---|---|
| 1-11 | Limestone extraction, face 1 (benches, drilling, blasting, loading) |
| 1-81 | Waste handling & dump (project-specific assignment) |
| 1-91 | Raw material transport: hauling |
| 2-11 | Limestone crushing, line 1 (hopper, crusher, conveyor, belt scale, online analyzer) |
| 2-91 | Crushed limestone transport & storage |

**Phase 01 assets:**

| Asset | Format | Example |
|---|---|---|
| Bench | `1-11-BNK-XX` | 1-11-BNK-01 |
| Drill rig | `1-11-DRL-XX` | 1-11-DRL-01 |
| Excavator | `1-11-EXC-XX` | 1-11-EXC-01 |
| Wheel loader | `1-11-LDR-XX` | 1-11-LDR-01 |
| Haul truck | `1-91-TRK-XX` | 1-91-TRK-01 |
| On-board payload sensor | `1-91-PLS-XX` | 1-91-PLS-01 (fitted on 1-91-TRK-01) |
| Crusher hopper | `2-11-HOP-XX` | 2-11-HOP-01 |
| Primary crusher | `2-11-CRS-XX` | 2-11-CRS-01 |
| Belt scale | `2-11-BWS-XX` | 2-11-BWS-01 |
| Online analyzer | `2-11-ANZ-XX` | 2-11-ANZ-01 |
| Limestone stockpile | `2-91-STK-XX` | 2-91-STK-01 |
| Waste dump | `1-81-DMP-XX` | 1-81-DMP-01 |

Geofences that are not tied to an asset use `ZN-TTT-NN` (e.g. `ZN-QUE-01` queue, `ZN-WSH-01` workshop, `ZN-PRK-01` parking).

### 2.2 Initial fleet and plant (configurable)

| Type | Qty | Nominal capacity | IDs |
|---|---|---|---|
| Drill rig | 1 | — | 1-11-DRL-01 |
| Excavator | 2 | — | 1-11-EXC-01 … 02 |
| Wheel loader | 1 | — | 1-11-LDR-01 |
| Haul truck | 5 | 55 t | 1-91-TRK-01 … 05 |
| Haul truck | 2 | 35 t | 1-91-TRK-06 … 07 |
| Crusher hopper | 1 | ~150 t live capacity | 2-11-HOP-01 |
| Primary crusher | 1 | ~1,000 t/h nominal | 2-11-CRS-01 |
| Belt scale | 1 | — | 2-11-BWS-01 |
| Online analyzer | 1 | — | 2-11-ANZ-01 |

Plant parameters used by the simulator and by Silver:

| Parameter | Default | Description |
|---|---|---|
| `hopper_live_capacity_t` | 150 | Usable hopper volume, in tonnes |
| `crusher_to_scale_delay_s` | 60 | Travel time from crusher discharge to the belt scale |
| `scale_to_analyzer_delay_s` | 20 | Travel time from the belt scale to the analyzer |

Fleet size and plant parameters may be adjusted after the first simulation runs if the tonnage balance does not make sense.

### 2.3 Benches (geological model)

| Field | Type | Unit | Description |
|---|---|---|---|
| `bench_id` | str | — | 1-11-BNK-XX |
| `elevation_m` | int | m a.s.l. | Bench elevation |
| `material_type` | enum | — | `HG`, `MG`, `WASTE` |
| `expected_cao_pct` | float \| null | % | Expected CaO from the geological model (null for waste) |
| `expected_mgo_pct` | float \| null | % | Expected MgO |
| `expected_sio2_pct` | float \| null | % | Expected SiO₂ |
| `rock_density_t_m3` | float | t/m³ | In-situ density |
| `available_tonnage_t` | float | t | Remaining in-situ tonnage at the start of the simulation |
| `initial_broken_stock_t` | float | t | Already-blasted rock available for loading at the start of the simulation |
| `status` | enum | — | `active`, `planned`, `exhausted` |

### 2.4 Shift calendar

| Item | Value |
|---|---|
| Operating days | Monday to Saturday (Sunday: no scheduled operation) |
| Shift A | 08:00–16:00 local time (America/Bogota) |
| Shift B | 16:00–24:00 local time |
| Night (00:00–08:00) | No scheduled operation |
| Shift handover | 10 min at the start and 10 min at the end of each shift |
| Meal break | 30 min per operator, **staggered** so the process never stops. Shift A: between 12:00 and 14:00. Shift B: between 19:00 and 21:00. |
| `shift_id` format | `YYYYMMDD-A` / `YYYYMMDD-B` |

Handovers and meal breaks are not generated as a dataset. They appear in the raw data as operator logout/login events, idle telemetry and lower crusher feed. Silver/Gold must recognize them.

---

## 3. Data sources

| # | Dataset | Simulated source system | Source type | Frequency |
|---|---|---|---|---|
| 1 | Drilling & blasting | Planning engineer's spreadsheet | **File** (Excel .xlsx) | 1 file per week |
| 2 | Equipment telemetry & events | Fleet management system (FMS) | **REST API** | Readings every 5 min + sensor events |
| 3 | Maintenance | Computerized maintenance management system (CMMS) | **Database** (PostgreSQL) | Transactional; rows created and updated continuously |
| 4 | Laboratory results | Laboratory information system (LIMS) | **File** (CSV/JSON export) | Daily batch |
| 5 | Crusher process & stops | Plant historian (SCADA) | **File** (CSV export) | Process every 1 min + stop events |
| 6 | Belt scale | Plant historian (SCADA) | **File** (CSV export) | Every 1 min + calibration log |
| 7 | Online analyzer | Analyzer software (via historian) | **File** (CSV export); candidate for **streaming** later | Every 1 min |

---

### 3.1 Drilling & blasting — Excel file

**File:** `drilling_blasting_YYYY-Www.xlsx`, sheet `blasts`, one row per blast, 3–6 blasts per week.

| Field | Type | Unit | Description |
|---|---|---|---|
| `blast_id` | str | — | Blast identifier (`BL-YYYYMMDD-NN`) |
| `blast_date` | date | — | Blast date |
| `blast_time` | time | — | Detonation time |
| `bench_id` | str | — | Blasted bench |
| `material_type` | enum | — | Bench's dominant material |
| `drill_id` | str | — | Drill rig used |
| `holes_count` | int | — | Number of blast holes |
| `hole_diameter_mm` | float | mm | Hole diameter |
| `hole_depth_m` | float | m | Average hole depth |
| `burden_m` | float | m | Pattern burden |
| `spacing_m` | float | m | Pattern spacing |
| `drilled_meters` | float | m | Total drilled meters |
| `explosive_type` | enum | — | `ANFO`, `EMULSION` |
| `explosive_kg` | float | kg | Explosive loaded |
| `detonators_count` | int | — | Detonators used |
| `rock_density_t_m3` | float | t/m³ | Density used in the estimate |
| `estimated_volume_bcm` | float | m³ | Estimated in-situ volume |
| `estimated_tonnage_t` | float | t | Estimated tonnage |
| `oversize_observed` | enum | — | `low`, `medium`, `high` (visual observation) |
| `status` | enum | — | `executed`, `cancelled` |
| `notes` | str | — | Engineer's free text |

*Calculated in Silver/Gold:* powder factor (kg/t), blasts per week, blasted vs. hauled tonnage.

---

### 3.2 Equipment telemetry & events — REST API

Simulates the API of a fleet management system (FMS) that **does not deliver pre-built haul cycles**. It only provides periodic readings and raw sensor events. Haul cycles (queue → load → haul loaded → dump → return) **are rebuilt in Silver** from these events.

Periodic readings follow the ISO 15143-3 / AEMP 2.0 telematics standard (cumulative hours, cumulative fuel, distance, position, idle hours). Events represent what the equipment sensors detect:

- **Weight:** truck suspension pressure (on-board payload sensor). This is the **only per-trip weight** in the system.
- **Bucket passes:** weight steps on the truck, plus bucket weighing on the loading unit.
- **Body:** truck body up/down sensor.
- **Location:** geofence entries and exits.

**Endpoints:**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/equipment` | Equipment catalog |
| GET | `/zones` | Geofence catalog |
| GET | `/telemetry?since=&until=&page=` | Periodic readings (paginated) |
| GET | `/events?since=&until=&page=` | Sensor events (paginated) |

`since`/`until` filter on `received_ts` and enable **incremental loading**. The API returns random errors (HTTP 500, 503 and 429) at a configurable rate, to practice retries.

#### `/equipment`

| Field | Type | Unit | Description |
|---|---|---|---|
| `equipment_id` | str | — | Equipment ID |
| `equipment_type` | enum | — | `drill`, `excavator`, `loader`, `haul_truck` |
| `model_class` | str | — | Generic class (e.g. "Rigid haul truck 55 t") |
| `nominal_payload_t` | float | t | Haul trucks only |
| `bucket_capacity_t` | float | t | Excavators and loaders only |
| `fuel_tank_l` | float | L | Tank capacity |
| `commissioned_date` | date | — | Commissioning date |

#### `/zones`

| Field | Type | Description |
|---|---|---|
| `zone_id` | str | Geofence ID. Zones tied to an asset reuse its ID (bench, hopper, dump); other zones use `ZN-TTT-NN` |
| `zone_type` | enum | `load`, `queue`, `dump_crusher`, `dump_waste`, `workshop`, `parking` |
| `polygon_wkt` | str | Zone polygon (WKT) |

#### `/telemetry` (every 5 min per unit)

| Field | Type | Unit | Description |
|---|---|---|---|
| `record_id` | str | — | Unique record ID |
| `equipment_id` | str | — | Equipment |
| `timestamp` | datetime (UTC) | — | Reading time |
| `latitude` / `longitude` | float | ° | GPS position |
| `engine_on` | bool | — | Engine running |
| `speed_kmh` | float | km/h | Instant speed |
| `engine_hours_cum` | float | h | Cumulative engine hours |
| `idle_hours_cum` | float | h | Cumulative idle hours |
| `fuel_used_cum_l` | float | L | Cumulative fuel used |
| `fuel_level_pct` | float | % | Tank level |
| `odometer_km` | float | km | Cumulative distance |
| `engine_load_pct` | float | % | Engine load |
| `coolant_temp_c` | float | °C | Coolant temperature |
| `payload_t` | float | t | Current weight reading (trucks only) |
| `body_raised` | bool | — | Body up (trucks only) |
| `fault_code` | str \| null | — | Active fault code |

#### `/events` (one record per detected event)

| Field | Type | Unit | Description |
|---|---|---|---|
| `event_id` | str | — | Unique event ID |
| `equipment_id` | str | — | Equipment that generated the event |
| `event_ts` | datetime (UTC) | — | When it happened on the equipment |
| `received_ts` | datetime (UTC) | — | When it reached the server (can be much later after a signal loss) |
| `event_type` | enum | — | See event types |
| `zone_id` | str \| null | — | Geofence (zone events) |
| `payload_t` | float \| null | t | Truck weight after the event |
| `bucket_weight_t` | float \| null | t | Bucket weight (loading-unit events) |
| `related_equipment_id` | str \| null | — | Truck that received the bucket |
| `operator_id` | str \| null | — | Operator (login/logout events) |
| `odometer_km` | float | km | Odometer at event time |
| `fuel_used_cum_l` | float | L | Cumulative fuel at event time |

**Event types:**

| `event_type` | Generated by | Source sensor |
|---|---|---|
| `zone_enter` / `zone_exit` | All | GPS + geofences |
| `payload_step` | Haul truck | Suspension pressure (each bucket pass raises the weight) |
| `bucket_dump` | Excavator / loader | Hydraulic bucket weighing |
| `body_up` / `body_down` | Haul truck | Body sensor. `body_down` carries the residual weight left in the body (carryback) |
| `operator_login` / `operator_logout` | All | Cab terminal (also marks handovers and meal breaks) |
| `engine_start` / `engine_stop` | All | Engine control unit |

**Normal truck cycle sequence (what Silver must rebuild):**

```text
zone_enter (queue) → zone_enter (load) → payload_step × N → zone_exit (load)
  → zone_enter (dump_crusher | dump_waste) → body_up → body_down → zone_exit
  → (empty return) → zone_enter (queue) ...
```

*Calculated in Silver:*
- Haul cycles with queue, load, loaded haul, dump and return times.
- Bucket passes (count of `payload_step`).
- **On-board trip payload** = last `payload_step` − residual weight at `body_down`.
- Origin bench and destination (from zones).
- Loaded/empty distance and fuel per cycle (differences in `odometer_km` and `fuel_used_cum_l` between events).

*Calculated in Gold:* tonnes moved per hour and per shift, fuel consumption in L/t and L/h, utilization, and actual vs. nominal payload.

---

### 3.3 Maintenance — PostgreSQL database (CMMS)

Simulates the operational database of a computerized maintenance management system, in its own schema (`cmms`), separate from the data warehouse. It records the asset registry, failure notifications, work orders, preventive plans and spare-part movements.

Rows are **created and then updated** as work progresses (a work order moves from `created` to `closed` over hours or days). Every table has `updated_at`, which enables **incremental loading** now and **change data capture (CDC)** later (roadmap ET-07).

The CMMS **does not share IDs** with the FMS or the historian. Links are rebuilt in Silver by asset and time window, for example a crusher stop with its corrective work order, or a truck in the workshop zone with its open work order.

#### Table `cmms.assets`

| Field | Type | Unit | Description |
|---|---|---|---|
| `asset_id` | str | — | PK. Uses the project naming convention (e.g. `1-91-TRK-01`) |
| `parent_asset_id` | str \| null | — | Parent asset (e.g. the payload sensor belongs to a truck) |
| `description` | str | — | Asset description |
| `asset_class` | enum | — | `mobile_equipment`, `fixed_equipment`, `instrument` |
| `criticality` | enum | — | `A` (critical), `B`, `C` |
| `install_date` | date | — | Installation date |
| `status` | enum | — | `in_service`, `out_of_service`, `retired` |
| `updated_at` | datetime (UTC) | — | Last change |

Instruments are registered as child assets so they can have their own work orders: payload sensors (`1-91-PLS-XX`), the belt scale and the analyzer. The hierarchy lives in `parent_asset_id`, not in the ID: every asset ID keeps the 4-segment `A-GL-TTT-NN` format. A payload sensor's sequence number matches its truck's (`1-91-PLS-01` → `1-91-TRK-01`).

#### Table `cmms.notifications` (failure reports)

| Field | Type | Unit | Description |
|---|---|---|---|
| `notification_id` | bigserial | — | PK |
| `notification_number` | str | — | Printed number (`NT-YYYYMMDD-NNNN`) |
| `asset_id` | str | — | FK → `cmms.assets` |
| `reported_ts` | datetime (UTC) | — | When the problem was reported |
| `reported_by` | str | — | Operator (anonymous code) |
| `symptom_code` | str | — | Reported symptom (e.g. `NOISE`, `LEAK`, `OVERHEAT`, `NO_START`, `READING_ERROR`) |
| `description` | str | — | Free text |
| `priority` | enum | — | `1` (immediate) to `4` (low) |
| `work_order_id` | bigint \| null | — | FK → `cmms.work_orders`, once one is created |
| `status` | enum | — | `open`, `in_process`, `closed` |
| `created_at` | datetime (UTC) | — | Record creation |
| `updated_at` | datetime (UTC) | — | Last change |

#### Table `cmms.work_orders`

| Field | Type | Unit | Description |
|---|---|---|---|
| `work_order_id` | bigserial | — | PK |
| `work_order_number` | str | — | Printed number (`WO-YYYYMMDD-NNNN`) |
| `asset_id` | str | — | FK → `cmms.assets` |
| `work_order_type` | enum | — | `preventive`, `corrective`, `calibration`, `inspection` |
| `pm_plan_id` | bigint \| null | — | FK → `cmms.pm_plans` (preventive orders only) |
| `priority` | enum | — | `1` to `4` |
| `status` | enum | — | `created`, `released`, `in_progress`, `completed`, `closed`, `cancelled` |
| `planned_start_ts` / `planned_end_ts` | datetime (UTC) | — | Planned window |
| `actual_start_ts` / `actual_end_ts` | datetime (UTC) \| null | — | Actual execution window |
| `failure_code` | str \| null | — | What failed (e.g. `BEARING`, `HYDRAULIC`, `ELECTRICAL`, `LINER_WEAR`, `SENSOR_DRIFT`) |
| `cause_code` | str \| null | — | Why it failed (e.g. `WEAR`, `CONTAMINATION`, `OVERLOAD`, `OPERATOR`, `UNKNOWN`) |
| `action_code` | str \| null | — | What was done (e.g. `REPLACE`, `REPAIR`, `ADJUST`, `CALIBRATE`, `CLEAN`) |
| `labor_hours` | float \| null | h | Total technician hours |
| `technician_id` | str \| null | — | Lead technician (anonymous code) |
| `created_at` | datetime (UTC) | — | Record creation |
| `updated_at` | datetime (UTC) | — | Last change |

#### Table `cmms.pm_plans` (preventive maintenance plans)

| Field | Type | Unit | Description |
|---|---|---|---|
| `pm_plan_id` | bigserial | — | PK |
| `asset_id` | str | — | FK → `cmms.assets` |
| `task_description` | str | — | Task (e.g. "Replace crusher hammers", "250 h truck service") |
| `trigger_type` | enum | — | `calendar_days`, `engine_hours`, `tonnage` |
| `trigger_interval` | float | — | Interval in days, engine hours or tonnes |
| `last_completed_ts` | datetime (UTC) \| null | — | Last execution |
| `active` | bool | — | Plan in use |
| `updated_at` | datetime (UTC) | — | Last change |

#### Table `cmms.materials` (spare-parts catalog)

| Field | Type | Unit | Description |
|---|---|---|---|
| `material_id` | str | — | PK (`MAT-NNNNN`) |
| `description` | str | — | Part description (e.g. "Crusher hammer", "Haul truck tire 24.00R35") |
| `unit_of_measure` | enum | — | `EA`, `L`, `KG`, `M` |
| `unit_cost` | numeric | COP | Standard unit cost |
| `min_stock` / `reorder_point` | float | — | Stock policy |
| `updated_at` | datetime (UTC) | — | Last change |

#### Table `cmms.material_movements`

| Field | Type | Unit | Description |
|---|---|---|---|
| `movement_id` | bigserial | — | PK |
| `material_id` | str | — | FK → `cmms.materials` |
| `movement_type` | enum | — | `goods_issue` (to a work order), `goods_receipt` (from supplier), `return` |
| `quantity` | float | — | Quantity moved |
| `work_order_id` | bigint \| null | — | FK → `cmms.work_orders` (issues and returns) |
| `storage_location` | str | — | Warehouse location |
| `movement_ts` | datetime (UTC) | — | Posting time |
| `created_at` | datetime (UTC) | — | Record creation |

*Calculated in Silver/Gold:* MTBF and MTTR per asset (combined with crusher stops and FMS downtime), preventive vs. corrective ratio, PM compliance, maintenance cost per asset and per tonne crushed, spare-part consumption, and payload-sensor calibration history (to explain changes in the reconciliation factor per truck).

---

### 3.4 Laboratory results — CSV/JSON export

The laboratory **validates and calibrates the analyzer**:

- **Shift composite sample:** one per shift, taken from the belt after the analyzer, compared against the analyzer's average for the same period.
- **Bench grade-control sample:** taken occasionally from a bench, to check the geological model's expected quality.

**File:** `lab_results_YYYYMMDD.csv`, plus a JSON with batch metadata. Results arrive **with a delay** (hours or days) and may include re-analyses, to practice *late-arriving data*.

| Field | Type | Unit | Description |
|---|---|---|---|
| `sample_id` | str | — | Sample ID |
| `sample_type` | enum | — | `shift_composite`, `bench_grade_control` |
| `sampling_point` | str | — | `2-11-ANZ-01` (belt) or a bench ID |
| `shift_id` | str \| null | — | Shift (composite samples) |
| `period_start_ts` / `period_end_ts` | datetime (UTC) \| null | — | Period the composite covers |
| `sampled_ts` | datetime (UTC) | — | Sampling time |
| `received_ts` | datetime (UTC) | — | Received at the lab |
| `analyzed_ts` | datetime (UTC) | — | Analysis completed |
| `method` | enum | — | `XRF` |
| `cao_pct` | float | % | Calcium oxide |
| `sio2_pct` | float | % | Silica |
| `al2o3_pct` | float | % | Alumina |
| `fe2o3_pct` | float | % | Iron oxide |
| `mgo_pct` | float | % | Magnesium oxide |
| `so3_pct` | float | % | Sulfur trioxide |
| `k2o_pct` | float | % | Potassium oxide |
| `na2o_pct` | float | % | Sodium oxide |
| `loi_pct` | float | % | Loss on ignition |
| `moisture_pct` | float | % | Moisture |
| `analyst_id` | str | — | Analyst (anonymous code) |
| `result_status` | enum | — | `preliminary`, `validated`, `reanalysis` |

*Calculated in Silver/Gold:* analyzer vs. lab bias per shift, geological model vs. actual quality per bench.

---

### 3.5 Primary crusher — historian export

Two files per day.

#### `crusher_process_YYYYMMDD.csv` (every 1 min)

| Field | Type | Unit | Description |
|---|---|---|---|
| `timestamp` | datetime (UTC) | — | Reading |
| `crusher_id` | str | — | Crusher |
| `running` | bool | — | Main motor running |
| `motor_power_kw` | float | kW | Main motor power |
| `motor_current_a` | float | A | Current |
| `feeder_speed_pct` | float | % | Feeder speed (hopper discharge) |
| `hopper_level_pct` | float | % | Hopper level (used in Silver to model the hopper inventory) |
| `css_mm` | float | mm | Closed side setting |
| `bearing_temp_c` | float | °C | Bearing temperature |
| `vibration_mm_s` | float | mm/s | Vibration |

#### `crusher_events_YYYYMMDD.csv` (one row per stop or delay)

| Field | Type | Unit | Description |
|---|---|---|---|
| `event_id` | str | — | Event ID |
| `crusher_id` | str | — | Crusher |
| `start_ts` | datetime (UTC) | — | Stop start |
| `end_ts` | datetime (UTC) \| null | — | Stop end (null if still open) |
| `event_category` | enum | — | See stop categories |
| `reason_code` | str | — | Cause code |
| `description` | str | — | Operator's text |
| `reported_by` | str | — | Operator (anonymous code) |

**Stop categories:**

| `event_category` | `reason_code` examples | Counts against availability? |
|---|---|---|
| `planned_maintenance` | Hammer/liner change, inspection, lubrication | Reported separately |
| `unplanned_mechanical` | Bearing, shaft, hydraulic leak | Yes |
| `unplanned_electrical` | Motor trip, drive fault, sensor | Yes |
| `process_blockage` | Hopper/chute blockage, wet or clayey material, oversize rock | Plant rule |
| `no_feed` | No trucks, feeder failure | No (idle) |
| `downstream_full` | Belt or stockpile full | No (idle) |
| `operational` | Shift handover, waiting for the rock breaker | Delay |

*Calculated in Silver/Gold:* availability, utilization, MTBF/MTTR, stop-cause Pareto.

---

### 3.6 Belt scale — historian export

Belt scale installed on the conveyor after the crusher. It multiplies the measured load on the belt by the belt speed to obtain the flow, and integrates the flow into a cumulative totalizer. It is the **reference measurement for crushed tonnage**.

#### `belt_scale_YYYYMMDD.csv` (every 1 min)

| Field | Type | Unit | Description |
|---|---|---|---|
| `timestamp` | datetime (UTC) | — | End of the 1-min interval |
| `scale_id` | str | — | 2-11-BWS-01 |
| `belt_speed_m_s` | float | m/s | Belt speed |
| `belt_load_kg_m` | float | kg/m | Average load per meter of belt |
| `flow_rate_tph` | float | t/h | Instant flow (load × speed) |
| `interval_tonnage_t` | float | t | Tonnage that passed in the interval |
| `totalizer_t` | float | t | Cumulative totalizer (never resets, except after a scale replacement) |
| `scale_status` | enum | — | `ok`, `belt_empty`, `zeroing`, `fault` |

#### `belt_scale_calibration_YYYYMMDD.csv` (one row per calibration action)

| Field | Type | Unit | Description |
|---|---|---|---|
| `calibration_id` | str | — | Calibration ID |
| `scale_id` | str | — | 2-11-BWS-01 |
| `calibration_ts` | datetime (UTC) | — | When it was performed |
| `calibration_type` | enum | — | `zero` (daily, empty belt), `span_test_weight`, `material_test` |
| `as_found_value` | float | — | Zero offset or span factor before adjustment |
| `as_left_value` | float | — | Value after adjustment |
| `performed_by` | str | — | Technician (anonymous code) |

*Calculated in Silver/Gold:* crushed tonnes per hour, shift and day; effective crusher t/h; scale drift between calibrations; reconciliation factor against on-board payloads (section 4).

---

### 3.7 Online analyzer — historian export

Radiometric cross-belt analyzer installed on the same conveyor, after the belt scale. It measures the chemistry of the full material flow continuously, without sampling.

**File:** `analyzer_YYYYMMDD.csv` (one row per minute). A real-time stream (Kafka) is a later improvement (see roadmap ET-07).

| Field | Type | Unit | Description |
|---|---|---|---|
| `timestamp` | datetime (UTC) | — | End of the 1-min measurement interval |
| `analyzer_id` | str | — | 2-11-ANZ-01 |
| `cao_pct` | float | % | Calcium oxide |
| `sio2_pct` | float | % | Silica |
| `al2o3_pct` | float | % | Alumina |
| `fe2o3_pct` | float | % | Iron oxide |
| `mgo_pct` | float | % | Magnesium oxide |
| `so3_pct` | float | % | Sulfur trioxide |
| `k2o_pct` | float | % | Potassium oxide |
| `na2o_pct` | float | % | Sodium oxide |
| `moisture_pct` | float | % | Moisture |
| `measurement_status` | enum | — | `valid`, `low_load` (too little material), `no_flow`, `fault` |
| `calibration_version` | str | — | Active calibration ID |

Analyzer readings carry no tonnage. To weight quality by tonnage, Silver joins them with the belt scale, shifted by `scale_to_analyzer_delay_s`.

**Simulation ranges (design assumption):**

| Material | CaO % | MgO % | SiO₂ % |
|---|---|---|---|
| HG | 50 – 54 | < 2 | 1 – 5 |
| MG | 44 – 50 | 1 – 3 | 5 – 12 |
| Waste | not measured (never reaches the belt) | — | — |

Measured quality varies around each bench's expected values from the geological model.

*Calculated in Silver/Gold:* quality per trip, per bench and per shift; tonnage-weighted stockpile quality (input for Phase 02 blending).

---

## 4. Trip tonnage and quality attribution (Silver design)

No source system knows how much material, or what quality, each truck trip delivered to the stockpile. Silver derives it by linking FMS dump events to belt-scale and analyzer readings. This is the core cross-source challenge of Phase 01.

### 4.1 Why it is not trivial

- **The hopper is a buffer.** A truck dumps 35–55 t in about a minute, but the crusher draws material out continuously. A dump does not appear on the belt as one clean block: it overlaps with the material already in the hopper and with the next truck.
- **There are transport delays.** Material takes time to go from the hopper, through the crusher, to the belt scale and then to the analyzer.
- **The sensors disagree.** On-board payload is accurate to about ±5 % per trip. The belt scale is accurate to about ±0.5–1 %, but only in aggregate.
- **Events can be late or missing** (signal loss, incomplete sequences).

### 4.2 Approach: payload per trip, reconciled with the belt scale

The method combines both measurements, each where it is strongest:

1. **Per-trip estimate.** Each crusher trip starts with its on-board payload (section 3.2).
2. **Reconciliation factor per window.** For each window (default: shift), compute:

   ```text
   reconciliation_factor = belt-scale tonnage in the window
                           ÷ sum of on-board payloads dumped at the crusher in the window
   ```

   The belt-scale window is shifted by the hopper residence time and `crusher_to_scale_delay_s`, so it covers the material those trucks actually delivered.
3. **Reconciled trip tonnage** = on-board payload × reconciliation factor. The sum of reconciled trips per shift equals the belt-scale total exactly.
4. **Quality per trip.** The hopper is modeled as **first-in, first-out (FIFO)**, using the dump times, the reconciled tonnages and the belt-scale flow. This gives the time interval when each trip's material passed the analyzer. The trip quality is the tonnage-weighted average of the analyzer readings in that interval. Where trips overlap at the boundaries, readings are split proportionally.
5. **Waste trips** keep their on-board payload with no reconciliation, because no reference measurement exists. They are flagged as `weight_source = onboard_payload`.

### 4.3 Expected outputs and quality flags

| Output | Description |
|---|---|
| `onboard_payload_t` | Raw payload from the truck sensor |
| `reconciled_tonnage_t` | Payload scaled by the shift reconciliation factor (crusher trips only) |
| `reconciliation_factor` | Factor applied, stored per shift |
| `weight_source` | `belt_reconciled` or `onboard_payload` |
| `belt_window_start_ts` / `belt_window_end_ts` | Interval attributed to the trip on the belt |
| `cao_pct`, `mgo_pct`, `sio2_pct`, … | Tonnage-weighted analyzer quality for the trip |
| `attribution_confidence` | `high`, `medium`, `low`: lowered when the factor falls outside 0.95–1.05, the analyzer status is not `valid`, or the trip events are incomplete |

A per-truck history of reconciliation factors also reveals trucks whose payload sensor is drifting. The `calibration` work orders in the CMMS show when each sensor was corrected.

---

## 5. Cross-source consistency rules

1. A truck only generates cycle events while its engine is on, an operator is logged in, and a shift is scheduled.
2. The sum of `bucket_weight_t` from `bucket_dump` events for a truck ≈ that truck's last `payload_step` (±3–5 %).
3. Per shift, the sum of on-board payloads dumped at `2-11-HOP-01` ≈ the belt-scale tonnage for the same (delay-shifted) window, within ±5 %.
4. The belt-scale `totalizer_t` increases by the same amount as the sum of `interval_tonnage_t`, and never goes backwards.
5. Cumulative tonnes hauled from a bench never exceed the tonnes blasted from it plus its `initial_broken_stock_t`.
6. `WASTE` trips always go to `1-81-DMP-01` and never reach the belt.
7. Analyzer quality follows the expected quality of the benches feeding the hopper, with realistic variation.
8. When the crusher is stopped, trucks bound for it queue or are redirected, the belt scale reports `belt_empty` and the analyzer reports `no_flow`. The hopper level stays constant or rises.
9. Outside scheduled shifts (00:00–08:00 and Sundays) there are no cycles or crusher feed. Telemetry shows engines off.
10. During handovers and staggered meal breaks, individual trucks pause, but the crusher keeps receiving feed while the hopper has material.
11. Every crusher stop in categories `planned_maintenance`, `unplanned_mechanical` or `unplanned_electrical` has a matching work order on `2-11-CRS-01` whose actual window overlaps the stop.
12. A truck that spends time in the workshop zone has a work order whose actual window overlaps that stay, and generates no cycle events meanwhile.
13. A truck's payload-sensor bias disappears after a `calibration` work order on its sensor is completed.
14. `goods_issue` movements only reference work orders that are `released` or later, and posting times fall within the work order's actual window (with a small tolerance).

## 6. Intentional data quality issues

Injected at a configurable rate (default 1–2 %):

- Nulls in non-key fields
- Timestamps out of order
- Telemetry with engine hours going backwards
- Crusher stops with no `end_ts`
- Duplicate FMS events (same `event_id` resent)
- Late events: `received_ts` hours after `event_ts` (signal loss)
- Incomplete sequences: missing `body_down` or `zone_exit`
- `payload_step` with weight dropping during loading (sensor noise)
- **Payload sensor bias:** one truck reads consistently 6–10 % high or low until its sensor is recalibrated
- **Carryback:** material left in the body after dumping (`body_down` with residual weight above 0)
- **Belt-scale zero drift:** a gradual offset that resets at the next `zero` calibration
- Analyzer drift: a gradual bias against the lab that resets when `calibration_version` changes
- Lab CaO out of range
- Work orders `closed` with no `actual_end_ts`, or with `actual_end_ts` before `actual_start_ts`
- Work orders updated days after completion (late status changes that incremental loads must pick up)
- `goods_issue` movements with no work order
- Maintenance stops with no matching work order, and work orders with no matching stop

## 7. General conventions

- **Time zone:** source timestamps in UTC. Shift times are defined in local time (America/Bogota), and Silver converts between both.
- **Units:** metric, tonnes for all weights. Costs in Colombian pesos (COP).
- **Reproducibility:** the simulator accepts `--seed`, `--start-date` and `--days`.
- **People identifiers:** always anonymous codes, never names.
- **Language:** all code, field names and documentation in English.
