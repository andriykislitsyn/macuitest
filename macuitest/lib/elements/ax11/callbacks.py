"""Wrap objc calls to raise python exception."""

from ApplicationServices import (AXObserverAddNotification, AXObserverCreate, AXObserverRemoveNotification,
                                 AXUIElementCopyActionNames, AXUIElementCopyAttributeNames,
                                 AXUIElementCopyAttributeValue, AXUIElementCopyElementAtPosition, AXUIElementGetPid,
                                 AXUIElementIsAttributeSettable, AXUIElementPerformAction, AXUIElementSetAttributeValue,
                                 AXUIElementSetMessagingTimeout, )
from objc import callbackFor

from macuitest.lib.elements.ax11 import errors

PAXObserverCallback = callbackFor(AXObserverCreate)


def PAXObserverCreate(application, callback):
    """
    Creates a new observer that can receive notifications
    from the specified application.

    Args:
        application: The process ID of the application
        callback: The callback function

    Returns: an AXObserverRef representing the observer object

    """
    error_code, observer = AXObserverCreate(application, callback, None)
    error_messages = {errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value",
                      errors.kAXErrorFailure: "There is some sort of system memory failure", }
    errors.check_ax_error(error_code, error_messages)
    return observer


def PAXObserverAddNotification(observer, element, notification, refcon):
    """
    Registers the specified observer to receive notifications from
    the specified accessibility object

    Args:
        observer: The observer object created from a call to AXObserverCreate
        element: The accessibility object for which to observe notifications
        notification: The name of the notification to observe
        refcon: Application-defined data passed to the callback when it is called

    """
    error_code = AXObserverAddNotification(observer, element, notification, refcon)
    error_messages = {errors.kAXErrorInvalidUIElementObserver: "The observer is not a valid AXObserverRef type.",
                      errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value or the length of the notification name is greater than 1024.",
                      errors.kAXErrorNotificationUnsupported: "The accessibility object does not support notifications (note that the system-wide accessibility object does not support notifications).",
                      errors.kAXErrorNotificationAlreadyRegistered: "The notification has already been registered.",
                      errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
                      errors.kAXErrorFailure: "There is some sort of system memory failure.", }
    errors.check_ax_error(error_code, error_messages)


def PAXObserverRemoveNotification(observer, element, notification):
    """
    Removes the specified notification from the list of notifications the
    observer wants to receive from the accessibility object.

    Args:
        observer: The observer object created from a call to AXObserverCreate
        element: The accessibility object for which this observer observes notifications
        notification: The name of the notification to remove from
            the list of observed notifications

    """
    error_code = AXObserverRemoveNotification(observer, element, notification)
    error_messages = {errors.kAXErrorInvalidUIElementObserver: "The observer is not a valid AXObserverRef type.",
                      errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value or the length of the notification name is greater than 1024.",
                      errors.kAXErrorNotificationUnsupported: "The accessibility object does not support notifications (note that the system-wide accessibility object does not support notifications).",
                      errors.kAXErrorNotificationNotRegistered: "This observer has not registered for any notifications.",
                      errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
                      errors.kAXErrorFailure: "There is some sort of system memory failure.", }
    errors.check_ax_error(error_code, error_messages)


def PAXUIElementCopyAttributeValue(element, attribute):
    """
    Returns the value of an accessibility object's attribute

    Args:
        element: The AXUIElementRef representing the accessibility object
        attribute: The attribute name

    Returns: the value associated with the specified attribute

    """
    error_code, attr_value = AXUIElementCopyAttributeValue(element, attribute, None)
    error_messages = {
        errors.kAXErrorAttributeUnsupported: "The specified AXUIElementRef does not support the specified attribute.",
        errors.kAXErrorNoValue: "The specified attribute does not have a value.",
        errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
        errors.kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return attr_value


def PAXUIElementIsAttributeSettable(element, attribute):
    """
    Returns whether the specified accessibility object's attribute can be modified

    Args:
        element: The AXUIElementRef representing the accessibility object
        attribute: The attribute name

    Returns: a Boolean value indicating whether the attribute is settable

    """
    error_code, settable = AXUIElementIsAttributeSettable(element, attribute, None)
    error_messages = {
        errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way (often due to a timeout).",
        errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        errors.kAXErrorAttributeUnsupported: "The specified AXUIElementRef does not support the specified attribute.",
        errors.kAXErrorNoValue: "The specified attribute does not have a value.",
        errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        errors.kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return settable


def PAXUIElementSetAttributeValue(element, attribute, value):
    """
    Sets the accessibility object's attribute to the specified value

    Args:
        element: The AXUIElementRef representing the accessibility object
        attribute: The attribute name
        value: The new value for the attribute

    """
    error_code = AXUIElementSetAttributeValue(element, attribute, value)
    error_messages = {
        errors.kAXErrorIllegalArgument: "The value is not recognized by the accessible application or one of the other arguments is an illegal value.",
        errors.kAXErrorAttributeUnsupported: "The specified AXUIElementRef does not support the specified attribute.",
        errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
        errors.kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)


def PAXUIElementCopyAttributeNames(element):
    """
    Returns a list of all the attributes supported by the specified accessibility object

    Args:
        element: The AXUIElementRef representing the accessibility object

    Returns: an array containing the accessibility object's attribute names

    """
    error_code, names = AXUIElementCopyAttributeNames(element, None)
    error_messages = {
        errors.kAXErrorAttributeUnsupported: "The specified AXUIElementRef does not support the specified attribute.",
        errors.kAXErrorIllegalArgument: "One or both of the arguments is an illegal value.",
        errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        errors.kAXErrorFailure: "There was a system memory failure.",
        errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
        errors.kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return names


def PAXUIElementCopyActionNames(element):
    """
    Returns a list of all the actions the specified accessibility object can perform

    Args:
        element: The AXUIElementRef representing the accessibility object

    Returns: an array of actions the accessibility object can perform
        (empty if the accessibility object supports no actions)

    """
    error_code, names = AXUIElementCopyActionNames(element, None)
    error_messages = {errors.kAXErrorIllegalArgument: "One or both of the arguments is an illegal value.",
                      errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
                      errors.kAXErrorFailure: "There was some sort of system memory failure.",
                      errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
                      errors.kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return names


def PAXUIElementPerformAction(element, action):
    """
    Requests that the specified accessibility object perform the specified action

    Args:
        element: The AXUIElementRef representing the accessibility object
        action: The action to be performed

    """
    error_code = AXUIElementPerformAction(element, action)
    error_messages = {
        errors.kAXErrorActionUnsupported: "The specified AXUIElementRef does not support the specified action (you will also receive this error if you pass in the system-wide accessibility object).",
        errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way or the application has not yet responded.",
        errors.kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)


def PAXUIElementGetPid(element):
    """
    Returns the process ID associated with the specified accessibility object

    Args:
        element: The AXUIElementRef representing an accessibility object

    Returns: the process ID associated with the specified accessibility object

    """
    error_code, pid = AXUIElementGetPid(element, None)
    error_messages = {errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
                      errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.", }
    errors.check_ax_error(error_code, error_messages)
    return pid


def PAXUIElementCopyElementAtPosition(application, x, y):
    """
    Returns the accessibility object at the specified position in
    top-left relative screen coordinates

    Args:
        application: The AXUIElementRef representing the application that
            contains the screen coordinates (or the system-wide accessibility object)
        x: The horizontal position
        y: The vertical position

    Returns: the accessibility object at the position specified by x and y

    """
    error_code, element = AXUIElementCopyElementAtPosition(application, x, y, None)
    error_messages = {errors.kAXErrorNoValue: "There is no accessibility object at the specified position.",
                      errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
                      errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
                      errors.kAXErrorCannotComplete: "The function cannot complete because messaging has failed in some way.",
                      errors.kAXErrorNotImplemented: "The process does not fully support the accessibility API.", }
    errors.check_ax_error(error_code, error_messages)
    return element


def PAXUIElementSetMessagingTimeout(element, timeout: int):
    """
    Sets the timeout value used in the accessibility API

    Args:
        element: The AXUIElementRef representing an accessibility object
        timeout: The number of seconds for the new timeout value

    """
    error_code = AXUIElementSetMessagingTimeout(element, timeout)
    error_messages = {
        errors.kAXErrorIllegalArgument: "One or more of the arguments is an illegal value (timeout values must be positive).",
        errors.kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.", }
    errors.check_ax_error(error_code, error_messages)
