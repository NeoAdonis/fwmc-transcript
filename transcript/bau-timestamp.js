"use strict";

const { filterTokens } = require("markdownlint-rule-helpers");

module.exports = {
    names: ["bau-timestamp"],
    description: "Timestamps are required in the summaries.",
    tags: ["transcript"],
    function: (params, onError) {
        filterTokens(params, "heading", function forToken(token) {
            if (token.content.includes("Timestamp:")) {
                return;
            }
            onError({
                lineNumber: token.lineNumber,
                detail: "Timestamps are required in the summaries.",
                range: token.range
            });
        });
    }
};