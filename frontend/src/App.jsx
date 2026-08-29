import { useEffect, useState, useCallback } from "react";
import "./App.css";


const STATUS_META = {
    unreviewed: { label: "Unreviewed", icon: "○" },
    safe: { label: "Marked Safe", icon: "✓" },
    needs_review: { label: "Needs Review", icon: "⚠" },
    confirmed_fraud: { label: "Confirmed Fraud", icon: "🚨" },
};


function formatINR(amount) {
    return `₹${Number(amount || 0).toLocaleString("en-IN", {
        maximumFractionDigits: 0,
    })}`;
}


function shortId(id) {
    if (!id) return "—";
    return id.length > 10 ? `${id.slice(0, 8)}…` : id;
}


function formatClock(timestamp) {
    if (!timestamp) return "—";
    const date = new Date(timestamp.replace(" ", "T"));
    if (Number.isNaN(date.getTime())) return timestamp;
    return date.toLocaleTimeString("en-IN", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
    });
}


function bandForScore(score) {
    if (score >= 85) return "critical";
    if (score >= 70) return "high";
    if (score >= 40) return "medium";
    return "low";
}


const BAND_META = {
    critical: { label: "CRITICAL", icon: "🚨" },
    high: { label: "HIGH", icon: "●" },
    medium: { label: "MEDIUM", icon: "●" },
    low: { label: "LOW", icon: "●" },
};


async function api(path, options) {
    const response = await fetch(path, options);

    if (!response.ok) {
        let message = "Request failed.";
        try {
            const errorData = await response.json();
            if (errorData.detail) message = errorData.detail;
        } catch {
            // ignore
        }
        throw new Error(message);
    }

    return response.json();
}


function App() {

    const [listTab, setListTab] = useState("queue");
    const [queue, setQueue] = useState([]);
    const [recent, setRecent] = useState([]);
    const [listLoading, setListLoading] = useState(true);
    const [listError, setListError] = useState("");

    const [searchValue, setSearchValue] = useState("");

    const [selectedId, setSelectedId] = useState(null);
    const [investigation, setInvestigation] = useState(null);
    const [invLoading, setInvLoading] = useState(false);
    const [invError, setInvError] = useState("");

    const [profile, setProfile] = useState(null);
    const [timeline, setTimeline] = useState([]);


    const loadQueue = useCallback(async () => {
        try {
            const data = await api("/api/queue?limit=40");
            setQueue(data.queue || []);
            return data.queue || [];
        } catch (err) {
            setListError(err.message || "Unable to load the queue.");
            return [];
        }
    }, []);


    const loadRecent = useCallback(async () => {
        try {
            const data = await api("/api/transactions?limit=40");
            setRecent(data.transactions || []);
        } catch (err) {
            setListError(err.message || "Unable to load transactions.");
        }
    }, []);


    useEffect(() => {
        (async () => {
            setListLoading(true);
            const [queueItems] = await Promise.all([
                loadQueue(),
                loadRecent(),
            ]);
            setListLoading(false);

            if (queueItems && queueItems.length > 0) {
                setSelectedId(queueItems[0].transaction_id);
            }
        })();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);


    const loadCustomerContext = useCallback(async (customerId) => {
        if (!customerId) return;

        try {
            const [profileData, timelineData] = await Promise.all([
                api(`/api/customers/${customerId}/profile`),
                api(`/api/customers/${customerId}/timeline?limit=8`),
            ]);
            setProfile(profileData.profile);
            setTimeline(timelineData.timeline || []);
        } catch {
            setProfile(null);
            setTimeline([]);
        }
    }, []);


    const investigate = useCallback(async (id) => {
        if (!id || !id.trim()) return;

        setInvLoading(true);
        setInvError("");
        setInvestigation(null);
        setProfile(null);
        setTimeline([]);

        try {
            const data = await api(`/api/investigate/${id.trim()}`);
            setInvestigation(data);
            loadCustomerContext(data.transaction?.customer_id);
        } catch (err) {
            setInvError(
                err.message || "Unable to connect to the Shield-AI backend."
            );
        } finally {
            setInvLoading(false);
        }
    }, [loadCustomerContext]);


    useEffect(() => {
        if (selectedId) investigate(selectedId);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedId]);


    function handleSearchSubmit(event) {
        event.preventDefault();
        if (!searchValue.trim()) return;
        setSelectedId(searchValue.trim());
    }


    function patchListCaseStatus(transactionId, status) {
        setQueue((items) =>
            items.map((item) =>
                item.transaction_id === transactionId
                    ? { ...item, case_status: status }
                    : item
            )
        );
        setRecent((items) =>
            items.map((item) =>
                item.transaction_id === transactionId
                    ? { ...item, case_status: status }
                    : item
            )
        );
    }


    async function handleStatusChange(status) {
        if (!investigation) return;
        const id = investigation.transaction_id;

        try {
            const data = await api(`/api/cases/${id}/status`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status }),
            });
            setInvestigation((prev) => ({ ...prev, case: data.case }));
            patchListCaseStatus(id, status);
        } catch (err) {
            setInvError(err.message || "Could not update the case status.");
        }
    }


    async function handleSaveNote(noteText) {
        if (!investigation || !noteText.trim()) return;
        const id = investigation.transaction_id;

        const data = await api(`/api/cases/${id}/notes`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ note: noteText.trim() }),
        });
        setInvestigation((prev) => ({ ...prev, case: data.case }));
    }


    return (
        <div className="app">

            <header className="navbar">
                <div className="brand">
                    <div className="brand-icon">S</div>
                    <div>
                        <h1>SHIELD-AI</h1>
                        <span>Explainable Fraud Intelligence</span>
                    </div>
                </div>

                <form className="global-search" onSubmit={handleSearchSubmit}>
                    <input
                        value={searchValue}
                        onChange={(event) => setSearchValue(event.target.value)}
                        placeholder="Jump to transaction ID or customer ID…"
                    />
                    <button type="submit">Investigate</button>
                </form>

                <div className="system-status">
                    <span className="status-dot"></span>
                    SYSTEM ONLINE
                </div>
            </header>

            <div className="workspace">

                <aside className="queue-panel">

                    <div className="list-tabs">
                        <button
                            className={listTab === "queue" ? "active" : ""}
                            onClick={() => setListTab("queue")}
                        >
                            Priority Queue
                            {queue.length > 0 && (
                                <span className="tab-count">{queue.length}</span>
                            )}
                        </button>
                        <button
                            className={listTab === "recent" ? "active" : ""}
                            onClick={() => setListTab("recent")}
                        >
                            All Activity
                        </button>
                    </div>

                    <div className="queue-list">

                        {listLoading && (
                            <div className="list-loading">
                                <div className="loader small"></div>
                            </div>
                        )}

                        {!listLoading && listError && (
                            <p className="list-error">{listError}</p>
                        )}

                        {!listLoading && listTab === "queue" && (
                            <QueueGroups
                                items={queue}
                                selectedId={selectedId}
                                onSelect={setSelectedId}
                            />
                        )}

                        {!listLoading && listTab === "recent" && (
                            <RecentList
                                items={recent}
                                selectedId={selectedId}
                                onSelect={setSelectedId}
                            />
                        )}

                    </div>

                </aside>

                <main className="detail-panel">

                    {!selectedId && !invLoading && (
                        <section className="empty-state">
                            <div className="empty-icon">◈</div>
                            <h3>Ready for investigation</h3>
                            <p>
                                Pick a transaction from the queue, or search for
                                a transaction or customer ID above.
                            </p>
                        </section>
                    )}

                    {invLoading && (
                        <section className="loading-state">
                            <div className="loader"></div>
                            <h3>AI investigation in progress</h3>
                            <p>
                                Analyzing transaction behavior, risk signals
                                and historical patterns...
                            </p>
                        </section>
                    )}

                    {!invLoading && invError && (
                        <section className="empty-state">
                            <div className="empty-icon">!</div>
                            <h3>Couldn't load that transaction</h3>
                            <p>{invError}</p>
                        </section>
                    )}

                    {!invLoading && !invError && investigation && (
                        <InvestigationView
                            data={investigation}
                            profile={profile}
                            timeline={timeline}
                            onStatusChange={handleStatusChange}
                            onSaveNote={handleSaveNote}
                        />
                    )}

                </main>

            </div>

        </div>
    );
}



function QueueGroups({ items, selectedId, onSelect }) {

    if (items.length === 0) {
        return (
            <p className="no-data">
                Nothing needs review right now — every transaction is
                scoring close to baseline.
            </p>
        );
    }

    const groups = { critical: [], high: [], medium: [] };

    items.forEach((item) => {
        const band = bandForScore(item.risk_score);
        (groups[band] || groups.medium).push(item);
    });

    return (
        <>
            {["critical", "high", "medium"].map((band) =>
                groups[band].length > 0 ? (
                    <div className="queue-group" key={band}>
                        <p className={`queue-group-label ${band}`}>
                            {BAND_META[band].icon} {BAND_META[band].label}
                            <span>{groups[band].length}</span>
                        </p>
                        {groups[band].map((item) => (
                            <QueueRow
                                key={item.transaction_id}
                                item={item}
                                band={band}
                                active={item.transaction_id === selectedId}
                                onSelect={onSelect}
                            />
                        ))}
                    </div>
                ) : null
            )}
        </>
    );
}


function QueueRow({ item, band, active, onSelect }) {

    const caseMeta = STATUS_META[item.case_status] || STATUS_META.unreviewed;

    return (
        <button
            className={`queue-row ${band} ${active ? "active" : ""}`}
            onClick={() => onSelect(item.transaction_id)}
        >
            <div className="queue-row-top">
                <code>{shortId(item.transaction_id)}</code>
                <span className="queue-score">{Math.round(item.risk_score)}</span>
            </div>
            <div className="queue-row-mid">
                <strong>{formatINR(item.amount)}</strong>
                <span className="queue-reason">{item.reason}</span>
            </div>
            <div className="queue-row-bottom">
                <span className="queue-time">{item.time_ago}</span>
                {item.case_status !== "unreviewed" && (
                    <span className={`case-pill ${item.case_status}`}>
                        {caseMeta.icon} {caseMeta.label}
                    </span>
                )}
            </div>
        </button>
    );
}


function RecentList({ items, selectedId, onSelect }) {

    if (items.length === 0) {
        return <p className="no-data">No transactions found.</p>;
    }

    return (
        <div className="queue-group">
            {items.map((item) => {
                const level = String(item.risk_level || "low").toLowerCase();
                return (
                    <button
                        key={item.transaction_id}
                        className={`recent-row ${level} ${
                            item.transaction_id === selectedId ? "active" : ""
                        }`}
                        onClick={() => onSelect(item.transaction_id)}
                    >
                        <div className="queue-row-top">
                            <code>{shortId(item.transaction_id)}</code>
                            <span className={`status-pill ${level}`}>
                                {item.status_label}
                            </span>
                        </div>
                        <div className="queue-row-mid">
                            <strong>{formatINR(item.amount)}</strong>
                            <span className="queue-reason">
                                {item.merchant_category}
                            </span>
                        </div>
                    </button>
                );
            })}
        </div>
    );
}



function SignalBars({ score, level }) {

    const segments = 20;
    const filled = Math.round((Math.min(score, 100) / 100) * segments);

    return (
        <div className="signal-bars">
            {Array.from({ length: segments }).map((_, index) => (
                <span
                    key={index}
                    className={`signal-bar ${
                        index < filled ? `filled ${level}` : ""
                    }`}
                />
            ))}
        </div>
    );
}



function InvestigationView({ data, profile, timeline, onStatusChange, onSaveNote }) {

    const transaction = data.transaction || {};
    const riskLevel = String(data.risk_level || "unknown").toLowerCase();
    const riskScore = Number(data.risk_score || 0);
    const displayBand = bandForScore(riskScore);

    const explanations = Array.isArray(data.explanations) ? data.explanations : [];
    const scoreBreakdown = Array.isArray(data.score_breakdown) ? data.score_breakdown : [];

    const comparisonPayload = data.behavior_comparison || {};
    const comparisons = Array.isArray(comparisonPayload)
        ? comparisonPayload
        : Array.isArray(comparisonPayload.signals)
            ? comparisonPayload.signals
            : [];
    const comparisonSummary =
        (!Array.isArray(comparisonPayload) && comparisonPayload.summary) || "";

    const flagSummary =
        data.flag_summary || (explanations[0] && explanations[0].message) || "";

    const caseData = data.case || { status: "unreviewed", notes: [] };

    const [noteDraft, setNoteDraft] = useState("");
    const [savingNote, setSavingNote] = useState(false);
    const [savingStatus, setSavingStatus] = useState(false);

    async function submitNote(event) {
        event.preventDefault();
        if (!noteDraft.trim()) return;
        setSavingNote(true);
        try {
            await onSaveNote(noteDraft);
            setNoteDraft("");
        } finally {
            setSavingNote(false);
        }
    }

    async function submitStatus(status) {
        setSavingStatus(true);
        try {
            await onStatusChange(status);
        } finally {
            setSavingStatus(false);
        }
    }

    return (
        <section className="investigation">

            <div className="transaction-header">
                <div>
                    <p className="section-label">INVESTIGATION RESULT</p>
                    <h2>Transaction</h2>
                    <code>{data.transaction_id}</code>
                </div>

                <div className="header-badges">
                    {caseData.status !== "unreviewed" && (
                        <span className={`case-pill large ${caseData.status}`}>
                            {STATUS_META[caseData.status].icon}{" "}
                            {STATUS_META[caseData.status].label}
                        </span>
                    )}
                    <div className={`risk-badge ${riskLevel}`}>
                        {displayBand === "critical" ? "CRITICAL" : data.risk_level}
                    </div>
                </div>
            </div>

            <div className="risk-grid">

                <div className="risk-card">
                    <p>AI RISK SCORE</p>

                    <div className="risk-score">
                        {riskScore.toFixed(1)}
                        <span>/100</span>
                    </div>

                    <SignalBars score={riskScore} level={riskLevel} />

                    {scoreBreakdown.length > 0 && (
                        <div className="score-breakdown">
                            <p className="score-breakdown-label">
                                Main contributing signals
                            </p>
                            {scoreBreakdown.map((driver, index) => (
                                <div className="score-driver" key={index}>
                                    <span
                                        className={`driver-dot ${driver.weight.toLowerCase()}`}
                                    />
                                    <span className="driver-label">{driver.label}</span>
                                    <span className="driver-points">
                                        +{driver.points}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="transaction-card">
                    <p>TRANSACTION</p>
                    <strong>{formatINR(transaction.amount)}</strong>
                    <span>
                        {transaction.payment_method || "Unknown"}
                        {" • "}
                        {transaction.merchant_category || "Unknown"}
                    </span>
                </div>

                <div className="action-card">
                    <p>RECOMMENDED ACTION</p>
                    <strong>{formatAction(data.recommended_action)}</strong>
                </div>

            </div>

            <div className="decision-panel">

                <div className="decision-buttons">
                    <p className="section-label">INVESTIGATOR DECISION</p>
                    <div className="decision-row">
                        <button
                            className={`decision-btn safe ${
                                caseData.status === "safe" ? "active" : ""
                            }`}
                            disabled={savingStatus}
                            onClick={() => submitStatus("safe")}
                        >
                            ✓ Mark Safe
                        </button>
                        <button
                            className={`decision-btn needs_review ${
                                caseData.status === "needs_review" ? "active" : ""
                            }`}
                            disabled={savingStatus}
                            onClick={() => submitStatus("needs_review")}
                        >
                            ⚠ Needs Review
                        </button>
                        <button
                            className={`decision-btn confirmed_fraud ${
                                caseData.status === "confirmed_fraud" ? "active" : ""
                            }`}
                            disabled={savingStatus}
                            onClick={() => submitStatus("confirmed_fraud")}
                        >
                            🚨 Confirm Fraud
                        </button>
                    </div>
                </div>

                <div className="notes-block">
                    <p className="section-label">INVESTIGATION NOTES</p>

                    {caseData.notes && caseData.notes.length > 0 && (
                        <div className="notes-list">
                            {caseData.notes.map((note, index) => (
                                <div className="note" key={index}>
                                    <p>{note.text}</p>
                                    <span>
                                        {new Date(note.created_at).toLocaleString(
                                            "en-IN",
                                            {
                                                day: "numeric",
                                                month: "short",
                                                hour: "numeric",
                                                minute: "2-digit",
                                                hour12: true,
                                            }
                                        )}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}

                    <form className="note-form" onSubmit={submitNote}>
                        <textarea
                            value={noteDraft}
                            onChange={(event) => setNoteDraft(event.target.value)}
                            placeholder="e.g. Customer usually transacts between 10 AM and 6 PM. This one is at 11 PM from a new device."
                            rows={3}
                        />
                        <button type="submit" disabled={savingNote || !noteDraft.trim()}>
                            {savingNote ? "Saving..." : "Save Note"}
                        </button>
                    </form>
                </div>

            </div>

            <div className="details-grid">

                <div className="panel">
                    <div className="panel-header">
                        <div>
                            <p className="section-label">MODEL EVIDENCE</p>
                            <h3>Why was this flagged?</h3>
                        </div>
                        <span className="ai-tag">AI</span>
                    </div>

                    {flagSummary && <p className="flag-summary">{flagSummary}</p>}

                    <div className="explanations">
                        {explanations.length === 0 && (
                            <p className="no-data">
                                {riskLevel === "low"
                                    ? "Nothing unusual stood out against this customer's baseline. The model is not treating this as a likely fraud case."
                                    : "The model raised risk from a mix of weaker signals rather than one obvious red flag. Check the behaviour comparison for what still differs from baseline."}
                            </p>
                        )}

                        {explanations.map((item, index) => (
                            <div className="explanation" key={index}>
                                <div
                                    className={`severity ${String(
                                        item.severity || "medium"
                                    ).toLowerCase()}`}
                                >
                                    !
                                </div>
                                <div>
                                    <strong>{item.title}</strong>
                                    <p>{item.message}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="panel">
                    <div className="panel-header">
                        <div>
                            <p className="section-label">BEHAVIORAL ANALYSIS</p>
                            <h3>Customer vs this payment</h3>
                        </div>
                    </div>

                    {comparisonSummary && (
                        <p className="comparison-summary">{comparisonSummary}</p>
                    )}

                    <div className="comparison">
                        {comparisons.length === 0 && (
                            <p className="no-data">
                                Behavioral comparison unavailable.
                            </p>
                        )}

                        {comparisons.length > 0 && (
                            <div className="comparison-head">
                                <div>Signal</div>
                                <div>Usual for this customer</div>
                                <div>This payment</div>
                                <div>Result</div>
                            </div>
                        )}

                        {comparisons.map((item, index) => {
                            const status = String(item.status || "NORMAL").toLowerCase();
                            return (
                                <div className={`comparison-row ${status}`} key={index}>
                                    <div className="comparison-signal">
                                        <strong>{item.signal || "Signal"}</strong>
                                        {item.insight && <p>{item.insight}</p>}
                                    </div>
                                    <div>{item.normal || "—"}</div>
                                    <div>{item.current || "—"}</div>
                                    <div>
                                        <span className={`status-pill ${status}`}>
                                            {item.status || "NORMAL"}
                                        </span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

            </div>

            <div className="details-grid">

                <div className="panel">
                    <div className="panel-header">
                        <div>
                            <p className="section-label">CUSTOMER RISK PROFILE</p>
                            <h3>{transaction.customer_id || "Unknown customer"}</h3>
                        </div>
                    </div>

                    {!profile && (
                        <p className="no-data">Customer profile unavailable.</p>
                    )}

                    {profile && (
                        <div className="profile-grid">
                            <ProfileStat label="Account Age" value={profile.account_age_display} />
                            <ProfileStat
                                label="Total Transactions"
                                value={profile.total_transactions}
                            />
                            <ProfileStat
                                label="Average Transaction"
                                value={formatINR(profile.average_transaction)}
                            />
                            <ProfileStat
                                label="Typical Activity"
                                value={profile.typical_activity}
                            />
                            <ProfileStat label="Known Devices" value={profile.known_devices} />
                            <ProfileStat
                                label="Usual Locations"
                                value={profile.usual_locations}
                            />
                            <ProfileStat
                                label="Previous Fraud Cases"
                                value={profile.previous_fraud_cases}
                                flagged={profile.previous_fraud_cases > 0}
                            />
                            <ProfileStat
                                label="Avg. Risk Score"
                                value={`${profile.average_risk_score}/100`}
                            />
                        </div>
                    )}
                </div>

                <div className="panel">
                    <div className="panel-header">
                        <div>
                            <p className="section-label">RISK TIMELINE</p>
                            <h3>Recent customer activity</h3>
                        </div>
                    </div>

                    {timeline.length === 0 && (
                        <p className="no-data">No recent activity available.</p>
                    )}

                    {timeline.length > 0 && (
                        <div className="timeline">
                            {timeline.map((item) => {
                                const isCurrent = item.transaction_id === data.transaction_id;
                                const status = item.status.toLowerCase();
                                const icon =
                                    status === "normal" ? "✓" :
                                    status === "watch" ? "⚠" : "🚨";

                                return (
                                    <div
                                        className={`timeline-row ${status} ${
                                            isCurrent ? "current" : ""
                                        }`}
                                        key={item.transaction_id}
                                    >
                                        <span className="timeline-time">
                                            {formatClock(item.timestamp)}
                                        </span>
                                        <span className="timeline-amount">
                                            {formatINR(item.amount)}
                                        </span>
                                        <span className="timeline-merchant">
                                            {item.merchant_category}
                                        </span>
                                        <span className={`timeline-status ${status}`}>
                                            {icon}{" "}
                                            {status === "normal"
                                                ? "Normal"
                                                : status === "watch"
                                                    ? "Watch"
                                                    : "Suspicious"}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

            </div>

            <div className="transaction-info">
                <div>
                    <span>CUSTOMER</span>
                    <strong>{transaction.customer_id || "Unknown"}</strong>
                </div>
                <div>
                    <span>LOCATION</span>
                    <strong>
                        {transaction.country || transaction.ip_country || "Unknown"}
                    </strong>
                </div>
                <div>
                    <span>MERCHANT</span>
                    <strong>{transaction.merchant_category || "Unknown"}</strong>
                </div>
                <div>
                    <span>TIMESTAMP</span>
                    <strong>{transaction.timestamp || "Unknown"}</strong>
                </div>
            </div>

        </section>
    );
}


function ProfileStat({ label, value, flagged }) {
    return (
        <div className={`profile-stat ${flagged ? "flagged" : ""}`}>
            <span>{label}</span>
            <strong>{value}</strong>
        </div>
    );
}


function formatAction(action) {
    if (action === "MANUAL_REVIEW") return "Manual Review";
    if (action === "STEP_UP_VERIFICATION") return "Step-up Verification";
    if (action === "ALLOW") return "Allow Transaction";
    if (!action) return "Review Required";
    return action
        .replaceAll("_", " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
}


export default App;
