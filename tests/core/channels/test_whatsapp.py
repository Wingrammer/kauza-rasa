from whatsapp import Message, WhatsApp as MessengerClient

yourclient = MessengerClient(token="EAAFIyXvLsLQBO9tsQdJqCJH4Ark2VM871PhnuymfZCStHXtzNWZCTXrFle8gjdxLWtqWD0QIK2Pvj64BGbEDZC31FDICqLNzGCDEpMfOzTibSSzZCqmH7MNt4NRTZA5F05WqaTbRnF4NEYzC8ZC7STjgOlk9OGMsGZBSl7LrnxMeGbV4NPbxDxHO1IKMDDs7KRisFay7XEYoYI1beusu5Y6O55mnyhXzkIiv2QZD", phone_number_id="226912030500829")

# message = Message(instance=yourclient, content="Hello world!", to="22893461083") # this is your message instance
# message.send() # this will send the message
new_message = Message(instance=yourclient, id="HBgLMjI4OTM0NjEwODMVAgASGBIzM0RGNUU3OTE2RDA0QzJGQjEA", data={"entry":[{"changes":[{"value":{'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '22893813095', 'phone_number_id': '226912030500829'}, 'contacts': [{'profile': {'name': 'WiN!'}, 'wa_id': '22893461083'}], 'messages': [{'from': '22893461083', 'id': 'wamid.HBgLMjI4OTM0NjEwODMVAgASGBIzM0RGNUU3OTE2RDA0QzJGQjEA', 'timestamp': '1708563917', 'text': {'body': 'Hello'}, 'type': 'text'}]}}]}]})
print(new_message.reply("new_message"))
