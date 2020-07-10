"""Wrap objc calls to raise python exception."""

from ApplicationServices import (AXUIElementCopyActionNames, AXUIElementCopyAttributeNames,
                                 AXUIElementCopyAttributeValue, AXUIElementCopyElementAtPosition, AXUIElementGetPid,
                                 AXUIElementIsAttributeSettable, AXUIElementPerformAction, AXUIElementSetAttributeValue,
                                 AXUIElementSetMessagingTimeout, )
from ApplicationServices import (kAXErrorActionUnsupported, kAXErrorAttributeUnsupported, kAXErrorCannotComplete,
                                 kAXErrorFailure, kAXErrorIllegalArgument, kAXErrorInvalidUIElement,
                                 kAXErrorNotImplemented, kAXErrorNoValue, )

from macuitest.lib.elements.native import errors


def get_accessibility_element_attribute(element, attribute):
    """ Return the value of an accessibility object's attribute
            Args:
                element: The AXUIElementRef representing the accessibility object
                attribute: The attribute name

            Returns: the value associated with the specified attribute
    """
    error_code, attr_value = AXUIElementCopyAttributeValue(element, attribute, None)
    error_messages = {
        kAXErrorAttributeUnsupported: "The specified AXUIElementRef does not support the specified attribute.",
        kAXErrorNoValue: "The specified attribute does not have a value.",
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return attr_value


def check_attribute_settable(element, attribute) -> bool:
    """ Check whether the specified accessibility object's attribute can be modified.
            Args:
                element: The AXUIElementRef representing the accessibility object
                attribute: The attribute name

            Returns: a Boolean value indicating whether the attribute is settable
    """
    error_code, settable = AXUIElementIsAttributeSettable(element, attribute, None)
    error_messages = {
        kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way (often due to a timeout).",
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        kAXErrorAttributeUnsupported: "The specified AXUIElementRef does not support the specified attribute.",
        kAXErrorNoValue: "The specified attribute does not have a value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return settable


def set_attribute_value(element, attribute, value):
    """ Set the accessibility object's attribute to the specified value
            Args:
                element: The AXUIElementRef representing the accessibility object
                attribute: The attribute name
                value: The new value for the attribute
    """
    error_code = AXUIElementSetAttributeValue(element, attribute, value)
    error_messages = {
        kAXErrorIllegalArgument: "The value is not recognized by the accessible application or one of the other arguments is an illegal value.",
        kAXErrorAttributeUnsupported: "The specified AXUIElementRef does not support the specified attribute.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)


def get_element_attribute_names(element):
    """ Get a list of attributes supported by the specified accessibility object
            Args:
                element: The AXUIElementRef representing the accessibility object

            Returns: an array containing the accessibility object's attribute names
    """
    error_code, names = AXUIElementCopyAttributeNames(element, None)
    error_messages = {
        kAXErrorAttributeUnsupported: "The specified AXUIElementRef does not support the specified attribute.",
        kAXErrorIllegalArgument: "One or both of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorFailure: "There was a system memory failure.",
        kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return names


def get_element_action_names(element):
    """ Get a list of all the actions the specified accessibility object can perform.
            Args:
                element: The AXUIElementRef representing the accessibility object

            Returns: an array of actions the accessibility object can perform
                (empty if the accessibility object supports no actions)
    """
    error_code, names = AXUIElementCopyActionNames(element, None)
    error_messages = {kAXErrorIllegalArgument: "One or both of the arguments is an illegal value.",
                      kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
                      kAXErrorFailure: "There was some sort of system memory failure.",
                      kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
                      kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return names


def perform_action_on_element(element, action):
    """ Make the accessibility object perform the specified action.
            Args:
                element: The AXUIElementRef representing the accessibility object
                action: The action to be performed
    """
    error_code = AXUIElementPerformAction(element, action)
    error_messages = {
        kAXErrorActionUnsupported: "The specified AXUIElementRef does not support the specified action (you will also receive this error if you pass in the system-wide accessibility object).",
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way or the application has not yet responded.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)


def get_accessibility_object_pid(element):
    """ Get the process ID associated with the specified accessibility object.
            Args:
                element: The AXUIElementRef representing an accessibility object

            Returns: the process ID associated with the specified accessibility object
    """
    error_code, pid = AXUIElementGetPid(element, None)
    error_messages = {kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
                      kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.", }
    errors.check_ax_error(error_code, error_messages)
    return pid


def get_accessibility_object_on_screen_position(application, x, y):
    """ Get the accessibility object at the specified position in top-left relative screen coordinates
            Args:
                application: The AXUIElementRef representing the application that
                    contains the screen coordinates (or the system-wide accessibility object)
                x: The horizontal position
                y: The vertical position

            Returns: the accessibility object at the position specified by x and y
    """
    error_code, element = AXUIElementCopyElementAtPosition(application, x, y, None)
    error_messages = {kAXErrorNoValue: "There is no accessibility object at the specified position.",
                      kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
                      kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
                      kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
                      kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return element


def set_accessibility_api_timeout(element, timeout: int):
    """ Set the timeout value used in the accessibility API
            Args:
                element: The AXUIElementRef representing an accessibility object
                timeout: The number of seconds for the new timeout value
    """
    error_code = AXUIElementSetMessagingTimeout(element, timeout)
    error_messages = {
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value (timeout values must be positive).",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.", }
    errors.check_ax_error(error_code, error_messages)
