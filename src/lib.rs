use std::error::Error;
use std::fmt;

use futures::{FutureExt, TryFutureExt};
use k8s_openapi::api::apps::v1::Deployment;
use k8s_openapi::api::core::v1::Pod;
use kube::api::{Api, ListParams};
use kube::client::APIClient;

#[derive(Eq, PartialEq, Debug)]
pub(crate) struct Image {
    pub(crate) registry: String,
    pub(crate) name: String,
}

pub async fn get_top_level_k8s_pods(client: APIClient, namespace: &str) -> Result<Vec<Pod>, Box<dyn Error>> {
    let pods: Api<Pod> = Api::namespaced(client, &namespace);
    pods
        .list(&ListParams::default())
        .await
        .map(|pod_list_response| pod_list_response.items)
        .map(|pods| pods
            .into_iter()
            .filter(|thing|
                thing
                    .metadata
                    .as_ref()
                    .unwrap()
                    .owner_references
                    .as_ref()
                    .unwrap()
                    .is_empty())
            .collect()
        )
        .map_err(|e| e.into())
}

pub async fn get_top_level_k8s_deployments(client: APIClient, namespace: &str) -> Result<Vec<Deployment>, Box<dyn Error>> {
    let deployments: Api<Deployment> = Api::namespaced(client, &namespace);
    deployments
        .list(&ListParams::default())
        .await
        .map(|deployment_list_response| deployment_list_response.items)
        .map(|deployments| deployments
            .into_iter()
            .filter(|thing|
                thing
                    .metadata
                    .as_ref()
                    .unwrap()
                    .owner_references
                    .as_ref()
                    .unwrap()
                    .is_empty())
            .collect()
        )
        .map_err(|e| e.into())
}

pub async fn get_top_level_k8s_resources(client: APIClient, namespace: &str) -> Result<String, Box<dyn Error>> {

    dbg!(get_top_level_k8s_deployments(client,namespace).await);
    Err(MyError::new("Not implemented").into())
}

const DEFAULT_REGISTRY_HOST: &str = "registry-1.docker.io";

pub(crate) fn get_registry_host_and_image(image_name: &str) -> Result<Image, String> {
    if image_name.matches("/").count() == 0 {
        Result::Ok(Image { registry: DEFAULT_REGISTRY_HOST.to_string(), name: format!("library/{image_name}", image_name = image_name) })
    } else if image_name.matches("/").count() == 2 || (image_name.matches('/').count() == 1 && image_name.splitn(2, '/').nth(0).unwrap().contains(".")) {
        Result::Ok(Image { registry: image_name.split('/').nth(0).unwrap().to_string(), name: image_name.splitn(2, "/").nth(1).unwrap().to_string() })
    } else if image_name.matches('/').count() == 1 {
        Result::Ok(Image { registry: DEFAULT_REGISTRY_HOST.to_string(), name: image_name.to_string() })
    } else {
        Result::Err(format!("Invalid image name format: {image_name}", image_name = image_name))
    }
}


#[derive(Debug)]
struct MyError {
    details: String
}

impl MyError {
    fn new(msg: &str) -> MyError {
        MyError { details: msg.to_string() }
    }
}

impl fmt::Display for MyError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.details)
    }
}

impl Error for MyError {
    fn description(&self) -> &str {
        &self.details
    }
}


#[cfg(test)]
mod tests {
    use parameterized::parameterized;

    use crate::get_registry_host_and_image;

    #[parameterized(image_name = {
    "postgresql", "test/image", "registry.example.com/repo/image", "k8s.gcr.io/etcd"
    }, expected = {
    ("registry-1.docker.io", "library/postgresql"), ("registry-1.docker.io", "test/image"), ("registry.example.com", "repo/image"), ("k8s.gcr.io", "etcd")
    })]
    fn do_a_thing(image_name: &str, expected: (&str, &str)) {
        assert!(get_registry_host_and_image(image_name).is_ok());
        assert_eq!(get_registry_host_and_image(image_name).ok().unwrap().registry, expected.0);
        assert_eq!(get_registry_host_and_image(image_name).ok().unwrap().name, expected.1);
    }
}