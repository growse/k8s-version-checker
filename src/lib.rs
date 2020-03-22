pub mod k8s;
pub mod registry;


#[cfg(test)]
mod tests {
    use parameterized::parameterized;

    use crate::registry::get_registry_host_and_image;

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