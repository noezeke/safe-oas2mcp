KEYWORD_GROUPS: dict[str, set[str]] = {
    "money": {
        "payment",
        "pay",
        "refund",
        "transfer",
        "payout",
        "invoice",
        "billing",
        "charge",
    },
    "identity": {
        "user",
        "account",
        "member",
        "customer",
        "password",
        "credential",
        "token",
        "secret",
        "key",
        "email",
        "phone",
    },
    "permission": {
        "admin",
        "root",
        "role",
        "permission",
        "policy",
        "access",
        "invite",
    },
    "destructive": {
        "delete",
        "remove",
        "destroy",
        "revoke",
        "disable",
        "suspend",
        "terminate",
    },
    "bulk_data": {
        "export",
        "bulk",
        "batch",
        "dump",
        "report",
        "download",
    },
}


HIGH_RISK_KEYWORDS = {
    keyword for keywords in KEYWORD_GROUPS.values() for keyword in keywords
}
