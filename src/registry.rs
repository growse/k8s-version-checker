use std::error::Error;
use std::fmt;

#[derive(Eq, PartialEq, Debug)]
pub struct Image {
    pub(crate) registry: String,
    pub(crate) name: String,
}


#[derive(Eq, PartialEq, Debug)]
pub struct VersionedImage {
    pub(crate) image: Image,
    pub(crate) version: String,
}

pub fn get_latest_image_version(_image: Image) -> Option<String> {
    None
}

const DEFAULT_REGISTRY_HOST: &str = "registry-1.docker.io";

pub fn parse_image_definition(image_definition: &str) -> Result<VersionedImage, Box<dyn Error>> {
    let image_split: Vec<&str> = image_definition.splitn(2, ':').collect();
    let image_name = image_split[0];
    let version = image_split[1];
    match image_split.len() {
        2 => get_registry_host_and_image(image_name).map(|i| VersionedImage { image: i, version: version.to_string() }),
        _ => Err(ImageVersionParseError { image_version_definition: image_definition.to_string() }.into())
    }
}

pub fn get_registry_host_and_image(image_name: &str) -> Result<Image, Box<dyn Error>> {
    if image_name.matches("/").count() == 0 {
        Ok(Image { registry: DEFAULT_REGISTRY_HOST.to_string(), name: format!("library/{image_name}", image_name = image_name) })
    } else if image_name.matches("/").count() == 2 || (image_name.matches('/').count() == 1 && image_name.splitn(2, '/').nth(0).unwrap().contains(".")) {
        Ok(Image { registry: image_name.split('/').nth(0).unwrap().to_string(), name: image_name.splitn(2, "/").nth(1).unwrap().to_string() })
    } else if image_name.matches('/').count() == 1 {
        Ok(Image { registry: DEFAULT_REGISTRY_HOST.to_string(), name: image_name.to_string() })
    } else {
        Err(ImageParseError { image_definition: image_name.to_string() }.into())
    }
}

#[derive(Debug)]
struct ImageVersionParseError {
    image_version_definition: String
}

impl Error for ImageVersionParseError {}

impl fmt::Display for ImageVersionParseError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Unable to extract image and version from: {}", self.image_version_definition)
    }
}

#[derive(Debug)]
struct ImageParseError {
    image_definition: String
}

impl Error for ImageParseError {}

impl fmt::Display for ImageParseError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Invalid image name format: {}", self.image_definition)
    }
}
