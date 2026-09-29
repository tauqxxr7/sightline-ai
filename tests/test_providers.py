import pytest

from app.inference.providers import ProviderUnavailable, plan_provider


def test_qnn_availability_is_not_execution():
    plan = plan_provider(("QNNExecutionProvider", "CPUExecutionProvider"))
    assert plan.selected == "QNNExecutionProvider"
    assert plan.active is None
    assert plan.backend is None
    assert plan.npu == "QNN/NPU not verified on this device"


def test_cpu_fallback_is_only_planned():
    plan = plan_provider(("CPUExecutionProvider",))
    assert plan.selected == "CPUExecutionProvider"
    assert plan.fallback == "planned_cpu"
    assert plan.active is None


def test_strict_mode_refuses_fallback():
    with pytest.raises(ProviderUnavailable):
        plan_provider(("CPUExecutionProvider",), strict=True)


def test_no_runtime_means_no_active_provider():
    plan = plan_provider(())
    assert plan.selected is None
    assert plan.active is None
    assert plan.fallback == "unavailable"


def test_explicit_cpu_request():
    plan = plan_provider(("CPUExecutionProvider",), requested="CPUExecutionProvider")
    assert plan.selected == "CPUExecutionProvider"
    assert plan.fallback == "not_started"


def test_invalid_provider_rejected():
    with pytest.raises(ValueError):
        plan_provider((), requested="invalid")
