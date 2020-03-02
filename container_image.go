package main

import (
	"fmt"
	"github.com/hashicorp/go-version"
	"strings"
)

type Image struct {
	Registry string
	Name     string
}

const defaultRegistryHost = "registry-1.docker.io"
const sep = "/"

func GetRegistryHostAndImage(definition string) Image {
	if !strings.Contains(definition, sep) {
		imageName := fmt.Sprintf("library/%v", definition)
		return Image{defaultRegistryHost, imageName}
	} else if strings.Count(definition, sep) == 2 ||
		(strings.Count(definition, sep) == 1 && strings.Contains(strings.Split(definition, sep)[0], ".")) {
		parts := strings.SplitN(definition, sep, 2)
		return Image{parts[0], parts[1]}
	} else {
		return Image{defaultRegistryHost, definition}
	}

}

func IsVersionedTag(tag string) bool {
	_, err := version.NewVersion(tag)
	return err == nil
}
