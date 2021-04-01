import datetime
import math
import pandas as pd
import re


trading_calendar = {2000: 252, 2001: 248, 2002: 252, 2003: 252, 2004: 252, 2005: 252, 2006: 251, 2007: 251, 2008: 253,
                   2009: 252, 2010: 252, 2011: 252, 2012: 250, 2013: 252, 2014: 252, 2015: 252, 2016: 252, 2017: 251,
                   2018: 251, 2019: 252}


def trade(chosen_pairs, trade_year, data):

    ''' Does the trading for each pair during the trade_year

    :param chosen_pairs: List of cointegrated pairs
    :param trade_year: Trading year
    :param data: Price series data
    :return: Number of pairs traded, List of payoffs made by each pair, List of payoffs obtained in each day
    '''

    print("Trading")
    payoffs_total = {}
    num_pairs_traded = {}

    payoffs_per_pair = {}
    payoffs_per_day = {}

    # Determine start of the trading period
    start_date = datetime.datetime(trade_year, 1, 1)

    # Monday = 0, Sunday = 6
    if start_date.weekday() == 6 or start_date.weekday() == 5:
        start_date = start_date + datetime.timedelta(days=2)
    elif start_date.weekday() == 4:
        start_date = start_date + datetime.timedelta(days=3)
    else:
        start_date = start_date + datetime.timedelta(days=1)

    start_date = pd.to_datetime(start_date)

    # Determine end of the trading period
    end_date = datetime.datetime(trade_year, 12, 31)

    # Monday = 0, Sunday = 6
    if end_date.weekday() == 6:
        end_date = end_date - datetime.timedelta(days=2)
    elif end_date.weekday() == 5:
        end_date = end_date - datetime.timedelta(days=1)

    end_date = pd.to_datetime(end_date)

    for key, list in chosen_pairs.items():
        payoffs_total[key] = []
        num_pairs_traded[key] = 0
        payoffs_per_pair[key] = []
        payoffs_per_day[key] = [[] for j in range(trading_calendar[trade_year])]

        for i in range(0, len(list)):
            payoffs = []
            code_one, start_one, code_two, start_two, mean, std, beta, sic_one, sic_two, speed = list[i]

            is_open = False
            is_delisted = False
            position = [] # Element one is short, element two is long
            num_trades = 0
            index = 0

            date_one = data.iloc[start_one]['date']
            current_one = data.iloc[start_one]['PERMNO']

            date_two = data.iloc[start_two]['date']
            current_two = data.iloc[start_two]['PERMNO']

            while start_date <= date_one <= end_date and start_date <= date_two <= end_date:

                # Stock delisted during trading period
                if date_one == date_two and str(current_one) == str(code_one) and str(current_two) == str(code_two):
                    if not 100 <= data.iloc[start_one]['DLSTCD'] < 200 or not 100 <= data.iloc[start_two]['DLSTCD'] < 200:
                        is_delisted = True
                        break

                    price_one = data.iloc[start_one]['PRC']
                    price_two = data.iloc[start_two]['PRC']

                    # At least one stock has missing prices during trading period --> Close on last available prices if required
                    if not bool(re.search('[1-9]+', str(price_one))) or not bool(re.search('[1-9]+', str(price_two))):
                        break

                    norm_price_one = math.log(price_one)
                    norm_price_two = math.log(price_two)

                    spread = norm_price_one - beta * norm_price_two

                    if is_open:
                        short, long = position[0], position[1]

                        if short[0] == 1:
                            diff_one = (1 / beta) - (price_one * short[1])
                            diff_two = (price_two * long[1]) - 1
                        elif short[0] == 2:
                            diff_two = beta - (price_two * short[1])
                            diff_one = (price_one * long[1]) - 1

                        temp = payoffs_per_day[key][index]
                        temp.append((diff_one + diff_two, sic_one, sic_two))
                        payoffs_per_day[key][index] = temp

                    index += 1

                    # Threshold to close positions: 0.5 SD away from mean
                    # Close position and calculate returns (Faff et al, 2016)
                    if is_open and abs(spread - mean) < 0.5*std:
                        print("Closing position")
                        print(str(abs(spread - mean)))
                        print(str(std))

                        short, long = position[0], position[1]

                        if short[0] == 1:
                            diff_one = (1 / beta) - (price_one * short[1])
                            diff_two = (price_two * long[1]) - 1
                        elif short[0] == 2:
                            diff_two = beta - (price_two * short[1])
                            diff_one = (price_one * long[1]) - 1

                        payoffs_total[key].append(diff_one + diff_two)

                        if short[0] == 1:
                            payoffs.append((diff_one + diff_two, short[3], start_one, long[3], start_two))
                        elif short[0] == 2:
                            payoffs.append((diff_one + diff_two, short[3], start_two, long[3], start_one))

                        position.clear()
                        is_open = False

                    # Threshold to open positions: 2 SD away from mean
                    # (Faff et al, 2016)
                    # If deviation is positive --> $1 long position for Stock 2 and $1/Beta short position for Stock 1
                    # If deviation is negative --> $1 long position for Stock 1 and $Beta short position for Stock 2
                    elif not is_open and abs(spread - mean) >= 2*std:
                        print("Opening position")
                        print(str(abs(spread - mean)))
                        print(str(std))

                        price_one = data.iloc[start_one]['PRC']
                        price_two = data.iloc[start_two]['PRC']

                        if (spread - mean) > 0:
                            position.append((1, (1 / beta) / price_one, price_one, start_one))
                            position.append((2, 1 / price_two, price_two, start_two))
                        elif (spread - mean) <= 0:
                            position.append((2, beta / price_two, price_two, start_two))
                            position.append((1, 1 / price_one, price_one, start_one))

                        num_trades = num_trades + 1
                        is_open = True
                else:
                    # Missing price for at least one of the stocks in the pair
                    # Break and calculate on last available aligned day if there is an open position on the pair
                    break

                start_one += 1
                start_two += 1

                date_one = data.iloc[start_one]['date']
                current_one = data.iloc[start_one]['PERMNO']

                date_two = data.iloc[start_two]['date']
                current_two = data.iloc[start_two]['PERMNO']

            # At this point, there are 3 possible scenarios
            # Scenario 1: At least one of the stock is delisted during the period
            # Scenario 2: Completed the whole trading period
            # Scenario 3: At least one of the stock has missing stock prices within the trading period
            # Scenarios 2 and 3 are handled similarly

            # close position based on last available price or delisting returns
            if is_open and is_delisted:
                short, long = position[0], position[1]

                if bool(re.search('[1-9]+', str(data.iloc[start_one]['PRC']))):
                    price_one = data.iloc[start_one]['PRC']
                    if short[0] == 1:
                        diff_one = (1 / beta) - (price_one * short[1])
                    elif short[0] == 2:
                        diff_one = (price_one * long[1]) - 1
                else:
                    if short[0] == 1:
                        return_one = data.iloc[start_one]['DLRET']
                        approx_price_one = return_one * short[2] + short[2]
                        diff_one = (1 / beta) - approx_price_one * short[1]
                    elif short[0] == 2:
                        return_one = data.iloc[start_one]['DLRET']
                        approx_price_one = return_one * long[2] + long[2]
                        diff_one = (approx_price_one * long[1]) - 1

                if bool(re.search('[1-9]+', str(data.iloc[start_two]['PRC']))):
                    price_two = data.iloc[start_two]['PRC']

                    if short[0] == 1:
                        diff_two = (price_two * long[1]) - 1
                    elif short[0] == 2:
                        diff_two = beta - (price_two * short[1])
                else:
                    if short[0] == 1:
                        return_two = data.iloc[start_two]['DLRET']
                        approx_price_two = return_two * long[2] + long[2]
                        diff_two = (approx_price_two * long[1]) - 1
                    elif short[0] == 2:
                        return_two = data.iloc[start_two]['DLRET']
                        approx_price_two = return_two * short[2] + short[2]
                        diff_two = beta - (approx_price_two * short[1])

                payoffs_total[key].append(diff_one + diff_two)

                if short[0] == 1:
                    payoffs.append((diff_one + diff_two, short[3], start_one, long[3], start_two))
                elif short[0] == 2:
                    payoffs.append((diff_one + diff_two, short[3], start_two, long[3], start_one))

            # close position based on last trading day or last available price
            elif is_open:
                start_one -= 1
                start_two -= 1

                price_one = data.iloc[start_one]['PRC']
                price_two = data.iloc[start_two]['PRC']

                short, long = position[0], position[1]

                if short[0] == 1:
                    diff_one = (1 / beta) - (price_one * short[1])
                    diff_two = (price_two * long[1]) - 1

                elif short[0] == 2:
                    diff_two = beta - (price_two * short[1])
                    diff_one = (price_one * long[1]) - 1

                payoffs_total[key].append(diff_one + diff_two)

                if short[0] == 1:
                    payoffs.append((diff_one + diff_two, short[3], start_one, long[3], start_two))
                elif short[0] == 2:
                    payoffs.append((diff_one + diff_two, short[3], start_two, long[3], start_one))
            if num_trades != 0:
                num_pairs_traded[key] += 1

            print(payoffs)
            payoffs_per_pair[key].append(payoffs)

    return num_pairs_traded, payoffs_per_pair, payoffs_per_day


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    pass