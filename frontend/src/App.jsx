import { useEffect, useState } from "react";
import "./App.css";


function App() {

    const [section, setSection] = useState("overview");
    const [transactionId, setTransactionId] = useState("");
    const [investigation, setInvestigation] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");


    function openInvestigation(id) {

        setTransactionId(id);
        setSection("investigate");
        investigate(id);
    }


    async function investigate(id) {

        const lookup = (id || transactionId).trim();

        if (!lookup) {
            setError("Enter a transaction ID.");
            return;
        }

        setLoading(true);
        setError("");
        setInvestigation(null);

        try {

            const response = await fetch(
                `/api/investigate/${lookup}`
            );

            if (!response.ok) {

                let message = "Transaction investigation failed.";

                try {
                    const errorData = await response.json();

                    if (errorData.detail) {
                        message = errorData.detail;
                    }

                } catch {
                    // Ignore invalid error response
                }

                throw new Error(message);
            }

            const data = await response.json();

            setInvestigation(data);

        } catch (err) {

            setError(
                err.message ||
                "Unable to connect to Shield-AI backend."
            );

        } finally {

            setLoading(false);
        }
    }


    return (

        <div className="app">

            <header className="navbar">

                <div className="brand">

                    <div className="brand-icon">
                        S
                    </div>

                    <div>

                        <h1>
                            SHIELD-AI
                        </h1>

                        <span>
                            Fraud & Risk Intelligence
                        </span>

                    </div>

                </div>

                <div className="system-status">

                    <span className="status-dot"></span>

                    SYSTEM OPERATIONAL

                </div>

            </header>


            <div className="shell">

                <nav className="sidebar">

                    <p className="nav-label">
                        OPERATIONS
                    </p>

                    <NavButton
                        id="overview"
                        label="Overview"
                        current={section}
                        onSelect={setSection}
                    />

                    <NavButton
                        id="transactions"
                        label="Transactions"
                        current={section}
                        onSelect={setSection}
                    />

                    <NavButton
                        id="investigate"
                        label="Investigate"
                        current={section}
                        onSelect={setSection}
                    />

                    <NavButton
                        id="analytics"
                        label="Analytics"
                        current={section}
                        onSelect={setSection}
                    />

                    <NavButton
                        id="settings"
                        label="Settings"
                        current={section}
                        onSelect={setSection}
                    />

                </nav>


                <main className="workspace">

                    {section === "overview" && (

                        <OverviewPage
                            onOpen={openInvestigation}
                        />

                    )}


                    {section === "transactions" && (

                        <TransactionsPage
                            onOpen={openInvestigation}
                        />

                    )}


                    {section === "investigate" && (

                        <InvestigatePage
                            transactionId={transactionId}
                            setTransactionId={setTransactionId}
                            investigation={investigation}
                            loading={loading}
                            error={error}
                            onInvestigate={() =>
                                investigate()
                            }
                        />

                    )}


                    {section === "analytics" && (
                        <AnalyticsPage />
                    )}


                    {section === "settings" && (
                        <SettingsPage />
                    )}

                </main>

            </div>

        </div>

    );
}


function NavButton({ id, label, current, onSelect }) {

    return (

        <button
            className={
                current === id
                    ? "nav-btn active"
                    : "nav-btn"
            }
            onClick={() => onSelect(id)}
        >
            {label}
        </button>

    );
}


function OverviewPage({ onOpen }) {

    const [summary, setSummary] = useState(null);
    const [error, setError] = useState("");


    useEffect(() => {

        fetch("/api/dashboard/summary")
            .then(async (response) => {

                if (!response.ok) {
                    throw new Error("Dashboard failed to load.");
                }

                return response.json();
            })
            .then(setSummary)
            .catch((err) =>
                setError(err.message)
            );

    }, []);


    if (error) {
        return <p className="error">{error}</p>;
    }


    if (!summary) {
        return <LoadingState text="Loading risk overview..." />;
    }


    const dist = summary.risk_distribution || {};


    return (

        <section>

            <p className="eyebrow">
                TODAY'S RISK OVERVIEW
            </p>

            <h2 className="page-title">
                Risk operations
            </h2>


            <div className="stat-grid">

                <StatCard
                    label="Total"
                    value={formatNumber(
                        summary.total_transactions
                    )}
                />

                <StatCard
                    label="Flagged"
                    value={formatNumber(
                        summary.flagged_transactions
                    )}
                />

                <StatCard
                    label="High risk"
                    value={formatNumber(
                        summary.high_risk
                    )}
                    tone="high"
                />

                <StatCard
                    label="Under review"
                    value={formatNumber(
                        summary.under_review
                    )}
                />

                <StatCard
                    label="False positive rate"
                    value={`${summary.false_positive_rate}%`}
                />

            </div>


            <div className="panel">

                <p className="section-label">
                    RISK DISTRIBUTION
                </p>

                <div className="distribution">

                    <DistributionBar
                        label="LOW"
                        value={dist.LOW}
                        tone="low"
                    />

                    <DistributionBar
                        label="MEDIUM"
                        value={dist.MEDIUM}
                        tone="medium"
                    />

                    <DistributionBar
                        label="HIGH"
                        value={dist.HIGH}
                        tone="high"
                    />

                </div>

            </div>


            <div className="panel">

                <p className="section-label">
                    TRANSACTION QUEUE
                </p>

                <TransactionTable
                    rows={summary.recent_suspicious || []}
                    onOpen={onOpen}
                />

            </div>

        </section>

    );
}


function TransactionsPage({ onOpen }) {

    const [query, setQuery] = useState("");
    const [risk, setRisk] = useState("ALL");
    const [offset, setOffset] = useState(0);
    const [data, setData] = useState(null);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);

    const limit = 25;


    useEffect(() => {

        const params = new URLSearchParams({
            query,
            risk,
            limit: String(limit),
            offset: String(offset)
        });

        setLoading(true);

        fetch(`/api/transactions?${params}`)
            .then(async (response) => {

                if (!response.ok) {
                    throw new Error("Unable to load transactions.");
                }

                return response.json();
            })
            .then(setData)
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));

    }, [query, risk, offset]);


    return (

        <section>

            <p className="eyebrow">
                TRANSACTIONS
            </p>

            <h2 className="page-title">
                Live transaction queue
            </h2>


            <div className="toolbar">

                <input
                    value={query}
                    onChange={(event) => {
                        setOffset(0);
                        setQuery(event.target.value);
                    }}
                    placeholder="Search transaction or customer..."
                />

                {["ALL", "HIGH", "MEDIUM", "LOW"].map((level) => (

                    <button
                        key={level}
                        className={
                            risk === level
                                ? "filter-btn active"
                                : "filter-btn"
                        }
                        onClick={() => {
                            setOffset(0);
                            setRisk(level);
                        }}
                    >
                        {level === "ALL" ? "All" : level}
                    </button>

                ))}

            </div>


            {error && <p className="error">{error}</p>}


            {loading && !data && (
                <LoadingState text="Loading transactions..." />
            )}


            {data && (

                <>

                    <p className="result-count">

                        {formatNumber(data.total)} transactions

                    </p>

                    <TransactionTable
                        rows={data.transactions || []}
                        onOpen={onOpen}
                    />

                    <div className="pager">

                        <button
                            disabled={offset === 0}
                            onClick={() =>
                                setOffset(
                                    Math.max(0, offset - limit)
                                )
                            }
                        >
                            Previous
                        </button>

                        <span>

                            {offset + 1}
                            –
                            {Math.min(
                                offset + limit,
                                data.total
                            )}

                        </span>

                        <button
                            disabled={
                                offset + limit >= data.total
                            }
                            onClick={() =>
                                setOffset(offset + limit)
                            }
                        >
                            Next
                        </button>

                    </div>

                </>

            )}

        </section>

    );
}


function InvestigatePage({
    transactionId,
    setTransactionId,
    investigation,
    loading,
    error,
    onInvestigate
}) {

    return (

        <section>

            <p className="eyebrow">
                TRANSACTION INVESTIGATION
            </p>

            <h2 className="page-title">
                AI investigation workspace
            </h2>


            <div className="search-card">

                <p className="search-label">
                    LOOK UP A TRANSACTION
                </p>

                <div className="search-row">

                    <input
                        value={transactionId}
                        onChange={(event) =>
                            setTransactionId(
                                event.target.value
                            )
                        }
                        onKeyDown={(event) => {

                            if (event.key === "Enter") {
                                onInvestigate();
                            }

                        }}
                        placeholder="Enter transaction ID..."
                    />

                    <button
                        onClick={onInvestigate}
                        disabled={loading}
                    >

                        {loading
                            ? "Analyzing..."
                            : "Investigate"}

                    </button>

                </div>

                {error && (
                    <p className="error">
                        {error}
                    </p>
                )}

            </div>


            {!investigation && !loading && (

                <div className="empty-state">

                    <div className="empty-icon">
                        ◈
                    </div>

                    <h3>
                        Select a transaction
                    </h3>

                    <p>

                        Open a row from Transactions, or enter
                        an ID to generate human-readable
                        risk reasoning.

                    </p>

                </div>

            )}


            {loading && (
                <LoadingState text="Analyzing transaction behavior, risk signals and historical patterns..." />
            )}


            {investigation && (
                <InvestigationPanel data={investigation} />
            )}

        </section>

    );
}


function AnalyticsPage() {

    const [data, setData] = useState(null);
    const [error, setError] = useState("");


    useEffect(() => {

        fetch("/api/analytics/risk")
            .then(async (response) => {

                if (!response.ok) {
                    throw new Error("Analytics failed to load.");
                }

                return response.json();
            })
            .then(setData)
            .catch((err) => setError(err.message));

    }, []);


    if (error) {
        return <p className="error">{error}</p>;
    }


    if (!data) {
        return <LoadingState text="Loading analytics..." />;
    }


    const total = data.total_transactions || 1;


    return (

        <section>

            <p className="eyebrow">
                ANALYTICS
            </p>

            <h2 className="page-title">
                Risk trends
            </h2>


            <div className="panel">

                <p className="section-label">
                    RISK COUNTS
                </p>

                {["HIGH", "MEDIUM", "LOW"].map((level) => (

                    <DistributionBar
                        key={level}
                        label={level}
                        value={
                            Math.round(
                                (data.counts?.[level] || 0)
                                / total
                                * 1000
                            ) / 10
                        }
                        tone={level.toLowerCase()}
                    />

                ))}

            </div>


            <div className="details-grid">

                <div className="panel">

                    <p className="section-label">
                        FLAGGED REASONS
                    </p>

                    {(data.flagged_reasons || []).map((item) => (

                        <div
                            className="metric-row"
                            key={item.reason}
                        >

                            <span>{item.reason}</span>

                            <strong>
                                {formatNumber(item.count)}
                            </strong>

                        </div>

                    ))}

                </div>


                <div className="panel">

                    <p className="section-label">
                        AVERAGE RISK BY CATEGORY
                    </p>

                    {(data.categories || []).map((item) => (

                        <div
                            className="metric-row"
                            key={item.category}
                        >

                            <span>{item.category}</span>

                            <strong>
                                {item.avg_risk}
                            </strong>

                        </div>

                    ))}

                </div>

            </div>

        </section>

    );
}


function SettingsPage() {

    return (

        <section>

            <p className="eyebrow">
                SETTINGS
            </p>

            <h2 className="page-title">
                Platform configuration
            </h2>


            <div className="panel">

                <div className="metric-row">
                    <span>Dataset</span>
                    <strong>data/raw/transactions.csv</strong>
                </div>

                <div className="metric-row">
                    <span>Model</span>
                    <strong>Random Forest risk engine</strong>
                </div>

                <div className="metric-row">
                    <span>Explanations</span>
                    <strong>Human-readable signal layer</strong>
                </div>

                <div className="metric-row">
                    <span>Investigate API</span>
                    <strong>/api/investigate/{"{id}"}</strong>
                </div>

            </div>

        </section>

    );
}


function TransactionTable({ rows, onOpen }) {

    return (

        <div className="table-wrap">

            <table className="tx-table">

                <thead>

                    <tr>
                        <th>Transaction</th>
                        <th>Amount</th>
                        <th>Customer</th>
                        <th>Risk</th>
                        <th>Status</th>
                        <th>Reason</th>
                    </tr>

                </thead>

                <tbody>

                    {rows.length === 0 && (

                        <tr>
                            <td colSpan={6}>
                                No transactions in this view.
                            </td>
                        </tr>

                    )}

                    {rows.map((row) => (

                        <tr
                            key={row.transaction_id}
                            onClick={() =>
                                onOpen(row.transaction_id)
                            }
                        >

                            <td>
                                <code>
                                    {shortId(row.transaction_id)}
                                </code>
                            </td>

                            <td>
                                ₹
                                {Number(row.amount || 0)
                                    .toLocaleString("en-IN")}
                            </td>

                            <td>{row.customer_id}</td>

                            <td>
                                <span
                                    className={`risk-badge ${String(
                                        row.risk_level || ""
                                    ).toLowerCase()}`}
                                >
                                    {row.risk_level}
                                </span>
                            </td>

                            <td>{row.status}</td>

                            <td>{row.reason || "—"}</td>

                        </tr>

                    ))}

                </tbody>

            </table>

        </div>

    );
}


function InvestigationPanel({ data }) {

    const transaction = data.transaction || {};

    const riskLevel = String(
        data.risk_level || "UNKNOWN"
    ).toLowerCase();

    const riskScore = Number(data.risk_score || 0);

    const explanations = Array.isArray(data.explanations)
        ? data.explanations
        : [];

    const comparisons = Array.isArray(data.behavior_comparison)
        ? data.behavior_comparison
        : [];


    return (

        <section className="investigation">

            <div className="transaction-header">

                <div>

                    <p className="section-label">
                        INVESTIGATION RESULT
                    </p>

                    <h2>
                        ₹
                        {Number(
                            transaction.amount || 0
                        ).toLocaleString("en-IN")}
                    </h2>

                    <code>
                        {data.transaction_id}
                    </code>

                </div>

                <div className={`risk-badge ${riskLevel}`}>
                    {data.risk_level} RISK
                </div>

            </div>


            <div className="risk-grid">

                <div className="risk-card">

                    <p>
                        RISK SCORE
                    </p>

                    <div className="risk-score">

                        {riskScore.toFixed(0)}

                        <span>
                            /100
                        </span>

                    </div>

                    <div className="risk-bar">

                        <div
                            className={`risk-fill ${riskLevel}`}
                            style={{
                                width: `${Math.min(riskScore, 100)}%`
                            }}
                        />

                    </div>

                </div>


                <div className="transaction-card">

                    <p>
                        TRANSACTION
                    </p>

                    <strong>

                        {transaction.payment_method || "Unknown"}

                    </strong>

                    <span>

                        {transaction.merchant_category ||
                            "Unknown"}

                    </span>

                </div>


                <div className="action-card">

                    <p>
                        AI RECOMMENDATION
                    </p>

                    <strong>
                        {formatAction(data.recommended_action)}
                    </strong>

                    <span>

                        Multiple independent behavioral
                        signals indicate elevated fraud risk
                        when several alerts fire together.

                    </span>

                </div>

            </div>


            <div className="details-grid">

                <div className="panel">

                    <div className="panel-header">

                        <div>

                            <p className="section-label">
                                WHY WAS THIS FLAGGED?
                            </p>

                            <h3>
                                Human-readable evidence
                            </h3>

                        </div>

                        <span className="ai-tag">
                            AI
                        </span>

                    </div>

                    <div className="explanations">

                        {explanations.length === 0 && (

                            <p className="no-data">
                                No elevated behavioral
                                signals were returned.
                            </p>

                        )}

                        {explanations.map((item, index) => (

                            <div
                                className="explanation"
                                key={index}
                            >

                                <div className="reason-index">
                                    {String(index + 1).padStart(2, "0")}
                                </div>

                                <div>

                                    <strong>
                                        {item.title}
                                    </strong>

                                    <p>
                                        {item.message}
                                    </p>

                                </div>

                            </div>

                        ))}

                    </div>

                </div>


                <div className="panel">

                    <div className="panel-header">

                        <div>

                            <p className="section-label">
                                CUSTOMER BEHAVIOR
                            </p>

                            <h3>
                                Normal vs current
                            </h3>

                        </div>

                    </div>

                    <div className="comparison">

                        <div className="comparison-row header">
                            <div>SIGNAL</div>
                            <div>NORMAL</div>
                            <div>CURRENT</div>
                        </div>

                        {comparisons.length === 0 && (

                            <p className="no-data">
                                Behavioral comparison
                                unavailable.
                            </p>

                        )}

                        {comparisons.map((item, index) => (

                            <div
                                className="comparison-row"
                                key={index}
                            >

                                <div>
                                    {item.signal || "Signal"}
                                </div>

                                <div>
                                    {item.normal || "—"}
                                </div>

                                <div>
                                    {item.current || "—"}
                                </div>

                            </div>

                        ))}

                    </div>

                </div>

            </div>


            <div className="transaction-info">

                <div>
                    <span>CUSTOMER</span>
                    <strong>
                        {transaction.customer_id || "Unknown"}
                    </strong>
                </div>

                <div>
                    <span>LOCATION</span>
                    <strong>
                        {transaction.country || "Unknown"}
                    </strong>
                </div>

                <div>
                    <span>MERCHANT</span>
                    <strong>
                        {transaction.merchant_category || "Unknown"}
                    </strong>
                </div>

                <div>
                    <span>TIMESTAMP</span>
                    <strong>
                        {transaction.timestamp || "Unknown"}
                    </strong>
                </div>

            </div>

        </section>

    );
}


function StatCard({ label, value, tone }) {

    return (

        <div className={`stat-card ${tone || ""}`}>

            <p>{label}</p>

            <strong>{value}</strong>

        </div>

    );
}


function DistributionBar({ label, value, tone }) {

    return (

        <div className="dist-row">

            <span>{label}</span>

            <div className="dist-track">

                <div
                    className={`dist-fill ${tone}`}
                    style={{ width: `${value || 0}%` }}
                />

            </div>

            <strong>{value}%</strong>

        </div>

    );
}


function LoadingState({ text }) {

    return (

        <section className="loading-state">

            <div className="loader"></div>

            <h3>
                Working
            </h3>

            <p>{text}</p>

        </section>

    );
}


function formatAction(action) {

    if (action === "MANUAL_REVIEW") {
        return "Manual Review";
    }

    if (action === "STEP_UP_VERIFICATION") {
        return "Step-up Verification";
    }

    if (action === "ALLOW") {
        return "Allow Transaction";
    }

    if (!action) {
        return "Review Required";
    }

    return action
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            (letter) => letter.toUpperCase()
        );
}


function formatNumber(value) {

    return Number(value || 0).toLocaleString("en-IN");
}


function shortId(id) {

    const value = String(id || "");

    if (value.length <= 12) {
        return value;
    }

    return `${value.slice(0, 4)}...${value.slice(-4)}`;
}


export default App;
