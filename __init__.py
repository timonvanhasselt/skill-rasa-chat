from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from mycroft.util.parse import match_one
import requests

class RasaSkill(MycroftSkill):
    """
    Mycroft skill that acts as an interface between a Rasa chatbot and a user,
    allowing continuous voice dialog between the two.
    """

    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        """
        Initialize the RasaSkill by setting the Rasa REST endpoint and setting up variables.
        """
        self.log.info("Done loading Rasa skill")
        self.conversation_active = False
        self.convoID = 1
        self.init_msg = "Insert the welcome message here" #change this to your own welcome message
        self.end_msg = "Insert the goodbye message here" #change this to your own goodbye message
        self.RASA_API = "http://localhost:5005/webhooks/rest/webhook" #change this to your own Rasa REST endpoint
        self.messages = []
        self.session = requests.Session()

    def send_message_to_rasa(self, msg) -> list:
        """
        Send a message to Rasa REST endpoint.

        :param msg: The message to send to Rasa.
        :return: The response from the Rasa REST endpoint.
        """
        data = self.session.post(
            self.RASA_API,
            json={
                "message": msg,
                "sender_id": "user{}".format(self.convoID)
            }
        )

        return data.json()

    def update_messages(self, data) -> None:
        """
        Update the messages list with the responses from Rasa.

        :param data: The response data from the Rasa REST endpoint.
        """
        for next_response in data:
            if "text" in next_response:
                # append to messages list
                self.messages.append(next_response["text"])
                # flush retry
                self.retry = 0

        if len(self.messages) == 0:
            self.messages = ["no response from rasa"]

    def retry_handler(self, msg):
        """
        Handle the retry logic for when the mic is opened but no response is given.
        """
        #TODO: Check a better way to handle empty responses when opening the mic
        if self.retry == 3:
            self.stop()

        if msg is None:
            self.retry += 1
            self.query_rasa("")

    def query_rasa(self, prompt=None):
        """
        Query the Rasa chatbot with a given prompt.

        :param prompt: The prompt to send to the Rasa chatbot.
        :return: The response from the chatbot.
        """
        if self.conversation_active == False:
            return self.end_msg

        msg = self.get_response(prompt, num_retries=0)

        self.retry_handler(msg)
        # flush messages
        self.messages = []
        # get rasa response
        data = self.send_message_to_rasa(msg)
        # update the messages list
        self.update_messages(data)
        # join the messages list
        prompt = " ".join(self.messages)

        return self.query_rasa(prompt)

    def stop(self) -> None:
        """
        Stop the current conversation with the Rasa chatbot.
        """
        self.conversation_active = False

    @intent_handler(IntentBuilder("StartChat").require("Chatwithrasa"))
    def handle_talk_to_rasa_intent(self, message) -> None:
        """
        Handle the intent to start a chat with the Rasa chatbot.
        """
        self.convoID += 1
        self.conversation_active = True
        # send welcome message to rasa
        welcome_response = self.send_message_to_rasa(self.init_msg)
        # update messages list
        self.update_messages(welcome_response)
        # join messages list
        prompt = " ".join(self.messages)
        # send prompt
        self.query_rasa(prompt)

    @intent_handler(IntentBuilder("StopChat").require("Stop"))
    def handle_stop_chat(self, message) -> None:
        """
        Handle the intent to stop a chat with the Rasa chatbot.
        """
        self.stop()
        self.query_rasa()

    # @intent_handler(IntentBuilder("ResumeChat").require("Resume"))
    # def handle_resume_chat(self, message) -> None:
    #     """
    #     Handle the intent to resume a chat with the Rasa chatbot.
    #     """
    #     self.conversation_active = True
    #     self.query_rasa()

def create_skill():
    return RasaSkill()