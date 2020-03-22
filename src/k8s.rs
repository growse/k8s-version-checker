use std::error;

use k8s_openapi::api::apps::v1::Deployment;
use kube::api::{Api, ListParams};
use kube::client::APIClient;
use kube::config;

pub async fn get_k8s_client() -> Result<APIClient, Box<dyn error::Error>> {
    config::load_kube_config()
        .await
        .map_err(|e| e.into())
        .map(|config| APIClient::new(config))
}


async fn get_top_level_k8s_deployments(client: APIClient, namespace: &str) -> Result<Vec<String>, Box<dyn error::Error>> {
    let deployments_api: Api<Deployment> = Api::namespaced(client, &namespace);
    let toot = deployments_api
        .list(&ListParams::default())
        .await
        .map(|deployment_list_response| deployment_list_response.items)
        .map(|deployments| deployments
            .into_iter()
            .filter(|thing|
                thing
                    .metadata
                    .as_ref()
                    .map(|metadata| metadata.owner_references.as_ref())
                    .flatten()
                    .map_or(true, |owners| owners.is_empty())
            ).flat_map(|deployment|
            deployment
                .spec
                .map(|deployment_spec| deployment_spec.template)
                .map(|pod_template_spec| pod_template_spec.spec)
                .flatten()
                .map(|pod_spec| pod_spec.containers)
                .map(|container|
                    container
                        .into_iter()
                        .map(|container| container.image).collect()
                ))

            .into_iter()
            .filter_map(|x| x)
            .collect()
        );
    toot.map_err(|e| e.into())
}

pub async fn get_top_level_k8s_resources(client: APIClient, namespace: &str) -> Result<Vec<String>, Box<dyn error::Error>> {
    get_top_level_k8s_deployments(client.clone(), namespace).await
}
