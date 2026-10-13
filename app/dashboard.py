import httpx
import pandas as pd
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="SENTINEL | Reliability Dashboard",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ SENTINEL")
st.subheader("Software Reliability Dashboard")
st.caption("Live request monitoring and reliability metrics")

if st.button("Refresh dashboard"):
    st.rerun()

try:
    metrics_response = httpx.get(
        f"{API_BASE_URL}/monitoring/metrics",
        timeout=5.0,
    )
    metrics_response.raise_for_status()
    metrics = metrics_response.json()

    history_response = httpx.get(
        f"{API_BASE_URL}/monitoring/requests",
        params={"limit": 50},
        timeout=5.0,
    )
    history_response.raise_for_status()
    history = history_response.json()["requests"]

except httpx.HTTPError as exc:
    st.error(
        "Could not connect to SENTINEL API. "
        "Make sure the FastAPI server is running on port 8000."
    )
    st.code(str(exc))
    st.stop()

# Main reliability metrics
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Total Requests",
    metrics["total_requests"],
)

col2.metric(
    "Server Failures",
    metrics["failed_requests"],
)

col3.metric(
    "Failure Rate",
    f'{metrics["failure_rate_percent"]:.2f}%',
)

col4.metric(
    "Avg Response Time",
    f'{metrics["avg_response_time_ms"]:.2f} ms',
)

col5.metric(
    "P95 Latency",
    f'{metrics["p95_response_time_ms"]:.2f} ms',
)

st.divider()

# Request history
st.subheader("Recent Request History")

if history:
    dataframe = pd.DataFrame(history)

    display_columns = [
        "id",
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "created_at",
    ]

    dataframe = dataframe[display_columns]

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("Fault Injection Lab")
    st.caption("Safely simulate failures in the local demo API.")

    try:
        fault_response = httpx.get(
            f"{API_BASE_URL}/demo/faults",
            timeout=5.0,
        )
        fault_response.raise_for_status()
        fault_state = fault_response.json()

        active_fault = fault_state["type"]

        if active_fault == "none":
            st.success("System status: Normal")
        else:
            st.warning(f"Active fault: {active_fault}")

        fault_col1, fault_col2, fault_col3 = st.columns(3)

        with fault_col1:
            if st.button("Inject HTTP 503", use_container_width=True):
                response = httpx.post(
                    f"{API_BASE_URL}/demo/faults/http-503",
                    timeout=5.0,
                )
                response.raise_for_status()
                st.success("HTTP 503 fault enabled.")
                st.rerun()

        with fault_col2:
            if st.button("Inject 1s Latency", use_container_width=True):
                response = httpx.post(
                    f"{API_BASE_URL}/demo/faults/latency",
                    params={"delay_seconds": 1.0},
                    timeout=5.0,
                )
                response.raise_for_status()
                st.success("Latency fault enabled.")
                st.rerun()

        with fault_col3:
            if st.button("Clear Faults", use_container_width=True):
                response = httpx.delete(
                    f"{API_BASE_URL}/demo/faults",
                    timeout=5.0,
                )
                response.raise_for_status()
                st.success("All faults cleared.")
                st.rerun()

    except httpx.HTTPError as exc:
        st.error("Could not load fault controls.")
        st.caption(str(exc))


    st.divider()

    st.subheader("Reliability Analytics")

    chart_col1, chart_col2 = st.columns(2)

    # Chart 1: Request count by HTTP status code
    with chart_col1:
        st.markdown("#### Requests by Status Code")

        status_counts = (
            dataframe.groupby("status_code")
            .size()
            .reset_index(name="requests")
            .set_index("status_code")
        )

        st.bar_chart(status_counts)

    # Chart 2: Response time across recent requests
    with chart_col2:
        st.markdown("#### Response Time Trend")

        latency_data = (
            dataframe.sort_values("id")
            .set_index("id")[["duration_ms"]]
        )

        st.line_chart(latency_data)

else:
    st.info("No requests have been recorded yet.")

st.caption(
    "Data source: SENTINEL FastAPI monitoring endpoints "
    "backed by SQLite."
)
