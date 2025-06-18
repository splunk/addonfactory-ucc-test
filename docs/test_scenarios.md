# Test scenarios

General test cases are described. There are scenarios for each and relevant [concepts](./design_principles.md#design-principles) that should be used.

***Note:** all `forge` tasks should be treated as `bootstrap` unless explicitly defined as `attach`*

***Note:** if `forge` term is used, that generally refers to setup step unless explicitly defined as teardown*


## Basic scenario

We want to ingest some general events for few inputs and vendor product is *talkative* enough to expose the event within seconds or few minutes.

1. Increase log level to DEBUG (forge)

2. Create configuration (forge; yield configuration name - will be used for input)

3. Create inputs that depend on just created configuration (forge with probe - will be used to wait; yield SPL query that should contain at least index, source and start time information)

4. Wait till events are indexed (probe; use SPL query)

5. Test - assert event/actual values are as expected (use SPL query; assert returned values against expected values)

6. Disable inputs (forge teardown)

7. Decrease log level to initial value (forge teardown)

## Isolate data in indexes

***Note:** this case is just an extension of [Basic scenario](#basic-scenario) and as such, just concepts that touches the differences will be described*

Specifics of an add-on considered in this scenario does not allow to distinguish which input was used to ingest specific event.

***Hint:** When constructing tests for this kind of add-on, you want to have [dedicated index for each input](./design_principles.md/#data-isolation)*

1. Increase log level to DEBUG

2. Create (`forges` as following can be done independently)

    1. configuration

    2. indexes (forge per index; yield index name - will be used for input)

3. Create inputs with reference to just created configuration and indexes

4. Wait

5. Test

6. Disable inputs

7. Decrease log level

## Test proxies

***Note:** this case is just an extension of [Basic scenario](#basic-scenario) and as such, just concepts that touches the differences will be described*

We want to be sure the add-on can be configured to use proxy if needed.

***Hint:** Proxy configuration is general for specific add-on, so if defined it will be used for all configuration entries as well as inputs.
When constructing this kind of tests you want to isolate them that can be achieved by using `attach` decorator that would group following tasks*

1. Increase log level to DEBUG 

2. Configure proxy or disabled if we want to test without proxy configured (`attache` to be sure all following forge tasks are in the context of this configuration)

    1. Create configuration - we want to be sure proxy configuration is applied to it, especially if connection to vendor product is established to validate configuration corectness

    2. Create inputs

    3. Wait

    4. Test

    5. Disable inputs

3. Decrease log level

## Trigger events generation

We want to ingest some general events for an input and vendor product needs to be triggered to generate the events first.

1. Increase log level to DEBUG (forge)

2. Following steps can be executed independently, before relevant input is created (forges)

    1. Create configuration (forge; yield configuration name - will be used for input)

    2. Trigger vendor product to generate event (forge; yield timestamp)

3. Create input that depend on just created configuration and timestamp (forge with probe - will be used to wait; yield SPL query that should contain at least index, source and start time information)

4. Wait till events are indexed (probe; use SPL query)

5. Test - assert event/actual values are as expected (use SPL query; assert returned values against expected values)

6. Disable input (forge teardown)

7. Decrease log level to initial value (forge teardown)

## Configure vendor product

***Note:** this case is just an extension of [triggering events generation](#trigger-events-generation) and as such, just concepts that touches the differences will be described*

Vendor product needs to be configured before it can be triggered to generate the events. The vendor product configuration has to be roll back then.

1. Increase log level to DEBUG

2. Configure vendor product (forge; yield configuration name - it can be used later for configuration or input and the configuration teardown)

2. Before input is created

    1. Create configuration

    2. Trigger vendor product to generate event

3. Create input

4. Wait

5. Test

6. Disable input

7. Delete vendor product configuration (forge teardown)

8. Decrease log level

## Eliminate dangling resources

***Note:** this case is just an extension of [configuring vendor product](#configure-vendor-product) and as such concepts that touches the differences will be described*

It happens that teardown is not reached in the tests. There can be number of reasons - eg. developer interupts tests execution before teardown is reached.

We have to maintain hygiene in vendor product configuration to eliminate dangling resources.

***Hint:** We want to be able to distinguish configuration created for our tests from: 1. configuration used for other purposes, 2. configuration created for our tests but other time, 3. configuration created for our tests but by other test run - that may be a case in CI*

All the steps are the same as for [configuring vendor product](#configure-vendor-product), beside implementation of:

2. Configure vendor product:

    1. Check list of configuration items and filter by names. Process only if name: 1. matches predefined pattern for the tests, 2. timestamp shows the configuration is older than predefined threshold. Delete the resources.

    2. When creating the configuration, make sure its name 1. matches predefined pattern, 2. contains timestamp and 3. contains [test id](./design_principles.md/#data-isolation).