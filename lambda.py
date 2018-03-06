# author: Muneeb Mallick

from __future__ import print_function
from oauth2client import client
import httplib2
from googleapiclient import discovery, http
import io
from apiclient.http import MediaIoBaseDownload

# --------------- Helpers that build all of the responses ----------------------

def welcome_build_speechlet_response(title, output, welcome_speech, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': "<speak>" + welcome_speech + output + "</speak>"
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome to My Photos Skill."
    speech_output = "To start your google photos slideshow, " \
                    "Please say show me my google photos"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please say show me my google photos"
    should_end_session = False
    return build_response(session_attributes, welcome_build_speechlet_response(
        card_title, speech_output, "Welcome to My Photos Skill <break/>", reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = ""
    speech_output = "Thank you for trying My Photos Skill. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

#import logging

def hasDisplay(context):
    #logging.warning(context)
    if "Display" in context["System"]["device"]["supportedInterfaces"]:
        return True
    else:
        return False


def renderTemplate(content):
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": content["hasDisplaySpeechOutput"]
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": content["hasDisplayRepromptText"]
                }
            },
            "card": {
                "type": "Simple",
                "title": content["simpleCardTitle"],
                "content": content["simpleCardContent"]
            },
            "directives": [
                    {
                        "type": "Display.RenderTemplate",
                        "template": {
                            "type": "BodyTemplate7",
                            "title": content["simpleCardTitle"],
                            "image": {
                                "contentDescription": "User Image",
                                "sources": [
                                    {
                                        "url": content["image"]
                                    }
                                ]
                            },
                        }
                    },
                ],
            "shouldEndSession": content["session"]
            },
        "sessionAttributes": content["sessionAttributes"]
    }
    return response


def StartDrive(token):
    credentials = client.AccessTokenCredentials(token, 'my-user-agent/1.0')  # obtaining credentials from the accesstoken
    http = httplib2.Http()
    http = credentials.authorize(http)  # authentication of the user credentials
    DRIVE = discovery.build('drive', 'v3', http=http)  # making of the DRIVE object
    return DRIVE

tmploc = "/tmp/"

def folderId(drive):
    files = drive.files().list(q="mimeType='application/vnd.google-apps.folder'",spaces='drive',fields='files(name, id, mimeType)').execute()
    for f in files.get('files', []):
        if f.get('mimeType') == 'application/vnd.google-apps.folder' and f.get('name') == 'gphotos':
            fold_id = f.get('id')
    return fold_id

import os
import time

def ListFolder(parent, drive):
    file_list = drive.files().list(q="'%s' in parents" % parent,fields='files(*)').execute()
    for f in file_list.get('files', []):
        if f.get('mimeType')=='image/png' or f.get('mimeType')=='image/jpeg' or f.get('mimeType')=='image/jpg':
            file_id = f.get('id')
            req = drive.files().get_media(fileId=file_id)
            fn = str(tmploc) + str(f.get('name'))
            logging.warning(os.path.isfile(fn))
            fh = io.FileIO(fn, 'wb')
            downloader = MediaIoBaseDownload(fh, req)
            logging.warning(os.path.isfile(fn))
            
            content = {"hasDisplayRepromptText": reprompt_text, "image": fn, "session": False,
            "templateToken": "photoTemplate","sessionAttributes": {} }
            renderTemplate(content)
            time.sleep(5)


def get_gphotos(intent, session, context, DRIVE):
    session_attributes = {}
    card_title = ""
    reprompt_text = "For another photo, " \
                    "Please say next, " \
                    "or show another photo."
    if hasDisplay(context) is True:
        folder_id = folderId(DRIVE)
        ListFolder(folder_id, DRIVE)

        should_end_session = True

        content = {
            #"hasDisplaySpeechOutput": speech_output,
            "hasDisplayRepromptText": reprompt_text,
            #"simpleCardTitle": card_title,
            #"simpleCardContent": randomFact,
            #"image": userimage,
            "session": should_end_session,
            "templateToken": "photoTemplate",

            "sessionAttributes": {}
        }
        return renderTemplate(content)

    else:
        return build_response(session_attributes, build_speechlet_response(card_title, "Sorry, You would need an Echo Show device to run this skill.", reprompt_text, True))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

import logging

def on_intent(intent_request, session, context):
    """ Called when the user specifies an intent for this skill """
    logging.warning("THIS IS THE LOG: ")
    logging.warning(session)
    token = session["user"]["accessToken"]
    logging.warning(token)

    #print("on_intent requestId=" + intent_request['requestId'] + ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "ViewMyGooglePhotos":
        return get_gphotos(intent, session, context, StartDrive(token))
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'], event['context'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
