extern crate k8s_version_checker;

use std::error;

use futures::TryFutureExt;
use kube::client::APIClient;
use kube::config;

#[tokio::main]
pub async fn main() -> Result<(), Box<dyn error::Error>> {
    let namespace = std::env::var("NAMESPACE").unwrap_or("default".into());
    let client = get_k8s_client()
        .and_then(|client| k8s_version_checker::get_top_level_k8s_resources(client, &namespace));

    match client.await {
        Ok(_) => println!("Yay"),
        Err(e) => println!("Error: {}", e),
    }
    Ok(())
}

async fn get_k8s_client() -> Result<APIClient, Box<dyn error::Error>> {
    return config::load_kube_config()
        .await
        .map_err(|e| e.into())
        .map(|config| APIClient::new(config));
}



