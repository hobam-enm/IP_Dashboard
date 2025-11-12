# 📈 IP 성과 자세히보기 — Standalone v2.0 (no-hover-lift)
# 모든 '들썩임(hover-lift)' 효과 CSS를 제거한 버전

#region [ 1. 라이브러리 임포트 ]
# =====================================================
import re
from typing import List, Dict, Any, Optional 
import time
import numpy as np
import pandas as pd
from plotly import graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

import gspread
from google.oauth2.service_account import Credentials
#endregion


#region [ 1-0. 페이지 설정 — 반드시 첫 번째 Streamlit 명령 ]
# =====================================================
st.set_page_config(
    page_title="시청자 반응 브리핑",
    layout="wide",
    initial_sidebar_state="expanded"
)
#endregion


#region [ 1-1. 사이드바 타이틀 ]
# =====================================================
def _rerun():
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
#endregion


#region [ 2. 공통 스타일 (들썩임 효과 전부 제거) ]
# =====================================================
st.markdown("""
<style>
/* 타이틀 */
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

/* 앱 배경 */
[data-testid="stAppViewContainer"] {
    background: #f7f8fb;
}

/* wrapper 기본 카드 스타일 (hover 변형 없음) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff;
    border: 1px solid #e9e9e9;
    border-radius: 10px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    padding: 1.25rem 1.25rem 1.5rem 1.25rem;
    margin-bottom: 1.5rem;
}

/* KPI/타이틀/필터는 배경/테두리 제거 */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-card),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-episode-card),
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

/* 사이드바 */
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
.page-title-wrap{ display:flex; align-items:center; gap:8px; margin:4px 0 10px 0; }
.page-title-emoji{ font-size:20px; line-height:1; }
.page-title-main{
  font-size: clamp(18px, 2.2vw, 24px);
  font-weight: 800; letter-spacing:-0.2px; line-height:1.15;
  background: linear-gradient(90deg,#6A5ACD 0%, #A663CC 40%, #FF7A8A 75%, #FF8A3D 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;
}
section[data-testid="stSidebar"] .page-title-wrap{justify-content:center;text-align:center;}
section[data-testid="stSidebar"] .page-title-main{display:block;text-align:center;}

/* 사이드바 내부 카드 제거 */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin-bottom: 0 !important;
}

/* KPI 기본 카드 */
.kpi-card {
  background: #ffffff;
  border: 1px solid #e9e9e9;
  border-radius: 10px;
  padding: 20px 15px;
  text-align: center;
  box-shadow: 0 2px 5px rgba(0,0,0,0.03);
  height: 100%;
  display: flex; flex-direction: column; justify-content: center;
}
.kpi-title { 
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 10px; 
    color: #333;
    display:flex; align-items:center; justify-content:center;
    text-align:center; line-height:1.3;
}
.kpi-value { 
    font-size: 28px; 
    font-weight: 800; 
    color: #000; 
    line-height: 1.2;
    text-align:center;
}
.kpi-subwrap { margin-top: 10px; line-height: 1.4; text-align:center; }
.kpi-sublabel { font-size: 12px; font-weight: 500; color: #555; letter-spacing: 0.1px; margin-right: 6px; }
.kpi-subpct { font-size: 14px; font-weight: 700; }

/* 섹션 타이틀 */
.sec-title{ 
    font-size: 20px; 
    font-weight: 700; 
    color: #111; 
    margin: 0 0 10px 0;
}

/* AgGrid */
.ag-theme-streamlit { font-size: 13px; }
.ag-theme-streamlit .ag-root-wrapper { border-radius: 8px; }
.ag-theme-streamlit .ag-header-cell-label { justify-content: center !important; }

</style>
""", unsafe_allow_html=True)
#endregion


#region [ 3. 공통 함수: 데이터 로드 / 유틸리티 ]
# =====================================================
@st.cache_resource(ttl=600)
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"GSpread 인증 실패: {e}")
        return None

@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    client = get_gspread_client()
    if client is None:
        return pd.DataFrame()
    try:
        sheet_id = st.secrets["SHEET_ID"]
        worksheet_name = st.secrets["SHEET_NAME"]
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

    if "주차시작일" in df.columns:
        df["주차시작일"] = pd.to_datetime(df["주차시작일"].astype(str).str.strip(), format="%Y. %m. %d", errors="coerce")
    if "방영시작일" in df.columns:
        df["방영시작일"] = pd.to_datetime(df["방영시작일"].astype(str).str.strip(), format="%Y. %m. %d", errors="coerce")
    if "value" in df.columns:
        v = df["value"].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False)
        df["value"] = pd.to_numeric(v, errors="coerce").fillna(0)
    for c in ["IP", "편성", "지표구분", "매체", "데모", "metric", "회차", "주차"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
    if "회차" in df.columns:
        df["회차_numeric"] = df["회차"].str.extract(r"(\\d+)", expand=False).astype(float)
    else:
        df["회차_numeric"] = pd.NA
    return df

@st.cache_data(ttl=600)
def get_tab_gids_from_sheet(edit_url: str) -> Dict[str, int]:
    client = get_gspread_client()
    if client is None: 
        return {}
    try:
        spreadsheet = client.open_by_url(edit_url)
        return {ws.title.strip(): ws.id for ws in spreadsheet.worksheets()}
    except Exception:
        return {}

@st.cache_data(ttl=600)
def load_processed_on_air_data() -> Dict[str, List[Dict[str, str]]]:
    worksheet_name = "방영중"
    client = get_gspread_client()
    if client is None:
        return {}
    try:
        sheet_id = st.secrets["SHEET_ID"]
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        values = worksheet.get_values('A2:D') 
        config_map = {}
        for row in values:
            if row and len(row) > 3 and row[0].strip() and row[1].strip() and row[2].strip() and row[3].strip():
                ip, tab_name, edit_url, pub_url = [s.strip() for s in row]
                if ip not in config_map:
                    config_map[ip] = {
                        "edit_url": edit_url,
                        "publish_url_base": pub_url.split('?')[0],
                        "tabs_to_process": []
                    }
                config_map[ip]["tabs_to_process"].append(tab_name)

        final_data_structure = {}
        for ip, config in config_map.items():
            final_data_structure[ip] = []
            gid_map = get_tab_gids_from_sheet(config["edit_url"])
            if not gid_map:
                continue
            for tab_name in config["tabs_to_process"]:
                gid = gid_map.get(tab_name.strip())
                if gid is not None:
                    final_url = f"{config['publish_url_base']}?gid={gid}&single=true"
                    if "사전 반응" in tab_name:
                        final_data_structure[ip].insert(0, {"title": tab_name, "url": final_url})
                    else:
                        final_data_structure[ip].append({"title": tab_name, "url": final_url})
        return final_data_structure
    except Exception:
        return {}

def fmt(v, digits=3, intlike=False):
    if v is None or pd.isna(v):
        return "–"
    return f"{v:,.0f}" if intlike else f"{v:.{digits}f}"

def render_published_url(published_url: str):
    st.markdown(f"""
        <iframe src="{published_url}" style="width: 100%; height: 700px; border: 1px solid #e0e0e0; border-radius: 8px;"></iframe>
        """, unsafe_allow_html=True)

def _get_view_data(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["metric"] == "조회수"].copy()
    if sub.empty:
        return sub
    if "매체" in sub.columns and "세부속성1" in sub.columns:
        yt_mask = (sub["매체"] == "유튜브")
        attr_mask = sub["세부속성1"].isin(["PGC", "UGC"])
        sub = sub[~yt_mask | (yt_mask & attr_mask)]
    return sub
#endregion


#region [ 4. 사이드바 - 네비게이션 ]
# =====================================================
def render_sidebar_navigation(on_air_ips: List[str]):
    st.sidebar.markdown("---")
    st.sidebar.markdown("######  NAVIGATING")

    current_selected_ip = st.session_state.get("selected_ip", None)

    if not on_air_ips:
        st.sidebar.warning("'방영중' 탭(A열)에 IP가 없습니다.")
        st.session_state.selected_ip = None
        st.sidebar.divider()
        if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True, key="btn_refresh_bottom"):
            try: st.cache_data.clear()
            except Exception: pass
            try: st.cache_resource.clear()
            except Exception: pass
            st.session_state["__last_refresh_ts__"] = int(time.time())
            _rerun()
        return

    if current_selected_ip is None or current_selected_ip not in on_air_ips:
        st.session_state.selected_ip = on_air_ips[0]
        current_selected_ip = on_air_ips[0]

    for ip_name in on_air_ips:
        is_active = (current_selected_ip == ip_name)
        clicked = st.sidebar.button(
            ip_name,
            key=f"navbtn__{ip_name}",
            use_container_width=True,
            type=("primary" if is_active else "secondary")
        )
        if clicked and not is_active:
            st.session_state.selected_ip = ip_name
            try:
                st.query_params.update(ip=ip_name)
            except AttributeError:
                st.experimental_set_query_params(ip=ip_name)
            _rerun()

    st.sidebar.divider()
    if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True, key="btn_refresh_bottom_ok"):
        try: st.cache_data.clear()
        except Exception: pass
        try: st.cache_resource.clear()
        except Exception: pass
        st.session_state["__last_refresh_ts__"] = int(time.time())
        _rerun()

    ts = st.session_state.get("__last_refresh_ts__")
    if ts:
        st.sidebar.caption(f"마지막 갱신: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))}")
#endregion


#region [ 5. 유틸: KPI 계산 ]
# =====================================================
def _normalize_metric(s: str) -> str:
    if s is None: return ""
    return re.sub(r"[^A-Za-z0-9가-힣]+", "", str(s)).lower()

def _metric_filter(df: pd.DataFrame, name: str) -> pd.DataFrame:
    t = _normalize_metric(name)
    df2 = df.copy()
    if "metric_norm" not in df2.columns:
        df2["metric_norm"] = df2["metric"].apply(_normalize_metric)
    return df2[df2["metric_norm"] == t]

def _fmt_ep(n) -> str:
    try:
        return f"{int(n):02d}화"
    except Exception:
        return "–"
#endregion


#region [ 6. 페이지 2: IP 성과 자세히보기 ]
# =====================================================
def render_ip_detail(ip_selected: str, on_air_data: Dict[str, List[Dict[str, str]]]):
    st.markdown(f"<div class='page-title'>📈 {ip_selected} 시청자 반응 브리핑</div>", unsafe_allow_html=True)

    embeddable_tabs = on_air_data.get(ip_selected, [])
    tab_titles = ["📈 성과 자세히보기"]
    if embeddable_tabs:
        tab_titles.append("👥 시청자 반응 브리핑")
        tab_titles.extend([t["title"] for t in embeddable_tabs])
    tabs = st.tabs(tab_titles)
    main_tab = tabs[0]
    dummy_tab = tabs[1] if len(tabs) >= 2 else None
    sheet_tabs_widgets = tabs[2:] if len(tabs) >= 3 else []

    with main_tab:
        filter_cols = st.columns([1, 1])

        with filter_cols[0]:
            selected_group_criteria = st.multiselect(
                "",
                ["동일 편성", "방영 연도"],
                default=[],
                placeholder="비교 기준을 선택하세요 (미선택 시 '전체' 평균)",
                key="ip_detail_group"
            )

        df_full = load_data()
        f = df_full[df_full["IP"] == ip_selected].copy()

        # 회차/주차 보정
        if "회차_numeric" in f.columns:
            f["회차_num"] = pd.to_numeric(f["회차_numeric"], errors="coerce")
        else:
            f["회차_num"] = pd.to_numeric(f["회차"].str.extract(r"(\\d+)", expand=False), errors="coerce")

        def _week_to_num(x: str):
            m = re.search(r"-?\\d+", str(x))
            return int(m.group(0)) if m else None

        has_week_col = "주차" in f.columns
        if has_week_col:
            f["주차_num"] = f["주차"].apply(_week_to_num)

        def _calc_week_from_episode(ep_num):
            try:
                if pd.isna(ep_num): return None
                n = int(ep_num)
                return (n + 1) // 2
            except Exception:
                return None

        if "주차_num" not in f.columns or f["주차_num"].isna().all():
            f["주차_num"] = f["회차_num"].apply(_calc_week_from_episode)
            f["주차"] = f["주차_num"].apply(lambda x: f"{int(x)}주차" if pd.notna(x) else None)

        # 비교 그룹 기준
        if "방영시작일" in df_full.columns and df_full["방영시작일"].notna().any():
            date_col_for_filter = "방영시작일"
        else:
            date_col_for_filter = "주차시작일"

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

        # 주차 선택 (기본: 가장 높은 주차) — 음수/0 주차 제외
        valid_weeks = (
            f.dropna(subset=["주차_num"])
             .sort_values("주차_num")["주차_num"]
             .drop_duplicates()
             .astype(int)
             .tolist()
        )
        valid_weeks = [w for w in valid_weeks if w > 0]

        default_week_index = max(0, len(valid_weeks) - 1)
        with filter_cols[1]:
            selected_week = st.selectbox(
                label="",
                options=valid_weeks,
                index=default_week_index if valid_weeks else 0,
                format_func=lambda w: f"{w}주차",
                placeholder="주차 선택",
                key="week_selector"
            )

        # 선택 주차의 앞/뒤 회차
        def _week_to_front_back_eps(week: int) -> tuple[Optional[int], Optional[int]]:
            if week is None: return (None, None)
            front, back = 2*week - 1, 2*week
            eps = f.dropna(subset=["회차_num"])["회차_num"].astype(int).unique().tolist()
            return (front if front in eps else None, back if back in eps else None)

        ep_front, ep_back = _week_to_front_back_eps(selected_week)

        # 비교 그룹 집합
        base = df_full.copy()
        group_name_parts = []
        if "동일 편성" in selected_group_criteria and sel_prog:
            base = base[base["편성"] == sel_prog]; group_name_parts.append(f"'{sel_prog}'")
        if "방영 연도" in selected_group_criteria and sel_year:
            base = base[base[date_col_for_filter].dt.year == sel_year]; group_name_parts.append(f"{int(sel_year)}년")
        if not selected_group_criteria or not group_name_parts:
            base = df_full.copy(); group_name_parts = ["전체"]

        if "회차_numeric" in base.columns:
            base["회차_num"] = pd.to_numeric(base["회차_numeric"], errors="coerce")
        else:
            base["회차_num"] = pd.to_numeric(base["회차"].str.extract(r"(\\d+)", expand=False), errors="coerce")

        # 값 계산
        def _value_rating_ep(df_src: pd.DataFrame, metric_name: str, ep_num: int | None) -> Optional[float]:
            if ep_num is None: return None
            sub = _metric_filter(df_src, metric_name)
            sub = sub[pd.to_numeric(sub["회차_num"], errors="coerce") == ep_num]
            if sub.empty: return None
            vals = pd.to_numeric(sub["value"], errors="coerce").dropna()
            return float(vals.mean()) if not vals.empty else None

        def _value_tving_ep_sum(df_src: pd.DataFrame, ep_num: int | None, include_quick_in_vod: bool = False) -> tuple[Optional[float], Optional[float]]:
            if ep_num is None: return (None, None)
            sub = _metric_filter(df_src, "시청인구")
            sub = sub[pd.to_numeric(sub["회차_num"], errors="coerce") == ep_num].copy()
            if sub.empty: return (None, None)
            sub["val"] = pd.to_numeric(sub["value"], errors="coerce")
            sub = sub.dropna(subset=["val"])

            live = sub[sub["매체"] == "TVING LIVE"]["val"].sum() if "TVING LIVE" in sub["매체"].unique() else 0.0
            vod_only = sub[sub["매체"] == "TVING VOD"]["val"].sum() if "TVING VOD" in sub["매체"].unique() else 0.0
            quick = sub[sub["매체"] == "TVING QUICK"]["val"].sum() if "TVING QUICK" in sub["매체"].unique() else 0.0
            vod = vod_only + (quick if include_quick_in_vod else 0.0)

            live = float(live) if live > 0 else (None if sub.empty else 0.0)
            vod  = float(vod)  if vod  > 0 else (None if sub.empty else 0.0)
            return (live, vod)

        def _base_ep_values_series(df_base: pd.DataFrame, metric_name: str, ep_num: int, media: Optional[List[str]] = None, include_quick_in_vod: bool = False) -> pd.Series:
            sub = df_base.copy()
            sub = sub[pd.to_numeric(sub["회차_num"], errors="coerce") == ep_num]
            if sub.empty: return pd.Series(dtype=float)

            if metric_name in ["T시청률", "H시청률"]:
                sub = _metric_filter(sub, metric_name)
                if sub.empty: return pd.Series(dtype=float)
                sub["val"] = pd.to_numeric(sub["value"], errors="coerce")
                s = sub.groupby("IP")["val"].mean().dropna()
                return s

            sub = _metric_filter(sub, "시청인구")
            if sub.empty: return pd.Series(dtype=float)
            sub["val"] = pd.to_numeric(sub["value"], errors="coerce")

            if media is None:
                media = ["TVING LIVE", "TVING VOD"]
            sub = sub[sub["매체"].isin(set(media + (["TVING QUICK"] if include_quick_in_vod else [])))]

            if include_quick_in_vod:
                def _sum_vod_quick(g):
                    vod = g[g["매체"] == "TVING VOD"]["val"].sum()
                    qk  = g[g["매체"] == "TVING QUICK"]["val"].sum()
                    return vod + qk
                live_series = sub[sub["매체"] == "TVING LIVE"].groupby("IP")["val"].sum()
                vod_series  = sub.groupby(["IP"]).apply(_sum_vod_quick)
                return vod_series if ("TVING VOD" in media and "TVING LIVE" not in media) else live_series
            else:
                s = sub.groupby(["IP"])["val"].sum().dropna()
                return s

        def _base_ep_mean(df_base: pd.DataFrame, metric_name: str, ep_num: int, media: Optional[List[str]] = None, include_quick_in_vod: bool = False) -> Optional[float]:
            s = _base_ep_values_series(df_base, metric_name, ep_num, media, include_quick_in_vod)
            if s.empty: return None
            return float(s.mean())

        def _rank_in_base_ep(df_base: pd.DataFrame, metric_name: str, ep_num: int, my_value: Optional[float],
                             media: Optional[List[str]] = None, include_quick_in_vod: bool = False) -> tuple[Optional[int], int]:
            if my_value is None or pd.isna(my_value):
                s = _base_ep_values_series(df_base, metric_name, ep_num, media, include_quick_in_vod)
                return (None, int(s.size))
            s = _base_ep_values_series(df_base, metric_name, ep_num, media, include_quick_in_vod).sort_values(ascending=False)
            if s.empty: return (None, 0)
            rank = int((s >= my_value).sum())
            return (rank, int(s.size))

        # KPI 회차 래핑 카드 (hover 효과 없음)
        _EP_CARD_STYLE = """
        <style>
        .kpi-episode-card{
            border: 1px solid rgba(0,0,0,.08);
            border-radius: 16px;
            padding: 14px 16px 10px;
            margin: 4px 0 10px;
            background: linear-gradient(180deg, rgba(255,255,255,.95), rgba(250,250,255,.92));
        }
        .kpi-episode-head{
            font-weight: 800; font-size: 28px; letter-spacing: -0.02em; margin-bottom: 8px; text-align:center;
        }
        .kpi-metrics{ display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 10px; }
        .kpi-card.sm{ border:1px solid rgba(0,0,0,.06); border-radius:12px; padding:10px 12px; background:#fff; }
        .kpi-title{
            font-size:16px; color:#333;
            display:flex; align-items:center; justify-content:center; gap:6px;
            text-align:center; line-height:1.3;
        }
        .kpi-title .ep-tag{opacity:.6; font-weight:600;}
        .kpi-value{ font-size:22px; font-weight:800; margin:3px 0 2px; text-align:center; }
        .kpi-subwrap{ font-size:12px; color:#555; text-align:center; }
        .kpi-subwrap .kpi-sublabel{ opacity:.75 }
        .kpi-subwrap .kpi-sep{ opacity:.35; padding:0 6px }
        </style>
        """
        st.markdown(_EP_CARD_STYLE, unsafe_allow_html=True)

        def _pct_color(val, base_val):
            if val is None or pd.isna(val) or base_val in (None, 0) or pd.isna(base_val):
                return "#888"
            pct = (val / base_val) * 100
            return "#d93636" if pct > 100 else ("#2a61cc" if pct < 100 else "#444")

        def sublines_html_ep(base_val, val, rank_tuple: tuple[Optional[int], int]):
            pct_txt = "–"; col = "#888"
            try:
                if (val is not None) and (base_val not in (None, 0)) and (not (pd.isna(val) or pd.isna(base_val))):
                    pct = (float(val) / float(base_val)) * 100.0
                    pct_txt = f"{pct:.0f}%"; col = _pct_color(val, base_val)
            except Exception:
                pct_txt = "–"; col = "#888"

            r_txt = "–위"
            if rank_tuple and rank_tuple[1] > 0 and rank_tuple[0] is not None:
                r_txt = f"{rank_tuple[0]}위 / {rank_tuple[1]}"

            return (
                "<div class='kpi-subwrap'>"
                f"<span class='kpi-sublabel'>그룹 평균比</span> "
                f"<span class='kpi-subpct' style='color:{col};'>{pct_txt}</span>"
                f"<span class='kpi-sep'> · </span>"
                f"<span class='kpi-sublabel'>동일회차 순위</span> "
                f"<span class='kpi-subpct'>{r_txt}</span>"
                "</div>"
            )

        def _kpi_box_html(title: str, value, base_val, ep_label: str, rank_tuple, intlike=False, digits=3, suffix=""):
            main_val = fmt(value, digits=digits, intlike=intlike)
            main = f"{main_val}{suffix}"
            return (
                "<div class='kpi-card sm'>"
                f"<div class='kpi-title'>{title} <span class='ep-tag'>{ep_label}</span></div>"
                f"<div class='kpi-value'>{main}</div>"
                f"{sublines_html_ep(base_val, value, rank_tuple)}"
                "</div>"
            )

        def _render_episode_kpi_row(ep_num: Optional[int]):
            if ep_num is None:
                st.info("선택 주차의 해당 회차 데이터가 없습니다.")
                return
            ep_label = _fmt_ep(ep_num)

            vT  = _value_rating_ep(f, "T시청률", ep_num)
            vH  = _value_rating_ep(f, "H시청률", ep_num)
            vLIVE, vVOD = _value_tving_ep_sum(f, ep_num, include_quick_in_vod=True)

            bT   = _base_ep_mean(base, "T시청률", ep_num)
            bH   = _base_ep_mean(base, "H시청률", ep_num)
            bLIVE = _base_ep_mean(base, "시청인구", ep_num, media=["TVING LIVE"])
            bVOD  = _base_ep_mean(base, "시청인구", ep_num, media=["TVING VOD"], include_quick_in_vod=True)

            rT   = _rank_in_base_ep(base, "T시청률", ep_num, vT)
            rH   = _rank_in_base_ep(base, "H시청률", ep_num, vH)
            rLIVE= _rank_in_base_ep(base, "시청인구", ep_num, vLIVE, media=["TVING LIVE"])
            rVOD = _rank_in_base_ep(base, "시청인구", ep_num, vVOD,  media=["TVING VOD"], include_quick_in_vod=True)

            html = []
            html.append("<div class='kpi-episode-card'>")
            html.append(f"<div class='kpi-episode-head'>{ep_label}</div>")
            html.append("<div class='kpi-metrics'>")
            html.append(_kpi_box_html("🎯 타깃시청률", vT,   bT,   ep_label, rT,   intlike=False, digits=3))
            html.append(_kpi_box_html("🏠 가구시청률", vH,   bH,   ep_label, rH,   intlike=False, digits=3))
            html.append(_kpi_box_html("📺 TVING LIVE", vLIVE, bLIVE, ep_label, rLIVE, intlike=True))
            html.append(_kpi_box_html("▶️ TVING VOD",  vVOD,  bVOD,  ep_label, rVOD,  intlike=True))
            html.append("</div></div>")
            st.markdown("".join(html), unsafe_allow_html=True)

        # KPI: 앞/뒤 회차
        _render_episode_kpi_row(ep_front)
        _render_episode_kpi_row(ep_back)

        st.divider()

        chart_h = 260
        common_cfg = {"scrollZoom": False, "staticPlot": False, "displayModeBar": False}

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

        cC, cD = st.columns(2)
        with cC:
            st.markdown("<div class='sec-title'>▶ 디지털 조회수</div>", unsafe_allow_html=True)
            dview = _get_view_data(f)
            if not dview.empty:
                if has_week_col and dview["주차"].notna().any():
                    order = (dview[["주차", "주차_num"]].dropna().drop_duplicates().sort_values("주차_num")["주차"].tolist())
                    pvt = dview.pivot_table(index="주차", columns="매체", values="value", aggfunc="sum").fillna(0)
                    pvt = pvt.reindex(order); x_vals = pvt.index.tolist(); use_category = True
                else:
                    pvt = (dview.pivot_table(index="주차시작일", columns="매체", values="value", aggfunc="sum")
                           .sort_index().fillna(0))
                    x_vals = pvt.index.tolist(); use_category = False

                fig_view = go.Figure()
                for col in pvt.columns:
                    fig_view.add_trace(go.Bar(name=col, x=x_vals, y=pvt[col], text=None))
                fig_view.update_layout(barmode="stack", legend_title=None, bargap=0.15, bargroupgap=0.05,
                                       height=chart_h, margin=dict(l=8, r=8, t=10, b=8))
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
                    pvt = pvt.reindex(order); x_vals = pvt.index.tolist(); use_category = True
                else:
                    pvt = (dbuzz.pivot_table(index="주차시작일", columns="매체", values="value", aggfunc="sum")
                           .sort_index().fillna(0))
                    x_vals = pvt.index.tolist(); use_category = False

                fig_buzz = go.Figure()
                for col in pvt.columns:
                    fig_buzz.add_trace(go.Bar(name=col, x=x_vals, y=pvt[col], text=None))
                fig_buzz.update_layout(barmode="stack", legend_title=None, bargap=0.15, bargroupgap=0.05,
                                       height=chart_h, margin=dict(l=8, r=8, t=10, b=8))
                if use_category:
                    fig_buzz.update_xaxes(categoryorder="array", categoryarray=x_vals, title=None, fixedrange=True)
                else:
                    fig_buzz.update_xaxes(title=None, fixedrange=True)
                fig_buzz.update_yaxes(title=None, fixedrange=True)
                st.plotly_chart(fig_buzz, use_container_width=True, config=common_cfg)
            else:
                st.info("표시할 언급량 데이터가 없습니다.")

        cE, cF = st.columns(2)
        with cE:
            st.markdown("<div class='sec-title'>🔥 화제성 지수</div>", unsafe_allow_html=True)
            fdx = _metric_filter(f, "FTotal").copy() if "metric_norm" in f.columns else _metric_filter(f, "F_Total").copy()
            if not fdx.empty:
                fdx["순위"] = pd.to_numeric(fdx["value"], errors="coerce").round().astype("Int64")

                order = (f[["주차", "주차_num"]].dropna().drop_duplicates().sort_values("주차_num")["주차"].tolist())
                if "주차" in fdx.columns and fdx["주차"].notna().any():
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
                    order = (f[["주차", "주차_num"]].dropna().drop_duplicates().sort_values("주차_num")["주차"].tolist())
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
                        st.info("표시할 화제성 점수 데이터가 없습니다.")
                else:
                    st.info("표시할 화제성 점수 데이터가 없습니다.")
            else:
                st.info("표시할 화제성 점수 데이터가 없습니다.")

    if dummy_tab:
        with dummy_tab:
            st.info("우측에서 조회를 원하는 회차를 선택해주세요.")

    for tab_widget, tab_info in zip(sheet_tabs_widgets, embeddable_tabs):
        with tab_widget:
            render_published_url(tab_info["url"])
#endregion


#region [ 7. 메인 실행 ]
# =====================================================
if "selected_ip" not in st.session_state:
    st.session_state.selected_ip = None

on_air_data = load_processed_on_air_data()
on_air_ips = list(on_air_data.keys())

try:
    selected_ip_from_url = st.query_params.get("ip", [None])[0]
except AttributeError:
    selected_ip_from_url = st.experimental_get_query_params().get("ip", [None])[0]

if st.session_state.selected_ip is None and selected_ip_from_url and selected_ip_from_url in on_air_ips:
    st.session_state.selected_ip = selected_ip_from_url

render_sidebar_navigation(on_air_ips)

current_selected_ip = st.session_state.get("selected_ip", None)

if current_selected_ip and selected_ip_from_url != current_selected_ip:
    try:
        st.query_params["ip"] = current_selected_ip
    except AttributeError:
        st.experimental_set_query_params(ip=current_selected_ip)

if current_selected_ip:
    render_ip_detail(current_selected_ip, on_air_data)
else:
    st.markdown("## 📈 IP 성과 자세히보기")
    st.error("오류: '방영중' 시트(A열)에 IP가 없습니다. 구글 시트를 확인하세요.")
#endregion
