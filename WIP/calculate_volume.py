import json
import pandas as pd


def calculate_volume():
    date_cols = ['date']
    crsp_file = "/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv"
    crsp_fields = ['date', 'PERMNO', 'PRC', 'SHROUT', 'VOL']
    crsp = pd.read_csv(crsp_file, usecols=crsp_fields, parse_dates=date_cols)
    crsp['PERMNO'] = crsp['PERMNO'].astype(int)

    volume_data = {} # {permno: {year: volume}}

    prev_year = crsp['date'].iloc[0].year
    prev_permno = crsp['PERMNO'].iloc[0]
    start = 0

    for i, row in crsp.iterrows():
        permno = row['PERMNO']

        year = row['date'].year

        if not permno == prev_permno or not year == prev_year:
            if str(prev_permno) not in volume_data.keys():
                volume_data[str(prev_permno)] = {}

            subset = crsp.iloc[start:i]
            mean = subset['VOL'].mean()

            print('Before')
            temp = volume_data[str(prev_permno)]
            print(temp)
            print('AFter')
            temp[str(prev_year)] = mean
            print(temp)
            volume_data[str(prev_permno)] = temp

            start = i
            prev_year = year

            if not permno == prev_permno:
                prev_permno = permno

    with open('volume.json', 'w') as fp:
        json.dump(volume_data, fp)


if __name__ == '__main__':
    calculate_volume()