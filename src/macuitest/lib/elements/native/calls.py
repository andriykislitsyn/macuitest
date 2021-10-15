"""Wrap objc calls to raise python exception."""
import AppKit
from ApplicationServices import AXIsProcessTrusted
from ApplicationServices import AXUIElementCopyActionNames
from ApplicationServices import AXUIElementCopyAttributeNames
from ApplicationServices import AXUIElementCopyAttributeValue
from ApplicationServices import AXUIElementCopyElementAtPosition
from ApplicationServices import AXUIElementGetPid
from ApplicationServices import AXUIElementIsAttributeSettable
from ApplicationServices import AXUIElementPerformAction
from ApplicationServices import AXUIElementSetAttributeValue
from ApplicationServices import AXUIElementSetMessagingTimeout
from ApplicationServices import kAXErrorActionUnsupported
from ApplicationServices import kAXErrorAPIDisabled
from ApplicationServices import kAXErrorAttributeUnsupported
from ApplicationServices import kAXErrorCannotComplete
from ApplicationServices import kAXErrorFailure
from ApplicationServices import kAXErrorIllegalArgument
from ApplicationServices import kAXErrorInvalidUIElement
from ApplicationServices import kAXErrorInvalidUIElementObserver
from ApplicationServices import kAXErrorNotificationAlreadyRegistered
from ApplicationServices import kAXErrorNotificationNotRegistered
from ApplicationServices import kAXErrorNotificationUnsupported
from ApplicationServices import kAXErrorNotImplemented
from ApplicationServices import kAXErrorNoValue
from ApplicationServices import kAXErrorSuccess
from PyObjCTools import AppHelper


def is_accessibility_enabled():
    """Return the status of accessibility on the system."""
    return AXIsProcessTrusted()


def get_frontmost_pid():
    """Return the process ID of the application in the foreground"""
    return AppKit.NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()


def get_running_apps():
    """Get a list of the running applications"""
    AppHelper.callLater(1, AppHelper.stopEventLoop)
    AppHelper.runConsoleEventLoop()
    work_space = AppKit.NSWorkspace.sharedWorkspace()
    return work_space.runningApplications()


def launch_app_by_bundle_id(bundle_id: str):
    work_space = AppKit.NSWorkspace.sharedWorkspace()
    response = work_space.launchAppWithBundleIdentifier_options_additionalEventParamDescriptor_launchIdentifier_(  # noqa: E501
        bundle_id,
        AppKit.NSWorkspaceLaunchAllowingClassicStartup,
        AppKit.NSAppleEventDescriptor.nullDescriptor(),
        None,
    )
    if not response[0]:
        raise RuntimeError(f"Error launching specified application. {response}")


def launch_app_by_bundle_path(bundle_path: str, arguments=None):
    if arguments is None:
        arguments = []
    bundle_url = AppKit.NSURL.fileURLWithPath_(bundle_path)
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    configuration = {AppKit.NSWorkspaceLaunchConfigurationArguments: arguments}
    return workspace.launchApplicationAtURL_options_configuration_error_(
        bundle_url, AppKit.NSWorkspaceLaunchAllowingClassicStartup, configuration, None
    )


def terminate_app_by_bundle_id(bundle_id: str):
    apps = get_running_apps_with_bundle_id(bundle_id)
    if apps:
        apps[0].terminate()


def get_running_apps_with_bundle_id(bundle_id: str):
    """Return an array of NSRunningApplications."""
    return AppKit.NSRunningApplication.runningApplicationsWithBundleIdentifier_(bundle_id)


def get_accessibility_element_attribute(element, attribute):
    """Return the value of an accessibility object's attribute
    Args:
        element: The AXUIElementRef representing the accessibility object
        attribute: The attribute name

    Returns: the value associated with the specified attribute
    """
    error_code, attr_value = AXUIElementCopyAttributeValue(element, attribute, None)
    error_messages = {
        kAXErrorAttributeUnsupported: "The specified AXUIElementRef "
        "does not support the specified attribute.",
        kAXErrorNoValue: "The specified attribute does not have a value.",
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorCannotComplete: "The function cannot complete "
        "because messaging has failed in some way.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.",
    }
    check_ax_error(error_code, error_messages)
    return attr_value


def check_attribute_settable(element, attribute) -> bool:
    """Check whether the specified accessibility object's attribute can be modified.
    Args:
        element: The AXUIElementRef representing the accessibility object
        attribute: The attribute name

    Returns: a Boolean value indicating whether the attribute is settable
    """
    error_code, settable = AXUIElementIsAttributeSettable(element, attribute, None)
    error_messages = {
        kAXErrorCannotComplete: "The function cannot complete because messaging "
        "has failed in some way (often due to a timeout).",
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        kAXErrorAttributeUnsupported: "The specified AXUIElementRef "
        "does not support the specified attribute.",
        kAXErrorNoValue: "The specified attribute does not have a value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.",
    }
    check_ax_error(error_code, error_messages)
    return settable


def set_attribute_value(element, attribute, value):
    """Set the accessibility object's attribute to the specified value
    Args:
        element: The AXUIElementRef representing the accessibility object
        attribute: The attribute name
        value: The new value for the attribute
    """
    error_code = AXUIElementSetAttributeValue(element, attribute, value)
    error_messages = {
        kAXErrorIllegalArgument: "The value is not recognized by the accessible application"
        " or one of the other arguments is an illegal value.",
        kAXErrorAttributeUnsupported: "The specified AXUIElementRef "
        "does not support the specified attribute.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorCannotComplete: "The function cannot complete "
        "because messaging has failed in some way.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.",
    }
    check_ax_error(error_code, error_messages)


def get_element_attribute_names(element):
    """Get a list of attributes supported by the specified accessibility object
    Args:
        element: The AXUIElementRef representing the accessibility object

    Returns: an array containing the accessibility object's attribute names
    """
    error_code, names = AXUIElementCopyAttributeNames(element, None)
    error_messages = {
        kAXErrorAttributeUnsupported: "The specified AXUIElementRef "
        "does not support the specified attribute.",
        kAXErrorIllegalArgument: "One or both of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorFailure: "There was a system memory failure.",
        kAXErrorCannotComplete: "The function cannot complete "
        "because messaging has failed in some way.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.",
    }
    check_ax_error(error_code, error_messages)
    return names


def get_element_action_names(element):
    """Get a list of all the actions the specified accessibility object can perform.
    Args:
        element: The AXUIElementRef representing the accessibility object

    Returns: an array of actions the accessibility object can perform
        (empty if the accessibility object supports no actions)
    """
    error_code, names = AXUIElementCopyActionNames(element, None)
    error_messages = {
        kAXErrorIllegalArgument: "One or both of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorFailure: "There was some sort of system memory failure.",
        kAXErrorCannotComplete: "The function cannot complete "
        "because messaging has failed in some way.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.",
    }
    check_ax_error(error_code, error_messages)
    return names


def perform_action_on_element(element, action):
    """Make the accessibility object perform the specified action.
    Args:
        element: The AXUIElementRef representing the accessibility object
        action: The action to be performed
    """
    error_code = AXUIElementPerformAction(element, action)
    error_messages = {
        kAXErrorActionUnsupported: "Specified AXUIElementRef does not support the specified action"
        " (you will also receive this error error "
        "if you pass in the system-wide accessibility object).",
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorCannotComplete: "The function cannot complete because messaging has failed"
        " in some way or the application has not yet responded.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.",
    }
    check_ax_error(error_code, error_messages)


def get_accessibility_object_pid(element):
    """Get the process ID associated with the specified accessibility object.
    Args:
        element: The AXUIElementRef representing an accessibility object

    Returns: the process ID associated with the specified accessibility object
    """
    error_code, pid = AXUIElementGetPid(element, None)
    error_messages = {
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
    }
    check_ax_error(error_code, error_messages)
    return pid


def get_accessibility_object_on_screen_position(application, x, y):
    """Get the accessibility object at the specified position
    in top-left relative screen coordinates
    Args:
        application: The AXUIElementRef representing the application that
            contains the screen coordinates (or the system-wide accessibility object)
        x: The horizontal position
        y: The vertical position

    Returns: the accessibility object at the position specified by x and y
    """
    error_code, element = AXUIElementCopyElementAtPosition(application, x, y, None)
    error_messages = {
        kAXErrorNoValue: "There is no accessibility object at the specified position.",
        kAXErrorIllegalArgument: "One or more of the arguments is an illegal value.",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
        kAXErrorCannotComplete: "The function cannot complete "
        "because messaging has failed in some way.",
        kAXErrorNotImplemented: "The process does not fully support the accessibility API.",
    }
    check_ax_error(error_code, error_messages)
    return element


def set_accessibility_api_timeout(element, timeout: int):
    """Set the timeout value used in the accessibility API
    Args:
        element: The AXUIElementRef representing an accessibility object
        timeout: The number of seconds for the new timeout value
    """
    error_code = AXUIElementSetMessagingTimeout(element, timeout)
    error_messages = {
        kAXErrorIllegalArgument: "One or more of the arguments "
        "is an illegal value (timeout values must be positive).",
        kAXErrorInvalidUIElement: "The AXUIElementRef is invalid.",
    }
    check_ax_error(error_code, error_messages)


class AXError(Exception):
    pass


class AXErrorUnsupported(AXError):
    pass


class AXErrorAPIDisabled(AXError):
    pass


class AXErrorInvalidUIElement(AXError):
    pass


class AXErrorCannotComplete(AXError):
    pass


class AXErrorNotImplemented(AXError):
    pass


class AXErrorIllegalArgument(AXError):
    pass


class AXErrorActionUnsupported(AXError):
    pass


class AXErrorNoValue(AXError):
    pass


class AXErrorFailure(AXError):
    pass


class AXErrorInvalidUIElementObserver(AXError):
    pass


class AXErrorNotificationUnsupported(AXError):
    pass


class AXErrorNotificationAlreadyRegistered(AXError):
    pass


class AXErrorNotificationNotRegistered(AXError):
    pass


class AXErrorAttributeUnsupported(AXError):
    pass


class AXErrorFactory:
    def __new__(cls, error_code):
        return {
            kAXErrorAPIDisabled: AXErrorAPIDisabled,
            kAXErrorInvalidUIElement: AXErrorInvalidUIElement,
            kAXErrorCannotComplete: AXErrorCannotComplete,
            kAXErrorNotImplemented: AXErrorNotImplemented,
            kAXErrorIllegalArgument: AXErrorIllegalArgument,
            kAXErrorNoValue: AXErrorNoValue,
            kAXErrorFailure: AXErrorFailure,
            kAXErrorInvalidUIElementObserver: AXErrorInvalidUIElementObserver,
            kAXErrorNotificationUnsupported: AXErrorNotificationUnsupported,
            kAXErrorNotificationAlreadyRegistered: AXErrorNotificationAlreadyRegistered,
            kAXErrorNotificationNotRegistered: AXErrorNotificationNotRegistered,
            kAXErrorAttributeUnsupported: AXErrorAttributeUnsupported,
            kAXErrorActionUnsupported: AXErrorActionUnsupported,
        }.get(error_code, AXErrorUnsupported)


def check_ax_error(error_code: int, error_messages) -> None:
    """Return if code is kAXErrorSuccess.
    Raise an error with given message based on given error code.
    Defaults to AXErrorUnsupported for unknown codes.
       Args:
           error_code: the error code
           error_messages: mapping from error code to error message
    """
    if error_code == kAXErrorSuccess:
        return
    try:
        error_message = error_messages[error_code]
    except KeyError:
        if error_code == kAXErrorFailure:
            error_message = "There is some sort of system memory failure"
        else:
            error_message = f"Unknown AX Error code: {error_code}"
    raise AXErrorFactory(error_code)(error_message)
