# Design principles

There are following concepts used in the framework as well as rules add-on developer should follow:

1. framework comes with libraries used to deal with Splunk (Enterprise as well as Cloud) and UCC-related functionalities. Vendor product-related as well as add-on specific functionalities are left to the developer to deal with.

2. **test function**s should be used just **to assert** actual vs expected values

3. test functions are wrapped by **forge decorators** that **define setup and teardown tasks**

4. forge can yield `Dict[str,Any]`. Key becomes globally available variable that refers to relevant value

5. **probe function** can be defined for forge **to optimise setup time**

6. **forge functions** are **executed in a sequence as they appear**  - that means setup tasks are executed in a sequence of appearance while tear down tasks are executed in reversed order

7. **forges decorator** allows to **group forge** tasks that can be **executed parallely**

8. **bootstrap** decorators group forge tasks that are **common for many tests**

9. **attach** decorators group forge tasks that are **specific for certain test**

*Note: [Order of importance is discussed separately.](./index.md#principles)*

## Performance

- **bootstrap** makes sure setup and teardown tasks are executed just once, no matter for how many tests they are required.

- **probes** when applied for setup tasks, makes setup task is finished as soon as expected state is achieved.

- **forges** allows to parallelise independent tasks.


## Complexity

The framework is thought the way, to be able to address even the most complicated Splunk add-ons. To achieve this goal, **each forge should cover just one functionality**. This way it becomes atomic. Atomic components can be connected, related or group flexible.

## Data isolation

There are certain ways data can be isolated:

- **dedicated index** is created for each test run by default and it is highly recommended to use the index. Moreover, AUT provides a functionality that allows to create custom indexes if needed.    

- **attach decorator** allows to isolate specific tests so time range can be defined for splunk events.

- source of the event allows to identify input.

## Supported platforms

This framework is supported on the most popular workstations (MacOS, Linux, Windows) as well as CIs (GitHub, GitLab).

## Developer experience

1. Run `ucc-test-modinput init` in  the context of your add-on repo  and proven to work tests for [splunk-example-ta](https://github.com/splunk/splunk-example-ta) will be populated for you. It is 

<!--
2. Follow [the instruction](./after_init_step_by_step.md) to adopt test files in correct order
-->

3. Keep checking comments (to understand general idea), documentation (to find more information) and unit tests (for details)