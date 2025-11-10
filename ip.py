
# -*- coding: utf-8 -*-
# 📈 IP 성과 자세히보기 — 단독 실행판 (with missing utils restored)

import re
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import gspread
from google.oauth2.service_account import Credentials


# ======================= [ 0. 페이지 설정 ] =======================
st.set_page_config(
    page_title="IP 성과 자세히보기",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ======================= [ 1. 스타일 ] =======================
st.markdown(
    """
<style>
.page-title { font-size: clamp(26px, 2.6vw, 36px); font-weight: 800; letter-spacing:-.02em; }
.kpi-card{background:rgba(0,0,0,.03);border-radius:16px;padding:14px 16px;margin:4px 0;box-shadow:inset 0 0 0 1px rgba(0,0,0,.04)}
.kpi-title{font-size:12px;color:#475569;margin-bottom:8px;font-weight:700;letter-spacing:.02em}
.kpi-value{font-size:22px;font-weight:800;letter-spacing:-.02em}
.gd-guideline { font-size: 13px; line-height: 1.35; }
.gd-guideline code{ background: rgba(16,185,129,.10); color:#16a34a; padding: 1px 6px; border-radius: 6px; }
</style>
""",
    unsafe_allow_html=True
)


# ======================= [ 2. 데이터 로드 (gspread) ] =======================
@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds_info = st.secrets["gcp_service_account"]
    if isinstance(creds_info, dict) and "private_key" in creds_info:
        pk = creds_info["private_key"]
        if isinstance(pk, str):
            creds_info = {**creds_info, "private_key": pk.replace("\\n", "\n")}
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)

    sheet_id = st.secrets["SHEET_ID"]
    worksheet_name = st.secrets["SHEET_NAME"]
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(worksheet_name)

    df = pd.DataFrame(worksheet.get_all_records())

    # 전처리
    if "주차시작일" in df.columns:
        df["주차시작일"] = pd.to_datetime(df["주차시작일"].astype(str).str.strip(), format="%Y. %m. %d", errors="coerce")
    if "방영시작일" in df.columns:
        df["방영시작일"] = pd.to_datetime(df["방영시작일"].astype(str).str.strip(), format="%Y. %m. %d", errors="coerce")
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


# ======================= [ 3. 공통 유틸 ] =======================
DEMO_COLS_ORDER: List[str] = [
    # 남성
    "남10대", "남20대", "남30대", "남40대", "남50대",
    # 여성
    "여10대", "여20대", "여30대", "여40대", "여50대",
    # (있으면 처리될 추가 열)
    "남전체", "여전체"
]

def _gender_from_demo(s: str) -> Optional[str]:
    if not isinstance(s, str): return None
    s = s.strip()
    if s.startswith("남"): return "남"
    if s.startswith("여"): return "여"
    return None

def _decade_label_clamped(s: str) -> Optional[str]:
    if not isinstance(s, str): return None
    m = re.search(r"(\d{2})대", s)
    if m:
        decade = int(m.group(1))
        # 10~50대만 사용, 범위 밖은 가장 가까운 구간으로 클램프
        decade = max(10, min(50, decade))
        return f"{decade}대"
    return None

def _fmt_ep(x) -> str:
    try:
        n = int(float(x))
        return f"{n}화"
    except Exception:
        return str(x)

def fmt(v, digits=3, intlike=False):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return f"{v:,.0f}" if intlike else f"{v:.{digits}f}"

def kpi(col, title, value):
    with col:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">{title}</div>'
            f'<div class="kpi-value">{value}</div></div>',
            unsafe_allow_html=True
        )

def _episode_col(df: pd.DataFrame) -> str:
    return "회차_numeric" if "회차_numeric" in df.columns else ("회차_num" if "회차_num" in df.columns else "회차")

def _get_view_data(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["metric"] == "조회수"].copy()
    if sub.empty: return sub
    if "매체" in sub.columns and "세부속성1" in sub.columns:
        yt_mask = (sub["매체"] == "유튜브")
        attr_mask = sub["세부속성1"].isin(["PGC", "UGC"])
        sub = sub[~yt_mask | (yt_mask & attr_mask)]
    return sub

def mean_of_ip_episode_mean(df: pd.DataFrame, metric_name: str, media: Optional[List[str]] = None) -> Optional[float]:
    sub = df[(df["metric"] == metric_name)].copy()
    if media is not None:
        sub = sub[sub["매체"].isin(media)]
    if sub.empty: return None
    ep_col = _episode_col(sub)
    sub = sub.dropna(subset=[ep_col]).copy()
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
    sub = sub.dropna(subset=["value"])
    if sub.empty: return None
    ep_mean = sub.groupby(["IP", ep_col], as_index=False)["value"].mean()
    per_ip_mean = ep_mean.groupby("IP")["value"].mean()
    return float(per_ip_mean.mean()) if not per_ip_mean.empty else None

def mean_of_ip_episode_sum(df: pd.DataFrame, metric_name: str, media: Optional[List[str]] = None) -> Optional[float]:
    sub = df[(df["metric"] == metric_name)].copy()
    if media is not None:
        sub = sub[sub["매체"].isin(media)]
    if sub.empty: return None
    ep_col = _episode_col(sub)
    sub = sub.dropna(subset=[ep_col]).copy()
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
    sub = sub.dropna(subset=["value"])
    if sub.empty: return None
    ep_sum = sub.groupby(["IP", ep_col], as_index=False)["value"].sum()
    per_ip_mean = ep_sum.groupby("IP")["value"].mean()
    return float(per_ip_mean.mean()) if not per_ip_mean.empty else None

def mean_of_ip_sums(df: pd.DataFrame, metric_name: str, media: Optional[List[str]] = None) -> Optional[float]:
    if metric_name == "조회수":
        sub = _get_view_data(df)
    else:
        sub = df[df["metric"] == metric_name].copy()
    if media is not None:
        sub = sub[sub["매체"].isin(media)]
    if sub.empty: return None
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce").replace(0, np.nan)
    sub = sub.dropna(subset=["value"])
    if sub.empty: return None
    per_ip_sum = sub.groupby("IP")["value"].sum()
    return float(per_ip_sum.mean()) if not per_ip_sum.empty else None


# ======================= [ 4. 성별 피라미드 (보조 섹션) ] =======================
def render_gender_pyramid(df_ip: pd.DataFrame, title: str = "성별/연령 피라미드"):
    if "데모" not in df_ip.columns or "metric" not in df_ip.columns:
        return
    sub = df_ip[(df_ip["metric"] == "시청인구") & (df_ip["데모"].isin(DEMO_COLS_ORDER))].copy()
    if sub.empty:
        return
    sub["gender"] = sub["데모"].map(_gender_from_demo)
    sub["decade"] = sub["데모"].map(_decade_label_clamped)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub = sub.dropna(subset=["gender", "decade", "value"])
    if sub.empty:
        return

    # 남성은 음수로 뒤집어 피라미드 형태
    sub.loc[sub["gender"] == "남", "plot_val"] = -sub.loc[sub["gender"] == "남", "value"]
    sub.loc[sub["gender"] == "여", "plot_val"] = sub.loc[sub["gender"] == "여", "value"]

    # 주차/회차 단위가 섞여 있을 수 있으니 전체 합계 기준
    g = sub.groupby(["gender", "decade"], as_index=False)["plot_val"].sum()
    g = g.sort_values("decade")

    fig = go.Figure()
    male = g[g["gender"] == "남"]
    female = g[g["gender"] == "여"]
    fig.add_bar(y=male["decade"], x=male["plot_val"], name="남성", orientation="h")
    fig.add_bar(y=female["decade"], x=female["plot_val"], name="여성", orientation="h")

    fig.update_layout(
        title=title,
        barmode="overlay",
        height=420,
        margin=dict(t=50, b=40, l=20, r=20),
        xaxis_title=None, yaxis_title=None,
    )
    # x축 라벨을 절대값으로 보기 좋게
    fig.update_xaxes(tickformat=",", tickvals=sorted(list(set(male["plot_val"].tolist() + female["plot_val"].tolist()))))
    st.plotly_chart(fig, use_container_width=True)


# ======================= [ 5. 페이지 본문 ] =======================
def render_ip_detail():
    df_full = load_data()

    filter_cols = st.columns([3, 2, 2])
    with filter_cols[0]:
        st.markdown("<div class='page-title'>📈 IP 성과 자세히보기</div>", unsafe_allow_html=True)
    with st.expander("ℹ️ 지표 기준 안내", expanded=False):
        st.markdown("<div class='gd-guideline'>", unsafe_allow_html=True)
        st.markdown(
            """
**지표 기준**
- **시청률** `회차평균`: 전국 기준 가구 / 타깃(2049) 시청률
- **티빙 LIVE** `회차평균`: 업데이트 예정
- **티빙 QUICK** `회차평균`: 방영당일 VOD 시청 UV
- **티빙 VOD** `회차평균`: 방영일+1부터 +6까지 **6days** VOD UV
- **디지털 조회/언급량** `회차총합`: 방영주차(월~일) 내 총합
- **화제성 점수** `회차평균`: 방영기간 주차별 화제성 점수 평균
"""
        )
        st.markdown("</div>", unsafe_allow_html=True)

    ip_options = sorted(df_full["IP"].dropna().unique().tolist())
    with filter_cols[1]:
        ip_selected = st.selectbox(
            "IP (단일선택)",
            ip_options,
            index=0 if ip_options else None,
            placeholder="IP 선택",
            label_visibility="collapsed"
        )
    with filter_cols[2]:
        st.multiselect(
            "비교 그룹 기준",
            ["동일 편성", "방영 연도"],
            default=["동일 편성"],
            label_visibility="collapsed"
        )

    if not ip_selected:
        st.stop()

    df_ip = df_full[df_full["IP"] == ip_selected].copy()

    # ===== KPI 계산 (IP 단일 기준) =====
    T = mean_of_ip_episode_mean(df_ip, "T시청률")
    H = mean_of_ip_episode_mean(df_ip, "H시청률")
    live = mean_of_ip_episode_sum(df_ip, "시청인구", ["TVING LIVE"])
    quick = mean_of_ip_episode_sum(df_ip, "시청인구", ["TVING QUICK"])
    vod = mean_of_ip_episode_sum(df_ip, "시청인구", ["TVING VOD"])
    views = mean_of_ip_sums(df_ip, "조회수")
    buzz = mean_of_ip_sums(df_ip, "언급량")

    k1 = st.columns(5)
    kpi(k1[0], "타깃시청률", fmt(T, digits=3))
    kpi(k1[1], "가구시청률", fmt(H, digits=3))
    kpi(k1[2], "티빙라이브", fmt(live, intlike=True))
    kpi(k1[3], "티빙QUICK", fmt(quick, intlike=True))
    kpi(k1[4], "티빙 VOD", fmt(vod, intlike=True))

    k2 = st.columns(2)
    kpi(k2[0], "총언급량", fmt(buzz, intlike=True))
    kpi(k2[1], "디지털조회수", fmt(views, intlike=True))

    st.markdown("---")

    # ===== 회차별 시청률 =====
    ep_col = _episode_col(df_ip)
    sub_rate = df_ip[df_ip["metric"].isin(["T시청률", "H시청률"])].dropna(subset=[ep_col]).copy()
    if not sub_rate.empty:
        sub_rate["value"] = pd.to_numeric(sub_rate["value"], errors="coerce")
        sub_rate = sub_rate.dropna(subset=["value"])
        sub_rate["metric"] = sub_rate["metric"].replace({"T시청률":"타깃","H시청률":"가구"})
        fig_rate = px.line(
            sub_rate.sort_values(by=[ep_col]),
            x=ep_col, y="value", color="metric",
            markers=True,
            title=f"회차별 시청률 추이 — {ip_selected}"
        )
        fig_rate.update_layout(xaxis_title="회차", yaxis_title="시청률(%)")
        st.plotly_chart(fig_rate, use_container_width=True)

    # ===== TVING 시청자 스택 =====
    sub_tving = df_ip[(df_ip["metric"]=="시청인구") & (df_ip["매체"].isin(["TVING LIVE","TVING QUICK","TVING VOD"]))].dropna(subset=[ep_col]).copy()
    if not sub_tving.empty:
        sub_tving["value"] = pd.to_numeric(sub_tving["value"], errors="coerce")
        sub_tving = sub_tving.dropna(subset=["value"])
        fig_tv = px.bar(
            sub_tving.sort_values(by=[ep_col]),
            x=ep_col, y="value", color="매체",
            title=f"회차별 TVING 시청자 — {ip_selected}"
        )
        fig_tv.update_layout(barmode="stack", xaxis_title="회차", yaxis_title="시청자수")
        st.plotly_chart(fig_tv, use_container_width=True)

    # ===== 디지털 조회/언급 (주차) =====
    sub_view = _get_view_data(df_ip.copy())
    if "주차시작일" in df_ip.columns and (not sub_view.empty or not df_ip[df_ip["metric"]=="언급량"].empty):
        sub_view = sub_view[["주차시작일","value"]].assign(metric="조회수") if not sub_view.empty else pd.DataFrame(columns=["주차시작일","value","metric"])
        sub_buzz = df_ip[df_ip["metric"]=="언급량"][["주차시작일","value"]].assign(metric="언급량")
        sub_du2 = pd.concat([sub_view, sub_buzz], ignore_index=True)
        sub_du2["value"] = pd.to_numeric(sub_du2["value"], errors="coerce")
        sub_du2 = sub_du2.dropna(subset=["value","주차시작일"])
        if not sub_du2.empty:
            sub_du2 = sub_du2.groupby(["주차시작일","metric"], as_index=False)["value"].sum()
            fig_du = px.bar(
                sub_du2.sort_values("주차시작일"),
                x="주차시작일", y="value", color="metric",
                title=f"주차별 디지털 조회/언급 — {ip_selected}"
            )
            fig_du.update_layout(barmode="stack", xaxis_title="주차", yaxis_title="합계")
            st.plotly_chart(fig_du, use_container_width=True)

    # ===== 성별/연령 피라미드 =====
    render_gender_pyramid(df_ip, title="성별/연령 피라미드 (전체 합계)")


# ======================= [ 6. 엔트리 포인트 ] =======================
def main():
    render_ip_detail()

if __name__ == "__main__":
    main()
