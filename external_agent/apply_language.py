predefined_input_firewall_intro = f"""
You are in the middle of the conversation. You previously worked on a response. You should now format it.

You have to structure your conversation and any outgoing response you are directing to the {{AI assistant}} in a very specific format.

This is a protocol agreed upon between you and the {{AI assistant}}. You will be given a long list. Consider it a specific "language" you have to abide by.

Basically, you should transform the answer to specific pairs of {{keys}} and {{values}}.
You must select the {{keys}} from this predefined {{Language}}. You should map the free form text to the closest corresponding key {{keys}} and {{values}} pairs from this {{Language}}. 

The {{values}} have types that are also specified in this {{Language}}. They can either be:

- Multiple choices you select from, you may select only one or more depending on the situation. Return the {{values}} as list containing only the choices you selected. 

- Specific python-like data types. For example, Type:datetime, Type:int, Type:float. You must abide by these data types. Anything that does not follow this will be rejected by the {{AI assistant}}. Follow the format specific for Type:datetime.

- Patterns of strings and data types. For example, to denote a range "{{Type:float}} to {{Type:float}}". Again, you must very strictly follow this pattern and match the string formatting and data types. 

- {{keys}} that have {{values}} of type "Type:bool" means either: 1) you are requesting an action or information from the {{AI assistant}}. In this case, this {{key}} must have a {{value}} of "True". 2) you are giving information to the {{AI assistant}} for example to confirm the status of booking. In this case, the {{value}} can either be "True" or "False" according to what has been said in the response.

- You are allowed to use free-from text with the {{keys}} that have a type of "Type:str" only, however note that these {{values}} will be replaced by an id (for example, you can include the name of a city, hotel, service provider, etc., but these will be replaced by the {{AI assistant}} to "destination_option1", "accomodation_option1", and so on. Your free-form text should only be names of options. For example, if you put a destination name (e.g., Paris) as {{value}} in the {{key}} destination , it will be replaced by destination1, and so on for any new destination names you specify.

- In order to maintain consistency in these identifiers, the {{AI assistant}} will maintain a programmable look-up table of {{"destination 1": "Paris"}}. You have to always make sure you use the same names (Type:str fields) (for example, names of hotels or destinations corresponding to the same option should be exactly the same throughout the conversation). In this example, if you previously said "Paris", you must not now say "Paris, France". You will be given a list of the names you have used in order to make sure you are consistent. 

- IMPORTANT: In the pre-constructed language, some {{keys}} and {{values}} work as pointers. For example, if you want to associate an accommodation option with a destination, you will find under the "accommodation" corresponding {{keys}} a key about {{destination}}. If the {{destination}} information is not present in the response, then it probably has been mentioned in the history and the {{AI assistant}} has selected a specific {{destination}} already and it is now asking for more options related to that. In this case, you can leave out the {{destination}} key.

- IMPORTANT: You don't have to use all {{keys}} from the {{Language}}. You should be very selective in mapping the current free-form text that you will receive at one point to a specific {{key}} following the rules stated earlier. 

- IMPORTANT: {{keys}} under "requested_information" or "requested_actions" must not have a {{value}} of false in the transformed answer. The {{keys}} must be there in the transformed answer with {{value}} of true if they are mentioned in the response, otherwise, they must not be in the transformed answer. Think of them as flags. 

- IMPORTANT: "requested_information" or "requested_actions" also includes suggestions given in the response. They don't need to be strictly required. 

- IMPORTANT: Don't include any {{key}} with {{value}} such as "null". The information/requests is simply in the response and should be transformed, otherwise if it is not there then the correponding {{key}} and {{value}} are irrelevant. 

- IMPORTANT: You must not make up information that was not said in the response. Your role is just to transform. The {{keys}} should very accurately reflect the current answer that you have to transform. In a previous interaction, you already had an extensive database of options you constructed your response from. Therefore, any information that is not in the response is irrelevant. The {{Language}} is a superset of everything you may need, not everything you must use. 

- IMPORTANT: You have to know that anything that does not exactly and strictly follow the {{Language}} with result in a complete failure!!!

"""


predefined_input_firewall_turn = """You will be given: The {{Langauge}} and the {{current_input}} you should transform. 

The {{Language}}: {}
The {{current_input}}: {}
These are the previous used {{names}} that you must be consistent with (will be empty if no names were used before): {} 

First, provide a step-by-step analysis of what {{keys}} and {{values}} you should select from the {{Language}} to very accurately reflect the {{current_input}} Then generate the final answer. You must generate the response in a JSON format according to the {{Language}}. Make sure the "Types" closely follow the corresponding Python types. Make sure no requests have {{values}} of "False". Make sure you maintain consistency with previous {{names}}. Use the following format:

ANALYSIS: 

FINAL ANSWER: 

"""
