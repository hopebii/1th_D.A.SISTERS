from django.shortcuts import render

import pandas as pd
import numpy as np
import warnings; warnings.filterwarnings('ignore')

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import requests
import urllib.request
import json
from collections import OrderedDict

novel = pd.read_csv('novel.csv',encoding='cp949').drop('Unnamed: 0',axis=1)
review = pd.read_csv('review.csv')
text =  pd.read_csv('text.csv').drop('Unnamed: 0',axis=1)
cos =  pd.read_csv('cosine_sim.csv').drop('Unnamed: 0',axis=1)



def main(request):
    return render(request, 'main.html')


def q_base(request):
    return render(request, 'q_base.html')

def q1(request):
    return render(request, 'q1.html')

adult = 0 
finish = 0 

def q2(request):
    if request.method == 'GET':
        if request.GET.get('adultchild') =='adult_yes' :
              adult = 1 # adult_yes / adult_no
        if request.GET.get('finished') == 'finish_yes' : 
              finish = 1 # finish_yes / finish_no
    return render(request, 'q2.html')

cf = 0 
cb = 0 


dict_user = {'like' : 0 , 'avgrating' : 0 , 'totalreview':0, 'purchase':0, 'waiting':0, 'keywords':0}

def q3(request):
    if request.method == 'GET':
        selected = request.GET.get('chb')
        for i in selected :  
            dict_user[i-1] = 1 

        search = request.GET.get('search') # 검색어. json 형태로 보내기 
        idx_list = []
        for i in range(len(novel)) : 
            if str(search) in novel['제목'][i] : 
                idx_list.append(i)
        
        

        idx_dict = {
            'image' : novel.loc[idx_list,'썸네일'].tolist()  , 
            'title' : novel.loc[idx_list,'제목'].tolist()  ,
            'author': novel.loc[idx_list,'작가'].tolist()  ,
            'genre' : novel.loc[idx_list,'장르'].tolist()
        }

        targetJson = json.dumps(idx_dict)


        return render(request, 'q3.html',{'targetjson' : targetJson})
        

# 프론트 : 별점 평가, 장바구니 담기기 -- novellist (가상 유저 데이터 프레임 생성)





# (1차완) 추천 코드 복붙 & 수정 -- 추천 결과 리스트 json 반환되게 하기 -- 프론트에 넘기는 
################################################
## 1. 성인, 완결 필터링 ##
a = [] # 리뷰에서도 작품을 제외하기 위한 list -> 이 안의 작품들은 리뷰에서 지워짐
f = []

if adult == 1:
    a = novel[novel['성인'] == True].index.tolist()
    
if finish == 1:
    f = novel[novel['완결'] == False].index.tolist()
    
# 이중리스트를 제거하고 중복 값 삭제
f_book = list(set(sum([a, f], [])))

# 리뷰에서 필터링된(f_book) 작품 제거
idx_del_review = review[review['novelindex'].isin(f_book)].index
idx_del_novel = novel[novel['novelindex'].isin(f_book)].index

review_new = review.drop(idx_del_review)
novel_new = novel.drop(idx_del_novel)

##2. CB##
indices = pd.Series(novel['제목'])
cos = np.array(cos)

def recommended_wn_each(title, cosine_sim = cos):

    recommended_wn = []
    idx = indices[indices == title].index[0]
    score_google = pd.Series(cos[idx]).iloc[novel.index].sort_values(ascending = False)
    score_google=score_google.iloc[novel.index]
    top_10_indices = score_google.iloc[2:11].index  
    
    for i in top_10_indices:
        recommended_wn.append(novel['제목'][i])
        
    return recommended_wn

def cb_recommend_all(index):
    topn=[]
    title_list = list(novel['제목'].iloc[user['novelindex']])
    for i in title_list :
        for j in recommended_wn_each(i) :
            topn.append(j)
    return list(set(topn))

def top_10(index) : 
    
    cb = 0 
    
    list_topn = cb_recommend_all(index)
    list_gidamoo = [] 
    for i in range(len(novel)) : 
        if novel['제목'][i] in list_topn : 
            list_gidamoo.append((i,novel['제목'][i],novel['기다무'][i], novel['무료공개'][i],novel['가중평균'][i]))
  
    df=pd.DataFrame({x[0]:x[1:] for x in list_gidamoo}).T.reset_index()
    df.columns = ['index','제목','기다무','무료공개','가중평균']

    if waiting == 1:
        df['기다무'] = scaler.fit_transform(df[['기다무']]) + 1
        df['가중평균'] = df['가중평균'] * df['기다무']

        df['무료공개'] = scaler.fit_transform(df[['무료공개']]) + 1
        df['가중평균'] = df['가중평균'] * df['무료공개']     
        
        cb += 1
    
    if keywords == 1:
        
        cb += 2

    return df[['index','제목','가중평균']].sort_values(by = '가중평균', ascending= False)[:2+cb]['index'].tolist()

cb_recmm=top_10(user['novelindex'])

##2. CF##
# review에 없는 작품 index list에 append
d = review.novelindex.sort_values().unique().tolist()
x = range(0, 457)
nonereview = []

sd = sum(d)
xd = sum(x)

for i in x: 
    if i not in d:
        nonereview.append(i)

if like == 1:
    like_scale = scaler.fit_transform(novel_new[['좋아요수']]) + 1
    like_scale = sum(like_scale.tolist(), [])
    
    # 계산된 가중치에서 rating table에 없는 것들 제외(행렬곱을 위함)
    for index in sorted(nonereview, reverse = True):
        del like_scale[index]
    
    cf += 1

if avgrating == 1:
    avgrating_scale = scaler.fit_transform(novel_new[['평균별점']]) + 1
    avgrating_scale = sum(avgrating_scale.tolist(), [])
    
    for index in sorted(nonereview, reverse = True):
        del avgrating_scale[index]
        
    cf += 1

if totalreview == 1:
    totalreview_scale = scaler.fit_transform(novel_new[['전체리뷰수']]) + 1
    totalreview_scale = sum(totalreview_scale.tolist(), [])
    
    for index in sorted(nonereview, reverse = True):
        del totalreview_scale[index]
    
    cf += 1
    
if purchase == 1:
    purchase_scale = scaler.fit_transform(novel_new[['구매자수']]) + 1
    purchase_scale = sum(purchase_scale.tolist(), [])
    
    for index in sorted(nonereview, reverse = True):
        del purchase_scale[index]
    
    cf += 1

review_user = pd.concat([user, review_new], axis = 0)

# user rating matrix
ratings = review_user.pivot_table('평점', index = 'ID', columns = 'novelindex')
ratings = ratings.fillna(0) # 없는 평점은 0으로

# item dim_df -> 영화간 유사도 계산
ratings_T = ratings.transpose()
item_sim = cosine_similarity(ratings_T, ratings_T)
item_sim_df = pd.DataFrame(data = item_sim, index = ratings.columns, columns = ratings.columns)

# 예측 평점을 구하는 함수, R(u, i)에 관한 식
def predict_rating(ratings_arr, item_sim_arr):
    ratings_pred = ratings_arr.dot(item_sim_arr) / np.array([np.abs(item_sim_arr).sum(axis=1)])
    return ratings_pred

predict = predict_rating(ratings, item_sim_df)


# 가중치 부여 
if like == 1:
    predict * np.array(like_scale)

if avgrating == 1:
    predict * np.array(avgrating_scale)

if purchase == 1:
    predict * np.array(purchase_scale)

if totalreview == 1:
    predict * np.array(totalreview_scale)
    

# 유저가 보지 않은 소설 반환
def unseen_item(ratings, ID):
    user_rating = ratings.loc[ID, :]
    already_seen = user_rating[user_rating>0].index.tolist()
    
    novel_list = ratings.columns.tolist()
    unseen_list = [novel for novel in novel_list if novel not in already_seen]
    
    return unseen_list

# 추천
def cf_item_recomm(pred_df, ID, unseen_list, top_n=10):
    recomm_novel = pred_df.loc[ID, unseen_list].sort_values(ascending=False)[:top_n]
    return recomm_novel

ID = 'user'

unseen_lst = unseen_item(ratings, ID)
recomm_novel = cf_item_recomm(predict, ID, unseen_lst, top_n = 2 + cf)

# list와 dataframe중 어떻게 넘길지?
# 상위 추천 작품 list (인덱스형태)
cf_recmm = recomm_novel.index.tolist()

##4. 추천 결과 합치기##
recmm_idx = cb_recmm + cf_recmm

recmm_dict = {
            'image' : novel.loc[recmm_idx,'썸네일'].tolist()  , 
            'title' : novel.loc[recmm_idx,'제목'].tolist()  ,
            'author': novel.loc[recmm_idx,'작가'].tolist()  ,
            'genre' : novel.loc[recmm_idx,'장르'].tolist()
        }

recomm_Json = json.dumps(recmm_dict)


#####################################################

def loading(request):
    return render(request, 'loading.html')

def novel_list(request):
    return render(request, 'novel_list.html')


def result(request):
    return render(request, 'result.html')


