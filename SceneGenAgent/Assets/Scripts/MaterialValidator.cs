using UnityEngine;
using System.Collections;
using System.IO;

// Step 1.6 — PBR Material Validation
// Loads generated texture set from pipeline/output, applies to a preview plane,
// renders under 3 lighting conditions (neutral / warm / cool), captures screenshots.
//
// Usage:
//   1. Attach this script to an empty GameObject in Unity.
//   2. Set PBR texture paths in the Inspector (albedoPath, normalPath, etc.).
//   3. Press Play — screenshots auto-saved to outputPath.
public class MaterialValidator : MonoBehaviour
{
    [Header("PBR Texture Paths (absolute)")]
    public string albedoPath;
    public string normalPath;
    public string roughnessPath;
    public string metallicPath;

    [Header("Output")]
    public string outputPath = @"C:\CurrentWorks\scene-gen-agent\docs\images\validation";

    private Light validationLight;
    private Material previewMaterial;

    // 3 lighting conditions: name / light color / intensity / directional angle
    private static readonly LightingCondition[] Conditions = {
        new LightingCondition("neutral", new Color(1.00f, 1.00f, 1.00f), 1.0f, new Vector3(50f, -30f, 0f)),
        new LightingCondition("warm",    new Color(1.00f, 0.82f, 0.55f), 1.3f, new Vector3(30f,  45f, 0f)),
        new LightingCondition("cool",    new Color(0.65f, 0.82f, 1.00f), 0.9f, new Vector3(65f, -60f, 0f)),
    };

    void Start()
    {
        BuildScene();
        StartCoroutine(CaptureSequence());
    }

    void BuildScene()
    {
        // Preview plane — horizontal, camera looks down at an angle
        GameObject plane = GameObject.CreatePrimitive(PrimitiveType.Plane);
        plane.name = "PBR_Preview";
        plane.transform.position = Vector3.zero;
        plane.transform.localScale = new Vector3(0.5f, 1f, 0.5f);

        previewMaterial = new Material(Shader.Find("Standard"));
        ApplyPBRTextures();
        plane.GetComponent<Renderer>().material = previewMaterial;

        // Camera angle: look down at 50° to show surface texture and lighting clearly
        Camera cam = Camera.main;
        if (cam != null)
        {
            cam.transform.position = new Vector3(0f, 3f, -2.5f);
            cam.transform.rotation = Quaternion.Euler(50f, 0f, 0f);
            cam.backgroundColor = new Color(0.1f, 0.1f, 0.1f);
            cam.clearFlags = CameraClearFlags.SolidColor;
        }

        // Single directional light — color/intensity/angle set per capture
        GameObject lightGo = new GameObject("ValidationLight");
        validationLight = lightGo.AddComponent<Light>();
        validationLight.type = LightType.Directional;

        // Low ambient so the directional light color reads clearly
        RenderSettings.ambientLight = new Color(0.12f, 0.12f, 0.12f);
    }

    void ApplyPBRTextures()
    {
        // Albedo → _MainTex
        if (FileReady(albedoPath))
            previewMaterial.mainTexture = LoadTex(albedoPath);

        // Normal map → _BumpMap
        // Runtime-loaded PNGs: Standard shader reads the RGB channels directly as XYZ normals.
        if (FileReady(normalPath))
        {
            previewMaterial.SetTexture("_BumpMap", LoadTex(normalPath));
            previewMaterial.EnableKeyword("_NORMALMAP");
            previewMaterial.SetFloat("_BumpScale", 1.0f);
        }

        // Roughness map (grayscale flat) → sample average → convert to smoothness (1 - r)
        if (FileReady(roughnessPath))
        {
            float roughness = AverageR(LoadTex(roughnessPath));
            previewMaterial.SetFloat("_Glossiness", 1f - roughness);
        }

        // Metallic map (grayscale flat) → sample average → _Metallic
        if (FileReady(metallicPath))
        {
            float metallic = AverageR(LoadTex(metallicPath));
            previewMaterial.SetFloat("_Metallic", metallic);
        }
    }

    IEnumerator CaptureSequence()
    {
        yield return null; // let scene initialize

        Directory.CreateDirectory(outputPath);

        foreach (var c in Conditions)
        {
            validationLight.color = c.color;
            validationLight.intensity = c.intensity;
            validationLight.transform.eulerAngles = c.euler;

            yield return new WaitForEndOfFrame();

            string file = Path.Combine(outputPath, $"material_validation_{c.name}.png");
            ScreenCapture.CaptureScreenshot(file);
            Debug.Log($"[MaterialValidator] Captured: {file}");

            yield return new WaitForSeconds(1f); // gap between captures
        }

        Debug.Log("[MaterialValidator] All 3 captures complete.");
    }

    static Texture2D LoadTex(string path)
    {
        Texture2D tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        tex.LoadImage(File.ReadAllBytes(path));
        return tex;
    }

    // Sample average R channel (grayscale maps store value in R)
    static float AverageR(Texture2D tex)
    {
        Color32[] px = tex.GetPixels32();
        float sum = 0f;
        foreach (var p in px) sum += p.r;
        return sum / (px.Length * 255f);
    }

    static bool FileReady(string path) =>
        !string.IsNullOrEmpty(path) && File.Exists(path);

    // Plain struct to hold a lighting condition — avoids ValueTuple deconstruct issues in older Unity
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
