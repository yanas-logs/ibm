use dioxus::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct MantraResponse {
    pub mode: String,
    pub intensity: f32,
    pub suggestion: String,
}

#[server]
pub async fn echo(input: String) -> Result<String, ServerFnError> {
    Ok(input)
}

#[server]
pub async fn get_mantra_atmosphere(gesture_data: String) -> Result<MantraResponse, ServerFnError> {
    let api_key =
        std::env::var("WATSONX_API_KEY").map_err(|_| ServerFnError::new("API Key not found"))?;

    let client = reqwest::Client::new();
    let url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29";

    let response = client.post(url)
        .bearer_auth(api_key)
        .json(&serde_json::json!({
            "input": format!("Analyze this movement and determine the atmosphere of the Mantra (Arcane/Zen).: {}", gesture_data),
            "parameters": { 
                "decoding_method": "sample", 
                "max_new_tokens": 50 
            }
        }))
        .send()
        .await
        .map_err(|e| ServerFnError::new(e.to_string()))?;

    let res = response
        .json::<MantraResponse>()
        .await
        .map_err(|e| ServerFnError::new(format!("Parsing error: {}", e)))?;
    Ok(res)
}
