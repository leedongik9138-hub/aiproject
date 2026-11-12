
# ==========================================
# 10. 그래프 데이터 만들기
# ==========================================

chart_data = []

# 과거 실제 기온과 회귀선
for year, actual in zip(years, temperatures):

    chart_data.append({
        "year": year,
        "actual": actual,
        "fitted": predict_temperature(year),
        "forecast": None
    })


# 미래 예측 연도까지 회귀선과 예측 데이터 연결
for year in range(max(years) + 1, int(prediction_year) + 1):

    chart_data.append({
        "year": year,
        "actual": None,
        "fitted": predict_temperature(year),
        "forecast": predict_temperature(year)
    })


# ==========================================
# 11. 꺾은선 그래프
# ==========================================

st.subheader("📈 과거 기온과 미래 예측 그래프")

st.write(
    f"분석 월: {month_names[selected_month]} "
    f"| 데이터 개수: {n}개 "
    f"| 분석 기간: {min(years)}~{max(years)}년"
)

chart_spec = {

    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",

    "width": "container",
    "height": 450,

    "layer": [

        # 1. 실제 기온과 회귀선 사이의 오차
        {
            "transform": [
                {
                    "filter": "isValid(datum.actual)"
                }
            ],

            "mark": {
                "type": "rule",
                "color": "#BDBDBD",
                "strokeDash": [3, 3]
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도"
                },
                "y": {
                    "field": "actual",
                    "type": "quantitative",
                    "title": "평균기온 (℃)"
                },
                "y2": {
                    "field": "fitted"
                }
            }
        },

        # 2. 과거 실제 기온 빨간색 꺾은선
        {
            "transform": [
                {
                    "filter": "isValid(datum.actual)"
                }
            ],

            "mark": {
                "type": "line",
                "color": "red",
                "strokeWidth": 3,
                "point": False
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도"
                },
                "y": {
                    "field": "actual",
                    "type": "quantitative",
                    "title": "평균기온 (℃)"
                },
                "tooltip": [
                    {
                        "field": "year",
                        "title": "연도"
                    },
                    {
                        "field": "actual",
                        "title": "실제 평균기온",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 3. 선형회귀 파란색 점선
        {
            "mark": {
                "type": "line",
                "color": "blue",
                "strokeWidth": 3,
                "strokeDash": [7, 5]
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도"
                },
                "y": {
                    "field": "fitted",
                    "type": "quantitative"
                },
                "tooltip": [
                    {
                        "field": "year",
                        "title": "연도"
                    },
                    {
                        "field": "fitted",
                        "title": "회귀선 기온",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 4. 미래 예측 주황색 꺾은선
        {
            "transform": [
                {
                    "filter": "isValid(datum.forecast)"
                }
            ],

            "mark": {
                "type": "line",
                "color": "orange",
                "strokeWidth": 4
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도"
                },
                "y": {
                    "field": "forecast",
                    "type": "quantitative",
                    "title": "평균기온 (℃)"
                },
                "tooltip": [
                    {
                        "field": "year",
                        "title": "예측 연도"
                    },
                    {
                        "field": "forecast",
                        "title": "예측 평균기온",
                        "format": ".2f"
                    }
                ]
            }
        }
    ],

    "config": {
        "axis": {
            "labelFontSize": 12,
            "titleFontSize": 14,
            "grid": True
        }
    }
}

st.vega_lite_chart(
    chart_data,
    chart_spec,
    use_container_width=True
)


# ==========================================
# 12. 그래프 범례
# ==========================================

st.markdown("""
**📌 그래프 범례**

- 🔴 빨간색 꺾은선: 과거 실제 평균기온
- 🔵 파란색 점선: 선형회귀 추세선
- 🟠 주황색 꺾은선: 미래 예측 기온
- 회색 세로 점선: 실제 기온과 회귀선 사이의 오차
""")
