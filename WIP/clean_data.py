import pandas as pd
import re


def clean_data():
    # Step 1: For delisted stocks with missing delisting returns, fill in with a number
    # Numbers are filled in by making use of the average available delisting return for that code,
    # if empty and NASDAQ firm - Use -55% else use -30%
    # (Beaver, McNicholas, Price) JAE 2007
    file_name = "/Users/elysiatan/PycharmProjects/thesis/Backup/Data_NASDAQ.csv"
    df = pd.read_csv(file_name)

    df['DLSTCD'].fillna(value=100, inplace=True)
    df['DLRETX'].fillna(value=0.0, inplace=True)
    df['DLPRC'].fillna(value=0.0, inplace=True)
    df['DLRET'].fillna(value=0, inplace=True)
    df['PRC'].fillna(value=0.0, inplace=True)
    df['VOL'].fillna(value=0, inplace=True)
    df['SHROUT'].fillna(value=0, inplace=True)
    df['RET'].fillna(value=-99, inplace=True)
    df['RETX'].fillna(value=-99, inplace=True)
    df['SICCD'].fillna(value=9999, inplace=True)

    total_delisting_200 = 0
    number_delisting_200 = 0
    missing_delisting_200 = []

    total_delisting_300 = 0
    number_delisting_300 = 0
    missing_delisting_300 = []

    total_delisting_400 = 0
    number_delisting_400 = 0
    missing_delisting_400 = []

    total_delisting_500 = 0
    number_delisting_500 = 0
    missing_delisting_500 = []

    # Delisting Code: 200s - M&A
    # Delisting Code: 300s - Issue Exchanged
    # Delisting Code: 400s - Issue Liquidated
    # Delisting Code: 500s - Dropped
    for i, row in df.iterrows():
        print(i)
        if row['PRC'] < 0:
            df.at[i, 'PRC'] = row['PRC'] * -1 # PRC is negative to indicate that it is a bid/ask average when there is no closing price

        if 100 <= row['DLSTCD'] < 200:
            continue
        elif 200 <= row['DLSTCD'] < 300:
            if not bool(re.search('[1-9]+', str(row['DLRET']))):
                missing_delisting_200.append(i)
            else:
                total_delisting_200 += float(row['DLRET'])
                number_delisting_200 += 1
        elif 300 <= row['DLSTCD'] < 400:
            if not bool(re.search('[1-9]+', str(row['DLRET']))):
                missing_delisting_300.append(i)
            else:
                total_delisting_300 += float(row['DLRET'])
                number_delisting_300 += 1
        elif 400 <= row['DLSTCD'] < 500:
            if not bool(re.search('[1-9]+', str(row['DLRET']))):
                missing_delisting_400.append(row)
            else:
                total_delisting_400 += float(row['DLRET'])
                number_delisting_400 += 1
        elif 500 <= row['DLSTCD'] < 600:
            if not bool(re.search('[1-9]+', str(row['DLRET']))):
                missing_delisting_500.append(row)
            else:
                total_delisting_500 += float(row['DLRET'])
                number_delisting_500 += 1

    fill_in_missing_delisting_returns(number_delisting_200, total_delisting_200, missing_delisting_200, df)
    fill_in_missing_delisting_returns(number_delisting_300, total_delisting_300, missing_delisting_300, df)
    fill_in_missing_delisting_returns(number_delisting_400, total_delisting_400, missing_delisting_400, df)
    fill_in_missing_delisting_returns(number_delisting_500, total_delisting_500, missing_delisting_500, df)

    new_file_name = "/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv"
    new_row = {'PERMNO': 0, 'date':'01/01/2020'}
    df['PERMNO'] = df['PERMNO'].astype(int)
    df = df.append(new_row, ignore_index=True)
    df.to_csv(new_file_name)

    print("done")


def fill_in_missing_delisting_returns(num, total, missing_list, df):
    if num != 0:
        average = total / num
    else:
        average = 0

    for i in range(0, len(missing_list)):
        if average == 0:
            #TODO: Change difffernet values for NASDAQ and other exchanges but see result from clustering first..
            df.at[i, 'DLRET'] = -0.30
        else:
            df.at[i, 'DLRET'] = average


def check_data(exchange_code):
    print("Checking for exchange: " + str(exchange_code))

    df = pd.read_csv("./Backup/Exchange" + str(exchange_code) + ".csv");
    df2 = pd.read_csv("./Updated/Exchange" + str(exchange_code) + "update.csv");

    # Number of rows
    print(df.shape[0])
    print(df2.shape[0])

    # Number of cols
    print(df.shape[1])
    print(df2.shape[1])

    # Print headers
    print(list(df.columns))
    print(list(df2.columns))

    # Print values for delisted returns
    for i, row in df2.iterrows():
        if 100 <= row['DLSTCD'] < 200:
            continue
        else:
            print(str(row['DLSTCD']) + ": " + str(row['DLRET']))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    clean_data()
    #check_data(i)