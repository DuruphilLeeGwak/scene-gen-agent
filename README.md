# 🤖 Scene Gen Agent

> **Proof-of-concept for generative simulation**: an LLM agent that autonomously generates diverse 3D training environments in Unity, inspired by the data synthesis challenges in robotics foundation model training.

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

Scene Gen Agent is a pipeline that takes a **natural language description** and automatically generates diverse 3D scenes in Unity Engine.

Given a single text prompt, the system:
1. Interprets the description via Claude API (LLM agent)
2. Outputs a structured JSON scene configuration
3. Spawns 3D objects, lighting, and environment in Unity
4. Generates multiple randomized variants from a single prompt

**Result: 3 prompts → 15 unique scenes, fully automated.**

---

## System Architecture

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

---

## Relevance to Robotics Data Synthesis

Training robust robotics foundation models requires **massive amounts of diverse environment data**. Manual scene creation doesn't scale. This project demonstrates a core primitive of that pipeline:

- **LLM as scene interpreter** — translates semantic descriptions into structured 3D configurations
- **Automatic variation** — seed-based randomization generates diverse training samples from a single prompt
- **Structured output** — JSON schema bridges the LLM and simulation engine, enabling scalable pipelines
- **Extensible** — the same architecture scales to complex manipulation environments, object placement policies, and domain randomization for sim-to-real transfer

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Agent | Claude API (claude-sonnet-4-5) |
| Pipeline | Python 3 + python-dotenv |
| Simulation | Unity 6 (Built-in Render Pipeline) |
| Scene Format | JSON |
| Version Control | Git / GitHub |

---

## Quick Start

### 1. Clone & Setup

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
│   └── prompt_to_scene.py        # Claude API → JSON pipeline
├── SceneGenAgent/
│   └── Assets/
│       └── Scripts/
│           ├── SceneLoader.cs    # JSON → Unity scene generation
│           ├── SceneVariant.cs   # Seed-based random variation
│           └── CameraOrbit.cs   # 360° orbit recorder
├── docs/
│   ├── demo_warehouse.gif        # Demo GIF
│   └── images/                   # Scene screenshots
│       ├── warehouse_00.png
│       ├── warehouse_01.png
│       ├── ...
│       ├── lab_00.png
│       └── outdoor_00.png
└── README.md
```

---

## Author

**Jooyoung Gwak (두루필)**
Media Artist & Technical Artist

- Unity / Unreal Engine interactive installation
- LLM agent pipeline development
- Generative simulation for robotics training data

[GitHub](https://github.com/DuruphilLeeGwak)
