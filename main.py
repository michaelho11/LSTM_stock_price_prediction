import numpy as np
import pandas as pd
import yfinance as yf
from keras.models import Sequential
import tensorflow as tf
# import keras
from keras import optimizers
# from keras.callbacks import History
from keras.models import Model
from keras.layers import Dense, Dropout, LSTM, Input, Activation, concatenate
from sklearn import preprocessing

def dataframe_download (stock, date):
    #download dataframe
    df = yf.download(stock, start = date)
    # df = df.head(100)
    close = df['Close']
    # print (close)
    return df

def test_train_split(df,ratio,history_point):
    #1. dividing the dataset
    index = int(len(df)*ratio)
    train_data_set = df[:index]
    test_data_set = df[index:]
    # print(train_data_set)
    # print(test_data_set)

    #2. norminalise the dataset and define x_train, y_train, x_test, y_test
    normaliser = preprocessing.MinMaxScaler()
    normalised_train_data = normaliser.fit_transform(train_data_set) #fit = calculated mean/variance
    x_train = np.array([normalised_train_data[:,0:][i:i+history_point].copy() for i in
                        range(len(normalised_train_data)-history_point)])
    y_train = np.array([normalised_train_data[i+history_point,3].copy() for i in
                        range(len(normalised_train_data)-history_point)])
    y_train = np.expand_dims(y_train,-1)

    normalised_test_data = normaliser.transform(test_data_set)  # transform = using the same mean/variance
    x_test = np.array([normalised_test_data[:,0:][i:i+history_point].copy() for i in
                        range(len(normalised_test_data)-history_point)])
    y_test = np.array([test_data_set['Adj Close'][i + history_point].copy() for i in
                        range(len(normalised_test_data) - history_point)])
    y_test = np.expand_dims(y_test,-1)

    #3. normalise the actual price
    actual_price_normaliser = preprocessing.MinMaxScaler()
    nor_adj_close = np.array([train_data_set['Adj Close'][i+history_point].copy() for i in
                        range(len(train_data_set)-history_point)])
    nor_adj_close = np.expand_dims(nor_adj_close, 1)
    actual_price_normaliser.fit(nor_adj_close)

    print('---')
    print(y_test)
    print(len(x_test))

    return x_train, y_train, x_test, y_test, actual_price_normaliser


def add_technical_indicators(stock_df):
    # 1. OBV calculation
    stock_df_copy = stock_df.copy()
    OBV_list = [0]
    OBV = 0
    for i in range(1,len(stock_df)):
        if stock_df['Adj Close'][i-1] < stock_df['Adj Close'][i]:
            OBV = OBV + stock_df['Volume'][i]
        elif stock_df['Adj Close'][i-1] > stock_df['Adj Close'][i]:
            OBV = OBV - stock_df['Volume'][i]
        OBV_list.append(OBV)    # list
    stock_df_copy['On Balanced Volume'] = OBV_list

    # 2. SMA calculation
    closing = stock_df['Close']
    stock_sma = pd.Series(closing).rolling(20).mean()  # Note: input pandas.core.series, but not input dataframe
    stock_df_copy['SMA'] = stock_sma

    # 3. EMA calculation
    stock_ema = closing.ewm(span=20).mean()   # EMA = k*price_t +(1-k)price_(t-1), where k = 2/(N+1), N=span
    stock_df_copy['EMA'] = stock_ema

    # 4. Bollinger bands N=20, P=2
    mid = pd.Series(closing).rolling(20).mean()
    std = pd.Series(closing).rolling(20).std(ddof=0).values
    upper = mid + std * 2
    lower = mid - std * 2
    stock_df_copy['BB_upper'] = upper
    stock_df_copy['BB_lower'] = lower

    return stock_df_copy

# def lstm_model (x_train, y_train, history_point):
#     tf.random.set_seed(10)
#     n_features = 6
#     model = Sequential()
#     model.add(LSTM(21, activation='relu',input_shape=(history_point,n_features)))
#     # model.add(Dropout(0.2))
#     model.add(Dense(1))
#     model.compile(optimizer=optimizers.Adam(learning_rate= 0.0008), loss='mse', metrics=['mean_absolute_error'])
#     model.fit(x=x_train, y=y_train,batch_size=15, epochs=170, shuffle=True, validation_split=0.1)
#
#     return model

def lstm_model(X_train, y_train, history_points):
    tf.random.set_seed(20)
    np.random.seed(10)
    lstm_input = Input(shape=(history_points,11), name='lstm_input')

    inputs = LSTM(21, name='first_layer')(lstm_input)
    inputs = Dense(1, name='dense_layer')(inputs)
    output = Activation('linear', name='output')(inputs)

    model = Model(inputs=lstm_input, outputs=output)
    adam = optimizers.Adam(lr = 0.0008)
    model.compile(optimizer=adam, loss='mse')
    model.fit(x=X_train, y=y_train, batch_size=15, epochs=170, shuffle=True, validation_split = 0.1)

    return model

# print (dataframe_download ('0700.HK', '2022-01-01'))
stock = dataframe_download('2013.HK', '2022-01-01')
stock = add_technical_indicators(stock)
stock = stock.dropna()
history_point = 21
test_train_split_ratio = 0.2
x_train, y_train, x_test, y_test, actual_price_normaliser= test_train_split(stock,test_train_split_ratio,history_point)
model = lstm_model(x_train, y_train, history_point)

y_pred = model.predict(x_test)
print(y_pred)
print('--')
predicted_price = actual_price_normaliser.inverse_transform(y_pred)
print(predicted_price)
print('---')







