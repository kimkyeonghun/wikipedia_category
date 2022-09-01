import argparse
import json
import os
import time

import pymysql
import pandas as pd

parser = argparse.ArgumentParser()
#DB args
parser.add_argument("--db_id", type=str, default='root')
parser.add_argument('--db_password', type=str)
parser.add_argument('--db_name', type=str, default='wikipedia')

#model args
parser.add_argument('--mode', type=str, choices=['a','u','l'])
parser.add_argument('--depth', type=int, default=5)

args = parser.parse_args()


def decode_dataframe(byte):
    # 바이트에서 스트링으로 변환
    return byte.decode()

def __cat_parent_tree(cur, cat):
    # page_namespace=14는 분류 페이지를 의미함
    sql = "select page_id, page_title from wikipedia_ko.page where page_title='{}' and page_namespace=14".format(
        cat)
    cur.execute(sql)
    page_id = cur.fetchall()
    # 검색 결과가 없을 경우
    if len(page_id)==0:
        return []
    else:
        page_id = page_id[0]['page_id']

    # categorylinks.cl_from == page.page_id
    sql = "select cl_from, cl_to from wikipedia_ko.categorylinks where cl_from={}".format(
        page_id)
    cur.execute(sql)
    rows = cur.fetchall()
    df = pd.DataFrame(rows)
    parents_cats = df['cl_to'].apply(decode_dataframe).tolist()

    return parents_cats


def __cat_sub_tree(cur, cat):
    sql = "select cl_from from wikipedia_ko.categorylinks where cl_to='{}' and cl_type='subcat';".format(
        cat)
    cur.execute(sql)
    rows = cur.fetchall()
    if len(rows) == 0:
        return []

    df = pd.DataFrame(rows)
    sub_page_ids = ", ".join(map(str, df['cl_from'].tolist()))

    #다중탐색을 위해
    sql = "select page_title, page_namespace from wikipedia_ko.page where page_id in ({})".format(
        sub_page_ids)
    cur.execute(sql)
    rows = cur.fetchall()
    df = pd.DataFrame(rows)
    sub_cats = df['page_title'].apply(decode_dataframe).tolist()

    return sub_cats

def _cat_parent_tree_rec(cur, cat, depth, tree, level):
    """
        category: {
            level: int,
            parent-categoeis: dict()        
            }
    """
    global categories

    if tree.get(cat) is None:
        tree[cat] = dict()
    tree[cat]['depth'] = level
    tree[cat]['parent-categories'] = dict()
    if cat not in categories:
        try:
            parent_cats = __cat_parent_tree(cur, cat)
        except IndexError:
            raise IndexError("May be wrong input")
    else:
        return

    if "숨은_분류" in parent_cats:
        del tree[cat]
        return
    elif depth and level >= depth:
        for ctg in parent_cats:
            temp_parent_cats = __cat_parent_tree(cur, ctg)
            if "숨은_분류" in temp_parent_cats:
                continue
            else:
                tree[cat]['parent-categories'][ctg] = None
    else:
        for ctg in parent_cats:
            if ctg in ['주제_분류', '주제별_분류_체계', '주제별_분류']:
                tree[cat]['parent-categories'][ctg] = None
                return
            else:
                categories.append(cat)
                _cat_parent_tree_rec(cur, ctg, depth, tree[cat]['parent-categories'], level+1)
                categories.pop()

def _cat_sub_tree_rec(cur, cat, depth, tree, level):
    global categories
    if tree.get(cat) is None:
        tree[cat] = dict()
    tree[cat]['depth'] = level
    tree[cat]['sub-categories'] = dict()
    if cat not in categories:
        try:
            sub_cats = __cat_sub_tree(cur, cat)
        except IndexError:
            raise IndexError("May be wrong input")
    else:
        return
    
    if "숨은_분류" in sub_cats:
        del tree[cat]
        return
    elif depth and level >= depth:
        for ctg in sub_cats:
            tree[cat]['sub-categories'][ctg] = None
    else:
        for ctg in sub_cats:
            categories.append(cat)
            _cat_sub_tree_rec(cur, ctg, depth, tree[cat]['sub-categories'], level+1)
            categories.pop()

if __name__ == '__main__':
    con = pymysql.connect(host='localhost', user=args.db_id, password=args.db_password,
    db='wikipedia_ko', charset='utf8', cursorclass=pymysql.cursors.DictCursor)
    cur = con.cursor()

    keyword = input("Enter keyword: ")
    keyword = "_".join(keyword.split(' '))

    hirerarchy_keyword = dict()

    categories = []
    start_time = time.time()
    if args.mode=='a':
        _cat_parent_tree_rec(cur, keyword, 3, hirerarchy_keyword, 1)
        categories = []
        mid_time = time.time()
        print("[ALL mode] Upper category time: ", mid_time - start_time)
        _cat_sub_tree_rec(cur, keyword, 1, hirerarchy_keyword, 1)
        end_time = time.time()
        print("[ALL mode] Lower category time: ", end_time - mid_time)
        print("[ALL mode] Total category time: ", end_time - start_time)
    elif args.mode=='u':
        _cat_parent_tree_rec(cur, keyword, args.depth, hirerarchy_keyword, 1)
        print("[Upper mode] Upper category time: ", time.time() - start_time)
    elif args.mode=='l':
        _cat_sub_tree_rec(cur, keyword, args.depth, hirerarchy_keyword, 1)
        print("[Lower mode] Lower category time: ", time.time() - start_time)
    
    if not os.path.exists('./results'):
        os.mkdir('./results')
        
    with open(f"./results/{keyword}.json", 'w') as outfile:
        json.dump(hirerarchy_keyword, outfile)
    con.close()