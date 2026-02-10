using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

// 1. ESTA ES LA CLASE DE DATOS: Debe ir afuera de la otra clase.
// Sus nombres deben ser EXACTOS a como los pusimos en Python (physio_model.py)
[System.Serializable]
public class HeartMetrics
{
    public float bpm;
    public float trimp;
    public float hrr;     // Métrica de recuperación solicitada en el PDF
    public string zone;
    public string color;  // El color en Hexadecimal que manda Python
}

public class HeartConnector : MonoBehaviour
{
    [Header("Configuración de API")]
    public string apiUrl = "http://localhost:8000/metrics";
    public float updateInterval = 0.5f; 

    [Header("Visualización")]
    public float scaleFactor = 0.2f; // Qué tanto se infla la esfera
    private Vector3 initialScale;
    private float currentBPM = 60f;
    private Renderer heartRenderer; // Referencia al color de la esfera

    void Start()
    {
        initialScale = transform.localScale;
        heartRenderer = GetComponent<Renderer>();
        
        // Iniciamos el bucle de petición de datos
        StartCoroutine(GetHeartDataLoop());
    }

    void Update()
    {
        // 2. EL LATIDO FÍSICO:
        // Usamos currentBPM que se actualiza desde Python
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
                    // 3. LEER EL JSON:
                    string json = webRequest.downloadHandler.text;
                    HeartMetrics metrics = JsonUtility.FromJson<HeartMetrics>(json);
                    
                    // Actualizamos variables locales con lo que dijo Python
                    currentBPM = metrics.bpm;

                    // 4. CAMBIO DE COLOR DINÁMICO:
                    // Usamos el color hexadecimal que configuramos en Python (hexadecimal)
                    Color zoneColor;
                    if (ColorUtility.TryParseHtmlString(metrics.color, out zoneColor))
                    {
                        heartRenderer.material.color = zoneColor;
                    }

                    Debug.Log($"Corazón: {metrics.bpm} BPM | Zona: {metrics.zone} | Recup: {metrics.hrr}");
                }
                else
                {
                    Debug.LogWarning("Servidor Python no responde. ¿Docker está UP?");
                }
            }
            yield return new WaitForSeconds(updateInterval);
        }
    }
}