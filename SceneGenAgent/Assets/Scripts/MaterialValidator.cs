using UnityEngine;
using System.Collections;
using System.IO;
using System.Linq;

// Step 1.6 — PBR Material Validation
// Auto-detects the latest pipeline/output/YYYY-MM-DD_<material>/ folder and loads
// the first texture set found. Inspector fields override auto-detection if filled.
//
// Usage:
//   1. Attach to an empty GameObject in Unity.
//   2. Leave all paths blank for auto-detection, or override individual paths in Inspector.
//   3. Press Play — 3 screenshots saved to docs/images/validation/.
public class MaterialValidator : MonoBehaviour
{
    [Header("PBR Texture Paths — leave blank to auto-detect from latest pipeline output")]
    public string albedoPath;
    public string normalPath;
    public string roughnessPath;
    public string metallicPath;

    [Header("Output")]
    public string outputPath = "";  // blank = auto: <repo_root>/docs/images/validation

    private Light validationLight;
    private Material previewMaterial;

    // Repo root = two levels above Application.dataPath (Assets/)
    // dataPath:  .../SceneGenAgent/Assets
    // repoRoot:  .../scene-gen-agent
    private string RepoRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));

    private static readonly LightingCondition[] Conditions = {
        new LightingCondition("neutral", new Color(1.00f, 1.00f, 1.00f), 1.0f, new Vector3(50f, -30f, 0f)),
        new LightingCondition("warm",    new Color(1.00f, 0.82f, 0.55f), 1.3f, new Vector3(30f,  45f, 0f)),
        new LightingCondition("cool",    new Color(0.65f, 0.82f, 1.00f), 0.9f, new Vector3(65f, -60f, 0f)),
    };

    void Start()
    {
        ResolveTexturePaths();
        BuildScene();
        StartCoroutine(CaptureSequence());
    }

    // Fill any blank path fields by scanning the latest pipeline/output/ subfolder
    void ResolveTexturePaths()
    {
        string pipelineOutput = Path.Combine(RepoRoot, "pipeline", "output");

        if (!Directory.Exists(pipelineOutput))
        {
            Debug.LogWarning($"[MaterialValidator] pipeline/output not found at: {pipelineOutput}");
            return;
        }

        // Subfolders named YYYY-MM-DD_<material> — sort descending to get the latest
        string latestFolder = Directory.GetDirectories(pipelineOutput)
            .OrderByDescending(d => Path.GetFileName(d))
            .FirstOrDefault();

        if (latestFolder == null)
        {
            Debug.LogWarning("[MaterialValidator] No output folders found in pipeline/output");
            return;
        }

        Debug.Log($"[MaterialValidator] Auto-detected folder: {latestFolder}");

        // Fill each path if not already set in Inspector
        if (string.IsNullOrEmpty(albedoPath))
            albedoPath = FirstMatch(latestFolder, "*_albedo.png");
        if (string.IsNullOrEmpty(normalPath))
            normalPath = FirstMatch(latestFolder, "*_normal.png");
        if (string.IsNullOrEmpty(roughnessPath))
            roughnessPath = FirstMatch(latestFolder, "*_roughness.png");
        if (string.IsNullOrEmpty(metallicPath))
            metallicPath = FirstMatch(latestFolder, "*_metallic.png");

        // Log resolved paths
        Debug.Log($"[MaterialValidator] albedo:    {albedoPath}");
        Debug.Log($"[MaterialValidator] normal:    {normalPath}");
        Debug.Log($"[MaterialValidator] roughness: {roughnessPath}");
        Debug.Log($"[MaterialValidator] metallic:  {metallicPath}");
    }

    // Returns the first file matching a glob pattern in a folder, sorted ascending
    static string FirstMatch(string folder, string pattern)
    {
        string[] matches = Directory.GetFiles(folder, pattern);
        if (matches.Length == 0) return "";
        System.Array.Sort(matches);
        return matches[0];
    }

    void BuildScene()
    {
        GameObject plane = GameObject.CreatePrimitive(PrimitiveType.Plane);
        plane.name = "PBR_Preview";
        plane.transform.position = Vector3.zero;
        plane.transform.localScale = new Vector3(0.5f, 1f, 0.5f);

        previewMaterial = new Material(Shader.Find("Standard"));
        ApplyPBRTextures();
        plane.GetComponent<Renderer>().material = previewMaterial;

        Camera cam = Camera.main;
        if (cam != null)
        {
            cam.transform.position = new Vector3(0f, 3f, -2.5f);
            cam.transform.rotation = Quaternion.Euler(50f, 0f, 0f);
            cam.backgroundColor = new Color(0.1f, 0.1f, 0.1f);
            cam.clearFlags = CameraClearFlags.SolidColor;
        }

        GameObject lightGo = new GameObject("ValidationLight");
        validationLight = lightGo.AddComponent<Light>();
        validationLight.type = LightType.Directional;

        RenderSettings.ambientLight = new Color(0.12f, 0.12f, 0.12f);
    }

    void ApplyPBRTextures()
    {
        if (FileReady(albedoPath))
            previewMaterial.mainTexture = LoadTex(albedoPath);

        if (FileReady(normalPath))
        {
            previewMaterial.SetTexture("_BumpMap", LoadTex(normalPath));
            previewMaterial.EnableKeyword("_NORMALMAP");
            previewMaterial.SetFloat("_BumpScale", 1.0f);
        }

        if (FileReady(roughnessPath))
            previewMaterial.SetFloat("_Glossiness", 1f - AverageR(LoadTex(roughnessPath)));

        if (FileReady(metallicPath))
            previewMaterial.SetFloat("_Metallic", AverageR(LoadTex(metallicPath)));
    }

    IEnumerator CaptureSequence()
    {
        yield return null;

        string outDir = string.IsNullOrEmpty(outputPath)
            ? Path.Combine(RepoRoot, "docs", "images", "validation")
            : outputPath;

        Directory.CreateDirectory(outDir);

        foreach (var c in Conditions)
        {
            validationLight.color = c.color;
            validationLight.intensity = c.intensity;
            validationLight.transform.eulerAngles = c.euler;

            yield return new WaitForEndOfFrame();

            string file = Path.Combine(outDir, $"material_validation_{c.name}.png");
            ScreenCapture.CaptureScreenshot(file);
            Debug.Log($"[MaterialValidator] Captured: {file}");

            yield return new WaitForSeconds(1f);
        }

        Debug.Log($"[MaterialValidator] Done. All captures saved to: {outDir}");
    }

    static Texture2D LoadTex(string path)
    {
        Texture2D tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        tex.LoadImage(File.ReadAllBytes(path));
        return tex;
    }

    static float AverageR(Texture2D tex)
    {
        Color32[] px = tex.GetPixels32();
        float sum = 0f;
        foreach (var p in px) sum += p.r;
        return sum / (px.Length * 255f);
    }

    static bool FileReady(string path) =>
        !string.IsNullOrEmpty(path) && File.Exists(path);

    private struct LightingCondition
    {
        public string name;
        public Color color;
        public float intensity;
        public Vector3 euler;

        public LightingCondition(string name, Color color, float intensity, Vector3 euler)
        {
            this.name = name;
            this.color = color;
            this.intensity = intensity;
            this.euler = euler;
        }
    }
}
