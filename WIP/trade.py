import datetime
import pandas as pd
import re

returns = []
num_pairs_traded = 0


def trade(chosen_pairs, trade_year, data):
    global returns
    global num_pairs_traded

    # Trade cointegrated pairs during trading period
    # Threshold to open positions: 2 SD away from mean
    # Threshold to close positions: 0.5 SD away from mean
    # For shares that are delisted during the holding period, the position is immediately closed using the last
    # available price or the delisting returns

    start_date = datetime.datetime(trade_year, 1, 1)
    if start_date.weekday() == 6:
        start_date = start_date + datetime.timedelta(days=1)
    elif start_date.weekday() == 5:
        start_date = start_date + datetime.timedelta(days=2)

    start_date = pd.to_datetime(start_date)

    end_date = datetime.datetime(trade_year, 12, 31)
    if end_date.weekday() == 6:  # Monday = 0, Sunday = 6
        end_date = end_date - datetime.timedelta(days=2)
    elif end_date.dt.dayofweek == 5:
        end_date = end_date - datetime.timedelta(days=1)

    end_date = pd.to_datetime(end_date)

    for i in range(0, len(chosen_pairs)):
        code_one, start_one, code_two, start_two, mean, std, beta = chosen_pairs[i]

        is_open = False
        is_delisted = False
        position = [] # Element one is short, element two is long
        num_trades = 0

        date_one = data.iloc[start_one]['date']
        current_one = data.iloc[start_one]['PERMNO']

        date_two = data.iloc[start_two]['date']
        current_two = data.iloc[start_two]['PERMNO']

        while start_date <= date_one <= end_date and start_date <= date_two <= end_date:
            if date_one == date_two and current_one == code_one and current_two == code_two:
                if not 100 <= data.iloc[start_one]['DLSTCD'] < 200 or not 100 <= data.iloc[start_two]['DLSTCD'] < 200:
                    # Stock delisted during trading period
                    is_delisted = True
                    break

                norm_price_one = data.iloc[start_one]['LOG_PRC']
                norm_price_two = data.iloc[start_two]['LOG_PRC']

                if not bool(re.search('[1-9]+', str(norm_price_one))) or not bool(re.search('[1-9]+', str(norm_price_two))):
                    # Either one stock has missing prices during trading period --> Close on last available prices
                    break

                spread = norm_price_one - norm_price_two

                if is_open and abs(spread - mean) < 0.5*std:
                    # close position and calculate returns
                    # returns: (receive - pay) / initial amount received or paid
                    price_one = data.iloc[start_one]['PRC']
                    price_two = data.iloc[start_two]['PRC']

                    short, long = position[0], position[1]

                    if short[0] == 1:
                        return_one = ((1 / beta) - (price_one * short[1])) / (1 / beta)
                        return_two = ((price_two * long[1]) - 1)
                    elif short[0] == 2:
                        return_two = ((1 / beta) - (price_two * short[1])) / (1 / beta)
                        return_one = ((price_one * long[1]) - 1)

                    returns.append(return_one + return_two)
                    is_open = False

                elif not is_open and abs(spread - mean) > 2*std:
                    '''
                    If deviation is positive --> $1 long position for Stock 2 and $1/Beta short position for Stock 1
                    If deviation is negative --> $1 long position for Stock 1 and $Beta short position for Stock 2
                    '''

                    price_one = data.iloc[start_one]['PRC']
                    price_two = data.iloc[start_two]['PRC']

                    if (spread - mean) > 0:
                        position.append((1, (1 / beta) / price_one, price_one))
                        position.append((2, 1 / price_two, price_two))
                    elif (spread - mean) <= 0:
                        position.append((2, beta / price_two, price_two))
                        position.append((1, 1 / price_one, price_one))

                    num_trades = num_trades + 1
                    is_open = True
            '''
            else:
                # Come in here means missing values for at least one of the stocks
                # 4 choices: Either fill in at the start with the prev day prices or ignore the trade all together or align dates or close with previous aligned date prices
                # TODO: align the two dates if possile - this should be fine??
                # TODO: or just ignore this trade?
                # I think it will never enter here right??
                break
            '''

            start_one += 1
            start_two += 1

            date_one = data.iloc[start_one]['date']
            current_one = data.iloc[start_one]['PERMNO']

            date_two = data.iloc[start_two]['date']
            current_two = data.iloc[start_two]['PERMNO']

        # At this point, there are 3 possible scenarios
        # Scenario 1: Completed the whole trading period
        # Scenario 2: At least one of the stock is delisted during the period
        # Scenario 3: At least one of the stock has missing stock prices within the trading period
        if is_open and is_delisted:
            # close position based on last available price or delisting returns
            short, long = position[0], position[1]

            if bool(re.search('[1-9]+', str(data.iloc[start_one]['PRC']))):
                price_one = data.iloc[start_one]['PRC']
                if short[0] == 1:
                    return_one = ((1 / beta) - (price_one * short[1])) / (1 / beta)
                elif short[0] == 2:
                    return_one = ((price_one * long[1]) - 1)
            else:
                return_one = data.iloc[start_one]['DLRET']

            if bool(re.search('[1-9]+', str(data.iloc[start_two]['PRC']))):
                price_two = data.iloc[start_two]['PRC']

                if short[0] == 1:
                    return_two = ((price_two * long[1]) - 1)
                elif short[0] == 2:
                    return_two = ((1 / beta) - (price_two * short[1])) / (1 / beta)
            else:
                return_two = data.iloc[start_two]['DLRET']

            returns.append(return_one + return_two)

        elif is_open:
            # close position based on last trading day or last available price
            start_one -= 1
            start_two -= 1

            price_one = data.iloc[start_one]['PRC']
            price_two = data.iloc[start_two]['PRC']

            short, long = position[0], position[1]

            if short[0] == 1:
                return_one = ((1 / beta) - (price_one * short[1])) / (1 / beta)
                return_two = ((price_two * long[1]) - 1)
            elif short[0] == 2:
                return_two = ((1 / beta) - (price_two * short[1])) / (1 / beta)
                return_one = ((price_one * long[1]) - 1)

            returns.append(return_one + return_two)

        if num_trades != 0:
            num_pairs_traded = num_pairs_traded + 1

    return sum(returns), num_pairs_traded


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    trade()