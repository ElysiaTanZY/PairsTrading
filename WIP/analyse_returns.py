import math
import statistics


def analyse_returns(returns, num_pairs_traded, num_pairs_chosen):
    # Excess returns
    return_on_committed_capital_list = []
    fully_invested_return_list = []

    for i in range(0, len(returns)):
        return_on_committed_capital_list.append(sum(returns) / num_pairs_chosen if num_pairs_chosen > 0 else 0)
        fully_invested_return_list.append(sum(returns) / num_pairs_traded if num_pairs_traded > 0 else 0)

    return_on_committed_capital = statistics.mean(return_on_committed_capital_list)
    fully_invested_return = statistics.mean(fully_invested_return_list)

    # Maximum Drawdown
    peak = max(returns)
    trough = min(returns)
    mdd = (trough - peak) / peak

    # Sharpe ratio
    average = statistics.mean(returns)
    sd = statistics.stdev(returns)
    # TODO: Need to find risk free rate - government bond yield (one year)
    risk_free_rate = 0.03
    sharpe_ratio = (average - risk_free_rate) / sd

    # Calmar ratio
    calmar_ratio = average / mdd

    # Sortino ratio
    minimal_acceptable_return = average

    downside_returns = []
    for i in range(0, len(returns)):
        returns_subtract_mar = returns[i] - minimal_acceptable_return

        if returns_subtract_mar < 0:
            downside_returns.append(returns_subtract_mar**2)

    downside_deviation = math.sqrt(sum(downside_returns) / len(returns))
    sortino_ratio = (average - risk_free_rate) / downside_deviation

    return

if __name__ == '__main__':
    analyse_returns()