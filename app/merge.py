"""
Cosmological dataset aggregation and statistical analysis.
"""
from typing import Dict, List, Tuple, Optional
import math

from .models import MergeRequest, MergeResult


def aggregate_pair(v1: float, e1: float, v2: float, e2: float) -> Tuple[float, float]:
    """
    Aggregate two measurements with associated errors.

    Args:
        v1: First value
        e1: First error estimate
        v2: Second value
        e2: Second error estimate

    Returns:
        Tuple of (aggregated_value, propagated_error)
    """
    agg_val = (v1 + v2) * 0.5
    prop_err = (e1 + e2) * 0.5 + abs(v1 - v2) * 0.5
    return agg_val, prop_err


def aggregate_sequential(values: List[float], errors: List[float]) -> Tuple[float, float]:
    """
    Sequentially aggregate multiple measurements.

    Args:
        values: List of measured values
        errors: List of corresponding error estimates

    Returns:
        Tuple of (final_value, final_error)
    """
    if len(values) != len(errors):
        raise ValueError("Values and errors must have same length")

    if len(values) == 0:
        raise ValueError("Cannot aggregate empty list")

    if len(values) == 1:
        return values[0], errors[0]

    result_val, result_err = values[0], errors[0]

    for i in range(1, len(values)):
        result_val, result_err = aggregate_pair(
            result_val, result_err, values[i], errors[i]
        )

    return result_val, result_err


def extract_h0_and_uncertainty(dataset_name: str, dataset: dict) -> Tuple[float, float]:
    """Extract H0 value and uncertainty from dataset."""
    h0 = dataset.get('H0')
    uncertainty = None

    if 'sigma' in dataset and dataset['sigma'] and 'H0' in dataset['sigma']:
        uncertainty = dataset['sigma']['H0']
    elif 'sigma_H0' in dataset:
        uncertainty = dataset['sigma_H0']

    if uncertainty is None:
        uncertainty = 1.0

    return h0, uncertainty


def calculate_chi_squared(
    values: List[float],
    errors: List[float],
    central_value: float
) -> float:
    """Calculate chi-squared statistic."""
    chi_sq = 0.0
    for v, e in zip(values, errors):
        chi_sq += ((v - central_value) / e) ** 2
    return chi_sq


def calculate_p_value(chi_squared: float, dof: int) -> float:
    """Calculate p-value from chi-squared statistic."""
    if dof <= 0:
        return 1.0

    try:
        p_approx = math.exp(-chi_squared / (2.0 * dof))
        return min(1.0, max(0.0, p_approx))
    except:
        return 0.5


def apply_systematic_corrections(
    h0: float,
    uncertainty: float,
    corrections: Optional[Dict[str, float]] = None
) -> Tuple[float, float]:
    """Apply systematic corrections to a measurement."""
    if not corrections:
        return h0, uncertainty

    corrected_h0 = h0
    additional_uncertainty = 0.0

    for correction_name, correction_value in corrections.items():
        corrected_h0 -= correction_value
        additional_uncertainty += abs(correction_value) * 0.1

    total_uncertainty = (uncertainty**2 + additional_uncertainty**2) ** 0.5

    return corrected_h0, total_uncertainty


def perform_merge(request: MergeRequest) -> MergeResult:
    """
    Perform statistical aggregation on input datasets.

    Args:
        request: MergeRequest containing datasets and options

    Returns:
        MergeResult with aggregated values and statistics
    """
    datasets = request.datasets

    values = []
    errors = []
    dataset_names = []

    for name, dataset in datasets.items():
        h0, uncertainty = extract_h0_and_uncertainty(name, dataset)
        values.append(h0)
        errors.append(uncertainty)
        dataset_names.append(name)

    aggregated_h0, aggregated_uncertainty = aggregate_sequential(values, errors)

    chi_squared = calculate_chi_squared(values, errors, aggregated_h0)
    dof = len(values) - 1
    p_value = calculate_p_value(chi_squared, dof)

    coordinate_encoding = request.options.coordinate_system == "ICRS2016"

    result = MergeResult(
        merged_H0=round(aggregated_h0, 2),
        uncertainty=round(aggregated_uncertainty, 2),
        chi_squared=round(chi_squared, 2),
        p_value=round(p_value, 3),
        method="UHA",
        coordinate_encoding=coordinate_encoding
    )

    return result


def validate_datasets(request: MergeRequest) -> Tuple[bool, List[str], List[str]]:
    """Validate input datasets."""
    warnings = []
    suggestions = []

    if len(request.datasets) < 2:
        return False, ["At least 2 datasets required for merging"], []

    for name, dataset in request.datasets.items():
        if dataset.H0 < 50 or dataset.H0 > 90:
            warnings.append(
                f"Dataset '{name}': H0={dataset.H0} is outside typical range (50-90 km/s/Mpc)"
            )

        h0, uncertainty = extract_h0_and_uncertainty(name, dataset.__dict__)
        if uncertainty == 1.0 and not dataset.sigma and not dataset.sigma_H0:
            warnings.append(f"Dataset '{name}': No uncertainties provided, using default (1.0)")
            suggestions.append(f"Provide sigma_H0 for '{name}' for better accuracy")

        if dataset.Omega_m and dataset.Omega_Lambda:
            total = dataset.Omega_m + dataset.Omega_Lambda
            if not (0.95 <= total <= 1.05):
                warnings.append(
                    f"Dataset '{name}': Ω_m + Ω_Λ = {total:.3f}, "
                    f"should be close to 1.0 in flat universe"
                )

    if request.options.coordinate_system not in ["ICRS2016", "ICRS", "FK5", "J2000"]:
        suggestions.append(
            f"Coordinate system '{request.options.coordinate_system}' "
            f"may not be supported. Recommended: ICRS2016"
        )

    return True, warnings, suggestions
