extern crate k8s_version_checker;

use std::error;

use futures::TryFutureExt;
use kube::client::APIClient;
use kube::config;
use std::convert::TryInto;
use futures::future::AndThen;
use futures::executor::block_on;

#[tokio::main]
async fn main() {
    let namespace = std::env::var("NAMESPACE").unwrap_or("default".into());
    fn curried(client: APIClient) -> impl Fn(&str) -> Result<String, Box<dyn error::Error>> {
        k8s_version_checker::get_top_level_k8s_resources(client, &namespace)
    }

    match get_k8s_client()
        .and_then(curried)
        .await
    {
        Ok(thing) => println!("nope"),
        Err(e) => { println!("e") }
    }
}

async fn get_k8s_client() -> Result<APIClient, Box<dyn error::Error>> {
    config::load_kube_config()
        .await
        .map_err(|e| e.into())
        .map(|config| APIClient::new(config))
}



