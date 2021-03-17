import json

def main(models):
    file_name = "trading_results_"
    pairs_dict = {}
    payoffs_per_pair_dict = {}
    payoffs_per_day_dict = {}

    for model in models:
        pairs_dict[model] = []
        payoffs_per_pair_dict[model] = []
        payoffs_per_day_dict[model] = []

        file = file_name + model + ".json"
        with open(file) as json_file:
            data = json.load(json_file)

        pairs_dict[model] = data["pairs_list"]
        payoffs_per_pair_dict[model] = data["payoffs_per_pair_list"]
        payoffs_per_day_dict[model] = data["payoffs_per_day_list"]

    return pairs_dict, payoffs_per_pair_dict, payoffs_per_day_dict