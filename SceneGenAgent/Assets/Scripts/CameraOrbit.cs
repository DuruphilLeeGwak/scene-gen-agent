using UnityEngine;
using System.Collections;
using System.IO;

public class CameraOrbit : MonoBehaviour
{
    [Header("Orbit Settings")]
    public float orbitRadius = 6f;
    public float orbitHeight = 3f;
    public float orbitSpeed = 60f;

    [Header("Recording Settings")]
    public int variantCount = 5;
    public float orbitDuration = 6f;
    public string outputPath = @"C:\CurrentWorks\scene-gen-agent\output\recording\";

    private SceneLoader sceneLoader;
    private int currentVariant = 0;
    private int frameIndex = 0;
    private Camera cam; // 추가

    void Start()
    {
        sceneLoader = GetComponent<SceneLoader>();
        cam = GetComponentInChildren<Camera>(); // 추가
        if (cam == null) cam = Camera.main;     // 추가
        Camera.main.clearFlags = CameraClearFlags.SolidColor;
        Camera.main.backgroundColor = new Color(0.05f, 0.05f, 0.05f);

        Directory.CreateDirectory(outputPath);
        StartCoroutine(RecordAllVariants());
    }

    IEnumerator RecordAllVariants()
    {
        for (int i = 0; i < variantCount; i++)
        {
            Debug.Log("Recording variant " + i);

            currentVariant = i;
            frameIndex = 0;

            sceneLoader.LoadScene();
            ApplyVariation(i);

            yield return new WaitForEndOfFrame();

            yield return StartCoroutine(OrbitAndCapture());

            Debug.Log("Variant " + i + " done!");
            yield return new WaitForSeconds(0.3f);
        }

        Debug.Log("All variants recorded!");
    }

    IEnumerator OrbitAndCapture()
    {
        float currentAngle = 0f;
        float elapsed = 0f;

        while (elapsed < orbitDuration)
        {
            currentAngle += orbitSpeed * Time.deltaTime;
            float rad = currentAngle * Mathf.Deg2Rad;

            Vector3 offset = new Vector3(
                Mathf.Sin(rad) * orbitRadius,
                orbitHeight,
                Mathf.Cos(rad) * orbitRadius
            );

            Vector3 center = new Vector3(0f, 0.5f, 0f);
            cam.transform.position = center + offset;
            cam.transform.LookAt(center);

            yield return new WaitForEndOfFrame();

            string filename = outputPath
                + "v" + currentVariant.ToString("D2")
                + "_f" + frameIndex.ToString("D4")
                + ".png";
            ScreenCapture.CaptureScreenshot(filename);

            frameIndex++;
            elapsed += Time.deltaTime;
        }
    }

    void ApplyVariation(int seed)
    {
        Random.InitState(seed * 1000);

        foreach (Transform child in transform)
        {
            if (child.GetComponent<Light>() != null) continue;
            if (child.name == "floor") continue;

            Vector3 posOffset = new Vector3(
                Random.Range(-1f, 1f),
                0f,
                Random.Range(-1f, 1f)
            );
            child.position += posOffset;

            float scaleMultiplier = Random.Range(0.7f, 1.3f);
            child.localScale *= scaleMultiplier;

            Renderer renderer = child.GetComponent<Renderer>();
            if (renderer != null)
            {
                Color originalColor = renderer.material.color;
                renderer.material.color = new Color(
                    Mathf.Clamp01(originalColor.r + Random.Range(-0.2f, 0.2f)),
                    Mathf.Clamp01(originalColor.g + Random.Range(-0.2f, 0.2f)),
                    Mathf.Clamp01(originalColor.b + Random.Range(-0.2f, 0.2f))
                );
            }
        }
    }
}