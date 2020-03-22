extern crate k8s_version_checker;

use futures::TryFutureExt;

use k8s_version_checker::k8s::{get_k8s_client, get_top_level_k8s_resources};
use k8s_version_checker::registry::{parse_image_definition, VersionedImage};

#[tokio::main]
async fn main() {
    let namespace = std::env::var("NAMESPACE").unwrap_or("default".into());

    let toot = get_k8s_client()
        .and_then(|client| get_top_level_k8s_resources(client, &namespace))
        .await
        .map(|images| {
            images
                .iter()
                .map(|image_and_version| parse_image_definition(image_and_version))
                .filter_map(Result::ok)
                .collect::<Vec<VersionedImage>>()
        }
        );

    match toot {
        Ok(thing) => {
            dbg!(thing);
            ()
        }
        Err(e) => eprintln!("Yaaay {}", e)
    };
}




