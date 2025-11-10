
# -*- coding: utf-8 -*-
# 📈 페이지 2 — IP 성과 자세히보기 (Standalone, gspread+ServiceAccount, no fallback)
# 실행: streamlit run ip_detail_page_gspread.py
#
# 🔐 필요한 secrets.toml (예시)
# [sheets]
# SHEET_ID = "<구글 시트 ID>"
# RAW_GID  = "407131354"
#
# # 서비스계정 JSON 통째로 넣기 (권장)
# gcp_service_account = """
# {
#   "type": "...",
#   "project_id": "...",
#   "private_key_id": "...",
#   "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
#   "client_email": "...",
#   "client_id": "...",
#   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#   "client_x509_cert_url": "..."
# }
# """
#
# 또는 딕셔너리형으로
# gcp_service_account = { ... }

import json
import re
import textwrap
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import gspread
from google.oauth2.service_account import Credentials

# =====================================================
# 0) 페이지 설정
# =====================================================
st.set_page_config(
    page_title="IP 성과 자세히보기 — 단일 페이지 (gspread)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# 1) 시크릿 로딩 (원본 방식과 동일: 서비스계정 + 시트ID/GID)
# =====================================================
def _secrets_get(keys, default=None):
    # 루트
    for k in keys:
        if k in st.secrets:
            return st.secrets.get(k)
    # 섹션 'sheets'
    sheets = st.secrets.get("sheets", {})
    if isinstance(sheets, dict):
        for k in keys:
            if k in sheets:
                return sheets.get(k)
    return default

def _load_service_account_info():
    raw = _secrets_get(["gcp_service_account", "service_account", "google_service_account"])
    if raw is None:
        st.error("secrets.toml에 서비스계정 JSON(gcp_service_account) 설정이 필요합니다.")
        st.stop()
    if isinstance(raw, str):
        raw = raw.strip()
        try:
            info = json.loads(raw)
        except json.JSONDecodeError:
            st.error("gcp_service_account 파싱 실패. 문자열이라면 유효한 JSON이어야 합니다.")
            st.stop()
    elif isinstance(raw, dict):
        info = raw
    else:
        st.error("gcp_service_account 형식이 잘못되었습니다. 문자열 JSON 또는 딕셔너리여야 합니다.")
        st.stop()
    return info

def _sheet_ids():
    sid = _secrets_get(["SHEET_ID", "sheet_id", "RAW_SHEET_ID"])
    gid = _secrets_get(["RAW_GID", "gid", "GID"])
    if not sid or not gid:
        st.error("secrets.toml에 [sheets] SHEET_ID 와 RAW_GID 가 필요합니다.")
        st.stop()
    return str(sid).strip(), str(gid).strip()

# =====================================================
# 2) gspread 클라이언트 & DataFrame 로더
# =====================================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

@st.cache_data(ttl=600, show_spinner=True)
def load_raw_dataframe() -> pd.DataFrame:
    sa_info = _load_service_account_info()
    sheet_id, raw_gid = _sheet_ids()

    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    gc = gspread.authorize(creds)

    sh = gc.open_by_key(sheet_id)
    # gid로 워크시트 찾기
    ws = None
    for w in sh.worksheets():
        # gspread Worksheet.id는 정수 gid
        if str(w.id) == str(raw_gid):
            ws = w
            break
    if ws is None:
        st.error(f"Sheet gid={raw_gid} 워크시트를 찾을 수 없습니다.")
        st.stop()

    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()

    header = values[0]
    rows = values[1:]

    # 헤더 정리: 공백이나 빈 헤더, 중복 헤더 방지
    cleaned = []
    seen = {}
    for h in header:
        name = (h or "").strip()
        if not name:
            name = "Unnamed"
        # 중복 처리
        cnt = seen.get(name, 0)
        if cnt > 0:
            newname = f"{name}.{cnt}"
        else:
            newname = name
        seen[name] = cnt + 1
        cleaned.append(newname)

    df = pd.DataFrame(rows, columns=cleaned)

    # 전처리 (원본 컨벤션 유지)
    if "주차시작일" in df.columns:
        df["주차시작일"] = pd.to_datetime(
            df["주차시작일"].astype(str).str.strip(),
            format="%Y. %m. %d",
            errors="coerce",
        )
    if "방영시작일" in df.columns:
        df["방영시작일"] = pd.to_datetime(
            df["방영시작일"].astype(str).str.strip(),
            format="%Y. %m. %d",
            errors="coerce",
        )
    if "value" in df.columns:
        v = df["value"].astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False)
        df["value"] = pd.to_numeric(v, errors="coerce").fillna(0)

    for c in ["IP", "편성", "지표구분", "매체", "데모", "metric", "회차", "주차", "세부속성1"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    if "회차" in df.columns:
        df["회차_numeric"] = df["회차"].str.extract(r"(\d+)", expand=False).astype(float)
    else:
        df["회차_numeric"] = pd.NA

    return df

# =====================================================
# 3) 공통 유틸
# =====================================================
def fmt(v, digits=3, intlike=False):
    if v is None or pd.isna(v):
        return "–"
    return f"{v:,.0f}" if intlike else f"{v:.{digits}f}"

def kpi(col, title, value):
    with col:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">{title}</div>'
            f'<div class="kpi-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

def _episode_col(df: pd.DataFrame) -> str:
    if "회차_numeric" in df.columns: return "회차_numeric"
    if "회차_num"     in df.columns: return "회차_num"
    return "회차"

def _get_view_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    '조회수' metric만 필터링하고, 유튜브 PGC/UGC 규칙을 적용.
    """
    sub = df[df["metric"] == "조회수"].copy()
    if sub.empty:
        return sub
    if "매체" in sub.columns and "세부속성1" in sub.columns:
        yt_mask = (sub["매체"] == "유튜브")
        attr_mask = sub["세부속성1"].isin(["PGC", "UGC"])
        sub = sub[~yt_mask | (yt_mask & attr_mask)]
    return sub

def mean_of_ip_episode_sum(df: pd.DataFrame, metric_name: str, media: Optional[List[str]]=None) -> Optional[float]:
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

def mean_of_ip_episode_mean(df: pd.DataFrame, metric_name: str, media: Optional[List[str]]=None) -> Optional[float]:
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

def mean_of_ip_sums(df: pd.DataFrame, metric_name: str, media: Optional[List[str]]=None) -> Optional[float]:
    if metric_name == "조회수":
        sub = _get_view_data(df)
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

# =====================================================
# 4) 페이지 2 — IP 성과 자세히보기
# =====================================================
def render_ip_detail():
    df_full = load_raw_dataframe()

    # --- 제목/가이드
    filter_cols = st.columns([3, 2, 2])
    with filter_cols[0]:
        st.markdown("<div class='page-title'>📈 IP 성과 자세히보기</div>", unsafe_allow_html=True)
    with st.expander("ℹ️ 지표 기준 안내", expanded=False):
        st.markdown("<div class='gd-guideline'>", unsafe_allow_html=True)
        st.markdown(textwrap.dedent("""
            **지표 기준**
        - **시청률** `회차평균`: 전국 기준 가구 / 타깃(2049) 시청률
        - **티빙 LIVE** `회차평균`: 업데이트 예정
        - **티빙 QUICK** `회차평균`: 방영당일 VOD 시청 UV
        - **티빙 VOD** `회차평균`: 방영일+1부터 +6까지 **6days** VOD UV
        - **디지털 조회/언급량** `회차총합`: 방영주차(월~일) 내 총합
        - **화제성 점수** `회차평균`: 방영기간 주차별 화제성 점수 평균
        """).strip())
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 필터 (IP 단일, 그룹 기준)
    ip_options = sorted(df_full["IP"].dropna().unique().tolist())
    with filter_cols[1]:
        ip_selected = st.selectbox("IP (단일선택)", ip_options, index=0 if ip_options else None,
                                   placeholder="IP 선택", label_visibility="collapsed")
    with filter_cols[2]:
        selected_group_criteria = st.multiselect(
            "비교 그룹 기준", ["동일 편성", "방영 연도"], default=["동일 편성"], label_visibility="collapsed"
        )

    if not ip_selected:
        st.info("IP를 선택하세요.")
        return

    # --- 기준 IP/그룹 정보
    df_ip = df_full[df_full["IP"] == ip_selected].copy()
    if df_ip.empty:
        st.warning("선택한 IP의 데이터가 없습니다.")
        return

    sel_prog = df_ip["편성"].dropna().mode().iloc[0] if not df_ip["편성"].dropna().empty else None
    date_col_for_filter = "방영시작일" if "방영시작일" in df_ip.columns and df_ip["방영시작일"].notna().any() else "주차시작일"
    sel_year = df_ip[date_col_for_filter].dropna().dt.year.mode().iloc[0] if not df_ip[date_col_for_filter].dropna().empty else None

    # --- 비교 그룹 구성
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

    # --- 회차 숫자 보조 컬럼
    for d in (df_ip, base):
        if "회차_numeric" in d.columns:
            d["회차_num"] = pd.to_numeric(d["회차_numeric"], errors="coerce")
        else:
            d["회차_num"] = pd.to_numeric(d["회차"].str.extract(r"(\\d+)", expand=False), errors="coerce")

    # --- 서브 타이틀
    st.markdown(f"<div class='sub-title'>📺 {ip_selected} 성과 상세 리포트</div>", unsafe_allow_html=True)
    st.markdown("---")

    # --- KPI 계산
    f = df_ip.copy()
    val_T    = mean_of_ip_episode_mean(f, "T시청률")
    val_H    = mean_of_ip_episode_mean(f, "H시청률")
    val_live = mean_of_ip_episode_sum(f, "시청인구", ["TVING LIVE"])
    val_quick= mean_of_ip_episode_sum(f, "시청인구", ["TVING QUICK"])
    val_vod  = mean_of_ip_episode_sum(f, "시청인구", ["TVING VOD"])
    val_buzz = mean_of_ip_sums(f, "언급량")
    val_view = mean_of_ip_sums(f, "조회수")
    val_f    = mean_of_ip_episode_mean(f, "F_Score")

    c1, c2, c3, c4, c5 = st.columns(5)
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
    c6, c7, c8, c9, c10 = st.columns(5)
    kpi(c1, "🎯 타깃 시청률", fmt(val_T, digits=3))
    kpi(c2, "🏠 가구 시청률", fmt(val_H, digits=3))
    kpi(c3, "📺 티빙 LIVE", fmt(val_live, intlike=True))
    kpi(c4, "⚡ 티빙 QUICK", fmt(val_quick, intlike=True))
    kpi(c5, "▶️ 티빙 VOD", fmt(val_vod, intlike=True))
    kpi(c6, "👀 디지털 조회", fmt(val_view, intlike=True))
    kpi(c7, "💬 디지털 언급량", fmt(val_buzz, intlike=True))
    kpi(c8, "🔥 화제성 점수", fmt(val_f, intlike=True))
    kpi(c9, "🥇 펀덱스 1위", "—")
    kpi(c10, "⚓ 앵커드라마", "—")

    st.divider()

    # --- 주차별 시청자수 트렌드 (Stacked Bar)
    df_trend = f[f["metric"]=="시청인구"].copy()
    if not df_trend.empty:
        tv_weekly = df_trend[df_trend["매체"]=="TV"].groupby("주차시작일")["value"].sum()
        tving_livequick_weekly = df_trend[df_trend["매체"].isin(["TVING LIVE","TVING QUICK"])]\
            .groupby("주차시작일")["value"].sum()
        tving_vod_weekly = df_trend[df_trend["매체"]=="TVING VOD"].groupby("주차시작일")["value"].sum()

        all_dates = sorted(list(set(tv_weekly.index) | set(tving_livequick_weekly.index) | set(tving_vod_weekly.index)))
        if all_dates:
            df_bar = pd.DataFrame({"주차시작일": all_dates})
            df_bar["TV 본방"]   = df_bar["주차시작일"].map(tv_weekly).fillna(0)
            df_bar["티빙 본방"] = df_bar["주차시작일"].map(tving_livequick_weekly).fillna(0)
            df_bar["티빙 VOD"]  = df_bar["주차시작일"].map(tving_vod_weekly).fillna(0)

            df_long = df_bar.melt(id_vars="주차시작일",
                                  value_vars=["TV 본방","티빙 본방","티빙 VOD"],
                                  var_name="구분", value_name="시청자수")
            fig = px.bar(
                df_long, x="주차시작일", y="시청자수", color="구분", text="시청자수",
                title="📊 주차별 시청자수 (TV 본방 / 티빙 본방 / 티빙 VOD, 누적)"
            )
            fig.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig.update_layout(
                barmode="stack",
                height=420,
                margin=dict(t=50, b=40, l=20, r=20),
                xaxis_title=None, yaxis_title=None,
            )
            st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 5) 스타일 (간단 버전)
# =====================================================
st.markdown("""
<style>
.page-title { font-size: clamp(26px, 2.4vw, 34px); font-weight: 800; line-height: 1.25; }
.sub-title  { font-size: clamp(20px, 2.0vw, 28px); font-weight: 700; margin: 6px 0 8px 0; }
.kpi-card{
  background: #fff; border:1px solid #e9e9e9; border-radius:12px;
  padding:12px 14px; box-shadow: 0 2px 5px rgba(0,0,0,.03);
}
.kpi-title{ font-size:12px; color:#666; margin-bottom:6px; }
.kpi-value{ font-size:20px; font-weight:800; letter-spacing:-.3px; }
.gd-guideline { font-size: 13px; line-height: 1.35; }
.gd-guideline code { background: rgba(16,185,129,.10); color:#16a34a; padding:1px 6px; border-radius:6px; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 6) 엔트리 포인트
# =====================================================
def main():
    render_ip_detail()

if __name__ == "__main__":
    main()
