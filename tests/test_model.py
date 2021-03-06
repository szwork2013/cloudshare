# -*- coding: utf-8 -*-
import os.path
import functools

import yaml


FIRST_PAGE = range(20)

PERFECT = 100
GOOD = 50
POOR = 25
BAD = 0

kgr_file = 'tests/known_good_jd_cv_mapping.yaml'
with open(kgr_file) as f:
    datas = yaml.load(f)


def kgr_percentage(jd_id, jd_service, sim, cvs=None, index_service=None, filterdict=None, percentage=100, above_allow=False):
    """
        >>> from tests.test_model import *
        >>> from webapp.settings import *
        >>> jd_service = SVC_PRJ_MED.jobdescription
        >>> sim = SVC_MIN.sim['medical']['medical']
        >>> assert kgr_perfect('9bbc45a81e4511e6b7066c3be51cefca', jd_service, sim)
        >>> assert kgr_good('098a91ca0b4f11e6abf46c3be51cefca', jd_service, sim)
        >>> assert kgr_poor('098a91ca0b4f11e6abf46c3be51cefca', jd_service, sim, above_allow=True)
        >>> assert kgr_poor('be97722a0cff11e6a3e16c3be51cefca', jd_service, sim)
        >>> assert kgr_bad('06fdc0680b5d11e6ae596c3be51cefca', jd_service, sim)
        >>> assert kgr_percentage('e290dd36428a11e6b2934ccc6a30cd76', jd_service, sim, percentage=33)
        >>> jd_id, cvs = '2fe1c53a231b11e6b7096c3be51cefca', ['3hffapdz', '2x5wx4aa']
        >>> assert kgr_bad(jd_id, jd_service, sim, cvs=cvs)
        >>> assert kgr_bad('cce2a5be547311e6964f4ccc6a30cd76', jd_service, sim, cvs=['qfgwkkhg', 'nji2v4s7', 'qssipwf9'])
        >>> assert kgr_percentage('cce2a5be547311e6964f4ccc6a30cd76', jd_service, sim, cvs=['qfgwkkhg', 'nji2v4s7', 'qssipwf9'], index_service=SVC_INDEX, filterdict={'expectation_places': ['长沙'.decode('utf-8')]}, percentage=int(float(2)/3*100))
    """
    if cvs is None:
        cvs = datas[jd_id]
    if not hasattr(cvs, '__iter__'):
        cvs = {cvs}
    success_count = kgr(jd_id, cvs, jd_service, sim, index_service, filterdict)
    if percentage == PERFECT:
        return success_count == len(cvs)
    elif percentage == GOOD:
        return len(cvs)*0.5 <= success_count and (success_count < len(cvs) or above_allow)
    elif percentage == POOR:
        return len(cvs)*0.25 <= success_count and (success_count < len(cvs)*0.5 or above_allow)
    elif percentage == BAD:
        return success_count == 0 or above_allow
    elif 0 < percentage < 100:
        return len(cvs)*float(percentage)/100 <= success_count and (success_count < len(cvs) or above_allow)

kgr_perfect = functools.partial(kgr_percentage, percentage=PERFECT)
kgr_good = functools.partial(kgr_percentage, percentage=GOOD)
kgr_poor = functools.partial(kgr_percentage, percentage=POOR)
kgr_bad = functools.partial(kgr_percentage, percentage=BAD)

def kgr(jd_id, cvs, jd_service, sim, index_service, filterdict):
    sucess_count = 0
    _ranks = ranks(jd_id, jd_service, sim, cvs, index_service, filterdict)
    for _rank in _ranks.values():
        if _rank in FIRST_PAGE:
            sucess_count += 1
    return sucess_count

def ranks(jd_id, jd_service, sim, cvs=None, index_service=None,
            filterdict=None):
    if cvs is None:
        cvs = datas[jd_id]
    job_desc = jd_service.get(jd_id)['description']
    score_board = sim.probability(job_desc)
    if index_service is not None and filterdict is not None:
        filteset = index_service.get(filterdict)
        score_board = filter(lambda x: os.path.splitext(x[0])[0] in filteset,
                             score_board)
    ranks_dict = {}
    for cv_id in cvs:
        for _rank, (_c, _s) in enumerate(score_board):
            if cv_id == _c:
                ranks_dict[cv_id] = _rank
    return ranks_dict
