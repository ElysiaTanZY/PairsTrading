import datetime
import math
import json
import statistics
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np


def analyse_returns(returns, num_pairs_traded, num_pairs_chosen):
    # Excess returns
    return_on_committed_capital_list = []
    fully_invested_return_list = []

    for i in range(0, len(returns)):
        return_on_committed_capital_list.append(returns[i] / num_pairs_chosen[i] if num_pairs_chosen[i] > 0 else 0)
        fully_invested_return_list.append(returns[i] / num_pairs_traded[i] if num_pairs_traded[i] > 0 else 0)

    return_on_committed_capital = statistics.mean(return_on_committed_capital_list)
    fully_invested_return = statistics.mean(fully_invested_return_list)

    print("Average Return on committed capital: " + str(return_on_committed_capital))
    print("Average Fully invested return: " + str(fully_invested_return))

    print("Average num pairs traded: " + str(statistics.mean(num_pairs_traded)))
    print("Average num pairs chosen: " + str(statistics.mean(num_pairs_chosen)))

    print("Return on committed capital: ")
    print(return_on_committed_capital_list)

    # Maximum Drawdown
    '''
    mdd_list_all_years = []
    
    for year in range(0, len(returns_mdd)):
        mdd_list_year = []
        for pair in range(0, len(returns_mdd[year])):
            for trade in returns_mdd[year][pair]:
                payoff, start_short, end_short, start_long, end_long = trade

                curr_short = start_short + 1
                curr_long = start_long + 1

                payoff_list = []

                while curr_short <= end_short and curr_long <= end_long:
                    short_payoff = data.iloc[start_short]['PRC'] - data.iloc[curr_short]['PRC']
                    long_payoff = data.iloc[curr_long]['PRC'] - data.iloc[start_long]['PRC']

                    payoff = short_payoff + long_payoff
                    payoff_list.append(payoff)

                    curr_short += 1
                    curr_long += 1

                peak = 0.0
                gap = 0.0
                print(payoff_list)
                if len(payoff_list) != 0:
                    cumulative_payoff_list = [payoff_list[0]]

                    for i in range(1, len(payoff_list)):
                        cumulative_payoff_list.append(cumulative_payoff_list[i - 1] + payoff_list[i])

                    for i in range(0, len(cumulative_payoff_list)):
                        for j in range(i + 1, len(cumulative_payoff_list)):
                            temp_gap = cumulative_payoff_list[j] - cumulative_payoff_list[i]

                            if (temp_gap < gap):
                                gap = temp_gap
                                peak = cumulative_payoff_list[i]

                mdd = gap / peak if peak > 0.0 else 0
                mdd_list_year.append(mdd)

        mdd_list_all_years.append(statistics.mean(mdd_list_year))

    mdd = statistics.mean(mdd_list_all_years)
    print("Maximum drawdown: " + str(mdd))
   
    mdd_list_all_years = []
    for year in range(0, len(payoffs_mdd)):
        cumulative_payoff_list = [payoffs_mdd[year][0]]

        for i in range(1, len(payoffs_mdd[year])):
            cumulative_payoff_list.append(cumulative_payoff_list[i-1] + payoffs_mdd[year][i])

        peak = 0.0
        gap = 0.0

        for i in range(0, len(cumulative_payoff_list)):
            for j in range(i + 1, len(cumulative_payoff_list)):
                temp_gap = cumulative_payoff_list[j] - cumulative_payoff_list[i]

                if (temp_gap < gap):
                    gap = temp_gap
                    peak = cumulative_payoff_list[i]

        mdd = gap / peak if peak > 0.0 else 0
        mdd_list_all_years.append(mdd)
    
    mdd = statistics.mean(mdd_list_all_years)
    print("Maximum drawdown: " + str(mdd))
    '''
    peak = 0.0
    gap = 0.0

    cumulative_returns = [returns[0]]

    for i in range(1, len(returns)):
        cumulative_returns.append(cumulative_returns[i - 1] + returns[i])

    for i in range(0, len(cumulative_returns)):
        for j in range(i + 1, len(cumulative_returns)):
            temp_gap = cumulative_returns[j] - cumulative_returns[i]

            if (temp_gap < gap):
                gap = temp_gap
                peak = cumulative_returns[i]

    mdd = gap / peak if peak > 0.0 else 0
    print("12-mth Maximum drawdown: " + str(mdd))

    '''   
    maximum_drawdown_list = []

    for returns_series in returns_series_all:
        returns_series.sort(key=lambda returns_pair: datetime.strptime(returns_pair[1], '%m/%d/%Y'))

        peak = 0.0
        gap = 0.0
    
        cumulative_returns = [returns_series[0][0]]
    
        for i in range(1, len(returns_series)):
            cumulative_returns.append(cumulative_returns[i-1] + returns_series[i][0])
    
        for i in range(0, len(cumulative_returns)):
            for j in range(i + 1, len(cumulative_returns)):
                temp_gap = cumulative_returns[j] - cumulative_returns[i]
    
                if (temp_gap < gap):
                    gap = temp_gap
                    peak = cumulative_returns[i]
    
        mdd = gap / peak if peak > 0.0 else 0
        maximum_drawdown_list.append(mdd)
    
    max_drawdown = statistics.mean(maximum_drawdown_list)
    print("Maximum drawdown: " + str(max_drawdown))
    '''

    # Sharpe ratio
    average = statistics.mean(return_on_committed_capital_list)
    sd = statistics.stdev(return_on_committed_capital_list, average)
    risk_free_rate = generate_risk_free_rate()  # Using average of 1-year treasury yield over past 17 years
    sharpe_ratio = (average - risk_free_rate) / sd if sd > 0.0 else 0

    print("Sharpe ratio: " + str(sharpe_ratio))
    print("Standard deviation: " + str(sd))

    # Calmar ratio
    calmar_ratio = average / mdd if bool(re.search('[1-9]+', str(mdd))) else 0

    print("Calmar ratio: " + str(calmar_ratio))

    # Sortino ratio (https://www.thebalance.com/what-is-downside-deviation-4590379)
    minimal_acceptable_return = average

    downside_returns = []
    for i in range(0, len(return_on_committed_capital_list)):
        returns_subtract_mar = return_on_committed_capital_list[i] - minimal_acceptable_return

        if returns_subtract_mar < 0:
            downside_returns.append(returns_subtract_mar**2)

    downside_deviation = math.sqrt(sum(downside_returns) / len(return_on_committed_capital_list)) if len(return_on_committed_capital_list) > 0 else 0
    sortino_ratio = (average - risk_free_rate) / downside_deviation if downside_deviation > 0.0 else 0

    print("Sortino ratio: " + str(sortino_ratio))
    print("Downside deviation: " + str(downside_deviation))

    return fully_invested_return_list


def generate_risk_free_rate():
    date_cols = ['DATE']
    rates_data = pd.read_csv('../Backup/1yr_TreasuryYield(Monthly).csv', parse_dates=date_cols)  # https://fred.stlouisfed.org/series/DGS1
    rates = []

    for i, row in rates_data.iterrows():
        if row['DATE'].month == 1:
            rates.append(float(row['GS1']))

    return statistics.mean(rates) / 100


def calculate_returns(path):
    # Used to just calculate after trading is done
    results = {}

    with open(path) as json_file:
        results = json.load(json_file)

    returns = results['returns']
    num_pairs_chosen = results['pairs_chosen']
    num_pairs_traded = results['pairs_traded']

    return_on_committed_capital_list = []
    fully_invested_return_list = []

    for i in range(0, len(returns)):
        return_on_committed_capital_list.append(returns[i] / num_pairs_chosen[i] if num_pairs_chosen[i] > 0 else 0)
        fully_invested_return_list.append(returns[i] / num_pairs_traded[i] if num_pairs_traded[i] > 0 else 0)

    return_on_committed_capital = statistics.mean(return_on_committed_capital_list)
    fully_invested_return = statistics.mean(fully_invested_return_list)

    print("Average Return on committed capital: " + str(return_on_committed_capital))
    print("Average Fully invested return: " + str(fully_invested_return))

    # Maximum Drawdown
    peak = 0.0
    gap = 0.0

    cumulative_returns = [returns[0]]

    for i in range(1, len(returns)):
        cumulative_returns.append(cumulative_returns[i - 1] + returns[i])

    for i in range(0, len(cumulative_returns)):
        for j in range(i + 1, len(cumulative_returns)):
            temp_gap = cumulative_returns[j] - cumulative_returns[i]

            if (temp_gap < gap):
                gap = temp_gap
                peak = cumulative_returns[i]

    mdd = gap / peak if peak > 0.0 else 0

    print("Maximum drawdown: " + str(mdd))

    # Sharpe ratio
    average = statistics.mean(return_on_committed_capital_list)
    sd = statistics.stdev(return_on_committed_capital_list, average)
    risk_free_rate = generate_risk_free_rate()  # Using average of 1-year treasury yield over past 17 years
    sharpe_ratio = (average - risk_free_rate) / sd if sd > 0.0 else 0

    print("Sharpe ratio: " + str(sharpe_ratio))
    print("Standard deviation: " + str(sd))

    # Calmar ratio
    calmar_ratio = average / mdd if bool(re.search('[1-9]+', str(mdd))) else 0

    print("Calmar ratio: " + str(calmar_ratio))

    # Sortino ratio (https://www.thebalance.com/what-is-downside-deviation-4590379)
    minimal_acceptable_return = average

    downside_returns = []
    for i in range(0, len(return_on_committed_capital_list)):
        returns_subtract_mar = return_on_committed_capital_list[i] - minimal_acceptable_return

        if returns_subtract_mar < 0:
            downside_returns.append(returns_subtract_mar ** 2)

    downside_deviation = math.sqrt(sum(downside_returns) / len(return_on_committed_capital_list)) if len(
        return_on_committed_capital_list) > 0 else 0
    sortino_ratio = (average - risk_free_rate) / downside_deviation if downside_deviation > 0.0 else 0

    print("Sortino ratio: " + str(sortino_ratio))
    print("Downside deviation: " + str(downside_deviation))


if __name__ == '__main__':
    print("Baseline")
    calculate_returns('/Users/elysiatan/PycharmProjects/thesis/Backup/returns_baseline.json')

    print("\nDBSCAN")
    calculate_returns('/Users/elysiatan/PycharmProjects/thesis/Backup/returns_dbscan.json')

    print("\nKMEDOIDS")
    calculate_returns('/Users/elysiatan/PycharmProjects/thesis/Backup/returns_kmedoids.json')

