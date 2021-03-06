'''
Detect the scam of golden crossing and death crossing
@ ChingRu 2019-01-13
'''

# Matrix
import pandas as pd
import numpy as np

# XGBoost
import xgboost as xgb 
from xgboost import XGBClassifier 
 
# Technical Indicator
import talib

# Plot and Visualize
import matplotlib.pyplot as plt
import graphviz

# Scikit-learn
from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix 
from sklearn import tree
from sklearn.metrics import accuracy_score, precision_score, recall_score

# 把warning關掉= =
import sys
import warnings
warnings.filterwarnings('ignore')

# terminal display 
# pd.options.display.max_rows = 999
# pd.options.display.max_columns = 999

# 參數設定
#ma_short_period = 4
#ma_long_period  = 56
ma_short_period = 5
ma_long_period  = 15
# 設定長線和短線的長度，要考慮資料裡每根 candle ohlcv 的單位
 
ma_short_type = 3
ma_long_type = 4
# 在 talib 的 MA 函數裡，0 代表 SMA，1 代表 EMA，2 代表 WMA，3 代表 DEMA，4 代表 TEMA

delay_period = 2
# 要延遲多少個報價

train_data_account_percent = 0.9
# 要對資料分割多少%給訓練

param_setting = {
                #'n_estimators': range(100),
                'n_estimators': [1,10,20,30,40,50,60,70,80,90,100],
                #'n_estimators': [1,10,100],
                'max_depth': [4,5,6],
                'subsample': [0.8],
                'learning_rate':[0.1],
                'objective': ['binary:logistic'],
                'seed':[42],
                'gamma':[0.1,0.2],
                'min_child_weight':[1]
            }

# 讀取csv
filename = sys.argv[1]
original_data = pd.read_csv(filename,index_col='Date') 
df = original_data.copy()
df.index = pd.to_datetime(df.index)

# 檢查
#print(df.tail())

# 檢查有沒有 NaN 的，刪掉，否則不好算
# print(df.isnull().any())
# print(df.isnull().any())
# df = df.dropna(how='any')

df = df[['Volume', 'Adj Close']]
df = df.drop(['Volume'],axis=1)

#print(df.head())
#print(df.tail())

# 計算MA
#df['ma_short'] = np.round(df['Adj Close'].rolling(window=5).mean(), 2)
#df['ma_long'] = np.round(df['Adj Close'].rolling(window=15).mean(), 2)
#df['ma_short'] = talib.MA(df['Adj Close'], timeperiod = 5, matype = 0)
#df['ma_long'] = talib.MA(df['Adj Close'], timeperiod = 15, matype = 0)

# 圖
#df.plot(grid=True, figsize=(8, 5))
#plt.show()

df['ma_short'] = talib.MA(df['Adj Close'], timeperiod = ma_short_period, matype = ma_short_type)
df['ma_long'] = talib.MA(df['Adj Close'], timeperiod = ma_long_period, matype = ma_long_type)
# 檢查
# print(df.tail())

# 圖
#df[['Adj Close', 'ma_short', 'ma_long']][-50:-30].plot(grid=True, figsize=(20, 10),linewidth=3)
#plt.show()
#print(df[-50:-30])

# 計算兩者之差
df['diff'] = df['ma_short'] - df['ma_long']
 
# Golden Crossing
# asign 大於0 = 1 小於0 = -1
asign = np.sign(df['diff'])
# print(asign)

# 處理 asign 有零的狀況（就是長短線得到一樣的值時，diff=0，會使 asign 回傳 0）
# 但在現實生活中幾乎不可能，所以不做也沒差
# sz 是用來處理是零的情況
'''
sz = asign == 0
while sz.any():
    asign[sz] = np.roll(asign, 1)[sz]
    sz = asign == 0
'''
# 黃金交叉就是在- 1 到 + 1 也就是 -1 - (+1) = -2 時發生
signchange = ((np.roll(asign, 1) - asign) == -2).astype(int)
#print("SIGNALCHANCE: ",signchange)
df['golden_cross'] = signchange
 
# Death Cross
asign = np.sign(df['diff'])
 
'''
一樣處理0
sz = asign == 0
while sz.any():
    asign[sz] = np.roll(asign, 1)[sz]
    sz = asign == 0
''' 
# 死亡交叉就是在 1 到 -1 也就是 1 - (-1) = 2 時發生
signchange = ((np.roll(asign, 1) - asign) == 2).astype(int)
df['death_cross'] = signchange
 
# 改為 -1
df['death_cross'][df['death_cross'] == 1] = -1
 
# 檢查
#print(df)

# 計算出有幾個黃金交叉、幾個死亡交叉
print("Golden Cross 黃金交叉總共有:", df['golden_cross'].sum(), "次")
print("Death Cross 死亡交叉總共有:", df['death_cross'].sum(), "次\n")
#print(df[0:5])
#print(df[25:34])
#print(df.tail())

# 找特徵
# 位移「當次報價之前的」前五次報價
df['Close_Pre_1'] = df['Adj Close'].shift(1)
df['Close_Pre_2'] = df['Adj Close'].shift(2)
df['Close_Pre_3'] = df['Adj Close'].shift(3)
df['Close_Pre_4'] = df['Adj Close'].shift(4)
df['Close_Pre_5'] = df['Adj Close'].shift(5)
df['diff_Pre_1'] = df['diff'].shift(1)
df['diff_Pre_2'] = df['diff'].shift(2)
df['diff_Pre_3'] = df['diff'].shift(3)
df['diff_Pre_4'] = df['diff'].shift(4)
df['diff_Pre_5'] = df['diff'].shift(5)
 
# diff
df['Close_Pre_1'] = df['Adj Close'] - df['Close_Pre_1']
df['Close_Pre_2'] = df['Adj Close'] - df['Close_Pre_2']
df['Close_Pre_3'] = df['Adj Close'] - df['Close_Pre_3']
df['Close_Pre_4'] = df['Adj Close'] - df['Close_Pre_4']
df['Close_Pre_5'] = df['Adj Close'] - df['Close_Pre_5']
df['diff_Pre_1'] = df['diff'] - df['diff_Pre_1']
df['diff_Pre_2'] = df['diff'] - df['diff_Pre_2']
df['diff_Pre_3'] = df['diff'] - df['diff_Pre_3']
df['diff_Pre_4'] = df['diff'] - df['diff_Pre_4']
df['diff_Pre_5'] = df['diff'] - df['diff_Pre_5']

# hold 2 次的情況下
df['profit_delay'] = df['Adj Close'].shift(-delay_period)
df['profit'] = df['profit_delay'] - df['Adj Close']
 
df.loc[df['profit'] > 0.00, 'result'] = 1 # hold好（等20分再買還是賺）
df.loc[df['profit'] <= 0.00, 'result'] = 0 # hold不好 （等20分再買會陪）
# print(df.head())
# print(df.tail())

# 真 黃金交叉
df_golden = df[df['golden_cross'] == 1]

df_golden = df_golden.drop(['diff', 'golden_cross', 'death_cross', 'profit', 'profit_delay'],axis=1)
# print("DF GOLDEN HEAD：")
#print(df_golden.tail())
 
data_array = df_golden.values

# 檢查
# print(data_array)

set_size = df_golden.shape[0]
set_property = df_golden.shape[1]
print(df_golden.shape) #should be (,14)
# print("n:",n)
# print("p:",p)
train_start = 0
train_end = int(np.floor(train_data_account_percent*set_size))
test_start = train_end + 1
test_end = set_size
train_set = data_array[np.arange(train_start, train_end), :]
test_set = data_array[np.arange(test_start, test_end), :]
 
# print("train set:",train_set)

x_train = train_set[:, :set_property-1]
y_train = train_set[:, -1]

# print("XTRAIN:",x_train)
# print("YTRAIN:",y_train)

x_test = test_set[:, :set_property-1]
y_test = test_set[:, -1]

# 濾掉nan
y_train = np.where(np.isnan(y_train), 0, y_train)
y_test = np.where(np.isnan(y_test), 0, y_test)

# print(x_train[0])
# print(y_train[0])
#print(x_train[0], '／',y_train[0]) # 印出第一筆就好
print('y_train.sum() =',y_train.sum()) # 因為每筆都是 1 ，所以 .sum() 相當於回傳有幾筆
print('y_test.sum() =',y_test.sum(), '\n')

# y_train = y_train.reshape(len(y_train), )

'''
# 單純樹分類
clf_2 = DecisionTreeClassifier(max_depth=2)
clf_2 = clf_2.fit(x_train,y_train)
pred_test_2 = clf_2.predict(x_test)

matrix2 = confusion_matrix(y_test,pred_test_2)
print(matrix2)
print("精確率：",accuracy_score(y_test, pred_test_2), '\n')

dot_data = tree.export_graphviz(clf_2, out_file=None, 
                         feature_names=df.columns[1:14],  
                         class_names=df.columns[0],
                         rounded = True, 
                         filled=True
                         )  
graph = graphviz.Source(dot_data)  
#graph.view()
'''

clf = xgb.XGBClassifier()
grid = GridSearchCV(clf, param_grid = param_setting, cv = 5, scoring = 'accuracy', verbose = 1)

#print("給定的參數：")
#print(param_setting, '\n')

grid.fit(x_train, y_train)
'''
print("開始在給定的範圍裏面輸找參數:")
print(grid, '\n')

print("訓練算法：")
print(grid.fit(x_train, y_train), '\n')
'''

#print("輸出最佳參數：")
#print(grid.best_params_, '\n')

# 訓練出模型！
print('\n',"建立模型：")
print(clf.fit(x_train, y_train), '\n')

# 用這個模型，帶入 test set 的資料
test_pred = clf.predict(x_test)

#print(y_test)
#print(test_pred)

# 輸出我們最關心的 confusion_matrix
print("Confusion_Matrix：")
print(confusion_matrix(y_test, test_pred, labels = [1, 0]), '\n')

print("檔案名稱：",filename,"，精確率：", accuracy_score(y_test, test_pred), '\n')

test_proba = clf.predict_proba(x_test)

#print("輸出每次交叉時的可信度：")
#print(test_proba, '\n')


'''
thresholds = [.1,.2,.3,.4,.5,.6,.7,.8,.9]
tmp_max = 0
tmp_max_ct = 0
tmp_min = 1.1
tmp_min_ct = 0
for i in zip(thresholds):
    y_test_predictions = test_proba[:,1] > i
    cnf_matrix = confusion_matrix(y_test, y_test_predictions, labels = [1, 0])
    np.set_printoptions(precision=2)
    print('Threshold:', i)
    #print('precision Score:', precision_score(y_test, y_test_predictions))
    
    if(precision_score(y_test, y_test_predictions) > tmp) :
        tmp_max = precision_score(y_test, y_test_predictions)
        tmp_max_ct = i
    
    if(precision_score(y_test, y_test_predictions) < tmp2):
        tmp_min = precision_score(y_test, y_test_predictions)
        tmp_min_ct = i
    
    #print('Precision Score:', precision_score(y_train, y_train_predictions))
    #print('AVG Precision Score:', average_precision_score(y_train, y_train_predictions))
    print(cnf_matrix)
    print('-------------------------')

print("MAX:", tmp_max_ct, tmp_max)
print("MIN:", tmp_min_ct, tmp_min)
'''