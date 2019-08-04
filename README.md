
# Running

    python -m version_checker  --help
    Usage: version-checker [OPTIONS]
    
      Checks a kubernetes cluster to see if any running pods, cron jobs or
      deployments have updated image tags or image digests on their
      repositories.
    
      Can be run either external to a cluster (requires `~/.kube/config` to be
      setup correctly) or within a cluster as a pod. In the latter case,
      notifications about available updates will be posted to a webhook.
    
      This script can be figured using annotations on the pods themselves. Pods
      can be ignored with:
    
      `growse.com/k8s-version-checker-ignore: "true"`
    
      And can have their elgiable tags scroped with a regular expression:
    
      `growse.com/k8s-version-checker-tag-regex: "^v.+?-amd64$"
    
    Options:
      --debug               Enable debug logging
      --image-pattern TEXT  Only look at images matchin this pattern
      -h, --help            Show this message and exit.


# Testing

`pytest` is used, and the `pytest-cov` plugin should be available:

    pytest --cov=version_checker tests/
