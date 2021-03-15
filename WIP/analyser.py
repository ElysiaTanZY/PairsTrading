import json

from WIP import analyse_model, generate_charts

models = ["baseline", "dbscan", "fuzzy", "kmedoids"]

if __name__ == '__main__':
    file_name = "trading_results_"
    pairs_list = {}
    payoffs_per_pair_list = {}
    payoffs_per_day_list = {}

    for model in models:
        pairs_list[model] = []
        payoffs_per_pair_list[model] = []
        payoffs_per_day_list[model] = []

        file = file_name + model + ".json"
        with open(file) as json_file:
            data = json.load(json_file)

        pairs_list[model] = data["pairs_list"]
        payoffs_per_pair_list[model] = data["payoffs_per_pair_list"]
        payoffs_per_day_list[model] = data["payoffs_per_day_list"]

    fully_invested_return_list = {}
    identified_pairs_list = {}
    traded_pairs_list = {}

    for model in models:
        print(model)
        fully_invested_return_list[model], identified_pairs_list[model], traded_pairs_list[model] = analyse_model.main(pairs_list[model], payoffs_per_pair_list[model], payoffs_per_day_list[model], model)
        print("\n")

    generate_charts.main(identified_pairs_list, traded_pairs_list, fully_invested_return_list, models)
