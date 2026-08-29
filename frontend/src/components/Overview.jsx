import {
    useEffect,
    useState
} from "react";

import {
    getDashboardSummary
} from "../services/api";


function Overview({
    openInvestigation,
    setActivePage
}) {

    const [data, setData] =
        useState(null);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");


    useEffect(() => {

        async function loadDashboard() {

            try {

                setLoading(true);

                const result =
                    await getDashboardSummary();

                setData(result);

            } catch (err) {

                setError(
                    err.message
                );

            } finally {

                setLoading(false);

            }

        }


        loadDashboard();

    }, []);


    if (loading) {

        return (

            <div className="page-loading">

                Loading risk intelligence...

            </div>

        );

    }


    if (error) {

        return (

            <div className="page-error">

                {error}

            </div>

        );

    }


    const summary = data || {};


    return (

        <div className="page">

            <div className="page-header">

                <div>

                    <p className="eyebrow">
                        RISK OPERATIONS
                    </p>


                    <h2>
                        Overview
                    </h2>


                    <p className="page-description">

                        Monitor transaction risk,
                        suspicious activity and
                        investigation queues.

                    </p>

                </div>

            </div>


            <div className="metrics-grid">

                <MetricCard
                    label="Total Transactions"
                    value={
                        summary.total_transactions
                    }
                    description="Transactions monitored"
                />


                <MetricCard
                    label="Flagged Transactions"
                    value={
                        summary.flagged_transactions
                    }
                    description="Requires attention"
                />


                <MetricCard
                    label="High Risk"
                    value={
                        summary.high_risk
                    }
                    description="Elevated fraud probability"
                    danger
                />


                <MetricCard
                    label="Under Review"
                    value={
                        summary.under_review
                    }
                    description="Manual investigation queue"
                />

            </div>


            <div className="overview-grid">

                <section className="panel">

                    <div className="panel-title">

                        <div>

                            <p className="section-eyebrow">
                                RISK DISTRIBUTION
                            </p>


                            <h3>
                                Transaction risk levels
                            </h3>

                        </div>

                    </div>


                    <div className="distribution">

                        <RiskDistribution
                            label="Low Risk"
                            value={
                                summary.risk_distribution?.LOW
                            }
                            type="low"
                        />


                        <RiskDistribution
                            label="Medium Risk"
                            value={
                                summary.risk_distribution?.MEDIUM
                            }
                            type="medium"
                        />


                        <RiskDistribution
                            label="High Risk"
                            value={
                                summary.risk_distribution?.HIGH
                            }
                            type="high"
                        />

                    </div>

                </section>


                <section className="panel">

                    <div className="panel-title">

                        <div>

                            <p className="section-eyebrow">
                                MODEL QUALITY
                            </p>


                            <h3>
                                Investigation signal
                            </h3>

                        </div>

                    </div>


                    <div className="quality-score">

                        <span>
                            Estimated false positive rate
                        </span>


                        <strong>

                            {
                                summary.false_positive_rate
                            }%

                        </strong>


                        <p>

                            Transactions flagged by
                            the current risk threshold
                            that appear non-fraudulent
                            in the evaluation dataset.

                        </p>

                    </div>

                </section>

            </div>


            <section className="panel suspicious-panel">

                <div className="panel-title">

                    <div>

                        <p className="section-eyebrow">
                            PRIORITY QUEUE
                        </p>


                        <h3>
                            Highest-risk transactions
                        </h3>

                    </div>


                    <button
                        className="text-button"
                        onClick={() =>
                            setActivePage(
                                "transactions"
                            )
                        }
                    >

                        View all →

                    </button>

                </div>


                <TransactionTable
                    transactions={
                        summary.recent_suspicious || []
                    }
                    onSelect={
                        openInvestigation
                    }
                />

            </section>

        </div>

    );

}


function MetricCard({
    label,
    value,
    description,
    danger = false
}) {

    return (

        <div className="metric-card">

            <p>
                {label}
            </p>


            <strong
                className={
                    danger
                        ? "danger-value"
                        : ""
                }
            >

                {Number(
                    value || 0
                ).toLocaleString("en-IN")}

            </strong>


            <span>
                {description}
            </span>

        </div>

    );

}


function RiskDistribution({
    label,
    value,
    type
}) {

    const percentage =
        Number(value || 0);


    return (

        <div className="distribution-item">

            <div className="distribution-label">

                <span>
                    {label}
                </span>


                <strong>
                    {percentage}%
                </strong>

            </div>


            <div className="distribution-track">

                <div
                    className={
                        `distribution-fill ${type}`
                    }
                    style={{
                        width:
                            `${percentage}%`
                    }}
                />

            </div>

        </div>

    );

}


function TransactionTable({
    transactions,
    onSelect
}) {

    if (!transactions.length) {

        return (

            <div className="empty-table">

                No suspicious transactions found.

            </div>

        );

    }


    return (

        <div className="table-wrapper">

            <table>

                <thead>

                    <tr>

                        <th>
                            Transaction
                        </th>

                        <th>
                            Customer
                        </th>

                        <th>
                            Amount
                        </th>

                        <th>
                            Risk
                        </th>

                        <th>
                            Primary signal
                        </th>

                    </tr>

                </thead>


                <tbody>

                    {transactions.map(
                        (transaction) => (

                            <tr
                                key={
                                    transaction.transaction_id
                                }
                                onClick={() =>
                                    onSelect(
                                        transaction.transaction_id
                                    )
                                }
                                className="clickable-row"
                            >

                                <td>

                                    <code>
                                        {
                                            transaction
                                                .transaction_id
                                                .slice(0, 12)
                                        }...
                                    </code>

                                </td>


                                <td>

                                    {
                                        transaction.customer_id
                                    }

                                </td>


                                <td className="amount">

                                    ₹
                                    {
                                        Number(
                                            transaction.amount
                                        ).toLocaleString(
                                            "en-IN"
                                        )
                                    }

                                </td>


                                <td>

                                    <RiskBadge
                                        level={
                                            transaction.risk_level
                                        }
                                    />

                                </td>


                                <td>

                                    {
                                        transaction.reason
                                    }

                                </td>

                            </tr>

                        )
                    )}

                </tbody>

            </table>

        </div>

    );

}


export function RiskBadge({
    level
}) {

    return (

        <span
            className={
                `risk-badge ${
                    String(
                        level
                    ).toLowerCase()
                }`
            }
        >

            {level}

        </span>

    );

}


export default Overview;