# Framework deep dive
*Not yet finished, writing is still in progress ...*

## Framework philosophy
This section explains the background why this framework was created, what it tries to solve and what ideas it implements

### Popular add-on test scenarios
Spunk technical add-on is an application which goal is to interact with vendor customer environment in order to pull required vendor specific data and then send it to Splunk environment to be ingested and saved in desired Splunk indexes. This makes functional testing of add-ons to stick to a couple of common test scenarios:

1. Test of Add-on configuration validators: 

- interact with add-on API endpoint trying to configure various add-on supported objects (inputs and supporting configuration files) using incorrect values

- expecting that corresponding API endpoint rejects these values with expected explanatory error message in response and proper error logged.

- Delete configuration and objects created for test from Splunk instance.

For example, test can try to configure add-on proxy configuration using unsupported port number and expect that proxy will not be configured and the endpoint responses with an error message clearly pointing to unsupported port number.

2. Data ingestion validation:

- interact with customer environment to apply configurations, create objects or reproduce user actions in order to recreate conditions making desired vendor specific data to appear and ready for pulling to Splunk.

- interact with add-on at Splunk instance to apply configurations and create objects in order engage required add-on modular input to ingest data created for it in customer environment.

- validate ingestion by interacting with Splunk services to makes sure that expected number of events of expected type have been ingested as well as make sure that add-on modular input did not log any error messages during ingestion process.

- Delete configuration and objects created for test from customer environment and Splunk instance.

For example, functional test may verify correct ingestion of data from AWS S3 bucket which may require to configure S3 bucket and upload a data file prepared for test, configure corresponding input the way it would point to correct resource at created S3 bucket, let this input to run and ingest expected data, execute Splunk searches to confirm the number and sourcetypes of ingested events are correct, execute Splunk searches to make sure input did not log any error messages during ingestion process.
### Test requirements
Based on the test scenarios and examples listed above it is clear that for each add-on functional test before actual verification developer should deal with preparing test requirements, i.e. creation of necessary resources at Splunk or vendor related environment - objects and configurations, possibly uploading some test data. Next step is to retrieve some of test environment state properties and only then do the actual checks by comparing retrieved parameters values with expectations. Another thing to take care is to remove prepared resources after the test completion or at the end of test session. There are even more topics to think about connected with test execution optimization: for example, if several test can safely reuse the same resource it would be better to preserve this resource to let it be reused instead of creating and deleting it several times for each tests; or what if several resources for a tests are independent then it would be faster to create them in parallel. Taking care about such improvements makes tests better but at the same time adds complexity and may make them less clear and straightforward and less maintainable. Unified functional test framework was developed with desire make it take care about all the mentioned improvements while hiding from developers all related complexity and giving clear and straightforward way to create test and describe test requirements. 
### Framework requirements
To address the challenges listed above, several core requirements have been developed to be implemented by the framework:

1. Framework should provide a declaration way of describing test requirements (resources required for tests) outside the test function body.

2. Test requirements should be provided in same area as the tests function they belong to and give clear understanding what resources are needed, and in what order they should be created. 

3. Test itself should be as small as possible and only contain as much code as needed for verifications (assert statements) and optionally the code to collect data needed for verifications.

4. Dependencies between resources should be declared as a flat list in contrast to recursive approach where code creating resource also creates all resources it depends on which increases code complexity and hides dependencies from developer potentially making the code difficult to understand and support.

5. Developer should be able to specify if some resources can be created in parallel.

6. Developer should be able to specify what resources can be created in advance and what should be created right before test execution.

7. Framework should understand lifetime of a resource and execute code removing the resource as soon as all tests using it are executed. Developer should have a way to alter default framework behavior for specific tests.

8. Developer should be able to specify conditions for certain resources that can be used by framework to confirm that this resource is created or to wait for this resource to be created during required time.

### Framework basic concepts
To address the above requirements framework introduces a concept of forges - reusable functions responsible for creation and optionally deletion of required resources. They are implemented by developer separately from tests and bound to test functions using 'bootstrap' or 'attach' decorators. The order in which forges are listed within decorators defines the dependencies between forges. In other words, forge declared earlier becomes a prerequisite for a forge declared later. As a result framework will make sure that dependent forge is executed after its dependency. If two or more forges do not depend on each other, they can be declared in the same "line" or block of forges which would tell framework to execute these forges in parallel if possible. 

Forges can accept data via function arguments. The values for those arguments can be defined by a user explicitly or via parametrized arguments when declaring a forge as test requirement. Another way for a forge to receive argument values is to collect them from test artifactory. Artifactory is an internal storage of key-value pairs maintained for each test function separately. The mapping of values from artifactory to forge arguments is done by framework automatically by arguments names. Forges can update artifactory values or create new ones through returned or yielded values. 

When forge function is assigned to a specific tests it will receive argument values specific for this test and may be the same or differ from other test. Depending on argument values the results of forge executions also can be the same or different. In some sense one can think about assigned forge as about a ```task``` that creates a resource or fulfills an action. Framework assumes that forge functions is not vulnerable to any side effect, which means that executing the same forge function with the same argument values should results in the same action taken or in the same resource created. Based on this, same forge executed twice with different argument values is treated by framework as two different ```tasks``` while when executed with the same argument values will be treated as the same ```task``` creating the same resource and by default framework will try to skip unnecessary executions. 

When assigning a forge to a test, one of two additional properties that developer can configuration is "probe". Probe property allows to attach a probe function that will be used by framework to make sure that action taken by forge indeed has expected result, i.e. a resource has been created or a specific configuration has been applied. Framework will be invoking probe function with certain interval until probe gets successful or time given for probe to success expires. Just like forges probe functions can access test artifactory variables via declared function arguments. Last boolean value returned by a probe will be added by framework to the test artifactory with the name of probe function as the property name so the test function will be able to verify if the probe was successful or exited because of timeout.

Scope is the second of the two arguments that forge can accept when assigned to a tests. Before forge function execution framework pays attention to forge function name, forge function arguments values and forge scope. If there several tests that have the same forge with the same scope assigned to them and those forges have the same call argument values, framework assumes it is the same forge (or forge represents the same task) dedicated to create the same resource and executes it only once. By default all forges have "session" scope which means this comparison will take place across all the executed tests.  Changing scope value at forge assignment to tests allows to narrow the scope of tests for which forge execution results may be reused, for example to all tests in the same module or to a single test. Note that as soon as the last test using forge is executed, framework invokes teardown code of the forge if such code was implemented by developer.

It is also important which of the two decorators are used to assign forge to a test. Bootstrap decorator assumes that forge should create resource before executing tests. All forges assigned to different tests taken as independent and executed in parallel - first go all forges at bootstrap list top, then all in the second place and so on. Attach decorator works differently - it invokes forges right before the test execution. Bootstrap is more preferable way to execute forges to achieve better tests execution times, but it requires from developer more efforts to make sure that forges of different tests do not compete for configuring the same resource. There are some cases where it's possible to avoid this competition, for example when dealing with global or single instance resources like testing different proxy configurations. In those cases it's important to apply each specific configuration right before execution of (i.e. specifically for) related test function and 'attach' decorator is the proper way to do this.

It is important to mention that framework also allows tests to receive (or subscribe for) test artifactory properties generated during forge executions just by using their names to test function argument list. This way forges and probes can prepare some useful values in test artifactory and let test to use them for necessary verifications. 

In some sense forges and pytest fixtures have a lot in common, however they are very different in one important way - the way of organizing dependencies between them. To make a fixture A to depend on results of fixture B, fixture B should be declared as argument of fixture A.  Implemented this way, the relationship between fixture A and fixture B are hardcoded and B cannot be replaced with another fixture that would generate expected output using different source data or algorithm. When fixture A is used in tests, its dependencies are hidden from developer, and to understand what fixture A does, developer should study its dependency B as well, and inside be he may discover other dependencies and so on. In big test projects relationship between fixtures can become pretty sophisticated. Forges dependencies, in contrast, are dynamic and rely on artifactory variables provided by dependency forges, that allows to recombine forges according to desired test scenario and taking into account arguments expected by the forge function and generated by it artifacts. When talking about declaring test dependencies, they all (test dependencies together with forges dependencies) are declared in a form of a flat list located right before test function that gives to developer a clear picture about test requirements, i.e. resources to be created for the test execution.

## Framework structure and entities
Framework is created as pytest plugin and relates on pytest mechanisms of tests execution. In addition framework collect information about required forges, tries to execute them optimally respecting defined dependencies and making sure that corresponding tests are not executed before all declared by developer requirements are met.

### Splunk client
Splunk client is a combination of two classes - client class, responsible for interactions with Splunk environment, and configuration class, responsible for providing necessary settings for client class to act and some test data and settings for forge, probe and test functions. This separation is chosen to make it possible to apply different configuration to the same client class and let it communicate with different Splunk instances or point to different test samples and so on. Using provided client and configuration classes framework creates a separate instance of client class for each test and make it available to forge, probe and test functions via internally supported function arguments.
#### Vendor client class
Splunk client class is supposed to implement methods providing access to Splunk and add-on specific API. This client class is what developer deals with through framework supported function argument ```splunk_client``` when implementing framework entities like forges, probes and tests themselves. Developer can use either default client class available out of the box or extend it with add-on API support as well as with custom methods to add support for Splunk related functionality not supported by the framework. Framework tries to save developers' efforts by automating the creation of splunk client class when developer executes framework ```init``` and ```gen``` commands. These commands use openapi.json file generated by UCC while building TA package to create swagger support classes for add-on API endpoints. Then, based on swagger classes, framework generates a new managed client class inherited from framework base client class. At the same time framework generates one more "developer facing" client class inherited from the managed client class. By doing this framework adds support for add-on API and also prepares area for developers' custom code extensions.

#### Splunk functionality supported out of the box.
- *splunk_client.instance_epoch_time()* - returns current time at splunk instance in epoch format

- *splunk_client.search(query)* - executes SPL search query at Splunk instance and returns result in SearchState class object (*splunk_add_on_ucc_modinput_test.common.splunk_instance.SearchState*)

- *splunk_client.create_index(name)* - creates Splunk index with a given name and returns *splunklib.Index* object.

- *splunk_client.default_index()* - returns default Splunk index name if framework configured to create one.

- *splunk_client.search_probe(probe_spl, verify_fn, timeout, interval, probe_name)* - probe generator function to simplify creation of framework probes based on Splunk searches.

- *splunk_client.repeat_search_until(spl, condition_fn, timeout, interval)* - methods execution Splunk search continuously in defined intervals until it gets expected result or reaches timeout.

- *splunk_client.instance_file_helper()* - Factory method for SplunkInstanceFileHelper, allowing to execute some file operations directly on Splunk host. Requires ```Splunk Add-on for Modinput Test``` to be installed on the Splunk host. May be used for creation and verification of file based checkpoints. 

- *splunk_client.app_file_helper()* - same as instance_file_helper except SplunkInstanceFileHelper (*splunk_add_on_ucc_modinput_test.functional.common.splunk_instance_file*) will treat provided file paths as relative to add-on root folder on Splunk host. Requires ```app_name``` property to be part of ```splunk_client``` configuration class,

#### Add-on API endpoint support
Each technical add-on creates an additional set of API endpoints responsible for add-on resources like inputs, configuration files and custom rest handlers. 
As mentioned earlier framework ```init``` and ```gen``` commands 

#### Client configuration class
Client configuration class is a separate class dedicated to collect all settings for client class. Framework contains implementation of the base configuration class to collect settings for base client class functionality. Developer has an option to extend it by inheriting a new class form base configuration class and adding new properties as well as redefine values or sources of default properties. Framework ```init``` command generates default client configuration class that looks like the following
```python
from splunk_add_on_ucc_modinput_test.functional.splunk import (
    SplunkConfigurationBase,
)
class Configuration(SplunkConfigurationBase):
    def customize_configuration(self) -> None:
        # to be implemented
        # self.encoded_prop = utils.get_from_environment_variable(
        #     "ENV_PROP_NAME1", string_function=utils.Base64.decode
        # )
        # self.not_encoded_prop = utils.get_from_environment_variable(
        #     "ENV_PROP_NAME2"
        # )
        pass
```
As seen from the example, developer has to overwrite ```customize_configuration``` method to add additional configuration properties. This method is called from class \_\_init\_\_ method and added to simplify defining of new configuration properties by avoiding overwriting  \_\_init\_\_ method itself that requires some specific arguments expected by framework. 

Collection of default framework properties is implemented through class methods listed below. If there is a need to alter values, sources or collection algorithms for some of these properties, corresponding methods should be overwritten.

- ```collect_host(cls) -> str | None``` - to collect Splunk host name. Default value source is environment variable MODINPUT_TEST_SPLUNK_HOST.

- ```collect_port(cls) -> str | None``` - to collect Splunk host port. Default value source is environment variable MODINPUT_TEST_SPLUNK_PORT.

- ```collect_username(cls) -> str | None``` - to collect Splunk user name. Default value source is environment variable MODINPUT_TEST_SPLUNK_USERNAME.

- ```collect_password(cls) -> str | None``` - to collect Splunk user password. Default value source is environment variable MODINPUT_TEST_SPLUNK_PASSWORD_BASE64.

- ```collect_splunk_dedicated_index(cls) -> str | None``` - to collect name of existing Splunk index. Default value source is environment variable MODINPUT_TEST_SPLUNK_DEDICATED_INDEX.

- ```collect_splunk_token(cls, is_optional: bool) -> str | None``` - to collect Splunk token. Default value source is environment variable MODINPUT_TEST_SPLUNK_TOKEN_BASE64.

- ```collect_acs_server(cls, is_optional: bool) -> str | None``` - to collect Splunk ACS service url. Default value source is environment variable MODINPUT_TEST_ACS_SERVER.

- ```collect_acs_stack(cls, is_optional: bool) -> str | None``` - to collect Splunk CS stack. Default value source is environment variable MODINPUT_TEST_ACS_STACK.

Note that ```is_optional``` is boolean argument tells method if property is treated as optional or mandatory. If property is mandatory and method fails to collect value it should log a critical error and raise SplunkClientConfigurationException exception (*splunk_add_on_ucc_modinput_test.common.utils*). 
```python
class Configuration(SplunkConfigurationBase):
    ...
    @classmethod
    def collect_host(cls) -> str | None:
        return <your code to provide the value>

    @classmethod
    def collect_acs_server(cls, is_optional: bool) -> str | None:
        try:
            return <your code to provide the value>
        except Exception:
            if is_optional:
                return None
            else:
                logger.critical("Your error message")
                raise SplunkClientConfigurationException()
```
Beside default framework properties, configuration class gives access to command argument values defined for pytest executions via properties: ```probe_invoke_interval```, ```probe_wait_timeout```, ```do_not_fail_with_teardown``` and so on. It's easy to guess any property name for any argument by removing from argument name leading dashes and replacing internal dashes with underscores, for example ```--bootstrap-wait-timeout``` argument name turns to ```bootstrap_wait_timeout``` property name.

### Splunk Client and configuration classes binding decorators
When custom Splunk client and configuration classes are implemented there is one more step to be done to let framework know about these classes and use them. This can be done by using one of the decorators: ```register_splunk_class``` or ```define_splunk_client_argument```. 

#### register_splunk_class(swagger_client, splunk_configuration_class)
This decorator should be applied to the Splunk client class created by a developer. It takes imported swagger client module as the first argument and binds it to client. Second argument is Splunk client configuration class implemented by developer. Decorator registers it in framework together with the Splunk client class. Usage of this decorator may look as the following
```python
import swagger_client

class Configuration(SplunkConfigurationBase):
    # your configuration class implementation

@register_splunk_class(swagger_client, Configuration)
class SplunkClient(AutogenSplunkClient):
    # code extending base Splunk client class
```
Having both classes registered, framework is capable to create instances of Splunk client classes with configuration class assigned to the instance and make it available via splunk_client builtin function argument in forges, probes and tests. 
```python
def my_forge(splunk_client: SplunkClient):
    splunk_client.some_splunk_client_method() # some splunk client class method (exact name depends on the class implementation)
```

The idea behind implementing client and configuration classes separately is to make it possible to use Splunk client class with different configurations. This may be useful to give tests access to several Splunk instances, for example, to execute comparative verifications of different Splunk and/or add-on versions. For this framework has another decorator that allows to register Splunk client class multiply times with different configuration classes.

#### define_splunk_client_argument(swagger_client, splunk_client_class, splunk_class_argument_name)
In contrast to ```register_splunk_class```, this decorator must be applied to a configuration class. It takes imported swagger client module as the first argument and binds it to client class specified in the second decorator argument. Last decorator argument is optional and allows to define new builtin framework argument name for the pair of client and configuration classes. By default this argument has value 'splunk_client' so leaving it unspecified allows to overwrite binding to default builtin argument - when used this way both decorators work identically. However, defining different value will create a new builtin variable for specified combination of splunk client and configuration classes. Note that ```splunk_class_argument_name``` value when specified should comply with python rules of variable naming.
```python
import swagger_client

class SplunkClient(AutogenSplunkClient):
    # code extending base Splunk client class

@splunk_class_argument_name(swagger_client, SplunkClient)
class ConfigurationSplunk9(SplunkConfigurationBase):
    def customize_configuration(self) -> None:
        # define configuration to access Splunk v9 instance

@splunk_class_argument_name(swagger_client, SplunkClient, "splunk_client_v10")
class ConfigurationSplunk10(SplunkConfigurationBase):
    def customize_configuration(self) -> None:
        # define configuration to access Splunk v10 instance
```
In the example above ```ConfigurationSplunk9``` is registered without ```splunk_class_argument_name``` value specified, which means that framework will attach it and the client class to default ```splunk_client``` variable. For configuration class ```ConfigurationSplunk10``` ```splunk_class_argument_name``` is defined as *"splunk_client_v10"* which adds to framework new builtin variable *splunk_client_v10* and through it framework will make available a Splunk client class object created using ```ConfigurationSplunk10``` configuration. This way forges, probes and tests will be able to use both builtin variables if needed:
```python
def my_forge1(splunk_client: SplunkClient, splunk_client_v10: SplunkClient):
    splunk_client.some_splunk_client_method() # action at Splunk v9 instance
    splunk_client_v10.some_splunk_client_method() # same action at Splunk v10 instance

def my_forge2(splunk_client_v10: SplunkClient):
    splunk_client_v10.some_other_splunk_client_method() # another action at Splunk v10 instance
```

Note that if all client classes are registered with (bound to) custom internal variable names, internal variable 'splunk_client' will still be available and bound to default client and configuration classes with default methods and configuration properties defined.

### Vendor client
Vendor client is a combination of two classes - client class, responsible for interactions with vendor environment, and configuration class, responsible for providing necessary settings for client class to act and some test data and settings for forge, probe and test functions. This separation is chosen to make it possible to apply different configuration to the same client class and let it communicate with different vendor hosts or point to different test samples and so on. Using provided client and configuration classes framework creates a separate instance of client class for each test and make it available to forges, probes and tests via internally supported function arguments.

#### Vendor client class
Vendor client class should be created by developer to access vendor related environments like vendor cloud services, appliances or even user desktop monitored by vendor tools in order to trigger desired events. Similar to Splunk client class, this client class is what developer deals with through framework supported function argument ```vendor_client``` when implementing framework entities like forges, probes and tests themselves. Framework creates one instance of this class object per test. Having no knowledge about possible vendor environments framework has very little out of the box support for vendor class: base classes for vendor client and configuration. The approach remains similar to the one used for Splunk classes - both custom vendor client and configuration classes must be implemented from base classes offered by framework and then registered in the framework using ```register_vendor_class``` or ```define_vendor_client_argument``` decorators.

#### Configuration class
Similar to Splunk client configuration, Vendor client configuration class should be created to provide client class with required configuration. Framework binds client and configuration classes at runtime when creates client instances - one for each tests. Framework implements default vendor configuration class that provides access to the same set of command prompt arguments values specified for pytest execution. The only place to setup configuration properties is  ```customize_configuration``` method.  In contrast to Splunk client configuration class, it does not have any default vendor configuration properties, so there are no corresponding collection methods to overwrite. 
```python
from splunk_add_on_ucc_modinput_test.functional.vendor import (
    VendorConfigurationBase,
)
class Configuration(VendorConfigurationBase):
    def customize_configuration(self) -> None:
        # to be implemented
        # self.encoded_prop = utils.get_from_environment_variable(
        #     "ENV_PROP_NAME1", string_function=utils.Base64.decode
        # )
        # self.not_encoded_prop = utils.get_from_environment_variable(
        #     "ENV_PROP_NAME2"
        # )
        pass
```

### Client classes register decorators
When custom vendor client and configuration classes are implemented there is one more step to be done to let framework know about these classes and use them. Similar to Splunk classes, this can be done by using one of the decorators: ```register_vendor_class``` or ```define_vendor_client_argument```. They act the same way as Splunk client binding decorators except they do not require swagger module to be specified. 
```python
class Configuration(VendorConfigurationBase):
    # your configuration class implementation

@register_vendor_class(Configuration)
class VendorClient(VendorClientBase):
    # code extending base vendor client class
```
If tests suppose to communicate with different vendor appliances based on different API, framework supports having several different vendor classes bound to different configurations and assigned to different framework internal variable names. Scenario with same class bound to different configurations is also supported.
```python
class CiscoMeraki(VendorClientBase):
    # code extending base vendor client class

class CiscoWSA(VendorClientBase):
    # code extending base vendor client class

@vendor_class_argument_name(CiscoMeraki)
class Meraki132Configuration(VendorConfigurationBase, "meraki132_client"):
    def customize_configuration(self) -> None:
        # define configuration to access Cisco Meraki v1.32.0 appliance

@vendor_class_argument_name(CiscoMeraki)
class Meraki138Configuration(VendorConfigurationBase, "meraki138_client"):
    def customize_configuration(self) -> None:
        # define configuration to access Cisco Meraki v1.38.0 appliance

@vendor_class_argument_name(CiscoWSA, "wsa_client")
class WSAConfiguration(VendorConfigurationBase):
    def customize_configuration(self) -> None:
        # define configuration to access Cisco WSA appliance
```
In the examples above ```register_vendor_class```binds ```Configuration``` class to ```VendorClient``` class and makes client instances created by this pair available through ```vendor_client``` variable. Another example demonstrates ```vendor_class_argument_name``` decorator binding same client class ```CiscoMeraki``` to two different configurations classes```Meraki132Configuration``` and ```Meraki138Configuration``` that become available via ```meraki132_client``` and ```meraki138_client``` internal variables. As well as another binding of vendor client class ```CiscoWSA``` to it's own configuration class ```WSAConfiguration``` thad becomes available via ```wsa_client``` internal variable. This way forges, probes and tests will be able to use all four  builtin variables if needed:
```python
def my_forge1(meraki132_client: CiscoMeraki, meraki132_client: CiscoMeraki):
    meraki132_client.some_meraki_client_method() # action at Meraki appliance with v1.32.0
    meraki138_client.some_meraki_client_method() # same action at Meraki appliance with v1.32.0

def my_forge2(wsa_client: CiscoWSA):
    wsa_client.some_ciscowsa_client_method() # another action at Cisco WSA appliance
```
Note that iff all client classes registered with (bound to) custom internal variable name, internal variable 'vendor_client' will still be available and bound to default client and configuration classes with nor methods of configuration properties defined.

### Forges
As said earlier, forges are reusable functions responsible for creation and optionally deletion of resources required by tests. Like pytest fixtures forges can receive and return values and can be implemented as regular or generator function functions. If implemented as a generator function, the first yield will be separating setup and teardown code of the forge. In the following sections these topics explained in more details:

#### Forge function arguments
Forge function can receive any number of arguments. Before forge is executed, framework analyses argument names and tries to collect and provide values for forge execution by mapping its function argument names to different internal dictionaries like test artifactory, built in arguments created by framework and arguments explicitly specified by user at forge assignment stage.

##### Builtin arguments (reserved argument names)
Framework supports the following out of the box builtin properties that can be mapped by name to forge, probe and test function arguments:

- **splunk_client** - is an instance of splunk client class created by developer separately and registered in framework using corresponding decorator. Framework creates dedicated Splunk client class instance per test, initializing it using configuration class responsible for collecting necessary setting from different sources like environment variables, hardcoded values. There is a way to tell framework to create additional splunk client instance with different configuration that would be mapped it to desired function argument names, for example ```splunk_v10_client```. This may be useful when running tests at two or more splunk instances at the same time, for example, for Splunk or add-on upgrade tests. 

- **vendor_client** - similarly to splunk client class this one is an instance of vendor client class created by developer separately and registered in framework using corresponding decorator. Framework creates dedicated vendor client class instance per test, initializing it using configuration class responsible for collecting necessary setting from different sources like environment variables, hardcoded values. There is a way to tell framework to create additional vendor client instances with different configurations that would be mapped it to a desired function arguments names, for example vendor_client_appliance2.  This may be useful when running tests at two or more vendor instances at the same time, for example, when testing with two different vendor appliances or using instances running different versions of vendor software.

- **session_id** - is a unique identifier generated by framework for each test execution. It may be helpful to name reused resources to make sure that from test execution to execution those resources have unique names

- **test_id** - is a unique identifier generated by framework for each test during tests execution. It may be helpful to name resources dedicated to specific tests to avoid conflicts between different tests that other way may by chance get their resources named identically.

#### Forges as regular functions
Below is example of a forge implemented as a regular function
```python
def my_forge(splunk_client: SplunkClient, test_id: str, other_argument: str):
    input_name = f"my_input_{test_id}"
    splunk_client.create_some_input(input_name, other_argument) # some splunk client class method to create an input (exact name depends on the add-on)
    return input_name
```
When execution above forge for specific test framework will first collect all necessary forge arguments, i.e. splunk_client and test_id will be taken from builtin arguments, other_argument will be mapped either from test artifactory, explicitly defined arguments or from parametrized arguments. Next framework will execute forge with prepared arguments passing them to forge function as keyword arguments. When forge is executed framework gets its return value. If return value is not None framework will create new new key-value pair (artefact) in test artifacts with the name of forge function as key and returned value as a value. 

There is a way to let forge to control the name of created artifact as well as to tell framework to save several artifacts. For this instead of returning a single value forge can return a dictionary object with desired artifact names mapped to desired returning values. For example
```python
def my_forge(splunk_client: SplunkClient, test_id: str, other_argument: str):
    input_name = f"my_input_{test_id}"
    successful = splunk_client.create_some_input(input_name, other_argument)  # some splunk client class method to create an input
    return dict(  # it's recommended to use dict() constructor to makes sure that artifact name used is a valid python variable.
        input_name = input_name,
        successful = successful
    )
```
Above forge function returns dictionary telling framework to update artifactory with 'input_name' and 'successful' artifacts with corresponding values. Note, that if artifacts with the same names already exist the will be overwritten.
#### Forges as generators functions
Forges as generators are useful when resources created by forge need to be removed and forge should contain teardown code to fullfil deletion. In that case yield statement of generator function splits setup and teardown code like in the following example:
```python
def my_forge(splunk_client: SplunkClient, test_id: str, other_argument: str):
    input_name = f"my_input_{test_id}"
    successful = splunk_client.create_some_input(input_name, other_argument) # some splunk client class method to create an input
    yield dict(  # it's recommended to use dict() constructor to makes sure that artifact name used is a valid python variable.
        input_name = input_name,
        successful = successful
    )
    # teardown code starts here
    if successful:
        splunk_client.delete_some_input(input_name)
```
As seen from the example, now instead of returning values to be stored in artifactory they should be yielded. It is fine to use yield without any value - this will mean that forge does not intend to update or create any artifacts in test artifactory. Note that as soon as forge invokes yield operator function return value will be ignored ignored. However if forge function has yield statement but does not yield, framework will again rely on returned forge value. This allows framework to support scenarios with conditional teardown. In other words, when forge needs teardown code to be executed it yields, and if teardown is not needed it returns.
```python
def my_forge(splunk_client: SplunkClient, test_id: str, does_not_need_teardown: bool = False):
    input_name = f"my_input_{test_id}"
    successful = splunk_client.create_some_input(input_name, other_argument) # some splunk client class method to create an input
    artifacts = dict(  # it's recommended to use dict() constructor to makes sure that artifact name used is a valid python variable.
        input_name = input_name,
        successful = successful
    )
    if does_not_need_teardown:
        return artifacts
    
    yield artifacts:
    
    # teardown code starts here
    if successful:
        splunk_client.delete_some_input(input_name)
```
In above example forge skips (turns off) teardown block by using ```return``` statement when function argument ```does_not_need_teardown``` value is True.


### Artifactory
Artifactory is an internal storage of key-value pairs maintained for each test function separately. It stores variables added by framework based on analysis of values provided by forges and probes. Test artifactories maintained by the framework automatically based on results collected from forges and probes. As well framework handles mapping of artifacts to forge, probe and test function arguments. This means that as soon as a new key value pair is added to test artifactory it can be used by forge, probe and test functions just by declaring function arguments using names of stored artifacts. For example, let's have a forge that creates an S3 bucket at AWS environment and returns ```bucket_name``` artefact
```python
def create_s3_bucket(vendor_client: VendorClient, test_id: str, bucket_config: Dict[str, object]):
    bucket_name = f"my_s3_bucket_{test_id}"
    vendor_client.create_s3_bucket(bucket_name, bucket_config) # some vendor client class method to create an s3 bucket
    return dict(bucket_name=bucket_name)
```
Now we can create another forge that would upload files with required data samples to created s3 bucket and returns another artifact - ```successfully_uploaded```:
```python
def upload_s3_bucket_files(vendor_client: VendorClient, bucket_name: str, data_file_path: str):
    bucket_name = f"my_s3_bucket_{test_id}"
    success = vendor_client.upload_file_to_s3_bucket(bucket_name, data_file_path) # some vendor client class method to upload files to s3 bucket
    return dict(successfully_uploaded=success)
```
And finally we implement a test function that depends on the above two forges:
```python
@bootstrap(
    forge(create_s3_bucket, bucket_config={"some": "config"}),
    forge(upload_s3_bucket_files, data_file_path="some/file/path")
)
test_s3_bucket(vendor_client: VendorClient, bucket_name: str, successfully_uploaded: bool):
    assert list_of_bucket_resources is True
    list_of_bucket_resources = vendor_client.list_bucket_files(bucket_name)
    assert expected_resource_name in list_of_bucket_resources
```
Above demonstrates how ```bucket_name``` and ```successfully_uploaded``` artifacts returned by forges can be used in arguments of other forges and in test function arguments.
```bootstrap``` decorator and other control elements required to declare test dependencies are explained in next section. Note where values for other forge arguments are taken from:
- ```vendor_client``` and ```test_id``` are builtin arguments provided by the framework. 
- ```bucket_config``` and ```data_file_path``` are defined explicitly by developer at test requirements declaration section.

## Forge ```scope```
Forge ```scope``` is a name of a common name or a marker grouping several forge assignments to tests. There are no special structures behind such group, only the name. Using the same group name with several forge assignments makes the resource belong to the scope of this group of tests. If to think about forge as about a declaration of test requirement to create a resource, the scope will define a group of tests sharing this resource. Forge ```scope``` is an important term in framework that allows to leverage forge setup and teardown parts executions by the framework. Scope is a part of the framework internal mechanism that allows multiply tests to have common dependency, i.e. to reuse resources created by same forge function and avoid unnecessary creations and deletions of this resource multiple times for each test. This mechanism is based on the following logic:

1. When framework plans execution of a forge function attached to a tests, it looks through internal records to check if this forge function has been already executed in context of a different test. 

2. Framework assumes that forge functions is not vulnerable to any side effect. In other words, if to execute the same forge function with the same argument values, it will do the same action or it will generate the same resource. So if framework finds previous execution of the forge with the same argument values, it's about to treat it as requirement for the same resource. 

3. If forge argument values are the same framework supposes that it's going to create the same resource and almost ready to make a decision to skip forge execution.

4. The last step before making the final decision about skipping the forge execution is to make sure if this is what developer wants to be done. At this point forge scopes are taken into account. Framework checks the forge declarations at both tests - where the forge function was executed and the current tests. If they have the same scope specified then forge execution is skipped. 

Knowing the above logic developer can tell framework how to treat the forge by letting forges to stay in the same scope or split them ito different scopes. Developer can use any string as a scope name, however there are three names that have special meaning for the framework:

- ```session``` - This is default scope name, which means that every forge assigned to every test has this scope if nothing different is specified. So by default all forge assignments belong to the same group for all tests, no matter in which module test is implemented. That in it's turn means that for all tests the same forge function with the same argument values will be treated by framework as creating the same resource and and will be executed only once. 

- ```module``` - This scope name says that forge assignment scope should be limited to all tests of the same test module (python source file). When framework registers forge assignment to a tests it does not store scope name as is, instead it replaces ```module``` with the path of the test module where this assignment takes place. Note that forge assignments with ```session``` scope and ```module``` scope remain in different scopes even if they are located in the same test module, i.e. ```module``` scope is made only of forge assignments with scope ```module``` and located in the same test module. In some sense value ```module``` is a shortcut to tests module file path, so using it in several test modules in reality creates a separate scope for each of those test modules.

- ```function``` - This scope name says framework to consider forge (or resource created by it) only in context of one single tests that this forge is assigned to. This means that framework will never treat this forge as creating common reusable resource. Similar to ```module``` scope, ```function``` scope name is not saved as is, instead framework replaces ```function``` string with full path to the test function that includes the path to test function module source file, test function class if exists and test function name.

Knowing the forge scope (single test or a group of tests), framework can estimate the lifetime of the resource created by forge function. It monitors the moment when the last test using this resource completes and immediately invokes forge teardown part to remove the resource. 

Notes:

- To avoid typos in predefined scope names framework defines enum object with corresponding enum values in ```splunk_add_on_ucc_modinput_test.functional.constants``` module:
    ```python
    class ForgeScope(Enum):
        FUNCTION = "function"
        MODULE = "module"
        SESSION = "session"
    ```
- In most cases framework can clearly understand when a forge assigned to several tests is going to create the same resource or different one judging only by forge argument values. 

- Explicit scope assignment makes sense only when developer has intention to alter default framework behavior, i.e. to tell framework to create resource for specific test or group of tests where otherwise it would reuse existing resource. 

- Same results can be achieved by manipulation of forge argument values, however some scenarios are more difficult to implement. One of the easiest ways to tell framework that specific forge creates separate resource for each test is to use builtin forge argument ```test_id``` - it will make forge argument values different from test to tests and at the same time provides unique identifier to form a unique name for created resource.

- When adjusting framework logic by explicitly defining forge assignment scope rethink names and lifetimes of the resources created by the forge to avoid failures caused by attempting to create resources with the same name as existing ones.

## Forge assignment
For forge assignment to tests framework implements two test function decorators that create binding between forges and a test and at the same time define when forge should be invoked - before all tests execution starts or before exact test execution starts. There are also two data collection helper classes tat allow to arrange forge dependencies and apply additional builtin and custom settings like scope and probe assignment, as well as explicit/in-place forge arguments values definition. Note that the same forge function can be assigned to different test functions, however framework does not support assigning same forge function to the same test function multiply times. Order of forges in which they are listed within used decorator defines forges dependencies, which means that each preceding forge (i.e. resource it creates) becomes a requirement for the forge following it. Note that each test should declare all forges (resources) it depends on, so if too tests depend on same resources they both should have the same list of forges declared in the same order.

### Helper data collection classes
These helper classes together allow developer to specify all forge data necessary to create internal forge object, as well as to define which forges can be executed in parallel and which sequentially.

#### ```forge``` helper data collection class
Let's start with this helper data class ```forge``` as it allows to specify all forge data necessary to create internal forge object. It was already used in some example of previous sections. It has only one mandatory positional argument that receives forge function itself. There are two other arguments that have special meaning for the framework - ```probe``` and ```scope```. They are optional and if used must be specified as named arguments. The first named argument, ```probe```, allows to link a probe function to the forge function assignment and by default takes value ```None```, which means no probe function is assigned.  The second named argument, ```scope```, defines forge assignment scope. By default scope value for all forge assignments is "session" if not redefined by ```forges``` helper data class. ```forge``` class constructor also allows to define argument values for assigned forge. Note that explicitly defines=d value for forge argument will have precedence over artifactory value is such exists in test artifactory. Here is an example of a forge function and this forge assignment using ```forge``` helper data class.
```python
from splunk_add_on_ucc_modinput_test.functional.constants import ForgeScope
def create_splunk_index(splunk_client, index_name):
    splunk_client.create_index(index_name)

@bootstrap(
    forge(create_splunk_index, index_name="some_index", scope=ForgeScope.FUNCTION, probe=wait_for_index_creation)
)
test_something(splunk_client)
    # test implementation
```
In above example forge ```create_splunk_index``` is assigned to test function ```test_something```. Beside forge function, ```forge``` helper data class constructor defines forge assignment (resource) scope as ```function``` and assigns ```wait_for_index_creation``` function as probe. Additionally it defines ```index_name``` argument value for the forge function, so when ```create_splunk_index``` function will be invoked it will receive ```splunk_client``` object from framework builtin argument and ```index_name``` value from this explicit value assignment.  

Within ```bootstrap``` or ```attach``` assignment decorators can declare multiply forge assignments one after another. This ordered list defines the sequence of forge function execution and can be treated as forge dependencies on each other. In other words, forge A preceding forge B in this least can be taken as forge A is a pre-requirement for forge B and must be executed before forge B. For example, Splunk index should be created before add-on modular input using this index, so forge creating index should be listed before the forge creating the modular input:
```python
def create_splunk_index(splunk_client, index_name):
    splunk_client.create_index(index_name)

def create_splunk_input(splunk_client, input_name):
    splunk_client.create_input(input_name)

@bootstrap(
    forge(create_splunk_index)
    forge(create_splunk_input)
)
test_something(splunk_client)
    # test implementation
```
#### ```forges``` helper data collection class
This is a helper data class that allows to define at certain list position a sub-list of independent forges that can be executed by framework in parallel. In other words, it allows to put a list of forges in place of a single forge assignment. 

This data collection class constructor receives unlimited number of ```forge``` data collection object and one optional named argument ```scope``` that allows ro efine scope for the whole group of listed forges.

This helper data collection class can be very useful if the resources to be created do not dependent on each other and though there is no reason to create them one after another. Much faster to create them in parallel.  For example, two types of modular inputs can be created independently but both depend on creation of index they going to use:
```python
def create_splunk_index(splunk_client, index_name):
    splunk_client.create_index(index_name)

def create_input_of_type_A(splunk_client, input_name):
    splunk_client.create_input_a(input_name)

 def create_input_of_type_B(splunk_client, input_name):
    splunk_client.create_input_b(input_name)

@bootstrap(
    forge(create_splunk_index)
    forges(
        forge(create_input_of_type_A),
        forge(create_input_of_type_B),
        scope=ForgeScope.MODULE
    )
)
test_something(splunk_client)
    # test implementation
```
Note that in the example ```scope``` value is defines in ```forges``` and it changes default scope for every forge in the list. 

### Forge assignment decorators
```bootstrap``` and ```attach``` decorators take the list of ```forge``` and ```forges``` instancies and do the actual assignment of each forge function to specific test function taking into account dependency information and the settings collected by the data classes. Depending on which decorator was used, assigned forges will have different execution algorithm and schedule.

#### ```bootstrap``` decorator
This decorator defines a scope of forges that should be executed before tests started.
```python
@bootstrap(
    forge(forge_function1)
    forge(forge_function2)
    forge(forge_function3)
)
test_something()
    # test implementation

@bootstrap(
    forge(forge_function4)
    forge(forge_function5)
    forge(forge_function6)
)
test_something_else()
    # test implementation    
```
#### ```attach``` decorator
This decorator defines a scope of forges that should be executed right before the tests it's assigned to has started.
```python
@attach(
    forge(forge_function1)
    forge(forge_function2)
    forge(forge_function3)
)
test_something()
    # test implementation
```

### Forge ```meta``` arguments
### Probes
The single purpose of a probe is to do a check that certain resource is created or required conditions met. Probes are used by the framework together with forges and let it verify that an action taken by a forge achieved the expected result and if it's not to wait for expected result if necessary. This means that if for some reason result of the probe is negative, framework will keep calling the probe in certain intervals until it gets successful or the time configured for waiting the expected result expires. Though framework does not jump to the next following forge execution until probe succeeds or expires. Probes can use any parameters saved in test artifactory by declaring them in probe function arguments. There are two ways do implement a probe supported by the unified functional test framework - using function or using generator function. Depending on the approach chosen, developer will have different control on the verification process and requirements to probe return values.
#### Probe as function
As follows from the name, this kind of probe is a regular function returning True or False, depending on if it was successful or failed accordingly. So it's pretty simple to implement and developer is required just to create straightforward code checking some desired condition. Framework in its turn is responsible for calling this probe with default frequency until it gets successful or default timeout is reached. The probe call interval and expiration period for all such probes are defined globally and can be controlled vial pytest command prompt arguments ```--probe-invoke-interval=\<value in seconds\>``` and ```--probe-wait-timeout=\<value in seconds\>``` correspondingly. In case of any exception raised inside probe ite will be taken as permanently failed without any following attempts to call it again and the whole corresponding test will be marked as failed as well. The same way probe timeout rises internal framework SplTaFwkWaitForProbeTimeout exception that fails the probe together with corresponding forge and the test.  Note that this kind of probe does not know about how many time it was called, if the current call is the first for the forge or consequent, what is the elapse time of waiting for a check to succeed. 

Here how this type of probe may look:
```python
def some_input_is_created(splunk_client: SplunkClient, input_name: str) -> bool:
    return splunk_client.get_some_input(input_name) is not None
```
#### Probe as generator function
This approach is more complicated and requires developer to create a generator which fulfils required protocol to interact with the framework: 
- in case of unsuccessful check this generator should yield integer positive value in seconds that framework should use as interval before calling probe once again. Framework verifies yielded interval value and makes sure it's within 1-60. Framework will update interval with minimum or maximum value of the expected range in case yielded interval value is less than the range minimum or bigger than the range maximum correspondingly.
- if the check was successful, generator should exit optionally returning True. 
- if probe has internally defined timeout which is less than global probe timeout, the probe can gracefully exit returning False or through an exception.
- if probe does not have internal timeout or internal timeout is greater then global probe timeout the framework will raise internal probe timeout exception when probing process time exceeded global probe timeout.

Here how this type of probe may look:
```python
def some_input_is_created(splunk_client: SplunkClient, input_name: str) -> Generator[int, None, Optional[bool]] :
    timeout = 60
    start_time = time()
    # can have here some preliminary preparations or checks
    while time() - start_time < timeout:
        success = splunk_client.get_some_input(input_name) is not None
        if success:
            return True
        yield 10
    
    return False # or raise and exception
```
As seen from the example this type of probe is aware about probing progress and has more control over it:

- it defines check interval and can vary it depending on progress conditions

- it can decide if with probe failing also to fail the test or exit gracefully giving a chance to a test to decide how to treat probe failing

- it can have some kind of init code for preliminary preparations and checks.

#### Helper search probe as generator function
To make creation of generator function probes easier framework provides a default probe as a methods of splunk_client built in argument. The probe is based on search operation in Splunk index which is most popular way of probing when it's needed to make sure that expected events have been ingested or logs have been generated by an add-on code. A probe using this helper probe will look like the following:
```python
def wait_for_some_input_to_start(
    splunk_client: SplunkClient
) -> Generator[int, None, True]:
    probe_spl = "some SPL looking into Splunk _internal index for a log generated by input process at start"
    successful = yield from splunk_client.search_probe(
        probe_spl,      # the SPL to search
        timeout=30,     # maximum time in seconds given to get successful result. It's an optional argument with default value 300
        interval=10,    # interval of prove invocation. It's an optional argument with default value 5
        verify_fn = my_verify_function,  # optional function to search result analysis return ing True/False. 
                                        # by default the probe is successful search returns at least one record
        probe_name="wait_for_some_input_to_start" # optional name of your probe used only for test logging
    )
    return successful
```
As seen from the example comments, only probe_spl argument is mandatory to call this helper probe.

By defining your own verification function (verify_fn argument) it's possible to alter expected condition for positive result. By default it expects from SPL any non empty result. Custom verify function like below will make it expect some specific number of events , let it be 10:
```python
def my_verify_function(state: SearchState) -> bool:
    return state.result_count == 10
```
#### Probe arguments and return value
To summarize, a probe can rely on any built in framework argument or any artefact (a property stored in test artifactory) just by declaring probe function arguments with the same names as expected artifacts. It's not possible to pass to a probe any argument value explicitly, but it's possible to do it via argument of the the forge this probe is assigned to and this forge should saves the argument in test artifactory. Probe can return a boolean value. If it does, framework will handle it and add to test artifactory with the name of probe function as the key and the returned boolean value as the value. This artefact can then be used by the test and by other probes and forges executed at later processing stages.
## Tests
### Test arguments
### Test execution order
### Tasks
Task is not what developer is going to deal with directly. Task is an internal framework entity that is a combination of a forge function with specific argument values and optionally attached probe that should be executed for a specific test.
## Forge execution flow and forge lifetime
## Best practices