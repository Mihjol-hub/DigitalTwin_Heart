using UnityEngine;
using UnityEngine.Networking;
using System;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Net.WebSockets;
using System.Data.Common;

[System.Serializable]
public class HeartMetrics
{
    public float bpm;
    public string zone;
    public string color;
}

public class HeartConnector : MonoBehaviour
{
    [Header("Configuración de API")]
    public string wsUrl = "ws://127.0.0.1:8000/ws/metrics";
    public string postUrl = "http://127.0.0.1:8000/set_intensity";

    [Header("Visualización")]
    public float scaleFactor = 0.2f;
    private Vector3 initialScale;
    private float currentBPM = 60f;
    public Renderer heartRenderer;
    private Material heartMaterial;

    // WebSocket
    private ClientWebSocket ws;
    private CancellationTokenSource cts;
    private HeartMetrics latestMetrics = null;

    void Start()
    {
        initialScale = transform.localScale;
        TryInitializeRenderer();

        // Start the connection in real time
        ConnectWebSocket();
    }

    void Update()
    {
        // 1. UPDATE VARIABLES FROM WEBSOCKET (Main thread)
        if (latestMetrics != null && TryInitializeRenderer())
        {
            currentBPM = latestMetrics.bpm;
            Color zoneColor;
            if (ColorUtility.TryParseHtmlString(latestMetrics.color, out zoneColor))
            {
                heartMaterial.color = Color.Lerp(heartMaterial.color, zoneColor, Time.deltaTime * 5f);
            }
        }

        // 2. PHYSICAL BEAT ORGANIC
        float beatSpeed = currentBPM / 60f;
        float pulse = Mathf.PingPong(Time.time * beatSpeed * 2f, scaleFactor);
        transform.localScale = initialScale + new Vector3(pulse, pulse, pulse);
    }

    bool TryInitializeRenderer()
    {
        if (heartRenderer == null)
        {
            heartRenderer = GetComponent<Renderer>();
        }

        if (heartRenderer == null)
        {
            heartRenderer = GetComponentInChildren<Renderer>(true);
        }

        if (heartRenderer == null)
        {
            return false;
        }

        if (heartMaterial == null)
        {
            heartMaterial = heartRenderer.material;
        }

        return heartMaterial != null;
    }

    // WebSocket
    async void ConnectWebSocket()
    {
        ws = new ClientWebSocket();
        cts = new CancellationTokenSource();

        try
        {
            await ws.ConnectAsync(new Uri(wsUrl), cts.Token);
            Debug.Log("🔌 Connected to the Digital Twin Brain (WebSockets)!");
            ReceiveLoop();
        }
        catch (Exception e)
        {
            Debug.LogError("Error connecting to WebSocket. Is Docker on?: " + e.Message);
        }
    }

    // 📡 CONTINUOUS LISTENING LOOP
    async void ReceiveLoop()
    {
        byte[] buffer = new byte[1024];

        while (ws.State == WebSocketState.Open)
        {
            var result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), cts.Token);
            if (result.MessageType == WebSocketMessageType.Text)
            {
                string json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                // Parse JSON in a secondary thread and save it
                latestMetrics = JsonUtility.FromJson<HeartMetrics>(json);
            }
        }
    }

    // SEND INTENSITY TO BACKEND (Keep HTTP POST for this)
    public void OnIntensityChanged(float val)
    {
        StopCoroutine("SetIntensity"); 
        StartCoroutine(SetIntensity(val));
    }

    System.Collections.IEnumerator SetIntensity(float intensity)
    {
        string url = $"{postUrl}/{intensity.ToString("F2", System.Globalization.CultureInfo.InvariantCulture)}";
        using (UnityWebRequest www = UnityWebRequest.PostWwwForm(url, ""))
        {
            yield return www.SendWebRequest();
            if (www.result == UnityWebRequest.Result.Success)
                Debug.Log($"🔥 Intensity sent: {intensity}");
            else
                Debug.LogWarning("Failed to send intensity to Python." + www.error);
        }
    }

    // 🧹 CLEANUP WHEN CLOSING UNITY
    private void OnDestroy()
    {
        if (ws != null)
        {
            cts.Cancel();
            ws.Dispose();
            Debug.Log("Disconnecting WebSocket...");
        }
    }
}