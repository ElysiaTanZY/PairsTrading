import datetime
import pandas as pd

# TODO: Add beta data

def calculate_yearly():
    date_cols = ['datadate']
    compustat_file = "/Users/elysiatan/PycharmProjects/thesis/Backup/Firm_Fundamentals_Annual.csv"
    compustat_field = ['datadate', 'LPERMNO', 'at', 'csho', 'ni', 'bkvlps', 'mkvalt', 'prcc_f', 'ceq', 'dvpa', 'tstkp']
    compustat = pd.read_csv(compustat_file, usecols=compustat_field, parse_dates=date_cols)

    date_cols.clear()
    date_cols = ['date']
    crsp_file = "/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv"
    crsp_field = ['date', 'PERMNO', 'PRC', 'SHROUT']
    crsp = pd.read_csv(crsp_file, usecols=crsp_field, parse_dates=date_cols)

    # ROE = Net Income / Shareholder's Equity
    compustat['roe'] = compustat.apply(lambda row: row['ni'] / (row['bkvlps'] * row['csho']), axis=1)

    # ROA = Net Income / Total Assets
    compustat['roa'] = compustat.apply(lambda row: row['ni'] / row['at'], axis=1)

    # Market Cap (Fiscal end) = Shares Outstanding * Share Price at fiscal end
    compustat['marketCap_Fiscal'] = compustat.apply(lambda row: row['csho'] * row['prcc_f'], axis=1)

    # Market Cap (Calendar end) = Shares Outstanding * Share Price
    crsp['marketCap_Calendar'] = crsp.apply(lambda row: row['PRC'] * row['SHROUT'], axis=1)

    # Book value of common equity = Common Equity + Preferred Treasury Stock - Preferred Dividends in Arrears
    # (The Book-to-Price Effect in Stock Returns: Accounting for Leverage)
    compustat['Book_Value'] = compustat.apply(lambda row: row['ceq'] + row['tstkp'] - row['dvpa'], axis=1)

    # Book-Market Ratio: Common Equity for the fiscal year ending in calendar year t-1 / Market Equity at the end of Dec
    # year t-1 (Size and Book-to-Market Factors in Earnings and Returns)
    # Book-Market Ratio: Common Shareholder's Equity / Market Cap
    compustat['Book-Market_Ratio'], compustat['Book-Market_Ratio'] = compute_book_to_market(compustat, crsp)

    result_list = ['datadate', 'LPERMNO', 'roe', 'roa', 'marketCap_Calendar', 'Book-Market_Ratio']
    result = compustat[result_list]

    new_file_name = "/Users/elysiatan/PycharmProjects/thesis/Updated/Data_Firm.csv"
    result.to_csv(new_file_name)


def compute_book_to_market(compustat, crsp):
    market_cap = []
    book_to_market = []

    for i, row in compustat.iterrows():
        permno = row['LPERMNO']
        year = row['datadate'].year

        end_date = datetime.datetime(year, 12, 31)
        if end_date.weekday() == 6:  # Monday = 0, Sunday = 6
            end_date = end_date - datetime.timedelta(days=2)
        elif end_date.weekday() == 5:
            end_date = end_date - datetime.timedelta(days=1)

        end_date = pd.to_datetime(end_date)

        result_row = crsp.loc[crsp['PERMNO'] == permno and crsp['date'] == end_date]
        market_cap.append(result_row['marketCap_Calendar'])
        book_to_market.append(row['Book_Value'] / result_row['marketCap_Calendar'])

    return market_cap, book_to_market


if __name__ == '__main__':
    calculate_yearly()