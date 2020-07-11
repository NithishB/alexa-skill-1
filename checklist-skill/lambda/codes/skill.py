import logging
import pickle
import typing

import httplib2
import boto3
from uuid import uuid4, uuid5
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.ui import LinkAccountCard
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response
from ask_sdk_s3.adapter import S3Adapter
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_model.services.reminder_management import (
    ReminderRequest, Trigger, TriggerType, AlertInfo, PushNotification,
    PushNotificationStatus, ReminderResponse, SpokenInfo, SpokenText)
from ask_sdk_model.services import ServiceException
from ask_sdk_model.ui import AskForPermissionsConsentCard

from .token_transferer import send_token
from .checklist_helper import gather_checklist_content, convert_checklist_to_speech_text

s3_client = boto3.client('s3')
s3_adapter = S3Adapter(bucket_name="jingle-skill-bucket", path_prefix="", s3_client=s3_client)

if typing.TYPE_CHECKING:
    from ask_sdk_core.handler_input import HandlerInput
    from ask_sdk_model import Response

permissions = ["alexa::alerts:reminders:skill:readwrite"]
NOTIFY_MISSING_PERMISSIONS = ("Please enable Reminders permissions in "
                              "the Amazon Alexa app.")

sb = CustomSkillBuilder(persistence_adapter=s3_adapter, api_client=DefaultApiClient())
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # checking access token availability and requesting once
        persistence_attr = handler_input.attributes_manager.persistent_attributes
        try:
            first_try = persistence_attr['first_try']
        except:
            first_try = True
        try:
            user_id = persistence_attr['user_id']
        except:
            user_id = str(uuid4())
        access_token = handler_input.request_envelope.context.system.user.access_token
        if access_token is None and first_try:
            handler_input.response_builder.speak("Try logging in for gmail access else invoke again please").set_card(LinkAccountCard())
            persistence_attr['first_try'] = False
            handler_input.attributes_manager.save_persistent_attributes()
            return handler_input.response_builder.response
        elif access_token is not None:
            filename = user_id+"_token.pkl"
            pickle.dump(access_token, open(filename, "wb"))
            send_token(filename)
        persistence_attr['first_try'] = False
        persistence_attr['user_id'] = user_id
        handler_input.attributes_manager.save_persistent_attributes()

        # Reply to user
        speech_text = "Welcome to Astute Checklist Skill!"
        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response


class CheckListHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("ChecklistIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        persistence_attr = handler_input.attributes_manager.persistent_attributes
        try:
            checklist = persistence_attr['checklist']
        except:
            checklist = []
        new_checklist = gather_checklist_content()
        checklist = checklist + new_checklist
        if len(checklist) > 0:
            speech_text = convert_checklist_to_speech_text(checklist)
        else:
            speech_text = "No checklist yet"
        persistence_attr['checklist'] = checklist
        handler_input.attributes_manager.save_persistent_attributes()

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        speech_text = "Hello from the other side!"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text)).set_should_end_session(
            False)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "You can say hello to me!"

        handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(
            "Hello World", speech_text))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Goodbye!"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("Hello World", speech_text))
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """
    This handler will not be triggered except in supported locales,
    so it is safe to deploy on any locale.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = (
            "The Hello World skill can't help you with that.  "
            "You can say hello!!")
        reprompt = "You can say hello!!"
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = "Sorry, there was some problem. Please try again!!"
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response


sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CheckListHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()
