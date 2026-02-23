use axum::{
    routing::post,
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tract_onnx::prelude::*;

#[derive(Deserialize)]
struct PatientData {
    bpm: f32,
    rmssd: f32,
}

#[derive(Serialize)]
struct PredictionResult {
    depth_score: f32,
    status: String,
}

struct AppState {
    model: RunnableModel<TypedFact, Box<dyn TypedOp>, Graph<TypedFact, Box<dyn TypedOp>>>,
}

#[tokio::main]
async fn main() {
    println!("🦀 Starting Clinical Microservice in Rust...");

    let model_path = "anesthesia_model.onnx";
    println!("📦 Loading AI brain: {}", model_path);
    
    let model = tract_onnx::onnx()
        .model_for_path(model_path).expect("❌ Error: No found the .onnx file")
    
        .with_input_fact(0, tract_onnx::prelude::InferenceFact::dt_shape(f32::datum_type(), tvec!(1, 2))).expect("Error definiendo el tamaño de entrada")
        .into_optimized().expect("Error optimizing")
        .into_runnable().expect("Error preparing execution");

    let shared_state = Arc::new(AppState { model });

    let app = Router::new()
        .route("/predict", post(predict_depth))
        .with_state(shared_state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    println!("🚀 Inference Engine running on http://0.0.0.0:8080/predict");
    
    axum::serve(listener, app).await.unwrap();
}

async fn predict_depth(
    axum::extract::State(state): axum::extract::State<Arc<AppState>>,
    Json(payload): Json<PatientData>,
) -> Json<PredictionResult> {
    
    let input_tensor = tensor2(&[[payload.bpm, payload.rmssd]]);
    let result = state.model.run(tvec!(input_tensor.into())).unwrap();
    
    let prediction = result[0].to_array_view::<f32>().unwrap();
    let depth_score = prediction[[0, 0]];
    
    let status = if depth_score > 70.0 {
        "Deep Sleep (Anesthetized)".to_string()
    } else if depth_score > 30.0 {
        "Light Sedation".to_string()
    } else {
        "Waking / Alert".to_string()
    };

    Json(PredictionResult {
        depth_score,
        status,
    })
}