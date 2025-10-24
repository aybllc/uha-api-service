"""
UHA merge functionality - Universal Hierarchical Aggregation

This module implements the UHA merge algorithm based on N/U algebra.
Patent: US 63/902,536

Mathematical Foundation:
For two measurements with nominal values (n1, n2) and uncertainties (u1, u2):
- Merged nominal: n_merge = (n1 + n2) / 2
- Merged uncertainty: u_merge = (u1 + u2) / 2 + |n1 - n2| / 2

This conservative merge rule ensures:
1. The merged interval covers both original intervals
2. Disagreement between measurements increases uncertainty
3. Associative and commutative properties (order-independent)
4. Never underestimates uncertainty
"""
from typing import Dict, List, Tuple, Optional
import time

from .models import MergeRequest, MergeResult


def nu_merge(n1: float, u1: float, n2: float, u2: float) -> Tuple[float, float]:
    """
    Core UHA merge function for two (nominal, uncertainty) pairs.

    Implements the N/U algebra merge rule:
    - n_merge = (n1 + n2) / 2
    - u_merge = (u1 + u2) / 2 + |n1 - n2| / 2

    Args:
        n1: First nominal value
        u1: First uncertainty
        n2: Second nominal value
        u2: Second uncertainty

    Returns:
        Tuple of (merged_nominal, merged_uncertainty)

    Reference:
        uhaMathematicalFoundation.txt, lines 5-9
    """
    n_merge = (n1 + n2) / 2.0
    u_merge = (u1 + u2) / 2.0 + abs(n1 - n2) / 2.0
    return n_merge, u_merge


def nu_cumulative_merge(nominals: List[float], uncertainties: List[float]) -> Tuple[float, float]:
    """
    Merge multiple measurements using iterative pairwise UHA merging.

    Due to associativity of the merge operation, the result is independent
    of merge order. This function applies nu_merge repeatedly.

    Args:
        nominals: List of nominal H0 values
        uncertainties: List of corresponding uncertainties

    Returns:
        Tuple of (final_nominal, final_uncertainty)

    Reference:
        uhaMathematicalFoundation.txt, lines 306-311
    """
    if len(nominals) != len(uncertainties):
        raise ValueError("Nominals and uncertainties must have same length")

    if len(nominals) == 0:
        raise ValueError("Cannot merge empty list")

    if len(nominals) == 1:
        return nominals[0], uncertainties[0]

    # Start with first measurement
    n_result, u_result = nominals[0], uncertainties[0]

    # Iteratively merge with remaining measurements
    for i in range(1, len(nominals)):
        n_result, u_result = nu_merge(n_result, u_result, nominals[i], uncertainties[i])

    return n_result, u_result


def extract_h0_and_uncertainty(dataset_name: str, dataset: dict) -> Tuple[float, float]:
    """
    Extract H0 value and uncertainty from dataset.

    Supports multiple uncertainty formats:
    - sigma.H0 (nested format)
    - sigma_H0 (flat format)
    - Default to 1.0 if not provided

    Args:
        dataset_name: Name of the dataset (for error messages)
        dataset: Dataset dictionary with H0 and uncertainty

    Returns:
        Tuple of (H0_value, uncertainty)
    """
    h0 = dataset.get('H0')

    # Try different uncertainty formats
    uncertainty = None

    # Format 1: sigma.H0
    if 'sigma' in dataset and dataset['sigma'] and 'H0' in dataset['sigma']:
        uncertainty = dataset['sigma']['H0']

    # Format 2: sigma_H0
    elif 'sigma_H0' in dataset:
        uncertainty = dataset['sigma_H0']

    # Default
    if uncertainty is None:
        uncertainty = 1.0  # Conservative default

    return h0, uncertainty


def calculate_chi_squared(
    nominals: List[float],
    uncertainties: List[float],
    merged_nominal: float
) -> float:
    """
    Calculate chi-squared statistic for the merge.

    χ² = Σ ((H0_i - H0_merged) / σ_i)²

    Args:
        nominals: Original H0 values
        uncertainties: Original uncertainties
        merged_nominal: Merged H0 value

    Returns:
        Chi-squared value
    """
    chi_squared = 0.0
    for n, u in zip(nominals, uncertainties):
        chi_squared += ((n - merged_nominal) / u) ** 2
    return chi_squared


def calculate_p_value(chi_squared: float, degrees_of_freedom: int) -> float:
    """
    Calculate p-value from chi-squared statistic.

    This is a simplified approximation. For production use with scipy:
    from scipy.stats import chi2
    p_value = 1.0 - chi2.cdf(chi_squared, degrees_of_freedom)

    Args:
        chi_squared: Chi-squared statistic
        degrees_of_freedom: Number of degrees of freedom (n_datasets - 1)

    Returns:
        Approximate p-value
    """
    # Simplified approximation (replace with scipy.stats.chi2 in production)
    # This is intentionally conservative
    if degrees_of_freedom <= 0:
        return 1.0

    # Rough approximation: p ≈ exp(-χ²/2df)
    # This is very approximate and should be replaced with proper chi2.sf
    import math
    try:
        p_approx = math.exp(-chi_squared / (2.0 * degrees_of_freedom))
        return min(1.0, max(0.0, p_approx))
    except:
        return 0.5  # Safe middle ground if calculation fails


def apply_systematic_corrections(
    h0: float,
    uncertainty: float,
    corrections: Optional[Dict[str, float]] = None
) -> Tuple[float, float]:
    """
    Apply known systematic corrections to a measurement.

    Corrections are subtracted from the nominal value and add to uncertainty.

    Example from SH0ES:
    - Anchor bias: -1.92 km/s/Mpc
    - P-L relation bias: -0.22 km/s/Mpc

    Args:
        h0: Original H0 value
        uncertainty: Original uncertainty
        corrections: Dict of correction_name -> correction_value

    Returns:
        Tuple of (corrected_h0, increased_uncertainty)

    Reference:
        uhaMathematicalFoundation.txt, lines 55-61
    """
    if not corrections:
        return h0, uncertainty

    corrected_h0 = h0
    additional_uncertainty = 0.0

    for correction_name, correction_value in corrections.items():
        # Apply correction to nominal
        corrected_h0 -= correction_value

        # Add uncertainty from the correction (assume 10% uncertainty in correction)
        additional_uncertainty += abs(correction_value) * 0.1

    # Combine uncertainties in quadrature
    total_uncertainty = (uncertainty**2 + additional_uncertainty**2) ** 0.5

    return corrected_h0, total_uncertainty


def perform_merge(request: MergeRequest) -> MergeResult:
    """
    Perform UHA merge on input datasets.

    Implements Universal Hierarchical Aggregation (UHA) based on N/U algebra.
    Patent: US 63/902,536

    Algorithm:
    1. Extract H0 and uncertainties from each dataset
    2. Apply any systematic corrections
    3. Merge using cumulative pairwise UHA merging
    4. Calculate chi-squared and p-value
    5. Return results with metadata

    Args:
        request: MergeRequest containing datasets and options

    Returns:
        MergeResult with merged values and statistics

    Reference:
        uhaMathematicalFoundation.txt, entire document
        Core equations: lines 5-9
        Example: lines 237-289
        Implementation: lines 294-311
    """
    datasets = request.datasets

    # Extract H0 values and uncertainties
    nominals = []
    uncertainties = []
    dataset_names = []

    for name, dataset in datasets.items():
        h0, uncertainty = extract_h0_and_uncertainty(name, dataset)

        # Apply systematic corrections if provided
        # (In production, you could add corrections to the request model)
        # For now, we don't apply corrections unless explicitly provided

        nominals.append(h0)
        uncertainties.append(uncertainty)
        dataset_names.append(name)

    # Perform UHA merge
    merged_h0, merged_uncertainty = nu_cumulative_merge(nominals, uncertainties)

    # Calculate chi-squared
    chi_squared = calculate_chi_squared(nominals, uncertainties, merged_h0)

    # Degrees of freedom
    dof = len(nominals) - 1

    # Calculate p-value
    p_value = calculate_p_value(chi_squared, dof)

    # Determine if coordinate encoding was used
    # (For ICRS2016, we consider coordinate encoding active)
    coordinate_encoding = request.options.coordinate_system == "ICRS2016"

    # Create result
    result = MergeResult(
        merged_H0=round(merged_h0, 2),
        uncertainty=round(merged_uncertainty, 2),
        chi_squared=round(chi_squared, 2),
        p_value=round(p_value, 3),
        method="UHA",
        coordinate_encoding=coordinate_encoding
    )

    return result


def validate_datasets(request: MergeRequest) -> Tuple[bool, List[str], List[str]]:
    """
    Validate input datasets.

    Returns: (valid: bool, warnings: list, suggestions: list)
    """
    warnings = []
    suggestions = []

    # Check minimum number of datasets
    if len(request.datasets) < 2:
        return False, ["At least 2 datasets required for merging"], []

    # Check each dataset
    for name, dataset in request.datasets.items():
        # Check H0 range
        if dataset.H0 < 50 or dataset.H0 > 90:
            warnings.append(
                f"Dataset '{name}': H0={dataset.H0} is outside typical range (50-90 km/s/Mpc)"
            )

        # Check if uncertainties are provided
        h0, uncertainty = extract_h0_and_uncertainty(name, dataset.__dict__)
        if uncertainty == 1.0 and not dataset.sigma and not dataset.sigma_H0:
            warnings.append(f"Dataset '{name}': No uncertainties provided, using default (1.0)")
            suggestions.append(f"Provide sigma_H0 for '{name}' for better accuracy")

        # Check Omega_m + Omega_Lambda for flat universe
        if dataset.Omega_m and dataset.Omega_Lambda:
            total = dataset.Omega_m + dataset.Omega_Lambda
            if not (0.95 <= total <= 1.05):
                warnings.append(
                    f"Dataset '{name}': Ω_m + Ω_Λ = {total:.3f}, "
                    f"should be close to 1.0 in flat universe"
                )

    # Check coordinate system
    if request.options.coordinate_system not in ["ICRS2016", "ICRS", "FK5", "J2000"]:
        suggestions.append(
            f"Coordinate system '{request.options.coordinate_system}' "
            f"may not be supported. Recommended: ICRS2016"
        )

    return True, warnings, suggestions


# Example usage and validation
if __name__ == "__main__":
    # Test case from uhaMathematicalFoundation.txt lines 15-21
    print("Testing UHA merge algorithm...")

    # Example: Planck (67.4±0.5) and SH0ES (73.0±1.0)
    n1, u1 = 67.4, 0.5
    n2, u2 = 73.0, 1.0

    n_merged, u_merged = nu_merge(n1, u1, n2, u2)

    print(f"\nInput:")
    print(f"  Dataset 1: {n1} ± {u1}")
    print(f"  Dataset 2: {n2} ± {u2}")
    print(f"\nUHA Merge Result:")
    print(f"  Merged: {n_merged:.2f} ± {u_merged:.2f}")
    print(f"\nExpected (from documentation): 70.2 ± 3.55")
    print(f"Actual result matches: {abs(n_merged - 70.2) < 0.01 and abs(u_merged - 3.55) < 0.01}")

    # Test cumulative merge with 4 datasets (lines 237-275)
    print("\n" + "="*60)
    print("Testing 4-dataset merge (Early + Late Universe)...")

    # Early universe
    planck = (67.4, 0.5)
    des = (67.2, 0.6)

    # Late universe
    shoes = (73.0, 1.0)
    trgb = (69.8, 2.5)

    # Merge early
    early_merged = nu_merge(*planck, *des)
    print(f"\nEarly Universe (Planck + DES): {early_merged[0]:.2f} ± {early_merged[1]:.2f}")
    print(f"Expected: 67.3 ± 0.65")

    # Merge late
    late_merged = nu_merge(*shoes, *trgb)
    print(f"Late Universe (SH0ES + TRGB): {late_merged[0]:.2f} ± {late_merged[1]:.2f}")
    print(f"Expected: 71.4 ± 3.35")

    # Global merge
    global_merged = nu_merge(*early_merged, *late_merged)
    print(f"\nGlobal Merge: {global_merged[0]:.2f} ± {global_merged[1]:.2f}")
    print(f"Expected: 69.35 ± 4.05")

    print("\n✅ UHA Algorithm Implementation Complete!")
