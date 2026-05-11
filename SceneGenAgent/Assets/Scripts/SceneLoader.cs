using UnityEngine;
using System.IO;
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

    void Start()
    {
        LoadScene();
    }

    public void LoadScene()
    {
        // 기존 오브젝트 삭제 (카메라 제외)
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

        // 환경 조명
        RenderSettings.ambientIntensity = data.environment.ambient_intensity;

        // 오브젝트 생성
        foreach (var obj in data.objects)
            SpawnObject(obj);

        /// 조명 생성
        foreach (var light in data.lights)
            SpawnLight(light);

        // 바닥 생성
        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "floor";
        floor.transform.SetParent(transform);
        floor.transform.position = Vector3.zero;
        floor.transform.localScale = new Vector3(3f, 1f, 3f);
        Renderer floorRenderer = floor.GetComponent<Renderer>();
        floorRenderer.material = new Material(Shader.Find("Standard"));
        floorRenderer.material.color = new Color(0.3f, 0.3f, 0.3f);

        
    
    }

    void SpawnObject(SceneObject obj)
    {
        GameObject go = null;

        switch (obj.type.ToLower())
        {
            case "box":
                go = GameObject.CreatePrimitive(PrimitiveType.Cube);
                break;
            case "sphere":
                go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                break;
            case "cylinder":
                go = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                break;
            case "capsule":
                go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                break;
            default:
                go = GameObject.CreatePrimitive(PrimitiveType.Cube);
                break;
        }

        go.name = obj.id;
        go.transform.SetParent(transform);
        go.transform.position = new Vector3(obj.position.x, obj.position.y, obj.position.z);
        go.transform.localScale = new Vector3(obj.scale.x, obj.scale.y, obj.scale.z);

        // 색상 적용
        Renderer renderer = go.GetComponent<Renderer>();
        renderer.material = new Material(Shader.Find("Standard"));
        renderer.material.color = new Color(obj.color.r, obj.color.g, obj.color.b);

        go.transform.SetParent(transform);
    }

    void SpawnLight(SceneLight lightData)
    {
        GameObject go = new GameObject(lightData.id);
        go.transform.SetParent(transform);
        go.transform.position = new Vector3(lightData.position.x, lightData.position.y, lightData.position.z);

        Light light = go.AddComponent<Light>();
        light.intensity = lightData.intensity;
        light.color = new Color(lightData.color.r, lightData.color.g, lightData.color.b);
        light.range = lightData.range;

        switch (lightData.type.ToLower())
        {
            case "spot":
                light.type = LightType.Spot;
                light.spotAngle = 60f;
                // 스팟라이트는 아래를 향하게
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