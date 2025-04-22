import json
import datetime
import json
import builtins
import re


def process_final_dict(filtered_dict, names_lookup={}):
    def replace_names_with_ids(filtered_dict):
        for key, value in filtered_dict.items():
            if isinstance(value, dict):
                replace_names_with_ids(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        replace_names_with_ids(item)
            else:
                if "_name" in key:
                    print(key)
                    key_type = key.split("_name")[0]
                    if not key_type in names_lookup:
                        names_lookup[key_type] = {value: key_type + "_option1"}
                        filtered_dict[key] = key_type + "_option1"
                    elif not value in names_lookup[key_type]:
                        num_options = len(names_lookup[key_type])
                        names_lookup[key_type][value] = (
                            key_type + f"_option{num_options+1}"
                        )
                        filtered_dict[key] = key_type + f"_option{num_options+1}"
                    else:
                        filtered_dict[key] = names_lookup[key_type][value]

    replace_names_with_ids(filtered_dict)
    return filtered_dict, names_lookup


def is_valid_type(type_str):
    ### check if it is a valid type
    if "datetime" in type_str:
        return True
    return hasattr(builtins, type_str) and isinstance(getattr(builtins, type_str), type)


def handle_datetime(string_to_check):
    try:
        datetime.date.fromisoformat(string_to_check)
        return True
    except:
        return False


def unflatten_json(flattened_data):
    unflattened_data = {}

    for key, value in flattened_data:
        keys = key.split(".")
        d = unflattened_data
        for k in keys[:-1]:
            if "[" in k:
                k = k.split("[")[0]
                if k not in d:
                    d[k] = []
                index = int(keys[keys.index(k) + 1].split("[")[1].split("]")[0])
                while len(d[k]) <= index:
                    d[k].append({})
                d = d[k][index]
            else:
                if k not in d:
                    d[k] = {}
                d = d[k]
        if keys[-1] not in d:
            d[keys[-1]] = value
        else:
            if isinstance(d[keys[-1]], list):
                d[keys[-1]].append(value)
            else:
                d[keys[-1]] = [d[keys[-1]], value]

    return unflattened_data


def combine_keys_with_indices(flattened_data):
    indexed_dict = {}
    other_data = []

    for key, value in flattened_data:
        if "[" in key:
            base_key = key.split("[")[0]
            index = int(key.split("[")[1].split("]")[0])
            sub_key = key.split(".", 1)[1]
            if base_key not in indexed_dict:
                indexed_dict[base_key] = {}
            if index not in indexed_dict[base_key]:
                indexed_dict[base_key][index] = {}
            indexed_dict[base_key][index][sub_key] = value
        else:
            other_data.append((key, value))

    combined_data = [
        (base_key, [indexed_dict[base_key][i] for i in sorted(indexed_dict[base_key])])
        for base_key in indexed_dict
    ]
    return combined_data + other_data


def remove_indices(text):
    # Use regular expression to find and remove indices in square brackets
    return re.sub(r"\[\d+\]", "", text)


def find_index(text):
    # Use regular expression to find the index in square brackets
    match = re.search(r"\[(\d+)\]", text)
    if match:
        return int(match.group(1))
    return None


def check_compliance_to_type(response_value, supported_type):
    """
    check whether types match
    """
    if supported_type == "int":
        supported_types = ["int", "float"]
    elif supported_type == "float":
        supported_types = ["int", "float"]
    else:
        supported_types = [supported_type]

    comply = False
    if response_value == None:
        return True
    for supported_type in supported_types:
        if "datetime" in supported_type:
            return handle_datetime(response_value)
        elif eval(supported_type) == str:
            return True
        elif isinstance(response_value, str):
            comply = comply or isinstance(eval(response_value), eval(supported_type))
        else:
            comply = comply or isinstance(response_value, eval(supported_type))
    return comply


def get_key_values_language(language_dict):
    """
    this flattens the language to parent.parent: value
    """
    items = {}

    def flatten_dict(d, parent_key="", sep="."):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                flatten_dict(v, new_key, sep=sep)
            else:
                items[new_key] = v

    flatten_dict(language_dict)

    return items


def get_key_values_response(response_dict):
    """
    this flattens the response to parent.parent: value
    if it is a list it will be parent[index].parent: value
    """
    items = []

    def flatten_dict(d, parent_key="", sep="."):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                flatten_dict(v, new_key, sep=sep)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        flatten_dict(item, f"{new_key}[{i}]", sep=sep)
                    else:
                        if v:
                            items.append((new_key, v))
            else:
                if v:
                    items.append((new_key, v))

    flatten_dict(response_dict)
    return items


def compare_keys(supported_language, repsponse):
    """
    this checks whether keys match
    """
    correct_key_value_pairs = []
    for item in repsponse:
        if remove_indices(item[0]) in supported_language:
            correct_key_value_pairs.append(item)
    return correct_key_value_pairs


def compare_values(key_value_pair_response, predefined_language_flattened):
    """
    this checks whether values match
    """
    try:
        key_response, value_response = key_value_pair_response
        key_response = remove_indices(key_response)
        language_supported_value = predefined_language_flattened[key_response]

        new_list_responses = []

        # check multiple choices
        if isinstance(language_supported_value, list):
            if isinstance(value_response, list):
                for response in value_response:
                    if response in language_supported_value:
                        new_list_responses.append(response)
            else:
                if not value_response in language_supported_value:
                    return False, new_list_responses

        # check other types
        else:
            language_supported_value = (
                language_supported_value.replace("{", "")
                .replace("}", "")
                .replace("Type:", "")
            )
            ### this is in case the value is a pattern
            supported_parts = [i.strip() for i in language_supported_value.split(" ")]
            if len(supported_parts) > 1:
                value_response = [i.strip() for i in value_response.split(" ")]
                ## if it is a text pattern it should be of the same length
                if not len(value_response) == len(supported_parts):
                    return False, new_list_responses
            else:
                value_response = [value_response]

            for i in range(len(supported_parts)):
                if is_valid_type(supported_parts[i].strip()):
                    if not check_compliance_to_type(
                        value_response[i], supported_parts[i].strip()
                    ):
                        return False, new_list_responses
                elif not value_response[i].strip() == supported_parts[i].strip():
                    return False, new_list_responses
        return True, new_list_responses
    except:
        return False, []


def check_compliance(predefined_language: str, response: str):
    """
    this checks whether keys and values match the language
    it removes the entries that do not match
    """
    predefined_language = json.loads(predefined_language)
    response = json.loads(response.split("```json")[-1].split("```")[0].strip())

    # flatten the data
    predefined_language_flattened = get_key_values_language(predefined_language)
    response_flattened = get_key_values_response(response)

    correct_keys_items = compare_keys(predefined_language_flattened, response_flattened)

    correct_value_items = []
    for key_value_response in correct_keys_items:
        complies, new_list = compare_values(
            key_value_response, predefined_language_flattened
        )
        if new_list:
            correct_value_items.append((key_value_response[0], new_list))
        elif complies:
            correct_value_items.append(key_value_response)

    # Combine keys with indices into unified keys
    combined_data = combine_keys_with_indices(correct_value_items)

    # Unflatten the data
    unflattened_data = unflatten_json(combined_data)

    return unflattened_data


def process_final_dict(filtered_dict: dict, names_lookup: dict = {}):
    """
    this updates the dict of names to IDs, and also replaces the names with IDs
    """

    def replace_names_with_ids(filtered_dict):
        for key, value in filtered_dict.items():
            if isinstance(value, dict):
                replace_names_with_ids(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        replace_names_with_ids(item)
            else:
                if "_name" in key:
                    key_type = key.split("_name")[0]
                    if not key_type in names_lookup:
                        names_lookup[key_type] = {value: key_type + "_option1"}
                        filtered_dict[key] = key_type + "_option1"
                    elif not value in names_lookup[key_type]:
                        num_options = len(names_lookup[key_type])
                        names_lookup[key_type][value] = (
                            key_type + f"_option{num_options+1}"
                        )
                        filtered_dict[key] = key_type + f"_option{num_options+1}"
                    else:
                        filtered_dict[key] = names_lookup[key_type][value]

    replace_names_with_ids(filtered_dict)
    return filtered_dict, names_lookup
