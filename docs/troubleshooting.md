# Troubleshooting

### CI issues
1. While installing the framework from Git instead of PyPI, you may encounter the following error:
    ```
    HangupExceptionThe remote server unexpectedly closed the connection
    ....
    The following error occurred when trying to handle this error:
    HangupException
    
    git@github.com: Permission denied (publickey)
    ....
    ```
    
    To resolve that, please install the package using PyPI. If that is not possible, and you use `addonfactory-workflow-addon-release`, please make sure you're using at least `v4.19` version.
2. If you encounter the following error:
    ```
    Existing splunk client (tests/ucc_modinput_functional/splunk/client/_managed_client.py) is outdated. Use --force-splunk-client-overwritten to overwrite it or --skip-splunk-client-check if you want to post.
    ```
    Please make sure to synchronize your output folder with the latest TA dev state and regenerate `_managed_client.py` by running 

    ```bash
   ucc-gen build 
   ucc-test-modinput gen --force-splunk-client-overwritten
   ```
   and add the `_managed_client.py` file to your commit.