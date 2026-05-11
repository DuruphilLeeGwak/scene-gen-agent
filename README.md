# Scene Gen Agent

> Proof-of-concept for generative simulation: an LLM agent that autonomously generates diverse 3D training environments in Unity, inspired by the data synthesis challenges in robotics foundation model training.

![Demo](output/screenshots/variant_00.png)

## Overview

Scene Gen Agent is a pipeline that takes a natural language description and automatically generates diverse 3D scenes in Unity. Given a single text prompt, the system produces multiple randomized scene variants — demonstrating how LLM-driven environment synthesis can scale the creation of training data for robotics models.

**3 prompts → 15 unique scenes, fully automated.**

## How It Works
## Demo

| Warehouse | Laboratory | Outdoor |
|---|---|---|
| ![](output/screenshots/variant_00.png) | ![](output/screenshots/variant_05.png) | ![](output/screenshots/variant_10.png) |

## Relevance to Robotics Data Synthesis

Training robust robotics foundation models requires massive amounts of diverse environment data. Manual scene creation doesn't scale. This project demonstrates a core primitive of that pipeline:

- **LLM as scene interpreter** — translates semantic descriptions into structured 3D configurations
- **Automatic variation** — seed-based randomization of position, scale, and color generates diverse training samples from a single prompt
- **Structured output** — JSON schema bridges the LLM and simulation engine, enabling scalable data pipelines

## Tech Stack

- **Claude API** (claude-sonnet-4-5) — scene interpretation agent
- **Python** — API pipeline and JSON orchestration
- **Unity 6 / C#** — real-time 3D scene generation
- **JSON** — structured scene description format

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
ANTHROPIC_API_KEY=your_api_key_here
### 3. Generate a Scene

```bash
cd python
python prompt_to_scene.py "dark warehouse with 3 boxes and 1 spotlight"
```

### 4. Load in Unity

- Open `SceneGenAgent` project in Unity 6
- Enable `CameraOrbit` component on the `SceneLoader` object
- Press Play — 5 scene variants are auto-generated and recorded

## Example Prompts
"dark warehouse with 3 boxes and 1 spotlight"
"bright laboratory with robot arm and 2 point lights"
"outdoor area with 3 spheres and directional sunlight"
## Project Structure
scene-gen-agent/
├── python/
│   └── prompt_to_scene.py    # Claude API → JSON pipeline
├── SceneGenAgent/
│   └── Assets/Scripts/
│       ├── SceneLoader.cs     # JSON → Unity scene
│       ├── SceneVariant.cs    # Random variation generator
│       └── CameraOrbit.cs    # 360° orbit recorder
├── output/
│   ├── screenshots/           # Generated scene images
│   └── recording/             # Orbit videos
└── README.md
## Author

**Jooyoung Gwak (두루필)**
Media Artist & Technical Artist
- Unity / Unreal Engine interactive installation
- LLM agent systems
- Generative simulation for robotics training data

[GitHub](https://github.com/DuruphilLeeGwak)