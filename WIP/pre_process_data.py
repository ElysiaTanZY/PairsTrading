import csv
import matlab.engine
import json
import pandas as pd
import re
from sklearn import preprocessing
from sklearn.decomposition import PCA

num_features = 15


def main(relevant_shares, firm_data, start_year, indicator=None, pca_variation=0.95):

    ''' Gets the final features for each share which will be used for clustering

    :param relevant_shares: Shares qualified for consideration in the formation period
    :param firm_data: Firm Fundamentals data
    :param start_year: Start of formation period
    :param indicator: Whether any features should be excluded
    (Indicator: 1 - Exclude volume, 2 - Exclude price, 3 - Exclude firm fundamentals)
    :param pca_variation: Total variation final PCA components are expected to explain
    :return: New features after PCA is done
    '''

    with open('/Users/elysiatan/PycharmProjects/thesis/WIP/volume.json') as json_file:
        vol_data = json.load(json_file)

    extract_time_series_features(relevant_shares)

    consolidated_features = consolidate_features(firm_data, vol_data, start_year, indicator)
    chosen_features = pca(consolidated_features, pca_variation)

    return chosen_features


def extract_time_series_features(relevant_shares):

    ''' Converts Price Series to static features

    :param relevant_shares: Shares whose price series is to be converted
    :return: None
    '''

    # Adapted from https: // github.com / cecilialeiqi / SPIRAL
    eng = matlab.engine.start_matlab()
    time_series_data = []

    for i in range(0, len(relevant_shares)):
        share = relevant_shares[i]
        share_price_series = share[3]['LOG_PRC'].tolist()
        share_price_series.insert(0, share[0])
        time_series_data.append(share_price_series)

    file = open('time_series.csv', 'w', newline='')
    with file:
        write = csv.writer(file)
        write.writerows(time_series_data)

    eng.runme('time_series.csv', nargout=0)
    eng.quit()


def consolidate_features(firm_data, vol_data, start_year, indicator):

    ''' Formats all the necessary input features into a single dataframe

    :param firm_data: Firm Fundamentals data
    :param vol_data: Trade volume data
    :param start_year: Start of formation period
    :param indicator: Whether any features should be excluded
    (Indicator: 1 - Exclude volume, 2 - Exclude price, 3 - Exclude firm fundamentals)
    :return: Formatted dataset with all the necessary input features for each stock
    '''

    col_names = ['permno']

    for i in range(0, num_features):
        col_name = 'feature' + str(i)
        col_names.append(col_name)

    if indicator != 2:
        time_series = pd.read_csv('/Users/elysiatan/PycharmProjects/thesis/WIP/sparse_features.csv', names=col_names, header=None)
        time_series['permno'] = time_series['permno'].astype(int)
    else:
        permno_series = pd.read_csv('/Users/elysiatan/PycharmProjects/thesis/WIP/sparse_features.csv', names=col_names, header=None)
        time_series = permno_series['permno'].to_frame()

    for i in range(start_year, start_year+3):
        roa = []
        roe = []
        beta = []
        market_cap = []
        b_m_ratio = []
        vol = []

        for j, row in time_series.iterrows():
            permno = int(row['permno'])

            # Get ROA, ROE, Market Capitalisation, B/M Ratio, beta
            result = firm_data.loc[firm_data['LPERMNO'] == permno]
            if len(result.values) != 0:
                result = result[result['datadate'].dt.year == i]
            else:
                time_series.drop(j, inplace=True)
                continue

            if len(result.values != 0):
                if bool(re.search('[1-9]+', str(result['roa'].values[0]))) and \
                        bool(re.search('[1-9]+', str(result['roe'].values[0]))) and \
                        bool(re.search('[1-9]+', str(result['marketCap_Calendar'].values[0]))) and \
                        bool(re.search('[1-9]+', str(result['BM_Ratio_Fiscal'].values[0]))) and \
                        bool(re.search('[1-9]+', str(result['beta'].values[0]))):

                    roa.append(result['roa'].values[0])
                    roe.append(result['roe'].values[0])
                    market_cap.append(result['marketCap_Calendar'].values[0])
                    b_m_ratio.append(result['BM_Ratio_Fiscal'].values[0])
                    beta.append(result['beta'].values[0])
                    ave_vol = vol_data[str(permno)][str(i)]
                    vol.append(ave_vol)

                else:
                    time_series.drop(j, inplace=True)
            else:
                time_series.drop(j, inplace=True)

        roa_col = 'roa' + str(i - start_year)
        roe_col = 'roe' + str(i - start_year)
        market_cap_col = 'market_cap' + str(i - start_year)
        b_m_ratio_col = 'b_m_ratio' + str(i - start_year)
        beta_col = 'beta' + str(i - start_year)
        vol_col = 'vol' + str(i - start_year)

        if indicator != 3:
            time_series[roa_col] = roa
            time_series[roe_col] = roe
            time_series[market_cap_col] = market_cap
            time_series[b_m_ratio_col] = b_m_ratio
            time_series[beta_col] = beta

        if indicator != 1:
            time_series[vol_col] = vol

    new_file_name = "/Users/elysiatan/PycharmProjects/thesis/Updated/pre-processed.csv"
    time_series.to_csv(new_file_name)
    return time_series


def pca(consolidated_features, pca_variation):

    ''' Conducts PCA

    :param consolidated_features: Initial data frame with all the required features
    :param pca_variation: Total amount of variation the chosen Principal Components are expected to explain
    :return: Principal components of each stock formatted in a single data frame
    '''

    col_list = list(consolidated_features.columns)
    col_list.pop()

    standard_scaler = preprocessing.StandardScaler()
    features = consolidated_features.loc[:,col_list].values
    features = standard_scaler.fit_transform(features)

    pca_features = PCA(n_components=pca_variation)

    principalComponents_features = pca_features.fit_transform(features)
    col_list.clear()

    for i in range(0, len(pca_features.explained_variance_ratio_)):
        col_name = 'component_' + str(i + 1)
        col_list.append(col_name)

    principal_features_Df = pd.DataFrame(data=principalComponents_features, columns=col_list)
    principal_features_Df['permno'] = consolidated_features['permno'].values
    print(consolidated_features.head())
    print(principal_features_Df.head())

    return principal_features_Df
