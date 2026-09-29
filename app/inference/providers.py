"""Provider intent is not evidence of execution."""

from dataclasses import asdict, dataclass
from typing import Literal

ProviderName = Literal["QNNExecutionProvider", "CPUExecutionProvider"]


class ProviderUnavailable(ValueError):
    """The requested provider cannot be selected under the current policy."""


@dataclass(frozen=True)
class ProviderPlan:
    requested: ProviderName
    available: tuple[str, ...]
    selected: str | None
    active: str | None = None
    fallback: str = "not_started"
    npu: str = "QNN/NPU not verified on this device"
    backend: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def plan_provider(
    available: tuple[str, ...],
    requested: ProviderName = "QNNExecutionProvider",
    strict: bool = False,
) -> ProviderPlan:
    """Plan only. A later session runner must provide actual execution evidence."""
    if requested not in ("QNNExecutionProvider", "CPUExecutionProvider"):
        raise ValueError("Unsupported provider")
    if requested in available:
        return ProviderPlan(requested, available, requested)
    if strict:
        raise ProviderUnavailable("Requested provider unavailable; strict mode forbids fallback.")
    if requested == "QNNExecutionProvider" and "CPUExecutionProvider" in available:
        return ProviderPlan(requested, available, "CPUExecutionProvider", fallback="planned_cpu")
    return ProviderPlan(requested, available, None, fallback="unavailable")
