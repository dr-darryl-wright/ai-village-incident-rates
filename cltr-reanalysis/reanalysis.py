"""Reanalysis of CLTR's insight report of 28 August 2026 ("AI loss of control incidents are worsening").

Data: monthly counts printed on the report's Annex 1 chart (incidents scoring 7+ out of 9, and all
incidents scoring 5+). October 2025 covers 19 days (from 12 Oct), August 2026 covers 9 days (to 9 Aug).
Requires: numpy, scipy, statsmodels.
"""
import numpy as np
from scipy import stats
import statsmodels.api as sm

months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
hi = np.array([0, 1, 2, 4, 9, 16, 10, 16, 7, 18, 8])          # scoring 7 or more
n = np.array([53, 109, 97, 121, 246, 293, 233, 204, 158, 306, 103])  # all incidents
days = np.array([19, 30, 31, 31, 28, 31, 30, 31, 30, 31, 9])

print("Total incidents:", n.sum(), "| in 2026:", n[3:].sum(), "| scoring 7+:", hi.sum())
print("Incidents per day:", dict(zip(months, np.round(n / days, 1))))

def fisher(k):
    a, b, c, d = hi[:k].sum(), n[:k].sum(), hi[k:].sum(), n[k:].sum()
    return a, b, c, d, stats.fisher_exact([[a, b - a], [c, d - c]])[1]

a, b, c, d, p = fisher(4)
print(f"\nOct-Jan {a}/{b} = {a/b:.1%}  vs  Feb-Aug {c}/{d} = {c/d:.1%}  Fisher p = {p:.4f}")

print("\nSensitivity to the split month:")
for k in range(2, 9):
    a, b, c, d, p = fisher(k)
    print(f"  split before {months[k]}: {a/b:.1%} vs {c/d:.1%}  p = {p:.4f}")

print("\nIf the early period had more incidents scoring 7+ (misclassification check):")
for extra in [0, 2, 3, 5]:
    a = 7 + extra
    p = stats.fisher_exact([[a, 380 - a], [84, 1543 - 84]])[1]
    print(f"  {a}/380 = {a/380:.1%}: ratio {0.0544/(a/380):.1f}x, p = {p:.3f}")

def trend(sl):
    X = sm.add_constant(np.arange(len(hi[sl])))
    r = sm.GLM(np.c_[hi[sl], n[sl] - hi[sl]], X, family=sm.families.Binomial()).fit()
    return r.params[1], r.pvalues[1]

s, p = trend(slice(4, 11))
print(f"\nTrend in share, Feb-Aug (logistic): slope {s:.3f} per month, p = {p:.2f}")
chi = stats.chi2_contingency(np.c_[hi[4:], n[4:] - hi[4:]])
print(f"Do Feb-Aug months differ (chi-square): p = {chi[1]:.2f}")

print("\nThe report's 7.4x rise in 7+ counts = volume ratio x share ratio: 7.4 / 3.2 =", round(7.4 / 3.2, 1))
