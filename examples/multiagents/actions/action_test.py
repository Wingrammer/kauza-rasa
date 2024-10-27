import uncurl
import requests

print(uncurl.parse("curl 'https://pypi.python.org/pypi/uncurl' -H 'Accept-Encoding: gzip,deflate,sdch'"))
resp = eval(uncurl.parse("curl 'https://pypi.python.org/pypi/uncurl' -H 'Accept-Encoding: gzip,deflate,sdch'"))
print(resp.text)


import pytest
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted
from .actions import KauzaApiCallAction, KauzaDocumentQueryAction, KauzaTicketAction, ActionSessionStart
import requests
from unittest.mock import patch

@pytest.fixture
def dispatcher():
    return CollectingDispatcher()

@pytest.fixture
def tracker():
    return Tracker(
        sender_id="22893461083-NmVjYTI2OTUtNjAzNi00MTFmLWEzMTQtNDk3YWFhZmYzMjQxLTY2MGU3NzYwNTkxNDJlZTk5YzgwNWQ2Yw==",
        slots={
            "total_amount": 5000,
            "description": "Chaussure VANS dernier modèle",
            "store_name": "Magasin le Choco",
            "phone_number": "97403627",
            "customer_email": "marnel.gnacadja@paydunya.com",
            "password": "Miliey@2121",
            "invoice_token": "test_6BaZCm7FXS"
        },
        latest_message={"text": "Generate payment token"},
        events=[],
        paused=False,
        followup_action=None,
        active_loop=None,
        latest_action_name=None
    )

@pytest.fixture
def domain():
    return {}

@pytest.mark.asyncio
async def test_kauza_api_call_action(dispatcher, tracker, domain):
    action = KauzaApiCallAction()
    with patch.object(requests, 'get') as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            "actions": [{
                "curl_template": '''
                curl -H "Content-Type: application/json" \
                -H "PAYDUNYA-MASTER-KEY: wQzk9ZwR-Qq9m-0hD0-zpud-je5coGC3FHKW" \
                -H "PAYDUNYA-PRIVATE-KEY: test_private_rMIdJM3PLLhLjyArx9tF3VURAF5" \
                -H "PAYDUNYA-TOKEN: IivOiOxGJuWhc5znlIiK" \
                -X POST -d '{"invoice": {"total_amount": {{total_amount}}, "description": "{{description}}"},"store": {"name": "{{store_name}}"}}' \
                "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create"
                '''
            }]
        }
        with patch('uncurl.parse', return_value="requests.post('https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create', json={'invoice': {'total_amount': 5000, 'description': 'Chaussure VANS dernier modèle'}, 'store': {'name': 'Magasin le Choco'}}, headers={'Content-Type': 'application/json', 'PAYDUNYA-MASTER-KEY': 'wQzk9ZwR-Qq9m-0hD0-zpud-je5coGC3FHKW', 'PAYDUNYA-PRIVATE-KEY': 'test_private_rMIdJM3PLLhLjyArx9tF3VURAF5', 'PAYDUNYA-TOKEN': 'IivOiOxGJuWhc5znlIiK'})"):
            events = await action.run(dispatcher, tracker, domain)
            assert len(events) == 0

@pytest.mark.asyncio
async def test_kauza_document_query_action(dispatcher, tracker, domain):
    action = KauzaDocumentQueryAction()
    with patch.object(requests, 'post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.text = "Response from RAG endpoint"
        events = await action.run(dispatcher, tracker, domain)
        assert dispatcher.messages[0]['text'] == "Response from RAG endpoint"

@pytest.mark.asyncio
async def test_kauza_ticket_action(dispatcher, tracker, domain):
    action = KauzaTicketAction()
    with patch.object(requests, 'post') as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.text = "Response from RAG endpoint"
        events = await action.run(dispatcher, tracker, domain)
        assert dispatcher.messages[0]['text'] == "Response from RAG endpoint"

@pytest.mark.asyncio
async def test_action_session_start(dispatcher, tracker, domain):
    action = ActionSessionStart()
    with patch.object(action, 'create_ticket_in_system', return_value="T123"):
        events = await action.run(dispatcher, tracker, domain)
        assert dispatcher.messages[0]['text'] == "Ticket T123 has been created for the session start."
        assert events[0] == SessionStarted()
        assert events[-1] == ActionExecuted("action_listen")