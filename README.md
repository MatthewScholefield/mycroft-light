

# Style Guidelines #

## Plugin System ##

Mycroft consists of a series of modules which can optionally be installed to extend behavior. The Module System exists to synamically load these modules without failing if they don't exist.

There are two types of dynamic plugins:
 - **Group** plugins: Represents multiple plugins that can all be simultaneously loaded
 - **Option** plugins: Represents a single plugin that can exist as one of many options

## Global System ##

To interact with other components, your object should receive the `rt` object which is the root `GroupPlugin`.

## Group Plugin ##

Each `GroupPlugin` consists of a list of dynamic object instances stored under a specific name. This instance can be accessed with `group_plugin.my_dynamic_object`. If the object with the name of `'my_dynamic_object'` exists, it is returned. Otherwise, an empty mock object that always evaluates to `False` is returned.
