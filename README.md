# Scene Gen Agent

> **Proof-of-concept for generative simulation**: an LLM agent that autonomously generates diverse 3D training environments in Unity, inspired by the data synthesis challenges in robotics foundation model training.
>
> Now extended into a full material-to-scene pipeline: real-world material capture → PBR texture generation via ControlNet → LLM scene design → automated evaluation.

---

## Demo

### 360° Orbit — Dark Warehouse (5 Variants)
![Demo Video](docs/demo_warehouse.gif)

| Variant 00 | Variant 01 | Variant 02 |
|---|---|---|
| ![](docs/images/warehouse_00.png) | ![](docs/images/warehouse_01.png) | ![](docs/images/warehouse_02.png) |

| Variant 03 | Variant 04 | |
|---|---|---|
| ![](docs/images/warehouse_03.png) | ![](docs/images/warehouse_04.png) | |

### Laboratory Scene
| Variant 00 | Variant 01 | Variant 02 |
|---|---|---|
| ![](docs/images/lab_00.png) | ![](docs/images/lab_01.png) | ![](docs/images/lab_02.png) |

### Outdoor Scene
| Variant 00 | Variant 01 | Variant 02 |
|---|---|---|
| ![](docs/images/outdoor_00.png) | ![](docs/images/outdoor_01.png) | ![](docs/images/outdoor_02.png) |

---

## Overview

Scene Gen Agent is a pipeline that takes a natural language description and automatically generates diverse 3D scenes in Unity Engine.

Given a single text prompt, the system:
1. Interprets the description via Claude API (LLM agent)
2. Outputs a structured JSON scene configuration
3. Spawns 3D objects, lighting, and environment in Unity
4. Generates multiple randomized variants from a single prompt

**Result: 3 prompts → 15 unique scenes, fully automated.**

---

## System Architecture

### Original Pipeline

```
Text Prompt
  │
  ▼
Claude API ──────── LLM Scene Interpreter
  │
  ▼
scene.json ─────── Structured scene config
  │                (objects, lights, environment)
  ▼
Unity C# Script ── Auto scene generation
  │
  ▼
Scene Variants ─── Seed-based randomization
  │                (position, scale, color)
  ▼
Output ─────────── Screenshots + 360° orbit video
```

### Extended Pipeline (in development)

```
Real Material Photo
  │
  ▼
Preprocessing ────── Lighting removal, diffuse flatten
  │
  ▼
ControlNet ──────── Albedo refinement + Normal map generation
  │
  ▼
PBR Texture Set ─── albedo / normal / roughness / metallic
  │
  ▼
Material Metadata ── Dominant color, category, roughness value
  │
  ▼
Claude API ──────── LLM interior scene design from material input
  │
  ▼
scene.json ─────── Scene config with material assignment
  │
  ▼
Unity Scene ─────── Auto-generated + texture applied
  │
  ▼
Claude Vision API ── Automated evaluation (coherence, lighting, composition)
  │
  ▼
evaluation_report.json
```

---

## Relevance

### Robotics Data Synthesis
Training robust robotics foundation models requires massive amounts of diverse environment data. Manual scene creation does not scale. This project demonstrates a core primitive of that pipeline:

- **LLM as scene interpreter** — translates semantic descriptions into structured 3D configurations
- **Automatic variation** — seed-based randomization generates diverse training samples from a single prompt
- **Structured output** — JSON schema bridges the LLM and simulation engine
- **Extensible** — scales to complex manipulation environments, object placement policies, and domain randomization for sim-to-real transfer

### XR and Spatial Computing
The extended pipeline addresses a recurring problem in XR and architectural visualization: bringing real-world materials into digital environments at scale, without manual authoring for each asset.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Agent | Claude API (claude-sonnet-4-5) |
| Image Pipeline | Python 3 + ComfyUI + ControlNet |
| Simulation | Unity 6 (Built-in Render Pipeline) |
| Scene Format | JSON |
| Version Control | Git / GitHub |
| CI/CD | GitHub Actions (planned) |

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/DuruphilLeeGwak/scene-gen-agent.git
cd scene-gen-agent/python
python -m venv venv
venv\Scripts\activate
pip install anthropic python-dotenv
```

### 2. Set API Key

Create `.env` in the root directory:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Generate a Scene

```bash
cd python
python prompt_to_scene.py "dark warehouse with 3 boxes and 1 spotlight"
```

### 4. Load in Unity

- Open `SceneGenAgent` project in Unity 6
- Enable `CameraOrbit` component on the `SceneLoader` object
- Press Play — 5 scene variants auto-generated and recorded

---

## Example Prompts

```
"dark warehouse with 3 boxes and 1 spotlight"
"bright laboratory with robot arm and 2 point lights"
"outdoor area with 3 spheres and directional sunlight"
```

---

## Project Structure

```
scene-gen-agent/
├── python/
│   ├── prompt_to_scene.py        # Claude API → JSON pipeline
│   └── capture_to_pbr.py         # Material photo → PBR texture set (in development)
├── SceneGenAgent/
│   └── Assets/
│       └── Scripts/
│           ├── SceneLoader.cs    # JSON → Unity scene generation
│           ├── SceneVariant.cs   # Seed-based random variation
│           └── CameraOrbit.cs   # 360° orbit recorder
├── docs/
│   ├── demo_warehouse.gif
│   └── images/
│       ├── warehouse_00.png
│       ├── lab_00.png
│       └── outdoor_00.png
└── README.md
```

---

## Development Roadmap

**Target: 18 Jun 2026 – 16 Jul 2026 (approx. 4 weeks, 1 hour/day)**

---

### Phase 1 — Material Capture to PBR Texture Pipeline
**18 Jun – 2 Jul**

Goal: Given a single smartphone photo of a real material, automatically output a PBR texture set ready for use in Unity or Unreal Engine 5.

---

**Step 1.1 — Capture and Preprocessing**

Remove lighting influence from raw photo. Flatten to diffuse color only.

- [ ] Select first test material (concrete, stone, or fabric)
- [ ] Photograph under consistent lighting conditions
- [ ] Write Python script to normalize brightness and reduce specular highlights
- [ ] Output: cleaned source image ready for ControlNet

**Cleared:** —

---

**Step 1.2 — ControlNet Albedo Refinement**

Use ControlNet (Canny or Tile model) to generate a lighting-free albedo from the cleaned photo.

- [ ] Set up ComfyUI workflow with ControlNet Canny or Tile conditioning
- [ ] Tune prompt and denoise strength for material type
- [ ] Validate output: albedo should be flat, no baked shadows
- [ ] Output: `albedo.png`

**Cleared:** —

---

**Step 1.3 — Normal Map Generation**

Generate a physically plausible normal map from the source image.

- [ ] Test ControlNet normal map model output
- [ ] Compare with height-to-normal conversion (numpy fallback)
- [ ] Select best method per material category
- [ ] Output: `normal.png`

**Cleared:** —

---

**Step 1.4 — Roughness and Metallic Estimation**

Rule-based estimation guided by material category input.

- [ ] Define material category list (metal / fabric / wood / stone / concrete / ceramic)
- [ ] Write roughness and metallic range lookup per category
- [ ] Apply color analysis to refine roughness within category range
- [ ] Output: `roughness.png`, `metallic.png`

**Cleared:** —

---

**Step 1.5 — Pipeline Integration and Output**

Wire all steps into a single Python script. Standardize output format.

- [ ] Single entry point: `python capture_to_pbr.py <image_path> <material_category>`
- [ ] Output folder: `output/<material_name>/` with 4 textures and source image
- [ ] File naming: `<name>_albedo.png`, `<name>_normal.png`, `<name>_roughness.png`, `<name>_metallic.png`
- [ ] README usage example updated

**Cleared:** —

---

**Step 1.6 — Unity / UE5 Material Validation**

Apply generated textures in engine. Verify physical plausibility under different lighting.

- [ ] Import texture set into Unity (Built-in or HDRP)
- [ ] Import texture set into UE5 (optional)
- [ ] Render under 3 lighting conditions: neutral, warm, cool
- [ ] Side-by-side comparison: real material photo vs rendered material
- [ ] Output: render screenshots for portfolio

**Cleared:** —

---

### Phase 2 — LLM Scene Design from Material Metadata
**3 Jul – 9 Jul**

Goal: Feed material properties extracted from Phase 1 into Claude API to automatically design an interior scene layout.

---

**Step 2.1 — Material Metadata Extraction**

- [ ] Extract dominant color, texture frequency, and estimated material category from Phase 1 output
- [ ] Format as structured JSON: `{ "category": "stone", "color": "#8B8B7A", "roughness": 0.8 }`

**Cleared:** —

---

**Step 2.2 — LLM Scene Interpreter**

Extension of the original `prompt_to_scene.py`.

- [ ] Extend pipeline to accept material metadata as input alongside text prompt
- [ ] Design system prompt: LLM generates interior scene configuration from given material
- [ ] Output: `scene.json` with object placement, lighting, and environment settings

**Cleared:** —

---

**Step 2.3 — Scene Generation in Unity**

- [ ] Update `SceneLoader.cs` to support material assignment from texture set
- [ ] Auto-apply Phase 1 textures to generated scene objects
- [ ] Generate 5 variants with seed-based randomization

**Cleared:** —

---

**Step 2.4 — GitHub Actions CI/CD** *(new)*

Add automated testing and validation to the pipeline.

- [ ] Write unit test for `prompt_to_scene.py` JSON output schema
- [ ] Write unit test for `capture_to_pbr.py` output file existence
- [ ] Set up GitHub Actions workflow: runs tests on every push
- [ ] Badge added to README

**Cleared:** —

---

### Phase 3 — Automated Evaluation
**10 Jul – 16 Jul**

Goal: Use Claude Vision API to evaluate generated scenes for material coherence, lighting interaction, and spatial quality.

---

**Step 3.1 — Evaluation Criteria Definition**

- [ ] Define scoring dimensions: material consistency, lighting plausibility, spatial composition
- [ ] Write evaluation prompt for Claude Vision API
- [ ] Output: JSON score per scene variant

**Cleared:** —

---

**Step 3.2 — Evaluation Pipeline**

- [ ] Capture screenshots of generated scenes automatically
- [ ] Pass to Claude Vision API with evaluation prompt
- [ ] Aggregate scores across variants
- [ ] Output: `evaluation_report.json`

**Cleared:** —

---

**Step 3.3 — Feedback Loop** *(optional)*

- [ ] Use evaluation scores to re-prompt LLM for improved scene configuration
- [ ] Run one iteration of prompt refinement based on lowest-scoring dimension
- [ ] Document improvement delta

**Cleared:** —

---

## Progress Log

| Date | Step | Work Done |
|---|---|---|
| 18 Jun 2026 | — | Project roadmap initialized. Extended pipeline direction defined. |

---

## Notes

- Phase 1 is the foundation. Do not proceed to Phase 2 until Step 1.6 render output is satisfactory.
- ControlNet method may vary per material category. Document which model works best for each.
- All render outputs go to `docs/images/` for portfolio use.
- Hyperlinks in PDF output are handled manually in InDesign.

---

## Author

**Jooyoung Gwak (두루필)**
Media Artist and Real-time Developer

- Unity / Unreal Engine interactive installation
- LLM agent pipeline development
- Generative simulation and AI driven content pipelines

[GitHub](https://github.com/DuruphilLeeGwak)
