# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from datetime import datetime, timedelta
import json
from typing import Any, Dict, List, Text, Tuple
from jinja2 import Template
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import uncurl
from rasa.core.channels.channel import decode_and_extract_ids
from jsonpath_ng import parse

from rasa.shared.core.events import ActionExecuted, SessionStarted


class KauzaApiCallAction(Action):
    def __init__(self):
        super().__init__()
        self.agent_config_action = {}
    def name(self) -> Text:

        return "kauza_api_call_action"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        agent_config_action = self.agent_config_action
        curl_template = agent_config_action.get("curl_template")
        # Render the Jinja2 template with actual slot values
        jinja_template = Template(curl_template)
        rendered_curl_command = jinja_template.render(**tracker.slots)

        # Make the HTTP request using the constructed cURL command
        response = eval(uncurl.parse(rendered_curl_command))
        
        if response.ok:
            # Process the response as needed
            response_data = response.json()
            # Handle response data here
            # Generate events and responses based on response data
            events = self.process_response_data(response_data, agent_config_action.get("events"))
            responses = agent_config_action.get("responses")
            # Return events and responses
            for response in responses:
                # 
                if response.get("template"):
                    
                    dispatcher.utter_message(
                        response=response.get("template"),
                        **response.get("data", {}),
                    )
                else:
                    
                    dispatcher.utter_message(**{
                        "text": self.render_value(response.get("text"), response_data),
                        "image": self.render_value(response.get("image"), response_data),
                        "response": self.render_value(response.get("template"), response_data),
                        "buttons": response.get("buttons"),
                        "json_message": json.loads(self.render_value(response.get("json_message"), response_data))
                    })
            return events
        else:
            # Handle error
            pass
        
        return []
    
    def render_value(value, response_data):
        template = Template(value)
        rendered_value = template.render(response_data=response_data)
        try:
            event_value = eval(rendered_value)
        except SyntaxError as e:
            event_value = rendered_value
        return event_value
    
    def process_response_data(self, response_data: Dict[Text, Any], raw_events: List[Dict[Text, Any]]) -> Tuple[List[Dict[Text, Any]], List[Dict[Text, Any]]]:
        """
        Process the response data from the API and generate events and responses.
        Modify this method according to the structure of your response data and the desired events and responses.
        """
        events = []
        for event in raw_events:
            event_type = event.get("event")
            
            if event_type == "slot":
                events.append({
                    "event": event_type,
                    "timestamp": event.get("timestamp"),
                    "name": event.get("name"),
                    "value": self.render_value(event.get("value"), response_data)
                })
            elif event_type == "reminder":
                # Extract required information from the reminder event
                
                intent = event.get("intent")
                entities = event.get("entities")
                time_offset = self.render_value(event.get("time_offset"), response_data)
                name = event.get("name")
                kill_on_user_msg = self.render_value(event.get("kill_on_user_msg", True), response_data)
                for ent, val in entities.items():
                    entities[ent] = self.render_value(val, response_data)
                # Schedule the reminder
                events.append({
                    "event": event_type,
                    "intent":intent,
                    "entities":entities,
                    "date_time":datetime.now() + timedelta(**time_offset),
                    "name":name,
                    "kill_on_user_msg":kill_on_user_msg
                })

            elif event_type == "cancel_reminder":
                # Extract required information from the reminder event
                
                intent = event.get("intent")
                entities = event.get("entities")
                time_offset = self.render_value(event.get("time_offset"), response_data)
                name = event.get("name")
                kill_on_user_msg = event.get("kill_on_user_msg", False)
                for ent, val in entities.items():
                    entities[ent] = self.render_value(val, response_data)
                # Schedule the reminder
                events.append({
                    "event": event_type,
                    "intent":intent,
                    "entities":entities,
                    "date_time":datetime.now() + timedelta(**time_offset),
                    "name":name
                })
            elif event_type == "followup":  
                events.append({
                    "event": event_type,
                    "name": event.get("name")
                })
            else:
                events.append({
                    "event": event_type
                })
        
        return events
    
class KauzaDocumentQueryAction(Action):
    def __init__(self):
        super().__init__()
        self.agent_config_action = {}
        
    def name(self) -> Text:
        return "kauza_document_query_action"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Decode tenant_id and agent_id from tracker sender_id
        tenant_id, agent_id = decode_and_extract_ids(tracker.sender_id.split('-')[1])

        # Construct the user message payload
        user_message = tracker.latest_message.get('text')

        # Make the HTTP request to the RAG endpoint
        rag_endpoint = f"http://localhost:9009/rag_query/{tenant_id}/{tracker.sender_id}"
        try:
            response = requests.post(rag_endpoint, json={"user_message": user_message, "message_id":tracker.latest_message.get('message_id')})
        except Exception as e:
            dispatcher.utter_message("Error: " + str(e))
            return []

        # Process the response
        dispatcher.utter_message(response.text)

class KauzaTicketAction(Action):

    def name(self) -> Text:
        return "kauza_ticket_action"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Decode tenant_id and agent_id from tracker sender_id
        tenant_id, agent_id = decode_and_extract_ids(tracker.sender_id.split('-')[1])
        channel = tracker.get_latest_input_channel()
        # Construct the user message payload
        user_message = tracker.latest_message.get('text')

        # Make the HTTP request to the RAG endpoint
        rag_endpoint = f"http://localhost:9009/rag_query/{tenant_id}/{tracker.sender_id}"
        try:
            response = requests.post(rag_endpoint, json={"user_message": user_message, "message_id":tracker.latest_message.get('message_id')})
        except Exception as e:
            dispatcher.utter_message("Error: " + str(e))
            return []

        # Process the response
        dispatcher.utter_message(response.text)

    # agents.kauzaafrica.com/webhooks/{channel_name}/send/{tenant_id}/{agent_id}

class KauzaMessageOrderAction(Action):
    """
    curl -X POST agents.kauzaafrica.com/webhooks/{{ channel }}/send/{{ tenant_id }}/{{ agent_id }} \
        -H "Content-Type: application/json" \
        -d '{
            "recipient_id": "{{ client_phone_number_slot }}",
            "message": "Bonjour, vous avez une nouvelle facture :\\nDescription: {{ invoice_description_slot }}\\nMontant: {{ invoice_amount_slot }}\\nEnvoyé par : {{ invoice_store_slot }}"
        }'
    """
    def name(self) -> Text:
        return "kauza_message_order_action"

    def __init__(self):
        super().__init__()
        self.agent_config_action = {}

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Decode tenant_id and agent_id from tracker sender_id
        tenant_id, agent_id = decode_and_extract_ids(tracker.sender_id.split('-')[1])
        channel = tracker.get_latest_input_channel()

        agent_config_action = self.agent_config_action
        recipient_id = agent_config_action.get("recipient_id")
        message_template = agent_config_action.get("message_template")

        body_template = {
            "recipient_id": recipient_id,
            "message_template": message_template
        }

        # Render the Jinja2 template with actual slot values
        jinja_template = Template(json.dumps(body_template))
        rendered_curl_command = jinja_template.render(
            **tracker.slots
        )
        endpoint = f"agents.kauzaafrica.com/webhooks/{channel}/send/{tenant_id}/{agent_id}"
        try:
            # Make the HTTP request using the constructed cURL command
            # response = eval(uncurl.parse(rendered_curl_command))
            response = requests.post(endpoint, json=body_template)

            if response.ok:
                dispatcher.utter_message("Le message a été envoyé avec succès au client.")
            else:
                dispatcher.utter_message(f"Erreur lors de l'envoi du message : {response.text}")
        except Exception as e:
            dispatcher.utter_message(f"Une erreur est survenue lors de l'envoi du message : {str(e)}")

        return []

class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    def create_ticket(self, dispatcher, tracker: Tracker) -> Text:
        # Extract necessary information from the tracker
        priority = "High"  # Default priority for session start ticket
        description = "New conversation session started"  # Default description
        
        # If metadata is available, include it in the description
        session_started_metadata = tracker.get_slot("session_started_metadata")
        if session_started_metadata:
            description += f"\nMetadata: {session_started_metadata}"

        # Create the ticket (replace this with your ticket creation logic)
        ticket_id = self.create_ticket_in_system(priority, description)
        
        return ticket_id

    async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # the session should begin with a `session_started` event
        events = [SessionStarted()]

        # Create a ticket for the session start
        ticket_id = self.create_ticket(dispatcher, tracker)
        dispatcher.utter_message(f"Ticket {ticket_id} has been created for the session start.")

        # any slots that should be carried over should come after the
        # `session_started` event
        # In this case, no slots need to be carried over
        
        # an `action_listen` should be added at the end as a user message follows
        events.append(ActionExecuted("action_listen"))

        return events

    def create_ticket_in_system(self, priority: Text, description: Text) -> Text:
        # Placeholder logic to create a ticket in your ticketing system
        # Replace this with your actual ticket creation logic
        # Return the ID of the created ticket
        return "T123"  # Example ticket ID