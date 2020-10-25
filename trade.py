import pandas as pd

def trade(_cointegrated_pairs, _start_year_trade, data):
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
    trade()