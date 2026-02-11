using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using UnityEngine.UI;


[System.Serializable]
public class HeartMetrics
{
    public string time;   //  JSON FastAPI
    public float bpm;
    public float trimp;
    public float hrr;
    public string zone;
    public string color;
    public float intensity; // from Unity to Python
}

public class HeartConnector : MonoBehaviour
{
    [Header("Configuración de API")]
    public string apiUrl = "http://localhost:8000/metrics";
    public float updateInterval = 0.5f; 

    [Header("Visualización")]
    public float scaleFactor = 0.2f; // how much will the sphere grow with each heartbeat?
    private Vector3 initialScale;
    private float currentBPM = 60f;
    private Renderer heartRenderer; // Reference to the sphere's color

    void Start()
    {
        initialScale = transform.localScale;
        heartRenderer = GetComponent<Renderer>();
        
        // Start the data request loop
        StartCoroutine(GetHeartDataLoop());
    }

    void Update()
    {
        // 2. PHYSICAL BEAT:
        // use currentBPM which is updated from Python
        float beatSpeed = currentBPM / 60f; 
        float pulse = Mathf.PingPong(Time.time * beatSpeed * 2f, scaleFactor);
        transform.localScale = initialScale + new Vector3(pulse, pulse, pulse);
    }

    IEnumerator GetHeartDataLoop()
    {
        while (true)
        {
            using (UnityWebRequest webRequest = UnityWebRequest.Get(apiUrl))
            {
                yield return webRequest.SendWebRequest();

                if (webRequest.result == UnityWebRequest.Result.Success)
                {
                    // 3. READ THE JSON:
                    string json = webRequest.downloadHandler.text;
                    HeartMetrics metrics = JsonUtility.FromJson<HeartMetrics>(json);
                    
                    // Update local variables with data from Python
                    currentBPM = metrics.bpm;

                    // 4. DYNAMIC COLOR CHANGE:
                    // Use the hexadecimal color configured in Python
                    Color zoneColor;
                    if (ColorUtility.TryParseHtmlString(metrics.color, out zoneColor))
                    {
                        heartRenderer.material.color = zoneColor;
                    }

                    Debug.Log($"Heart: {metrics.bpm} BPM | Zone: {metrics.zone} | Recovery: {metrics.hrr}");
                }
                else
                {
                    Debug.LogWarning("Python server not responding. Is Docker UP?");
                }
            }
            yield return new WaitForSeconds(updateInterval);
        }
    }

    public void OnIntensityChanged(float  val)
    {
        StartCoroutine(SetIntensity(val));
    }

    IEnumerator SetIntensity(float intensity)
    
    {
    
        string postUrl = $"http://localhost:8000/set_intensity/{intensity}";
        using (UnityWebRequest www = UnityWebRequest.PostWwwForm(postUrl, ""))
        {
            yield return www.SendWebRequest();
            if (www.result == UnityWebRequest.Result.Success)
                Debug.Log($"🚀 Intensity sent: {intensity}");
        }
    }
    
}