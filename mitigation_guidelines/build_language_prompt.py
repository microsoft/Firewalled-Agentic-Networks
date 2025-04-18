language_tag = "TEMPLATE"

build_language_prompt = """
You are auditing a conversation between an {AI assistant} and an {external agent}.
The {AI assistant} is tasked with booking a vacation for the {user}.
The {external agent} is a travel agency.

The {AI assistant} is engaging in a conversation with the {external agent} to make bookings and plan the full package including flights, hotel, activities, restaurants, etc.

The {external agent} is asking the {AI assistant} for questions and giving it choices. Additionally, the {external agent} is asking the {AI assistant} for information about the {user}.

Your task is to create a taxonomy of possible input variables that the {AI assistant} can accept and respond to. For example, when the {external agent} gives several hotel packages with prices, benefits, and so on, you would expand the taxonomy by the given option {“accomodation_type”: “hotel”, “price”: “X”, “currency”: “euros”, breakfast: “included”}, and so on based on all that the {external agent} has mentioned. As much as possible, the value for each field of the taxonomy (e.g., euros) would have to be also a fixed set of options that you will build out of the conversation (that cannot be changed later). The values can also be boolean. They can also be indicated by a “data type”. For example, you can say the price is expected to be a digit. Through several simulations, you will be able to build such a taxonomy (or think of it as an interface to a class and the allowed data types of each variable) of options that should be converted into a json-like template.

Very importantly, we want to minimize the natural language input fields that will be passed to the {AI assistant}. We will leave this for fields that can never be expressed except in natural language (such as the names of hotels, entities, companies, etc.). If a certain field can’t be expressed in anything except arbitrary natural language inputs that cannot be bound with a fixed set of options, you should indicate that in the value of this field.

Except names and named entities and addresses, you must not include fields in the taxonomy that require free-form sentences (that are very generic) such as "descriptions", "highlight", etc. You MUST extract from the natural language descriptions given by the {external agent} some high-level attributes, such as "outdoor": Type:bool, "sports": ["diving", "hiking"], and ONLY use this to build the taxonomy instead. Basically you need to know, ANYTHING expressed in natural language will not be given to the {AI assistant} in the first place, so if this is important for the {AI assistant} to decide, then you MUST provide enough predefined values that would express this option.

If you are indicating a data type such as string, you have to write Type:str, Type:int, Type:float, Type:datetime, etc. Think of these as python types. Type:str should be for fields with free form texts and should be used only when absolutely necessary. You could also use simple formattable strings of that would contain concrete data types such as "{Type:int} to {Type:int}" or "{Type:datetime} to {Type:datetime}" to express duration, timing, etc..

If you really have to keep something as string (such as a city name), include properties of the city as well that would have prefixed values (such as "location": ["West Europe", ... etc] "type": ["beach destination", ... etc]). You MUST reduce the fields that would have free-form text as much as possible. You must also think of how to expand the fields themselves not just the values. For example, what else may be included in the package?

Feel free to use your own knowledge in order to suggest what kind of attributes/values would work with each item even if they were not explicitely expressed in the conversations, for example, you can think of what kind of general themes and categories this field may usually be associated with. A helpful way to do that is to think, if the user was different (they are a family instead of a single traveller, what properties of options would they be interested to know about?). Expand the taxonomy as MUCH as possible in order to cover other conversations that you may have not seen. You must be proactive.

You can also assume that some fields will be grouped with others: for example, the transportation may be grouped with the destination, so there is no need to include free form fields in the transportation as well, etc.

As a rule of thumb, assume that each field would have a field as a name that would be replaced by a short identifier (e.g., activity1, name1, etc.). Everything else should not have free form natural language text.

Fields should denote given or requested information from the {external agent} to the {AI assistant}, they must not express inputs from the {AI assistant}. For example, you shouldn't include a field of the "remaining_budget" or the "user_budget" that the {AI assistant} has shared. You shouldn't also include items in the final package summary. This is not a property of destinations/hotels/activities of options shared by the {external agent}. You have to differentiate between things said in the conversation and the actual properties of items.

Don't include very very very specific values for fields that are hard to generalize to new conversations with different options.

You must also include fields that would express if something was available and now it is not, or any change of state compared to the previously shared items. This is to support referring to a previous part of the conversation.

You must also include fields related to requested information that the {external agent} is asking the {AI assistant} to share. The fields must only express the request, not the actual information or answer from the {AI assistant}. Fields expressing requested information must clearly be indicated as request via the name of the fields. Your template must clearly indicate whether this information is given by the {external agent} or requested by the {external agent}.
Requested information does not have data types because the values will not be given by the {external agent}. In this case, you must leave the values blank or boolean (for example: "is_needed": Type:bool). 

General fields such as accumulated cost across all options or fields should not be there. The cost/price is a property for each item. The {AI assistant} is responsible to do this computation of the total or remaining budget. Also, any information the {AI assistant} is giving (e.g., what preferences the user has or their conditions) must not be used to build the template. Your template is strictly based on the {external agent}. But, for example, the template may contain requests from the {external agent} asking about the user's preferences, etc.

You have to also include which information the {external agent} may request from the {AI assistant} in order to tailor the suggestions or packages.

Essentially, your template is either: information about packages, items, reservartions, etc. given by the {external agent}. Or, requests about information the {external agent} is asking from the {AI assistant}, without the actual answers. These two should be marked clearly as such.

You must include everything in json format.

"""

previous_template_prompt = """
You should first write down your observations about the questions the {{external agent}} have asked. Then if you are given a previous template that you have worked on, you should write down how you can expand it or refine it. Think also of how to expand this template based on your own knowledge. Also think of how to minimize the natural language description (Type:str), and how to already refine the template to reduce these (Type:str) items. Correct any mistakes that you have done before if you have introduced lots of (Type:str) items. You must also make sure the template reflects either information given or information requested by the {{external agent}}. It must not reflect information given or information requested by the {{AI assistant}}. Then after all of your analysis, write down the new template based on your analysis. You must not remove existing information from template. Copy anything you have not changed from the existing template.  If there is nothing new to add, just return the old template. After your analysis and notes, write the new templates by including this format: <{language_tag}> </{language_tag}>
# """

building_language_input_format = """
This is a history of a conversation between the {{AI assistant}} and the {{external_agent}}: {}
"""

building_language_output_format = f"""
You should first write down your observations about the questions the {{external agent}} have asked. Then if you are given a previous template that you have worked on, you should write down how you can expand it or refine it. If there are no changes required, just repeat the old ones. Please use the following format: <{language_tag}> </{language_tag}>
"""
