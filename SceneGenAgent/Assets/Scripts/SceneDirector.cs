using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;

// Scene Director — Unity UI frontend for the LLM scene generation pipeline.
//
// UI setup (create in Unity Editor before use):
//   Canvas (Screen Space - Overlay)
//   └── Panel (full-screen, semi-transparent)
//       ├── PromptField    InputField   — LLM prompt input
//       ├── CountField     InputField   — number of variants to generate (default: 1)
//       ├── StatusText     Text         — "Generating variant 2/5... (3.1s)"
//       ├── CostText       Text         — API call count + cost breakdown
//       ├── VariantText    Text         — "Variant 2 / 5"
//       ├── PrevButton     Button       — ◄  (also: Left arrow key)
//       └── NextButton     Button       — ►  (also: Right arrow key)
//
// Attach this script to any GameObject and wire the references in Inspector.
// Set SceneLoader reference to the existing SceneLoader GameObject.
public class SceneDirector : MonoBehaviour
{
    [Header("UI References")]
    public InputField promptField;
    public InputField countField;
    public Text statusText;
    public Text costText;
    public Text variantText;
    public Button prevButton;
    public Button nextButton;

    [Header("Scene")]
    public SceneLoader sceneLoader;

    [Header("Python")]
    [Tooltip("Leave blank to auto-detect venv Python at python/venv/Scripts/python.exe")]
    public string pythonExePath = "";

    // --- state ---
    private readonly List<string> variantPaths = new();
    private int currentIndex = 0;
    private bool isGenerating = false;
    private int totalApiCalls = 0;      // lifetime call counter (resets per session)
    private int lastRunCalls = 0;       // calls made in the last generation run

    private string RepoRoot =>
        Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));

    private string PythonScript =>
        Path.Combine(RepoRoot, "python", "prompt_to_scene.py");

    private string LastPromptPath =>
        Path.Combine(RepoRoot, "output", "last_prompt.txt");

    private string ResolvePython()
    {
        if (!string.IsNullOrEmpty(pythonExePath) && File.Exists(pythonExePath))
            return pythonExePath;
        string venvPy = Path.Combine(RepoRoot, "python", "venv", "Scripts", "python.exe");
        return File.Exists(venvPy) ? venvPy : "python";
    }

    // -------------------------------------------------------------------------

    void Start()
    {
        // Pre-fill prompt from last session
        if (File.Exists(LastPromptPath))
        {
            string saved = File.ReadAllText(LastPromptPath).Trim();
            if (!string.IsNullOrEmpty(saved))
                promptField.text = saved;
        }

        countField.text = "1";

        // Enter key in prompt field triggers generation
        promptField.onSubmit.AddListener(OnPromptSubmit);

        prevButton.onClick.AddListener(ShowPrev);
        nextButton.onClick.AddListener(ShowNext);

        RefreshUI();
    }

    void Update()
    {
        if (isGenerating) return;
        if (Input.GetKeyDown(KeyCode.LeftArrow))  ShowPrev();
        if (Input.GetKeyDown(KeyCode.RightArrow)) ShowNext();
    }

    // -------------------------------------------------------------------------

    void OnPromptSubmit(string prompt)
    {
        if (isGenerating || string.IsNullOrWhiteSpace(prompt)) return;
        int count = ParseCount();
        StartCoroutine(GenerateAll(prompt.Trim(), count));
    }

    IEnumerator GenerateAll(string prompt, int count)
    {
        isGenerating = true;
        variantPaths.Clear();
        currentIndex = 0;
        lastRunCalls = 0;

        string python = ResolvePython();
        string outDir = Path.Combine(RepoRoot, "output");
        Directory.CreateDirectory(outDir);

        // Persist prompt for next Play session
        File.WriteAllText(LastPromptPath, prompt);

        for (int i = 0; i < count; i++)
        {
            // Append variant hint so the LLM produces diverse outputs
            string variantPrompt = count > 1
                ? $"{prompt} [variant {i + 1} of {count}]"
                : prompt;

            string jsonPath = Path.Combine(outDir, $"scene_variant_{i}.json");

            float elapsed = 0f;

            // --- launch Python subprocess ---
            var psi = new ProcessStartInfo
            {
                FileName               = python,
                Arguments              = $"\"{PythonScript}\" \"{EscapeArg(variantPrompt)}\" --output \"{jsonPath}\"",
                UseShellExecute        = false,
                RedirectStandardError  = true,
                CreateNoWindow         = true,
            };

            Process proc;
            try { proc = Process.Start(psi); }
            catch (System.Exception ex)
            {
                statusText.text = $"Error launching Python: {ex.Message}";
                isGenerating = false;
                yield break;
            }

            totalApiCalls++;
            lastRunCalls++;
            RefreshCostUI(count, i + 1);

            // Poll until process exits, updating elapsed time each frame
            while (proc != null && !proc.HasExited)
            {
                elapsed += Time.deltaTime;
                statusText.text =
                    $"Generating variant {i + 1} / {count}...  {elapsed:F1}s";
                yield return null;
            }

            if (File.Exists(jsonPath))
            {
                variantPaths.Add(jsonPath);
                statusText.text =
                    $"Variant {i + 1} / {count} ready  ({elapsed:F1}s)";
            }
            else
            {
                string err = proc?.StandardError.ReadToEnd() ?? "";
                statusText.text =
                    $"Variant {i + 1} failed — check Console";
                UnityEngine.Debug.LogError($"[SceneDirector] variant {i + 1} error:\n{err}");
            }

            RefreshUI();
            yield return null;
        }

        isGenerating = false;

        if (variantPaths.Count > 0)
        {
            ShowVariant(0);
            statusText.text =
                $"Done — {variantPaths.Count} variant(s) in {lastRunCalls} API call(s)";
        }
        else
        {
            statusText.text = "No variants generated. Check Console for errors.";
        }

        RefreshUI();
    }

    // -------------------------------------------------------------------------

    void ShowVariant(int index)
    {
        if (variantPaths.Count == 0) return;
        currentIndex = Mathf.Clamp(index, 0, variantPaths.Count - 1);
        sceneLoader.jsonPath = variantPaths[currentIndex];
        sceneLoader.LoadScene();
        RefreshUI();
    }

    void ShowPrev() => ShowVariant(
        variantPaths.Count == 0 ? 0 : (currentIndex - 1 + variantPaths.Count) % variantPaths.Count
    );

    void ShowNext() => ShowVariant(
        variantPaths.Count == 0 ? 0 : (currentIndex + 1) % variantPaths.Count
    );

    // -------------------------------------------------------------------------

    void RefreshUI()
    {
        int total = variantPaths.Count;
        bool hasMany = total > 1 && !isGenerating;

        variantText.text = total > 0
            ? $"Variant  {currentIndex + 1}  /  {total}"
            : "—";

        prevButton.interactable = hasMany;
        nextButton.interactable = hasMany;

        RefreshCostUI(ParseCount(), lastRunCalls);
    }

    void RefreshCostUI(int requestedCount, int callsMadeThisRun)
    {
        // Show where cost is incurred: each variant = 1 API call to claude-sonnet-4-6
        // Input tokens ≈ 300 (system prompt + texture lib), output ≈ 400 (scene.json)
        // Sonnet 4.6: $3/M input, $15/M output → ≈ $0.0009 + $0.006 = ~$0.007 per call
        costText.text =
            $"API calls this run:  {callsMadeThisRun} / {requestedCount}\n" +
            $"Total this session:  {totalApiCalls}\n" +
            $"Cost source:  1 call per variant  (claude-sonnet-4-6)\n" +
            $"Est. per call:  ~$0.007  (300 in + 400 out tokens)";
    }

    int ParseCount()
    {
        return int.TryParse(countField.text, out int n) && n >= 1 ? n : 1;
    }

    static string EscapeArg(string s) => s.Replace("\"", "\\\"");
}
