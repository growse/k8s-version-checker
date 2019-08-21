# About

`k8s-version-checker` is a simple script that looks for updated tags of image digests on a kubernetes (k8s) cluster.

# Running `k8s-version-checker`

`k8s-version-checker` can either be run locally where a `~/.kube/config` environment is available, or it can be run on a k8s cluster itself. If the latter, then a common deployment pattern is to use a `CronJob` to scheulde the execution periodically.

An example manifest with the relevent roles and permissions is present in `k8s-cron-job.yml`.

    Usage: version-checker [OPTIONS]
    
      Checks a kubernetes cluster to see if any running pods, cron jobs or
      deployments have updated image tags or image digests on their
      repositories.
    
      Can be run either external to a cluster (requires `~/.kube/config` to be
      setup correctly) or within a cluster as a pod. In the latter case,
      notifications about available updates will be posted to a webhook.
    
      This script can be figured using annotations on the pods themselves. Pods
      can be ignored with:
    
      `growse.com/version-checker-ignore: "true"`
    
      And can have their elgiable tags scroped with a regular expression:
    
      `growse.com/version-checker-tag-regex: "^v.+?-amd64$"
    
    Options:
      --debug           Enable debug logging
      --namespace TEXT  Only look in this namespace
      -h, --help        Show this message and exit.


# Testing

`pytest` is used, and the `pytest-cov` plugin should be available:

    pytest --cov=version_checker tests/

# TODO

- [ ] Notifications. Somehow. K8s events?
- [x] Inspect cron job resources
- [ ] Store state of notifications between invocations
- [ ] Tests for version pattern matching