import streamlit as st
import pandas as pd
import time
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Tra cứu cổ phiếu VN", page_icon="📈", layout="wide")

st.markdown("""
<style>
html, body, p, div, span, li, label { font-size: 17px !important; }
table { font-size: 16px !important; border-collapse: collapse; width: 100%; }
thead th { font-size: 16px !important; font-weight: bold; background: #f0f2f6; padding: 8px 12px; }
tbody td { font-size: 16px !important; padding: 7px 12px; border-bottom: 1px solid #e6e9ef; }
tbody tr:hover { background: #f8f9fb; }
[data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 600; }
[data-testid="stMetricLabel"] { font-size: 15px !important; }
h1 { font-size: 28px !important; }
h2, h3 { font-size: 22px !important; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Tra cứu cổ phiếu Việt Nam")

col1, col2 = st.columns([5, 1])
with col1:
    symbol = st.text_input("", placeholder="Nhập mã: ACB, VCB, FPT, HPG...").upper().strip()
with col2:
    search = st.button("🔍 Tra cứu", type="primary", use_container_width=True)

if not symbol or not search:
    st.info("Nhập mã cổ phiếu và bấm Tra cứu")
    st.stop()

try:
    from vnstock import Reference, Fundamental
    from vnstock.ui import Market
except ImportError:
    st.error("Lỗi import vnstock")
    st.stop()

def fetch(fn, delay=0.8):
    try:
        r = fn()
        time.sleep(delay)
        return r
    except Exception:
        return None

def fmt_df(df):
    df2 = df.copy()
    for col in df2.select_dtypes(include='number').columns:
        def fmt_val(x):
            if pd.isna(x):
                return '-'
            f = float(x)
            if f == int(f) and abs(f) >= 1:
                return f"{int(f):,}"
            elif abs(f) < 1000:
                return f"{f:,.2f}"
            else:
                return f"{f:,.0f}"
        df2[col] = df2[col].apply(fmt_val)
    return df2

def show(df):
    if df is not None and not df.empty:
        st.table(fmt_df(df))

ref = Reference()
fun = Fundamental()
mkt = Market()
company = ref.company(symbol)
eq_mkt = mkt.equity(symbol)
eq_fun = fun.equity(symbol)

tab1, tab2, tab3, tab4 = st.tabs(["🏢 Công ty", "📊 Giá & Giao dịch", "💰 Tài chính", "📰 Tin tức & Sự kiện"])

with tab1:
    with st.spinner("Đang tải thông tin công ty..."):
        info = fetch(lambda: company.info())

    if info is not None and not info.empty:
        row = info.iloc[0]
        st.subheader(row.get('symbol', symbol))

        ff_raw = float(row.get('free_float_percentage') or 0)
        outstanding = float(row.get('outstanding_shares') or 1)
        if ff_raw <= 100:
            ff_pct = ff_raw
        elif ff_raw <= outstanding:
            ff_pct = ff_raw / outstanding * 100
        else:
            ff_pct = ff_raw
            while ff_pct > 100:
                ff_pct /= 100
        charter = float(row.get('charter_capital') or 0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sàn", row.get('exchange', '-'))
        c2.metric("Vốn điều lệ (tỷ)", f"{charter/1e9:,.0f}" if charter >= 1e9 else "-")
        c3.metric("CP lưu hành (triệu)", f"{outstanding/1e6:,.1f}")
        c4.metric("Free float", f"{ff_pct:.1f}%")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("CEO", row.get('ceo_name', '-'))
        c6.metric("Thành lập", str(row.get('founded_date', ''))[:10] if row.get('founded_date') else '-')
        c7.metric("Niêm yết", str(row.get('listing_date', ''))[:10] if row.get('listing_date') else '-')
        c8.metric("Giá niêm yết", f"{float(row.get('listing_price') or 0)/1000:,.1f}k")

        with st.expander("📋 Mô hình kinh doanh"):
            st.write(row.get('business_model', '-'))
        with st.expander("📜 Lịch sử phát triển"):
            st.write(row.get('history', '-'))
        with st.expander("📍 Địa chỉ & liên hệ"):
            st.write(f"**Địa chỉ:** {row.get('address', '-')}")
            st.write(f"**Điện thoại:** {row.get('phone', '-')}")
            st.write(f"**Email:** {row.get('email', '-')}")
            st.write(f"**Website:** {row.get('website', '-')}")
    else:
        st.warning(f"Không tìm thấy mã {symbol}")
        st.stop()

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("👥 Cổ đông lớn")
        sh = fetch(lambda: company.shareholders())
        if sh is not None and not sh.empty:
            try:
                sh = sh[['name', 'ownership_percentage', 'shares_owned', 'update_date']].copy()
                sh['update_date'] = sh['update_date'].astype(str).str[:10]
                sh.columns = ['Tên cổ đông', '% sở hữu', 'Số CP', 'Ngày CĐ']
            except Exception:
                pass
            show(sh)

        st.subheader("🏗️ Cơ cấu sở hữu")
        own = fetch(lambda: company.ownership())
        if own is not None and not own.empty:
            try:
                own = own[['owner_type', 'ownership_percentage', 'shares_owned']].copy()
                own.columns = ['Loại', '% sở hữu', 'Số CP']
            except Exception:
                pass
            show(own)

    with col_b:
        st.subheader("👔 Ban lãnh đạo")
        officers = fetch(lambda: company.officers())
        if officers is not None and not officers.empty:
            try:
                off = officers[['name', 'position', 'from_date']].copy()
                off.columns = ['Họ tên', 'Chức vụ', 'Từ năm']
                show(off)
            except Exception:
                show(officers)

        st.subheader("🏢 Công ty con")
        subs = fetch(lambda: company.subsidiaries())
        if subs is not None and not subs.empty:
            try:
                s = subs[['name', 'ownership_percent', 'charter_capital']].copy()
                s['charter_capital'] = (s['charter_capital'] / 1e9).round(1)
                s.columns = ['Tên', '% sở hữu', 'Vốn (tỷ)']
                show(s)
            except Exception:
                show(subs)

with tab2:
    st.subheader(f"💹 Giá hiện tại — {symbol}")
    with st.spinner("Đang tải giá..."):
        quote = fetch(lambda: eq_mkt.quote())

    if quote is not None and not quote.empty:
        qrow = quote.iloc[0]
        price = float(qrow.get('close_price') or 0)
        change = float(qrow.get('price_change') or 0)
        pct = float(qrow.get('percent_change') or 0)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Giá (nghìn đ)", f"{price/1000:,.2f}", f"{change/1000:+,.2f} ({pct:+.2f}%)")
        c2.metric("Mở cửa", f"{float(qrow.get('open_price') or 0)/1000:,.2f}")
        c3.metric("Cao nhất", f"{float(qrow.get('high_price') or 0)/1000:,.2f}")
        c4.metric("Thấp nhất", f"{float(qrow.get('low_price') or 0)/1000:,.2f}")
        c5.metric("TB khớp", f"{float(qrow.get('average_price') or 0)/1000:,.2f}")

        c6, c7, c8, c9, c10 = st.columns(5)
        c6.metric("Giá tham chiếu", f"{float(qrow.get('reference_price') or 0)/1000:,.2f}")
        c7.metric("Giá trần", f"{float(qrow.get('ceiling_price') or 0)/1000:,.2f}")
        c8.metric("Giá sàn", f"{float(qrow.get('floor_price') or 0)/1000:,.2f}")
        c9.metric("KL khớp (triệu CP)", f"{float(qrow.get('volume_accumulated') or 0)/1e6:,.2f}")
        c10.metric("Giá trị (tỷ)", f"{float(qrow.get('total_value') or 0)/1e9:,.1f}")

        st.subheader("🌏 Khối ngoại")
        cn1, cn2, cn3 = st.columns(3)
        buy_vol = float(qrow.get('foreign_buy_volume') or 0)
        sell_vol = float(qrow.get('foreign_sell_volume') or 0)
        net = buy_vol - sell_vol
        cn1.metric("NN mua (nghìn CP)", f"{buy_vol/1000:,.0f}")
        cn2.metric("NN bán (nghìn CP)", f"{sell_vol/1000:,.0f}")
        cn3.metric("NN ròng (nghìn CP)", f"{net/1000:+,.0f}")

        st.subheader("📋 Bảng giá (3 bước)")
        try:
            bid_ask = pd.DataFrame({
                'Giá mua': [f"{float(qrow.get(f'bid_price_{i}') or 0)/1000:,.2f}" for i in range(1,4)],
                'KL mua': [f"{int(qrow.get(f'bid_vol_{i}') or 0):,}" for i in range(1,4)],
                'Giá bán': [f"{float(qrow.get(f'ask_price_{i}') or 0)/1000:,.2f}" for i in range(1,4)],
                'KL bán': [f"{int(qrow.get(f'ask_vol_{i}') or 0):,}" for i in range(1,4)],
            }, index=['Bước 1', 'Bước 2', 'Bước 3'])
            st.table(bid_ask)
        except Exception:
            st.info("Không có dữ liệu bảng giá bid/ask")

    st.divider()
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.subheader("📈 Lịch sử giá (30 ngày)")
        today = pd.Timestamp.now()
        start = (today - pd.Timedelta(days=40)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        ohlcv = fetch(lambda: eq_mkt.ohlcv(start=start, end=end, interval='1D'))
        if ohlcv is not None and not ohlcv.empty:
            ohlcv['time'] = pd.to_datetime(ohlcv['time'])
            st.line_chart(ohlcv.set_index('time')['close'], height=200)
            ohlcv_show = ohlcv.sort_values('time', ascending=False).head(20).copy()
            ohlcv_show['time'] = ohlcv_show['time'].dt.strftime('%d/%m/%Y')
            show(ohlcv_show)

    with col_right:
        st.subheader("⚡ Khớp lệnh gần nhất")
        trades = fetch(lambda: eq_mkt.trades())
        if trades is not None and not trades.empty:
            try:
                t = trades.head(20).copy()
                t['time'] = pd.to_datetime(t['time']).dt.strftime('%H:%M:%S')
                t['price'] = t['price'].apply(lambda x: f"{x:,.2f}")
                t['volume'] = t['volume'].apply(lambda x: f"{x:,}")
                t.columns = ['Giờ', 'Giá (nghìn)', 'KL', 'Chiều', 'ID']
                st.table(t[['Giờ', 'Giá (nghìn)', 'KL', 'Chiều']])
            except Exception:
                show(trades.head(20))

with tab3:
    st.subheader(f"📊 Chỉ số tài chính — {symbol}")
    ratio = fetch(lambda: eq_fun.ratio())
    if ratio is not None and not ratio.empty:
        show(ratio)

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📋 KQKD theo quý")
        income_q = fetch(lambda: eq_fun.income_statement(period='quarter'))
        if income_q is not None and not income_q.empty:
            show(income_q)

    with col_r:
        st.subheader("📋 KQKD theo năm")
        income_y = fetch(lambda: eq_fun.income_statement(period='year'))
        if income_y is not None and not income_y.empty:
            show(income_y)

    st.subheader("🏦 Bảng cân đối kế toán (năm)")
    bs = fetch(lambda: eq_fun.balance_sheet(period='year'))
    if bs is not None and not bs.empty:
        show(bs)

    st.subheader("💸 Lưu chuyển tiền tệ (năm)")
    cf = fetch(lambda: eq_fun.cash_flow(period='year'))
    if cf is not None and not cf.empty:
        show(cf)

    st.subheader("💰 Lịch sử tăng vốn")
    cap = fetch(lambda: company.capital_history())
    if cap is not None and not cap.empty:
        try:
            cap['Vốn (tỷ)'] = (cap['charter_capital'] / 1e9).round(1)
            cap['Ngày'] = cap['date'].astype(str).str[:10]
            show(cap[['Ngày', 'Vốn (tỷ)']].sort_values('Ngày', ascending=False))
        except Exception:
            show(cap)

with tab4:
    col_n, col_e = st.columns(2)
    with col_n:
        st.subheader(f"📰 Tin tức — {symbol}")
        news = fetch(lambda: company.news())
        if news is not None and not news.empty:
            for _, nrow in news.head(15).iterrows():
                date = str(nrow.get('publish_time', ''))[:10]
                st.markdown(f"**{nrow.get('title', '')}**  \n*{date}*")
                st.caption(str(nrow.get('head', ''))[:200])
                st.divider()
        else:
            st.info("Không có tin tức")

    with col_e:
        st.subheader(f"📅 Sự kiện — {symbol}")
        events = fetch(lambda: company.events())
        if events is not None and not events.empty:
            show(events)
        else:
            st.info("Không có sự kiện")

        st.subheader("🔄 Giao dịch nội bộ")
        insider = fetch(lambda: company.insider_trading())
        if insider is not None and not insider.empty:
            show(insider)
        else:
            st.info("Không có dữ liệu giao dịch nội bộ")
