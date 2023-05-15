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

    def initialize(self):
        """
        Initialize the RasaSkill by setting the Rasa REST endpoint and setting up variables.
        """
        self.conversation_active = False
        self.convoID = 1
        self.RASA_API = "http://localhost:5005/webhooks/rest/webhook"
        self.messages = []

    def send_message_to_rasa(self, msg) -> list:
        """
        Send a message to Rasa REST endpoint.

        :param msg: The message to send to Rasa.
        :return: The response from the Rasa REST endpoint.
        """
        data = requests.post(
            self.RASA_API,
            json={
                "message": msg,
                "sender_id": "user{}".format(self.convoID)
            }
        )

        return data

    def update_messages(self, data) -> None:
        """
        Update the messages list with the responses from Rasa.

        :param data: The response data from the Rasa REST endpoint.
        """
        for next_response in data.json():
            if "text" in next_response:
                self.messages.append(next_response["text"])

        if len(self.messages) == 0:
            self.messages = ["no response from rasa"]

    def query_rasa(self, prompt=None):
        """
        Query the Rasa chatbot with a given prompt.

        :param prompt: The prompt to send to the Rasa chatbot.
        :return: The response from the chatbot.
        """
        if self.conversation_active == False:
            return

        if prompt is None and len(self.messages) > 0:
            prompt = self.messages[-1]

        msg = self.get_response(prompt, num_retries=0)
        if msg is None:
            return
            
        # flush messages
        self.messages = []
        # get rasa response
        data = self.send_message_to_rasa(msg)
        # update the messages list
        self.update_messages(data)
        # join the messages list
        prompt = " ".join(self.messages)

        return self.query_rasa(prompt)

    @intent_handler(IntentBuilder("StartChat").require("Chatwithrasa"))
    def handle_talk_to_rasa_intent(self, message) -> None:
        """
        Handle the intent to start a chat with the Rasa chatbot.
        """
        self.convoID += 1
        self.conversation_active = True
        prompt = "hallo"
        self.query_rasa(prompt)

    @intent_handler(IntentBuilder("ResumeChat").require("Resume"))
    def handle_resume_chat(self, message) -> None:
        """
        Handle the intent to resume a chat with the Rasa chatbot.
        """
        self.conversation_active = True
        self.query_rasa()

    def stop(self) -> None:
        """
        Stop the current conversation with the Rasa chatbot.
        """
        self.conversation_active = False

def create_skill():
    return RasaSkill()