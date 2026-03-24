"""
visualization.py
----------------
Three Plotly chart functions. Each returns fig.to_json() — a JSON string
the frontend parses and passes directly to Plotly.js.

Charts:
  create_sentiment_trend_chart(responses_over_time) → line chart of sentiment over time
  create_sentiment_chart(sentiment)                 → donut chart of sentiment distribution
  create_sentiment_gauge(avg_score)                 → gauge showing overall mood (-1 to +1)
"""

import plotly.graph_objects as go

COLORS = {
    "positive": "#22c55e",
    "negative": "#ef4444",
    "neutral":  "#94a3b8",
    "bars":     ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd"],
}


def create_sentiment_trend_chart(responses_over_time: list) -> str:
    """
    Line chart showing customer sentiment score over time.
    Each point = one response that had text feedback.
    responses_over_time = [{"time": str, "score": float, "option": str}, ...]
    Green zone = positive, red zone = negative, grey = neutral.
    Dashed purple line = moving average trend.
    """
    if not responses_over_time:
        fig = go.Figure()
        fig.update_layout(
            annotations=[dict(
                text="Submit responses with comments to see sentiment trend",
                showarrow=False,
                font=dict(size=13, color="#94a3b8"),
                xref="paper", yref="paper", x=0.5, y=0.5
            )],
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=20, b=20, l=20, r=20),
        )
        return fig.to_json()

    times   = [r["time"]   for r in responses_over_time]
    scores  = [r["score"]  for r in responses_over_time]
    options = [r["option"] for r in responses_over_time]

    point_colors = [
        "#22c55e" if s > 0.1 else "#ef4444" if s < -0.1 else "#94a3b8"
        for s in scores
    ]

    fig = go.Figure()

    # Sentiment zone shading
    fig.add_hrect(y0=0.1,  y1=1.1,  fillcolor="#dcfce7", opacity=0.25, line_width=0)
    fig.add_hrect(y0=-1.1, y1=-0.1, fillcolor="#fee2e2", opacity=0.25, line_width=0)
    fig.add_hrect(y0=-0.1, y1=0.1,  fillcolor="#f8fafc", opacity=0.5,  line_width=0)

    # Zero baseline
    fig.add_hline(y=0, line_dash="dot", line_color="#cbd5e1", line_width=1)

    # Sentiment line + points
    fig.add_trace(go.Scatter(
        x=times, y=scores,
        mode="lines+markers",
        line=dict(color="#6366f1", width=2, shape="spline"),
        marker=dict(color=point_colors, size=9, line=dict(width=1.5, color="white")),
        hovertemplate="<b>Option: %{customdata}</b><br>Sentiment: %{y:.2f}<extra></extra>",
        customdata=options,
        name="Sentiment",
    ))

    # Moving average trend line (needs 3+ points)
    if len(scores) >= 3:
        window = min(5, len(scores))
        ma = [
            round(sum(scores[max(0, i-window+1):i+1]) / min(window, i+1), 3)
            for i in range(len(scores))
        ]
        fig.add_trace(go.Scatter(
            x=times, y=ma,
            mode="lines",
            line=dict(color="#a78bfa", width=2, dash="dash"),
            name="Trend (avg)",
            hoverinfo="skip",
        ))

    fig.update_layout(
        xaxis_title="Response time",
        yaxis_title="Sentiment",
        yaxis=dict(
            range=[-1.1, 1.1],
            gridcolor="#f1f5f9",
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"],
            tickfont=dict(size=10),
        ),
        xaxis=dict(gridcolor="#f1f5f9", tickangle=-30, tickfont=dict(size=10)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        margin=dict(t=20, b=60, l=100, r=20),
        legend=dict(orientation="h", y=1.08, x=0),
        showlegend=True,
    )
    return fig.to_json()


def create_sentiment_chart(sentiment: dict) -> str:
    """Donut chart — sentiment distribution."""
    labels = list(sentiment.keys())
    values = list(sentiment.values())
    colors = [COLORS.get(label, "#94a3b8") for label in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo="label+percent",
    )])

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=13),
        margin=dict(t=10, b=20, l=20, r=20),
        showlegend=False,
    )
    return fig.to_json()


def create_sentiment_gauge(avg_score: float | None) -> str:
    """Gauge chart — single-number mood meter from -1.0 to +1.0."""
    score = avg_score if avg_score is not None else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(score, 2),
        number=dict(suffix="  mood score"),
        gauge=dict(
            axis=dict(range=[-1, 1], tickvals=[-1, -0.5, 0, 0.5, 1]),
            bar=dict(color="#6366f1"),
            steps=[
                dict(range=[-1,    -0.05], color="#fee2e2"),
                dict(range=[-0.05,  0.05], color="#f1f5f9"),
                dict(range=[ 0.05,  1   ], color="#dcfce7"),
            ],
            threshold=dict(
                line=dict(color="#1e293b", width=2),
                thickness=0.75,
                value=score,
            ),
        ),
        title=dict(text="Average Sentiment"),
    ))

    fig.update_layout(
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=13),
        margin=dict(t=60, b=20, l=40, r=40),
        height=280,
    )
    return fig.to_json()
