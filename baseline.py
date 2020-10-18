import pandas as pd
import matplotlib as plt
import statsmodels as st

# Data Files
exchange_1 = pd.read_csv("./Updated files/Exchange1update.csv")
exchange_1["date"] = exchange_1.Date.apply(lambda x: exchange_1.to_datetime(x).strftime('%d/%m/%Y %H:%M')).dt.date

exchange_2 = pd.read_csv("./Updated files/Exchange2update.csv")
exchange_2["date"] = exchange_2.Date.apply(lambda x: exchange_2.to_datetime(x).strftime('%d/%m/%Y %H:%M')).dt.date

exchange_3 = pd.read_csv("./Updated files/Exchange3update.csv")
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

    if start_date.dt.dayofweek == 5:
        start_date.apply(pd.DateOffset(3))
    else:
        start_date.apply(pd.DateOffset(1))

    end_date = pd.datetime.date(_start_year_form + 2, 12, 31)

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


def cointegration(_possible_pairs):
    # Test pairs for cointegration and return cointegrated pairs
    # Normalise price series before testing for cointegration
    # TODO: Heat map???
    selected_pairs = []

    relevant_cols = ['date', 'PRC']

    for i in range(0, len(_possible_pairs)):
        pair_one, pair_two = _possible_pairs[i]       # Exchange, Share code, start row, end row

        pair_one_prices = data[pair_one[0]].iloc[pair_one[1]:pair_one[2] + 1]
        pair_one_price_series = pd.DataFrame(pair_one_prices, columns=relevant_cols)

        pair_two_prices = data[pair_two[0]].iloc[pair_two[1]:pair_two[2] + 1]
        pair_two_price_series = pd.DataFrame(pair_two_prices, columns=relevant_cols)

        # Plot time series
        ax = pair_one_price_series.plot(x='date', y='PRC')
        pair_two_price_series.plot(ax=ax)
        plt.show()

        # Test for co-integration
        coint_t, pvalue, crit_value = st.coint(pair_one_price_series['PRC'], pair_two_price_series['PRC'])

        if pvalue < 0.05:
            selected_pairs.append(_possible_pairs[i])

    return selected_pairs


def trade(_cointegrated_pairs, _start_year_trade):
    # Trade cointegrated pairs during trading period
    # Threshold: 2 SD away from mean
    # For shares that are delisted during the holding period, the position is immediately closed using the delisting returns
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
        cointegrated_pairs = cointegration(possible_pairs)
        trade(cointegrated_pairs, start_year + 3)

