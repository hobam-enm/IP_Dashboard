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
    page_title="Drama Dashboard - IP Detail", # 페이지 타이틀 수정
    layout="wide",
    initial_sidebar_state="expanded"
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
    min-width:320px !important;
    max-width:320px !important;
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
    font-size: 15px; 
    font-weight: 600; 
    margin-bottom: 10px; 
    color: #444; 
}
.kpi-value { 
    font-size: 28px; 
    font-weight: 700; 
    color: #000; 
    line-height: 1.2;
}
.kpi-subwrap { margin-top: 10px; line-height: 1.4; }
.kpi-sublabel { font-size: 12px; font-weight: 500; color: #555; letter-spacing: 0.1px; margin-right: 6px; }
.kpi-substrong { font-size: 14px; font-weight: 700; color: #111; }
.kpi-subpct { font-size: 14px; font-weight: 700; }

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
    if "주차시작일" in df.columns:
        df["주차시작일"] = pd.to_datetime(
            df["주차시작일"].astype(str).str.strip(),
            format="%Y. %m. %d",
            errors="coerce"
        )
    if "방영시작일" in df.columns:
        df["방영시작일"] = pd.to_datetime(
            df["방영시작일"].astype(str).str.strip(),
            format="%Y. %m. %d",
            errors="coerce"
        )

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

# ===== 3.1c. [수정] '방영중' 탭 (A,B,C,D열) 처리 =====
@st.cache_data(ttl=600)
def load_processed_on_air_data() -> Dict[str, List[Dict[str, str]]]:
    """
    [수정] '방영중' 탭(A,B,C,D열)을 읽어 최종 임베딩 URL 맵을 생성합니다.
    1. C열 URL로 GID 맵 가져오기 (get_tab_gids_from_sheet)
    2. D열 URL에 B열 탭의 GID를 조합하여 최종 URL 생성
    """
    worksheet_name = "방영중"
    
    client = get_gspread_client()
    if client is None:
        return {}
        
    try:
        sheet_id = st.secrets["SHEET_ID"]
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # 'A2:D' 범위의 모든 값을 가져옵니다 (헤더 제외).
        values = worksheet.get_values('A2:D') 
        
        # 1. A,B,C,D열 데이터를 IP별로 그룹화
        config_map = {}
        for row in values:
            if row and len(row) > 3 and row[0].strip() and row[1].strip() and row[2].strip() and row[3].strip():
                ip, tab_name, edit_url, pub_url = [s.strip() for s in row]
                
                if ip not in config_map:
                    config_map[ip] = {
                        "edit_url": edit_url, # C열 (GID 찾기용)
                        "publish_url_base": pub_url.split('?')[0], # D열 (임베딩용, ?gid= 전까지)
                        "tabs_to_process": [] # B열 (탭 이름 목록)
                    }
                config_map[ip]["tabs_to_process"].append(tab_name)

        # 2. IP별로 GID를 찾아 최종 URL 조합
        final_data_structure = {}
        for ip, config in config_map.items():
            final_data_structure[ip] = []
            
            # C열 URL로 API 호출하여 GID 맵 가져오기
            gid_map = get_tab_gids_from_sheet(config["edit_url"]) 
            
            if not gid_map: # API 호출 실패 시 (권한 오류 등)
                st.warning(f"'{ip}'의 GID를 C열 시트에서 가져오지 못했습니다. (권한 확인 필요)")
                continue 

            # B열의 탭 이름을 GID로 변환하고 D열 URL과 조합
            for tab_name in config["tabs_to_process"]:
                gid = gid_map.get(tab_name.strip())
                
                if gid is not None:
                    # D열 URL 베이스 + 찾은 GID
                    final_url = f"{config['publish_url_base']}?gid={gid}&single=true"
                    
                    # '사전 반응' 탭 우선 정렬
                    if "사전 반응" in tab_name:
                         final_data_structure[ip].insert(0, {"title": tab_name, "url": final_url})
                    else:
                         final_data_structure[ip].append({"title": tab_name, "url": final_url})
                else:
                    st.warning(f"'{ip}'의 시트(C열)에서 '{tab_name}'(B열) 탭을 찾을 수 없습니다.")

        return final_data_structure

    except gspread.exceptions.WorksheetNotFound:
        st.sidebar.error(f"'{worksheet_name}' 탭을 찾을 수 없습니다.")
        return {}
    except Exception as e:
        st.sidebar.error(f"'방영중' 탭(A:D열) 로드 오류: {e}")
        return {}

# ===== 3.2. UI / 포맷팅 헬퍼 함수 =====

def fmt(v, digits=3, intlike=False):
    """
    숫자 포맷팅 헬퍼 (None이나 NaN은 '–'로 표시)
    """
    if v is None or pd.isna(v):
        return "–"
    return f"{v:,.0f}" if intlike else f"{v:.{digits}f}"

# ===== [수정] 3.2b. G-Sheet '게시용' URL 렌더러 =====
def render_published_url(published_url: str):
    """[수정] '웹에 게시'된 URL을 iframe으로 렌더링합니다. (URL 변환 X)"""
    
    st.markdown(f"""
        <iframe
            src="{published_url}"
            style="width: 100%; height: 700px; border: 1px solid #e0e0e0; border-radius: 8px;"
        ></iframe>
        """, unsafe_allow_html=True)


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
#endregion


#region [ 4. 사이드바 - IP 네비게이션 ]
# =====================================================
def render_sidebar_navigation(on_air_ips: List[str]):
    """
    [수정] '방영중' 탭(A열)에서 불러온 고유 IP 목록으로 네비게이션 버튼을 렌더링합니다.
    """
    
    # --- 1. '방영중' IP 목록 (A열) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("######  NAVIGATING")
    
    current_selected_ip = st.session_state.get("selected_ip", None)
    
    if not on_air_ips:
        st.sidebar.warning("'방영중' 탭(A열)에 IP가 없습니다.")
        st.session_state.selected_ip = None
        return

    # [수정] st.session_state.selected_ip가 None이거나 목록에 없으면, 첫 번째 IP로 강제 설정
    if current_selected_ip is None or current_selected_ip not in on_air_ips:
        st.session_state.selected_ip = on_air_ips[0]
        current_selected_ip = on_air_ips[0]

    # '방영중' IP 목록으로 버튼 생성
    for ip_name in on_air_ips:
        is_active = (current_selected_ip == ip_name)
        wrapper_cls = "nav-active" if is_active else "nav-inactive"
        st.sidebar.markdown(f'<div class="{wrapper_cls}">', unsafe_allow_html=True)

        clicked = st.sidebar.button(
            ip_name,
            key=f"navbtn__{ip_name}",
            use_container_width=True,
            type=("primary" if is_active else "secondary")
        )
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        
        if clicked and not is_active:
            st.session_state.selected_ip = ip_name
            _rerun() # _rerun은 Region 1-1에 정의됨
    
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

# [수정] gender_from_demo() 는 이 페이지에서 미사용 (페이지 3 전용)

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

# ===== 6.2. 피라미드 차트 렌더링 (페이지 1, 2) =====
COLOR_MALE = "#2a61cc"
COLOR_FEMALE = "#d93636"

def render_gender_pyramid(container, title: str, df_src: pd.DataFrame, height: int = 260):

    if df_src.empty:
        container.info("표시할 데이터가 없습니다.")
        return

    df_demo = df_src.copy()
    df_demo["성별"] = df_demo["데모"].apply(_gender_from_demo)
    df_demo["연령대_대"] = df_demo["데모"].apply(_to_decade_label)
    df_demo = df_demo[df_demo["성별"].isin(["남","여"]) & df_demo["연령대_대"].notna()]

    if df_demo.empty:
        container.info("표시할 데모 데이터가 없습니다.")
        return

    order = sorted(df_demo["연령대_대"].unique().tolist(), key=_decade_key)

    pvt = (
        df_demo.groupby(["연령대_대","성별"])["value"]
               .sum()
               .unstack("성별")
               .reindex(order)
               .fillna(0)
    )

    male = -pvt.get("남", pd.Series(0, index=pvt.index))
    female = pvt.get("여", pd.Series(0, index=pvt.index))

    max_abs = float(max(male.abs().max(), female.max()) or 1)

    male_share = (male.abs() / male.abs().sum() * 100) if male.abs().sum() else male.abs()
    female_share = (female / female.sum() * 100) if female.sum() else female

    male_text = [f"{v:.1f}%" for v in male_share]
    female_text = [f"{v:.1f}%" for v in female_share]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=pvt.index, x=male, name="남",
        orientation="h",
        marker_color=COLOR_MALE,
        text=male_text,
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(color="#ffffff", size=12),
        hovertemplate="연령대=%{y}<br>남성=%{customdata[0]:,.0f}명<br>성별내 비중=%{customdata[1]:.1f}%<extra></extra>",
        customdata=np.column_stack([male.abs(), male_share])
    ))
    fig.add_trace(go.Bar(
        y=pvt.index, x=female, name="여",
        orientation="h",
        marker_color=COLOR_FEMALE,
        text=female_text,
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(color="#ffffff", size=12),
        hovertemplate="연령대=%{y}<br>여성=%{customdata[0]:,.0f}명<br>성별내 비중=%{customdata[1]:.1f}%<extra></extra>",
        customdata=np.column_stack([female, female_share])
    ))

    fig.update_layout(
        barmode="overlay",
        height=height,
        margin=dict(l=8, r=8, t=48, b=8),
        legend_title=None,
        bargap=0.15,
        bargroupgap=0.05,
    )
    # 피라미드 차트 전용 로컬 제목 (전역 테마 오버라이드)
    fig.update_layout(
        title=dict(
            text=title,
            x=0.0, xanchor="left",
            y=0.98, yanchor="top",
            font=dict(size=14)
        )
    )
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=order,
        title=None,
        tickfont=dict(size=12),
        fixedrange=True
    )
    fig.update_xaxes(
        range=[-max_abs*1.05, max_abs*1.05],
        title=None,
        showticklabels=False,
        showgrid=False,
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="#888",
        fixedrange=True
    )

    container.plotly_chart(fig, use_container_width=True,
                           config={"scrollZoom": False, "staticPlot": False, "displayModeBar": False})

# [수정] get_avg_demo_pop_by_episode() 함수 제거 (페이지 3 전용)
#endregion


#region [ 7. 페이지 2: IP 성과 자세히보기 ]
# =====================================================
# [수정] 원본 Region 8
def render_ip_detail(ip_selected: str, on_air_data: Dict[str, List[Dict[str, str]]]):
    """
    [수정] ip_selected와 '방영중' 탭에서 처리된 최종 데이터를 인자로 받음
    [수정] 탭 UI를 페이지 최상단으로 이동
    """

    # ===== [수정] 1. 고정 페이지 타이틀 (항상 표시) =====
    st.markdown(f"<div class='page-title'>📈 {ip_selected} 시청자 반응 브리핑</div>", unsafe_allow_html=True)

    # ===== [수정] 2. 탭 UI 구성 (페이지 상단) =====
    
    # 2a. 임베딩할 탭 목록 가져오기
    embeddable_tabs = on_air_data.get(ip_selected, []) 

    # 2b. [수정] 탭 생성 방식을 st.tab()으로 변경 (비활성 탭 추가)
    main_tab = st.tab("📈 성과 자세히보기")
    
    # [신규] 2. G-Sheet에서 가져온 탭이 있을 경우에만 더미 탭과 G-Sheet 탭 추가
    sheet_tabs_info = [] # G-Sheet 탭 위젯과 정보를 저장할 리스트
    if embeddable_tabs:
        # [신규] 2. 더미 탭 (시각적 구분용)
        st.tab("👥 시청자 반응 브리핑", disabled=True) 

        # [신규] 2. G-Sheet 탭 목록 생성
        for tab_info in embeddable_tabs:
            tab_widget = st.tab(tab_info["title"])
            # 위젯과 정보를 함께 저장
            sheet_tabs_info.append({"widget": tab_widget, "info": tab_info})
    
    # [기존 코드 삭제]
    # tab_titles = ["📈 성과 자세히보기"] + [tab["title"] for tab in embeddable_tabs]
    # main_tab, *sheet_tabs = st.tabs(tab_titles)

    # ===== 탭 1: 기존 성과 자세히보기 =====
    with main_tab:
        
        # [신규] 탭 서브 타이틀
        st.markdown(f"### 📈 성과 자세히보기") # [수정] 2. 탭 제목 일관성
        
        # [수정] 1. '비교 그룹 기준' 필터를 탭 내부로, 컬럼 제거
        selected_group_criteria = st.multiselect(
            "📊 비교 그룹 기준 선택", # [수정] 1. 레이블 명시
            ["동일 편성", "방영 연도"],
            default=["동일 편성"],
            key="ip_detail_group"
            # [수정] 1. label_visibility="collapsed" 및 st.columns 제거
        )
        
        # [기존 코드 삭제]
        # _col_spacer, col_filter = st.columns([3, 2])
        # with col_filter:
        #    selected_group_criteria = st.multiselect(...)
        
        # --- [이하 'render_ip_detail'의 기존 로직을 main_tab 안에 배치] ---
        
        df_full = load_data() # [3. 공통 함수]
        
        if "방영시작일" in df_full.columns and df_full["방영시작일"].notna().any():
            date_col_for_filter = "방영시작일"
        else:
            date_col_for_filter = "주차시작일"

        # --- 선택 IP / 기간 필터 ---
        f = df_full[df_full["IP"] == ip_selected].copy()

        if "회차_numeric" in f.columns:
            f["회차_num"] = pd.to_numeric(f["회차_numeric"], errors="coerce")
        else:
            f["회차_num"] = pd.to_numeric(f["회차"].str.extract(r"(\d+)", expand=False), errors="coerce")

        def _week_to_num(x: str):
            m = re.search(r"-?\d+", str(x))
            return int(m.group(0)) if m else None

        has_week_col = "주차" in f.columns
        if has_week_col:
            f["주차_num"] = f["주차"].apply(_week_to_num)

        try:
            sel_prog = f["편성"].dropna().mode().iloc[0]
        except Exception:
            sel_prog = None

        try:
            sel_year = (
                f[date_col_for_filter].dropna().dt.year.mode().iloc[0]
                if date_col_for_filter in f.columns and not f[date_col_for_filter].dropna().empty
                else None
            )
        except Exception:
            sel_year = None

        # --- 베이스(비교 그룹 기준) ---
        base = df_full.copy()
        group_name_parts = []

        if "동일 편성" in selected_group_criteria:
            if sel_prog:
                base = base[base["편성"] == sel_prog]
                group_name_parts.append(f"'{sel_prog}'")
            else:
                st.warning(f"'{ip_selected}'의 편성 정보가 없어 '동일 편성' 기준은 제외됩니다.", icon="⚠️")

        if "방영 연도" in selected_group_criteria:
            if sel_year:
                base = base[base[date_col_for_filter].dt.year == sel_year]
                group_name_parts.append(f"{int(sel_year)}년")
            else:
                st.warning(f"'{ip_selected}'의 연도 정보가 없어 '방영 연도' 기준은 제외됩니다.", icon="⚠️")

        if not group_name_parts and selected_group_criteria:
            st.warning("그룹핑 기준 정보 부족. 전체 데이터와 비교합니다.", icon="⚠️")
            group_name_parts.append("전체")
            base = df_full.copy()
        elif not group_name_parts:
            group_name_parts.append("전체")
            base = df_full.copy()

        prog_label = " & ".join(group_name_parts) + " 평균"

        if "회차_numeric" in base.columns:
            base["회차_num"] = pd.to_numeric(base["회차_numeric"], errors="coerce")
        else:
            base["회차_num"] = pd.to_numeric(base["회차"].str.extract(r"(\d+)", expand=False), errors="coerce")

        # [수정] 이 sub-title은 탭 이름으로 대체되었으므로 주석 처리 (또는 삭제)
        # st.markdown(
        #     f"<div class='sub-title'>📺 {ip_selected} 성과 상세 리포트</div>",
        #     unsafe_allow_html=True
        # )
        st.markdown("---") # st.markdown("---") 대신 <hr> 사용

        # --- Metric Normalizer (페이지 2 전용) ---
        def _normalize_metric(s: str) -> str:
            if s is None:
                return ""
            s2 = re.sub(r"[^A-Za-z0-9가-힣]+", "", str(s)).lower()
            return s2

        def _metric_filter(df: pd.DataFrame, name: str) -> pd.DataFrame:
            target = _normalize_metric(name)
            if "metric_norm" not in df.columns:
                df = df.copy()
                df["metric_norm"] = df["metric"].apply(_normalize_metric)
            return df[df["metric_norm"] == target]

        # --- KPI/평균비/랭킹 계산 ---
        val_T = mean_of_ip_episode_mean(f, "T시청률") # [5. 공통 함수]
        val_H = mean_of_ip_episode_mean(f, "H시청률") # [5. 공통 함수]
        val_live = mean_of_ip_episode_sum(f, "시청인구", ["TVING LIVE"]) # [5. 공통 함수]
        val_quick = mean_of_ip_episode_sum(f, "시청인구", ["TVING QUICK"]) # [5. 공통 함수]
        val_vod = mean_of_ip_episode_sum(f, "시청인구", ["TVING VOD"]) # [5. 공통 함수]
        val_buzz = mean_of_ip_sums(f, "언급량") # [5. 공통 함수]
        val_view = mean_of_ip_sums(f, "조회수") # [5. 공통 함수]

        # --- 화제성 메트릭 (페이지 2 전용) ---
        def _min_of_ip_metric(df_src: pd.DataFrame, metric_name: str) -> float | None:
            sub = _metric_filter(df_src, metric_name).copy()
            if sub.empty:
                return None
            s = pd.to_numeric(sub["value"], errors="coerce").dropna()
            return float(s.min()) if not s.empty else None

        def _mean_like_rating(df_src: pd.DataFrame, metric_name: str) -> float | None:
            sub = _metric_filter(df_src, metric_name).copy()
            if sub.empty:
                return None
            sub["val"] = pd.to_numeric(sub["value"], errors="coerce")
            sub = sub.dropna(subset=["val"])
            if sub.empty:
                return None

            if "회차_num" in sub.columns and sub["회차_num"].notna().any():
                g = sub.dropna(subset=["회차_num"]).groupby("회차_num", as_index=False)["val"].mean()
                return float(g["val"].mean()) if not g.empty else None

            if date_col_for_filter in sub.columns and sub[date_col_for_filter].notna().any():
                g = sub.dropna(subset=[date_col_for_filter]).groupby(date_col_for_filter, as_index=False)["val"].mean()
                return float(g["val"].mean()) if not g.empty else None

            return float(sub["val"].mean()) if not sub["val"].empty else None

        val_topic_min = _min_of_ip_metric(f, "F_Total")
        val_topic_avg = _mean_like_rating(f, "F_score")

        base_T = mean_of_ip_episode_mean(base, "T시청률")
        base_H = mean_of_ip_episode_mean(base, "H시청률")
        base_live = mean_of_ip_episode_sum(base, "시청인구", ["TVING LIVE"])
        base_quick = mean_of_ip_episode_sum(base, "시청인구", ["TVING QUICK"])
        base_vod = mean_of_ip_episode_sum(base, "시청인구", ["TVING VOD"])
        base_buzz = mean_of_ip_sums(base, "언급량")
        base_view = mean_of_ip_sums(base, "조회수")

        # --- 화제성 베이스값 (페이지 2 전용) ---
        def _series_ip_metric(base_df: pd.DataFrame, metric_name: str, mode: str = "mean", media: List[str] | None = None):
            
            if metric_name == "조회수":
                sub = _get_view_data(base_df) # [3. 공통 함수]
            else:
                sub = _metric_filter(base_df, metric_name).copy()

            if media is not None:
                sub = sub[sub["매체"].isin(media)]
            if sub.empty:
                return pd.Series(dtype=float)

            ep_col = _episode_col(sub) # [5. 공통 함수]
            sub = sub.dropna(subset=[ep_col])
            if sub.empty: 
                return pd.Series(dtype=float)

            sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
            sub = sub.dropna(subset=["value"])
            if sub.empty:
                return pd.Series(dtype=float)

            if mode == "mean":
                ep_mean = sub.groupby(["IP", ep_col], as_index=False)["value"].mean()
                s = ep_mean.groupby("IP")["value"].mean()
            elif mode == "sum":
                s = sub.groupby("IP")["value"].sum()
            elif mode == "ep_sum_mean":
                ep_sum = sub.groupby(["IP", ep_col], as_index=False)["value"].sum()
                s = ep_sum.groupby("IP")["value"].mean()
            elif mode == "min":
                s = sub.groupby("IP")["value"].min()
            else:
                s = sub.groupby("IP")["value"].mean() # mode="mean"의 폴백
                
            return pd.to_numeric(s, errors="coerce").dropna()

        base_topic_min_series = _series_ip_metric(base, "F_Total", mode="min")
        base_topic_min = float(base_topic_min_series.mean()) if not base_topic_min_series.empty else None
        base_topic_avg = _mean_like_rating(base, "F_score")

        # --- 랭킹 계산 유틸 (페이지 2 전용) ---
        def _rank_within_program(
            base_df: pd.DataFrame, metric_name: str, ip_name: str, value: float,
            mode: str = "mean", media: List[str] | None = None, low_is_good: bool = False
        ):
            s = _series_ip_metric(base_df, metric_name, mode=mode, media=media)
            if s.empty or value is None or pd.isna(value):
                return (None, 0)
            if ip_name not in s.index:
                if low_is_good:
                    r = int((s < value).sum() + 1)
                else:
                    r = int((s > value).sum() + 1)
                return (r, int(s.shape[0]))
            
            s = s.dropna()
            if ip_name not in s.index:
                return (None, int(s.shape[0]))
                
            ranks = s.rank(method="min", ascending=low_is_good)
            r = int(ranks.loc[ip_name])
            return (r, int(s.shape[0]))

        rk_T     = _rank_within_program(base, "T시청률", ip_selected, val_T,   mode="mean",        media=None)
        rk_H     = _rank_within_program(base, "H시청률", ip_selected, val_H,   mode="mean",        media=None)
        rk_live  = _rank_within_program(base, "시청인구", ip_selected, val_live,  mode="ep_sum_mean", media=["TVING LIVE"])
        rk_quick = _rank_within_program(base, "시청인구", ip_selected, val_quick, mode="ep_sum_mean", media=["TVING QUICK"])
        rk_vod   = _rank_within_program(base, "시청인구", ip_selected, val_vod,   mode="ep_sum_mean", media=["TVING VOD"])
        rk_buzz  = _rank_within_program(base, "언급량",   ip_selected, val_buzz,  mode="sum",        media=None)
        rk_view  = _rank_within_program(base, "조회수",   ip_selected, val_view,  mode="sum",        media=None)
        rk_fmin  = _rank_within_program(base, "F_Total",  ip_selected, val_topic_min, mode="min",   media=None, low_is_good=True)
        rk_fscr  = _rank_within_program(base, "F_score",  ip_selected, val_topic_avg, mode="mean",  media=None, low_is_good=False)

        # --- KPI 렌더 유틸 (페이지 2 전용) ---
        def _pct_color(val, base_val):
            if val is None or pd.isna(val) or base_val in (None, 0) or pd.isna(base_val):
                return "#888"
            pct = (val / base_val) * 100
            return "#d93636" if pct > 100 else ("#2a61cc" if pct < 100 else "#444")

        def sublines_html(prog_label: str, rank_tuple: tuple, val, base_val):
            rnk, total = rank_tuple if rank_tuple else (None, 0)
            rank_label = f"{rnk}위" if (rnk is not None and total > 0) else "–위"
            pct_txt = "–"; col = "#888"
            try:
                if (val is not None) and (base_val not in (None, 0)) and (not (pd.isna(val) or pd.isna(base_val))):
                    pct = (float(val) / float(base_val)) * 100.0
                    pct_txt = f"{pct:.0f}%"; col = _pct_color(val, base_val)
            except Exception:
                pct_txt = "–"; col = "#888"
            return (
                "<div class='kpi-subwrap'>"
                "<span class='kpi-sublabel'>그룹 內</span> "
                f"<span class='kpi-substrong'>{rank_label}</span><br/>"
                "<span class='kpi-sublabel'>그룹 평균比</span> "
                f"<span class='kpi-subpct' style='color:{col};'>{pct_txt}</span>"
                "</div>"
            )

        def sublines_dummy():
            return (
                "<div class='kpi-subwrap' style='visibility:hidden;'>"
                "<span class='kpi-sublabel'>_</span> <span class='kpi-substrong'>_</span><br/>"
                "<span class='kpi-sublabel'>_</span> <span class='kpi-subpct'>_</span>"
                "</div>"
            )

        def kpi_with_rank(col, title, value, base_val, rank_tuple, prog_label,
                          intlike=False, digits=3, value_suffix:str=""):
            with col:
                main_val = fmt(value, digits=digits, intlike=intlike) # [3. 공통 함수]
                main = f"{main_val}{value_suffix}"
                st.markdown(
                    f"<div class='kpi-card'>"
                    f"<div class='kpi-title'>{title}</div>"
                    f"<div class='kpi-value'>{main}</div>"
                    f"{sublines_html(prog_label, rank_tuple, value, base_val)}"
                    f"</div>",
                    unsafe_allow_html=True
                )

        def kpi_dummy(col):
            with col:
                st.markdown(
                    "<div class='kpi-card'>"
                    "<div class='kpi-title' style='visibility:hidden;'>_</div>"
                    "<div class='kpi-value' style='visibility:hidden;'>_</div>"
                    f"{sublines_dummy()}"
                    "</div>",
                    unsafe_allow_html=True
                )

        # === KPI 배치 ===
        r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
        kpi_with_rank(r1c1, "🎯 타깃시청률",    val_T,   base_T,   rk_T,     prog_label, intlike=False, digits=3)
        kpi_with_rank(r1c2, "🏠 가구시청률",    val_H,   base_H,   rk_H,     prog_label, intlike=False, digits=3)
        kpi_with_rank(r1c3, "📺 TVING LIVE",     val_live,  base_live,  rk_live,  prog_label, intlike=True)
        kpi_with_rank(r1c4, "⚡ TVING QUICK",    val_quick, base_quick, rk_quick, prog_label, intlike=True)
        kpi_with_rank(r1c5, "▶️ TVING VOD",      val_vod,   base_vod,   rk_vod,   prog_label, intlike=True)

        r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
        kpi_with_rank(r2c1, "💬 총 언급량",     val_buzz,  base_buzz,  rk_buzz,  prog_label, intlike=True)
        kpi_with_rank(r2c2, "👀 디지털 조회수", val_view,  base_view,  rk_view,  prog_label, intlike=True)

        with r2c3:
            v = val_topic_min
            main_val = "–" if (v is None or pd.isna(v)) else f"{int(round(v)):,d}위"
            st.markdown(
                "<div class='kpi-card'>"
                "<div class='kpi-title'>🏆 최고 화제성 순위</div>"
                f"<div class='kpi-value'>{main_val}</div>"
                f"{sublines_dummy()}"
                "</div>",
                unsafe_allow_html=True
            )

        kpi_with_rank(r2c4, "🔥 화제성 점수",     val_topic_avg, base_topic_avg, rk_fscr,
                      prog_label, intlike=True)

        kpi_dummy(r2c5)

        st.divider()

        # --- 공통 그래프 크기/설정 ---
        chart_h = 260
        common_cfg = {"scrollZoom": False, "staticPlot": False, "displayModeBar": False}

        # === [Row1] 시청률 추이 | 티빙추이 ===
        cA, cB = st.columns(2)
        with cA:
            st.markdown("<div class='sec-title'>📈 시청률 추이 (회차별)</div>", unsafe_allow_html=True)
            rsub = f[f["metric"].isin(["T시청률", "H시청률"])].dropna(subset=["회차", "회차_num"]).copy()
            rsub = rsub.sort_values("회차_num")
            if not rsub.empty:
                ep_order = rsub[["회차", "회차_num"]].drop_duplicates().sort_values("회차_num")["회차"].tolist()
                t_series = rsub[rsub["metric"] == "T시청률"].groupby("회차", as_index=False)["value"].mean()
                h_series = rsub[rsub["metric"] == "H시청률"].groupby("회차", as_index=False)["value"].mean()
                ymax = pd.concat([t_series["value"], h_series["value"]]).max()
                y_upper = float(ymax) * 1.4 if pd.notna(ymax) else None

                fig_rate = go.Figure()
                fig_rate.add_trace(go.Scatter(
                    x=h_series["회차"], y=h_series["value"],
                    mode="lines+markers+text", name="가구시청률",
                    text=[f"{v:.2f}" for v in h_series["value"]], textposition="top center"
                ))
                fig_rate.add_trace(go.Scatter(
                    x=t_series["회차"], y=t_series["value"],
                    mode="lines+markers+text", name="타깃시청률",
                    text=[f"{v:.2f}" for v in t_series["value"]], textposition="top center"
                ))
                fig_rate.update_xaxes(categoryorder="array", categoryarray=ep_order, title=None, fixedrange=True)
                fig_rate.update_yaxes(title=None, fixedrange=True, range=[0, y_upper] if (y_upper and y_upper > 0) else None)
                fig_rate.update_layout(legend_title=None, height=chart_h, margin=dict(l=8, r=8, t=10, b=8))
                st.plotly_chart(fig_rate, use_container_width=True, config=common_cfg)
            else:
                st.info("표시할 시청률 데이터가 없습니다.")

        with cB:
            st.markdown("<div class='sec-title'>📊 TVING 시청자 추이 (회차별)</div>", unsafe_allow_html=True)
            t_keep = ["TVING LIVE", "TVING QUICK", "TVING VOD"]
            tsub = f[(f["metric"] == "시청인구") & (f["매체"].isin(t_keep))].dropna(subset=["회차", "회차_num"]).copy()
            tsub = tsub.sort_values("회차_num")
            if not tsub.empty:
                ep_order = tsub[["회차", "회차_num"]].drop_duplicates().sort_values("회차_num")["회차"].tolist()
                pvt = tsub.pivot_table(index="회차", columns="매체", values="value", aggfunc="sum").fillna(0)
                pvt = pvt.reindex(ep_order)

                fig_tving = go.Figure()
                for col in [c for c in ["TVING LIVE", "TVING QUICK", "TVING VOD"] if c in pvt.columns]:
                    fig_tving.add_trace(go.Bar(name=col, x=pvt.index, y=pvt[col], text=None))
                fig_tving.update_layout(
                    barmode="stack", legend_title=None,
                    bargap=0.15, bargroupgap=0.05,
                    height=chart_h, margin=dict(l=8, r=8, t=10, b=8)
                )
                fig_tving.update_xaxes(categoryorder="array", categoryarray=ep_order, title=None, fixedrange=True)
                fig_tving.update_yaxes(title=None, fixedrange=True)
                st.plotly_chart(fig_tving, use_container_width=True, config=common_cfg)
            else:
                st.info("표시할 TVING 시청자 데이터가 없습니다.")

        # === [Row2] 디지털조회수 | 디지털언급량 ===
        cC, cD = st.columns(2)
        with cC:
            st.markdown("<div class='sec-title'>▶ 디지털 조회수</div>", unsafe_allow_html=True)
            dview = _get_view_data(f) # [3. 공통 함수] (피드백 3번)
            if not dview.empty:
                if has_week_col and dview["주차"].notna().any():
                    order = (dview[["주차", "주차_num"]].dropna().drop_duplicates().sort_values("주차_num")["주차"].tolist())
                    pvt = dview.pivot_table(index="주차", columns="매체", values="value", aggfunc="sum").fillna(0)
                    pvt = pvt.reindex(order)
                    x_vals = pvt.index.tolist(); use_category = True
                else:
                    pvt = (dview.pivot_table(index="주차시작일", columns="매체", values="value", aggfunc="sum")
                           .sort_index().fillna(0))
                    x_vals = pvt.index.tolist(); use_category = False

                fig_view = go.Figure()
                for col in pvt.columns:
                    fig_view.add_trace(go.Bar(name=col, x=x_vals, y=pvt[col], text=None))
                fig_view.update_layout(
                    barmode="stack", legend_title=None,
                    bargap=0.15, bargroupgap=0.05,
                    height=chart_h, margin=dict(l=8, r=8, t=10, b=8)
                )
                if use_category:
                    fig_view.update_xaxes(categoryorder="array", categoryarray=x_vals, title=None, fixedrange=True)
                else:
                    fig_view.update_xaxes(title=None, fixedrange=True)
                fig_view.update_yaxes(title=None, fixedrange=True)
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
                    pvt = (dbuzz.pivot_table(index="주차시작일", columns="매체", values="value", aggfunc="sum")
                           .sort_index().fillna(0))
                    x_vals = pvt.index.tolist(); use_category = False

                fig_buzz = go.Figure()
                for col in pvt.columns:
                    fig_buzz.add_trace(go.Bar(name=col, x=x_vals, y=pvt[col], text=None))
                fig_buzz.update_layout(
                    barmode="stack", legend_title=None,
                    bargap=0.15, bargroupgap=0.05,
                    height=chart_h, margin=dict(l=8, r=8, t=10, b=8)
                )
                if use_category:
                    fig_buzz.update_xaxes(categoryorder="array", categoryarray=x_vals, title=None, fixedrange=True)
                else:
                    fig_buzz.update_xaxes(title=None, fixedrange=True)
                fig_buzz.update_yaxes(title=None, fixedrange=True)
                st.plotly_chart(fig_buzz, use_container_width=True, config=common_cfg)
            else:
                st.info("표시할 언급량 데이터가 없습니다.")

        # === [Row3] 화제성  ===
        cE, cF = st.columns(2)
        with cE:
            st.markdown("<div class='sec-title'>🔥 화제성 지수</div>", unsafe_allow_html=True)
            fdx = _metric_filter(f, "F_Total").copy()
            if not fdx.empty:
                fdx["순위"] = pd.to_numeric(fdx["value"], errors="coerce").round().astype("Int64")

                if has_week_col and fdx["주차"].notna().any():
                    order = (
                        fdx[["주차", "주차_num"]].dropna()
                        .drop_duplicates()
                        .sort_values("주차_num")["주차"].tolist()
                    )
                    s = fdx.groupby("주차", as_index=True)["순위"].min().reindex(order).dropna()
                    x_vals = s.index.tolist(); use_category = True
                else:
                    s = fdx.set_index("주차시작일")["순위"].sort_index().dropna()
                    x_vals = s.index.tolist(); use_category = False
                
                if not s.empty:
                    y_min, y_max = 0.5, 10
                    labels = [f"{int(v)}위" for v in s.values]
                    text_positions = ["bottom center" if (v <= 1.5) else "top center" for v in s.values]

                    fig_fx = go.Figure()
                    fig_fx.add_trace(go.Scatter(
                        x=x_vals, y=s.values,
                        mode="lines+markers+text", name="화제성 순위",
                        text=labels, textposition=text_positions,
                        textfont=dict(size=12, color="#111"),
                        cliponaxis=False, marker=dict(size=8)
                    ))
                    fig_fx.update_yaxes(autorange=False, range=[y_max, y_min], dtick=1,
                                        title=None, fixedrange=True)
                    if use_category:
                        fig_fx.update_xaxes(categoryorder="array", categoryarray=x_vals,
                                            title=None, fixedrange=True)
                    else:
                        fig_fx.update_xaxes(title=None, fixedrange=True)
                    fig_fx.update_layout(legend_title=None, height=chart_h,
                                         margin=dict(l=8, r=8, t=10, b=8))
                    st.plotly_chart(fig_fx, use_container_width=True, config=common_cfg)
                else:
                    st.info("표시할 화제성 지수 데이터가 없습니다.")
            else:
                st.info("표시할 화제성 지수 데이터가 없습니다.")

        with cF:
            st.markdown("<div class='sec-title'>🔥 화제성 점수</div>", unsafe_allow_html=True)
            fs = _metric_filter(f, "F_score").copy()
            if not fs.empty:
                fs["val"] = pd.to_numeric(fs["value"], errors="coerce")
                fs = fs.dropna(subset=["val"])
                if not fs.empty:
                    order = (
                        f[["주차", "주차_num"]]
                        .dropna()
                        .drop_duplicates()
                        .sort_values("주차_num")["주차"]
                        .tolist()
                    )
                    fs_week = fs.dropna(subset=["주차"]).groupby("주차", as_index=True)["val"].mean()
                    fs_plot = fs_week.reindex(order).dropna()
                    
                    if not fs_plot.empty:
                        x_vals = fs_plot.index.tolist()
                        fig_fscore = go.Figure()
                        fig_fscore.add_trace(go.Scatter(
                            x=x_vals, y=fs_plot.values,
                            mode="lines", 
                            name="화제성 점수", 
                            line_shape="spline"
                        ))
                        fig_fscore.update_xaxes(categoryorder="array", categoryarray=x_vals, title=None, fixedrange=True)
                        fig_fscore.update_yaxes(title=None, fixedrange=True)
                        fig_fscore.update_layout(legend_title=None, height=chart_h, margin=dict(l=8, r=8, t=10, b=8))
                        st.plotly_chart(fig_fscore, use_container_width=True, config=common_cfg)
                    else:
                        st.info("표시할 화제성 점수(F_score) 데이터가 없습니다.")
                else:
                    st.info("표시할 화제성 점수(F_score) 데이터가 없습니다.")
            else:
                st.info("표시할 화제성 점수(F_score) 데이터가 없습니다.")


        # === [Row4] TV/TVING 데모분포  ===
        cG, cH = st.columns(2)

        tv_demo = f[(f["매체"] == "TV") & (f["metric"] == "시청인구") & f["데모"].notna()].copy()
        render_gender_pyramid(cG, "🎯 TV 데모 분포", tv_demo, height=260) # [6. 공통 함수]

        t_keep = ["TVING LIVE", "TVING QUICK", "TVING VOD"]
        tving_demo = f[(f["매체"].isin(t_keep)) & (f["metric"] == "시청인구") & f["데모"].notna()].copy()
        render_gender_pyramid(cH, "📺 TVING 데모 분포", tving_demo, height=260) # [6. 공통 함수]

        st.divider()

        # === [Row5] 데모분석 상세 표 (AgGrid) ===
        st.markdown("#### 👥 데모분석 상세 표")

        # --- [페이지 2]용 데모 테이블 빌더 ---
        def _build_demo_table_numeric(df_src: pd.DataFrame, medias: List[str]) -> pd.DataFrame:
            sub = df_src[
                (df_src["metric"] == "시청인구") &
                (df_src["데모"].notna()) &
                (df_src["매체"].isin(medias))
            ].copy()
            if sub.empty:
                return pd.DataFrame(columns=["회차"] + DEMO_COLS_ORDER)

            sub["성별"] = sub["데모"].apply(_gender_from_demo) # [6. 공통 함수]
            sub["연령대_대"] = sub["데모"].apply(_decade_label_clamped) # [6. 공통 함수]
            sub = sub[sub["성별"].isin(["남", "여"]) & sub["연령대_대"].notna()].copy()
            
            if "회차_num" not in sub.columns: 
                sub["회차_num"] = sub["회차"].str.extract(r"(\d+)", expand=False).astype(float)

            sub = sub.dropna(subset=["회차_num"])
            sub["회차_num"] = sub["회차_num"].astype(int)
            sub["라벨"] = sub.apply(lambda r: f"{r['연령대_대']}{'남성' if r['성별']=='남' else '여성'}", axis=1)

            pvt = sub.pivot_table(index="회차_num", columns="라벨", values="value", aggfunc="sum").fillna(0)

            for c in DEMO_COLS_ORDER: # [2.1. 공통 상수]
                if c not in pvt.columns:
                    pvt[c] = 0
            pvt = pvt[DEMO_COLS_ORDER].sort_index()
            pvt.insert(0, "회차", pvt.index.map(_fmt_ep)) # [6. 공통 함수]
            return pvt.reset_index(drop=True)

        # --- [페이지 2]용 AgGrid 렌더러 ---
        diff_renderer = JsCode("""
        function(params){
          const api = params.api;
          const colId = params.column.getColId();
          const rowIndex = params.node.rowIndex;
          const val = Number(params.value || 0);
          if (colId === "회차") return params.value;

          let arrow = "";
          if (rowIndex > 0) {
            const prev = api.getDisplayedRowAtIndex(rowIndex - 1);
            if (prev && prev.data && prev.data[colId] != null) {
              const pv = Number(prev.data[colId] || 0);
              if (val > pv) arrow = "🔺";
              else if (val < pv) arrow = "▾";
            }
          }
          const txt = Math.round(val).toLocaleString();
          return arrow + txt;
        }
        """)

        _js_demo_cols = "[" + ",".join([f'"{c}"' for c in DEMO_COLS_ORDER]) + "]"
        cell_style_renderer = JsCode(f"""
        function(params){{
          const field = params.colDef.field;
          if (field === "회차") {{
            return {{'text-align':'left','font-weight':'600','background-color':'#fff'}};
          }}
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
          return {{
            'background-color': bg,
            'text-align': 'right',
            'padding': '2px 4px',
            'font-weight': '500'
          }};
        }}
        """)

        def _render_aggrid_table(df_numeric: pd.DataFrame, title: str, height: int = 320):
            st.markdown(f"###### {title}")
            if df_numeric.empty:
                st.info("표시할 데이터가 없습니다.")
                return

            gb = GridOptionsBuilder.from_dataframe(df_numeric)
            gb.configure_grid_options(rowHeight=34, suppressMenuHide=True, domLayout='normal')
            gb.configure_default_column(
                sortable=False, resizable=True, filter=False,
                cellStyle={'textAlign': 'right'}, headerClass='centered-header bold-header'
            )
            gb.configure_column("회차", header_name="회차", cellStyle={'textAlign': 'left'})

            for c in [col for col in df_numeric.columns if col != "회차"]:
                gb.configure_column(
                    c,
                    header_name=c,
                    cellRenderer=diff_renderer,
                    cellStyle=cell_style_renderer
                )
            grid_options = gb.build()
            AgGrid(
                df_numeric,
                gridOptions=grid_options,
                theme="streamlit",
                height=height,
                fit_columns_on_grid_load=True,
                update_mode=GridUpdateMode.NO_UPDATE,
                allow_unsafe_jscode=True
            )

        tv_numeric = _build_demo_table_numeric(f, ["TV"])
        _render_aggrid_table(tv_numeric, "📺 TV (시청자수)")

        tving_numeric = _build_demo_table_numeric(f, ["TVING LIVE", "TVING QUICK", "TVING VOD"])
        _render_aggrid_table(tving_numeric, "▶︎ TVING 합산 (LIVE/QUICK/VOD) 시청자수")

    # ===== [신규] 탭 2, 3...: 임베딩된 G-Sheet =====
    # [수정] st.tab()으로 생성된 위젯과 정보를 순회
    for tab_data in sheet_tabs_info:
        tab_widget = tab_data["widget"]
        tab_info = tab_data["info"]
        
        with tab_widget:
            
            # [신규] 탭 서브 타이틀 (B열 이름)
            st.markdown(f"### {tab_info['title']}")
            
            # [수정] 4. 캡션 텍스트 및 hr 제거
            # st.caption(f"이 탭은 '방영중' 시트(D열)에 등록된 '웹에 게시' URL을 기반으로 생성되었습니다.")
            # st.markdown("---")
            
            # [수정] render_published_url 함수 사용
            render_published_url(tab_info["url"]) # [ 3. 공통 함수 ]

#endregion


#region [ 8. 메인 실행 ]
# =====================================================
# [수정] 관리자 모드 및 selected_ip_url 세션 스테이트 제거

# --- 1. 세션 스테이트 초기화 ---
if "selected_ip" not in st.session_state:
    st.session_state.selected_ip = None # 사이드바에서 선택한 IP

# --- 2. 사이드바 타이틀 렌더링 ---
# (스크립트 상단 Region 1-1 에서 자동으로 실행됨)

# --- 3. '방영중' 데이터 로드 (A, B, C, D열 처리) ---
# [수정] API로 GID를 찾아 최종 URL 맵을 생성하는 메인 함수 호출
on_air_data = load_processed_on_air_data() # [ 3. 공통 함수 ]

# --- 4. 사이드바 네비게이션 렌더링 ---
# [수정] 딕셔너리의 Key 리스트(고유 IP 목록)만 전달
render_sidebar_navigation(list(on_air_data.keys())) # [ 4. 사이드바 ... ] 함수 호출

# --- 5. 메인 페이지 렌더링 ---
current_selected_ip = st.session_state.get("selected_ip", None)

if current_selected_ip:
    # 선택된 IP가 있으면 해당 IP의 상세 페이지를 렌더링
    # [수정] 선택된 IP와 '방영중' 탭 전체 데이터를 전달
    render_ip_detail(current_selected_ip, on_air_data) # [ 7. 페이지 2 ... ] 함수 호출
else:
    # 선택된 IP가 없으면 안내 메시지 표시 (e.g. '방영중' 탭이 비어있을 경우)
    st.markdown("## 📈 IP 성과 자세히보기")
    st.error("오류: '방영중' 시트(A열)에 IP가 없습니다. 구글 시트를 확인하세요.")
    
#endregion









