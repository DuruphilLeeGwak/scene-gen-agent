using UnityEngine;
using System.IO;
using System.Linq;
using System.Collections.Generic;

[System.Serializable]
public class SceneColor { public float r, g, b; }

[System.Serializable]
public class SceneVector3 { public float x, y, z; }

[System.Serializable]
public class SceneObject
{
    public string id;
    public string type;
    public SceneVector3 position;
    public SceneVector3 scale;
    public SceneColor color;
    public string texture_id; // optional — LLM assigns which texture set to use ("001", "002", ...)
}

[System.Serializable]
public class SceneLight
{
    public string id;
    public string type;
    public SceneVector3 position;
    public float intensity;
    public SceneColor color;
    public float range;
}

[System.Serializable]
public class SceneEnvironment
{
    public string type;
    public float ambient_intensity;
}

[System.Serializable]
public class SceneData
{
    public string scene_id;
    public SceneEnvironment environment;
    public List<SceneObject> objects;
    public List<SceneLight> lights;
    public int variant_seed;
}

public class SceneLoader : MonoBehaviour
{
    public string jsonPath = @"C:\CurrentWorks\scene-gen-agent\output\scene.json";

    // Repo root = two levels above Assets/ (SceneGenAgent/Assets → SceneGenAgent → repo root)
    private string RepoRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));

    void Start()
    {
        LoadScene();
    }

    public void LoadScene()
    {
        foreach (Transform child in transform)
        {
            if (child.GetComponent<Camera>() != null) continue;
            Destroy(child.gameObject);
        }

        if (!File.Exists(jsonPath))
        {
            Debug.LogError("scene.json not found: " + jsonPath);
            return;
        }

        string json = File.ReadAllText(jsonPath);
        SceneData data = JsonUtility.FromJson<SceneData>(json);

        Debug.Log("Loaded scene: " + data.scene_id);

        RenderSettings.ambientIntensity = data.environment.ambient_intensity;

        foreach (var obj in data.objects)
            SpawnObject(obj);

        foreach (var light in data.lights)
            SpawnLight(light);

        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "floor";
        floor.transform.SetParent(transform);
        floor.transform.position = Vector3.zero;
        floor.transform.localScale = new Vector3(3f, 1f, 3f);
        floor.GetComponent<Renderer>().material = new Material(Shader.Find("Standard"))
        {
            color = new Color(0.3f, 0.3f, 0.3f)
        };
    }

    void SpawnObject(SceneObject obj)
    {
        GameObject go = obj.type.ToLower() switch
        {
            "box"      => GameObject.CreatePrimitive(PrimitiveType.Cube),
            "sphere"   => GameObject.CreatePrimitive(PrimitiveType.Sphere),
            "cylinder" => GameObject.CreatePrimitive(PrimitiveType.Cylinder),
            "capsule"  => GameObject.CreatePrimitive(PrimitiveType.Capsule),
            _          => GameObject.CreatePrimitive(PrimitiveType.Cube),
        };

        go.name = obj.id;
        go.transform.SetParent(transform);
        go.transform.position  = new Vector3(obj.position.x, obj.position.y, obj.position.z);
        go.transform.localScale = new Vector3(obj.scale.x,   obj.scale.y,   obj.scale.z);

        Renderer rend = go.GetComponent<Renderer>();

        // texture_id present → load PBR texture set; fallback → plain color
        if (!string.IsNullOrEmpty(obj.texture_id))
            rend.material = BuildPBRMaterial(obj.texture_id, obj.color);
        else
            rend.material = BuildColorMaterial(obj.color);
    }

    // Finds the latest pipeline/output subfolder and loads the PBR maps for a given texture_id
    Material BuildPBRMaterial(string textureId, SceneColor fallbackColor)
    {
        string textureFolder = FindLatestOutputFolder();
        if (textureFolder == null)
        {
            Debug.LogWarning($"[SceneLoader] pipeline/output not found — falling back to color for texture_id '{textureId}'");
            return BuildColorMaterial(fallbackColor);
        }

        Material mat = new Material(Shader.Find("Standard"));

        string albedoPath    = Path.Combine(textureFolder, $"{textureId}_albedo.png");
        string normalPath    = Path.Combine(textureFolder, $"{textureId}_normal.png");
        string roughnessPath = Path.Combine(textureFolder, $"{textureId}_roughness.png");
        string metallicPath  = Path.Combine(textureFolder, $"{textureId}_metallic.png");

        if (File.Exists(albedoPath))
            mat.mainTexture = LoadTex(albedoPath);

        if (File.Exists(normalPath))
        {
            mat.SetTexture("_BumpMap", LoadTex(normalPath));
            mat.EnableKeyword("_NORMALMAP");
            mat.SetFloat("_BumpScale", 1.0f);
        }

        if (File.Exists(roughnessPath))
            mat.SetFloat("_Glossiness", 1f - AverageR(LoadTex(roughnessPath)));

        if (File.Exists(metallicPath))
            mat.SetFloat("_Metallic", AverageR(LoadTex(metallicPath)));

        Debug.Log($"[SceneLoader] Applied PBR texture '{textureId}' to {(mat.mainTexture != null ? "ok" : "missing albedo")}");
        return mat;
    }

    Material BuildColorMaterial(SceneColor c)
    {
        var mat = new Material(Shader.Find("Standard"));
        if (c != null)
            mat.color = new Color(c.r, c.g, c.b);
        return mat;
    }

    // Returns path to the latest YYYY-MM-DD_<material> subfolder, or null
    string FindLatestOutputFolder()
    {
        string pipelineOutput = Path.Combine(RepoRoot, "pipeline", "output");
        if (!Directory.Exists(pipelineOutput)) return null;

        string[] dirs = Directory.GetDirectories(pipelineOutput);
        if (dirs.Length == 0) return null;

        System.Array.Sort(dirs);
        return dirs[dirs.Length - 1]; // last = lexicographically latest = most recent date
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

    void SpawnLight(SceneLight lightData)
    {
        GameObject go = new GameObject(lightData.id);
        go.transform.SetParent(transform);
        go.transform.position = new Vector3(lightData.position.x, lightData.position.y, lightData.position.z);

        Light light = go.AddComponent<Light>();
        light.intensity = lightData.intensity;
        light.color     = new Color(lightData.color.r, lightData.color.g, lightData.color.b);
        light.range     = lightData.range;

        switch (lightData.type.ToLower())
        {
            case "spot":
                light.type      = LightType.Spot;
                light.spotAngle = 60f;
                go.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                break;
            case "point":
                light.type = LightType.Point;
                break;
            case "directional":
                light.type = LightType.Directional;
                go.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
                break;
            default:
                light.type = LightType.Point;
                break;
        }
    }
}
