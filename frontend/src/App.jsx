import { useState } from "react";
import "./App.css";


function App() {

    const [transactionId, setTransactionId] = useState("");
    const [investigation, setInvestigation] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");


    async function investigate() {

        if (!transactionId.trim()) {
            setError("Enter a transaction ID.");
            return;
        }

        setLoading(true);
        setError("");
        setInvestigation(null);

        try {

            const response = await fetch(
                `/api/investigate/${transactionId.trim()}`
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

            console.log("Investigation response:", data);

            setInvestigation(data);

        } catch (err) {

            console.error("Investigation error:", err);

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
                            Explainable Fraud Intelligence
                        </span>

                    </div>

                </div>


                <div className="system-status">

                    <span className="status-dot"></span>

                    SYSTEM ONLINE

                </div>

            </header>


            <main className="main">

                <section className="hero">

                    <p className="eyebrow">
                        AI FRAUD INVESTIGATION CONSOLE
                    </p>


                    <h2>
                        Investigate suspicious
                        <br />
                        transactions.
                    </h2>


                    <p className="hero-text">

                        Understand exactly why a transaction
                        was flagged — with AI-backed evidence,
                        behavioral analysis and recommended
                        action.

                    </p>

                </section>


                <section className="search-card">

                    <p className="search-label">
                        TRANSACTION INVESTIGATION
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

                                if (
                                    event.key === "Enter"
                                ) {
                                    investigate();
                                }

                            }}
                            placeholder="Enter transaction ID..."
                        />


                        <button
                            onClick={investigate}
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

                </section>


                {!investigation && !loading && (

                    <section className="empty-state">

                        <div className="empty-icon">
                            ◈
                        </div>


                        <h3>
                            Ready for investigation
                        </h3>


                        <p>

                            Enter a transaction ID above
                            to begin an AI-powered fraud
                            investigation.

                        </p>

                    </section>

                )}


                {loading && (

                    <section className="loading-state">

                        <div className="loader"></div>


                        <h3>
                            AI investigation in progress
                        </h3>


                        <p>

                            Analyzing transaction behavior,
                            risk signals and historical
                            patterns...

                        </p>

                    </section>

                )}


                {investigation && (

                    <InvestigationPanel
                        data={investigation}
                    />

                )}

            </main>

        </div>

    );
}



function InvestigationPanel({ data }) {

    const transaction =
        data.transaction || {};


    const riskLevel =
        String(
            data.risk_level || "UNKNOWN"
        ).toLowerCase();


    const riskScore =
        Number(
            data.risk_score || 0
        );


    const explanations =
        Array.isArray(data.explanations)
            ? data.explanations
            : [];


    const comparisons =
        Array.isArray(data.behavior_comparison)
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
                        Transaction
                    </h2>


                    <code>
                        {data.transaction_id}
                    </code>

                </div>


                <div
                    className={`risk-badge ${riskLevel}`}
                >

                    {data.risk_level}

                </div>

            </div>


            <div className="risk-grid">

                <div className="risk-card">

                    <p>
                        AI RISK SCORE
                    </p>


                    <div className="risk-score">

                        {riskScore.toFixed(1)}

                        <span>
                            /100
                        </span>

                    </div>


                    <div className="risk-bar">

                        <div
                            className={`risk-fill ${riskLevel}`}
                            style={{
                                width:
                                    `${Math.min(
                                        riskScore,
                                        100
                                    )}%`
                            }}
                        />

                    </div>

                </div>


                <div className="transaction-card">

                    <p>
                        TRANSACTION
                    </p>


                    <strong>

                        ₹
                        {Number(
                            transaction.amount || 0
                        ).toLocaleString("en-IN")}

                    </strong>


                    <span>

                        {transaction.payment_method ||
                            "Unknown"}

                        {" • "}

                        {transaction.merchant_category ||
                            "Unknown"}

                    </span>

                </div>


                <div className="action-card">

                    <p>
                        RECOMMENDED ACTION
                    </p>


                    <strong>

                        {formatAction(
                            data.recommended_action
                        )}

                    </strong>

                </div>

            </div>


            <div className="details-grid">

                <div className="panel">

                    <div className="panel-header">

                        <div>

                            <p className="section-label">
                                MODEL EVIDENCE
                            </p>


                            <h3>
                                Why was this flagged?
                            </h3>

                        </div>


                        <span className="ai-tag">
                            AI
                        </span>

                    </div>


                    <div className="explanations">

                        {explanations.length === 0 && (

                            <p className="no-data">
                                No explanation signals
                                were returned.
                            </p>

                        )}


                        {explanations.map(
                            (item, index) => (

                                <div
                                    className="explanation"
                                    key={index}
                                >

                                    <div
                                        className={`severity ${String(
                                            item.severity ||
                                            "medium"
                                        ).toLowerCase()}`}
                                    >
                                        !
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

                            )
                        )}

                    </div>

                </div>


                <div className="panel">

                    <div className="panel-header">

                        <div>

                            <p className="section-label">
                                BEHAVIORAL ANALYSIS
                            </p>


                            <h3>
                                Normal vs current
                            </h3>

                        </div>

                    </div>


                    <div className="comparison">

                        {comparisons.length === 0 && (

                            <p className="no-data">
                                Behavioral comparison
                                unavailable.
                            </p>

                        )}


                        {comparisons.map(
                            (item, index) => (

                                <div
                                    className="comparison-row"
                                    key={index}
                                >

                                    <div>
                                        {item.signal ||
                                            "Signal"}
                                    </div>


                                    <div>
                                        {item.normal ||
                                            "—"}
                                    </div>


                                    <div>
                                        {item.current ||
                                            "—"}
                                    </div>

                                </div>

                            )
                        )}

                    </div>

                </div>

            </div>


            <div className="transaction-info">

                <div>

                    <span>
                        CUSTOMER
                    </span>


                    <strong>
                        {transaction.customer_id ||
                            "Unknown"}
                    </strong>

                </div>


                <div>

                    <span>
                        LOCATION
                    </span>


                    <strong>
                        {transaction.country ||
                            transaction.ip_country ||
                            "Unknown"}
                    </strong>

                </div>


                <div>

                    <span>
                        MERCHANT
                    </span>


                    <strong>
                        {transaction.merchant_category ||
                            "Unknown"}
                    </strong>

                </div>


                <div>

                    <span>
                        TIMESTAMP
                    </span>


                    <strong>
                        {transaction.timestamp ||
                            "Unknown"}
                    </strong>

                </div>

            </div>

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
            (letter) =>
                letter.toUpperCase()
        );
}



export default App;