import {
    useEffect,
    useState
} from "react";

import {
    getTransactions
} from "../services/api";

import {
    RiskBadge
} from "./Overview";


function Transactions({
    openInvestigation
}) {

    const [data, setData] =
        useState(null);

    const [query, setQuery] =
        useState("");

    const [risk, setRisk] =
        useState("ALL");

    const [offset, setOffset] =
        useState(0);

    const [loading, setLoading] =
        useState(true);


    const limit = 20;


    useEffect(() => {

        loadTransactions();

    }, [
        risk,
        offset
    ]);


    async function loadTransactions(
        searchQuery = query
    ) {

        try {

            setLoading(true);

            const result =
                await getTransactions(
                    searchQuery,
                    risk,
                    limit,
                    offset
                );

            setData(result);

        } catch (error) {

            console.error(error);

        } finally {

            setLoading(false);

        }

    }


    function handleSearch(event) {

        event.preventDefault();

        setOffset(0);

        loadTransactions(query);

    }


    function changeRisk(newRisk) {

        setRisk(newRisk);

        setOffset(0);

    }


    const transactions =
        data?.transactions || [];


    return (

        <div className="page">

            <div className="page-header">

                <div>

                    <p className="eyebrow">
                        TRANSACTION MONITORING
                    </p>


                    <h2>
                        Transactions
                    </h2>


                    <p className="page-description">

                        Search and investigate
                        transaction activity across
                        the risk monitoring system.

                    </p>

                </div>

            </div>


            <div className="transaction-controls">

                <form
                    onSubmit={handleSearch}
                    className="search-form"
                >

                    <input
                        value={query}
                        onChange={(event) =>
                            setQuery(
                                event.target.value
                            )
                        }
                        placeholder="Search transaction ID or customer ID..."
                    />


                    <button>
                        Search
                    </button>

                </form>


                <div className="risk-filters">

                    {[
                        "ALL",
                        "HIGH",
                        "MEDIUM",
                        "LOW"
                    ].map(
                        (level) => (

                            <button
                                key={level}
                                className={
                                    risk === level
                                        ? "filter active"
                                        : "filter"
                                }
                                onClick={() =>
                                    changeRisk(
                                        level
                                    )
                                }
                            >

                                {level}

                            </button>

                        )
                    )}

                </div>

            </div>


            <section className="panel">

                <div className="table-header">

                    <div>

                        <h3>
                            Transaction queue
                        </h3>


                        <p>

                            {data?.total || 0}
                            {" "}
                            transactions found

                        </p>

                    </div>

                </div>


                {loading ? (

                    <div className="page-loading">

                        Loading transactions...

                    </div>

                ) : (

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
                                        Method
                                    </th>

                                    <th>
                                        Risk
                                    </th>

                                    <th>
                                        Primary reason
                                    </th>

                                    <th>
                                        Status
                                    </th>

                                </tr>

                            </thead>


                            <tbody>

                                {transactions.map(
                                    (
                                        transaction
                                    ) => (

                                        <tr
                                            key={
                                                transaction.transaction_id
                                            }
                                            className="clickable-row"
                                            onClick={() =>
                                                openInvestigation(
                                                    transaction.transaction_id
                                                )
                                            }
                                        >

                                            <td>

                                                <code>

                                                    {
                                                        transaction
                                                            .transaction_id
                                                            .slice(
                                                                0,
                                                                12
                                                            )
                                                    }

                                                    ...

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

                                                {
                                                    transaction.payment_method
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


                                            <td>

                                                <span className="status">

                                                    {
                                                        transaction.status
                                                            ?.replaceAll(
                                                                "_",
                                                                " "
                                                            )
                                                    }

                                                </span>

                                            </td>

                                        </tr>

                                    )
                                )}

                            </tbody>

                        </table>

                    </div>

                )}


                <div className="pagination">

                    <button
                        disabled={
                            offset === 0
                        }
                        onClick={() =>
                            setOffset(
                                Math.max(
                                    0,
                                    offset - limit
                                )
                            )
                        }
                    >

                        ← Previous

                    </button>


                    <span>

                        Showing{" "}

                        {offset + 1}

                        {" - "}

                        {Math.min(
                            offset + limit,
                            data?.total || 0
                        )}

                    </span>


                    <button
                        disabled={
                            offset + limit >=
                            (data?.total || 0)
                        }
                        onClick={() =>
                            setOffset(
                                offset + limit
                            )
                        }
                    >

                        Next →

                    </button>

                </div>

            </section>

        </div>

    );

}


export default Transactions;