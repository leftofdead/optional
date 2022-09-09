#!/usr/bin/env python

import logging
import inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Placeholder for values where 'None' is a valid value
UNSET = "UNSET"

# A decorator designed to minimize handling when copying an attribute into a calss/data structure

# When data cannot be retrieved from the source, the default value returned will be prioritized as follows:
#   1) The value for the parameter "default" in the call to 'middle_fn', unless that value is UNSET
#   2) The value returned from the function supplied in callback, unlesscallback is None
#   3) which takes priority over the default value in 'optional'

def optional(default=UNSET, exceptions=Exception, callback=None):
    general_default = default

    def outer_fn(inner_fn, *args, **kwargs):
        # Do global processing here, when the function is declared

        # ASSUME that a parameter named "self" represents what it "always" does
        found_self = False
        for index, param in enumerate(inspect.signature(inner_fn).parameters):
            if param == "self" and index == 0:
                found_self = True
                break

        def middle_fn(*args, **kwargs):
            specific_default = kwargs.pop("default", UNSET)
            callback_value   = kwargs.pop("callback", callback)
            dest_value       = kwargs.pop("dest", None)

            self = None
            # If we found that the first parameter is named 'self', set that value to 'self'
            if found_self:
                # ASSUME the parameters are ordered the same as in the function call
                self = args[0]

            try:
                value = inner_fn(*args, **kwargs)

            except exceptions as e:
                value = general_default
                if callback_value is not None:
                    # free function without 'self' parameter
                    if self is None:
                        value = callback_value(e, *args, **kwargs)
                    else:
                        # class method
                        if isinstance(callback_value, str):
                            value = getattr(self, callback_value)(e, *args[1:], **kwargs)
                        # free function with 'self' parameter
                        else:
                            value = callback_value(self, e, *args[1:], **kwargs)

                    if specific_default is not UNSET:
                        value = specific_default

                logger.debug(f"There was an error retrieving the data. A default value of {value} will be used: {type(e).__name__}: {e}")

            if dest_value is not None and self is not None:
                setattr(self, dest_value, value)
            return value

        return middle_fn

    return outer_fn

#=========================================================================================

# Add 'handle_exception' to your class as a handler
@optional(exceptions=KeyError, callback="handle_exception")
def from_dict(self, a_dict, key=None, dest=None):
    return a_dict[key]

# Add 'handle_exception' to your class as a handler
@optional(exceptions=IndexError, callback="handle_exception")
def from_list(self, a_list, index):
    return a_list[index]
