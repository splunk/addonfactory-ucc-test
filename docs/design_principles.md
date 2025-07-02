# Design principles

The addonfactory-ucc-test framework follows principles in an order based on importance:

1. [add-on developer experience](./before_you_write_your_first_line_of_code.md)

2. [execution time](./design_principles.md#performance)

3. [test scenarios complexity](./design_principles.md#complexity)

4. [data isolation](./design_principles.md#data-isolation)

5. [cross-platform & CI-ready](./design_principles.md#supported-platforms)

6. [framework deepdive](./framework_deepdive.md)

## Building blocks

The addonfactory-ucc-test framework consists of following building blocks:

- addonfactory-ucc-test that contains:

    - [`ucc-test-modinput` CLI tool](./ucc-test-modinput_cli_tool.md) used to initialise the tests (creates relevant directories, files and initial test; one time action), generate add-on SDK and other supporting actions (text encryption and decryption) 

    - [`addonfactory-ucc-test/functional` pytest plugin](./addonfactory-ucc-test_pytest_plugin.md) used to extend pytest functionality to support end-to-end functional tests 

- supporting artifacts:

    - `ucc_modinput_functional` tests in [`Splunk Add-on for Example` ](https://github.com/splunk/splunk-example-ta)

    - this documentation

## Concepts to use and rules to follow

Framework comes with libraries used to deal with Splunk (Enterprise as well as Cloud), UCC-related functionalities and common actions.

There are following concepts used in the framework as well as rules add-on developer should follow:

1. **Vendor product-related and add-on specific functionalities** are left to the **developer to deal with**

2. **test functions** should be used just **to assert** actual vs expected values

3. test functions are wrapped by **forge decorators** that **define setup and teardown tasks**

4. forge can yield `Dict[str,Any]`. Key becomes globally available variable that refers to relevant value

5. **probe function** can be defined for forge **to optimise setup time**

6. **forge functions** are **executed in a sequence as they appear**  - that means setup tasks are executed in a sequence of appearance while tear down tasks are executed in reversed order

7. **forges decorator** allows to **group forge** tasks that can be **executed parallely**

8. **bootstrap** decorators group forge tasks that are **common for many tests**

9. **attach** decorators group forge tasks that are **specific for certain test**

*Note: [Order of importance is discussed separately.](./framework_deepdive.md/#forges)*

## Performance

- **bootstrap** makes sure setup and teardown tasks are executed just once, no matter for how many tests they are required.

- **probes** when applied for setup tasks, makes setup task is finished as soon as expected state is achieved.

- **forges** allows to parallelise independent tasks.


## Complexity

The framework is thought the way, to be able to address even the most complicated Splunk add-ons. To achieve this goal, **each forge should cover just one functionality**. This way it becomes atomic. Atomic components can be connected, related or group flexible.

## Data isolation

There are certain ways data can be isolated:

- **dedicated index** is created for each test run by default and it is highly recommended to use the index. Moreover, AUT provides a functionality that allows to create custom indexes if needed

- **attach decorator** allows to isolate specific tests so time range can be defined for splunk events

- source of the event allows to identify input

- unique **test id** can be used to distinguish between specific tests and test runs

## Supported platforms

This framework is supported on the most popular workstations (MacOS, Linux, Windows) as well as CIs (GitHub, GitLab).

