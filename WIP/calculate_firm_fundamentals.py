import datetime
import pandas as pd
import re

shares = {}  # {PERMNO: {year: (start, end)}}


def calculate_yearly():
    ''' Calculate the necessary firm fundamentals

    :return: None
    '''

    date_cols = ['datadate']
    compustat_file = "/Users/elysiatan/PycharmProjects/thesis/Backup/Firm_Fundamentals_Annual.csv"
    compustat_fields = ['datadate', 'LPERMNO', 'at', 'csho', 'ni', 'lt', 'mkvalt', 'seq', 'prcc_f', 'ceq', 'dvpa', 'tstkp', 'ebit', 'txt', 'ch', 'dlc', 'dltt']
    compustat = pd.read_csv(compustat_file, usecols=compustat_fields, parse_dates=date_cols)

    date_cols.clear()
    date_cols = ['date']
    crsp_file = "/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv"
    crsp_fields = ['date', 'PERMNO', 'PRC', 'SHROUT']
    crsp = pd.read_csv(crsp_file, usecols=crsp_fields, parse_dates=date_cols)
    crsp.dropna(subset=['PERMNO'], inplace=True)
    crsp['PERMNO'] = crsp['PERMNO'].astype(int)

    # Nullified if net income is negative
    # ROE = Net Income / Shareholder's Equity
    compustat['roe'] = compustat.apply(lambda row: row['ni'] / (row['at'] - row['lt']) if
        bool(re.search('[1-9]+', str(row['at'] - row['lt']))) and row['ni'] > 0 else 0.0, axis=1)

    print("done roe")

    # ROA = Net Income / Total Assets
    compustat['roa'] = compustat.apply(lambda row: row['ni'] / row['at'] if
        bool(re.search('[1-9]+', str(row['at']))) and row['ni'] > 0 else 0.0, axis=1)

    print("done roa")

    # ROIC: NOPAT / Inveted Capital
    compustat['nopat'] = compustat.apply(lambda row: row['ebit'] - row['txt'], axis=1)
    compustat['invested_capital'] = compustat.apply(lambda row: row['dlc'] + row['dltt'] + row['seq'] - row['ch'], axis=1)
    compustat['roic'] = compustat.apply(lambda row: row['nopat'] / row['invested_capital'] if
        bool(re.search('[1-9]+', str(row['invested_capital']))) and row['nopat'] > 0 else 0.0, axis=1)

    print('done roic')

    # Market Cap (Fiscal end) = Shares Outstanding * Share Price at fiscal end
    compustat['marketCap_Fiscal'] = compustat.apply(lambda row: row['csho'] * row['prcc_f'], axis=1)

    print('done market cap fiscal')

    # Book value of common equity = Common Equity + Preferred Treasury Stock - Preferred Dividends in Arrears
    # (The Book-to-Price Effect in Stock Returns: Accounting for Leverage)
    compustat['Book_Value_CE'] = compustat.apply(lambda row: row['ceq'] + row['tstkp'] - row['dvpa'], axis=1)

    print('done book value')

    compustat['BM_Ratio_Fiscal'] = compustat.apply(lambda row: row['Book_Value_CE'] / (row['marketCap_Fiscal']) if
    bool(re.search('[1-9]+', str(row['marketCap_Fiscal']))) else 0.0, axis=1)

    print('done b-m ratio fiscal')

    # Book-Market Ratio: Common Equity for the fiscal year ending in calendar year t-1 / Market Equity at the end of Dec
    # year t-1 (Size and Book-to-Market Factors in Earnings and Returns)
    # Book-Market Ratio: Common Shareholder's Equity / Market Cap
    compustat['marketCap_Calendar'], compustat['BM_Ratio_Calendar'] = retrieve_from_crsp(compustat, crsp)

    print('done market cap calendar and b-m ratio calendar')

    # Beta: Retrieved from Beta Suite by WRDS
    compustat['beta'] = retrieve_from_beta_suite(compustat)

    print('done beta')

    result_list = ['datadate', 'LPERMNO', 'roe', 'roa', 'roic', 'marketCap_Calendar', 'marketCap_Fiscal', 'BM_Ratio_Fiscal', 'BM_Ratio_Calendar', 'beta', 'Book_Value_CE', 'nopat', 'invested_capital']
    result = compustat[result_list]

    new_file_name = "/Users/elysiatan/PycharmProjects/thesis/Updated/Data_Firm.csv"
    result.to_csv(new_file_name)


def retrieve_from_beta_suite(compustat):

    ''' Retrieves market beta from beta suite dataset

    :param compustat: Compustat dataset that holds firm fundamentals --> Provides the list of PERMNO for which beta
    needs to be extracted
    :return: List of beta for each stock
    '''

    beta = []

    date_cols = ['DATE']
    file = "/Users/elysiatan/PycharmProjects/thesis/Backup/beta_monthly.csv"
    fields = ['DATE', 'PERMNO', 'b_mkt']
    beta_suite = pd.read_csv(file, usecols=fields, parse_dates=date_cols)

    for i, row in compustat.iterrows():
        permno = row['LPERMNO']
        year = row['datadate'].year

        end_date = datetime.datetime(year, 12, 31)
        if end_date.weekday() == 6:  # Monday = 0, Sunday = 6
            end_date = end_date - datetime.timedelta(days=2)
        elif end_date.weekday() == 5:
            end_date = end_date - datetime.timedelta(days=1)

        end_date = pd.to_datetime(end_date)

        result = beta_suite.loc[beta_suite['PERMNO'] == permno]
        result = result.loc[result['DATE'] == end_date]

        if len(result.values) != 0:
            beta.append(result['b_mkt'].values[0])
        else:
            beta.append(0.0)

    return beta


def retrieve_from_crsp(compustat, crsp):

    ''' Retrieves market cap at calendar year end and calculate book/market ratio

    :param compustat: Compustat dataset that holds firm fundamentals --> Provides the list of PERMNO for which beta
    :param crsp: CRSP dataset that holds stock information --> Provides the trade volume required to calculate B/M ratio
    :return:
    '''

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
        if permno not in shares.keys():
            market_cap.append(0.0)
            book_to_market.append(0.0)
            continue

        if year not in shares[permno].keys():
            market_cap.append(0.0)
            book_to_market.append(0.0)
            continue

        start, end = shares[permno][year]
        result = crsp.iloc[[end]]

        if bool(re.search('[1-9]+', str(result.iloc[0]['PRC']))) and \
                bool(re.search('[1-9]+', str(result.iloc[0]['SHROUT']))):
            market_cap.append(result.iloc[0]['PRC'] * result.iloc[0]['SHROUT'])
            book_to_market.append((row['Book_Value_CE'] * ((result.iloc[0]['SHROUT']/ 1000) / row['csho'])) / (
                        result.iloc[0]['PRC'] * (result.iloc[0]['SHROUT'] / 1000)))

    return market_cap, book_to_market


def check_yearly():
    result_file = "/Users/elysiatan/PycharmProjects/thesis/Updated/Data_Firm_All_2.csv"
    result = pd.read_csv(result_file)

    result = result.drop(columns=['index'])

    print(result[['roe', 'roa', 'roic']].describe())
    print(result[result.roe == result.roe.min()])
    print(result[result.roe == result.roe.max()])
    print(result[result.roa == result.roa.min()])
    print(result[result.roa == result.roa.max()])
    print(result[result.roic == result.roic.min()])
    print(result[result.roic == result.roic.max()])

    print(result[['beta']].describe())

    print(result[['Book_Value_CE']].describe())
    print(result[result.Book_Value_CE == result.Book_Value_CE.min()])
    print(result[result.Book_Value_CE == result.Book_Value_CE.max()])

    print(result[['marketCap_Calendar', 'marketCap_Fiscal']].describe())
    print(result[result.marketCap_Calendar == result.marketCap_Calendar.min()])
    print(result[result.marketCap_Calendar == result.marketCap_Calendar.max()])
    print(result[result.marketCap_Fiscal == result.marketCap_Fiscal.min()])
    print(result[result.marketCap_Fiscal == result.marketCap_Fiscal.max()])

    print(result[['BM_Ratio_Fiscal', 'BM_Ratio_Calendar']].describe())
    print(result[result.BM_Ratio_Fiscal == result.BM_Ratio_Fiscal.min()])
    print(result[result.BM_Ratio_Fiscal == result.BM_Ratio_Fiscal.max()])
    print(result[result.BM_Ratio_Calendar == result.BM_Ratio_Calendar.min()])
    print(result[result.BM_Ratio_Calendar == result.BM_Ratio_Calendar.max()])


if __name__ == '__main__':
    calculate_yearly()
    check_yearly()