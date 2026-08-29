import {
    useEffect,
    useState
} from "react";

import {
    getRiskAnalytics
} from "../services/api";


function Analytics() {

    const [data, setData] =
        useState(null);

    const [loading, setLoading] =
        useState(true);


    useEffect(() => {

        async function loadAnalytics() {

            try {

                const result =
                    await getRiskAnalytics();

                setData(result);

            } catch (error) {

                console.error(error);

            } finally {

                setLoading(false);

            }

        }


        loadAnalytics();

    }, []);


    if (loading) {

        return (

            <div className="page-loading">

                Loading analytics...

            </div>

        );

    }


    return (

        <div className="page">

            <div className="page-header">

                <div>

                    <p className="eyebrow">
                        RISK INTELLIGENCE
                    </p>


                    <h2>
                        Analytics
                    </h2>


                    <p className="page-description">

                        Understand risk patterns and
                        recurring fraud signals across
                        transaction activity.

                    </p>

                </div>

            </div>


            <div className="analytics-grid">

                <section className="panel">

                    <p className="section-eyebrow">

                        RISK LEVELS

                    </p>


                    <h3>
                        Transaction distribution
                    </h3>


                    <div className="analytics-bars">

                        {Object.entries(
                            data?.counts || {}
                        ).map(
                            ([level, count]) => (

                                <Bar
                                    key={level}
                                    label={level}
                                    value={count}
                                    total={
                                        data?.total_transactions
                                    }
                                />

                            )
                        )}

                    </div>

                </section>


                <section className="panel">

                    <p className="section-eyebrow">

                        FRAUD SIGNALS

                    </p>


                    <h3>
                        Most common flag reasons
                    </h3>


                    <div className="reason-list">

                        {
                            data?.flagged_reasons
                                ?.map(
                                    (
                                        item,
                                        index
                                    ) => (

                                        <div
                                            className="reason-item"
                                            key={index}
                                        >

                                            <span>

                                                {
                                                    item.reason
                                                }

                                            </span>


                                            <strong>

                                                {
                                                    item.count
                                                }

                                            </strong>

                                        </div>

                                    )
                                )
                        }

                    </div>

                </section>

            </div>


            <section className="panel">

                <p className="section-eyebrow">

                    MERCHANT RISK

                </p>


                <h3>
                    Categories with highest average risk
                </h3>


                <div className="category-grid">

                    {
                        data?.categories
                            ?.map(
                                (
                                    item,
                                    index
                                ) => (

                                    <div
                                        className="category-card"
                                        key={index}
                                    >

                                        <span>

                                            {
                                                item.category
                                            }

                                        </span>


                                        <strong>

                                            {
                                                item.avg_risk
                                            }

                                            <small>
                                                /100
                                            </small>

                                        </strong>

                                    </div>

                                )
                            )
                    }

                </div>

            </section>

        </div>

    );

}


function Bar({
    label,
    value,
    total
}) {

    const percentage =
        total
            ? (value / total) * 100
            : 0;


    return (

        <div className="analytics-bar">

            <div>

                <span>
                    {label}
                </span>


                <strong>
                    {value}
                </strong>

            </div>


            <div className="bar-track">

                <div
                    className={`bar-fill ${label.toLowerCase()}`}
                    style={{
                        width:
                            `${percentage}%`
                    }}
                />

            </div>

        </div>

    );

}


export default Analytics;