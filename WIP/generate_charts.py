import matplotlib.pyplot as plt
import pandas as pd
import datetime

from matplotlib.dates import DateFormatter


def main(identified, traded, fully_invested_returns, model_list):
    for model in model_list:
        model = str(model)
        generate_bar_chart_pairs(identified[model], traded[model], model)

    generate_time_series(fully_invested_returns, model_list)


def generate_bar_chart_pairs(identified_time_series, traded_time_series, model):

    ''' Plots the bar chart to show the proportion of identified pairs that were traded

    :param identified_time_series: Number of pairs identified by the model in each year
    :param traded_time_series: Number of pairs traded by the model in each year
    :param model: Model in concern
    :return: None
    '''

    not_traded_time_series = []

    if len(identified_time_series) != len(traded_time_series):
        raise Exception("Mismatch in years between time series for identified pairs and traded pairs")

    for i in range(0, len(identified_time_series)):
        not_traded_time_series.append(identified_time_series[i] - traded_time_series[i])

    years = ["0" + str(i) if len(str(i)) == 1 else str(i) for i in range(3, 3 + len(identified_time_series))]
    fig, ax = plt.subplots()

    ax1 = ax.bar(years, traded_time_series, label="Traded", color='lightsteelblue')
    ax2 = ax.bar(years, not_traded_time_series, label="Not Traded", color='steelblue', bottom=traded_time_series)
    ax.set_ylabel("Number of pairs")
    ax.set_xlabel("Year")
    ax.set_title("Identified pairs by traded and not traded (" + str(model) + ")")
    ax.legend()

    for r1, r2 in zip(ax1, ax2):
        h1 = r1.get_height()
        h2 = r2.get_height()
        plt.text(r1.get_x() + r1.get_width() / 2., h1 / 2., "%d" % h1, ha="center", va="center", color="black",
                 fontsize=6)
        plt.text(r2.get_x() + r2.get_width() / 2., h1 + h2 / 2., "%d" % h2, ha="center", va="center", color="black",
                 fontsize=6)

    for r1, r2 in zip(ax1, ax2):
        h1 = r1.get_height()
        h2 = r2.get_height()
        plt.text(r1.get_x() + r1.get_width() / 2., h1 + h2, '%s' % (h1 + h2), ha='center', va='bottom', fontsize=6)

    plt.show()


def generate_time_series(fully_invested_returns, model_list):

    ''' Plots the time series of fully invested returns for each model

    :param fully_invested_returns: List of Fully Invested Returns List for each model
    :param model_list: Models whose Fully Invested Returns time series should be plotted
    :return: None
    '''

    years = []
    for trade_year in range(2003, 2003 + len(fully_invested_returns[str(model_list[0])])):
        years.append(pd.to_datetime(datetime.datetime(trade_year, 12, 31)))

    # Plot time series of Fully Invested Returns from each model experimented with, including baseline
    colours = ['springgreen', 'steelblue', 'orange', 'violet']
    for i in range(0, len(model_list)):
        model = str(model_list[i])
        time_series = pd.Series(fully_invested_returns[model], index=years)
        plt.plot(time_series, label=model, color=colours[i%len(model_list)])

    # Plot time series of NASDAQ returns to get a sense of how the pairs trading returns correlate with market movement
    # https://www.macrotrends.net/2623/nasdaq-by-year-historical-annual-returns
    nasdaq_returns = pd.read_csv("../Backup/nasdaq-by-year-historical-annual-returns.csv")
    nasdaq_returns_time_series = pd.Series(nasdaq_returns["value"][:len(years)].values, index=years)
    nasdaq_returns_time_series = nasdaq_returns_time_series.divide(100)
    plt.plot(nasdaq_returns_time_series, label="NASDAQ", color='black')

    date_form = DateFormatter("%y")
    plt.gca().xaxis.set_major_formatter(date_form)
    plt.xlabel("Year")
    plt.ylabel("Fully Invested Returns")
    plt.legend()
    plt.show()