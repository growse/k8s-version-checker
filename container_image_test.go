package main

import (
	"github.com/stretchr/testify/assert"
	"testing"
)

func TestGetRegistryHostAndImage(t *testing.T) {
	parameters := []struct {
		input    string
		expected Image
	}{
		{"postgresql", Image{"registry-1.docker.io", "library/postgresql"}},
		{"org/image", Image{"registry-1.docker.io", "org/image"}},
		{"registry.example.com/repo/image", Image{"registry.example.com", "repo/image"}},
		{"k8s.gcr.io/etcd", Image{"k8s.gcr.io", "etcd"}},
	}
	for i := range parameters {
		actual := GetRegistryHostAndImage(parameters[i].input)
		assert.Equal(t, parameters[i].expected, actual)
	}
}

func TestIsVersionedTagForValidVersions(t *testing.T) {
	parameters := []struct {
		input string
	}{
		{"1"},
		{"v1"},
		{"1.2"},
		{"1.23.4"},
		{"v1.23.4"},
		{"1.23.4-5"},
		{"v1.23.4-5"},
		{"1.23.4-rc1"},
		{"v1.23.4-rc1"},
	}
	for i := range parameters {
		assert.True(t, IsVersionedTag(parameters[i].input))
	}
}

func TestIsVersionedTagForInValidVersions(t *testing.T) {
	parameters := []struct {
		input string
	}{
		{"latest"},
		{"dev"},
	}
	for i := range parameters {
		assert.False(t, IsVersionedTag(parameters[i].input))
	}
}
