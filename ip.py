# 📈 IP 성과 자세히보기 — Standalone v2.0
# 원본 Dashboard.py에서 'IP 성과 자세히보기' 페이지만을 추출한 단독 실행 파일입니다.

#region [ 1. 라이브러리 임포트 ]
# =====================================================
import re
from typing import List, Dict, Any, Optional 
import time, uuid
import textwrap

import numpy as np
import pandas as pd
import plotly.express as px
from plotly import graph_objects as go
import plotly.io as pio
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

import gspread
from google.oauth2.service_account import Credentials
#endregion


#region [ 1-0. 페이지 설정 — 반드시 첫 번째 Streamlit 명령 ]
# =====================================================
st.set_page_config(
    page_title="시청자 반응 브리핑", # 페이지 타이틀 수정
    layout="wide",
    initial_sidebar_state="collapsed"
)
#endregion


#region [ 1-1. 사이드바 타이틀 ]
# =====================================================
# [수정] 인증 관련 함수는 모두 삭제하고, 사이드바 UI와 _rerun만 남깁니다.

def _rerun():
    """세션 상태 변경 후 페이지를 새로고침합니다."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

with st.sidebar:
    st.markdown(
        """
        <div class="page-title-wrap">
          <span class="page-title-emoji">📈</span>
          <span class="page-title-main">IP-시청자 반응 브리핑</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='sidebar-contact' style='font-size:12px; color:gray; text-align:center;'>문의 : 미디어)디지털마케팅팀 데이터파트</p>",
        unsafe_allow_html=True
    )
    
    # [수정] 관리자 모드 로그인 UI 전체 삭제

#endregion


#region [ 2. 공통 스타일 통합 ]
# =====================================================
# (이 영역은 원본과 동일하게 유지됩니다)
st.markdown("""
<style>

 /* -------------------------------------------------------------------
   0. [추가] 스트림릿 기본 헤더(Toolbar) 숨기기
   ------------------------------------------------------------------- */
header[data-testid="stHeader"] {
    display: none !important; /* 상단 헤더 영역 전체 숨김 */
}
div[data-testid="stDecoration"] {
    display: none !important; /* 상단 컬러 데코레이션 바 숨김 */
}

/* --- [추가] 메인 컨텐츠 상단 패딩 줄이기 (가장 중요) --- */
div[data-testid="stAppViewBlock"] {
    padding-top: 1rem !important; /* 메인 블록 상단 여백을 줄임 */
}
.block-container {
    padding-top: 0rem !important; /* 위젯 컨테이너의 상단 패딩을 제거 */
}
            
/* --- [기본] Hover foundation & Title/Box exceptions --- */
div[data-testid="stVerticalBlockBorderWrapper"]{
    transition: transform .18s ease, box-shadow .18s ease !important;
    will-change: transform, box-shadow;
    overflow: visible !important;
    position: relative;
    pointer-events: auto;
}
section[data-testid="stVerticalBlock"] h1,
section[data-testid="stVerticalBlock"] h2,
section[data-testid="stVerticalBlock"] h3 {
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.25;
}
section[data-testid="stVerticalBlock"] h1 { font-size: clamp(28px, 2.8vw, 38px); }
section[data-testid="stVerticalBlock"] h2 { font-size: clamp(24px, 2.4vw, 34px); }
section[data-testid="stVerticalBlock"] h3 { font-size: clamp(22px, 2.0vw, 30px); }

.page-title {
    font-size: clamp(26px, 2.4vw, 34px);
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -0.02em;
    margin: 6px 0 14px 0;
    display: inline-flex;
    align-items: center;
    gap: 10px;
}

/* Remove box background/border/shadow for KPI, titles, filters, mode switchers */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-card),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.page-title),
div[data-testid="stVerticalBlockBorderWrapper"]:has(h1),
div[data-testid="stVerticalBlockBorderWrapper"]:has(h2),
div[data-testid="stVerticalBlockBorderWrapper"]:has(h3),
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stSelectbox"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stMultiSelect"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stSlider"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stRadio"]),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.filter-group),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.mode-switch) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 0.5rem !important;
}

/* --- [기본] Background & Hover (Legacy) --- */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(1200px 500px at 10% -10%, rgba(99, 102, 241, 0.05), transparent 40%),
                radial-gradient(1200px 500px at 90% -20%, rgba(236, 72, 153, 0.05), transparent 40%),
                #f7f8fb;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{
    transform: translateY(-2px);
    box-shadow: 0 14px 36px rgba(16, 24, 40, 0.14), 0 4px 12px rgba(16, 24, 40, 0.08);
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{
    transform: translate3d(0, -2px, 0) !important;
    box-shadow: 0 14px 36px rgba(16, 24, 40, 0.14), 0 4px 12px rgba(16, 24, 40, 0.08) !important;
    z-index: 2;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{
  transform: none !important;
  box-shadow: inherit !important;
  z-index: auto !important;
}
section[data-testid="stSidebar"] .kpi-card:hover,
section[data-testid="stSidebar"] .block-card:hover,
section[data-testid="stSidebar"] .stPlotlyChart:hover,
section[data-testid="stSidebar"] .ag-theme-streamlit .ag-root-wrapper:hover{
  transform: none !important;
  box-shadow: inherit !important;
}
.kpi-card, .block-card, .stPlotlyChart, .ag-theme-streamlit .ag-root-wrapper{
  transition: transform .18s ease, box-shadow .18s ease;
  will-change: transform, box-shadow;
  backface-visibility: hidden;
  -webkit-font-smoothing: antialiased;
}
.kpi-card:hover, .block-card:hover, .stPlotlyChart:hover, .ag-theme-streamlit .ag-root-wrapper:hover{
  transform: translateY(-2px);
  box-shadow: 0 14px 36px rgba(16,24,40,.14), 0 4px 12px rgba(16,24,40,.08);
}


/* --- [기본] 지표기준안내 (gd-guideline) --- */
.gd-guideline { font-size: 13px; line-height: 1.35; }
.gd-guideline ul { margin: .2rem 0 .6rem 1.1rem; padding: 0; }
.gd-guideline li { margin: .15rem 0; }
.gd-guideline b, .gd-guideline strong { font-weight: 600; }
.gd-guideline code{
  background: rgba(16,185,129,.10);
  color: #16a34a;
  padding: 1px 6px;
  border-radius: 6px;
  font-size: .92em;
}

/* --- [기본] 앱 배경 / 카드 스타일 --- */
[data-testid="stAppViewContainer"] {
    background-color: #f8f9fa; /* 매우 연한 회색 배경 */
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff;
    border: 1px solid #e9e9e9;
    border-radius: 10px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    padding: 1.25rem 1.25rem 1.5rem 1.25rem;
    margin-bottom: 1.5rem;
}

/* --- [사이드바] 기본 스타일 + 접힘 방지 --- */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e0e0e0;
    padding-top: 1rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
}
div[data-testid="collapsedControl"] { display:none !important; }

/* --- [사이드바] 그라디언트 타이틀 --- */
.page-title-wrap{
  display:flex; align-items:center; gap:8px; margin:4px 0 10px 0;
}
.page-title-emoji{ font-size:20px; line-height:1; }
.page-title-main{
  font-size: clamp(18px, 2.2vw, 24px);
  font-weight: 800; letter-spacing:-0.2px; line-height:1.15;
  background: linear-gradient(90deg,#6A5ACD 0%, #A663CC 40%, #FF7A8A 75%, #FF8A3D 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
section[data-testid="stSidebar"] .page-title-wrap{justify-content:center;text-align:center;}
section[data-testid="stSidebar"] .page-title-main{display:block;text-align:center;}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] .stMarkdown p.sidebar-contact{ text-align:center !important; }

/* --- [사이드바] 네비게이션 버튼 (v2) --- */
/* [수정] 네비게이션 관련 스타일 제거 (단독 페이지이므로 불필요) */
/*
section[data-testid="stSidebar"] .block-container{padding-top:0.75rem;}
...
.sidebar-hr { margin: 0; border-top: 1px solid #E5E7EB; }
*/

/* --- [사이드바] 내부 카드/여백 제거 (SIDEBAR CARD STRIP) --- */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin-bottom: 0 !important; /* [수정] 네비게이션 버튼 간격 제거 */
}
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  transform: none !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] .block-container, 
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding-left: 0 !important;
  padding-right: 0 !important;
  box-shadow: none !important;
  border: none !important;
  background: transparent !important;
}

/* --- [컴포넌트] KPI 카드 --- */
.kpi-card {
  background: #ffffff;
  border: 1px solid #e9e9e9;
  border-radius: 10px;
  padding: 20px 15px;
  text-align: center;
  box-shadow: 0 2px 5px rgba(0,0,0,0.03);
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.kpi-title { 
    font-size: 20px; 
    font-weight: 600; 
    margin-bottom: 10px; 
    color: #444; 
}
.kpi-value { 
    font-size: 25px; 
    font-weight: 700; 
    color: #000; 
    line-height: 1.2;
}
.kpi-subwrap { margin-top: 10px; line-height: 1.4; }
.kpi-sublabel { font-size: 13px; font-weight: 500; color: #555; letter-spacing: 0.1px; margin-right: 6px; }
.kpi-substrong { font-size: 16px; font-weight: 700; color: #111; }
.kpi-subpct { font-size: 16px; font-weight: 700; }

/* --- [컴포넌트] AgGrid 공통 --- */
.ag-theme-streamlit { font-size: 13px; }
.ag-theme-streamlit .ag-root-wrapper { border-radius: 8px; }
.ag-theme-streamlit .ag-row-hover { background-color: #f5f8ff !important; }
.ag-theme-streamlit .ag-header-cell-label { justify-content: center !important; }
.ag-theme-streamlit .centered-header .ag-header-cell-label { justify-content: center !important; }
.ag-theme-streamlit .centered-header .ag-sort-indicator-container { margin-left: 4px; }
.ag-theme-streamlit .bold-header .ag-header-cell-text { 
    font-weight: 700 !important; 
    font-size: 13px; 
    color: #111;
}

/* --- [컴포넌트] 기타 미세 조정 --- */
.sec-title{ 
    font-size: 20px; 
    font-weight: 700; 
    color: #111; 
    margin: 0 0 10px 0;
    padding-bottom: 0;
    border-bottom: none;
}
div[data-testid="stMultiSelect"], div[data-testid="stSelectbox"] { margin-top: -10px; }
h3 { margin-top: -15px; margin-bottom: 10px; }
h4 { font-weight: 700; color: #111; margin-top: 0rem; margin-bottom: 0.5rem; }
hr { margin: 1.5rem 0; background-color: #e0e0e0; }


/* --- [수정] HOVER FIX OVERRIDE (v2) --- */
.stPlotlyChart:hover,
.ag-theme-streamlit .ag-root-wrapper:hover {
  transform: none !important;
  box-shadow: inherit !important;
}

/* [수정] ._liftable 클래스 의존성 제거 및 중복 규칙 통합 */
div[data-testid="stVerticalBlockBorderWrapper"] {
  transition: transform .18s ease, box-shadow .18s ease !important;
  will-change: transform, box-shadow;
  backface-visibility: hidden;
  position: relative;
  /* emulate ._liftable (원본 주석 유지) */
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.stPlotlyChart:hover):not(:has(div[data-testid="stVerticalBlockBorderWrapper"] .stPlotlyChart:hover)) { /* [수정] ._liftable 제거 */
  transform: translate3d(0,-4px,0) !important;
  box-shadow: 0 16px 40px rgba(16,24,40,.16), 0 6px 14px rgba(16,24,40,.10) !important;
  z-index: 3 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ag-theme-streamlit .ag-root-wrapper:hover):not(:has(div[data-testid="stVerticalBlockBorderWrapper"] .ag-theme-streamlit .ag-root-wrapper:hover)) { /* [수정] ._liftable 제거 */
  transform: translate3d(0,-4px,0) !important;
  box-shadow: 0 16px 40px rgba(16,24,40,.16), 0 6px 14px rgba(16,24,40,.10) !important;
  z-index: 3 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-card:hover):not(:has(div[data-testid="stVerticalBlockBorderWrapper"] .kpi-card:hover)), /* [수정] .*_liftable 제거 */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.block-card:hover):not(:has(div[data-testid="stVerticalBlockBorderWrapper"] .block-card:hover)) { /* [수정] .*_liftable 제거 */
  transform: translate3d(0,-4px,0) !important;
  box-shadow: 0 16px 40px rgba(16,24,40,.16), 0 6px 14px rgba(16,24,40,.10) !important;
  z-index: 3 !important;
}
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
  transform: none !important;
  box-shadow: inherit !important;
  z-index: auto !important;
  /* [추가] 사이드바에서는 트랜지션 효과 제거 */
  transition: none !important; 
}
/* [수정] 아래의 중복 규칙들은 위의 통합 규칙으로 병합됨 */
            
/* ===== Sidebar compact spacing (tunable) ===== */
/* [수정] 네비게이션이 없으므로, 원본의 사이드바 여백 조절 스타일은 대부분 불필요 */
/* [수정] 단, 로그인 버튼/텍스트 등 최소한의 스타일은 남김 */
[data-testid="stSidebar"]{
  --sb-gap: 6px;
  --sb-pad-y: 8px;
  --sb-pad-x: 10px;
  --label-gap: 3px;
}
[data-testid="stSidebar"] .block-container{
  padding: var(--sb-pad-y) var(--sb-pad-x) !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{
  gap: var(--sb-gap) !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
[data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6{
  margin: 2px 0 calc(var(--label-gap)+1px) !important;
}
[data-testid="stSidebar"] .stMarkdown, 
[data-testid="stSidebar"] label{
  margin: 0 0 var(--label-gap) !important;
  line-height: 1.18 !important;
}
[data-testid="stSidebar"] .stButton{ margin: 0 !important; }

/* --- [수정] 종영작 리스트 페이지 카드 스타일 (v2) --- */
div[data-testid="stVerticalBlock"] > div.ended-card-grid button {
    background-color: #ffffff !important;
    border: 1px solid #e9e9e9 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;
    
    /* [핵심] 높이 고정 (더미/내용량 무관하게 일정 유지) */
    height: 160px !important;
    min-height: 160px !important;
    width: 100% !important;
    padding: 20px 16px !important;
    
    /* 텍스트 정렬 및 줄바꿈 처리 */
    white-space: pre-wrap !important; 
    text-align: left !important;
    line-height: 1.5 !important;
    
    transition: all .2s ease !important;
    vertical-align: top !important; /* 상단 정렬 */
}

div[data-testid="stVerticalBlock"] > div.ended-card-grid button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.08) !important;
    border-color: #5c6bc0 !important;
}

/* [핵심] 버튼 내부 텍스트 기본 스타일 (지표 부분) */
div[data-testid="stVerticalBlock"] > div.ended-card-grid button p {
    font-size: 13px !important;
    color: #666 !important; /* 지표는 약간 연하게 */
    margin-bottom: 0 !important;
}

/* [핵심] 첫 번째 줄 (IP명) 스타일링 - 크고 진하게 */
div[data-testid="stVerticalBlock"] > div.ended-card-grid button p::first-line {
    font-size: 18px !important;
    font-weight: 800 !important;
    color: #111 !important; /* 제목은 진하게 */
    line-height: 2.0 !important; /* 제목과 내용 사이 간격 확보 */
}

</style>
""", unsafe_allow_html=True)
#endregion


#region [ 2.1. 기본 설정 및 공통 상수 ]
# =====================================================

# ===== [수정] 'IP 성과 자세히보기' 페이지에서만 사용하는 상수 =====
DECADES = ["10대","20대","30대","40대","50대","60대"]
DEMO_COLS_ORDER = [f"{d}남성" for d in DECADES] + [f"{d}여성" for d in DECADES]

# ===== Plotly 공통 테마 설정 =====
dashboard_theme = go.Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='sans-serif', size=12, color='#333333'),
    title=dict(font=dict(size=16, color="#111"), x=0.05),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1,
        bgcolor='rgba(0,0,0,0)'
    ),
    margin=dict(l=20, r=20, t=50, b=20),
    xaxis=dict(
        showgrid=False, 
        zeroline=True, 
        zerolinecolor='#e0e0e0', 
        zerolinewidth=1
    ),
    yaxis=dict(
        showgrid=True, 
        gridcolor='#f0f0f0',
        zeroline=True, 
        zerolinecolor='#e0e0e0'
    ),
)
pio.templates['dashboard_theme'] = go.layout.Template(layout=dashboard_theme)
pio.templates.default = 'dashboard_theme'
# =====================================================
#endregion


#region [ 2.2. 사이드바 바닥 고정 스타일 ]
# =====================================================
# 사이드바를 세로 플렉스 컨테이너로 만들고, .sb-bottom을 아래에 붙인다.
st.markdown("""
<style>
/* 사이드바 컨텐츠를 세로 플렉스 레이아웃으로 */
section[data-testid="stSidebar"] .block-container{
  display: flex !important;
  flex-direction: column !important;
  min-height: 100vh !important;
}

/* 최하단 고정 영역 */
.sb-bottom{
  margin-top: auto !important;
  padding: 10px 8px 12px 8px !important;
  background: transparent !important;
}
</style>
""", unsafe_allow_html=True)
#endregion


#region [ 2.3. 종영작 리스트 카드 스타일 오버라이드 ]
# =====================================================
st.markdown("""
<style>

/* 1. 외곽 카드 제거 → '박스 안에 박스' 문제 해결 */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ended-card-grid) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 0 !important;
}

/* 2. 종영작 카드 버튼 공통 스타일 (기존 것 덮어쓰기) */
div[data-testid="stVerticalBlock"] > div.ended-card-grid button {
    background-color: #ffffff !important;
    border: 1px solid #e9e9e9 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;
    
    /* 높이 통일 (더미/실제 카드 모두 맞추기) */
    height: 160px !important;
    min-height: 160px !important;
    width: 100% !important;
    padding: 20px 16px !important;
    
    /* 줄바꿈 + 좌측 정렬 */
    white-space: pre-wrap !important;
    text-align: left !important;
    line-height: 1.5 !important;
    
    vertical-align: top !important;
    transition: all .2s ease !important;
}

/* hover 효과 */
div[data-testid="stVerticalBlock"] > div.ended-card-grid button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.08) !important;
    border-color: #5c6bc0 !important;
}

/* 버튼 안 텍스트 기본 스타일 (두 번째 줄 이하) */
div[data-testid="stVerticalBlock"] > div.ended-card-grid button p {
    font-size: 13px !important;
    color: #666 !important;
    margin-bottom: 0 !important;
}

/* 첫 줄(IP명)만 굵게/크게 → IP명 볼드 처리 */
div[data-testid="stVerticalBlock"] > div.ended-card-grid button p::first-line {
    font-size: 18px !important;
    font-weight: 800 !important;
    color: #111 !important;
    line-height: 2.0 !important;  /* IP명과 지표 사이 간격 확보 */
}

/* 3. 더미 카드 스타일 (실제 카드와 동일 높이) */
div[data-testid="stVerticalBlock"] > div.ended-card-grid .ended-card-dummy {
    background-color: #ffffff !important;
    border: 1px solid #e9e9e9 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03) !important;

    height: 160px !important;
    min-height: 160px !important;
    width: 100% !important;
    padding: 20px 16px !important;

    display: flex;
    align-items: center;
    justify-content: center;
    color: #9ca3af;
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)
#endregion


#region [ 3. 공통 함수: 데이터 로드 / 유틸리티 ]
# =====================================================

# ===== [신규] 3.0. GSpread 클라이언트 캐싱 =====
@st.cache_resource(ttl=600)
def get_gspread_client():
    """gspread 클라이언트 객체를 인증하고 캐시합니다."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except KeyError as e:
        st.error(f"Streamlit Secrets에 'gcp_service_account' 키가 없습니다. {e}")
        return None
    except Exception as e:
        st.error(f"GSpread 클라이언트 인증 실패: {e}")
        return None

# ===== 3.1. 데이터 로드 (gspread) =====
@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    """
    [수정] Streamlit Secrets와 gspread를 사용하여 비공개 Google Sheet에서 데이터를 인증하고 로드합니다.
    st.secrets에 'SHEET_ID', 'SHEET_NAME'이 있어야 합니다.
    """
    
    client = get_gspread_client() # [수정] 캐시된 클라이언트 사용
    if client is None:
        return pd.DataFrame()
        
    try:
        # --- 2. 데이터 로드 ---
        sheet_id = st.secrets["SHEET_ID"]
        worksheet_name = st.secrets["SHEET_NAME"] 
        
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        data = worksheet.get_all_records() 
        df = pd.DataFrame(data)

    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Streamlit Secrets의 SHEET_NAME 값 ('{worksheet_name}')에 해당하는 워크시트를 찾을 수 없습니다.")
        return pd.DataFrame()
    except KeyError as e:
        st.error(f"Streamlit Secrets에 필요한 키({e})가 없습니다. TOML 설정을 확인하세요.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Google Sheets 데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

    # --- 3. 데이터 전처리 (원본 코드와 동일) ---
    # [수정] 날짜 문자열 포맷이 "2024. 1. 1" / "2024.1.1" 등으로 섞여도 안전하게 파싱
    def _parse_kor_date_series(s: pd.Series) -> pd.Series:
        ss = s.astype(str).str.strip()
        # 1) "2024. 1. 1" 형태
        out = pd.to_datetime(ss, format="%Y. %m. %d", errors="coerce")
        # 2) 공백 제거 후 "2024.1.1" 형태
        mask = out.isna()
        if mask.any():
            ss2 = ss.str.replace(" ", "", regex=False)
            out2 = pd.to_datetime(ss2, format="%Y.%m.%d", errors="coerce")
            out.loc[mask] = out2.loc[mask]
        return out

    if "주차시작일" in df.columns:
        df["주차시작일"] = _parse_kor_date_series(df["주차시작일"])

    # 원본/변형 컬럼명 모두 처리
    if "방영시작일" in df.columns:
        df["방영시작일"] = _parse_kor_date_series(df["방영시작일"])
    if "방영시작" in df.columns:
        df["방영시작"] = _parse_kor_date_series(df["방영시작"])
    if "value" in df.columns:
        v = df["value"].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False)
        df["value"] = pd.to_numeric(v, errors="coerce").fillna(0)

    for c in ["IP", "편성", "지표구분", "매체", "데모", "metric", "회차", "주차"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    if "회차" in df.columns:
        df["회차_numeric"] = df["회차"].str.extract(r"(\d+)", expand=False).astype(float)
    else:
        df["회차_numeric"] = pd.NA

    return df

# ===== [신규] 3.1b. C열 URL에서 GID 맵 가져오기 (API) =====
@st.cache_data(ttl=600)
def get_tab_gids_from_sheet(edit_url: str) -> Dict[str, int]:
    """
    [신규] C열의 /edit URL을 API로 열어 {탭이름: GID} 딕셔너리를 반환합니다.
    (주의: 서비스 계정이 이 edit_url 시트에 '뷰어'로 초대되어 있어야 합니다.)
    """
    client = get_gspread_client()
    if client is None: 
        return {}
        
    try:
        spreadsheet = client.open_by_url(edit_url)
        # 모든 탭을 순회하며 {탭이름: GID} 맵 생성
        gid_map = {ws.title.strip(): ws.id for ws in spreadsheet.worksheets()}
        return gid_map
        
    except gspread.exceptions.APIError as e:
        st.error(f"시트 접근 오류(권한 확인 필요): C열의 URL을 열 수 없습니다.\nURL: {edit_url}\nError: {e}")
        return {}
    except Exception as e:
        st.error(f"C열의 시트({edit_url}) GID 로드 중 오류: {e}")
        return {}

# ===== 3.1c. [수정] '방영중' 탭 (A,B,C,D,E열) 처리 =====
@st.cache_data(ttl=600)
def load_processed_on_air_data() -> tuple[Dict[str, List[Dict[str, str]]], Dict[str, str]]:
    """
    [수정] '방영중' 탭(A:E열)을 읽어 최종 임베딩 URL 맵과 IP 상태 맵을 생성합니다.
    - A: IP명, B: 탭명, C: Edit URL, D: Publish URL, E: 상태(방영중/종영)
    """
    worksheet_name = "방영중"
    
    client = get_gspread_client()
    if client is None:
        return {}, {}
        
    try:
        sheet_id = st.secrets["SHEET_ID"]
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # [수정] 'A2:E' 범위로 확장하여 상태값(E열)까지 가져옵니다.
        values = worksheet.get_values('A2:E') 
        
        # 1. A~E열 데이터를 IP별로 그룹화
        config_map = {}
        ip_status_map = {} # [신규] IP별 상태 저장 (순서 보장형 딕셔너리 활용)

        for row in values:
            # 기본 A~D열이 있는지 확인
            if row and len(row) >= 4 and row[0].strip():
                ip = row[0].strip()
                tab_name = row[1].strip()
                edit_url = row[2].strip()
                pub_url = row[3].strip()
                
                # [신규] E열 상태값 확인 (없으면 기본값 '방영중')
                status = row[4].strip() if len(row) > 4 and row[4].strip() else "방영중"
                
                # IP 상태 맵에 저장 (최초 1회만 저장하여 시트 순서 유지)
                if ip not in ip_status_map:
                    ip_status_map[ip] = status

                if ip not in config_map:
                    config_map[ip] = {
                        "edit_url": edit_url, 
                        "publish_url_base": pub_url.split('?')[0],
                        "tabs_to_process": [] 
                    }
                config_map[ip]["tabs_to_process"].append(tab_name)

        # 2. IP별로 GID를 찾아 최종 URL 조합
        final_data_structure = {}
        for ip, config in config_map.items():
            final_data_structure[ip] = []
            
            gid_map = get_tab_gids_from_sheet(config["edit_url"]) 
            
            if not gid_map:
                st.warning(f"'{ip}'의 GID를 C열 시트에서 가져오지 못했습니다. (권한 확인 필요)")
                continue 

            for tab_name in config["tabs_to_process"]:
                gid = gid_map.get(tab_name.strip())
                if gid is not None:
                    final_url = f"{config['publish_url_base']}?gid={gid}&single=true"
                    if "사전 반응" in tab_name:
                         final_data_structure[ip].insert(0, {"title": tab_name, "url": final_url})
                    else:
                         final_data_structure[ip].append({"title": tab_name, "url": final_url})
                else:
                    st.warning(f"'{ip}'의 시트(C열)에서 '{tab_name}'(B열) 탭을 찾을 수 없습니다.")

        return final_data_structure, ip_status_map

    except gspread.exceptions.WorksheetNotFound:
        st.sidebar.error(f"'{worksheet_name}' 탭을 찾을 수 없습니다.")
        return {}, {}
    except Exception as e:
        st.sidebar.error(f"'방영중' 탭(A:E열) 로드 오류: {e}")
        return {}, {}

# ===== 3.2. UI / 포맷팅 헬퍼 함수 =====

def fmt(v, digits=3, intlike=False):
    """
    숫자 포맷팅 헬퍼 (None이나 NaN은 '–'로 표시)
    """
    if v is None or pd.isna(v):
        return "–"
    return f"{v:,.0f}" if intlike else f"{v:.{digits}f}"

# ===== 3.2b. G-Sheet '게시용' URL 렌더러 =====
def render_published_url(published_url: str):
    """[수정] '웹에 게시'된 URL을 iframe으로 렌더링합니다. (URL 변환 X)"""
    
    st.markdown(f"""
        <iframe
            src="{published_url}"
            style="width: 1300px; height: 900px; border: 1px solid #e0e0e0; border-radius: 8px;"
        ></iframe>
        """, unsafe_allow_html=True)

# [신규] 억/만 단위 포맷팅 함수 (Dashboard_test.py 10.0.에서 이식)
def _fmt_kor_large(v):
    """N억 NNNN만 단위 포맷팅"""
    if v is None or pd.isna(v): return "–"
    val = float(v)
    if val == 0: return "0"
    
    uk = int(val // 100000000)
    man = int((val % 100000000) // 10000)
    
    if uk > 0:
        return f"{uk}억{man:04d}만"
    elif man > 0:
        return f"{man}만"
    else:
        return f"{int(val)}"
        
# [신규] 시청자수 포맷팅 함수 (Dashboard_test.py 8.에서 이식)
def fmt_live_kor(x):
    if pd.isna(x): return "0"
    val = float(x)
    if val == 0: return "0"
    man = int(val // 10000); cheon = int((val % 10000) // 1000)
    if man > 0: return f"{man}만{cheon}천" if cheon > 0 else f"{man}만"
    return f"{cheon}천" if cheon > 0 else f"{int(val)}"

# [신규] 축 눈금 포맷팅 함수 (Dashboard_test.py 8.에서 이식)
def get_axis_ticks(max_val, formatter=_fmt_kor_large): # _fmt_kor_large가 억만 포맷이므로 기본값 변경
    if pd.isna(max_val) or max_val <= 0: return None, None
    step = max_val / 4
    power = 10 ** int(np.log10(step))
    base = step / power
    if base < 1.5: step = 1 * power
    elif base < 3.5: step = 2 * power
    elif base < 7.5: step = 5 * power
    else: step = 10 * power
    vals = np.arange(0, max_val + step * 0.1, step)
    texts = [formatter(v) for v in vals]
    return vals, texts


# ===== 3.3. 페이지 라우팅 / 데이터 헬퍼 함수 =====

def _get_view_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    '조회수' metric만 필터링하고, 유튜브 PGC/UGC 규칙을 적용하는 공통 유틸.
    """
    sub = df[df["metric"] == "조회수"].copy()
    if sub.empty:
        return sub
        
    if "매체" in sub.columns and "세부속성1" in sub.columns:
        yt_mask = (sub["매체"] == "유튜브")
        attr_mask = sub["세부속성1"].isin(["PGC", "UGC"])
        sub = sub[~yt_mask | (yt_mask & attr_mask)]
    
    return sub


# ===== [신규] 미래 방영작 제외 공통 유틸 =====

# --- [신규] 지표별 컷오프 기반 베이스 슬라이싱 ---
def _base_slice_for_metric(base_raw: pd.DataFrame, f: pd.DataFrame, metric_name: str, cutoff_kind: str = "episode", media=None) -> pd.DataFrame:
    """선택 IP(f)의 '해당 지표' 데이터가 존재하는 구간까지만 base_raw를 잘라 비교 공정성을 맞춘다.
    cutoff_kind:
      - "episode": 회차_num 기준 컷
      - "week": 주차_num 기준 컷 (없으면 회차_num로 fallback)

    NOTE:
    - metric_name == "조회수" 는 원본 구조가 달라 _get_view_data()로 표준화해서 컷오프를 산출한다.
    - 슬라이싱은 전체 base_raw에 적용(해당 지표 뿐 아니라 동일 구간의 모든 row를 유지)한다.
    """
    # 지표별로 선택 IP의 최대 구간 산출
    if metric_name == "조회수":
        sub_ip = _get_view_data(f)
    else:
        sub_ip = f[f["metric"] == metric_name].copy()

    if media is not None and "매체" in sub_ip.columns:
        sub_ip = sub_ip[sub_ip["매체"].isin(media)]

    cut_ep = None
    cut_week = None

    if cutoff_kind == "week" and "주차_num" in sub_ip.columns and sub_ip["주차_num"].notna().any():
        cut_week = sub_ip["주차_num"].max()

    if "회차_num" in sub_ip.columns and sub_ip["회차_num"].notna().any():
        cut_ep = sub_ip["회차_num"].max()

    out = base_raw.copy()

    # base 슬라이싱 (우선 week, 그 다음 episode)
    if cutoff_kind == "week" and cut_week is not None and "주차_num" in out.columns:
        out = out[out["주차_num"] <= cut_week].copy()
        return out

    if cut_ep is not None and "회차_num" in out.columns:
        out = out[out["회차_num"] <= cut_ep].copy()
        return out

    return out

def _today_kst_date():
    """KST(Asia/Seoul) 기준 오늘 날짜"""
    return pd.Timestamp.now(tz="Asia/Seoul").date()

def _pick_air_start_col(df: pd.DataFrame) -> str | None:
    """데이터프레임에서 '방영시작' 계열 컬럼명을 자동 탐색"""
    for c in ["방영시작", "방영시작일", "첫방", "방송시작일", "start_date", "startDate"]:
        if c in df.columns:
            return c
    return None

def _exclude_future_ips(df: pd.DataFrame, date_col: str | None = None) -> pd.DataFrame:
    """
    IP별 방영시작(최소값)이 오늘(KST) 이후인 작품은 비교군(평균/순위)에서 제외
    - date_col이 없으면 자동 탐색
    - 날짜 파싱 실패(NaT)는 제외하지 않음(데이터가 없을 수 있으므로)
    """
    if df is None or df.empty:
        return df
    col = date_col or _pick_air_start_col(df)
    if not col or col not in df.columns:
        return df

    d = df.copy()
    # 이미 datetime이면 그대로, 아니면 문자열 파싱 시도
    if not pd.api.types.is_datetime64_any_dtype(d[col]):
        ss = d[col].astype(str).str.strip()
        dt = pd.to_datetime(ss, format="%Y. %m. %d", errors="coerce")
        mask = dt.isna()
        if mask.any():
            ss2 = ss.str.replace(" ", "", regex=False)
            dt2 = pd.to_datetime(ss2, format="%Y.%m.%d", errors="coerce")
            dt.loc[mask] = dt2.loc[mask]
        d[col] = dt

    min_by_ip = d.groupby("IP")[col].min()
    today = _today_kst_date()
    future_ips = min_by_ip[(min_by_ip.notna()) & (min_by_ip.dt.date > today)].index
    if len(future_ips) == 0:
        return df
    return d[~d["IP"].isin(future_ips)].copy()
#endregion


#region 4. 사이드바 - IP 네비게이션] 수정
# =====================================================
def render_sidebar_navigation(ip_status_map: Dict[str, str]):
    """
    [수정] '방영중'은 개별 버튼 노출, '종영'은 '모아보기' 버튼 하나로 통합 노출
    """
    
    # 1. IP 리스트 분리
    on_air_list = [ip for ip, status in ip_status_map.items() if status == "방영중"]
    ended_list = [ip for ip, status in ip_status_map.items() if status == "종영"]
    
    current_selected = st.session_state.get("selected_ip")

    # 2. 내부 렌더링 헬퍼 (방영중 IP용)
    def _render_nav_button(ip_name):
        is_active = (current_selected == ip_name)
        # 방영중 버튼 스타일 (기본)
        type_val = "primary" if is_active else "secondary"
        
        if st.sidebar.button(ip_name, key=f"navbtn__{ip_name}", use_container_width=True, type=type_val):
            st.session_state.selected_ip = ip_name
            _rerun()

    # 3. 사이드바 구성
    st.sidebar.markdown("---")
    
    # [섹션 1] 🛑 방영중 (기존대로 리스트 나열)
    st.sidebar.markdown("##### 🛑 방영중")
    if on_air_list:
        for ip in on_air_list:
            _render_nav_button(ip)
    else:
        st.sidebar.caption("방영중인 IP가 없습니다.")

    # [섹션 2] 🏁 종영 (버튼 하나로 통합)
    if ended_list:
        st.sidebar.markdown("---")
        st.sidebar.markdown("##### 🏁 종영작")
        
        # 종영작 리스트 페이지인지 확인
        is_ended_page = (current_selected == "__ENDED_LIST__")
        
        # 버튼 색상을 다르게 하기 위해 type 활용 (방영중과 반대 or 강조)
        # 여기서는 종영작 버튼을 눈에 띄게 하거나 구분감을 줌
        if st.sidebar.button(
            "🗂️ 종영작 보러가기", 
            key="btn_go_ended_list", 
            use_container_width=True, 
            type="primary" if is_ended_page else "secondary" 
        ):
            st.session_state.selected_ip = "__ENDED_LIST__"
            _rerun()

    # === 최하단: 데이터 새로고침 버튼 ===
    st.sidebar.markdown('<div class="sb-bottom">', unsafe_allow_html=True)
    st.sidebar.divider()
    if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True, key="btn_refresh_bottom"):
        try: st.cache_data.clear()
        except Exception: pass
        try: st.cache_resource.clear()
        except Exception: pass
        st.session_state["__last_refresh_ts__"] = int(time.time())
        _rerun()

    ts = st.session_state.get("__last_refresh_ts__")
    if ts:
        st.sidebar.caption(f"마지막 갱신: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))}")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
#endregion


#region [ 5. 공통 집계 유틸: KPI 계산 ]
# =====================================================
def _episode_col(df: pd.DataFrame) -> str:
    """데이터프레임에 존재하는 회차 숫자 컬럼명을 반환합니다."""
    return "회차_numeric" if "회차_numeric" in df.columns else ("회차_num" if "회차_num" in df.columns else "회차")

def mean_of_ip_episode_sum(df: pd.DataFrame, metric_name: str, media=None) -> float | None:
    sub = df[(df["metric"] == metric_name)].copy()
    if media is not None:
        sub = sub[sub["매체"].isin(media)]
    if sub.empty:
        return None
    ep_col = _episode_col(sub)
    sub = sub.dropna(subset=[ep_col]).copy()
    
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
    sub = sub.dropna(subset=["value"])

    ep_sum = sub.groupby(["IP", ep_col], as_index=False)["value"].sum()
    per_ip_mean = ep_sum.groupby("IP")["value"].mean()
    return float(per_ip_mean.mean()) if not per_ip_mean.empty else None


def mean_of_ip_episode_mean(df: pd.DataFrame, metric_name: str, media=None) -> float | None:
    sub = df[(df["metric"] == metric_name)].copy()
    if media is not None:
        sub = sub[sub["매체"].isin(media)]
    if sub.empty:
        return None
    ep_col = _episode_col(sub)
    sub = sub.dropna(subset=[ep_col]).copy()
    
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
    sub = sub.dropna(subset=["value"])

    ep_mean = sub.groupby(["IP", ep_col], as_index=False)["value"].mean()
    per_ip_mean = ep_mean.groupby("IP")["value"].mean()
    return float(per_ip_mean.mean()) if not per_ip_mean.empty else None


def mean_of_ip_sums(df: pd.DataFrame, metric_name: str, media=None) -> float | None:
    
    if metric_name == "조회수":
        sub = _get_view_data(df) # [3. 공통 함수]
    else:
        sub = df[df["metric"] == metric_name].copy()

    if media is not None:
        sub = sub[sub["매체"].isin(media)]
    
    if sub.empty:
        return None
        
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
    sub = sub.dropna(subset=["value"])

    per_ip_sum = sub.groupby("IP")["value"].sum()
    return float(per_ip_sum.mean()) if not per_ip_sum.empty else None
#endregion


#region [ 6. 공통 집계 유틸: 데모  ]
# =====================================================
# ===== 6.1. 데모 문자열 파싱 유틸 =====
def _gender_from_demo(s: str):
    """'데모' 문자열에서 성별(남/여/기타)을 추출합니다."""
    s = str(s)
    if any(k in s for k in ["여", "F", "female", "Female"]): return "여"
    if any(k in s for k in ["남", "M", "male", "Male"]): return "남"
    return "기타"

def _to_decade_label(x: str):
    """'데모' 문자열에서 연령대(10대, 20대...)를 추출합니다."""
    m = re.search(r"\d+", str(x))
    if not m: return "기타"
    n = int(m.group(0))
    return f"{(n//10)*10}대"

def _decade_label_clamped(x: str):
    """ 10대~60대 범위로 연령대 라벨 생성, 그 외는 None (페이지 2, 3용) """
    m = re.search(r"\d+", str(x))
    if not m: return None
    n = int(m.group(0))
    n = max(10, min(60, (n // 10) * 10))
    return f"{n}대"

def _decade_key(s: str):
    """연령대 정렬을 위한 숫자 키를 추출합니다."""
    m = re.search(r"\d+", str(s))
    return int(m.group(0)) if m else 999

def _fmt_ep(n):
    """ 회차 번호를 '01화' 형태로 포맷팅 (페이지 2, 3용) """
    try:
        return f"{int(n):02d}화"
    except Exception:
        return str(n)

# ===== 6.2. 피라미드 차트 렌더링 (페이지 1, 2) [신버전 로직 사용] =====
# [수정] 피라미드 차트 로직을 Dashboard_test.py의 _render_pyramid_local 로직으로 대체
def _render_pyramid_local(container, title: str, df_src: pd.DataFrame, height: int = 260):

    if df_src.empty:
        container.info("표시할 데이터가 없습니다.")
        return

    COLOR_MALE_NEW = "#5B85D9"; COLOR_FEMALE_NEW = "#E66C6C"

    df_demo = df_src.copy()
    df_demo["성별"] = df_demo["데모"].apply(_gender_from_demo)
    df_demo["연령대_대"] = df_demo["데모"].apply(_to_decade_label)
    df_demo = df_demo[df_demo["성별"].isin(["남","여"]) & df_demo["연령대_대"].notna()]

    if df_demo.empty: container.info("표시할 데모 데이터가 없습니다."); return

    order = ["60대", "50대", "40대", "30대", "20대", "10대"] # 신버전 순서

    pvt = df_demo.groupby(["연령대_대","성별"])["value"].sum().unstack("성별").reindex(order).fillna(0)
    male = -pvt.get("남", pd.Series(0, index=pvt.index))
    female = pvt.get("여", pd.Series(0, index=pvt.index))

    total_pop = male.abs().sum() + female.sum()
    if total_pop == 0: total_pop = 1
    
    male_share = (male.abs() / total_pop * 100) # 성별 내 비중이 아닌, 전체 인구 비중 사용
    female_share = (female / total_pop * 100)
    max_abs = float(max(male.abs().max(), female.max()) or 1)

    male_text = [f"{v:.1f}%" if v > 0 else "" for v in male_share]
    female_text = [f"{v:.1f}%" if v > 0 else "" for v in female_share]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=pvt.index, x=male, name="남", orientation="h", marker_color=COLOR_MALE_NEW,
        text=male_text, textposition="inside", insidetextanchor="end",
        textfont=dict(color="#ffffff", size=11),
        hovertemplate="연령대=%{y}<br>남성=%{customdata[0]:,.0f}명<br>전체비중=%{customdata[1]:.1f}%<extra></extra>",
        customdata=np.column_stack([male.abs(), male_share])
    ))
    fig.add_trace(go.Bar(
        y=pvt.index, x=female, name="여", orientation="h", marker_color=COLOR_FEMALE_NEW,
        text=female_text, textposition="inside", insidetextanchor="start",
        textfont=dict(color="#ffffff", size=11),
        hovertemplate="연령대=%{y}<br>여성=%{customdata[0]:,.0f}명<br>전체비중=%{customdata[1]:.1f}%<extra></extra>",
        customdata=np.column_stack([female, female_share])
    ))

    fig.update_layout(
        barmode="overlay", height=height, margin=dict(l=8, r=8, t=48, b=8),
        legend_title=None, bargap=0.15,
        title=dict(text=title, x=0.0, y=0.98, font=dict(size=14))
    )
    fig.update_yaxes(categoryorder="array", categoryarray=order, fixedrange=True)
    fig.update_xaxes(range=[-max_abs*1.1, max_abs*1.1], showticklabels=False, showgrid=False, zeroline=True, fixedrange=True)
    container.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
#endregion


#region [ 7. 페이지 2: IP 성과 자세히보기 ]
# =====================================================

def _normalize_metric(s: str) -> str:
    if s is None: return ""
    s2 = re.sub(r"[^A-Za-z0-9가-힣]+", "", str(s)).lower()
    return s2

# [신규] Metric Filter (Dashboard_test.py 8.에서 이식)
def _metric_filter(df: pd.DataFrame, name: str) -> pd.DataFrame:
    target = _normalize_metric(name)
    if "metric_norm" not in df.columns:
        df = df.copy()
        df["metric_norm"] = df["metric"].apply(_normalize_metric)
    return df[df["metric_norm"] == target]

# [신규] Metric Series Aggregation (Dashboard_test.py 8.에서 이식)
def _series_ip_metric(base_df: pd.DataFrame, metric_name: str, mode: str = "mean", media: List[str] | None = None):
    
    if metric_name == "조회수": sub = _get_view_data(base_df)
    else: sub = _metric_filter(base_df, metric_name).copy()
    
    if media is not None: sub = sub[sub["매체"].isin(media)]
    if sub.empty: return pd.Series(dtype=float)
    
    # [수정] 넷플릭스 순위 등 회차 정보가 없을 수 있는 지표 예외 처리
    ep_col = _episode_col(sub)
    
    if metric_name == "N_W순위":
         # 회차 상관없이 값만 있으면 됨
         sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
         sub = sub.dropna(subset=["value"])
         if sub.empty: return pd.Series(dtype=float)
         
         if mode == "min": return sub.groupby("IP")["value"].min()
         elif mode == "mean": return sub.groupby("IP")["value"].mean()
         return sub.groupby("IP")["value"].min()
    else:
        sub = sub.dropna(subset=[ep_col])
        sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
        sub = sub.dropna(subset=["value"])
        if sub.empty: return pd.Series(dtype=float)
        
        if mode == "mean":
            ep_mean = sub.groupby(["IP", ep_col], as_index=False)["value"].mean()
            s = ep_mean.groupby("IP")["value"].mean()
        elif mode == "sum": s = sub.groupby("IP")["value"].sum()
        elif mode == "ep_sum_mean":
            ep_sum = sub.groupby(["IP", ep_col], as_index=False)["value"].sum()
            s = ep_sum.groupby("IP")["value"].mean()
        elif mode == "min": s = sub.groupby("IP")["value"].min()
        else: s = sub.groupby("IP")["value"].mean()
        return pd.to_numeric(s, errors="coerce").dropna()

# [신규] Min Metric (Dashboard_test.py 8.에서 이식)
def _min_of_ip_metric(df_src: pd.DataFrame, metric_name: str) -> float | None:
    sub = _metric_filter(df_src, metric_name).copy()
    if sub.empty: return None
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan) # 0 제외
    s = pd.to_numeric(sub["value"], errors="coerce").dropna()
    return float(s.min()) if not s.empty else None

# [신규] Mean Like Rating (Dashboard_test.py 8.에서 이식)
def _mean_like_rating(df_src: pd.DataFrame, metric_name: str) -> float | None:
    sub = _metric_filter(df_src, metric_name).copy()
    if sub.empty: return None
    sub["val"] = pd.to_numeric(sub["value"], errors="coerce")
    sub = sub.dropna(subset=["val"])
    if sub.empty: return None
    if "회차_num" in sub.columns and sub["회차_num"].notna().any():
        g = sub.dropna(subset=["회차_num"]).groupby("회차_num", as_index=False)["val"].mean()
        return float(g["val"].mean())
    if "방영시작일" in sub.columns and sub["방영시작일"].notna().any():
        g = sub.dropna(subset=["방영시작일"]).groupby("방영시작일", as_index=False)["val"].mean()
        return float(g["val"].mean())
    return float(sub["val"].mean())

# [신규] Ranking (Dashboard_test.py 8.에서 이식)
def _rank_within_program(base_df, metric_name, ip_name, value, mode="mean", media=None, low_is_good=False):
    s = _series_ip_metric(base_df, metric_name, mode=mode, media=media)
    if s.empty or value is None or pd.isna(value): return (None, 0)
    s = s.dropna()
    if ip_name not in s.index: return (None, int(s.shape[0]))
    ranks = s.rank(method="min", ascending=low_is_good)
    return (int(ranks.loc[ip_name]), int(s.shape[0]))

# [신규] PCT Color (Dashboard_test.py 8.에서 이식)
def _pct_color(val, base_val):
    if val is None or pd.isna(val) or base_val in (None, 0) or pd.isna(base_val): return "#888"
    pct = (val / base_val) * 100
    return "#d93636" if pct > 100 else ("#2a61cc" if pct < 100 else "#444")

# [신규] KPI Sublines (Dashboard_test.py 8.에서 이식)
def sublines_html(prog_label: str, rank_tuple: tuple, val, base_val, cutoff_label: str | None = None):
    rnk, total = rank_tuple if rank_tuple else (None, 0)

    if rnk is not None and total > 0:
        prefix = "👑 " if rnk == 1 else ""
        cutoff_txt = f"/{cutoff_label}" if cutoff_label else ""
        rank_label = (
            f"{prefix}{rnk}위"
            f"<span style='font-size:13px;font-weight:400;color:#9ca3af;margin-left:2px'>(총{total}개{cutoff_txt})</span>"
        )
    else:
        rank_label = "–위"

    pct_txt = "–"; col = "#888"
    try:
        if (val is not None) and (base_val not in (None, 0)) and (not (pd.isna(val) or pd.isna(base_val))):
            pct = (float(val) / float(base_val)) * 100.0
            pct_txt = f"{pct:.0f}%"; col = _pct_color(val, base_val)
    except Exception:
        pass

    return (
        "<div class='kpi-subwrap'>"
        "<span class='kpi-sublabel'>그룹 內</span> "
        f"<span class='kpi-substrong'>{rank_label}</span><br/>"
        "<span class='kpi-sublabel'>그룹 평균比</span> "
        f"<span class='kpi-subpct' style='color:{col};'>{pct_txt}</span>"
        "</div>"
    )

# [신규] cutoff label helper
def _cutoff_label_for_metric(f: pd.DataFrame, metric_name: str, cutoff_kind: str = "episode", media: List[str] | None = None) -> str | None:
    """선택 IP(f) 기준으로 컷오프 라벨 생성
    - week   : ~W+N
    - episode: ~N화
    """
    if f is None or f.empty:
        return None

    # metric 표준화
    if metric_name == "조회수":
        sub = _get_view_data(f)
    else:
        sub = f[f["metric"] == metric_name].copy()

    if media is not None and "매체" in sub.columns:
        sub = sub[sub["매체"].isin(media)]

    if sub.empty:
        return None

    if cutoff_kind == "week":
        if "주차_num" in sub.columns and sub["주차_num"].notna().any():
            cut_week = sub["주차_num"].max()
            if pd.notna(cut_week):
                return f"~W{int(cut_week)}"

        # week이 없으면 episode로 fallback
        if "회차_num" in sub.columns and sub["회차_num"].notna().any():
            cut_ep = sub["회차_num"].max()
            if pd.notna(cut_ep):
                return f"~{int(cut_ep)}화"
        return None

    # episode
    if "회차_num" in sub.columns and sub["회차_num"].notna().any():
        cut_ep = sub["회차_num"].max()
        if pd.notna(cut_ep):
            return f"~{int(cut_ep)}화"

    return None

# [신규] KPI Dummy (Dashboard_test.py 8.에서 이식)
def sublines_dummy():
    return (
     "<div class='kpi-subwrap' style='visibility:hidden;'>"
     "<span class='kpi-sublabel'>_</span> <span class='kpi-substrong'>_</span><br/>"
     "<span class='kpi-sublabel'>_</span> <span class='kpi-subpct'>_</span>"
      "</div>"
    )

# [신규] KPI Render (Dashboard_test.py 8.에서 이식)
def kpi_with_rank(col, title, value, base_val, rank_tuple, prog_label, intlike=False, digits=3, value_suffix="", cutoff_label: str | None = None):
    with col:
        main_val = fmt(value, digits=digits, intlike=intlike)
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-title'>{title}</div>"
            f"<div class='kpi-value'>{main_val}{value_suffix}</div>"
            f"{sublines_html(prog_label, rank_tuple, value, base_val, cutoff_label=cutoff_label)}</div>",
            unsafe_allow_html=True
        )

# [신규] KPI Dummy Card (Dashboard_test.py 8.에서 이식)
def kpi_dummy(col):
    with col:
        st.markdown(
            f"<div class='kpi-card' style='opacity:0; pointer-events:none;'><div class='kpi-title'>-</div>"
            f"<div class='kpi-value'>-</div>{sublines_dummy()}</div>",
            unsafe_allow_html=True
        )


def render_ip_detail(ip_selected: str, on_air_data: Dict[str, List[Dict[str, str]]], target_tab: str = None):
    """
    [수정] target_tab이 있으면 해당 탭을 리스트 맨 앞으로 이동시켜 기본 선택되게 함
    [수정] 편성 기준 필터에 '평일' 추가 및 '수목' 편성작의 경우 디폴트를 '평일'로 설정
    """

    # ===== 1. 고정 페이지 타이틀 (항상 표시) =====
    st.markdown(f"<div class='page-title'>📣 {ip_selected} 시청자 반응 브리핑</div>", unsafe_allow_html=True)

    # ===== 2. 탭 구성 데이터 준비 =====
    # 2a. 탭 정의 (Main 대시보드는 type='main', G-Sheet는 type='sheet')
    # 기본 탭 구성
    all_tab_configs = [{"title": "📈 성과 자세히보기", "type": "main", "url": None}]
    
    # G-Sheet 탭 추가
    embeddable_tabs = on_air_data.get(ip_selected, [])
    for tab in embeddable_tabs:
        all_tab_configs.append({"title": tab["title"], "type": "sheet", "url": tab["url"]})

    # 2b. [핵심] 링크된 탭이 있다면 순서 재배치 (맨 앞으로 이동)
    if target_tab:
        # 제목이 정확히 일치하는 탭 찾기
        target_index = next((i for i, t in enumerate(all_tab_configs) if t["title"] == target_tab), -1)
        if target_index > 0: # 0번(메인)이 아니면 순서 변경
            target_item = all_tab_configs.pop(target_index)
            all_tab_configs.insert(0, target_item)
            st.toast(f"🔗 '{target_tab}' 탭으로 이동했습니다.")

    # 2c. 탭 생성 (순서가 바뀐 리스트로 생성)
    created_tabs = st.tabs([t["title"] for t in all_tab_configs])
    
    # 2d. 위젯 매핑 (Main 대시보드가 어느 탭 객체에 들어갈지 찾기)
    main_tab_widget = None
    sheet_widgets = [] # (tab_widget, url) 튜플 리스트

    for i, config in enumerate(all_tab_configs):
        if config["type"] == "main":
            main_tab_widget = created_tabs[i]
        else:
            sheet_widgets.append((created_tabs[i], config["url"]))

    # ===== 탭 1: 기존 성과 자세히보기 (변수명 main_tab -> main_tab_widget 사용) =====
    if main_tab_widget:
        with main_tab_widget:
            
            df_full = load_data() 

            # [수정] 필터 UI를 신버전 로직으로 교체
            # [수정] filter_cols를 [1, 1] 비율로 조정하여 필터 2개만 배치
            filter_cols = st.columns([1, 1])

            # --- 데이터 전처리 (Default 설정을 위해 위치 이동) ---
            # [수정] 방영 연도 필터 기준을 '편성연도' 컬럼으로 변경 (날짜 파싱 X)
            date_col_for_filter = "편성연도"

            target_ip_rows = df_full[df_full["IP"] == ip_selected]
            
            # Default 연도/편성 추출
            default_year_list = []
            sel_prog = None
            
            if not target_ip_rows.empty:
                try:
                    # [수정] 날짜 파싱(.dt.year) 없이 값 그대로 모드 추출
                    if date_col_for_filter in target_ip_rows.columns:
                        y_mode = target_ip_rows[date_col_for_filter].dropna().mode()
                        if not y_mode.empty:
                            default_year_list = [y_mode.iloc[0]]
                    
                    sel_prog = target_ip_rows["편성"].dropna().mode().iloc[0]
                except Exception:
                    pass
                    
            all_years = []
            # [수정] '편성연도' 컬럼의 고유값을 그대로 사용
            if date_col_for_filter in df_full.columns:
                unique_vals = df_full[date_col_for_filter].dropna().unique()
                try:
                    all_years = sorted(unique_vals, reverse=True)
                except:
                    # 정렬 실패(타입 혼재 등) 시 문자열 변환 후 정렬
                    all_years = sorted([str(x) for x in unique_vals], reverse=True)

            # [수정] [Col 1] 방영 연도
            with filter_cols[0]:
                selected_years = st.multiselect(
                    "방영 연도",
                    all_years,
                    default=default_year_list,
                    placeholder="방영 연도 선택",
                    label_visibility="collapsed"
                )

            # [수정] [Col 2] 편성 기준 필터 (평일 추가 및 디폴트 로직 적용)
            with filter_cols[1]:
                # 1. 옵션 리스트 정의 ("평일" 추가)
                filter_options = ["동일 편성", "평일", "월화", "토일", "전체"]
                
                # 2. 디폴트 인덱스 설정 로직
                # 기본값은 0 ("동일 편성")
                default_idx = 0
                
                # 만약 해당 IP의 편성이 "수목"이라면, 디폴트를 "평일"로 설정
                if sel_prog == "수목":
                    # "평일"이 options 리스트의 몇 번째인지 확인 (여기서는 1번 인덱스)
                    try:
                        default_idx = filter_options.index("평일")
                    except ValueError:
                        default_idx = 0
                
                comp_type = st.selectbox(
                    "편성 기준",
                    filter_options, 
                    index=default_idx,
                    label_visibility="collapsed"
                )

            # [신규] 지표 기준 안내를 필터 행 아래 별도 행에 배치
            with st.expander("ℹ️ 지표 기준 안내", expanded=False):
                st.markdown("<div class='gd-guideline'>", unsafe_allow_html=True)
                st.markdown(textwrap.dedent("""
                    **지표 기준**
                - **시청률** `누적 회차평균`: 전국 기준 가구 & 타깃(2049) 시청률
                - **티빙 LIVE UV** `누적 회차평균`: 실시간 시청 UV
                - **티빙 당일 VOD UV** `누적 회차평균`: 본방송 당일 VOD UV
                - **티빙 주간 VOD UV** `누적 회차평균`: [회차 방영일부터 +6일까지의 7일간 VOD UV] - [티빙 당일 VOD] `*주간 VOD수치는 방영 7일 후 업데이트 됩니다.`
                - **디지털 조회** `누적 회차총합`: 방영주간 월~일 발생 총합 / 유튜브,인스타그램,틱톡,네이버TV,페이스북
                - **디지털 언급량** `누적 회차총합`: 방영주차(월~일) 내 총합 / 커뮤니티,트위터,블로그                            
                - **화제성 점수** `누적 회차평균`: 방영기간 주차별 화제성 점수의 평균 (펀덱스)
                - **넷플릭스 순위** `최고 순위`: 방영 기간 중 기록한 주간 최고 순위 (N_W순위 기준, 0 제외)
                """).strip())
                st.markdown("</div>", unsafe_allow_html=True)


            # --- 선택 IP 데이터 필터링 ---
            f = target_ip_rows.copy()

            if "회차_numeric" in f.columns:
                f["회차_num"] = pd.to_numeric(f["회차_numeric"], errors="coerce")
            else:
                f["회차_num"] = pd.to_numeric(f["회차"].str.extract(r"(\d+)", expand=False), errors="coerce")
            
            my_max_ep = f["회차_num"].max()

            def _week_to_num(x: str):
                m = re.search(r"-?\d+", str(x))
                return int(m.group(0)) if m else None

            has_week_col = "주차" in f.columns
            if has_week_col:
                f["주차_num"] = f["주차"].apply(_week_to_num)

            # --- 베이스(비교 그룹) 데이터 필터링 ---
            base_raw = df_full.copy()
            group_name_parts = []

            # 1. 편성 필터 (확장된 로직 적용)
            if comp_type == "동일 편성":
                if sel_prog:
                    base_raw = base_raw[base_raw["편성"] == sel_prog]
                    group_name_parts.append(f"'{sel_prog}'")
                else:
                    st.warning(f"'{ip_selected}'의 편성 정보가 없어 '동일 편성' 기준은 제외됩니다.", icon="⚠️")
            
            elif comp_type == "평일":
                # [수정] 평일: 월화 + 수목 포함
                base_raw = base_raw[base_raw["편성"].isin(["월화", "수목"])]
                group_name_parts.append("'평일(월화/수목)'")

            elif comp_type == "월화":
                base_raw = base_raw[base_raw["편성"] == "월화"]
                group_name_parts.append("'월화'")
            
            elif comp_type == "토일":
                base_raw = base_raw[base_raw["편성"] == "토일"]
                group_name_parts.append("'토일'")
            # "전체"인 경우 별도 필터 없음

            # 2. 방영 연도 필터
            if selected_years:
                # [수정] 날짜 파싱(.dt.year) 없이 컬럼 값 그대로 비교
                base_raw = base_raw[base_raw[date_col_for_filter].isin(selected_years)]
                
                if len(selected_years) <= 3:
                    years_str = ",".join(map(str, sorted(selected_years)))
                    # [수정] 데이터 값 자체("24년")를 사용하므로 "년" 접미사 제거
                    group_name_parts.append(f"{years_str}")
                else:
                    try:
                        group_name_parts.append(f"{min(selected_years)}~{max(selected_years)}")
                    except:
                        group_name_parts.append("선택연도")
            else:
                st.warning("선택된 연도가 없습니다. (전체 연도 데이터와 비교)", icon="⚠️")

            if not group_name_parts:
                group_name_parts.append("전체")
            
            prog_label = " & ".join(group_name_parts) + " 평균"

            # [신규] 미래 방영작은 비교군(평균/순위/총N개)에서 제외
            base_raw = _exclude_future_ips(base_raw)

            # --- (이하 로직 동일) ---
            if "회차_numeric" in base_raw.columns:
                base_raw["회차_num"] = pd.to_numeric(base_raw["회차_numeric"], errors="coerce")
            else:
                base_raw["회차_num"] = pd.to_numeric(base_raw["회차"].str.extract(r"(\d+)", expand=False), errors="coerce")
            
            if pd.notna(my_max_ep):
                base = base_raw[base_raw["회차_num"] <= my_max_ep].copy()
            else:
                base = base_raw.copy()

            st.markdown(
                f"<div class='sub-title'>📺 {ip_selected} 성과 상세 리포트</div>",
                unsafe_allow_html=True
            )
            st.markdown("---")


            # --- KPI Calculation ---

            val_T = mean_of_ip_episode_mean(f, "T시청률")
            val_H = mean_of_ip_episode_mean(f, "H시청률")
            # [수정] TVING VOD = LIVE + QUICK + VOD 합산
            val_live = mean_of_ip_episode_sum(f, "시청인구", ["TVING LIVE"])
            val_quick = mean_of_ip_episode_sum(f, "시청인구", ["TVING QUICK"]) 
            val_vod = mean_of_ip_episode_sum(f, "시청인구", ["TVING VOD"])
            
            # [신규] Wavve VOD (metric="시청자수", media="웨이브")
            val_wavve = mean_of_ip_episode_sum(f, "시청자수", ["웨이브"])
            
            # [신규] Netflix Best Rank
            val_netflix_best = _min_of_ip_metric(f, "N_W순위")

            val_buzz = mean_of_ip_sums(f, "언급량")
            val_view = mean_of_ip_sums(f, "조회수")
            val_topic_min = _min_of_ip_metric(f, "F_Total")
            val_topic_avg = _mean_like_rating(f, "F_score")

            base_T = mean_of_ip_episode_mean(_base_slice_for_metric(base_raw, f, "T시청률", "episode"), "T시청률")
            base_H = mean_of_ip_episode_mean(_base_slice_for_metric(base_raw, f, "H시청률", "episode"), "H시청률")
            base_live = mean_of_ip_episode_sum(_base_slice_for_metric(base_raw, f, "시청인구", "episode"), "시청인구", ["TVING LIVE"])
            base_quick = mean_of_ip_episode_sum(_base_slice_for_metric(base_raw, f, "시청인구", "episode"), "시청인구", ["TVING QUICK"])
            base_vod = mean_of_ip_episode_sum(_base_slice_for_metric(base_raw, f, "시청인구", "episode"), "시청인구", ["TVING VOD"])
            
            # [신규] Wavve VOD Base
            base_wavve = mean_of_ip_episode_sum(_base_slice_for_metric(base_raw, f, "시청자수", "episode"), "시청자수", ["웨이브"])
            
            # [신규] Netflix Base
            base_netflix_series = _series_ip_metric(_base_slice_for_metric(base_raw, f, "N_W순위", "week"), "N_W순위", mode="min")
            base_netflix_best = float(base_netflix_series.mean()) if not base_netflix_series.empty else None

            base_buzz = mean_of_ip_sums(_base_slice_for_metric(base_raw, f, "언급량", "week"), "언급량")
            base_view = mean_of_ip_sums(_base_slice_for_metric(base_raw, f, "조회수", "week"), "조회수")
            base_topic_min_series = _series_ip_metric(_base_slice_for_metric(base_raw, f, "F_Total", "week"), "F_Total", mode="min")
            base_topic_min = float(base_topic_min_series.mean()) if not base_topic_min_series.empty else None
            base_topic_avg = _mean_like_rating(_base_slice_for_metric(base_raw, f, "F_score", "week"), "F_score")

            # --- Ranking ---
            # [수정] TVING VOD, QUICK 로직을 신버전의 EP_SUM_MEAN 로직으로 변경
            rk_T     = _rank_within_program(_base_slice_for_metric(base_raw, f, "T시청률", "episode"), "T시청률", ip_selected, val_T,   mode="mean",        media=None)
            rk_H     = _rank_within_program(_base_slice_for_metric(base_raw, f, "H시청률", "episode"), "H시청률", ip_selected, val_H,   mode="mean",        media=None)
            rk_live  = _rank_within_program(_base_slice_for_metric(base_raw, f, "시청인구", "episode"), "시청인구", ip_selected, val_live,  mode="ep_sum_mean", media=["TVING LIVE"])
            rk_quick = _rank_within_program(_base_slice_for_metric(base_raw, f, "시청인구", "episode"), "시청인구", ip_selected, val_quick, mode="ep_sum_mean", media=["TVING QUICK"])
            rk_vod   = _rank_within_program(_base_slice_for_metric(base_raw, f, "시청인구", "episode"), "시청인구", ip_selected, val_vod,   mode="ep_sum_mean", media=["TVING VOD"])
            
            # [신규] Wavve Rank
            rk_wavve = _rank_within_program(_base_slice_for_metric(base_raw, f, "시청자수", "episode"), "시청자수", ip_selected, val_wavve, mode="ep_sum_mean", media=["웨이브"])
            
            # [신규] Netflix Rank
            rk_netflix = _rank_within_program(_base_slice_for_metric(base_raw, f, "N_W순위", "week"), "N_W순위", ip_selected, val_netflix_best, mode="min", media=None, low_is_good=True)

            rk_buzz  = _rank_within_program(_base_slice_for_metric(base_raw, f, "언급량", "week"), "언급량",   ip_selected, val_buzz,  mode="sum",        media=None)
            rk_view  = _rank_within_program(_base_slice_for_metric(base_raw, f, "조회수", "week"), "조회수",   ip_selected, val_view,  mode="sum",        media=None)
            rk_fmin  = _rank_within_program(_base_slice_for_metric(base_raw, f, "F_Total", "week"), "F_Total",  ip_selected, val_topic_min, mode="min",   media=None, low_is_good=True)
            rk_fscr  = _rank_within_program(_base_slice_for_metric(base_raw, f, "F_score", "week"), "F_score",  ip_selected, val_topic_avg, mode="mean",  media=None, low_is_good=False)


                        # === KPI 배치 (Row 1) ===
            # 컷오프 라벨(선택 IP 기준)
            cut_T     = _cutoff_label_for_metric(f, "T시청률", "episode")
            cut_H     = _cutoff_label_for_metric(f, "H시청률", "episode")
            cut_live  = _cutoff_label_for_metric(f, "시청인구", "episode", media=["TVING LIVE"])
            cut_quick = _cutoff_label_for_metric(f, "시청인구", "episode", media=["TVING QUICK"])
            cut_vod   = _cutoff_label_for_metric(f, "시청인구", "episode", media=["TVING VOD"])

            c1, c2, c3, c4, c5 = st.columns(5)
            kpi_with_rank(c1, "🎯 타깃시청률",        val_T,     base_T,     rk_T,     prog_label, digits=3,  cutoff_label=cut_T)
            kpi_with_rank(c2, "🏠 가구시청률",        val_H,     base_H,     rk_H,     prog_label, digits=3,  cutoff_label=cut_H)
            kpi_with_rank(c3, "📺 티빙 LIVE UV",     val_live,  base_live,  rk_live,  prog_label, intlike=True, cutoff_label=cut_live)
            kpi_with_rank(c4, "⚡ 티빙 당일 VOD UV",  val_quick, base_quick, rk_quick, prog_label, intlike=True, cutoff_label=cut_quick)
            kpi_with_rank(c5, "▶️ 티빙 주간 VOD UV",  val_vod,   base_vod,   rk_vod,   prog_label, intlike=True, cutoff_label=cut_vod)

            # === KPI 배치 (Row 2) ===
            cut_view  = _cutoff_label_for_metric(f, "조회수",  "week")
            cut_buzz  = _cutoff_label_for_metric(f, "언급량",  "week")
            cut_fscr  = _cutoff_label_for_metric(f, "F_score", "week")
            cut_wavve = _cutoff_label_for_metric(f, "시청자수", "episode", media=["웨이브"])

            c6, c7, c8, c9, c10 = st.columns(5)
            kpi_with_rank(c6, "👀 디지털 조회수", val_view, base_view, rk_view, prog_label, intlike=True, cutoff_label=cut_view)
            kpi_with_rank(c7, "💬 디지털 언급량", val_buzz, base_buzz, rk_buzz, prog_label, intlike=True, cutoff_label=cut_buzz)

            with c8:
                v = val_topic_min
                main_val = "–" if (v is None or pd.isna(v)) else f"{int(round(v)):,d}위"
                st.markdown(
                    f"<div class='kpi-card'><div class='kpi-title'>🏆 최고 화제성 순위</div>"
                    f"<div class='kpi-value'>{main_val}</div>{sublines_dummy()}</div>",
                    unsafe_allow_html=True
                )

            kpi_with_rank(c9, "🔥 화제성 점수", val_topic_avg, base_topic_avg, rk_fscr, prog_label, intlike=True, cutoff_label=cut_fscr)

            # [수정] 마지막 5번째 슬롯: Wavve 우선 -> Netflix -> 없으면 빈칸 (미방영 텍스트 X)
            with c10:
                if val_wavve is not None and not pd.isna(val_wavve):
                    kpi_with_rank(c10, "🌊 웨이브 VOD UV", val_wavve, base_wavve, rk_wavve, prog_label, intlike=True, cutoff_label=cut_wavve)

                elif val_netflix_best is not None and not pd.isna(val_netflix_best) and val_netflix_best > 0:
                    main_val = f"{int(val_netflix_best)}위"
                    st.markdown(
                        f"<div class='kpi-card'><div class='kpi-title'>🍿 넷플릭스 주간 최고순위</div>"
                        f"<div class='kpi-value'>{main_val}</div>{sublines_dummy()}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    kpi_dummy(c10)

            st.divider()

            # --- Charts ---
            chart_h = 320
            common_cfg = {"scrollZoom": False, "staticPlot": False, "displayModeBar": False}

            # === [Row1] 시청률 | [수정] OTT (TVING + Wavve Hidden) ===
            cA, cB = st.columns(2)
            with cA:
                st.markdown("<div class='sec-title'>📈 시청률</div>", unsafe_allow_html=True)
                rsub = f[f["metric"].isin(["T시청률", "H시청률"])].dropna(subset=["회차", "회차_num"]).copy()
                rsub = rsub.sort_values("회차_num")
                if not rsub.empty:
                    ep_order = rsub[["회차", "회차_num"]].drop_duplicates().sort_values("회차_num")["회차"].tolist()
                    t_series = rsub[rsub["metric"] == "T시청률"].groupby("회차", as_index=False)["value"].mean()
                    h_series = rsub[rsub["metric"] == "H시청률"].groupby("회차", as_index=False)["value"].mean()
                    ymax = pd.concat([t_series["value"], h_series["value"]]).max()
                    y_upper = float(ymax) * 1.4 if pd.notna(ymax) else None

                    fig_rate = go.Figure()
                    # [수정] 신버전 라인 스타일 적용
                    fig_rate.add_trace(go.Scatter(
                        x=h_series["회차"], y=h_series["value"], mode="lines+markers+text", name="가구시청률",
                        line=dict(color='#90a4ae', width=2), text=[f"{v:.2f}" for v in h_series["value"]], textposition="top center"
                    ))
                    fig_rate.add_trace(go.Scatter(
                        x=t_series["회차"], y=t_series["value"], mode="lines+markers+text", name="타깃시청률",
                        line=dict(color='#3949ab', width=3), text=[f"{v:.2f}" for v in t_series["value"]], textposition="top center"
                    ))
                    fig_rate.update_xaxes(categoryorder="array", categoryarray=ep_order, title=None, fixedrange=True)
                    fig_rate.update_yaxes(title=None, fixedrange=True, range=[0, y_upper] if (y_upper and y_upper > 0) else None)
                    # [수정] 범례 위치 변경 (신버전)
                    fig_rate.update_layout(legend_title=None, height=chart_h, margin=dict(l=8, r=8, t=10, b=8), legend=dict(orientation='h', yanchor='bottom', y=1.02))
                    st.plotly_chart(fig_rate, use_container_width=True, config=common_cfg)
                else:
                    st.info("표시할 시청률 데이터가 없습니다.")

            # [수정] OTT 차트: TVING + Wavve(Hidden) 통합
            with cB:
                # 1. 데이터 준비
                # (1) TVING 데이터
                t_keep = ["TVING LIVE", "TVING QUICK", "TVING VOD"]
                tsub = f[(f["metric"] == "시청인구") & (f["매체"].isin(t_keep))].dropna(subset=["회차", "회차_num"]).copy()
                
                # (2) Wavve 데이터 확인
                wsub = f[(f["metric"] == "시청자수") & (f["매체"] == "웨이브")].dropna(subset=["회차", "회차_num"]).copy()
                has_wavve = not wsub.empty
                
                # 타이틀 결정
                chart_title = "📱 TVING & Wavve 시청자수" if has_wavve else "📱 TVING 시청자수"
                st.markdown(f"<div class='sec-title'>{chart_title}</div>", unsafe_allow_html=True)

                if not tsub.empty or not wsub.empty:
                    # --- 데이터 합치기 ---
                    combined = pd.DataFrame()
                    
                    if not tsub.empty:
                        media_map = {"TVING LIVE": "LIVE", "TVING QUICK": "당일 VOD", "TVING VOD": "주간 VOD"}
                        tsub["매체_표기"] = tsub["매체"].map(media_map)
                        combined = pd.concat([combined, tsub[["회차", "회차_num", "매체_표기", "value"]]])
                    
                    if has_wavve:
                        wsub["매체_표기"] = "Wavve"
                        combined = pd.concat([combined, wsub[["회차", "회차_num", "매체_표기", "value"]]])
                    
                    # Pivot
                    pvt = combined.pivot_table(index="회차", columns="매체_표기", values="value", aggfunc="sum").fillna(0)
                    
                    # 정렬 (회차 기준)
                    ep_order = combined[["회차", "회차_num"]].drop_duplicates().sort_values("회차_num")["회차"].tolist()
                    pvt = pvt.reindex(ep_order)
                    
                    # --- 차트 그리기 ---
                    fig_ott = go.Figure()
                    
                    # 1) TVING Traces (Always Visible)
                    tving_stack_order = ["LIVE", "당일 VOD", "주간 VOD"]
                    tving_colors = {"LIVE": "#90caf9", "당일 VOD": "#64b5f6", "주간 VOD": "#1565c0"}
                    
                    for m in tving_stack_order:
                        if m in pvt.columns:
                            fig_ott.add_trace(go.Bar(
                                name=m, x=pvt.index, y=pvt[m],
                                marker_color=tving_colors[m],
                                text=None,
                                hovertemplate=f"<b>%{{x}}</b><br>{m}: %{{y:,.0f}}<extra></extra>"
                            ))
                    
                    # 2) Wavve Trace (Visible='legendonly')
                    if "Wavve" in pvt.columns:
                        fig_ott.add_trace(go.Bar(
                            name="Wavve", x=pvt.index, y=pvt["Wavve"],
                            marker_color="#5c6bc0", # Wavve 전용 컬러 (인디고 계열)
                            visible='legendonly', # [핵심] 기본 숨김 처리
                            text=None,
                            hovertemplate="<b>%{x}</b><br>Wavve: %{y:,.0f}<extra></extra>"
                        ))

                    # 3) Total Label (TVING Sum Only - Default View 기준)
                    # 웨이브가 켜지면 막대 높이는 올라가지만, Total 텍스트는 TVING 합계 위치에 남음 (UI 복잡도 최소화)
                    tving_cols = [c for c in pvt.columns if c in tving_stack_order]
                    if tving_cols:
                        total_vals = pvt[tving_cols].sum(axis=1)
                        max_val = total_vals.max()
                        # 만약 웨이브가 더 크다면 max_val 보정 (축 잘림 방지)
                        if "Wavve" in pvt.columns:
                            max_val = max(max_val, (total_vals + pvt["Wavve"]).max())

                        total_txt = [fmt_live_kor(v) for v in total_vals]
                        
                        fig_ott.add_trace(go.Scatter(
                            x=pvt.index, y=total_vals, mode='text',
                            text=total_txt, textposition='top center',
                            textfont=dict(size=11, color='#333'),
                            showlegend=False, hoverinfo='skip'
                        ))
                    else:
                        max_val = pvt.max().max() if not pvt.empty else 100

                    fig_ott.update_layout(
                        barmode='stack', height=chart_h, margin=dict(l=8, r=8, t=10, b=8),
                        legend=dict(orientation='h', yanchor='bottom', y=1.02),
                        yaxis=dict(showgrid=False, visible=False, range=[0, max_val * 1.25]),
                        xaxis=dict(categoryorder="array", categoryarray=ep_order, fixedrange=True)
                    )
                    st.plotly_chart(fig_ott, use_container_width=True, config=common_cfg)
                    
                else:
                    st.info("표시할 시청자 데이터가 없습니다.")


            # === [Row2] 데모 분포 ===
            cG, cH, cI = st.columns(3)
            
            # [수정] 데모 분포 차트 (3개 컬럼)
            with cG:
                st.markdown("<div class='sec-title' style='font-size:18px;'>👥누적 시청자 분포 - TV</div>", unsafe_allow_html=True)
                tv_demo = f[(f["매체"] == "TV") & (f["metric"] == "시청인구") & f["데모"].notna()].copy()
                _render_pyramid_local(cG, "", tv_demo, height=260) # [수정] _render_pyramid_local 사용

            with cH:
                st.markdown("<div class='sec-title' style='font-size:18px;'>👥누적 시청자 분포 - TVING LIVE</div>", unsafe_allow_html=True)
                live_demo = f[(f["매체"] == "TVING LIVE") & (f["metric"] == "시청인구") & f["데모"].notna()].copy()
                _render_pyramid_local(cH, "", live_demo, height=260) # [수정] _render_pyramid_local 사용

            with cI:
                # [수정] TVING VOD는 QUICK과 합산
                st.markdown("<div class='sec-title' style='font-size:18px;'>👥누적 시청자 분포 - TVING VOD</div>", unsafe_allow_html=True)
                vod_demo = f[(f["매체"].isin(["TVING VOD", "TVING QUICK"])) & (f["metric"] == "시청인구") & f["데모"].notna()].copy()
                _render_pyramid_local(cI, "", vod_demo, height=260) # [수정] _render_pyramid_local 사용


            # === [Row3] 디지털 조회수/언급량 (2분할) ===
            cC, cD = st.columns(2)
            digital_colors = ['#5c6bc0', '#7e57c2', '#26a69a', '#66bb6a', '#ffa726', '#ef5350'] # [신규] 디지털 색상
            
            with cC:
                st.markdown("<div class='sec-title'>💻 디지털 조회수</div>", unsafe_allow_html=True)
                dview = _get_view_data(f) # [3. 공통 함수] (피드백 3번 반영)
                if not dview.empty:
                    if has_week_col and dview["주차"].notna().any():
                        order = (dview[["주차", "주차_num"]].dropna().drop_duplicates().sort_values("주차_num")["주차"].tolist())
                        pvt = dview.pivot_table(index="주차", columns="매체", values="value", aggfunc="sum").fillna(0)
                        pvt = pvt.reindex(order)
                        x_vals = pvt.index.tolist(); use_category = True
                    else:
                        pvt = (dview.pivot_table(index="주차시작일", columns="매체", values="value", aggfunc="sum").sort_index().fillna(0))
                        x_vals = pvt.index.tolist(); use_category = False

                    total_view = pvt.sum(axis=1) # [신규] 총합 계산
                    max_view = total_view.max()
                    view_ticks_val, view_ticks_txt = get_axis_ticks(max_view, formatter=_fmt_kor_large) # [신규] 축 눈금 포맷팅
                    total_text = [_fmt_kor_large(v) for v in total_view] # [신규] 총합 레이블

                    fig_view = go.Figure()
                    for i, col in enumerate(pvt.columns):
                        h_texts = [_fmt_kor_large(v) for v in pvt[col]] # [신규] 호버 텍스트
                        fig_view.add_trace(go.Bar(
                            name=col, x=x_vals, y=pvt[col], marker_color=digital_colors[i % len(digital_colors)],
                            hovertemplate="<b>%{x}</b><br>" + f"{col}: " + "%{text}<extra></extra>",
                            text=h_texts, textposition='none' # [신규] 텍스트 포지션
                        ))
                    
                    # [신규] 총합 레이블 트레이스
                    fig_view.add_trace(go.Scatter(
                        x=x_vals, y=total_view, mode='text', text=total_text, textposition='top center',
                        textfont=dict(size=11, color='#333'), showlegend=False, hoverinfo='skip'
                    ))
                    
                    fig_view.update_layout(
                        barmode="stack", legend_title=None, height=chart_h, margin=dict(l=8, r=8, t=10, b=8),
                        yaxis=dict(tickvals=view_ticks_val, ticktext=view_ticks_txt, fixedrange=True, range=[0, max_view * 1.15]) # [수정] y축 범위 및 눈금
                    )
                    if use_category: fig_view.update_xaxes(categoryorder="array", categoryarray=x_vals, fixedrange=True)
                    st.plotly_chart(fig_view, use_container_width=True, config=common_cfg)
                else:
                    st.info("표시할 조회수 데이터가 없습니다.")

            with cD:
                st.markdown("<div class='sec-title'>💬 디지털 언급량</div>", unsafe_allow_html=True)
                dbuzz = f[f["metric"] == "언급량"].copy()
                if not dbuzz.empty:
                    if has_week_col and dbuzz["주차"].notna().any():
                        order = (dbuzz[["주차", "주차_num"]].dropna().drop_duplicates().sort_values("주차_num")["주차"].tolist())
                        pvt = dbuzz.pivot_table(index="주차", columns="매체", values="value", aggfunc="sum").fillna(0)
                        pvt = pvt.reindex(order)
                        x_vals = pvt.index.tolist(); use_category = True
                    else:
                        pvt = (dbuzz.pivot_table(index="주차시작일", columns="매체", values="value", aggfunc="sum").sort_index().fillna(0))
                        x_vals = pvt.index.tolist(); use_category = False

                    total_buzz = pvt.sum(axis=1) # [신규] 총합 계산
                    max_buzz = total_buzz.max()
                    total_text = [f"{v:,.0f}" for v in total_buzz] # [신규] 총합 레이블

                    fig_buzz = go.Figure()
                    for i, col in enumerate(pvt.columns):
                        h_texts = [f"{v:,.0f}" for v in pvt[col]] # [신규] 호버 텍스트
                        fig_buzz.add_trace(go.Bar(
                            name=col, x=x_vals, y=pvt[col], marker_color=digital_colors[(i+2) % len(digital_colors)],
                            hovertemplate="<b>%{x}</b><br>" + f"{col}: " + "%{text}<extra></extra>",
                            text=h_texts, textposition='none' # [신규] 텍스트 포지션
                        ))
                    
                    # [신규] 총합 레이블 트레이스
                    fig_buzz.add_trace(go.Scatter(
                        x=x_vals, y=total_buzz, mode='text', text=total_text, textposition='top center',
                        textfont=dict(size=11, color='#333'), showlegend=False, hoverinfo='skip'
                    ))

                    fig_buzz.update_layout(
                        barmode="stack", legend_title=None, height=chart_h, margin=dict(l=8, r=8, t=10, b=8),
                        yaxis=dict(fixedrange=True, range=[0, max_buzz * 1.15]) # [수정] y축 범위
                    )
                    if use_category: fig_buzz.update_xaxes(categoryorder="array", categoryarray=x_vals, fixedrange=True)
                    st.plotly_chart(fig_buzz, use_container_width=True, config=common_cfg)
                else:
                    st.info("표시할 언급량 데이터가 없습니다.")

            # === [Row4] 화제성 & 넷플릭스 (2분할) ===
            cE, cF = st.columns(2)
            
            with cE:
                st.markdown("<div class='sec-title'>🔥 화제성 점수 & 순위</div>", unsafe_allow_html=True) # [수정] 제목
                fdx = _metric_filter(f, "F_Total").copy(); fs = _metric_filter(f, "F_score").copy()
                
                # [수정] 화제성 통합 차트 로직 (Dashboard_test.py 8.에서 이식)
                if has_week_col and f["주차"].notna().any():
                    order = (f[["주차", "주차_num"]].dropna().drop_duplicates().sort_values("주차_num")["주차"].tolist())
                    key_col = "주차"; use_category = True
                else:
                    key_col = "주차시작일"; order = sorted(f[key_col].dropna().unique()); use_category = False
                    
                if not fs.empty:
                    fs["val"] = pd.to_numeric(fs["value"], errors="coerce")
                    fs_agg = fs.dropna(subset=[key_col]).groupby(key_col, as_index=False)["val"].mean()
                else: fs_agg = pd.DataFrame(columns=[key_col, "val"])
                    
                if not fdx.empty:
                    fdx["rank"] = pd.to_numeric(fdx["value"], errors="coerce")
                    fdx_agg = fdx.dropna(subset=[key_col]).groupby(key_col, as_index=False)["rank"].min()
                else: fdx_agg = pd.DataFrame(columns=[key_col, "rank"])
                    
                if not fs_agg.empty:
                    merged = pd.merge(fs_agg, fdx_agg, on=key_col, how="left")
                    if use_category: merged = merged.set_index(key_col).reindex(order).dropna(subset=["val"]).reset_index()
                    else: merged = merged.sort_values(key_col)
                    
                    if not merged.empty:
                        x_vals = merged[key_col].tolist(); y_vals = merged["val"].tolist()
                        # [수정] 라벨 포맷 변경
                        labels = [f"{int(r['rank'])}위<br>/{int(r['val']):,}점" if pd.notna(r['rank']) else f"{int(r['val']):,}점" for _, r in merged.iterrows()]
                        
                        fig_comb = go.Figure()
                        fig_comb.add_trace(go.Scatter(
                            x=x_vals, y=y_vals, mode="lines+markers+text", name="화제성 점수",
                            text=labels, textposition="top center", textfont=dict(size=11, color="#333"),
                            line=dict(color='#ec407a', width=3), marker=dict(size=7, color='#ec407a')
                        ))
                        if y_vals: fig_comb.update_yaxes(range=[0, max(y_vals) * 1.25], title=None, fixedrange=True)
                        if use_category: fig_comb.update_xaxes(categoryorder="array", categoryarray=x_vals, fixedrange=True)
                        fig_comb.update_layout(legend_title=None, height=chart_h, margin=dict(l=8, r=8, t=20, b=8))
                        st.plotly_chart(fig_comb, use_container_width=True, config=common_cfg)
                    else: st.info("표시할 화제성 데이터가 없습니다.")
                else: st.info("표시할 화제성 데이터가 없습니다.")

            # [신규] 넷플릭스 주간 순위 그래프 추가
            with cF:
                st.markdown("<div class='sec-title'>🍿 넷플릭스 주간 순위 추이</div>", unsafe_allow_html=True)
                # N_W순위 데이터 필터링 (0은 제외)
                n_df = _metric_filter(f, "N_W순위").copy()
                n_df["val"] = pd.to_numeric(n_df["value"], errors="coerce").replace(0, np.nan)
                n_df = n_df.dropna(subset=["val"])

                if not n_df.empty:
                    if has_week_col and f["주차"].notna().any():
                        # 주차별 최소 순위 (1위가 최고)
                        n_agg = n_df.groupby("주차", as_index=False)["val"].min()
                        # 주차 정렬
                        all_weeks = (f[["주차", "주차_num"]].dropna().drop_duplicates().sort_values("주차_num")["주차"].tolist())
                        n_agg = n_agg.set_index("주차").reindex(all_weeks).dropna().reset_index()
                        x_vals = n_agg["주차"]
                        use_cat = True
                    else:
                        n_agg = n_df.groupby("주차시작일", as_index=False)["val"].min().sort_values("주차시작일")
                        x_vals = n_agg["주차시작일"]
                        use_cat = False
                    
                    y_vals = n_agg["val"]
                    labels = [f"{int(v)}위" for v in y_vals]

                    fig_nf = go.Figure()
                    fig_nf.add_trace(go.Scatter(
                        x=x_vals, y=y_vals, mode="lines+markers+text", name="넷플릭스 순위",
                        text=labels, textposition="top center",
                        line=dict(color='#E50914', width=3), # Netflix Red
                        marker=dict(size=7, color='#E50914')
                    ))
                    
                    # Y축 반전 (1위가 위로 가도록)
                    # 범위 설정: 1위 ~ max+buffer. autorange="reversed" 사용
                    fig_nf.update_yaxes(autorange="reversed", title=None, fixedrange=True, zeroline=False)
                    
                    if use_cat:
                        fig_nf.update_xaxes(categoryorder="array", categoryarray=all_weeks, fixedrange=True)
                    
                    fig_nf.update_layout(legend_title=None, height=chart_h, margin=dict(l=8, r=8, t=20, b=8))
                    st.plotly_chart(fig_nf, use_container_width=True, config=common_cfg)

                else:
                    st.info("넷플릭스 방영 기록이 없거나 데이터가 없습니다.")


            st.divider()

            # === [Row5] 데모분석 상세 표 (AgGrid) ===
            st.markdown("#### 👥 회차별 시청자수 분포")

            # [신규] _build_demo_table_numeric (Dashboard_test.py 8.에서 이식)
            def _build_demo_table_numeric(df_src: pd.DataFrame, medias: List[str]) -> pd.DataFrame:
                sub = df_src[
                    (df_src["metric"] == "시청인구") &
                    (df_src["데모"].notna()) &
                    (df_src["매체"].isin(medias))
                ].copy()
                if sub.empty:
                    return pd.DataFrame(columns=["회차"] + DEMO_COLS_ORDER)

                sub["성별"] = sub["데모"].apply(_gender_from_demo)
                sub["연령대_대"] = sub["데모"].apply(_decade_label_clamped)
                sub = sub[sub["성별"].isin(["남", "여"]) & sub["연령대_대"].notna()].copy()
                
                if "회차_num" not in sub.columns: 
                    sub["회차_num"] = sub["회차"].str.extract(r"(\d+)", expand=False).astype(float)

                sub = sub.dropna(subset=["회차_num"])
                sub["회차_num"] = sub["회차_num"].astype(int)
                sub["라벨"] = sub.apply(lambda r: f"{r['연령대_대']}{'남성' if r['성별']=='남' else '여성'}", axis=1)

                pvt = sub.pivot_table(index="회차_num", columns="라벨", values="value", aggfunc="sum").fillna(0)

                for c in DEMO_COLS_ORDER:
                    if c not in pvt.columns:
                        pvt[c] = 0
                pvt = pvt[DEMO_COLS_ORDER].sort_index()
                pvt.insert(0, "회차", pvt.index.map(_fmt_ep))
                return pvt.reset_index(drop=True)

            # [수정] AgGrid Diff Renderer (작은 삼각형 ▴, ▾)
            diff_renderer = JsCode("""
            class DiffRenderer {
              init(params) {
                this.eGui = document.createElement('span');
                
                const api = params.api;
                const colId = params.column.getColId();
                const rowIndex = params.node.rowIndex;
                const val = Number(params.value || 0);
                
                // 1. 숫자 포맷팅
                let displayVal = colId === "회차" ? params.value : Math.round(val).toLocaleString();
                
                // 2. 화살표 로직
                let arrow = "";
                if (colId !== "회차" && rowIndex > 0) {
                  const prev = api.getDisplayedRowAtIndex(rowIndex - 1);
                  if (prev && prev.data && prev.data[colId] != null) {
                    const pv = Number(prev.data[colId] || 0);
                    
                    if (val > pv) {
                       // 상승: (▴) 작은 삼각형, 빨간색
                       arrow = '<span style="margin-left:4px;">(<span style="color:#d93636;">▴</span>)</span>';
                    } else if (val < pv) {
                       // 하락: (▾) 작은 삼각형, 파란색
                       arrow = '<span style="margin-left:4px;">(<span style="color:#2a61cc;">▾</span>)</span>';
                    }
                  }
                }
                
                // 3. HTML 주입
                this.eGui.innerHTML = displayVal + arrow;
              }

              getGui() {
                return this.eGui;
              }
            }
            """)

            _js_demo_cols = "[" + ",".join([f'"{c}"' for c in DEMO_COLS_ORDER]) + "]"
            # [수정] Cell Style Renderer (Dashboard_test.py 8.에서 이식)
            cell_style_renderer = JsCode(f"""
            function(params){{
              const field = params.colDef.field;
              if (field === "회차") return {{'text-align':'left','font-weight':'600','background-color':'#fff'}};
              const COLS = {_js_demo_cols};
              let rowVals = [];
              for (let k of COLS) {{
                const v = Number((params.data && params.data[k] != null) ? params.data[k] : NaN);
                if (!isNaN(v)) rowVals.push(v);
              }}
              let bg = '#ffffff';
              if (rowVals.length > 0) {{
                const v = Number(params.value || 0);
                const mn = Math.min.apply(null, rowVals);
                const mx = Math.max.apply(null, rowVals);
                let norm = 0.5;
                if (mx > mn) norm = (v - mn) / (mx - mn);
                const alpha = 0.12 + 0.45 * Math.max(0, Math.min(1, norm));
                bg = 'rgba(30,90,255,' + alpha.toFixed(3) + ')';
              }}
              return {{'background-color': bg, 'text-align': 'right', 'padding': '2px 4px', 'font-weight': '500'}};
            }}""")

            # [수정] AgGrid 렌더러 (Dashboard_test.py 8.에서 이식)
            def _render_aggrid_table(df_numeric: pd.DataFrame, title: str):
                st.markdown(f"###### {title}")
                if df_numeric.empty: st.info("데이터 없음"); return
                gb = GridOptionsBuilder.from_dataframe(df_numeric)
                # [수정] domLayout='autoHeight'
                gb.configure_grid_options(rowHeight=34, suppressMenuHide=True, domLayout='autoHeight')
                gb.configure_default_column(sortable=False, resizable=True, filter=False, cellStyle={'textAlign': 'right'}, headerClass='centered-header bold-header')
                gb.configure_column("회차", header_name="회차", cellStyle={'textAlign': 'left'})
                
                for c in [col for col in df_numeric.columns if col != "회차"]:
                    gb.configure_column(c, header_name=c, cellRenderer=diff_renderer, cellStyle=cell_style_renderer)
                    
                # [신규] fit_columns_on_grid_load=True 추가
                AgGrid(
                    df_numeric, 
                    gridOptions=gb.build(), 
                    theme="streamlit", 
                    height=None, 
                    update_mode=GridUpdateMode.NO_UPDATE, 
                    allow_unsafe_jscode=True,
                    fit_columns_on_grid_load=True
                )


            tv_numeric = _build_demo_table_numeric(f, ["TV"])
            _render_aggrid_table(tv_numeric, "📺 TV (시청자수)")

            tving_numeric = _build_demo_table_numeric(
                f, ["TVING LIVE", "TVING QUICK", "TVING VOD"]
            )
            _render_aggrid_table(tving_numeric, "▶︎ TVING 합산 시청자수")
#endregion

    # ===== 탭 2+: 임베딩된 G-Sheet (재배치된 위젯에 렌더링) =====
    for tab_widget, sheet_url in sheet_widgets:
        with tab_widget:
            # 탭 타이틀은 이미 탭 버튼에 있으므로 생략하거나, 필요시 표시
            render_published_url(sheet_url) # [ 3. 공통 함수 ]


#region [7.5. 종영작 리스트 페이지]
# =====================================================
def render_ended_ip_list_page(ip_status_map: Dict[str, str]):
    """
    종영된 IP의 요약 정보를 카드에 표시하는 페이지.

    변경 사항:
    - st.button 대신 HTML 카드(<a> + <div>)로 렌더
    - IP명은 굵게(bold), 아래 지표는 줄바꿈해서 표시
    - 마지막 줄 빈 칸은 '빈 카드 박스'만 유지 (텍스트 없음)
    - 클릭 시 ?ip=IP명 쿼리파라미터로 이동 → 메인 로직에서 그대로 처리
    """
    from urllib.parse import quote

    # 1. 종영 IP 리스트 추출
    ended_list = [ip for ip, status in ip_status_map.items() if status == "종영"]

    st.markdown(
        f"<div class='page-title'>🏁 종영작 모아보기 ({len(ended_list)})</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if not ended_list:
        st.info("종영된 IP 데이터가 없습니다.")
        return

    # 2. 원본 데이터 로드
    df = load_data()

    # 3. 4열 그리드로 카드 배치
    cols_per_row = 4
    for i in range(0, len(ended_list), cols_per_row):
        row_ips = ended_list[i : i + cols_per_row]
        cols = st.columns(cols_per_row)

        # (1) 실제 카드들
        for col, ip_name in zip(cols, row_ips):
            with col:
                sub = df[df["IP"] == ip_name].copy()

                # --- 시청률 계산 ---
                val_T = mean_of_ip_episode_mean(sub, "T시청률")
                val_H = mean_of_ip_episode_mean(sub, "H시청률")

                fmt_T = f"{val_T:.2f}%" if val_T is not None else "-"
                fmt_H = f"{val_H:.2f}%" if val_H is not None else "-"

                # --- 방영 시작일 계산 ---
                start_date_str = "-"
                if "방영시작일" in sub.columns:
                    dates = pd.to_datetime(sub["방영시작일"], errors="coerce").dropna()
                    if not dates.empty:
                        start_date_str = dates.min().strftime("%Y-%m-%d")
                elif "주차시작일" in sub.columns:
                    dates = pd.to_datetime(sub["주차시작일"], errors="coerce").dropna()
                    if not dates.empty:
                        start_date_str = dates.min().strftime("%Y-%m-%d")

                # --- 카드 HTML 구성 ---
                # 1줄: IP명 (굵게)
                # 2~4줄: 타깃/가구/방영시작 (줄바꿈)
                card_html = f"""
<a href="?ip={quote(ip_name)}" style="text-decoration:none; color:inherit;">
  <div style="
      border-radius: 12px;
      padding: 14px 16px;
      border: 1px solid #e5e7eb;
      background: #ffffff;
      box-shadow: 0 2px 4px rgba(15,23,42,0.06);
      min-height: 130px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
  ">
    <div style="font-weight: 700; font-size: 14px; margin-bottom: 6px; color:#111827;">
      {ip_name}
    </div>
    <div style="font-size: 12px; line-height: 1.5; color:#4b5563;">
      🎯 타깃 : {fmt_T}<br>
      🏠 가구 : {fmt_H}<br>
      📅 시작 : {start_date_str}
    </div>
  </div>
</a>
"""
                st.markdown(card_html, unsafe_allow_html=True)

        # (2) 남는 칸은 "빈 카드 박스"만 만들어서 그리드 유지 (텍스트 없음)
        if len(row_ips) < cols_per_row:
            for col in cols[len(row_ips) :]:
                with col:
                    st.markdown(
                        """
<div style="
    border-radius: 12px;
    padding: 14px 16px;
    border: 1px solid transparent;
    min-height: 130px;
">
</div>
""",
                        unsafe_allow_html=True,
                    )

        # 행 간 여백
        st.write("")

#endregion


#region [ 8. 메인 실행  ]
# =====================================================

# --- 1. 세션 스테이트 초기화 ---
if "selected_ip" not in st.session_state:
    st.session_state.selected_ip = None 

# --- 2. 데이터 로드 ---
on_air_data, ip_status_map = load_processed_on_air_data() 
on_air_ips = list(ip_status_map.keys())

# --- 3. URL 파라미터 처리 ---
url_ip = None
url_tab = None # [신규] 탭 파라미터 변수

if hasattr(st, "query_params"):
    # Streamlit 최신 버전 (Dictionary-like)
    url_ip = st.query_params.get("ip", None)
    url_tab = st.query_params.get("tab", None) # [신규]
else:
    # Streamlit 구버전 (List-like)
    params = st.experimental_get_query_params()
    url_ip = params.get("ip", [None])[0]
    url_tab = params.get("tab", [None])[0] # [신규]

# [수정] URL 파라미터는 '세션 정보가 없을 때(최초 진입)'만 적용하도록 조건 추가
# (버튼 클릭 시에는 이미 session_state가 설정되어 있으므로 URL을 무시해야 함)
if st.session_state.selected_ip is None and url_ip:
    if url_ip in ip_status_map:          # 방영중/종영 여부 상관 없이, 목록에 있는 IP면
        st.session_state.selected_ip = url_ip
    elif url_ip == "__ENDED_LIST__":     # 종영작 리스트 페이지용 특수 값
        st.session_state.selected_ip = "__ENDED_LIST__"

# 최초 로드 시 URL에 IP가 없고, 세션도 비어있다면 -> 방영중 첫 번째 IP 자동 선택
if st.session_state.selected_ip is None:
    if on_air_ips:
        # 방영중인 것 중 첫번째
        actives = [k for k,v in ip_status_map.items() if v == "방영중"]
        if actives:
            st.session_state.selected_ip = actives[0]
        else:
            # 방영중 없으면 종영작 리스트로
            st.session_state.selected_ip = "__ENDED_LIST__"
    elif not on_air_ips and "__ENDED_LIST__" in url_ip: # 데이터가 아예 없을 때 예외처리
         st.session_state.selected_ip = "__ENDED_LIST__"


# --- 4. 사이드바 렌더링 ---
render_sidebar_navigation(ip_status_map)


# --- 5. 메인 컨텐츠 라우팅 ---
current_ip = st.session_state.selected_ip

if current_ip == "__ENDED_LIST__":
    # [신규] 종영작 리스트 페이지
    render_ended_ip_list_page(ip_status_map)
    # URL 업데이트
    if hasattr(st, "query_params"): st.query_params["ip"] = "__ENDED_LIST__"
    else: st.experimental_set_query_params(ip="__ENDED_LIST__")

elif current_ip in on_air_ips:
    # [수정] url_tab 인자 전달
    # (주의: URL의 IP와 현재 선택된 IP가 다르면 탭 이동을 하지 않아야 꼬이지 않음)
    target_tab_arg = url_tab if (url_ip == current_ip) else None
    
    # [기존] IP 상세 페이지 + [신규] 탭 이동
    render_ip_detail(current_ip, on_air_data, target_tab=target_tab_arg)
    
    # URL 업데이트
    if hasattr(st, "query_params"): 
        st.query_params["ip"] = current_ip
        if target_tab_arg: st.query_params["tab"] = target_tab_arg # 탭 정보 유지
    else: 
        p = {"ip": current_ip}
        if target_tab_arg: p["tab"] = target_tab_arg
        st.experimental_set_query_params(**p)

else:
    # 예외 처리
    st.empty()
    
#endregion

