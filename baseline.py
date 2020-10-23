import numpy as np
import pandas as pd
import matplotlib as plt
import statsmodels as st

# Data Files
exchange_1 = pd.read_csv("Updated/Exchange1update.csv")
exchange_1["date"] = exchange_1.Date.apply(lambda x: exchange_1.to_datetime(x).strftime('%d/%m/%Y %H:%M')).dt.date

exchange_2 = pd.read_csv("Updated/Exchange2update.csv")
exchange_2["date"] = exchange_2.Date.apply(lambda x: exchange_2.to_datetime(x).strftime('%d/%m/%Y %H:%M')).dt.date

exchange_3 = pd.read_csv("Updated/Exchange3update.csv")
exchange_3["date"] = exchange_3.Date.apply(lambda x: exchange_3.to_datetime(x).strftime('%d/%m/%Y %H:%M')).dt.date

data = [exchange_1, exchange_2, exchange_3]
shares = []


def get_shares():
    # Get the code of all shares that are available in the exchanges
    for i in range(0, 3):
        curr_share = data[i].iloc[0]['PERMNO']
        share_list = []

        for j, row in data[i].iterrows():
            if row['PERMNO'] != curr_share:
                share_list.append(curr_share)
                curr_share = row['PERMNO']

        shares.append(share_list)
        print(share_list)


def find_shares(_start_year_form):
    # Sieves out all stocks that have prices for all days within the formation period
    chosen_shares = []
    start_date = pd.datetime.date(_start_year_form, 1, 1)
    if start_date.dt.dayofweek == 7:
        start_date.apply(pd.DateOffset(1))
    elif start_date.dt.dayofweek == 6:
        start_date.apply(pd.DateOffset(2))

    end_date = pd.datetime.date(_start_year_form + 2, 12, 31)

    if end_date.dt.dayofweek == 7:
        end_date.apply(pd.DateOffset(-2))
    elif end_date.dt.dayofweek == 6:
        end_date.apply(pd.DateOffset(-1))

    for i in range (0, 3):
        curr_date = start_date
        curr_share = shares[i][0]
        count = 1
        start_index = 0
        is_start = False

        for j, row in data[i].iterrows():
            if row['PERMNO'] == curr_share:
                if is_start:
                    start_index = j

                if row['date'] == curr_date:
                    if curr_date.dt.dayofweek == 5:
                        curr_date.apply(pd.DateOffset(3))
                    else:
                        curr_date.apply(pd.DateOffset(1))

                elif row['date'] == end_date:
                    chosen_shares.append([i, curr_share, start_index, j])

                    curr_share = shares[i][count]
                    count += 1
                    curr_date = start_date
                    is_start = True

                else:
                    curr_share = shares[i][count]
                    count += 1
                    curr_date = start_date
                    is_start = True

        print(chosen_shares)

    return chosen_shares


def form_pairs(_relevant_shares):
    # Generate all the relevant pairs
    pairs = []
    for i in range(0, len(_relevant_shares)):
        for j in range(i, len(_relevant_shares)):
            pairs.append((_relevant_shares[i], _relevant_shares[j]))

    print(pairs)
    return pairs

#TODO: Not sure whether should rank beforehand and only pick the first few
def rank_pairs(_possible_pairs):
    # Rank the pairs based on sum of squared difference between normalised price series
    relevant_cols = ['date', 'LOG_PRC']
    for i in range(0, len(_possible_pairs)):
        pair_one, pair_two = _possible_pairs[i]

        pair_one_prices = data[pair_one[0]].iloc[pair_one[1]:pair_one[2] + 1]
        pair_one_price_series = pd.DataFrame(pair_one_prices, columns=relevant_cols)

        pair_two_prices = data[pair_two[0]].iloc[pair_two[1]:pair_two[2] + 1]
        pair_two_price_series = pd.DataFrame(pair_two_prices, columns=relevant_cols)

    return


def cointegration(_ranked_pairs):
    # Test pairs for cointegration and return cointegrated pairs
    # Normalise price series before testing for cointegration
    # TODO: Heat map??? and stop once hit 20 actually check how many pairs are there in total and decide number from there
    selected_pairs = []

    relevant_cols = ['date', 'LOG_PRC']

    for i in range(0, len(_ranked_pairs)):
        pair_one, pair_two = _ranked_pairs[i]       # Exchange, Share code, start row, end row

        pair_one_prices = data[pair_one[0]].iloc[pair_one[1]:pair_one[2] + 1]
        pair_one_price_series = pd.DataFrame(pair_one_prices, columns=relevant_cols)

        pair_two_prices = data[pair_two[0]].iloc[pair_two[1]:pair_two[2] + 1]
        pair_two_price_series = pd.DataFrame(pair_two_prices, columns=relevant_cols)

        # Plot time series
        ax = pair_one_price_series.plot(x='date', y='LOG_PRC')
        pair_two_price_series.plot(ax=ax)
        plt.show()

        # Test for co-integration
        coint_t, pvalue, crit_value = st.coint(pair_one_price_series['LOG_PRC'], pair_two_price_series['LOG_PRC'])

        if pvalue < 0.05:
            spread = pair_one_price_series['LOG_PRC'] - pair_two_price_series['LOG_PRC']
            mean = spread.mean()
            std = spread.std()
            pair = (pair_one[0], pair_one[1], pair_one[3] + 1, pair_two[0], pair_two[1], pair_two[3] + 1, mean, std)
            selected_pairs.append(pair)

    return selected_pairs


def trade(_cointegrated_pairs, _start_year_trade):
    # Trade cointegrated pairs during trading period
    # Threshold: 2 SD away from mean
    # For shares that are delisted during the holding period, the position is immediately closed using the delisting returns
    for i in range(0, len(_cointegrated_pairs)):
        exchange_one, code_one, start_one, exchange_two, code_two, start_two, mean, std = _cointegrated_pairs[i]

        start_date = pd.datetime.date(_start_year_trade, 1, 1)
        if start_date.dt.dayofweek == 7:
            start_date.apply(pd.DateOffset(1))
        elif start_date.dt.dayofweek == 6:
            start_date.apply(pd.DateOffset(2))

        end_date = pd.datetime.date(_start_year_trade, 12, 31)
        if end_date.dt.dayofweek == 7:
            end_date.apply(pd.DateOffset(-2))
        elif end_date.dt.dayofweek == 6:
            end_date.apply(pd.DateOffset(-1))

        open = False
        position = [] # Element one is short, element two is long
        returns = []
        num_trades = 0

        curr_date = start_date

        while (curr_date <= end_date):
            date_one = data[exchange_one].iloc[start_one]['date']
            current_one = data[exchange_one].iloc[start_one]['PERMNO']

            date_two = data[exchange_two].iloc[start_two]['date']
            current_two = data[exchange_two].iloc[start_two]['PERMNO']

            if (date_one == date_two and current_one == code_one and current_two == code_two):
                norm_price_one = data[exchange_one].iloc[start_one]['LOG_PRC']
                norm_price_two = data[exchange_two].iloc[start_two]['LOG_PRC']

                spread = norm_price_one - norm_price_two

                if open and abs(spread - mean) < 2*std:
                    # close position and calculate returns
                    price_one = data[exchange_one].iloc[start_one]['PRC']
                    price_two = data[exchange_two].iloc[start_two]['PRC']

                    short, long = position[0], position[1]

                    if (short[0] == 1):
                        return_one = (short[2] - price_one) * short[1]
                        return_two = (price_two - long[2]) * long[1]
                    elif (short[0] == 2):
                        return_two = (short[2] - price_two) * short[1]
                        return_one = (price_one - long[2]) * long[1]

                    returns.append(return_one + return_two)
                    open = False
                elif not open and abs(spread - mean) > 2*std:
                    # one dollar short in higher priced stock and one dollar long in lower priced stock
                    price_one = data[exchange_one].iloc[start_one]['PRC']
                    price_two = data[exchange_two].iloc[start_two]['PRC']

                    if price_one > price_two:
                        position.append((1, 1 / price_one, price_one))
                        position.append((2, 1 / price_two, price_two))
                    elif price_one <= price_two:
                        position.append((2, 1 / price_two, price_two))
                        position.append((1, 1 / price_one, price_one))

                    num_trades += 1
                    open = True
            elif current_one != code_one or current_two != code_two or date_one != date_two:
                if open:
                    price_one = data[exchange_one].iloc[start_one]['PRC']
                    price_two = data[exchange_two].iloc[start_two]['PRC']

                    short, long = position[0], position[1]

                    if (short[0] == 1):
                        return_one = (short[2] - price_one) * short[1]
                        return_two = (price_two - long[2]) * long[1]
                    elif (short[0] == 2):
                        return_two = (short[2] - price_two) * short[1]
                        return_one = (price_one - long[2]) * long[1]

                    delisting_code_one = data[exchange_one].iloc[start_one]['DLSTCD']
                    delisting_code_two = data[exchange_two].iloc[start_two]['DLSTCD']

                    if (delisting_code_one != 100):
                        # Stock one was delisted
                        return_one = data[exchange_one].iloc[start_one]['DLRET']

                    elif (delisting_code_two != 100):
                        # Stock two was delisted
                        return_two = data[exchange_two].iloc[start_two]['DLRET']

                    returns.append(return_one + return_two)
                    open = False
                    continue

            if curr_date.dt.dayofweek == 5:
                curr_date.apply(pd.DateOffset(3))
            else:
                curr_date.apply(pd.DateOffset(1))

            start_one += 1
            start_two += 1

        if open:
            # close position based on last trading day
            start_one -= 1
            start_two -= 1

            price_one = data[exchange_one].iloc[start_one]['PRC']
            price_two = data[exchange_two].iloc[start_two]['PRC']

            short, long = position[0], position[1]

            if (short[0] == 1):
                return_one = (short[2] - price_one) * short[1]
                return_two = (price_two - long[2]) * long[1]
            elif (short[0] == 2):
                return_two = (short[2] - price_two) * short[1]
                return_one = (price_one - long[2]) * long[1]

            returns.append(return_one + return_two)

        # TODO: Calculate statistics


    return


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Formation period: 3 years + Trading period: 1 year (Rolling basis)
    # Start date: 1 Jan 2000
    start_year = 2000
    get_shares()

    for start_year in range(2000, 2017):
        relevant_shares = find_shares(start_year)
        possible_pairs = form_pairs(relevant_shares)         # exchange number, share code, start row, end row
        #ranked_pairs = rank_pairs(possible_pairs)
        cointegrated_pairs = cointegration(possible_pairs)
        trade(cointegrated_pairs, start_year + 3)

