import {
    useEffect,
    useState
} from "react";

import {
    investigateTransaction
} from "../services/api";


function Investigation({
    transactionId,
    goBack
}) {

    const [data, setData] =
        useState(null);

    const [loading, setLoading] =
        useState(true);

    const [error, setError] =
        useState("");


    useEffect(() => {

        async function investigate() {

            try {

                setLoading(true);

                const result =
                    await investigateTransaction(
                        transactionId
                    );

                setData(result);

            } catch (err) {

                setError(
                    err.message
                );

            } finally {

                setLoading(false);

            }

        }


        if (transactionId) {

            investigate();

        }

    }, [transactionId]);


    if (loading) {

        return (

            <div className="page-loading">

                SHIELD-AI is investigating
                this transaction...

            </div>

        );

    }


    if (error) {

        return (

            <div className="page-error">

                <p>
                    {error}
                </p>


                <button
                    onClick={goBack}
                >

                    Back to transactions

                </button>

            </div>

        );

    }


    const transaction =
        data?.transaction || {};


    return (

        <div className="page investigation-page">

            <button
                className="back-button"
                onClick={goBack}
            >

                ← Back to transactions

            </button>


            <div className="investigation-title">

                <div>

                    <p className="eyebrow">
                        TRANSACTION INVESTIGATION
                    </p>


                    <h2>
                        Investigation report
                    </h2>


                    <code>

                        {transactionId}

                    </code>

                </div>


                <div
                    className={
                        `large-risk ${
                            String(
                                data?.risk_level
                            ).toLowerCase()
                        }`
                    }
                >

                    <span>
                        {data?.risk_level}
                    </span>


                    <strong>

                        {Number(
                            data?.risk_score || 0
                        ).toFixed(0)}

                        <small>
                            /100
                        </small>

                    </strong>

                </div>

            </div>


            <div className="investigation-summary">

                <div>

                    <span>
                        TRANSACTION AMOUNT
                    </span>


                    <strong>

                        ₹
                        {
                            Number(
                                transaction.amount || 0
                            ).toLocaleString(
                                "en-IN"
                            )
                        }

                    </strong>

                </div>


                <div>

                    <span>
                        CUSTOMER
                    </span>


                    <strong>

                        {transaction.customer_id}

                    </strong>

                </div>


                <div>

                    <span>
                        LOCATION
                    </span>


                    <strong>

                        {transaction.country}

                    </strong>

                </div>


                <div>

                    <span>
                        PAYMENT METHOD
                    </span>


                    <strong>

                        {transaction.payment_method}

                    </strong>

                </div>

            </div>


            <section className="panel recommendation-panel">

                <p className="section-eyebrow">

                    AI RECOMMENDATION

                </p>


                <h3>

                    {
                        formatAction(
                            data?.recommended_action
                        )
                    }

                </h3>


                <p>

                    This recommendation is based
                    on the combination of transaction
                    risk signals and deviations from
                    the customer's normal behavior.

                </p>

            </section>


            <div className="investigation-grid">

                <section className="panel">

                    <div className="panel-title">

                        <div>

                            <p className="section-eyebrow">

                                EXPLAINABLE AI

                            </p>


                            <h3>

                                Why was this flagged?

                            </h3>

                        </div>

                    </div>


                    <div className="explanation-list">

                        {
                            data?.explanations
                                ?.map(
                                    (
                                        explanation,
                                        index
                                    ) => (

                                        <div
                                            className="explanation-item"
                                            key={index}
                                        >

                                            <div className="explanation-number">

                                                {String(
                                                    index + 1
                                                ).padStart(
                                                    2,
                                                    "0"
                                                )}

                                            </div>


                                            <div>

                                                <span
                                                    className={
                                                        `severity ${
                                                            String(
                                                                explanation.severity ||
                                                                "medium"
                                                            ).toLowerCase()
                                                        }`
                                                    }
                                                >

                                                    {
                                                        explanation.severity
                                                    }

                                                </span>


                                                <h4>

                                                    {
                                                        explanation.title
                                                    }

                                                </h4>


                                                <p>

                                                    {
                                                        explanation.message
                                                    }

                                                </p>

                                            </div>

                                        </div>

                                    )
                                )
                        }

                    </div>

                </section>


                <section className="panel">

                    <p className="section-eyebrow">

                        BEHAVIOR ANALYSIS

                    </p>


                    <h3>

                        Normal vs current behavior

                    </h3>


                    <div className="behavior-table">

                        <div className="behavior-header">

                            <span>
                                Signal
                            </span>

                            <span>
                                Normal
                            </span>

                            <span>
                                Current
                            </span>

                        </div>


                        {
                            data?.behavior_comparison
                                ?.map(
                                    (
                                        item,
                                        index
                                    ) => (

                                        <div
                                            className="behavior-row"
                                            key={index}
                                        >

                                            <span>

                                                {
                                                    item.signal
                                                }

                                            </span>


                                            <span>

                                                {
                                                    item.normal
                                                }

                                            </span>


                                            <strong>

                                                {
                                                    item.current
                                                }

                                            </strong>

                                        </div>

                                    )
                                )
                        }

                    </div>

                </section>

            </div>


            <section className="panel transaction-details">

                <p className="section-eyebrow">

                    TRANSACTION DETAILS

                </p>


                <div className="details-grid">

                    <Detail
                        label="Transaction ID"
                        value={transactionId}
                    />


                    <Detail
                        label="Merchant Category"
                        value={
                            transaction.merchant_category
                        }
                    />


                    <Detail
                        label="Device ID"
                        value={
                            transaction.device_id
                        }
                    />


                    <Detail
                        label="Timestamp"
                        value={
                            transaction.timestamp
                        }
                    />

                </div>

            </section>

        </div>

    );

}


function Detail({
    label,
    value
}) {

    return (

        <div className="detail">

            <span>
                {label}
            </span>


            <strong>
                {value || "—"}
            </strong>

        </div>

    );

}


function formatAction(action) {

    if (!action) {

        return "Manual Review";

    }


    return action
        .replaceAll(
            "_",
            " "
        )
        .replace(
            /\b\w/g,
            (letter) =>
                letter.toUpperCase()
        );

}


export default Investigation;