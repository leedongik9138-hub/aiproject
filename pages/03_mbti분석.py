
# =====================================
# 12. 순위 순서대로 실제 막대그래프 만들기
# =====================================
st.subheader(
    f"🏆 {selected_country} MBTI 순위별 그래프"
)

st.caption("🥇 1등부터 16등까지 순서대로 표시됩니다.")

# sorted_data는 이미 높은 비율부터 정렬되어 있음
chart_data = {
    "순위": [
        f"{rank + 1}등 ({mbti})"
        for rank, (mbti, percent) in enumerate(sorted_data)
    ],
    "비율(%)": [
        round(percent, 2)
        for mbti, percent in sorted_data
    ]
}

# 실제 막대그래프 출력
st.bar_chart(
    chart_data,
    x="순위",
    y="비율(%)",
    height=500,
    horizontal=False
)
