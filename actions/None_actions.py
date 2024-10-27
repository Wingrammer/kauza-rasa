from typing import Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests


from typing import Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests



    class payment_by_foxolz(KauzaApiCallAction):
        def __init__(self):
            super().__init__()
            self.agent_config_action = {'id': None, 'name': 'payment_by_foxolz', 'send_domain': True, 'intent': 'string', 'active_loop': 'payment_form', 'condition': [{}], 'action_type': 'KauzaApiCallAction', 'curl_template': 'curl -H \'Content-Type: application/json\' -X POST -d \'{"phone_phone": {{ phone_phone }}, "customer_email": {{ customer_email }}, "password": {{ password }}, "invoice_token": {{ invoice_token }}}\' \'https://app.paydunya.com/sandbox-api/v1/softpay/checkout/make-payment\\\'', 'response': None, 'events': None, 'query_slot': 'string', 'created_by': 'af505b53-523b-4188-8cfa-6d767ee60283', 'updated_by': 'af505b53-523b-4188-8cfa-6d767ee60283', 'tenant_id': 'e8308caa-c5f3-4554-9293-571333556f68', 'config_id': 'None'}
        
        def name(self) -> Text:
            return "payment_by_foxolz"
    