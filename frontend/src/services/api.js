const API_BASE = "/api";


async function request(endpoint) {

    const response = await fetch(
        `${API_BASE}${endpoint}`
    );

    if (!response.ok) {

        let message =
            "Something went wrong.";

        try {

            const error =
                await response.json();

            message =
                error.detail || message;

        } catch {

            // Ignore invalid JSON responses

        }

        throw new Error(message);

    }

    return response.json();

}


export function getDashboardSummary() {

    return request(
        "/dashboard/summary"
    );

}


export function getTransactions(
    query = "",
    risk = "ALL",
    limit = 25,
    offset = 0
) {

    const params =
        new URLSearchParams({

            query,
            risk,
            limit,
            offset

        });

    return request(
        `/transactions?${params}`
    );

}


export function getTransaction(
    transactionId
) {

    return request(
        `/transactions/${transactionId}`
    );

}


export function investigateTransaction(
    transactionId
) {

    return request(
        `/investigate/${transactionId}`
    );

}


export function getRiskAnalytics() {

    return request(
        "/analytics/risk"
    );

}