"""Observation noise. Independent (Stage 1) or correlated (Stage 2)."""

class NoiseProcess:
    """
    independent : each observation errs i.i.d. at base_error_rate.
    correlated  : a per-cycle shared bias source makes errors co-occur.
                  With probability `correlation` the cycle enters a 'burst'
                  in which the error rate is elevated for ALL observers, so
                  repeated observations are no longer independent evidence.
                  Marginal error rate is held ~constant so that correlated and
                  independent conditions are comparable rather than merely
                  noisier. Built now, exercised in Stage 2.
    """

    def __init__(self, cfg, rng):
        self.mode = cfg["mode"]
        self.p = cfg["base_error_rate"]
        self.rho = cfg.get("correlation", 0.0)
        self.rng = rng
        self._cycle = None
        self._burst = False

    def _refresh(self, cycle):
        if cycle != self._cycle:
            self._cycle = cycle
            self._burst = (self.mode == "correlated"
                           and self.rng.random() < self.rho)

    def err_rate(self, cycle):
        self._refresh(cycle)
        if self.mode == "independent" or self.rho <= 0:
            return self.p
        # Keep marginal error rate ~= p: burst rate p_hi with prob rho,
        # low rate p_lo otherwise, s.t. rho*p_hi + (1-rho)*p_lo = p.
        p_hi = min(0.95, self.p / max(self.rho, 1e-9) * 0.6 + self.p)
        p_lo = max(0.0, (self.p - self.rho * p_hi) / max(1 - self.rho, 1e-9))
        return p_hi if self._burst else p_lo

    def observe(self, truth, cycle):
        return truth if self.rng.random() > self.err_rate(cycle) else 1 - truth
