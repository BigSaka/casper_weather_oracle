//! Reputation contract for the Weather Oracle.
//!
//! Kept separate from `WeatherOracle` because it has a different caller
//! (the reconciliation job, not the live agent) and a different lifecycle
//! (it only writes after ground-truth data becomes available, which is
//! always later than the original reading). Splitting it also means the
//! oracle contract stays small and auditable on its own.

use odra::prelude::*;
use odra::{Address, Var};

#[odra::event]
pub struct OutcomeRecorded {
    pub reading_index: u32,
    pub official_value_fp: i64,
    pub posted_value_fp: i64,
    pub was_accurate: bool,
}

#[odra::odra_error]
pub enum Error {
    NotAuthorizedReconciler = 1,
}

/// Accuracy is judged "hit" if the posted value is within a tolerance band
/// of the official value. Tolerance is fixed-point, same scale as readings
/// (value * 100), so e.g. a 200 tolerance on rainfall means +/-2.00mm.
#[odra::module(events = [OutcomeRecorded])]
pub struct Reputation {
    /// The only address allowed to call `record_outcome`. In the MVP this
    /// can be the same wallet as the oracle's agent, run as a second,
    /// slower cron job — or a separate reconciler key if you want to keep
    /// "post" and "grade" privileges apart.
    reconciler: Var<Address>,
    tolerance_fp: Var<i64>,
    total_readings: Var<u32>,
    accurate_readings: Var<u32>,
    current_streak: Var<u32>,
}

#[odra::module]
impl Reputation {
    pub fn init(&mut self, reconciler: Address, tolerance_fp: i64) {
        self.reconciler.set(reconciler);
        self.tolerance_fp.set(tolerance_fp);
        self.total_readings.set(0);
        self.accurate_readings.set(0);
        self.current_streak.set(0);
    }

    /// Called once ground-truth data is available for a previously posted
    /// reading. Compares posted vs. official value within tolerance and
    /// updates the running accuracy score and streak.
    pub fn record_outcome(
        &mut self,
        reading_index: u32,
        posted_value_fp: i64,
        official_value_fp: i64,
    ) {
        let caller = self.env().caller();
        if caller != self.reconciler.get_or_revert(&Error::NotAuthorizedReconciler) {
            self.env().revert(Error::NotAuthorizedReconciler);
        }

        let tolerance = self.tolerance_fp.get_or_default();
        let diff = (posted_value_fp - official_value_fp).abs();
        let was_accurate = diff <= tolerance;

        self.total_readings.set(self.total_readings.get_or_default() + 1);
        if was_accurate {
            self.accurate_readings.set(self.accurate_readings.get_or_default() + 1);
            self.current_streak.set(self.current_streak.get_or_default() + 1);
        } else {
            self.current_streak.set(0);
        }

        self.env().emit_event(OutcomeRecorded {
            reading_index,
            official_value_fp,
            posted_value_fp,
            was_accurate,
        });
    }

    /// Dashboard read: accuracy as basis points (e.g. 9500 = 95.00%).
    /// Returns 0 if no readings have been graded yet.
    pub fn get_accuracy_bps(&self) -> u32 {
        let total = self.total_readings.get_or_default();
        if total == 0 {
            return 0;
        }
        let accurate = self.accurate_readings.get_or_default();
        (accurate as u64 * 10_000 / total as u64) as u32
    }

    pub fn get_total_readings(&self) -> u32 {
        self.total_readings.get_or_default()
    }

    pub fn get_current_streak(&self) -> u32 {
        self.current_streak.get_or_default()
    }
}
