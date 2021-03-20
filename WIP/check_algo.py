import json
import pandas as pd
import math


with open('/Users/elysiatan/PycharmProjects/thesis/WIP/volume.json') as json_file:
    vol = json.load(json_file)

with open('/Users/elysiatan/PycharmProjects/thesis/Backup/result.json') as json_file:
    indices = json.load(json_file)

date_cols = ['date']
prices_data = pd.read_csv("/Users/elysiatan/PycharmProjects/thesis/Updated/Data_NASDAQ.csv", parse_dates=date_cols)


def check_data():
    with open('/Users/elysiatan/PycharmProjects/thesis/Backup/result.json') as json_file:
        data = json.load(json_file)

    index_list = {}
    for key, values in data.items():
        for year, indexes in values.items():
            index_list[indexes[0]] = indexes[1]

    start = 0
    end = prices_data.shape[0] - 1
    curr = start

    while curr != end:
        if curr in index_list.keys():
            curr = index_list[curr] + 1
        else:
            print("Fail")
            break

    print("Pass")


def check_volume():
    for permno, volumes in vol.items():
        for year, value in volumes.items():
            start, end = indices[permno][year][0], indices[permno][year][1]

            vol_list = prices_data.iloc[start:end+1]
            mean = vol_list['VOL'].mean()

            if not math.isclose(mean, value):
                print(permno)
                print(year)
                print(mean)
                print(value)
                print("Fail")
                return

    for permno, years in indices.items():
        for year, val in years.items():
            start, end = val[0], val[1]

            vol_list = prices_data.iloc[start:end + 1]
            mean = vol_list['VOL'].mean()

            if not math.isclose(mean, vol[permno][year]):
                print("Fail")

    print("Pass")


if __name__ == '__main__':
    check_data()
    check_volume()
