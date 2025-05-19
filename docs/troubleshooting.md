# Troubleshooting

### CI issues
While installing the framework from Git instead of PyPI, you may encounter the following error:
```
HangupExceptionThe remote server unexpectedly closed the connection
....
The following error occurred when trying to handle this error:
HangupException

git@github.com: Permission denied (publickey)
....
```

To resolve that, please install the package using PyPI. If that is not possible, and you use `addonfactory-workflow-addon-release`, please make sure you're using at least `v4.19` version.