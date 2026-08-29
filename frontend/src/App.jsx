import { useEffect, useMemo, useState } from "react";
import "./App.css";

function App() {
    const [activePage, setActivePage] = useState("overview");

    const [transactions, setTransactions] = useState([]);
    const [filteredTransactions, setFilteredTransactions] = useState([]);

    const [loadingTransactions, setLoadingTransactions] =
        useState(true);

    const [transactionsError, setTransactionsError] =
        useState("");

    const [searchQuery, setSearchQuery] = useState("");

    const [investigation, setInvestigation] =
        useState(null);

    const [selectedTransaction, setSelectedTransaction] =
        useState(null);

    const [loadingInvestigation, setLoadingInvestigation] =
        useState(false);

    const [investigationError, setInvestigationError] =
        useState("");


    // =====================================================
    // LOAD TRANSACTIONS
    // =====================================================

    async function loadTransactions() {
        setLoadingTransactions(true);
        setTransactionsError("");

        try {
            const response = await fetch(
                "/api/transactions?limit=100"
            );

            if (!response.ok) {
                throw new Error(
                    "Unable to load transactions."
                );
            }

            const data = await response.json();

            const loadedTransactions =
                data.transactions || [];

            setTransactions(
                loadedTransactions
            );

            setFilteredTransactions(
                loadedTransactions
            );

        } catch (error) {
            console.error(
                "Transaction loading error:",
                error
            );

            setTransactionsError(
                error.message ||
                "Unable to connect to Shield-AI backend."
            );

        } finally {
            setLoadingTransactions(false);
        }
    }


    // =====================================================
    // LOAD DATA WHEN APP STARTS
    // =====================================================

    useEffect(() => {
        loadTransactions();
    }, []);


    // =====================================================
    // SEARCH TRANSACTIONS
    // =====================================================

    useEffect(() => {

        const query =
            searchQuery
                .trim()
                .toLowerCase();

        if (!query) {
            setFilteredTransactions(
                transactions
            );

            return;
        }

        const results =
            transactions.filter(
                (transaction) =>
                    transaction.transaction_id
                        .toLowerCase()
                        .includes(query) ||

                    transaction.customer_id
                        .toLowerCase()
                        .includes(query)
            );

        setFilteredTransactions(
            results
        );

    }, [
        searchQuery,
        transactions
    ]);


    // =====================================================
    // DASHBOARD STATISTICS
    // =====================================================

    const statistics = useMemo(() => {

        const total =
            transactions.length;

        const fraudTransactions =
            transactions.filter(
                (transaction) =>
                    transaction.is_fraud === 1
            );

        const safeTransactions =
            transactions.filter(
                (transaction) =>
                    transaction.is_fraud === 0
            );

        const totalAmount =
            transactions.reduce(
                (sum, transaction) =>
                    sum + transaction.amount,
                0
            );

        const fraudRate =
            total === 0
                ? 0
                : (
                    fraudTransactions.length /
                    total
                ) * 100;

        return {
            total,
            fraudCount:
                fraudTransactions.length,
            safeCount:
                safeTransactions.length,
            totalAmount,
            fraudRate
        };

    }, [transactions]);


    // =====================================================
    // OPEN INVESTIGATION
    // =====================================================

    async function openInvestigation(
        transaction
    ) {

        setSelectedTransaction(
            transaction
        );

        setActivePage(
            "investigation"
        );

        setLoadingInvestigation(
            true
        );

        setInvestigationError(
            ""
        );

        setInvestigation(
            null
        );

        try {

            const response =
                await fetch(
                    `/api/investigate/${transaction.transaction_id}`
                );

            if (!response.ok) {

                let message =
                    "Investigation failed.";

                try {

                    const errorData =
                        await response.json();

                    if (
                        errorData.detail
                    ) {
                        message =
                            errorData.detail;
                    }

                } catch {
                    // Ignore invalid JSON response
                }

                throw new Error(
                    message
                );
            }

            const data =
                await response.json();

            console.log(
                "Investigation:",
                data
            );

            setInvestigation(
                data
            );

        } catch (error) {

            console.error(
                "Investigation error:",
                error
            );

            setInvestigationError(
                error.message ||
                "Unable to investigate transaction."
            );

        } finally {

            setLoadingInvestigation(
                false
            );
        }
    }


    // =====================================================
    // FORMATTERS
    // =====================================================

    function formatCurrency(amount) {

        return new Intl.NumberFormat(
            "en-IN",
            {
                style: "currency",
                currency: "INR",
                maximumFractionDigits: 0
            }
        ).format(amount);
    }


    function formatDate(timestamp) {

        const date =
            new Date(timestamp);

        if (Number.isNaN(date.getTime())) {
            return timestamp;
        }

        return date.toLocaleString(
            "en-IN",
            {
                dateStyle: "medium",
                timeStyle: "short"
            }
        );
    }


    // =====================================================
    // NAVIGATION
    // =====================================================

    function navigate(page) {

        setActivePage(page);

        if (
            page !== "investigation"
        ) {

            setInvestigation(null);

            setSelectedTransaction(null);

            setInvestigationError("");
        }
    }


    // =====================================================
    // RENDER PAGE
    // =====================================================

    function renderPage() {

        if (
            activePage === "overview"
        ) {
            return (
                <OverviewPage
                    statistics={statistics}
                    transactions={transactions}
                    loading={loadingTransactions}
                    error={transactionsError}
                    onInvestigate={
                        openInvestigation
                    }
                    formatCurrency={
                        formatCurrency
                    }
                />
            );
        }


        if (
            activePage === "transactions"
        ) {
            return (
                <TransactionsPage
                    transactions={
                        filteredTransactions
                    }
                    loading={
                        loadingTransactions
                    }
                    error={
                        transactionsError
                    }
                    searchQuery={
                        searchQuery
                    }
                    onSearch={
                        setSearchQuery
                    }
                    onInvestigate={
                        openInvestigation
                    }
                    formatCurrency={
                        formatCurrency
                    }
                    formatDate={
                        formatDate
                    }
                    onRefresh={
                        loadTransactions
                    }
                />
            );
        }


        if (
            activePage === "investigation"
        ) {
            return (
                <InvestigationPage
                    transaction={
                        selectedTransaction
                    }
                    investigation={
                        investigation
                    }
                    loading={
                        loadingInvestigation
                    }
                    error={
                        investigationError
                    }
                    onBack={() =>
                        navigate(
                            "transactions"
                        )
                    }
                    formatCurrency={
                        formatCurrency
                    }
                />
            );
        }


        if (
            activePage === "analytics"
        ) {
            return (
                <AnalyticsPage
                    transactions={
                        transactions
                    }
                    statistics={
                        statistics
                    }
                    loading={
                        loadingTransactions
                    }
                    formatCurrency={
                        formatCurrency
                    }
                />
            );
        }
    }


    return (

        <div className="app-shell">

            <aside className="sidebar">

                <div className="logo">

                    <div className="logo-icon">
                        S
                    </div>

                    <div>

                        <h1>
                            SHIELD-AI
                        </h1>

                        <span>
                            FRAUD INTELLIGENCE
                        </span>

                    </div>

                </div>


                <nav className="navigation">

                    <button
                        className={
                            activePage ===
                            "overview"
                                ? "nav-item active"
                                : "nav-item"
                        }
                        onClick={() =>
                            navigate(
                                "overview"
                            )
                        }
                    >
                        Overview
                    </button>


                    <button
                        className={
                            activePage ===
                            "transactions"
                                ? "nav-item active"
                                : "nav-item"
                        }
                        onClick={() =>
                            navigate(
                                "transactions"
                            )
                        }
                    >
                        Transactions
                    </button>


                    <button
                        className={
                            activePage ===
                            "analytics"
                                ? "nav-item active"
                                : "nav-item"
                        }
                        onClick={() =>
                            navigate(
                                "analytics"
                            )
                        }
                    >
                        Analytics
                    </button>

                </nav>


                <div className="sidebar-footer">

                    <span className="status-dot" />

                    SYSTEM ONLINE

                </div>

            </aside>


            <main className="content">

                <header className="topbar">

                    <div>

                        <p className="topbar-label">
                            SHIELD-AI RISK PLATFORM
                        </p>

                        <h2>
                            {
                                activePage ===
                                "overview"
                                    ? "Risk Overview"
                                    : activePage ===
                                      "transactions"
                                    ? "Transactions"
                                    : activePage ===
                                      "analytics"
                                    ? "Risk Analytics"
                                    : "AI Investigation"
                            }
                        </h2>

                    </div>


                    <button
                        className="refresh-button"
                        onClick={
                            loadTransactions
                        }
                    >
                        Refresh Data
                    </button>

                </header>


                {renderPage()}

            </main>

        </div>
    );
}


// =========================================================
// OVERVIEW PAGE
// =========================================================

function OverviewPage({
    statistics,
    transactions,
    loading,
    error,
    onInvestigate,
    formatCurrency
}) {

    const suspiciousTransactions =
        transactions
            .filter(
                (transaction) =>
                    transaction.is_fraud === 1
            )
            .slice(0, 5);


    return (

        <div className="page">

            <section className="page-intro">

                <p className="eyebrow">
                    REAL-TIME FRAUD MONITORING
                </p>

                <h3>
                    Monitor risk across
                    your payment ecosystem.
                </h3>

                <p>
                    Shield-AI analyzes
                    transaction behaviour and
                    helps investigators
                    understand suspicious
                    activity.
                </p>

            </section>


            {loading && (
                <div className="loading-card">
                    Loading transaction data...
                </div>
            )}


            {error && (
                <div className="error-card">
                    {error}
                </div>
            )}


            {!loading && !error && (

                <>

                    <section className="stats-grid">

                        <StatCard
                            label="TOTAL TRANSACTIONS"
                            value={
                                statistics.total
                            }
                        />


                        <StatCard
                            label="FLAGGED TRANSACTIONS"
                            value={
                                statistics.fraudCount
                            }
                        />


                        <StatCard
                            label="FRAUD RATE"
                            value={
                                `${statistics.fraudRate.toFixed(
                                    1
                                )}%`
                            }
                        />


                        <StatCard
                            label="TRANSACTION VOLUME"
                            value={
                                formatCurrency(
                                    statistics.totalAmount
                                )
                            }
                        />

                    </section>


                    <section className="panel">

                        <div className="panel-header">

                            <div>

                                <p className="section-label">
                                    PRIORITY QUEUE
                                </p>

                                <h3>
                                    Recently flagged
                                    transactions
                                </h3>

                            </div>

                        </div>


                        {suspiciousTransactions.length ===
                        0 ? (

                            <p className="empty-message">
                                No flagged transactions
                                found in the current
                                dataset.
                            </p>

                        ) : (

                            <div className="transaction-list">

                                {suspiciousTransactions.map(
                                    (transaction) => (

                                        <TransactionRow
                                            key={
                                                transaction.transaction_id
                                            }
                                            transaction={
                                                transaction
                                            }
                                            onClick={
                                                onInvestigate
                                            }
                                            formatCurrency={
                                                formatCurrency
                                            }
                                        />

                                    )
                                )}

                            </div>

                        )}

                    </section>

                </>

            )}

        </div>
    );
}


// =========================================================
// STAT CARD
// =========================================================

function StatCard({
    label,
    value
}) {

    return (

        <div className="stat-card">

            <p>
                {label}
            </p>

            <h3>
                {value}
            </h3>

        </div>
    );
}


// =========================================================
// TRANSACTIONS PAGE
// =========================================================

function TransactionsPage({
    transactions,
    loading,
    error,
    searchQuery,
    onSearch,
    onInvestigate,
    formatCurrency,
    formatDate,
    onRefresh
}) {

    return (

        <div className="page">

            <section className="page-intro">

                <p className="eyebrow">
                    TRANSACTION MONITORING
                </p>

                <h3>
                    Investigate payment
                    activity.
                </h3>

            </section>


            <section className="toolbar">

                <input
                    type="text"
                    value={
                        searchQuery
                    }
                    onChange={(event) =>
                        onSearch(
                            event.target.value
                        )
                    }
                    placeholder="Search by transaction ID or customer ID..."
                />


                <button
                    onClick={
                        onRefresh
                    }
                >
                    Reload
                </button>

            </section>


            {loading && (
                <div className="loading-card">
                    Loading transactions...
                </div>
            )}


            {error && (
                <div className="error-card">
                    {error}
                </div>
            )}


            {!loading && !error && (

                <section className="table-panel">

                    <div className="table-scroll">

                        <table>

                            <thead>

                                <tr>

                                    <th>
                                        Transaction ID
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
                                        Category
                                    </th>

                                    <th>
                                        Country
                                    </th>

                                    <th>
                                        Status
                                    </th>

                                    <th>
                                        Action
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
                                        >

                                            <td className="transaction-id">
                                                {
                                                    transaction.transaction_id
                                                }
                                            </td>


                                            <td>
                                                {
                                                    transaction.customer_id
                                                }
                                            </td>


                                            <td>
                                                {
                                                    formatCurrency(
                                                        transaction.amount
                                                    )
                                                }
                                            </td>


                                            <td>
                                                {
                                                    transaction.payment_method
                                                }
                                            </td>


                                            <td>
                                                {
                                                    transaction.merchant_category
                                                }
                                            </td>


                                            <td>
                                                {
                                                    transaction.country
                                                }
                                            </td>


                                            <td>

                                                <span
                                                    className={
                                                        transaction.is_fraud ===
                                                        1
                                                            ? "risk-badge high"
                                                            : "risk-badge safe"
                                                    }
                                                >

                                                    {transaction.is_fraud ===
                                                    1
                                                        ? "FLAGGED"
                                                        : "NORMAL"}

                                                </span>

                                            </td>


                                            <td>

                                                <button
                                                    className="investigate-button"
                                                    onClick={() =>
                                                        onInvestigate(
                                                            transaction
                                                        )
                                                    }
                                                >
                                                    Investigate
                                                </button>

                                            </td>

                                        </tr>

                                    )
                                )}


                                {transactions.length ===
                                0 && (

                                    <tr>

                                        <td
                                            colSpan="8"
                                            className="no-results"
                                        >
                                            No transactions found.
                                        </td>

                                    </tr>

                                )}

                            </tbody>

                        </table>

                    </div>

                </section>

            )}

        </div>
    );
}


// =========================================================
// SMALL TRANSACTION ROW
// =========================================================

function TransactionRow({
    transaction,
    onClick,
    formatCurrency
}) {

    return (

        <button
            className="transaction-row"
            onClick={() =>
                onClick(
                    transaction
                )
            }
        >

            <div>

                <strong>
                    {
                        transaction.transaction_id
                    }
                </strong>

                <span>
                    {
                        transaction.customer_id
                    }
                </span>

            </div>


            <div>

                <strong>
                    {
                        formatCurrency(
                            transaction.amount
                        )
                    }
                </strong>

                <span>
                    {
                        transaction.country
                    }
                </span>

            </div>


            <span className="investigate-link">
                Investigate →
            </span>

        </button>
    );
}


// =========================================================
// INVESTIGATION PAGE
// =========================================================

function InvestigationPage({
    transaction,
    investigation,
    loading,
    error,
    onBack,
    formatCurrency
}) {

    return (

        <div className="page">

            <button
                className="back-button"
                onClick={
                    onBack
                }
            >
                ← Back to Transactions
            </button>


            <section className="page-intro">

                <p className="eyebrow">
                    AI FRAUD INVESTIGATION
                </p>

                <h3>
                    Transaction analysis
                </h3>

                {transaction && (

                    <p>
                        Transaction ID:
                        {" "}
                        <strong>
                            {
                                transaction.transaction_id
                            }
                        </strong>
                    </p>

                )}

            </section>


            {loading && (
                <div className="loading-card">
                    AI is analyzing this
                    transaction...
                </div>
            )}


            {error && (
                <div className="error-card">
                    {error}
                </div>
            )}


            {investigation && (

                <>

                    <section className="investigation-grid">

                        <div className="risk-score-card">

                            <p>
                                AI RISK SCORE
                            </p>

                            <h2>
                                {
                                    investigation.risk_score
                                }
                            </h2>

                            <span>
                                {
                                    investigation.risk_level
                                }
                            </span>

                        </div>


                        <div className="recommendation-card">

                            <p>
                                RECOMMENDED ACTION
                            </p>

                            <h3>
                                {
                                    investigation.recommended_action
                                }
                            </h3>

                        </div>

                    </section>


                    <section className="details-grid">

                        <InfoCard
                            label="Amount"
                            value={
                                formatCurrency(
                                    investigation.transaction.amount
                                )
                            }
                        />

                        <InfoCard
                            label="Customer"
                            value={
                                investigation.transaction.customer_id
                            }
                        />

                        <InfoCard
                            label="Payment Method"
                            value={
                                investigation.transaction.payment_method
                            }
                        />

                        <InfoCard
                            label="Merchant Category"
                            value={
                                investigation.transaction.merchant_category
                            }
                        />

                        <InfoCard
                            label="Country"
                            value={
                                investigation.transaction.country
                            }
                        />

                        <InfoCard
                            label="Timestamp"
                            value={
                                investigation.transaction.timestamp
                            }
                        />

                    </section>


                    <section className="panel">

                        <p className="section-label">
                            AI EXPLANATION
                        </p>

                        <h3>
                            Why this transaction
                            was flagged
                        </h3>


                        <ExplanationContent
                            data={
                                investigation.explanations
                            }
                        />

                    </section>


                    <section className="panel">

                        <p className="section-label">
                            BEHAVIOUR COMPARISON
                        </p>

                        <h3>
                            Customer behaviour
                            analysis
                        </h3>


                        <ExplanationContent
                            data={
                                investigation.behavior_comparison
                            }
                        />

                    </section>

                </>

            )}

        </div>
    );
}


// =========================================================
// INFO CARD
// =========================================================

function InfoCard({
    label,
    value
}) {

    return (

        <div className="info-card">

            <p>
                {label}
            </p>

            <strong>
                {String(value)}
            </strong>

        </div>
    );
}


// =========================================================
// DYNAMIC EXPLANATION RENDERER
// =========================================================

function ExplanationContent({
    data
}) {

    if (!data) {
        return (
            <p className="empty-message">
                No explanation available.
            </p>
        );
    }


    if (Array.isArray(data)) {

        return (

            <ul className="explanation-list">

                {data.map(
                    (item, index) => (

                        <li
                            key={index}
                        >
                            {
                                typeof item ===
                                "object"
                                    ? JSON.stringify(
                                        item
                                    )
                                    : String(
                                        item
                                    )
                            }
                        </li>

                    )
                )}

            </ul>

        );
    }


    if (
        typeof data ===
        "object"
    ) {

        return (

            <div className="explanation-grid">

                {Object.entries(
                    data
                ).map(
                    ([key, value]) => (

                        <div
                            className="explanation-item"
                            key={key}
                        >

                            <span>
                                {key
                                    .replace(
                                        /_/g,
                                        " "
                                    )
                                    .toUpperCase()}
                            </span>

                            <strong>
                                {
                                    typeof value ===
                                    "object"
                                        ? JSON.stringify(
                                            value
                                        )
                                        : String(
                                            value
                                        )
                                }
                            </strong>

                        </div>

                    )
                )}

            </div>

        );
    }


    return (
        <p>
            {String(data)}
        </p>
    );
}


// =========================================================
// ANALYTICS PAGE
// =========================================================

function AnalyticsPage({
    transactions,
    statistics,
    loading,
    formatCurrency
}) {

    const fraudByCountry =
        useMemo(() => {

            const countries =
                {};

            transactions
                .filter(
                    (transaction) =>
                        transaction.is_fraud === 1
                )
                .forEach(
                    (transaction) => {

                        const country =
                            transaction.country;

                        countries[country] =
                            (countries[country] ||
                                0) + 1;
                    }
                );

            return Object.entries(
                countries
            )
                .sort(
                    (a, b) =>
                        b[1] - a[1]
                )
                .slice(0, 5);

        }, [
            transactions
        ]);


    if (loading) {

        return (
            <div className="loading-card">
                Loading analytics...
            </div>
        );
    }


    return (

        <div className="page">

            <section className="page-intro">

                <p className="eyebrow">
                    FRAUD INTELLIGENCE
                </p>

                <h3>
                    Risk patterns across
                    transactions.
                </h3>

            </section>


            <section className="analytics-grid">

                <StatCard
                    label="TOTAL ANALYZED"
                    value={
                        statistics.total
                    }
                />

                <StatCard
                    label="HIGH RISK"
                    value={
                        statistics.fraudCount
                    }
                />

                <StatCard
                    label="NORMAL ACTIVITY"
                    value={
                        statistics.safeCount
                    }
                />

                <StatCard
                    label="PAYMENT VOLUME"
                    value={
                        formatCurrency(
                            statistics.totalAmount
                        )
                    }
                />

            </section>


            <section className="panel">

                <p className="section-label">
                    GEOGRAPHIC RISK
                </p>

                <h3>
                    Countries with flagged
                    activity
                </h3>


                <div className="country-list">

                    {fraudByCountry.map(
                        ([country, count]) => (

                            <div
                                className="country-row"
                                key={country}
                            >

                                <span>
                                    {country}
                                </span>

                                <strong>
                                    {
                                        count
                                    } flagged
                                </strong>

                            </div>

                        )
                    )}


                    {fraudByCountry.length ===
                    0 && (

                        <p className="empty-message">
                            No flagged activity
                            found.
                        </p>

                    )}

                </div>

            </section>

        </div>
    );
}


export default App;