# -*- coding: utf-8 -*-
import re
import numpy

import utils.builtin
import core.mining.info
import core.mining.lsimodel
import core.outputstorage

from extractor.utils_parsing import *


EDUCATION_REQUIREMENT = re.compile(ur'(?P<education>.+)[及或]?以上学历')


def rate(miner, svc_cv, doc, top=10, selected=5, uses=None, name_list=None):
    result = []
    rating = next(miner, svc_cv, doc, top, uses=uses, name_list=name_list)
    blank, reference = rating.pop(0)
    candidate = [r[1] for r in reference]
    for text, rate in rating:
        score = []
        high = [r[1] for r in rate]
        for i, n in enumerate(candidate):
            if n not in high:
                score.append(0.)
            else:
                score.append(float(rate[high.index(n)][2]))
        precent = [(float(each))*100 for each in score]
        if name_list is not None:
            namelist_candidate = []
            namelist_precent = []
            namelist_score = []
            for name in name_list:
                id = name.split('.')[0]
                index = candidate.index(id)
                namelist_candidate.append(candidate[index])
                namelist_precent.append(precent[index])
                namelist_score.append(score[index])
            result.append((text, zip(namelist_candidate,
                                     namelist_precent, namelist_score)))
        else:
            result.append((text, zip(candidate[:selected],
                                     precent[:selected],
                                     score[:selected])))
    return result
    
def extract(datas):
    result = []
    for i, d in enumerate(datas):
        result.append((i, d[0].split('.')[0], d[1]))
    return result

def next(miner, svc_cv, doc, top, uses=None, name_list=None):
    rating = []
    extract_data_full = []
    if name_list is not None:
        names_data_full = miner.minelist(doc, name_list, uses=uses)
        extract_data_full.extend(extract(names_data_full))
    else:
        name_list = []
        top_data_full = miner.minetop(doc, top, uses=uses)
        extract_data_full = extract(top_data_full)
        name_list.extend([core.outputstorage.ConvertName(each[1]).md
                          for each in extract_data_full])
    rating.append((doc, extract_data_full))
    total = miner.lenght(uses=uses)
    for text in doc.split('\n'):
        if not text.strip():
            continue
        education_requirement = EDUCATION_REQUIREMENT.match(text)
        if education_requirement:
            new_data = mine_education(svc_cv,
                education_requirement.group('education'), name_list)
        else:
            result = miner.minelistrank(text, name_list, uses=uses)
            new_data = zip(name_list, map(lambda x: rankvalue(x, total), result))
        if len(filter(lambda x: float(x[1])> 0., new_data)) > 0:
            rating.append((text, extract(new_data)))
    return rating

def rankvalue(rank, total):
    # best 5% use 20% point, top 5~20% use 20% point,
    # middle 20% ~ 60% use 40% point, the last 40% use 20% point,
    rankvalue = 0 # float(total-rank)/total
    beststandard = total*0.05
    topstandard = total*0.15
    midstandard = total*0.4
    botstandard = total*0.4
    if rank < beststandard:
        rankvalue = 0.8 + float(total*0.05 - rank)/beststandard*0.2
    elif rank > beststandard and rank < total*0.2:
        rankvalue = 0.6 + float(total*0.2 - rank)/topstandard*0.2
    elif rank > topstandard and rank < total*0.6:
        rankvalue = 0.2 + float(total*0.6 - rank)/midstandard*0.4
    else:
        rankvalue = float(total - rank)/botstandard*0.2
    return rankvalue

def mine_education(svc_cv, text, name_list):
    def education_rate(education):
        for (k, RE) in EDUCATION_LIST.items():
            if RE.match(education):
                return k
        else:
            return 0

    assert text
    assert name_list
    datas = []
    for name in name_list:
        education = education_rate(svc_cv.getyaml(name)['education'])
        req = education_rate(text)
        if education and req:
            datas.append((name, str((5 + education - req)*0.1)))
    return datas
