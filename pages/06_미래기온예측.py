
# ==========================================
# 10. 그래프 데이터 생성
# ==========================================

chart_data = []

# 회귀선 데이터
for year in range(min(years), int(prediction_year) + 1):

    chart_data.append({
        "year": year,
        "actual": None,
        "fitted": predict_temperature(year),
        "forecast": None
    })


# 실제 평균기온 데이터
for year, temperature in zip(years, temperatures):

    chart_data.append({
        "year": year,
        "actual": temperature,
        "fitted": None,
        "forecast": None
    })


# 미래 예측 데이터
chart_data.append({
    "year": latest_year,
    "actual": None,
    "fitted": None,
    "forecast": temperatures[years.index(latest_year)]
})

chart_data.append({
    "year": int(prediction_year),
    "actual": None,
    "fitted": None,
    "forecast": predicted_temperature
})


# ==========================================
# 11. 그래프 그리기
# ==========================================

st.subheader("📈 서울 월별 평균기온 및 미래 예측")

st.write(
    f"선택한 월: {month_names[selected_month]} | "
    f"분석 기간: {min(years)}~{latest_year}년"
)

chart_spec = {

    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",

    "data": {
        "values": chart_data
    },

    "width": "container",
    "height": 500,

    "layer": [

        # 1. 실제 평균기온 빨간색 실선
        {
            "transform": [
                {"filter": "isValid(datum.actual)"}
            ],

            "mark": {
                "type": "line",
                "color": "#E53935",
                "strokeWidth": 3,
                "point": False
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "title": "연도",
                    "scale": {
                        "domain": [1907, 2100],
                        "nice": False
                    },
                    "axis": {
                        "values": [1907, 1920, 1940, 1960,
                                   1980, 2000, 2020, 2040,
                                   2060, 2080, 2100],
                        "labelAngle": -45
                    }
                },

                "y": {
                    "field": "actual",
                    "type": "quantitative",
                    "title": "평균기온 (℃)"
                },

                "tooltip": [
                    {"field": "year", "title": "연도"},
                    {
                        "field": "actual",
                        "title": "실제 평균기온",
                        "format": ".2f"
                    }
                ]
            }
        },

        # 2. 실제 데이터 회색 점
        {
            "transform": [
                {"filter": "isValid(datum.actual)"}
            ],

            "mark": {
                "type": "point",
                "filled": True,
                "color": "#808080",
                "size": 65
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "scale": {
                        "domain": [1907, 2100],
                        "nice": False
                    }
                },

                "y": {
                    "field": "actual",
                    "type": "quantitative"
                },

                "tooltip": [
                    {"field": "year", "title": "연도"},
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
            "transform": [
                {"filter": "isValid(datum.fitted)"}
            ],

            "mark": {
                "type": "line",
                "color": "#2563EB",
                "strokeWidth": 3,
                "strokeDash": [7, 5]
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "scale": {
                        "domain": [1907, 2100],
                        "nice": False
                    }
                },

                "y": {
                    "field": "fitted",
                    "type": "quantitative"
                }
            }
        },

        # 4. 미래 예측 주황색 선
        {
            "transform": [
                {"filter": "isValid(datum.forecast)"}
            ],

            "mark": {
                "type": "line",
                "color": "#FF9800",
                "strokeWidth": 4
            },

            "encoding": {
                "x": {
                    "field": "year",
                    "type": "quantitative",
                    "scale": {
                        "domain": [1907, 2100],
                        "nice": False
                    }
                },

                "y": {
                    "field": "forecast",
                    "type": "quantitative"
                }
            }
        }
    ],

    "config": {
        "axis": {
            "grid": True,
            "labelFontSize": 11,
            "titleFontSize": 14
        }
    }
}

st.vega_lite_chart(
    None,
    chart_spec,
    use_container_width=True
)


# ==========================================
# 12. 그래프 범례
# ==========================================

st.markdown("""
### 📌 그래프 범례

🔴 빨간색 실선: 실제 월별 평균기온

⚫ 회색 점: 실제 관측 데이터

🔵 파란색 점선: 선형회귀 추세선

🟠 주황색 선: 미래 예측 기온
""")
