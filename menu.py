import streamlit as st
import pandas as pd
from io import BytesIO
import numpy as np 
from PIL import Image
from finance_utils import insert_summary_rows, calculate_financials

st.set_page_config(page_title="for_freee_user", layout="wide")
pd.options.display.float_format = '{:,.0f}'.format

image1 = Image.open("image1.png")
image2 = Image.open("image2.png")
image3 = Image.open("image3.png")
image4 = Image.open("image4.png")
image5 = Image.open("image5.png")
image6 = Image.open("image6.png")

st.subheader('部門別推移表変換 freee形式 to 財務R4形式')

# freee側の設定
with st.expander('freeeから勘定科目一覧(CSV)を出力する方法'):
        st.image(image1, caption="「マスタ・口座」から「勘定科目」を選択してください。", use_container_width=True)
        st.image(image2, caption="「エクスポート」から「勘定科目csvエクスポート」を選択してください。", use_container_width=True)
        st.image(image3, caption="「ショートカット2」に必ず勘定科目コードを設定してください。", use_container_width=True)
        
with st.expander('freeeから推移表(CSV)を出力する方法'):
        st.image(image4, caption="「マスタ・口座」から「勘定科目」を選択してください。", use_container_width=True)
        st.image(image5, caption="「エクスポート」から「勘定科目csvエクスポート」を選択してください。", use_container_width=True)
        st.image(image6, caption="「ショートカット2」に必ず勘定科目コードを設定してください。", use_container_width=True)

# ファイルアップロード
freee_kamoku_file = st.file_uploader("freeeから出力した勘定科目一覧(CSV)をアップロードしてください。")
freee_before_file = st.file_uploader("freeeから出力した前期の推移表(CSV)をアップロードしてください。")
freee_this_file   = st.file_uploader("freeeから出力した今期の推移表(CSV)をアップロードしてください。")

if freee_kamoku_file:
    kamoku_df = pd.read_csv(freee_kamoku_file, encoding="cp932", header=0)

    if '勘定科目コード' not in kamoku_df.columns and 'ショートカット2' in kamoku_df.columns:
        kamoku_df.rename(columns={'ショートカット2': '勘定科目コード'}, inplace=True)
        with st.expander('勘定科目一覧を表示する。'):
            st.dataframe(kamoku_df)
    else:         
        with st.expander('勘定科目一覧を表示する。'):
            st.dataframe(kamoku_df)
    this_df = pd.read_csv(freee_this_file, encoding="cp932", header=1)
    this_df.rename(columns={this_df.columns[1]: "勘定科目"}, inplace=True)
    this_df = this_df[this_df['勘定科目'] != '当期商品仕入']
    if '部門' not in this_df.columns:
        this_df.insert(2, '部門', '')  # 3列目（0始まり）に空の「部門」列を追加

    if {"勘定科目コード","部門"}.issubset(this_df.columns):
        m1 = this_df["勘定科目コード"].notna() & this_df["部門"].isna()
        m2 = this_df["勘定科目コード"].isna()  & this_df["部門"].isna()
        this_df.loc[m1, "部門"] = "合計"
        this_df.loc[m2, "部門"] = "集計科目"
    if "期間累計" in this_df.columns:
        cols = list(this_df.columns)
        cols.remove("期間累計")
        cols.insert(3, "期間累計")
        this_df = this_df[cols]
    this_df.rename(columns={"期間累計": "今期累計"}, inplace=True)
    this_df.insert(3, "前期累計", 0)
    this_df.insert(5, "増減", 0)
    this_df["今期累計"] = pd.to_numeric(this_df["今期累計"], errors="coerce").fillna(0)
    this_df = this_df.merge(kamoku_df[["勘定科目","小分類"]], on="勘定科目", how="left")

    excl = {"勘定科目","勘定科目コード","部門","前期累計","増減","今期累計","小分類"}
    elapsed_months = len([c for c in this_df.columns if c not in excl])

    before_df = pd.read_csv(freee_before_file, encoding="cp932", header=1)
    before_df.rename(columns={before_df.columns[1]: "勘定科目"}, inplace=True)
    before_df = before_df[this_df['勘定科目'] != '当期商品仕入']
    if '部門' not in before_df.columns:
        before_df.insert(2, '部門', '')  # 3列目（0始まり）に空の「部門」列を追加
        
    if {"勘定科目コード","部門"}.issubset(before_df.columns):
        m1 = before_df["勘定科目コード"].notna() & before_df["部門"].isna()
        m2 = before_df["勘定科目コード"].isna()  & before_df["部門"].isna()
        before_df.loc[m1, "部門"] = "合計"
        before_df.loc[m2, "部門"] = "集計科目"
    if "期間累計" in before_df.columns:
        cols = list(before_df.columns)
        cols.remove("期間累計")
        cols.insert(3, "期間累計")
        before_df = before_df[cols].rename(columns={"期間累計": "前期累計"})
    else:
        before_df["前期累計"] = 0
    before_df = before_df.merge(kamoku_df[["勘定科目","小分類"]], on="勘定科目", how="left")

    monthly_cols = [
        c for c in before_df.columns
        if c not in {"勘定科目","勘定科目コード","部門","前期累計","小分類"}
    ][:elapsed_months]

    before_df["前期累計"] = (
        before_df[monthly_cols].replace({',':''}, regex=True)
        .apply(pd.to_numeric, errors="coerce").sum(axis=1)
    )

    before_df["平均"] = (
        before_df[monthly_cols].replace({',': ''}, regex=True)
        .apply(pd.to_numeric, errors="coerce").mean(axis=1)
        .apply(np.floor).fillna(0).astype(int)
    )

    all_kamoku = kamoku_df[["勘定科目コード", "勘定科目", "小分類"]].drop_duplicates()
    all_depts = pd.concat([this_df["部門"], before_df["部門"]]).dropna().unique()
    dept_df = pd.DataFrame(all_depts, columns=["部門"])
    all_combos = all_kamoku.merge(dept_df, how="cross")
    this_df = all_combos.merge(this_df, on=["勘定科目コード", "勘定科目", "小分類", "部門"], how="left")
    before_df = all_combos.merge(before_df, on=["勘定科目コード", "勘定科目", "小分類", "部門"], how="left")

    for df in [this_df, before_df]:
        for col in df.columns:
            if col not in ["勘定科目コード", "勘定科目", "小分類", "部門"] and df[col].dtype.kind in "fi":
                df[col] = df[col].fillna(0)

    st.subheader('前期推移表プレビュー')
    st.dataframe(before_df)

    depts = pd.concat([this_df["部門"], before_df["部門"]]).dropna().unique().tolist()
    default = [d for d in depts if d != "集計科目"]
    selected = st.multiselect(
        "表示する部門を選択してください（デフォルトは『集計科目』以外）",
        options=depts, default=default
    )

    if selected:
        prior_parts = []
        for dept in selected:
            df_b = before_df[before_df["部門"] == dept].copy()
            df_b = insert_summary_rows(df_b, dept)
            df_b = calculate_financials(df_b)
            cols_b = [
                c for c in df_b.columns
                if c not in {"勘定科目","勘定科目コード","部門","小分類","前期累計","増減"}
            ][:elapsed_months]
            df_b["前期累計"] = df_b[cols_b].sum(axis=1)
            prior_parts.append(df_b[["勘定科目","部門","前期累計"]])
        prior_df_lookup = pd.concat(prior_parts).drop_duplicates()

        dfs = []
        for dept in selected:
            df_t = this_df[this_df["部門"] == dept].copy()
            df_t = insert_summary_rows(df_t, dept)
            df_t = calculate_financials(df_t)
            df_t.drop(columns=["前期累計"], inplace=True)
            df_t = df_t.merge(prior_df_lookup, on=["勘定科目","部門"], how="left")
            df_t["前期累計"] = df_t["前期累計"].fillna(0)
            df_t["増減"]     = df_t["今期累計"] - df_t["前期累計"]
            dfs.append(df_t)

        final_df = pd.concat(dfs, ignore_index=True)
        cols = final_df.columns.tolist()
        if "前期累計" in cols:
            cols.remove("前期累計")
            cols.insert(3, "前期累計")
            final_df = final_df[cols]

        avg_df = before_df[["勘定科目", "部門", "平均"]].copy()
        avg_df.rename(columns={"平均": "前年平均"}, inplace=True)
        final_df = final_df.merge(avg_df, on=["勘定科目", "部門"], how="left")

        st.subheader('今期推移表プレビュー')
        st.dataframe(final_df)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            wb = writer.book
            num_fmt        = wb.add_format({'num_format': '#,##0', 'border': 1})
            border_fmt     = wb.add_format({'border': 1})
            gray_fmt       = wb.add_format({'bg_color': '#D9D9D9', 'border': 1, 'num_format': '#,##0'})
            highlight_fmt  = wb.add_format({'bg_color': '#C6EFCE', 'bold': True, 'border': 1})
            highlight_num  = wb.add_format({'bg_color': '#C6EFCE', 'bold': True, 'border': 1, 'num_format': '#,##0'})
            average_fmt    = wb.add_format({'bold': True, 'border': 1, 'bg_color': '#FFFFCC', 'num_format': '#,##0'})
            title_fmt      = wb.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'font_size': 28})

            highlights = [
                "純売上高", "純仕入高", "売上原価", "売上総利益", "人件費合計", "販売費及び一般管理費",
                "営業利益", "営業外収益合計", "営業外費用合計", "経常利益",
                "特別利益合計", "特別損失合計", "税引前当期純利益",
                "法人税・住民税・事業税", "税引後当期純利益"
            ]

            for dept in selected:
                df = final_df[final_df["部門"] == dept].copy()
                df = df.drop(columns=['勘定科目コード', '部門', '小分類'], errors='ignore')
                cols = df.columns.tolist()
                if "前期累計" in cols:
                    cols.remove("前期累計")
                    cols.insert(1, "前期累計")
                    df = df[cols]

                sheet = dept[:31].replace('/', '_').replace('\\', '_')
                ws = writer.book.add_worksheet(sheet)
                writer.sheets[sheet] = ws
                startrow = 2
                col_names = df.columns.tolist()
                last_col = len(col_names) - 1
                ws.set_row(0, 30)
                ws.merge_range(0, 0, 0, last_col, '2 期 比 較 推 移表', title_fmt)
                ws.write(1, 0, dept)
                for col_idx, col in enumerate(col_names):
                    fmt = average_fmt if col == "前年平均" else border_fmt
                    ws.write(startrow, col_idx, col, fmt)

                for row_idx, (_, row) in enumerate(df.iterrows(), start=startrow + 1):
                    is_highlight = row.iloc[0] in highlights
                    avg_val = row.get("前年平均", None)
                    for col_idx, val in enumerate(row):
                        col_name = col_names[col_idx]
                        if is_highlight:
                            if col_name == "前年平均":
                                fmt = average_fmt
                            elif pd.isna(val):
                                fmt = highlight_fmt
                            elif isinstance(val, (int, float)):
                                fmt = highlight_num
                            else:
                                fmt = highlight_fmt
                        elif col_idx >= 4 and col_name != "前年平均" and pd.notna(val) and pd.notna(avg_val):
                            if abs(val - avg_val) >= 300000:
                                fmt = gray_fmt
                            else:
                                fmt = num_fmt
                        elif col_name == "前年平均":
                            fmt = average_fmt
                        elif pd.isna(val):
                            fmt = border_fmt
                        elif isinstance(val, (int, float)):
                            fmt = num_fmt
                        else:
                            fmt = border_fmt
                        if pd.isna(val):
                            ws.write_blank(row_idx, col_idx, None, fmt)
                        else:
                            ws.write(row_idx, col_idx, val, fmt)

                ws.set_default_row(25)
                ws.set_column('A:A', 25)
                ws.set_column('B:Z', 15)

        output.seek(0)
        st.download_button(
            label="Excel(円単位)をダウンロード",
            data=output,
            file_name="部門別推移表(円単位).xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Excel出力
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        wb = writer.book

        # フォーマット（千円単位表示に変更）
        num_fmt        = wb.add_format({'num_format': '#,##0,', 'border': 1})
        border_fmt     = wb.add_format({'border': 1})
        gray_fmt       = wb.add_format({'bg_color': '#D9D9D9', 'border': 1, 'num_format': '#,##0,'})
        highlight_fmt  = wb.add_format({'bg_color': '#C6EFCE', 'bold': True, 'border': 1})
        highlight_num  = wb.add_format({'bg_color': '#C6EFCE', 'bold': True, 'border': 1, 'num_format': '#,##0,'})
        average_fmt    = wb.add_format({'bold': True, 'border': 1, 'bg_color': '#FFFFCC', 'num_format': '#,##0,'})
        title_fmt      = wb.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'font_size': 28})

        highlights = [
            "純売上高", "純仕入高", "売上原価", "売上総利益", "人件費合計", "販売費及び一般管理費",
            "営業利益", "営業外収益合計", "営業外費用合計", "経常利益",
            "特別利益合計", "特別損失合計", "税引前当期純利益",
            "法人税・住民税・事業税", "税引後当期純利益"
        ]

        for dept in selected:
            df = final_df[final_df["部門"] == dept].copy()
            df = df.drop(columns=['勘定科目コード', '部門', '小分類'], errors='ignore')
            cols = df.columns.tolist()
            if "前期累計" in cols:
                cols.remove("前期累計")
                cols.insert(1, "前期累計")
                df = df[cols]

            sheet = dept[:31].replace('/', '_').replace('\\', '_')
            ws = writer.book.add_worksheet(sheet)
            writer.sheets[sheet] = ws
            startrow = 2
            col_names = df.columns.tolist()
            last_col = len(col_names) - 1
            ws.set_row(0, 30)

            # タイトル
            ws.merge_range(0, 0, 0, last_col, '2 期 比 較 推 移 表', title_fmt)
            ws.write(1, 0, dept + "　※ 単位：千円")

            # ヘッダー
            for col_idx, col in enumerate(col_names):
                fmt = average_fmt if col == "前年平均" else border_fmt
                ws.write(startrow, col_idx, col, fmt)

            # データ行
            for row_idx, (_, row) in enumerate(df.iterrows(), start=startrow + 1):
                is_highlight = row.iloc[0] in highlights
                avg_val = row.get("前年平均", None)

                # 金額列だけ抽出（通常は4列目以降）
                value_cols = row.iloc[4:]
                is_all_zero_or_blank = not is_highlight and value_cols.apply(lambda x: pd.isna(x) or x == 0).all()

                # 非表示行の場合、set_rowで行自体に設定
                if is_all_zero_or_blank:
                    ws.set_row(row_idx, options={'hidden': True})
                else:
                    ws.set_row(row_idx, 25)  # 通常行の高さ指定

                for col_idx, val in enumerate(row):
                    col_name = col_names[col_idx]
                    if is_highlight:
                        if col_name == "前年平均":
                            fmt = average_fmt
                        elif pd.isna(val):
                            fmt = highlight_fmt
                        elif isinstance(val, (int, float)):
                            fmt = highlight_num
                        else:
                            fmt = highlight_fmt
                    elif col_idx >= 4 and col_name != "前年平均" and pd.notna(val) and pd.notna(avg_val):
                        if abs(val - avg_val) >= 300000:
                            fmt = gray_fmt
                        else:
                            fmt = num_fmt
                    elif col_name == "前年平均":
                        fmt = average_fmt
                    elif pd.isna(val):
                        fmt = border_fmt
                    elif isinstance(val, (int, float)):
                        fmt = num_fmt
                    else:
                        fmt = border_fmt

                    if pd.isna(val):
                        ws.write_blank(row_idx, col_idx, None, fmt)
                    else:
                        ws.write(row_idx, col_idx, val, fmt)



            # レイアウト調整
            ws.set_default_row(25)
            ws.set_column('A:A', 25)
            ws.set_column('B:Z', 12)

    output.seek(0)
    st.download_button(
        label="Excel(千円単位)をダウンロード",
        data=output,
        file_name="部門別推移表(千円単位).xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Excel出力
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        wb = writer.book

        # フォーマット（千円単位表示に変更）
        num_fmt        = wb.add_format({'num_format': '#,##0,', 'border': 1})
        border_fmt     = wb.add_format({'border': 1})
        highlight_fmt  = wb.add_format({'bg_color': '#C6EFCE', 'bold': True, 'border': 1})
        highlight_num  = wb.add_format({'bg_color': '#C6EFCE', 'bold': True, 'border': 1, 'num_format': '#,##0,'})
        title_fmt      = wb.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'font_size': 28})
        subtitle_fmt  = wb.add_format({'bold': True, 'font_size': 14})

        highlights = [
            "純売上高", "純仕入高", "売上原価", "売上総利益", "人件費合計", "販売費及び一般管理費",
            "営業利益", "営業外収益合計", "営業外費用合計", "経常利益",
            "特別利益合計", "特別損失合計", "税引前当期純利益",
            "法人税・住民税・事業税", "税引後当期純利益"
        ]

        for dept in selected:
            df = final_df[final_df["部門"] == dept].copy()
            df = df.drop(columns=['勘定科目コード', '部門', '小分類', '前年平均'], errors='ignore')
            sheet = dept[:31].replace('/', '_').replace('\\', '_')
            ws = writer.book.add_worksheet(sheet)
            writer.sheets[sheet] = ws
            startrow = 2
            col_names = df.columns.tolist()
            last_col = len(col_names) - 1
            ws.set_row(0, 30)

            # タイトル
            ws.merge_range(0, 0, 0, last_col, '2 期 比 較 推 移 表', title_fmt)
            ws.write(1, 0, dept + "　※ 単位：千円", subtitle_fmt)

            # ヘッダー
            for col_idx, col in enumerate(col_names):
                ws.write(startrow, col_idx, col, border_fmt)

            # データ行
            for row_idx, (_, row) in enumerate(df.iterrows(), start=startrow + 1):
                is_highlight = row.iloc[0] in highlights

                # 金額列だけ抽出（通常は4列目以降）
                value_cols = row.iloc[4:]
                is_all_zero_or_blank = not is_highlight and value_cols.apply(lambda x: pd.isna(x) or x == 0).all()

                # 非表示設定または通常行設定
                if is_all_zero_or_blank:
                    ws.set_row(row_idx, options={'hidden': True})
                else:
                    ws.set_row(row_idx, 25)

                for col_idx, val in enumerate(row):
                    if is_highlight:
                        if pd.isna(val):
                            fmt = highlight_fmt
                        elif isinstance(val, (int, float)):
                            fmt = highlight_num
                        else:
                            fmt = highlight_fmt
                    elif pd.isna(val):
                        fmt = border_fmt
                    elif isinstance(val, (int, float)):
                        fmt = num_fmt
                    else:
                        fmt = border_fmt

                    if pd.isna(val):
                        ws.write_blank(row_idx, col_idx, None, fmt)
                    else:
                        ws.write(row_idx, col_idx, val, fmt)

            # レイアウト調整
            ws.set_default_row(25)
            ws.set_column('A:A', 25)
            ws.set_column('B:Z', 12)

    output.seek(0)
    st.download_button(
        label="通常) Excel(千円単位)をダウンロード",
        data=output,
        file_name="部門別推移表(千円単位).xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
