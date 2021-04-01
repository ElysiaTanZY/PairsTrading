import json


def main(models):
    file_name = "../Results/trading_results_"
    pairs_dict = {}
    payoffs_per_pair_dict = {}
    payoffs_per_day_dict = {}
    num_outliers_dict = {}       # Only for DBSCAN models

    for model in models:
        model = str(model)
        pairs_dict[model] = []
        payoffs_per_pair_dict[model] = []
        payoffs_per_day_dict[model] = []

        file = file_name + model + ".json"
        with open(file) as json_file:
            data = json.load(json_file)

        pairs_dict[model] = data["pairs_list"]
        payoffs_per_pair_dict[model] = data["payoffs_per_pair_list"]
        payoffs_per_day_dict[model] = data["payoffs_per_day_list"]

        try:
            num_outliers_dict[model] = data["num_outliers_list"]
        except:
            pass

    return pairs_dict, payoffs_per_pair_dict, payoffs_per_day_dict, num_outliers_dict