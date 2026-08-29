import enum


class TransactionStatus(str, enum.Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PaymentAttemptStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class PaymentMethod(str, enum.Enum):
    CARD = "CARD"
    UPI = "UPI"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"


class FailureReason(str, enum.Enum):
    TIMEOUT = "TIMEOUT"
    BANK_DECLINED = "BANK_DECLINED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    NETWORK_ERROR = "NETWORK_ERROR"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"


class RecoveryActionType(str, enum.Enum):
    RETRY_NOW = "RETRY_NOW"
    RETRY_AFTER_DELAY = "RETRY_AFTER_DELAY"
    SEND_PAYMENT_LINK = "SEND_PAYMENT_LINK"
    CHANGE_PAYMENT_METHOD = "CHANGE_PAYMENT_METHOD"
    NOTIFY_CUSTOMER = "NOTIFY_CUSTOMER"
    ESCALATE = "ESCALATE"
    STOP = "STOP"


class RecoveryActionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ActorType(str, enum.Enum):
    SYSTEM = "SYSTEM"
    AI_AGENT = "AI_AGENT"
    HUMAN = "HUMAN"
    POLICY_ENGINE = "POLICY_ENGINE"
