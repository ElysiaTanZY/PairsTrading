import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime

from matplotlib.dates import DateFormatter


def main(identified, traded, fully_invested_returns, model_list):
    for i in range(0, len(model_list)):
        generate_bar_chart_pairs(identified[model_list[i]], traded[model_list[i]], model_list[i])

    #generate_time_series(fully_invested_returns, model_list)
    generate_bar_chart_payoffs(fully_invested_returns, model_list)


# For returns
def generate_bar_chart_payoffs(fully_invested_returns, model_list):
    years = ["0" + str(i) if len(str(i)) == 1 else str(i) for i in range(3, 3 + len(fully_invested_returns[model_list[0]]))]

    ind = np.arange(len(years))  # the label locations
    width = 0.15  # the width of the bars

    fig, ax = plt.subplots(figsize=(25, 10))

    rects1 = ax.bar(ind, fully_invested_returns["baseline"], width, color='#f29ca2')
    rects2 = ax.bar(ind + width, fully_invested_returns["kmedoids"], width, color='#61eaf2')
    rects3 = ax.bar(ind + width * 2, fully_invested_returns["dbscan"], width, color='#6da4d9')
    rects4 = ax.bar(ind + width * 3, fully_invested_returns["fuzzy"], width, color='#f2bb12')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Fully invested returns')
    ax.set_xticks(ind)
    ax.set_xticklabels(years)
    ax.legend()

    autolabel(rects1, ax)
    autolabel(rects2, ax)
    autolabel(rects3, ax)
    autolabel(rects4, ax)

    ax.legend((rects1[0], rects2[0], rects3[0], rects4[0]), ('Baseline', 'KMedoids', 'DBSCAN', 'Fuzzy C-Means'))
    plt.show()


def autolabel(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""

    for rect in rects:
        height = rect.get_height()
        ax.annotate('%.3f' % float(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=6)


# For pairs identified vs traded
def generate_bar_chart_pairs(identified_time_series, traded_time_series, model):
    not_traded_time_series = []

    print(identified_time_series)
    print(traded_time_series)

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
    years = []
    for trade_year in range(2003, 2003 + len(fully_invested_returns[model_list[0]])):
        years.append(pd.to_datetime(datetime.datetime(trade_year, 12, 31)))

    colours = ['springgreen', 'steelblue', 'orange', 'violet']
    for i in range(0, len(model_list)):
        time_series = pd.Series(fully_invested_returns[model_list[i]], index=years)
        plt.plot(time_series, label=model_list[i], color=colours[i%len(model_list)])

    date_form = DateFormatter("%y")
    plt.gca().xaxis.set_major_formatter(date_form)
    plt.xlabel("Year")
    plt.ylabel("Fully Invested Returns")
    plt.legend()
    plt.show()