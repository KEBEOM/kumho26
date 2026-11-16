"""추가 입력으로 발견된 오류의 재발 방지 및 Word 내보내기 검증."""
from pathlib import Path
from io import BytesIO
import sys
import zipfile
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import analysis as A
from report_export import build_report_docx


@pytest.mark.parametrize('unit', [1e-8, 1., 1e8])
def test_regression_scale_stability(unit):
    x = np.arange(20, dtype=float) * unit
    y = 3 + np.arange(20)*2 + np.random.default_rng(3).normal(size=20)
    result = A.regression(pd.DataFrame({'x': x, 'y': y}), 'y', ['x'])
    independent = stats.linregress(x, y)
    assert result['coef'].iloc[0]['B'] == pytest.approx(independent.intercept, abs=1e-9)
    assert result['coef'].iloc[1]['B'] == pytest.approx(independent.slope, rel=1e-10)
    assert result['coef'].iloc[1]['SE'] == pytest.approx(independent.stderr, rel=1e-10)
    assert result['r2'] == pytest.approx(independent.rvalue**2)


def test_regression_perfect_fit_friendly():
    with pytest.raises(A.AnalysisError, match='잔차'):
        A.regression(pd.DataFrame({'x': np.arange(10), 'y': 3+2*np.arange(10)}), 'y', ['x'])


@pytest.mark.parametrize('invalid', [np.inf, -np.inf, np.nan])
def test_nonfinite_excluded(invalid):
    d = pd.DataFrame({'x': [1,2,3,4,5,6], 'y': [3,4,7,invalid,12,14]})
    r = A.regression(d, 'y', ['x'])
    assert r['n'] == 5 and r['dropped'] == 1
    assert np.isfinite(r['coef']['B']).all()


def test_collinear_friendly():
    d = pd.DataFrame({'x':range(10), 'z':np.arange(10)*2, 'y':[2,4,5,9,12,14,15,18,19,20]})
    with pytest.raises(A.AnalysisError, match='공선성'):
        A.regression(d,'y',['x','z'])


def test_alpha_total_constant():
    with pytest.raises(A.AnalysisError, match='총점'):
        A.cronbach_alpha(pd.DataFrame({'a':[1,2,3,4,5], 'b':[5,4,3,2,1]}), ['a','b'])


def test_alpha_undefined_not_classified_low():
    sentence = A.alpha_sentence({'alpha':np.nan})
    assert '판정하지' in sentence
    assert '낮은' not in sentence and 'nan' not in sentence


def test_normality_large_sample_actual_n():
    rng=np.random.default_rng(44)
    values=np.r_[rng.normal(size=5000),rng.exponential(20,size=5000)]
    row=A.normality(pd.DataFrame({'v':values}),['v'])['table'].iloc[0]
    selected=np.random.default_rng(2026).choice(values,5000,replace=False)
    expected=stats.shapiro(selected)
    assert row['n']==10000 and row['검정 n']==5000
    assert '무작위' in row['검정 표본']
    assert row['p']==pytest.approx(expected.pvalue)
    assert row['Shapiro-Wilk W']==pytest.approx(expected.statistic)
    assert row['p'] < .05


def test_normality_nonfinite_and_small():
    row=A.normality(pd.DataFrame({'v':[1,2,3,4,np.inf]}),['v'])['table'].iloc[0]
    assert row['n']==4 and row['검정 n']==4
    row=A.normality(pd.DataFrame({'v':[1,2]}),['v'])['table'].iloc[0]
    assert row['검정 n']==0


@pytest.mark.parametrize('center',[False,True])
def test_moderation_keeps_original_missing_count(center):
    d=pd.read_excel(Path(__file__).resolve().parents[1]/'data/reference_data.xlsx')
    d.loc[0,'mod_y']=np.nan
    r=A.moderation(d,'mod_x','mod_w','mod_y',center=center)
    assert r['n']==35 and r['dropped']==1


def test_multiregression_conditional_sentence():
    d=pd.read_excel(Path(__file__).resolve().parents[1]/'data/reference_data.xlsx')
    r=A.regression(d,'score',['study_time','pre_score'])
    assert '다른 독립변수를 일정하게' in A.regression_sentence(r)


def test_docx_is_real_ooxml_and_contains_report():
    frame=pd.DataFrame({'변수':['학습시간'], 'B':[.125], 'p':['< .001']})
    sections=[{'title':'다중회귀','data':'연습.xlsx','time':'12:00','missing':'결측 1행 제외',
               'parts':[('table','회귀계수',frame,False),('text','다른 변수를 일정하게 두었을 때의 관계입니다.'),('apa','R² = .500')]}]
    content=build_report_docx(sections,'빅데이터 8조')
    with zipfile.ZipFile(BytesIO(content)) as z:
        assert 'word/document.xml' in z.namelist()
    doc=Document(BytesIO(content))
    paragraphs='\n'.join(p.text for p in doc.paragraphs)
    assert '결측 1행 제외' in paragraphs and 'R² = .500' in paragraphs
    assert doc.tables[0].cell(1,0).text=='학습시간'
    assert doc.tables[0].cell(1,2).text=='< .001'


def test_docx_wide_table_landscape():
    frame=pd.DataFrame([range(10)],columns=[f'열{i}' for i in range(10)])
    doc=Document(BytesIO(build_report_docx([{'title':'넓은 표','data':'예제','time':'12:00','parts':[('table','기초통계',frame,False)]}],'8조')))
    assert doc.sections[0].page_width > doc.sections[0].page_height
    assert len(doc.tables[0].columns)==10
