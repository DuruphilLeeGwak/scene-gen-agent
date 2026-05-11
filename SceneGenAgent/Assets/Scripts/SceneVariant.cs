using UnityEngine;
using System.IO;
using System.Collections;

public class SceneVariant : MonoBehaviour
{
    public string jsonPath = @"C:\CurrentWorks\scene-gen-agent\output\scene.json";
    public string screenshotPath = @"C:\CurrentWorks\scene-gen-agent\output\screenshots\";
    public int variantCount = 5;

    private SceneLoader sceneLoader;

    void Start()
    {
        sceneLoader = GetComponent<SceneLoader>();
        StartCoroutine(GenerateVariants());
    }

    IEnumerator GenerateVariants()
    {
        // 스크린샷 폴더 생성
        Directory.CreateDirectory(screenshotPath);

        for (int i = 0; i < variantCount; i++)
        {
            // 씬 로드
            sceneLoader.LoadScene();

            // 시드 기반 랜덤 변형 적용
            ApplyVariation(i);

            // 한 프레임 대기 (렌더링 완료 후 스크린샷)
            yield return new WaitForEndOfFrame();

            // 스크린샷 저장
            string filename = screenshotPath + "variant_" + i.ToString("D2") + ".png";
            ScreenCapture.CaptureScreenshot(filename);
            Debug.Log("Screenshot saved: " + filename);

            // 다음 변형 전 잠깐 대기
            yield return new WaitForSeconds(0.5f);
        }

        Debug.Log("All " + variantCount + " variants generated!");
    }

    void ApplyVariation(int seed)
    {
        Random.InitState(seed * 1000);

        foreach (Transform child in transform)
        {
            // 조명, 바닥은 변형 제외
            if (child.GetComponent<Light>() != null) continue;
            if (child.name == "floor") continue;
            // 위치 랜덤 오프셋 (-1 ~ +1)
            Vector3 posOffset = new Vector3(
                Random.Range(-1f, 1f),
                0f,
                Random.Range(-1f, 1f)
            );
            child.position += posOffset;

            // 스케일 랜덤 변형 (0.7 ~ 1.3)
            float scaleMultiplier = Random.Range(0.7f, 1.3f);
            child.localScale *= scaleMultiplier;

            // 색상 랜덤 변형
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