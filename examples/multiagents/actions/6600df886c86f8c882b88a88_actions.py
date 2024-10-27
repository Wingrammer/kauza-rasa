
from .actions import KauzaApiCallAction

from typing import Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
    


class Create_Business_2(KauzaApiCallAction):
    def __init__(self):
        super().__init__()
        self.agent_config_action = {'id': '6675a8c887b91cceb8be74fb', 'name': 'Create_Business_2', 'send_domain': False, 'intent': 'string', 'active_loop': 'create_business_form', 'condition': [{}], 'action_type': 'KauzaApiCallAction', 'curl_template': '', 'response': None, 'events': None, 'query_slot': 'string', 'created_by': 'af505b53-523b-4188-8cfa-6d767ee60283', 'updated_by': 'af505b53-523b-4188-8cfa-6d767ee60283', 'tenant_id': 'e8308caa-c5f3-4554-9293-571333556f68', 'config_id': '6600df886c86f8c882b88a88'}

    def name(self) -> Text:
        return "create_business_2"


